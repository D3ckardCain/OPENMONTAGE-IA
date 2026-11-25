"""E05 synthetic receipt/provider-count tests. Never load or synthesize a voice."""
import hashlib
import json
import threading
import wave
from pathlib import Path
from types import SimpleNamespace
import pytest
from lib import studio_piper_jobs as jobs, studio_piper as piper, studio_editor as editor

KEY='a'*32
DATA=dict(request_id=KEY,voice='test-local',speaker_id=0,text='Synthetic request, no real speech.')


@pytest.fixture
def rig(monkeypatch,tmp_path):
    calls=[]
    version=['resource-v1']
    project=tmp_path/'project'
    project.mkdir()
    monkeypatch.setattr(jobs.studio,'project_path',lambda pid:project if pid=='qa' else (_ for _ in ()).throw(ValueError('wrong project')))
    monkeypatch.setattr(jobs,'_fingerprint',lambda inputs:hashlib.sha256(json.dumps([inputs,version],sort_keys=True).encode()).hexdigest())
    def provider(text,voice,speaker,output):
        calls.append((text,voice,speaker))
        output.parent.mkdir(parents=True,exist_ok=True)
        with wave.open(str(output),'wb') as stream:
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(8000);stream.writeframes(b'\x01\x00'*80)
        receipt=dict(output=str(output),frames=80,sample_rate=8000,seconds=.01,speaker_id=speaker,
                     text_sha256=hashlib.sha256(text.encode()).hexdigest(),wave_sha256=jobs.checksum(output),
                     provenance=dict(id=voice),listening_validated=False)
        jobs.studio.save_json(Path(str(output)+'.json'),receipt)
        return receipt
    monkeypatch.setattr(piper,'synthesize',provider)
    jobs.ACTIVE.clear()
    yield SimpleNamespace(project=project,calls=calls,version=version,provider=provider)
    jobs.ACTIVE.clear()


def test_lost_http_response_reuses_exact_receipt(rig):
    first=jobs.preview('qa',DATA)  # Caller deliberately discards this response.
    result=jobs.preview('qa',DATA)
    assert result['reused'] and result['relative_path']==first['relative_path']
    assert len(rig.calls)==1
    assert jobs.status('qa',KEY)['state']=='completed'
    assert len(list((rig.project/'assets/audio').glob('*.wav')))==1


@pytest.mark.parametrize('field,value',[('text','Changed text'),('voice','another-voice'),('speaker_id',1)])
def test_request_id_never_changes_inputs(rig,field,value):
    jobs.preview('qa',DATA)
    with pytest.raises(editor.Conflict):jobs.preview('qa',{**DATA,field:value})
    assert len(rig.calls)==1


@pytest.mark.parametrize('damage',['wav','receipt','runtime','model'])
def test_invalidated_completion_never_reruns(rig,damage):
    result=jobs.preview('qa',DATA)
    output=rig.project/result['relative_path']
    if damage=='wav':output.write_bytes(b'partial')
    if damage=='receipt':Path(str(output)+'.json').write_text('{',encoding='utf-8')
    if damage in ('runtime','model'):rig.version[0]=damage+'-changed'
    assert jobs.status('qa',KEY)['state']=='invalid'
    with pytest.raises(editor.Conflict):jobs.preview('qa',DATA)
    assert len(rig.calls)==1


def test_restart_after_worker_receipt_before_state_commit(rig):
    jobs.preview('qa',DATA)
    path=rig.project/'artifacts/piper_previews'/ (KEY+'.json')
    record=jobs.studio.read_json(path);record['state']='running';record.pop('receipt_sha256')
    jobs.studio.save_json(path,record);jobs.ACTIVE.clear()
    status=jobs.status('qa',KEY)
    assert status['state']=='completed' and status['result']['speaker_id']==0
    assert jobs.preview('qa',DATA)['reused'] and len(rig.calls)==1


def test_failed_provider_and_partial_are_not_retried(rig,monkeypatch):
    def failing(*args):
        rig.calls.append('failed');args[-1].parent.mkdir(parents=True,exist_ok=True);args[-1].write_bytes(b'partial')
        raise ValueError('synthetic provider failure')
    monkeypatch.setattr(piper,'synthesize',failing)
    with pytest.raises(ValueError):jobs.preview('qa',DATA)
    assert jobs.status('qa',KEY)['state']=='failed'
    with pytest.raises(editor.Conflict):jobs.preview('qa',DATA)
    assert len(rig.calls)==1


def test_interrupted_without_receipt_never_restarts(rig):
    path=rig.project/'artifacts/piper_previews'/(KEY+'.json')
    jobs.studio.save_json(path,dict(request_id=KEY,state='running',inputs={k:v for k,v in DATA.items() if k!='request_id'},
                                  fingerprint='missing',relative_path='assets/audio/piper-'+KEY+'.wav'))
    assert jobs.status('qa',KEY)['state']=='interrupted'
    with pytest.raises(editor.Conflict):jobs.preview('qa',DATA)
    assert not rig.calls


def test_cross_process_claim_without_state_never_restarts(rig):
    path=rig.project/'artifacts/piper_previews'/(KEY+'.claim');path.parent.mkdir(parents=True);path.write_text('{}')
    assert jobs.status('qa',KEY)['state']=='interrupted'
    with pytest.raises(editor.Conflict):jobs.preview('qa',DATA)
    assert not rig.calls


def test_concurrent_same_id_has_one_provider(rig,monkeypatch):
    entered=threading.Event();release=threading.Event();errors=[]
    def waiting(*args):
        entered.set();assert release.wait(3);return rig.provider(*args)
    monkeypatch.setattr(piper,'synthesize',waiting)
    def run():
        try:jobs.preview('qa',DATA)
        except Exception as exc:errors.append(exc)
    thread=threading.Thread(target=run);thread.start();assert entered.wait(3)
    try:
        assert jobs.status('qa',KEY)['state']=='running'
        with pytest.raises(editor.Conflict):jobs.preview('qa',DATA)
    finally:release.set();thread.join(3)
    assert not errors and len(rig.calls)==1


@pytest.mark.parametrize('key',['../escape','A'*32,'x'*32,'',None])
def test_bad_tokens_do_not_write_or_run(rig,key):
    with pytest.raises(ValueError):jobs.preview('qa',{**DATA,'request_id':key})
    assert not rig.calls and not list(rig.project.iterdir())


def test_actual_routes_recover_without_provider_repeat(rig):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backlot.editor_routes import create_editor_router
    async def body(request,*args):return await request.json()
    app=FastAPI();app.include_router(create_editor_router(body));client=TestClient(app)
    prefix='/api/studio/editor/qa/piper/'
    assert client.post(prefix+'preview',json=DATA).status_code==200
    assert client.get(prefix+'requests/'+KEY).json()['state']=='completed'
    assert client.post(prefix+'preview',json=DATA).json()['reused']
    assert len(rig.calls)==1


@pytest.mark.parametrize('field,value',[('text_sha256','wrong'),('provenance',None),('provenance',{'id':'other-voice'})])
def test_orphaned_receipt_must_match_request(rig,field,value):
    result=jobs.preview('qa',DATA)
    receipt_path=Path(str(rig.project/result['relative_path'])+'.json')
    receipt=jobs.studio.read_json(receipt_path);receipt[field]=value;jobs.studio.save_json(receipt_path,receipt)
    path=rig.project/'artifacts/piper_previews'/(KEY+'.json')
    record=jobs.studio.read_json(path);record.update(state='running');record.pop('receipt_sha256');jobs.studio.save_json(path,record)
    assert jobs.status('qa',KEY)['state']=='interrupted'
    with pytest.raises(editor.Conflict):jobs.preview('qa',DATA)
    assert len(rig.calls)==1


def test_real_resource_fingerprint_detects_weight_and_runtime_changes(monkeypatch,tmp_path):
    python=tmp_path/'runtime/Scripts/python.exe';python.parent.mkdir(parents=True);python.write_bytes(b'synthetic executable, never run')
    meta=tmp_path/'runtime/Lib/site-packages/piper_tts-1.8.0.dist-info/METADATA';meta.parent.mkdir(parents=True);meta.write_text('Version: 1.8.0')
    folder=tmp_path/'voices/test-local';folder.mkdir(parents=True);model=folder/'model.onnx';model.write_bytes(b'fake ONNX, never loaded')
    voice=dict(id='test-local',available=True,blocked=False,speakers={'A':0},revision='fixed',
               files=[dict(name='model.onnx',sha256=jobs.checksum(model))])
    monkeypatch.setattr(piper,'catalog',lambda:[voice])
    monkeypatch.setattr(piper,'configuration',lambda:dict(python=str(python),voices_root=str(folder.parent)))
    inputs={k:v for k,v in DATA.items() if k!='request_id'}
    first=jobs._fingerprint(inputs);assert jobs._fingerprint(inputs)==first
    meta.write_text('Version: 1.9.0');assert jobs._fingerprint(inputs)!=first
    model.write_bytes(b'modified synthetic model')
    with pytest.raises(ValueError,match='recurso'):jobs._fingerprint(inputs)


def test_partial_wav_even_with_matching_partial_checksum_is_not_complete(rig):
    result=jobs.preview('qa',DATA)
    output=rig.project/result['relative_path'];output.write_bytes(output.read_bytes()[:-10])
    receipt_path=Path(str(output)+'.json');receipt=jobs.studio.read_json(receipt_path)
    receipt['wave_sha256']=jobs.checksum(output);jobs.studio.save_json(receipt_path,receipt)
    path=rig.project/'artifacts/piper_previews'/(KEY+'.json');record=jobs.studio.read_json(path)
    record.update(state='running');record.pop('receipt_sha256');jobs.studio.save_json(path,record)
    assert jobs.status('qa',KEY)['state']=='interrupted'
    assert len(rig.calls)==1


def test_worker_writes_text_and_wave_evidence_without_real_piper(monkeypatch,tmp_path,capsys):
    import io
    import sys
    from lib import piper_worker as worker
    model=tmp_path/'model.onnx';model.write_bytes(b'fake model, not loaded')
    output=tmp_path/'sample.wav'
    class FakeVoice:
        @classmethod
        def load(cls,*args,**kwargs):return cls()
        def synthesize_wav(self,text,stream,config):
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(8000);stream.writeframes(b'\x01\x00'*80)
    monkeypatch.setitem(sys.modules,'piper',SimpleNamespace(PiperVoice=FakeVoice,SynthesisConfig=lambda **kwargs:kwargs))
    monkeypatch.setattr(worker,'block_network',lambda:None)
    monkeypatch.setattr(worker.importlib.metadata,'version',lambda name:'1.8.0')
    payload=dict(model=str(model),output=str(output),speaker_id=0,text='Synthetic test',references=dict(id='test',
                 files=[dict(name=model.name,bytes=model.stat().st_size,sha256=jobs.checksum(model))]))
    monkeypatch.setattr(sys,'stdin',io.StringIO(json.dumps(payload)))
    worker.main()
    receipt=json.loads(capsys.readouterr().out)
    assert receipt['text_sha256']==hashlib.sha256(payload['text'].encode()).hexdigest()
    assert receipt['wave_sha256']==jobs.checksum(output)
    assert jobs.studio.read_json(Path(str(output)+'.json'))==receipt


def test_agent_uses_the_same_preview_and_status_contract(rig,monkeypatch):
    from jsonschema import validate
    from tools.audio.piper_tts import PiperTTS
    from tools.base_tool import ToolStatus
    monkeypatch.setattr(PiperTTS,'get_status',lambda self:ToolStatus.AVAILABLE)
    tool=PiperTTS()
    data=dict(operation='preview',project_id='qa',request_id=KEY,model=DATA['voice'],text=DATA['text'],speaker_id=0)
    validate(data,tool.input_schema)
    assert tool.execute(data).success
    assert tool.execute(data).data['reused'] and len(rig.calls)==1
    monkeypatch.setattr(PiperTTS,'get_status',lambda self:ToolStatus.UNAVAILABLE)
    query=dict(operation='status',project_id='qa',request_id=KEY)
    validate(query,tool.input_schema)
    assert tool.execute(query).data['state']=='completed' and len(rig.calls)==1
