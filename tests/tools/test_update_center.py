import pytest
import hashlib
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
