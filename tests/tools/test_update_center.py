import pytest
import hashlib
import io
from pathlib import Path
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import update_center as updates
from lib import production_studio as studio


def test_update_targets_page_catalog_models_and_apps():
    first=updates.targets(0,10)
    assert first['models']>0 and first['applications']>0 and first['total']>10
    assert len(first['rows'])==10 and first['next_offset']==10
    assert all(row['kind'] in ('model','application') for row in first['rows'])
    assert all(row['source_url'].startswith('https://huggingface.co/') for row in first['rows'] if row['kind']=='model')
    with pytest.raises(ValueError):updates.targets(0,21)


def test_live_check_compares_source_revision_without_claiming_installation(monkeypatch):
    row=next(row for offset in range(0,updates.targets()['total'],10)
             for row in updates.targets(offset,10)['rows'] if row['kind']=='model')
    requested=[]
    def fetch(url):
        requested.append(url)
        return {'sha':'f'*40,'siblings':[{'rfilename':'other/file.safetensors'}]}
    monkeypatch.setattr(updates,'_json',fetch)
    result=updates.check('model',row['id'])
    assert requested==['https://huggingface.co/api/models/'+row['id']]
    assert result['status']=='source_revision_changed'
    assert result['missing_file_count']>0
    assert 'instalación' in result['note'] and result['latest_revision']=='f'*40
    with pytest.raises(ValueError):updates.check('model','other/unknown-repo')
    with pytest.raises(ValueError):updates.check('model','example.com/../../internal')


def test_application_release_is_not_local_update(monkeypatch):
    monkeypatch.setattr(updates,'_json',lambda url:{'tag_name':'v1.2.3','published_at':'2026-11-20'})
    result=updates.check('application','yt-dlp')
    assert result['tag']=='v1.2.3' and result['local_version']=='unknown'
    assert updates.check('application','blender')['status']=='manual_review'


@pytest.mark.parametrize('siblings',[None,{},[None],[{}],[{'rfilename':[]}],
    [{'rfilename':'model.bin'},{'rfilename':'model.bin'}]])
def test_model_source_rejects_incomplete_file_lists(monkeypatch,siblings):
    row=next(row for offset in range(0,updates.targets()['total'],20)
             for row in updates.targets(offset,20)['rows'] if row['kind']=='model')
    monkeypatch.setattr(updates,'_json',lambda url:{'sha':'f'*40,'siblings':siblings})
    with pytest.raises(ValueError):updates.check('model',row['id'])
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.get('/api/studio/updates/check',params={'kind':'model','identifier':row['id']})
    assert response.status_code==400


def test_discovery_is_bounded_and_does_not_install(monkeypatch):
    urls=[]
    def fetch(url):
        urls.append(url)
        if 'huggingface.co' in url:
            return [{'id':'NewOrg/NewVideo','lastModified':'2026-11-20','pipeline_tag':'text-to-video'}]
        return {'items':[{'full_name':'NewOrg/NewEditor','description':'local editor','updated_at':'2026-11-20'}]}
    monkeypatch.setattr(updates,'_json',fetch)
    models=updates.discover('model','video local')
    apps=updates.discover('application','video editor')
    assert models['rows'][0]['id']=='NewOrg/NewVideo'
    assert apps['rows'][0]['id']=='NewOrg/NewEditor'
    assert models['downloads_started']==apps['downloads_started']==0
    assert urls[0].startswith('https://huggingface.co/api/models?')
    assert urls[1].startswith('https://api.github.com/search/repositories?')
    with pytest.raises(ValueError):updates.discover('model','a')
    with pytest.raises(ValueError):updates.discover('application','video&per_page=1000')


def test_update_api_read_only(monkeypatch):
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.get('/api/studio/updates?offset=0&limit=5')
    assert response.status_code==200 and len(response.json()['rows'])==5
    monkeypatch.setattr(updates,'_json',lambda url:{'tag_name':'v1.2.3'})
    response=client.get('/api/studio/updates/check?kind=application&identifier=yt-dlp')
    assert response.status_code==200 and response.json()['status']=='release_found'
    monkeypatch.setattr(updates,'_json',lambda url:[])
    assert client.get('/api/studio/updates/discover?kind=model&query=video').json()['rows']==[]


def test_explicit_local_file_hash_matches_only_catalogued_bytes(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'REPO_ROOT',tmp_path)
    target=tmp_path/'weights/model.safetensors';target.parent.mkdir();target.write_bytes(b'weights')
    expected=hashlib.sha256(b'weights').hexdigest()
    studio.save_json(tmp_path/'docs/models/test.json',{'files':[{'destination':str(target),
        'url':'https://huggingface.co/Org/Video/resolve/'+'a'*40+'/model.safetensors',
        'size_bytes':7,'sha256':expected}]})
    listing=updates.files('Org/Video')
    assert listing['total']==1 and listing['rows'][0]['index']==0
    assert updates.check_local('Org/Video',0)['status']=='matches_catalog'
    target.write_bytes(b'changed')
    assert updates.check_local('Org/Video',0)['status']=='differs_from_catalog'
    target.unlink()
    assert updates.check_local('Org/Video',0)['status']=='missing_or_link'
    with pytest.raises(ValueError):updates.check_local('Org/Video',1)


@pytest.mark.parametrize('content',[b'',b'weights'])
def test_local_hash_handles_empty_files_and_stat_failure(tmp_path,monkeypatch,content):
    target=tmp_path/'model.bin';target.write_bytes(content)
    monkeypatch.setattr(updates,'_files',lambda identifier:[{
        'destination':str(target),'catalog_sha256':hashlib.sha256(content).hexdigest(),
        'catalog_bytes':len(content)}])
    assert updates.check_local('Org/Video',0)['status']=='matches_catalog'
    original=Path.stat
    def unavailable(path,*args,**kwargs):
        if path==target:raise PermissionError('unavailable')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'stat',unavailable)
    assert updates.check_local('Org/Video',0)['status']=='unreadable'


def test_local_hash_stops_reading_a_growing_file(tmp_path,monkeypatch):
    target=tmp_path/'model.bin';target.write_bytes(b'old')
    monkeypatch.setattr(updates,'_files',lambda identifier:[{
        'destination':str(target),'catalog_sha256':hashlib.sha256(b'old').hexdigest(),
        'catalog_bytes':3}])
    original=Path.open
    def growing(path,*args,**kwargs):
        if path==target:return io.BytesIO(b'old'+b'x'*100)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',growing)
    result=updates.check_local('Org/Video',0)
    assert result['status']=='changed_during_check'
    assert result['bytes_read']==4


@pytest.fixture
def remote_catalog(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(studio,'REPO_ROOT',tmp_path)
    studio.save_json(tmp_path/'docs/models/test.json',{'files':[{
        'destination':'D:/models/model.safetensors',
        'url':'https://huggingface.co/Org/Video/resolve/'+'a'*40+'/nested/model.safetensors',
        'size_bytes':7,'sha256':'b'*64}]})


@pytest.mark.parametrize('metadata,status',[
    ({'size':7,'lfs':{'sha256':'b'*64}},'remote_matches_catalog'),
    ({'size':7,'lfs':{'sha256':'c'*64}},'remote_differs_from_catalog'),
    ({'size':8,'lfs':{'sha256':'b'*64}},'remote_differs_from_catalog'),
    ({'size':8},'remote_differs_from_catalog'),
    ({'size':7,'blobId':'b'*40},'remote_comparison_inconclusive'),
    ({'size':True,'lfs':{'sha256':'invalid'}},'remote_comparison_inconclusive'),
    ({},'remote_comparison_inconclusive'),
])
def test_remote_file_compares_content_not_repository_commit(remote_catalog,monkeypatch,metadata,status):
    urls=[]
    def fetch(url):
        urls.append(url)
        return {'sha':'f'*40,'siblings':[{'rfilename':'nested/model.safetensors',**metadata}]}
    monkeypatch.setattr(updates,'_json',fetch)
    result=updates.check_remote_file('Org/Video',0)
    assert result['status']==status
    assert result['remote_revision']=='f'*40
    assert result['catalog_revision']=='a'*40
    assert result['downloads_started']==0
    assert urls==['https://huggingface.co/api/models/Org/Video?blobs=true']


def test_remote_file_missing_and_pinned_revision(remote_catalog,monkeypatch):
    urls=[]
    def fetch(url):
        urls.append(url)
        return {'sha':'f'*40,'siblings':[]}
    monkeypatch.setattr(updates,'_json',fetch)
    result=updates.check_remote_file('Org/Video',0,'f'*40)
    assert result['status']=='missing_at_remote_revision'
    assert urls==['https://huggingface.co/api/models/Org/Video/revision/'+'f'*40+'?blobs=true']
    with pytest.raises(ValueError,match='revisión solicitada'):
        updates.check_remote_file('Org/Video',0,'e'*40)


@pytest.mark.parametrize('payload',[
    None,{}, {'sha':'invalid','siblings':[]}, {'sha':'f'*40},
    {'sha':'f'*40,'siblings':[{}]},
    {'sha':'f'*40,'siblings':[{'rfilename':'nested/model.safetensors'}]*2},
])
def test_remote_file_rejects_incomplete_or_ambiguous_metadata(remote_catalog,monkeypatch,payload):
    monkeypatch.setattr(updates,'_json',lambda url:payload)
    with pytest.raises(ValueError):updates.check_remote_file('Org/Video',0)


@pytest.mark.parametrize('identifier,index,revision',[
    ('Org/Unknown',0,None),('Org/Video',True,None),('Org/Video',-1,None),
    ('Org/Video',1,None),('Org/Video',0,'main'),('Org/Video',0,'f'*40+'/../'),
])
def test_remote_file_rejects_invalid_requests_before_network(remote_catalog,monkeypatch,identifier,index,revision):
    def forbidden(url):pytest.fail('Invalid requests must not access the network')
    monkeypatch.setattr(updates,'_json',forbidden)
    with pytest.raises(ValueError):updates.check_remote_file(identifier,index,revision)


def test_remote_file_api_and_agent_share_explicit_snapshot(remote_catalog,monkeypatch):
    from lib.production_agent import LocalAgent,TOOLS
    monkeypatch.setattr(updates,'_json',lambda url:{'sha':'f'*40,'siblings':[
        {'rfilename':'nested/model.safetensors','size':7,'lfs':{'sha256':'b'*64}}]})
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    args={'identifier':'Org/Video','index':0,'revision':'f'*40}
    response=client.get('/api/studio/updates/remote-file-check',params=args)
    assert response.status_code==200,response.text
    assert response.json()['status']=='remote_matches_catalog'
    assert response.json()['remote_revision']=='f'*40
    assert client.get('/api/studio/updates/remote-file-check',params={**args,'revision':'main'}).status_code==400
    worker=LocalAgent.__new__(LocalAgent)
    result=worker.dispatch('update_remote_file_check',args)
    assert result['status']=='remote_matches_catalog'
    assert result['remote_revision']=='f'*40
    assert any(tool['function']['name']=='update_remote_file_check' for tool in TOOLS)


@pytest.mark.parametrize('license_value,expected',[
    ('apache-2.0','declared_requires_review'),
    (['mit','other'],'declared_requires_review'),
    (None,'license_metadata_incomplete'),
    ({'name':'mit'},'license_metadata_incomplete'),
    (['mit',None],'license_metadata_incomplete'),
    ('<script>alert(1)</script>','license_metadata_incomplete'),
])
def test_remote_review_never_grants_rights_or_runtime_approval(remote_catalog,monkeypatch,license_value,expected):
    monkeypatch.setattr(updates,'_json',lambda url:{
        'sha':'f'*40,'cardData':{'license':license_value},'gated':'manual','private':False,
        'siblings':[{'rfilename':'nested/model.safetensors','size':7,'lfs':{'sha256':'b'*64}},
                    {'rfilename':'LICENSE.md'}]})
    result=updates.check_remote_file('Org/Video',0,'f'*40)
    assert result['license_review']['status']==expected
    assert result['license_review']['commercial_use']=='not_verified'
    assert result['license_review']['cost_conditions']=='not_verified'
    assert result['license_review']['license_file_urls']==[
        'https://huggingface.co/Org/Video/blob/'+'f'*40+'/LICENSE.md']
    assert result['access_review']=={'gated':'manual','private':False}
    assert result['compatibility_review']['status']=='catalog_content_matches_runtime_unverified'
    assert result['compatibility_review']['hardware']=='not_tested'
    assert result['update_allowed'] is False


@pytest.mark.parametrize('missing', [True,False])
def test_remote_changes_require_review_even_with_declared_license(remote_catalog,monkeypatch,missing):
    monkeypatch.setattr(updates,'_json',lambda url:{'sha':'f'*40,'cardData':{'license':'mit'},
        'siblings':[] if missing else [{'rfilename':'nested/model.safetensors','size':8}]})
    result=updates.check_remote_file('Org/Video',0)
    assert result['compatibility_review']['status']=='requires_review'
    assert result['update_allowed'] is False
    assert result['access_review']=={'gated':'unknown','private':'unknown'}


def document_transport(monkeypatch,raw,content_type='text/plain'):
    from email.message import Message
    calls=[]
    class Response(io.BytesIO):
        headers=Message()
    Response.headers['Content-Type']=content_type
    class Opener:
        def open(self,request,timeout):
            calls.append((request.full_url,timeout))
            return Response(raw)
    monkeypatch.setattr(updates.urllib.request,'build_opener',lambda *args:Opener())
    return calls


def document_metadata(monkeypatch,raw,**entry):
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    monkeypatch.setattr(updates,'_json',lambda url:{'sha':'f'*40,'siblings':[
        {'rfilename':'LICENSE','size':len(raw),'blobId':blob,**entry}]})


def test_document_api_and_agent_read_identical_pinned_evidence(remote_catalog,monkeypatch):
    from lib.production_agent import LocalAgent,TOOLS
    raw=b'Terms: attribution required. <script>never execute()</script>'
    document_metadata(monkeypatch,raw)
    calls=document_transport(monkeypatch,raw)
    args={'identifier':'Org/Video','revision':'f'*40,'filename':'LICENSE'}
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.get('/api/studio/updates/document',params=args)
    assert response.status_code==200,response.text
    result=response.json()
    assert result['text']==raw.decode()
    assert result['sha256']==hashlib.sha256(raw).hexdigest()
    assert result['git_blob_verified'] is True
    assert result['update_allowed'] is False
    assert result['content_role']=='untrusted_source_document'
    worker=LocalAgent.__new__(LocalAgent)
    assert worker.dispatch('update_read_document',args)['text']==result['text']
    assert calls==[('https://huggingface.co/Org/Video/raw/'+'f'*40+'/LICENSE',8)]*2
    assert any(tool['function']['name']=='update_read_document' for tool in TOOLS)


@pytest.mark.parametrize('identifier,revision,filename',[
    ('Org/Unknown','f'*40,'README.md'),('Org/Video','main','LICENSE'),
    ('Org/Video',None,'LICENSE'),('Org/Video','f'*40,'../LICENSE'),
    ('Org/Video','f'*40,'model.safetensors'),('Org/Video','f'*40,'https://localhost/LICENSE'),
    ('Org/Video','f'*40,[]),
])
def test_document_rejects_invalid_requests_without_network(remote_catalog,monkeypatch,identifier,revision,filename):
    monkeypatch.setattr(updates,'_json',lambda url:pytest.fail('Invalid request accessed network'))
    with pytest.raises(ValueError):updates.read_remote_document(identifier,revision,filename)


@pytest.mark.parametrize('raw,mime',[
    (b'x'*64_001,'text/plain'),(b'\xff','text/plain'),(b'abc\0def','text/plain'),
    (b'version https://git-lfs.github.com/spec/v1\n','text/plain'),
    (b'<html>Login</html>','text/html'),
])
def test_document_rejects_large_binary_pointer_and_html(remote_catalog,monkeypatch,raw,mime):
    document_metadata(monkeypatch,raw,size=None)
    document_transport(monkeypatch,raw,mime)
    with pytest.raises(ValueError):updates.read_remote_document('Org/Video','f'*40,'LICENSE')


@pytest.mark.parametrize('entry',[
    {'blobId':'a'*40},{'blobId':'invalid'},{'size':50},{'size':64_001},{'lfs':{}},
])
def test_document_rejects_changed_or_weight_metadata(remote_catalog,monkeypatch,entry):
    document_metadata(monkeypatch,b'Terms',**entry)
    document_transport(monkeypatch,b'Terms')
    with pytest.raises(ValueError):updates.read_remote_document('Org/Video','f'*40,'LICENSE')


@pytest.mark.parametrize('payload',[
    None,{}, {'sha':'e'*40,'siblings':[]}, {'sha':'f'*40,'siblings':[{}]},
    {'sha':'f'*40,'siblings':[]},
    {'sha':'f'*40,'siblings':[{'rfilename':'LICENSE'}]*2},
])
def test_document_rejects_missing_or_ambiguous_revision(remote_catalog,monkeypatch,payload):
    monkeypatch.setattr(updates,'_json',lambda url:payload)
    with pytest.raises(ValueError):updates.read_remote_document('Org/Video','f'*40,'LICENSE')


def test_document_network_error_is_not_empty_evidence(remote_catalog,monkeypatch):
    document_metadata(monkeypatch,b'Terms')
    class Opener:
        def open(self,*args,**kwargs):raise updates.urllib.error.URLError('offline')
    monkeypatch.setattr(updates.urllib.request,'build_opener',lambda *args:Opener())
    with pytest.raises(ValueError,match='documento oficial'):
        updates.read_remote_document('Org/Video','f'*40,'LICENSE')


def test_document_offline_round_trip_and_listing_never_access_network(remote_catalog,monkeypatch):
    from lib.production_agent import LocalAgent
    raw=b'Historic terms'
    document_metadata(monkeypatch,raw)
    document_transport(monkeypatch,raw)
    live=updates.read_remote_document('Org/Video','f'*40,'LICENSE')
    assert live['cache_saved'] is True and live['retrieval']=='online'
    monkeypatch.setattr(updates,'_json',lambda url:pytest.fail('Offline call reached network'))
    worker=LocalAgent.__new__(LocalAgent)
    args={'identifier':'Org/Video','revision':'f'*40,'filename':'LICENSE','offline':True}
    cached=worker.dispatch('update_read_document',args)
    assert cached['text']==live['text'] and cached['sha256']==live['sha256']
    assert cached['checked_at']==live['checked_at']
    assert cached['retrieval']=='offline_cache' and cached['network_checked'] is False
    assert cached['update_allowed'] is False
    listing=worker.dispatch('update_cached_documents',{'identifier':'Org/Video'})
    assert listing['total']==1 and listing['rows'][0]['remote_revision']=='f'*40
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.get('/api/studio/updates/documents',params={'identifier':'Org/Video'}).json()['total']==1
    response=client.get('/api/studio/updates/document',params=args)
    assert response.status_code==200 and response.json()['network_checked'] is False
    with pytest.raises(ValueError):updates.read_remote_document('Org/Video','e'*40,'LICENSE',True)


def test_document_cache_is_idempotent_and_online_does_not_hide_failures(remote_catalog,monkeypatch):
    document_metadata(monkeypatch,b'Terms');document_transport(monkeypatch,b'Terms')
    updates.read_remote_document('Org/Video','f'*40,'LICENSE')
    updates.read_remote_document('Org/Video','f'*40,'LICENSE')
    assert updates.cached_documents('Org/Video')['total']==1
    def fail(url):raise ValueError('offline')
    monkeypatch.setattr(updates,'_json',fail)
    with pytest.raises(ValueError,match='offline'):updates.read_remote_document('Org/Video','f'*40,'LICENSE')
    assert updates.read_remote_document('Org/Video','f'*40,'LICENSE',True)['text']=='Terms'


@pytest.mark.parametrize('change',[
    {'text':'Altered'}, {'remote_revision':'e'*40}, {'bytes_read':True},
    {'checked_at':'invalid'}, {'git_blob_verified':'true'},
])
def test_corrupt_cache_is_rejected_and_omitted(remote_catalog,monkeypatch,change):
    document_metadata(monkeypatch,b'Terms');document_transport(monkeypatch,b'Terms')
    updates.read_remote_document('Org/Video','f'*40,'LICENSE')
    path=updates._document_cache_path('Org/Video','f'*40,'LICENSE')
    record=studio.read_json(path);record.update(change);studio.save_json(path,record)
    with pytest.raises(ValueError):updates.read_remote_document('Org/Video','f'*40,'LICENSE',True)
    report=updates.cached_documents('Org/Video')
    assert report['total']==0 and report['invalid_records']==1


def test_cache_save_failure_preserves_live_evidence(remote_catalog,monkeypatch):
    document_metadata(monkeypatch,b'Terms');document_transport(monkeypatch,b'Terms')
    def deny(*args):raise OSError('disk full')
    monkeypatch.setattr(studio,'save_json',deny)
    result=updates.read_remote_document('Org/Video','f'*40,'LICENSE')
    assert result['text']=='Terms' and result['cache_saved'] is False
    assert 'disk full' in result['cache_warning']
    with pytest.raises(ValueError):updates.read_remote_document('Org/Video','f'*40,'LICENSE',True)


def test_cache_capacity_and_pagination(remote_catalog,monkeypatch):
    monkeypatch.setattr(updates,'_CACHE_LIMIT',2)
    document_metadata(monkeypatch,b'Terms');document_transport(monkeypatch,b'Terms')
    updates.read_remote_document('Org/Video','f'*40,'LICENSE')
    original=updates._json
    monkeypatch.setattr(updates,'_json',lambda url:{**original(url),'sha':'e'*40})
    updates.read_remote_document('Org/Video','e'*40,'LICENSE')
    assert updates.cached_documents('Org/Video',0,1)['next_offset']==1
    assert len(updates.cached_documents('Org/Video',1,1)['rows'])==1
    monkeypatch.setattr(updates,'_json',lambda url:{**original(url),'sha':'d'*40})
    result=updates.read_remote_document('Org/Video','d'*40,'LICENSE')
    assert result['cache_saved'] is False and 'cache_warning' in result
    assert updates.cached_documents('Org/Video')['total']==2


def test_update_plan_keeps_original_and_pins_separate_candidate(remote_catalog,monkeypatch):
    from lib.production_agent import LocalAgent
    urls=[]
    def fetch(url):
        urls.append(url)
        return {'sha':'f'*40,'siblings':[{'rfilename':'nested/model.safetensors','size':9,'lfs':{'sha256':'c'*64}}]}
    monkeypatch.setattr(updates,'_json',fetch)
    plan=updates.prepare_file_update('Org/Video',0,'f'*40)
    assert plan['status']=='candidate_plan_prepared'
    assert plan['original_destination']=='D:/models/model.safetensors'
    assert plan['candidate']['destination'].startswith('D:/models/.openmontage-updates/'+'f'*40+'/')
    assert plan['candidate']['destination'].endswith('/model.safetensors')
    assert plan['candidate']['url']=='https://huggingface.co/Org/Video/resolve/'+'f'*40+'/nested/model.safetensors'
    assert plan['candidate']['sha256']=='c'*64 and plan['additional_storage_bytes_at_least']==9
    assert plan['update_allowed'] is False and plan['free_space_verified'] is False
    assert plan['downloads_started']==plan['files_changed']==plan['local_files_read']==0
    assert plan['rollback']['configuration_changed'] is False
    worker=LocalAgent.__new__(LocalAgent)
    args={'identifier':'Org/Video','index':0,'revision':'f'*40}
    assert worker.dispatch('update_prepare_plan',args)['candidate']==plan['candidate']
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.get('/api/studio/updates/plan',params=args).json()['candidate']==plan['candidate']
    assert all('/revision/'+'f'*40 in url for url in urls)


@pytest.mark.parametrize('metadata,status',[
    (None,'blocked_missing_remote_file'),
    ({'size':7,'lfs':{'sha256':'b'*64}},'catalog_content_unchanged'),
    ({'size':9},'blocked_insufficient_remote_metadata'),
    ({'lfs':{'sha256':'c'*64}},'blocked_insufficient_remote_metadata'),
    ({'size':0,'lfs':{'sha256':'c'*64}},'blocked_insufficient_remote_metadata'),
])
def test_update_plan_does_not_propose_unverifiable_candidates(remote_catalog,monkeypatch,metadata,status):
    monkeypatch.setattr(updates,'_json',lambda url:{'sha':'f'*40,'siblings':[] if metadata is None else [
        {'rfilename':'nested/model.safetensors',**metadata}]})
    result=updates.prepare_file_update('Org/Video',0,'f'*40)
    assert result['status']==status and 'candidate' not in result
    assert result['files_changed']==0


def test_update_plan_requires_explicit_commit_before_network(remote_catalog,monkeypatch):
    monkeypatch.setattr(updates,'_json',lambda url:pytest.fail('Unexpected network'))
    for revision in (None,'main','a'*39):
        with pytest.raises(ValueError):updates.prepare_file_update('Org/Video',0,revision)


@pytest.fixture
def candidate_catalog(remote_catalog,monkeypatch):
    original=studio.REPO_ROOT/'installed/model.safetensors'
    original.parent.mkdir();original.write_bytes(b'original')
    manifest_path=studio.REPO_ROOT/'docs/models/test.json'
    manifest=studio.read_json(manifest_path)
    manifest['files'][0]['destination']=str(original)
    studio.save_json(manifest_path,manifest)
    digest=hashlib.sha256(b'candidate').hexdigest()
    monkeypatch.setattr(updates,'_json',lambda url:{'sha':'f'*40,'siblings':[
        {'rfilename':'nested/model.safetensors','size':9,'lfs':{'sha256':digest}}]})
    plan=updates.prepare_file_update('Org/Video',0,'f'*40)
    candidate=Path(plan['candidate']['destination'])
    candidate.parent.mkdir(parents=True)
    return original,candidate


@pytest.mark.parametrize('content,status',[
    (b'candidate','candidate_matches_remote'),(b'wrongdata','candidate_differs_remote'),
    (b'incomplete','candidate_differs_remote'),(None,'missing_or_link'),
])
def test_candidate_integrity_preserves_original(candidate_catalog,content,status):
    original,candidate=candidate_catalog
    if content is not None:candidate.write_bytes(content)
    result=updates.check_candidate('Org/Video',0,'f'*40)
    assert result['status']==status
    assert result['candidate_destination']==str(candidate).replace('\\','/')
    assert result['update_allowed'] is False and result['files_changed']==0
    assert original.read_bytes()==b'original'
    assert not (studio.CONFIG_DIR/'settings.json').exists()


def test_candidate_api_and_agent_check_same_file(candidate_catalog):
    from lib.production_agent import LocalAgent
    original,candidate=candidate_catalog;candidate.write_bytes(b'candidate')
    args={'identifier':'Org/Video','index':0,'revision':'f'*40}
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.get('/api/studio/updates/candidate-check',params=args)
    assert response.status_code==200,response.text
    assert response.json()['status']=='candidate_matches_remote'
    worker=LocalAgent.__new__(LocalAgent)
    assert worker.dispatch('update_check_candidate',args)['local_sha256']==response.json()['local_sha256']
    assert original.read_bytes()==b'original'


def test_candidate_growth_is_bounded(candidate_catalog,monkeypatch):
    original,candidate=candidate_catalog;candidate.write_bytes(b'candidate')
    original_open=Path.open
    def growing(path,*args,**kwargs):
        if path==candidate:return io.BytesIO(b'candidate'+b'x'*100)
        return original_open(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',growing)
    result=updates.check_candidate('Org/Video',0,'f'*40)
    assert result['status']=='changed_during_check' and result['bytes_read']==10


def test_candidate_rejects_linked_parent(candidate_catalog):
    original,candidate=candidate_catalog
    folder=candidate.parent;folder.rmdir()
    target=folder.parent/'linked';target.mkdir()
    try:folder.symlink_to(target,target_is_directory=True)
    except OSError:pytest.skip('Directory symlink unavailable on this host')
    result=updates.check_candidate('Org/Video',0,'f'*40)
    assert result['status']=='candidate_parent_is_link' and result['bytes_read']==0


def test_candidate_without_plan_does_not_read_local_files(remote_catalog,monkeypatch):
    monkeypatch.setattr(updates,'_json',lambda url:{'sha':'f'*40,'siblings':[]})
    monkeypatch.setattr(updates,'_check_local_entry',lambda *args:pytest.fail('No candidate may be read'))
    result=updates.check_candidate('Org/Video',0,'f'*40)
    assert result['status']=='not_checked_no_candidate' and result['bytes_read']==0
