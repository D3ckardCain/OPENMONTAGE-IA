"""New Qwen variant/plan checks only. Never import torch, load weights or synthesize."""
import json
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from lib import qwen_tts_local as qwen, studio_editor as editor, production_studio as studio
from lib.hyperframes_staging import identity


@pytest.fixture
def resource(tmp_path,monkeypatch):
    model=tmp_path/'model';model.mkdir();(model/'speech_tokenizer').mkdir()
    main=model/'model.safetensors';main.write_bytes(b'fixture-main')
    token=model/'speech_tokenizer/model.safetensors';token.write_bytes(b'fixture-token')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    monkeypatch.setitem(qwen.PROFILES,'voice-design',{**qwen.PROFILES['voice-design'],'main_bytes':main.stat().st_size,'main_sha256':sha(main)})
    monkeypatch.setattr(qwen,'TOKEN_BYTES',token.stat().st_size);monkeypatch.setattr(qwen,'TOKEN_SHA',sha(token))
    cache=tmp_path/'verified.json';cache.write_text(json.dumps({str(p.resolve()):dict(identity=identity(p),sha256=sha(p)) for p in [main,token]}));monkeypatch.setattr(qwen,'HASH_CACHE',cache)
    (model/'config.json').write_text(json.dumps(dict(tts_model_type='voice_design',tts_model_size='1b7')))
    for name in ['generation_config.json','preprocessor_config.json','tokenizer_config.json','vocab.json','merges.txt','speech_tokenizer/config.json','speech_tokenizer/configuration.json','speech_tokenizer/preprocessor_config.json']:(model/name).write_text('{}')
    return model,cache


def test_verified_profile_diagnostic_reads_no_weights(resource,monkeypatch):
    model,_=resource;original=Path.open
    def guarded(path,*args,**kw):
        assert path.suffix!='.safetensors','Diagnostic must not read model weights'
        return original(path,*args,**kw)
    monkeypatch.setattr(Path,'open',guarded)
    result=qwen.resources('voice-design',model)
    assert result['resources_verified'] and not result['weights_read']


@pytest.mark.parametrize('case',['variant','size','identity','hash','token_config'])
def test_incomplete_or_wrong_variant_not_available(resource,case):
    model,cache=resource
    if case=='variant':(model/'config.json').write_text(json.dumps(dict(tts_model_type='custom_voice',tts_model_size='1b7')))
    if case=='size':(model/'model.safetensors').write_bytes(b'changed')
    if case in ('identity','hash'):
        rows=json.loads(cache.read_text());row=rows[str((model/'model.safetensors').resolve())]
        if case=='identity':row['identity'][-1]-=1
        else:row['sha256']='f'*64
        cache.write_text(json.dumps(rows))
    if case=='token_config':(model/'speech_tokenizer/config.json').unlink()
    result=qwen.resources('voice-design',model)
    assert not result['resources_verified'] and result['problems']


def test_configuration_json_does_not_replace_config(resource):
    model,_=resource;(model/'config.json').unlink()
    result=qwen.resources('voice-design',model)
    assert any('configuration.json no lo sustituye' in p for p in result['problems'])


def test_request_plan_persist_undo_redo_no_synthesis(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    value=editor.create('Qwen plan QA');pid=value['project_id'];before=value['edit_decisions']
    data=dict(operation='qwen_tts_plan',revision=0,profile='voice-design',language='es',text='Texto sintético.',instruction='Voz adulta clara.')
    with patch('subprocess.Popen') as spawn:
        applied=editor.command(pid,data)['edit_decisions'];assert applied['qwen_tts_plan']['language']=='Spanish'
        assert not applied['qwen_tts_plan']['synthesized']
        assert editor.command(pid,dict(operation='undo',revision=1))['edit_decisions']==before
        assert editor.command(pid,dict(operation='redo',revision=2))['edit_decisions']==applied
        assert editor.state(pid)['edit_decisions']==applied
    spawn.assert_not_called()


def test_base_requires_authorized_wav_reference_without_switching_variant():
    edl=editor._empty();edl['sources']={'r':dict(kind='audio',path='assets/ref.wav',sha256='a'*64)}
    data=dict(profile='qwen-tts-17b-base',language='es',text='Prueba',reference_source_id='r',reference_text='Referencia')
    with pytest.raises(ValueError,match='autorización'):qwen.save_plan(edl,data)
    data['reference_authorized']=True;qwen.save_plan(edl,data)
    assert edl['qwen_tts_plan']['profile']=='qwen-tts-17b-base'
    assert edl['qwen_tts_plan']['reference_sha256']=='a'*64


def test_worker_rejects_wrong_base_before_torch_import(tmp_path):
    from lib.model_adapter_worker import run
    (tmp_path/'config.json').write_text(json.dumps(dict(tts_model_type='custom_voice',tts_model_size='1b7')))
    with pytest.raises(ValueError,match='Base1.7B'):
        run(dict(family='qwen-tts-17b-base',model_dir=str(tmp_path),output_dir=str(tmp_path/'out'),inputs={'reference_authorized':True}))


@pytest.mark.parametrize("target", ["cache", "config"])
def test_malformed_diagnostic_json_reports_clear_problem(resource,target):
    model,cache=resource
    (cache if target=="cache" else model/"config.json").write_text("{unfinished")
    result=qwen.resources("voice-design",model)
    assert not result["resources_verified"] and result["problems"]


def test_cpu_memory_preflight_blocks_without_loading_weights(resource):
    model,_=resource
    low=qwen.cpu_memory_preflight(model,1)
    high=qwen.cpu_memory_preflight(model,100*1024**3)
    assert not low["allowed"] and high["allowed"]
    assert not low["model_loaded"] and low["estimate_not_peak_measurement"]


def test_backend_identity_detects_qwen_helper_and_catalog_changes(tmp_path):
    from backlot.studio_identity import fingerprint
    for name in ["lib/qwen_tts_local.py","lib/model_adapter_worker.py","docs/models/qwen17.json"]:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text("first")
        before=fingerprint(tmp_path)
        path.write_text("changed")
        assert fingerprint(tmp_path)["sha256"]!=before["sha256"]
