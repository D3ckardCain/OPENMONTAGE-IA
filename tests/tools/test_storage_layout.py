import pytest
from lib import storage_layout as storage
from lib import production_studio as studio


def test_multiple_disks_preserve_files_and_require_restart(tmp_path,monkeypatch):
    monkeypatch.delenv('OPENMONTAGE_PROJECTS_DIR',raising=False)
    repo=tmp_path/'app';one=tmp_path/'disk-one';two=tmp_path/'disk-two'
    one.mkdir();two.mkdir();(one/'keep.txt').write_text('original')
    result=storage.configure(repo,{'volumes':[{'name':'Datos 1','projects_dir':str(one)},
        {'name':'Datos 2','projects_dir':str(two)}],'active_projects_dir':str(two)},studio.save_json)
    assert result['files_moved'] is False
    assert storage.projects_directory(repo)==two
    state=storage.describe(repo,one)
    assert state['restart_required'] and len(state['volumes'])==2
    assert (one/'keep.txt').read_text()=='original' and not list(two.iterdir())


def test_disconnected_disk_is_visible_without_fallback(tmp_path,monkeypatch):
    monkeypatch.delenv('OPENMONTAGE_PROJECTS_DIR',raising=False)
    root=tmp_path/'external';root.mkdir()
    storage.configure(tmp_path/'app',{'volumes':[{'name':'External','projects_dir':str(root)}],
        'active_projects_dir':str(root)},studio.save_json)
    root.rmdir()
    assert storage.projects_directory(tmp_path/'app')==root
    state=storage.describe(tmp_path/'app',root)
    assert not state['available'] and state['volumes'][0]['free_bytes'] is None


def test_duplicate_or_disconnected_selection_is_rejected(tmp_path):
    root=tmp_path/'data';root.mkdir();volume={'name':'Data','projects_dir':str(root)}
    with pytest.raises(ValueError,match='repetida'):
        storage.configure(tmp_path,{'volumes':[volume,volume],'active_projects_dir':str(root)},studio.save_json)
    with pytest.raises(ValueError,match='registrado'):
        storage.configure(tmp_path,{'volumes':[volume],'active_projects_dir':str(tmp_path/'absent')},studio.save_json)


def test_environment_override_takes_priority(tmp_path,monkeypatch):
    root=tmp_path/'override';monkeypatch.setenv('OPENMONTAGE_PROJECTS_DIR',str(root))
    assert storage.projects_directory(tmp_path)==root
    monkeypatch.setenv('OPENMONTAGE_PROJECTS_DIR','relative')
    with pytest.raises(ValueError):storage.projects_directory(tmp_path)


def test_readiness_identifies_missing_final_disk_before_start(tmp_path,monkeypatch):
    from lib import production_agent
    repo=tmp_path/'app';working=tmp_path/'working';finals=tmp_path/'finals'
    working.mkdir();finals.mkdir()
    studio.save_json(working/'one/production_request.json',{})
    storage.configure(repo,{'volumes':[{'name':'Work','projects_dir':str(working)}],
        'active_projects_dir':str(working),'final_outputs_dir':str(finals)},studio.save_json)
    assert storage.readiness(repo,working)['ready']
    finals.rmdir()
    report=storage.readiness(repo,working)
    assert not report['ready'] and 'Videos finales' in report['problems'][0]
    monkeypatch.setattr(studio,'REPO_ROOT',repo)
    monkeypatch.setattr(studio,'PROJECTS_DIR',working)
    with pytest.raises(ValueError,match='Almacenamiento no preparado'):production_agent.start('one')


def test_full_working_disk_is_reported_without_writing(tmp_path,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(storage.shutil,'disk_usage',lambda path:SimpleNamespace(free=0))
    report=storage.readiness(tmp_path/'app',tmp_path)
    assert not report['ready'] and report['write_test_performed'] is False
