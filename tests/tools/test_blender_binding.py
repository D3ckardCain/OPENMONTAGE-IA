from types import SimpleNamespace
from pathlib import Path
from lib import production_studio as studio,external_applications as apps
from tools.graphics import blender_world


def test_command_center_blender_binding_is_used_by_scene_runtime(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    executable=tmp_path/'blender.exe';executable.write_bytes(b'fixture')
    apps.configure('blender',{'executable':str(executable)})
    assert blender_world.find_blender()==executable.resolve()
    entry=next(row for row in apps.catalog() if row['id']=='blender')
    assert entry['automation_tools']==['blender_world']
    assert entry['integration']=='managed_scene_workflow_and_project_file_handoff'


def test_missing_explicit_binding_never_silently_uses_another_blender(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    fallback=tmp_path/'fallback/blender';fallback.parent.mkdir();fallback.write_bytes(b'fixture')
    monkeypatch.setenv('BLENDER_PATH',str(fallback))
    studio.save_json(studio.CONFIG_DIR/'applications.json',{'blender':{'executable':str(tmp_path/'missing/blender.exe')}})
    assert blender_world.find_blender() is None
    studio.save_json(studio.CONFIG_DIR/'applications.json',{})
    assert blender_world.find_blender()==fallback.resolve()


def test_blender_doctor_uses_bound_executable_with_simulated_process(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    executable=tmp_path/'blender.exe';executable.write_bytes(b'fixture')
    apps.configure('blender',{'executable':str(executable)})
    calls=[]
    def run(command,**kwargs):
        calls.append(command);return SimpleNamespace(returncode=0,stdout='OPENMONTAGE_BLENDER=fixture',stderr='')
    monkeypatch.setattr(blender_world.subprocess,'run',run)
    result=blender_world.BlenderWorld().execute({'operation':'doctor'})
    assert result.success and calls[0][0]==str(executable)
    assert '--background' in calls[0]
