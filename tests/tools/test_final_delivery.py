import pytest
from lib import production_studio as studio
from lib import storage_layout as storage
from lib.final_delivery import deliver


@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'REPO_ROOT',tmp_path/'app')
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'working')
    project=studio.PROJECTS_DIR/'one';studio.save_json(project/'production_request.json',{})
    renders=project/'renders';renders.mkdir();source=renders/'video.mp4';source.write_bytes(b'verified-render-fixture')
    finals=tmp_path/'finals';finals.mkdir()
    storage.configure(studio.REPO_ROOT,{'volumes':[{'name':'Working','projects_dir':str(studio.PROJECTS_DIR)}],
        'active_projects_dir':str(studio.PROJECTS_DIR),'final_outputs_dir':str(finals)},studio.save_json)
    return project,source,finals


def test_final_disk_copy_is_verified_and_repeatable(setup):
    project,source,finals=setup
    first=deliver('one',[{'path':str(source)}]);second=deliver('one',[{'path':str(source)}])
    assert first['outputs']==second['outputs']
    assert source.read_bytes()==b'verified-render-fixture'
    assert len(list((finals/'one').glob('*.mp4')))==1
    assert studio.read_json(project/'final_delivery.json')['copied'] is True


def test_missing_final_disk_preserves_working_render(setup):
    project,source,finals=setup;finals.rmdir()
    with pytest.raises(ValueError,match='no está conectado'):deliver('one',[{'path':str(source)}])
    assert source.is_file() and not (project/'final_delivery.json').exists()


def test_final_destination_may_share_model_disk(setup):
    project,source,finals=setup
    (finals/'model.safetensors').write_bytes(b'model-fixture')
    deliver('one',[{'path':str(source)}])
    assert (finals/'model.safetensors').read_bytes()==b'model-fixture'
