import pytest
from lib import production_studio as studio
from lib import storage_layout as storage
from lib.final_delivery import deliver,digest


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
    verified={'path':str(source),'verified_sha256':digest(source)}
    first=deliver('one',[verified]);second=deliver('one',[verified])
    assert first['outputs']==second['outputs']
    assert source.read_bytes()==b'verified-render-fixture'
    assert len(list((finals/'one').glob('*.mp4')))==1
    assert studio.read_json(project/'final_delivery.json')['copied'] is True


def test_missing_final_disk_preserves_working_render(setup):
    project,source,finals=setup;finals.rmdir()
    with pytest.raises(ValueError,match='no está conectado'):deliver('one',[{'path':str(source),'verified_sha256':digest(source)}])
    assert source.is_file() and not (project/'final_delivery.json').exists()


def test_final_destination_may_share_model_disk(setup):
    project,source,finals=setup
    (finals/'model.safetensors').write_bytes(b'model-fixture')
    deliver('one',[{'path':str(source),'verified_sha256':digest(source)}])
    assert (finals/'model.safetensors').read_bytes()==b'model-fixture'


def test_final_copy_rejects_missing_or_changed_verification_hash(setup):
    project,source,finals=setup
    with pytest.raises(ValueError,match='Falta el SHA-256'):
        deliver('one',[{'path':str(source)}])
    with pytest.raises(ValueError,match='render cambió'):
        deliver('one',[{'path':str(source),'verified_sha256':'0'*64}])
    assert not list(finals.rglob('*.mp4')) and not (project/'final_delivery.json').exists()


def test_multi_video_delivery_checks_all_hashes_before_first_copy(setup):
    project,source,finals=setup
    second=source.parent/'second.mp4';second.write_bytes(b'another video')
    with pytest.raises(ValueError,match='render cambió'):
        deliver('one',[{'path':str(source),'verified_sha256':digest(source)},
                       {'path':str(second),'verified_sha256':'0'*64}])
    assert not list(finals.rglob('*.mp4'))
    assert not (project/'final_delivery.json').exists()


def test_delivery_rejects_empty_or_duplicate_render_manifest(setup):
    project,source,finals=setup
    with pytest.raises(ValueError,match='entre una y dieciséis'):
        deliver('one',[])
    verified={'path':str(source),'verified_sha256':digest(source)}
    with pytest.raises(ValueError,match='repite un render'):
        deliver('one',[verified,{'path':'renders/video.mp4','verified_sha256':digest(source)}])
    assert not list(finals.rglob('*.mp4'))
    assert not (project/'final_delivery.json').exists()
