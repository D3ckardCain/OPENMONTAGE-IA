"""Preparation only: no model/code download or weights imported."""
import hashlib
import json
from pathlib import Path

import pytest
from lib import voice_preparation as voices
from lib.hyperframes_staging import identity


def test_runtime_metadata_missing_keeps_inference_unqualified(tmp_path):
    row=voices.chatterbox_runtime(tmp_path/'absent')
    assert row['installed']=={}
    assert not row['declared_core_versions_present']
    assert not row['imports_verified']


def test_runtime_metadata_accepts_cuda_suffix_without_importing_models(tmp_path):
    expected=voices.chatterbox_runtime(tmp_path)['expected']
    for name,version in expected.items():
        if name in ('torch','torchaudio'):version+='+cu124'
        dist=tmp_path/(name.replace('-','_')+'-'+version+'.dist-info')
        dist.mkdir()
        (dist/'METADATA').write_text('Metadata-Version: 2.1\nName: '+name+'\nVersion: '+version+'\n')
    row=voices.chatterbox_runtime(tmp_path)
    assert row['declared_core_versions_present']
    assert not row['loader_verified'] and not row['weights_loaded']


@pytest.fixture
def resources(tmp_path,monkeypatch):
    monkeypatch.setattr(voices,'MODEL_ROOT',tmp_path)
    monkeypatch.setattr(voices,'CACHE',tmp_path/'verified.json')
    monkeypatch.setattr(voices,'SHARED',tmp_path/'shared.json')
    for key,profile in list(voices.PROFILES.items()):
        monkeypatch.setitem(voices.PROFILES,key,{**profile,'bytes':4,'sha256':hashlib.sha256(b't3xx').hexdigest()})
        folder=tmp_path/profile['folder'];folder.mkdir()
        (folder/profile['filename']).write_bytes(b't3xx')
    monkeypatch.setattr(voices,'DECODER',dict(filename='s3gen_v3.safetensors',bytes=4,sha256=hashlib.sha256(b'decx').hexdigest()))
    mx=tmp_path/voices.PROFILES['chatterbox-es-mx-latam']['folder']
    (mx/'s3gen_v3.safetensors').write_bytes(b'decx')
    (mx/'grapheme_mtl_merged_expanded_v1.json').write_text('{}')
    rows={str(p.resolve()):{'identity':identity(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in tmp_path.rglob('*.safetensors')}
    voices.CACHE.write_text(json.dumps(rows))
    return mx


def test_metadata_only_shares_compatible_decoder_without_claiming_loader(resources,monkeypatch):
    original=Path.open
    def guarded(path,*a,**kw):
        assert path.suffix!='.safetensors','Availability must not hash or load weights'
        return original(path,*a,**kw)
    monkeypatch.setattr(Path,'open',guarded)
    rows=voices.catalog()['profiles']
    assert all(row['main']['status']=='verified_cached' for row in rows)
    assert rows[0]['decoder']['path']==rows[1]['decoder']['path']
    assert all(not row['ready'] and not row['preview_available'] and not row['weights_read'] for row in rows)
    assert any('Loader regional V3' in p for p in rows[1]['problems'])


def test_preallocated_partial_is_not_a_finished_weight(resources):
    spec=voices.PROFILES['chatterbox-es-mx-latam'];Path(str(resources/spec['filename'])+'.fdmdownload').write_bytes(b'partial')
    assert voices.catalog()['profiles'][0]['main']['status']=='download_incomplete'


def test_changed_identity_requires_explicit_verification(resources):
    spec=voices.PROFILES['chatterbox-es-mx-latam'];(resources/spec['filename']).write_bytes(b'new!')
    assert voices.catalog()['profiles'][0]['main']['status']=='unverified_or_changed'


def test_regional_request_cannot_fall_back_to_legacy_or_english(resources):
    from lib.model_adapter_worker import run
    with pytest.raises(ValueError,match='no cambia a inglés'):
        voices.guard_request({'regional_profile':'chatterbox-es-es','language':'en'})
    with pytest.raises(ValueError,match='regional no preparado'):
        run({'family':'chatterbox','model_dir':str(resources),'output_dir':str(resources/'out'),
             'inputs':{'regional_profile':'chatterbox-es-es','language':'es'}})


def test_agent_read_only_profile_action_uses_studio(monkeypatch):
    from tools.video import studio_project_edit as module
    calls=[]
    monkeypatch.setattr(module,'request',lambda path: calls.append(path) or {'profiles':[]})
    assert module.StudioProjectEdit().execute({'project_id':'qa','action':'chatterbox_profiles'}).success
    assert calls==['chatterbox/profiles']


def test_cosyvoice_standard_does_not_require_alternative_backends(tmp_path):
    from lib.model_adapters import expected_files
    required=expected_files('cosyvoice',tmp_path/'FunAudioLLM--Fun-CosyVoice3-0.5B-2512')
    assert 'CosyVoice-BlankEN/model.safetensors' in required
    assert 'flow.pt' in required and 'speech_tokenizer_v3.onnx' in required
    assert not set(voices.cosyvoice3(tmp_path)['excluded_alternatives']).intersection(required)


def test_cosyvoice_guard_before_yaml_execution_or_torch(tmp_path):
    from lib.model_adapter_worker import run
    (tmp_path/'cosyvoice3.yaml').write_text('not executed !apply:fixture')
    with pytest.raises(ValueError,match='CosyVoice3 no preparado'):
        run({'family':'cosyvoice','model_dir':str(tmp_path),'output_dir':str(tmp_path/'out'),'inputs':{}})


def test_verified_shared_tokenizer_preferred_without_copy_or_new_hash(resources,monkeypatch):
    shared=resources.parent/'shared-tokenizer.json';shared.write_text('{"fixture":true}')
    raw=shared.read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    monkeypatch.setattr(voices,'TOKENIZER_BLOB',blob)
    rows=json.loads(voices.CACHE.read_text());rows[str(shared.resolve())]={'identity':identity(shared),'git_blob_sha1':blob}
    voices.CACHE.write_text(json.dumps(rows));voices.SHARED.write_text(json.dumps({'chatterbox_tokenizer':str(shared)}))
    result=voices.catalog()['profiles']
    assert all(row['tokenizer']['path']==str(shared) and row['tokenizer']['verified_cached'] for row in result)
    assert all(not row['ready'] for row in result)


def test_cosy_auxiliary_receipts_bound_to_identity_without_yaml_read(tmp_path,monkeypatch):
    cache=tmp_path/'cache.json';monkeypatch.setattr(voices,'CACHE',cache)
    yaml=tmp_path/'cosyvoice3.yaml';yaml.write_text('!not-executed fixture')
    monkeypatch.setattr(voices,'COSY_AUX_BLOBS',{'cosyvoice3.yaml':'fixed-official-blob'})
    cache.write_text(json.dumps({str(yaml.resolve()):{'identity':identity(yaml),'git_blob_sha1':'fixed-official-blob'}}))
    original=Path.open
    def guard(path,*args,**kwargs):
        assert path!=yaml,'Diagnostic must not read or execute YAML'
        return original(path,*args,**kwargs)
    with monkeypatch.context() as context:
        context.setattr(Path,'open',guard)
        assert voices.cached_auxiliaries(tmp_path)
    yaml.write_text('changed fixture')
    assert not voices.cached_auxiliaries(tmp_path)


def test_cosy_verified_resources_still_do_not_accredit_inference(tmp_path,monkeypatch):
    monkeypatch.setattr(voices,'verified_file',lambda *a,**kw:{'status':'verified_cached'})
    monkeypatch.setattr(voices,'cached_auxiliaries',lambda folder:True)
    row=voices.cosyvoice3(tmp_path)
    assert row['all_weights_verified'] and row['auxiliaries_verified']
    assert not row['ready'] and not row['evaluation_load_performed']
    assert not row['yaml_executed'] and not row['weights_read']


def test_cosy_cpu_preflight_has_conservative_headroom_without_weight_reads():
    low=voices.cosyvoice_cpu_preflight(5*1024**3)
    high=voices.cosyvoice_cpu_preflight(16*1024**3)
    assert not low['headroom_ok'] and high['headroom_ok']
    assert low['estimated_required_available_bytes']==high['estimated_required_available_bytes']
    assert not low['weights_loaded'] and not low['peak_measured']
