"""Only the new encoded-final-mix measurement API/cache; no prior audio suites."""
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio,studio_editor as edit,studio_mix_meter as meter
from tests.backlot.test_studio_editor import project,command,add

LOG = b'''[astats] Overall
[astats] Peak level dB: -3.000
[astats] RMS level dB: -18.250
[astats] Number of samples: 480000
Summary:
  Integrated loudness:
    I: -17.2 LUFS
    Threshold: -27.2 LUFS
  Loudness range:
    LRA: 2.4 LU
  True peak:
    Peak: -2.5 dBFS
'''


@pytest.fixture
def ready(project,monkeypatch):
    pid,key,path=project;add(pid,key);rendered=path.parent/'render.mp4';rendered.write_bytes(b'fake rendered audio fixture')
    studio.save_json(studio.project_path(pid)/'artifacts/manual_render.json',{'status':'completed','path':'assets/render.mp4',
        'sha256':'a'*64,'render_sha256':edit.state(pid)['render_sha256'],'duration':10,'preview':False})
    engine=path.parent/'ffmpeg.exe';engine.write_bytes(b'fake engine identity')
    monkeypatch.setattr(meter,'require_media',lambda _:str(engine));monkeypatch.setattr(meter,'ACTIVE',{})
    calls=[]
    def execute(*args,**kwargs):calls.append(args[0]);return SimpleNamespace(returncode=0,stderr=LOG)
    monkeypatch.setattr(meter,'execute',execute)
    class Inline:
        def __init__(self,target,args,**_):self.target=target;self.args=args
        def start(self):self.target(*self.args)
    monkeypatch.setattr(meter.threading,'Thread',Inline)
    return pid,rendered,calls


def request(pid,rid='meter-test',**kwargs):return {'request_id':rid,'revision':edit.state(pid)['revision'],**kwargs}


def test_cached_final_mix_provenance_recovery_without_edl_change(ready):
    pid,path,calls=ready;before=edit.state(pid);data=request(pid)
    value=meter.start(pid,data)
    assert value['status']=='completed' and value['current'] and not value['cache_hit']
    assert value['metrics']['rms_dbfs']==-18.25 and value['metrics']['true_peak_dbfs']==-2.5
    assert meter.start(pid,data)['request_id']==data['request_id'] and len(calls)==1
    assert meter.start(pid,request(pid,'another-request'))['cache_hit'] and len(calls)==1
    assert edit.state(pid)==before
    assert '-f' in calls[0] and calls[0][-2:]==['null','-']
    with pytest.raises(edit.Conflict):meter.start(pid,{**data,'start_seconds':1})
    command(pid,'clip',id=before['edit_decisions']['cuts'][0]['id'],gain=.5)
    assert not meter.status(pid,data['request_id'])['current']
    with pytest.raises(edit.Conflict):meter.start(pid,request(pid,'stale-render'))


@pytest.mark.parametrize('bad',[{'start_seconds':True},{'duration_seconds':121},{'start_seconds':11},
    {'request_id':'../../escape'},{'revision':-1},{'duration_seconds':float('inf')},{'expression':'evil'}])
def test_invalid_interval_and_revision_never_decode(ready,bad):
    pid,_,calls=ready
    with pytest.raises((ValueError,edit.Conflict)):meter.start(pid,{**request(pid),**bad})
    assert not calls and pid not in edit.EXPORTING


def test_partial_coverage_and_changed_render_invalidates_receipt(ready):
    pid,path,calls=ready
    # Matching interval sample count, independent of full render duration.
    def execute(*args,**kwargs):calls.append(args[0]);return SimpleNamespace(returncode=0,stderr=LOG.replace(b'480000',b'96000'))
    from unittest.mock import patch
    with patch.object(meter,'execute',execute):value=meter.start(pid,request(pid,start_seconds=2,duration_seconds=2))
    assert value['coverage']['partial'] and value['coverage']['start_seconds']==2
    path.write_bytes(b'changed render')
    assert not meter.status(pid,'meter-test')['current']


def test_decode_error_and_short_read_do_not_cache(ready,monkeypatch):
    pid,_,calls=ready
    monkeypatch.setattr(meter,'execute',lambda *a,**kw:SimpleNamespace(returncode=1,stderr=b'bad decoder'))
    value=meter.start(pid,request(pid));assert value['status']=='failed' and 'bad decoder' in value['error']
    monkeypatch.setattr(meter,'execute',lambda *a,**kw:SimpleNamespace(returncode=0,stderr=LOG.replace(b'480000',b'4800')))
    value=meter.start(pid,request(pid,'short'));assert value['status']=='failed' and 'intervalo' in value['error']
    assert not list((studio.project_path(pid)/'artifacts/mix_meter/cache').glob('*.json'))


def test_cancel_before_decode_and_restart_interruption(ready,monkeypatch):
    pid,_,calls=ready;pending=[]
    class Deferred:
        def __init__(self,target,args,**_):self.target=target;self.args=args
        def start(self):pending.append(self)
    monkeypatch.setattr(meter.threading,'Thread',Deferred)
    def execute(command,work,control,**kw):control.check();raise AssertionError('Must not decode')
    monkeypatch.setattr(meter,'execute',execute)
    assert meter.start(pid,request(pid))['status']=='running' and pid in edit.EXPORTING
    assert meter.cancel(pid,'meter-test')['status']=='cancelling'
    pending[0].target(*pending[0].args)
    assert meter.status(pid,'meter-test')['status']=='cancelled' and pid not in edit.EXPORTING
    meter.start(pid,request(pid,'interrupted'));meter.ACTIVE.clear();edit.EXPORTING.discard(pid)
    assert meter.status(pid,'interrupted')['status']=='interrupted'


def test_parser_silence_and_missing_metrics():
    metrics=meter.parse(LOG.replace(b'-3.000',b'-inf').replace(b'-18.250',b'-inf').replace(b'-2.5',b'-inf').replace(b'-17.2',b'-70.0'))
    assert metrics['rms_dbfs'] is None and metrics['true_peak_dbfs'] is None and metrics['loudness_below_gate']
    with pytest.raises(ValueError):meter.parse(b'no usable summary')


def test_agent_api_start_status_and_receipt_share_cache(ready,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,_,calls=ready;client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def transport(path,data=None):
        r=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert r.status_code==200,r.text
        return r.json()
    monkeypatch.setattr(bridge,'request',transport)
    assert 'mix_meter' in transport('capabilities')['commands']
    tool=bridge.StudioProjectEdit();result=tool.execute({'project_id':pid,'action':'mix_meter_start','request_id':'agent-meter','revision':edit.state(pid)['revision']})
    assert result.success and result.data['status']=='completed'
    result=tool.execute({'project_id':pid,'action':'mix_meter_status','request_id':'agent-meter'})
    assert result.success and result.data['origin']=='agent' and len(calls)==1
    transport(pid+'/mix-meter',request(pid,'user-receipt'))
    result=tool.execute({'project_id':pid,'action':'mix_meter_status','request_id':'user-receipt'})
    assert result.data['origin']=='agent' and result.data['measurement_origin']=='user' and len(calls)==1


def test_cancel_during_owned_decode_persists_confirmed_stop(ready,monkeypatch):
    pid,_,_=ready
    def execute(command,work,control,**kwargs):
        control.process=SimpleNamespace(poll=lambda:0);control.stopped=True
        assert meter.cancel(pid,'meter-test')['status']=='cancelling'
        control.check()
    monkeypatch.setattr(meter,'execute',execute)
    job=meter.start(pid,request(pid))
    assert job['status']=='cancelled' and job['decoder_started'] and job['process_stopped']
    assert job['cancel_requested_at']
    assert 'metrics' not in job and pid not in edit.EXPORTING


def test_thread_start_failure_releases_project_with_failed_receipt(ready,monkeypatch):
    pid,_,_=ready
    class Broken:
        def __init__(self,**kwargs):pass
        def start(self):raise RuntimeError('test thread failure')
    monkeypatch.setattr(meter.threading,'Thread',Broken)
    with pytest.raises(ValueError,match='No se pudo iniciar'):meter.start(pid,request(pid))
    assert meter.status(pid,'meter-test')['status']=='failed' and pid not in edit.EXPORTING


def test_unconfirmed_child_exit_retains_resource_guard(ready,monkeypatch):
    pid,_,_=ready
    def execute(command,work,control,**kwargs):
        control.process=SimpleNamespace(poll=lambda:None)
        return SimpleNamespace(returncode=1,stderr=b'fake owned decoder exit failure')
    monkeypatch.setattr(meter,'execute',execute)
    job=meter.start(pid,request(pid))
    assert job['status']=='failed' and not job['process_stopped'] and pid in edit.EXPORTING
    assert pid in meter.ACTIVE and 'metrics' not in job
