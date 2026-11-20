import pytest
from lib.model_file_checks import download_problem
from lib import model_adapters as adapters,production_studio as studio

@pytest.mark.parametrize('content',[b'<!DOCTYPE html><html>error',b'\xef\xbb\xbf <HTML>Login',b'version https://git-lfs.github.com/spec/v1\noid sha256:fixture',b'<?xml version="1.0"?><Error>denied'])
def test_failed_download_prefix_is_detected(tmp_path,content):
    path=tmp_path/'model.safetensors';path.write_bytes(content)
    assert download_problem(path)


def test_binary_prefix_is_not_a_quality_or_integrity_certificate(tmp_path):
    path=tmp_path/'model.bin';path.write_bytes(b'\x80\x03fixture')
    assert download_problem(path) is None


def test_complete_copy_selection_rejects_html_weights(tmp_path,monkeypatch):
    first=tmp_path/'a/model';second=tmp_path/'b/model'
    for folder in (first,second):folder.mkdir(parents=True)
    (first/'weights.safetensors').write_text('<html>Access denied')
    (second/'weights.safetensors').write_bytes(b'fixture binary')
    monkeypatch.setattr(adapters,'model_candidates',lambda family:[first,second])
    monkeypatch.setattr(adapters,'configuration',lambda family:{})
    monkeypatch.setattr(adapters,'expected_files',lambda family,path:['weights.safetensors'])
    assert adapters.resolve_model('fixture')==second
    assert adapters.model_copy_status('fixture',first)['problems']


def test_suspicious_voice_is_not_offered_as_a_local_choice(tmp_path):
    from lib.model_languages import local_voices
    voices=tmp_path/'voices';voices.mkdir()
    (voices/'ef_bad.pt').write_text('<html>Login')
    (voices/'ef_good.pt').write_bytes(b'fixture tensor')
    assert local_voices('es',tmp_path)==['ef_good']
