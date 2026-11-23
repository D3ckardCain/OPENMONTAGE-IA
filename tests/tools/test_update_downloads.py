"""Synthetic downloads only; no network, real weights or GPU execution."""
import hashlib
import io
import threading
from email.message import Message
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import update_downloads as downloads
from lib import update_center as updates


@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setattr(downloads.studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(downloads,'_LOADED_FOR',None)
    monkeypatch.setattr(downloads,'_HISTORY_WARNING',None)
    monkeypatch.setattr(downloads,'_LAST_SAVED',0.0)
    original=tmp_path/'original.safetensors';original.write_bytes(b'original')
    target=tmp_path/'staging/model.safetensors'
    raw=b'candidate';digest=hashlib.sha256(raw).hexdigest()
    plan={'candidate':{'destination':str(target),'sha256':digest,'size_bytes':len(raw),
                       'url':'https://huggingface.co/Org/Video/resolve/'+'f'*40+'/model.safetensors'}}
    monkeypatch.setattr(updates,'prepare_file_update',lambda *args:plan)
    monkeypatch.setattr(updates,'check_candidate_space',lambda *args:{'status':'space_available_for_candidate'})
    monkeypatch.setattr(updates,'_files',lambda identifier:[{}])
    monkeypatch.setattr(downloads,'_ACTIVE',None);monkeypatch.setattr(downloads,'_JOBS',{})
    job={'args':{'identifier':'Org/Video','index':0,'revision':'f'*40,'expected_sha256':digest},
         'report':{'job_id':'test','bytes_present':0},'cancel':threading.Event()}
    return original,target,raw,plan,job


def transport(monkeypatch,raw,offset=0,status=200,range_value=None):
    calls=[]
    class Response(io.BytesIO):
        pass
    def open_source(url,start):
        calls.append((url,start))
        response=Response(raw);response.status=status;response.headers=Message()
        response.headers['Content-Length']=str(len(raw))
        if range_value:response.headers['Content-Range']=range_value
        return response
    monkeypatch.setattr(downloads,'_open',open_source)
    return calls


def test_download_verified_candidate_preserves_original(setup,monkeypatch):
    original,target,raw,plan,job=setup
    calls=transport(monkeypatch,raw)
    downloads._run(job)
    assert job['report']['status']=='candidate_ready'
    assert target.read_bytes()==raw and original.read_bytes()==b'original'
    assert not target.with_name(target.name+'.part').exists()
    assert calls==[(plan['candidate']['url'],0)]


@pytest.mark.parametrize('partial',[b'cand',b''])
def test_download_resumes_partial_at_exact_offset(setup,monkeypatch,partial):
    original,target,raw,plan,job=setup;target.parent.mkdir()
    target.with_name(target.name+'.part').write_bytes(partial)
    offset=len(partial)
    calls=transport(monkeypatch,raw[offset:],status=206 if offset else 200,
                    range_value='bytes '+str(offset)+'-8/9' if offset else None)
    downloads._run(job)
    assert job['report']['status']=='candidate_ready'
    assert job['report']['resumed_from']==offset and target.read_bytes()==raw
    assert calls[0][1]==offset


@pytest.mark.parametrize('data',[b'wrongdata',b'short',b'candidate-extra'])
def test_download_never_finalizes_bad_content(setup,monkeypatch,data):
    original,target,raw,plan,job=setup
    transport(monkeypatch,data)
    downloads._run(job)
    assert job['report']['status']=='failed' and not target.exists()
    assert original.read_bytes()==b'original'


def test_range_ignored_does_not_append_wrong_data(setup,monkeypatch):
    original,target,raw,plan,job=setup;target.parent.mkdir()
    part=target.with_name(target.name+'.part');part.write_bytes(b'cand')
    transport(monkeypatch,raw,status=200)
    downloads._run(job)
    assert job['report']['status']=='failed' and part.read_bytes()==b'cand'


def test_cancel_preserves_partial(setup,monkeypatch):
    original,target,raw,plan,job=setup;target.parent.mkdir()
    part=target.with_name(target.name+'.part');part.write_bytes(b'cand')
    job['cancel'].set()
    monkeypatch.setattr(downloads,'_open',lambda *args:pytest.fail('Cancelled download must not start'))
    downloads._run(job)
    assert job['report']['status']=='cancelled' and part.read_bytes()==b'cand'


def test_existing_candidate_is_never_overwritten(setup,monkeypatch):
    original,target,raw,plan,job=setup;target.parent.mkdir();target.write_bytes(b'keep-this')
    monkeypatch.setattr(downloads,'_open',lambda *args:pytest.fail('Existing candidate must not be overwritten'))
    downloads._run(job)
    assert job['report']['status']=='failed' and target.read_bytes()==b'keep-this'


def test_finalization_on_filesystem_without_hardlinks(setup,monkeypatch):
    original,target,raw,plan,job=setup
    transport(monkeypatch,raw)
    monkeypatch.setattr(downloads.os,'link',lambda *args:(_ for _ in ()).throw(OSError('not supported')))
    downloads._run(job)
    assert job['report']['status']=='candidate_ready' and target.read_bytes()==raw


def test_unreviewed_hash_and_insufficient_space_block_before_network(setup,monkeypatch):
    original,target,raw,plan,job=setup
    monkeypatch.setattr(downloads,'_open',lambda *args:pytest.fail('Must be blocked'))
    job['args']['expected_sha256']='a'*64;downloads._run(job)
    assert job['report']['status']=='failed' and not target.parent.exists()
    job['args']['expected_sha256']=plan['candidate']['sha256']
    monkeypatch.setattr(updates,'check_candidate_space',lambda *args:{'status':'insufficient_space'})
    downloads._run(job)
    assert job['report']['status']=='failed' and not target.parent.exists()


def test_api_start_poll_cancel_and_discard_are_explicit(setup,monkeypatch):
    original,target,raw,plan,job=setup
    transport(monkeypatch,b'wrongdata')
    class Thread:
        def __init__(self,target,args,daemon):self.target=target;self.args=args
        def start(self):self.target(*self.args)
    monkeypatch.setattr(downloads,'Thread',Thread)
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.post('/api/studio/updates/downloads',json=job['args'])
    assert response.status_code==200,response.text
    jid=response.json()['job_id']
    assert client.get('/api/studio/updates/downloads/'+jid).json()['status']=='failed'
    part=target.with_name(target.name+'.part');assert part.exists()
    assert client.get('/api/studio/updates/downloads',params={key:job['args'][key] for key in ('identifier','index','revision')}).json()['rows'][0]['job_id']==jid
    assert client.post('/api/studio/updates/downloads/'+jid+'/discard-partial',json={}).json()['status']=='partial_discarded'
    assert not part.exists() and original.read_bytes()==b'original'
    assert client.post('/api/studio/updates/downloads',json={**job['args'],'path':'arbitrary'}).status_code==400
    assert client.post('/api/studio/updates/downloads',json=job['args'],headers={'Origin':'https://other.example'}).status_code==403


@pytest.mark.parametrize('url',[
    'http://huggingface.co/a','https://huggingface.co.evil.example/a','https://localhost/a',
    'https://user:password@huggingface.co/a','https://huggingface.co:8443/a',
])
def test_download_rejects_unapproved_redirect_hosts(url):
    assert not downloads._allowed_url(url)


def test_single_job_and_invalid_requests(setup,monkeypatch):
    original,target,raw,plan,job=setup
    monkeypatch.setattr(downloads,'_ACTIVE','busy')
    with pytest.raises(ValueError,match='curso'):downloads.start(**job['args'])
    for args in ({**job['args'],'revision':'main'},{**job['args'],'index':True},{**job['args'],'expected_sha256':'bad'}):
        with pytest.raises(ValueError):downloads.start(**args)


def test_interrupted_transfer_can_resume_later(setup,monkeypatch):
    original,target,raw,plan,job=setup
    class Response:
        status=200;headers=Message();headers['Content-Length']='9'
        calls=0
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self,size):
            self.calls+=1
            if self.calls==1:return raw[:3]
            raise OSError('network down')
    monkeypatch.setattr(downloads,'_open',lambda *args:Response())
    downloads._run(job)
    part=target.with_name(target.name+'.part')
    assert job['report']['status']=='failed' and part.read_bytes()==raw[:3]
    transport(monkeypatch,raw[3:],status=206,range_value='bytes 3-8/9')
    downloads._run(job)
    assert job['report']['status']=='candidate_ready' and target.read_bytes()==raw


def test_redirect_handler_rejects_outside_destination():
    request=downloads.urllib.request.Request('https://huggingface.co/Org/Video/file')
    with pytest.raises(ValueError):downloads._Redirect().redirect_request(request,None,302,'',{},'http://127.0.0.1/file')


def saved_job(setup,state='downloading'):
    original,target,raw,plan,job=setup
    jid='a'*32
    job['report'].update(job_id=jid,status=state,candidate_destination=str(target),bytes_present=4,
                         updated_at='2026-11-22T20:00:00+00:00')
    return jid,job


def write_history(job):
    downloads.studio.save_json(downloads.studio.CONFIG_DIR/'update_download_jobs.json',
                              {'version':1,'jobs':[{'args':job['args'],'report':job['report']}]})


def test_restart_recovers_interrupted_job_without_starting_network(setup,monkeypatch):
    jid,job=saved_job(setup);write_history(job)
    monkeypatch.setattr(downloads,'_open',lambda *args:pytest.fail('History must not start network'))
    report=downloads.status(jid)
    assert report['status']=='interrupted' and report['historical'] is True
    assert report['bytes_present']==4 and report['updated_at']=='2026-11-22T20:00:00+00:00'
    assert downloads._ACTIVE is None and report['update_allowed'] is False
    assert downloads.list_jobs('Org/Video',0,'f'*40)['rows'][0]['job_id']==jid


def test_restart_does_not_certify_previous_candidate_ready(setup):
    jid,job=saved_job(setup,'candidate_ready');write_history(job)
    assert downloads.status(jid)['status']=='historical_candidate_ready'


def test_recovered_job_resumes_only_explicitly(setup,monkeypatch):
    original,target,raw,plan,job=setup
    jid,job=saved_job(setup);write_history(job)
    target.parent.mkdir();target.with_name(target.name+'.part').write_bytes(raw[:4])
    calls=transport(monkeypatch,raw[4:],status=206,range_value='bytes 4-8/9')
    class Thread:
        def __init__(self,target,args,daemon):self.target=target;self.args=args
        def start(self):self.target(*self.args)
    monkeypatch.setattr(downloads,'Thread',Thread)
    assert downloads.status(jid)['status']=='interrupted' and not calls
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    result=client.post('/api/studio/updates/downloads/'+jid+'/resume',json={})
    assert result.status_code==200,result.text
    assert result.json()['status']=='candidate_ready' and result.json()['job_id']!=jid
    assert target.read_bytes()==raw and original.read_bytes()==b'original'


def test_history_route_change_blocks_resume_and_discard(setup):
    original,target,raw,plan,job=setup
    jid,job=saved_job(setup);write_history(job)
    target.parent.mkdir();partial=target.with_name(target.name+'.part');partial.write_bytes(b'cand')
    downloads.status(jid)
    plan['candidate']['destination']=str(target.parent/'other.safetensors')
    with pytest.raises(ValueError,match='ruta'):downloads.resume(jid)
    with pytest.raises(ValueError,match='ruta'):downloads.discard_partial(jid)
    assert partial.read_bytes()==b'cand'


def test_invalid_or_oversized_history_is_reported(setup):
    path=downloads.studio.CONFIG_DIR/'update_download_jobs.json';path.parent.mkdir()
    path.write_bytes(b'x'*(downloads._HISTORY_LIMIT+1))
    report=downloads.list_jobs('Org/Video',0,'f'*40)
    assert report['rows']==[] and report['history_warning']


def test_history_save_failure_keeps_current_state(setup,monkeypatch):
    jid,job=saved_job(setup)
    downloads._JOBS[jid]=job
    def deny(*args):raise OSError('disk full')
    monkeypatch.setattr(downloads.studio,'save_json',deny)
    downloads._change(job,status='failed',message='network down')
    assert job['report']['status']=='failed'
    assert downloads._HISTORY_WARNING


def test_progress_history_writes_are_throttled(setup,monkeypatch):
    jid,job=saved_job(setup);downloads._JOBS[jid]=job
    writes=[]
    monkeypatch.setattr(downloads.studio,'save_json',lambda *args:writes.append(args))
    monkeypatch.setattr(downloads.time,'monotonic',lambda:10.0)
    downloads._change(job,status='downloading')
    downloads._change(job,bytes_present=5)
    downloads._change(job,bytes_present=6)
    downloads._change(job,status='failed')
    assert len(writes)==2
