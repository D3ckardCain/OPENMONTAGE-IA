from types import SimpleNamespace
import pytest
from lib import production_studio as studio
from lib import external_applications as apps
from lib.integration_coverage import coverage
from lib.model_adapters import CATALOG


def test_coverage_includes_every_catalogued_family_without_probing(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    report=coverage()
    assert {x['family'] for x in report['models']}==set(CATALOG)
    assert report['total']==47 and report['native_workers']==32
    assert report['prepared_recipes']==47
    assert all(x['workflow_recipe']['preparation_implemented'] for x in report['models'])
    assert not any(x['inference_verified'] for x in report['models'])
    assert all(x['next_step'] for x in report['models'])


def test_installers_are_not_runtime_bindings(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    installer=tmp_path/'Avogadro2-2.1.0-win64.exe';installer.write_bytes(b'not executed')
    with pytest.raises(ValueError,match='instalador'):apps.configure('avogadro',{'executable':str(installer)})


def test_project_handoff_uses_no_shell_and_records_launch(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(apps,'CHILDREN',{})
    project=studio.PROJECTS_DIR/'one';studio.save_json(project/'production_request.json',{})
    executable=tmp_path/'solvespace.exe';executable.write_bytes(b'not executed')
    apps.configure('solvespace',{'executable':str(executable)})
    file=project/'scene.slvs';file.write_bytes(b'fixture')
    calls=[]
    def popen(args,**kwargs):calls.append((args,kwargs));return SimpleNamespace(pid=123,poll=lambda:None)
    monkeypatch.setattr(apps.subprocess,'Popen',popen)
    record=apps.launch('solvespace','one','scene.slvs')
    assert calls[0][1]['shell'] is False
    assert calls[0][0]==[str(executable),str(file)]
    assert record['status']=='launched_not_verified'
    assert (project/'application_logs/solvespace-last.json').is_file()
    with pytest.raises(ValueError):apps.launch('solvespace','one','../../other.slvs')
