import pytest
from lib import translation_progress as progress


def test_progress_is_atomic_and_rejects_incompatible_source(tmp_path):
    chunks=[{'index':0,'start':0,'end':4,'text':'hola'}]
    key=progress.fingerprint(tmp_path,'en',chunks,512)
    path=tmp_path/'progress.json'
    assert progress.load(path,key,chunks)==[]
    progress.save(path,key,[{**chunks[0],'translation':'hello'}])
    assert progress.load(path,key,chunks)[0]['translation']=='hello'
    with pytest.raises(ValueError):progress.load(path,'different',chunks)
    with pytest.raises(ValueError):progress.load(path,key,[{**chunks[0],'text':'otro'}])
    assert not list(tmp_path.glob('.translation-*.tmp'))


def test_fingerprint_changes_when_model_or_settings_change(tmp_path):
    model=tmp_path/'weights';model.mkdir()
    chunks=[{'index':0,'start':0,'end':4,'text':'hola'}]
    original=progress.fingerprint(model,'en',chunks,512)
    (model/'config.json').write_text('{}')
    assert progress.fingerprint(model,'en',chunks,512)!=original
    assert progress.fingerprint(model,'ko',chunks,512)!=progress.fingerprint(model,'en',chunks,512)
