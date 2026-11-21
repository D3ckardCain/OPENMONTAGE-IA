import pytest
from lib.model_languages import binding,validate_request


@pytest.mark.parametrize('family,code,expected',[('kokoro','pt-BR','p'),('kokoro','en-GB','b'),('kokoro','es-MX','e'),('qwen-tts','ko-KR','Korean'),('qwen-tts','Spanish','Spanish'),('aligner','pt_BR','Portuguese')])
def test_known_adapter_bindings(family,code,expected):assert binding(family,code)==expected


def test_wrong_voice_or_unknown_language_is_rejected():
    with pytest.raises(ValueError,match='voz Kokoro'):validate_request('kokoro',{'language':'es'})
    validate_request('kokoro',{'language':'es-MX','voice':'ef_dora'})
    with pytest.raises(ValueError):validate_request('kokoro',{'language':'ko','voice':'af_heart'})
    with pytest.raises(ValueError):validate_request('qwen-tts',{'language':'invalid'})


def test_adapter_rejects_language_before_diagnostics_or_model_load(tmp_path,monkeypatch):
    from lib import model_adapters
    from tools.models.local_adapters import model_kokoro
    monkeypatch.setattr(model_adapters,'diagnostics',lambda *args:pytest.fail('Must reject before diagnostics'))
    result=model_kokoro().execute({'output_dir':str(tmp_path/'output'),'text':'Hola','language':'es','voice':'af_heart'})
    assert result.success is False and 'voz Kokoro' in result.error
    assert not (tmp_path/'output').exists()


def test_local_voice_candidates_filter_language_empty_files_and_links(tmp_path):
    from lib.model_languages import local_voices
    voices=tmp_path/'voices';voices.mkdir()
    for name in ('ef_dora.pt','em_alex.pt','af_heart.pt'):(voices/name).write_bytes(b'fixture')
    (voices/'ef_empty.pt').touch()
    try:(voices/'ef_link.pt').symlink_to(voices/'ef_dora.pt')
    except OSError:pass
    assert local_voices('es-MX',tmp_path)==['ef_dora','em_alex']
    assert local_voices('en-US',tmp_path)==['af_heart']
    assert local_voices('es',None)==[]
