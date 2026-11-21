"""Diagnostic execution contracts. Fixture WAVs do not certify real TTS quality."""
import math
import struct
import wave
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from lib import model_adapters as adapters
from lib import model_validation as checks
from tools.base_tool import ToolRuntime,ToolTier,ToolResult

@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(agent,'ACTIVE',{})
    return tmp_path


def wav(path,silence=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000)
        f.writeframes(b''.join(struct.pack('<h',0 if silence else int(3000*math.sin(i/12))) for i in range(24000)))


def prepare(tmp,monkeypatch,transcribe=True,asr_ready=True,asr_text='Hola mundo'):
    from tests.tools.test_model_adapters import fake_model
    model=fake_model(tmp,'kokoro');whisper=fake_model(tmp,'faster-whisper')
    adapters.configure('kokoro',{'model_dir':str(model)})
    adapters.configure('faster-whisper',{'model_dir':str(whisper)})
    identifier='check-123456abcdef';path=checks.root()/identifier;path.mkdir(parents=True)
    checks.save(path,id=identifier,created_at=studio.now(),status='running',request={'text':'Hola mundo','voice':'ef_dora','device':'cpu','transcribe':transcribe},models={})
    def diagnostic(family):
        return {'ready':family=='kokoro' or asr_ready,'model_dir':str(model if family=='kokoro' else whisper),'available_voices':['ef_dora'],'problems':[] if asr_ready else ['Falta runtime ASR']}
    monkeypatch.setattr(adapters,'diagnostics',diagnostic)
    def synth(inputs):
        output=__import__('pathlib').Path(inputs['output_dir'])/'voice.wav';wav(output)
        return ToolResult(success=True,data={'outputs':[str(output)]})
    def transcribe_fn(inputs):
        studio.save_json(__import__('pathlib').Path(inputs['output_dir'])/'result.json',{'segments':[{'start':0,'end':1,'text':asr_text,'words':[{'start':0,'end':1,'word':asr_text}]}]})
        return ToolResult(success=True)
    def tool(fn):return SimpleNamespace(runtime=ToolRuntime.LOCAL,tier=ToolTier.CORE,estimate_cost=lambda inputs:0,execute=fn)
    registry=SimpleNamespace(get=lambda name:tool(synth if name=='model_kokoro' else transcribe_fn))
    return identifier,path,model,registry


def test_wav_metrics_and_silence(isolated):
    path=isolated/'sample.wav';wav(path)
    result=checks.measure_wav(path)
    assert result['duration_seconds']==1 and result['sample_rate']==24000
    assert 0<result['rms']<result['peak']<1
    wav(path,silence=True)
    with pytest.raises(ValueError,match='audible'):checks.measure_wav(path)


def test_real_diagnostic_path_preserves_files_and_separate_human_review(isolated,monkeypatch):
    identifier,path,model,registry=prepare(isolated,monkeypatch)
    checks.execute(identifier,registry)
    report=checks.read(identifier)
    assert report['status']=='review_required'
    assert report['audio']['decoded']
    assert report['transcription']['comparison']['word_error_rate']==0
    assert not report.get('human_review')
    evidence=checks.current_evidence('kokoro',model)
    assert evidence['scope']=='single_controlled_sample' and evidence['quality_review'] is None
    checks.review(identifier,{'accepted':True,'comment':'Escuchado en prueba de interfaz'})
    assert checks.read(identifier)['status']=='reviewed'
    assert checks.current_evidence('kokoro',model)['quality_review']['accepted']
    weights=model/'kokoro-v1_0.pth';weights.write_bytes(b'changed fixture weights')
    assert checks.current_evidence('kokoro',model) is None


def test_missing_asr_is_partial_and_keeps_voice(isolated,monkeypatch):
    identifier,path,model,registry=prepare(isolated,monkeypatch,asr_ready=False)
    checks.execute(identifier,registry);report=checks.read(identifier)
    assert report['status']=='partial' and report['transcription']['status']=='blocked'
    assert (path/'voice/voice.wav').is_file()
    assert checks.current_evidence('kokoro',model)


def test_bad_asr_does_not_erase_successful_audio_evidence(isolated,monkeypatch):
    identifier,path,model,registry=prepare(isolated,monkeypatch,asr_text='')
    checks.execute(identifier,registry)
    report=checks.read(identifier)
    assert report['status']=='partial'
    assert 'faster-whisper' not in report['models']
    assert checks.current_evidence('kokoro',model)


def test_wer_is_measurement_not_a_quality_pass():
    result=checks.compare_transcript('¡Hola, corazón!','hola corazon')
    assert result['word_error_rate']==0 and result['quality_pass'] is None
    assert checks.compare_transcript('uno dos','tres cuatro cinco')['word_error_rate']>1


def test_blocked_setup_never_claims_inference(isolated,monkeypatch):
    identifier,path,model,registry=prepare(isolated,monkeypatch)
    monkeypatch.setattr(adapters,'diagnostics',lambda family:{'ready':False,'problems':['Faltan pesos']})
    checks.execute(identifier,registry)
    report=checks.read(identifier)
    assert report['status']=='blocked' and not report['models']
    assert not report.get('audio_url')


def test_http_validation_review_audio_and_input_contract(isolated,monkeypatch):
    identifier,path,model,registry=prepare(isolated,monkeypatch,transcribe=False)
    checks.execute(identifier,registry)
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert len(client.get('/api/studio/validations').json())==1
    assert client.get('/api/studio/validations/'+identifier+'/audio').headers['content-type']=='audio/wav'
    assert client.post('/api/studio/validations/'+identifier+'/review',json={'accepted':False}).status_code==200
    assert client.get('/api/studio/validations/'+identifier).json()['status']=='rejected'
    assert client.post('/api/studio/validations',json={'text':'hola','voice':'../../private'}).status_code==400
    assert client.post('/api/studio/validations',json={},headers={'Origin':'https://evil.invalid'}).status_code==403
    agent.ACTIVE['busy']=(None,None)
    assert client.post('/api/studio/validations',json={'text':'Hola','voice':'ef_dora'}).status_code==400
    assert client.get('/api/studio/validations/check-000000000000/audio').status_code==404


def test_report_without_live_worker_is_interrupted(isolated,monkeypatch):
    identifier,path,model,registry=prepare(isolated,monkeypatch)
    assert checks.read(identifier)['status']=='interrupted'
    with pytest.raises(ValueError):checks.review(identifier,{'accepted':True})


def test_diagnostics_exposes_only_matching_measured_evidence(isolated,monkeypatch):
    original=adapters.diagnostics
    identifier,path,model,registry=prepare(isolated,monkeypatch,transcribe=False)
    checks.execute(identifier,registry)
    monkeypatch.setattr(adapters,'diagnostics',original)
    monkeypatch.setattr(adapters,'dependency_probe',lambda *a:{module:True for module in a[1]})
    info=adapters.diagnostics('kokoro')
    assert info['inference_verified'] and info['validation_evidence']['quality_review'] is None
    (path/'voice/voice.wav').unlink()
    assert not adapters.diagnostics('kokoro')['inference_verified']
