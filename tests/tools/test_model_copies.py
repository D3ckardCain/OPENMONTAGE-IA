import pytest
from lib import model_adapters as adapters
from lib import production_studio as studio

@pytest.fixture
def copies(tmp_path,monkeypatch):
    first=tmp_path/'disk-one'/'fixture-model';second=tmp_path/'disk-two'/'fixture-model'
    first.mkdir(parents=True);second.mkdir(parents=True)
    monkeypatch.setattr(adapters,'model_candidates',lambda family:[first,second])
    monkeypatch.setattr(adapters,'configuration',lambda family:{})
    monkeypatch.setattr(adapters,'expected_files',lambda family,path:['config.json','model.safetensors'])
    for folder in (first,second):studio.save_json(folder/'config.json',{})
    (second/'model.safetensors').write_bytes(b'fixture')
    return first,second


def test_complete_copy_is_preferred_without_moving_files(copies):
    first,second=copies
    assert adapters.resolve_model('fixture')==second
    assert adapters.model_copy_status('fixture',first)['missing_files']==['model.safetensors']
    assert first.is_dir() and not (first/'model.safetensors').exists()


def test_explicit_path_is_not_replaced_and_variant_is_not_switched(copies,monkeypatch):
    first,second=copies
    monkeypatch.setattr(adapters,'configuration',lambda family:{'model_dir':str(first)})
    assert adapters.resolve_model('fixture')==first
    monkeypatch.setattr(adapters,'configuration',lambda family:{})
    renamed=second.with_name('different-variant');second.rename(renamed)
    monkeypatch.setattr(adapters,'model_candidates',lambda family:[first,renamed])
    assert adapters.resolve_model('fixture')==first


def test_missing_shard_prevents_complete_copy_status(copies):
    first,second=copies
    studio.save_json(second/'model.index.json',{'weight_map':{'a':'missing-shard.safetensors'}})
    assert adapters.model_copy_status('fixture',second)['complete_files'] is False
    assert adapters.resolve_model('fixture')==first
