import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from lib import voice_preparation as voices
from lib.hyperframes_staging import identity


def test_actual_sample_receipt_requires_current_code_resources_and_output(tmp_path,monkeypatch):
    monkeypatch.setattr(voices,'ROOT',tmp_path)
    monkeypatch.setattr(voices,'QUALIFICATIONS',tmp_path/'qualifications.json')
    runtime={'declared_core_versions_present':True,'installed':{'torch':'2.6.0+cu124'}}
    row={'id':'fixture-regional','revision':'fixed-fixture-revision'}
    for key in ('main','decoder','tokenizer','voice_encoder'):
        path=tmp_path/key;path.write_bytes(b'fixture');row[key]={'path':str(path)}
    for name in ('lib/chatterbox_regional_runtime.py','.runtime/chatterbox/venv/Scripts/python.exe'):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
    output=tmp_path/'synthetic-fixture.wav';output.write_bytes(b'unit-test-only-not-a-real-qa-sample')
    value=dict(signature=voices.regional_signature(row,runtime),output=str(output),output_identity=identity(output),success=True)
    voices.QUALIFICATIONS.write_text(json.dumps({row['id']:value}))
    assert voices.regional_qualification(row,runtime)==value
    assert voices.regional_qualification(row,{**runtime,'declared_core_versions_present':False}) is None
    output.write_bytes(b'changed-output-fixture')
    assert voices.regional_qualification(row,runtime) is None
    value['output_identity']=identity(output);voices.QUALIFICATIONS.write_text(json.dumps({row['id']:value}))
    Path(row['main']['path']).write_bytes(b'changed-resource-fixture')
    assert voices.regional_qualification(row,runtime) is None


def test_qualified_profile_requires_authorized_reference_and_explicit_cuda(tmp_path,monkeypatch):
    row={'id':'chatterbox-es-es','ready':True};monkeypatch.setattr(voices,'catalog',lambda:{'profiles':[row]})
    reference=tmp_path/'reference.wav';reference.write_bytes(b'explicit-unit-fixture')
    inputs=dict(regional_profile=row['id'],language='es',reference_audio=str(reference),device='cuda',text='Prueba')
    with pytest.raises(ValueError,match='autorización'):voices.guard_request(inputs)
    inputs['reference_authorized']=True
    assert voices.guard_request(inputs) is row
    with pytest.raises(ValueError,match='CUDA'):voices.guard_request({**inputs,'device':'cpu'})
    with pytest.raises(ValueError,match='240 caracteres'):voices.guard_request({**inputs,'text':'x'*241})
    with pytest.raises(ValueError,match='512 tokens'):voices.guard_request({**inputs,'max_new_tokens':8192})


def test_native_adapter_uses_selected_profile_without_mutating_legacy_configuration(tmp_path,monkeypatch):
    from lib import model_adapters as adapters
    row=dict(id='chatterbox-es-es',python_executable='isolated-fixture-python',main={'path':str(tmp_path/'regional'/'t3.safetensors')})
    calls=[];monkeypatch.setattr(voices,'guard_request',lambda data:calls.append(data['regional_profile']) or row)
    monkeypatch.setenv('PYTHONPATH','explicit-unit-fixture-external-path')
    monkeypatch.setattr(adapters,'diagnostics',lambda *a,**kw:pytest.fail('Regional request must not select legacy model'))
    monkeypatch.setattr(adapters,'configuration',lambda *a:pytest.fail('Regional request must preserve legacy config'))
    def execute(command,**kwargs):
        request=json.loads(Path(command[3]).read_text())
        assert command[0]=='isolated-fixture-python' and request['source_dir']==''
        assert 'PYTHONPATH' not in kwargs['env'] and 'PYTHONHOME' not in kwargs['env']
        assert kwargs['env']['PYTHONNOUSERSITE']=='1'
        assert request['model_dir']==str(tmp_path/'regional') and request['inputs']['language']=='es'
        output=tmp_path/'out'/'voice.wav';output.write_bytes(b'explicit-mocked-transport-fixture')
        Path(command[4]).write_text(json.dumps({'success':True,'outputs':[str(output)]}))
        return SimpleNamespace(returncode=0,stdout='',stderr='')
    monkeypatch.setattr(adapters.subprocess,'run',execute)
    tool=type('FixtureRegionalAdapter',(adapters.LocalModelAdapter,),{'family':'chatterbox','name':'fixture_regional'})()
    result=tool.execute(dict(regional_profile=row['id'],language='es',device='cuda',reference_authorized=True,
                             reference_audio=str(tmp_path/'reference.wav'),text='Prueba',output_dir=str(tmp_path/'out')))
    assert result.success,result.error
    assert calls==[row['id'],row['id']]
