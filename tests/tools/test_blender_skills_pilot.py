import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from lib import checkpoint,production_studio as studio
from tools.graphics import blender_skills_pilot as pilot


@pytest.fixture
def project(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    root=tmp_path/'pilot';(root/'artifacts').mkdir(parents=True);(root/'assets/scene').mkdir(parents=True);(root/'renders').mkdir()
    (root/'project.json').write_text(json.dumps({'project_id':'pilot','pipeline_type':'blender-skills-pilot'}))
    profile={'id':'blender-5.3','executable':str(tmp_path/'blender.exe'),'version':'5.3.0','user_resources':str(tmp_path/'profile')}
    monkeypatch.setattr(pilot.blender_profiles,'resolve',lambda _:profile)
    monkeypatch.setattr(pilot.blender_profiles,'environment',lambda _: {'TEMP':'isolated'})
    return root,profile


@pytest.mark.parametrize('inputs',[{'project_id':'../outside','phase':'build'},{'project_id':'pilot','phase':'unknown'},{'project_id':'pilot','phase':'build','script':'untrusted.py'}])
def test_invalid_inputs_never_start_blender(project,monkeypatch,inputs):
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:pytest.fail('No subprocess allowed'))
    assert not pilot.BlenderSkillsPilot().execute(inputs).success


def test_different_pipeline_cannot_be_overwritten(project,monkeypatch):
    root,_=project;(root/'project.json').write_text(json.dumps({'project_id':'pilot','pipeline_type':'animation'}))
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:pytest.fail('No subprocess allowed'))
    assert not pilot.BlenderSkillsPilot().execute({'project_id':'pilot','phase':'build'}).success


def test_existing_blend_is_conserved(project,monkeypatch):
    root,_=project;blend=root/'assets/scene/pilot.blend';blend.write_bytes(b'original')
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:pytest.fail('No subprocess allowed'))
    assert not pilot.BlenderSkillsPilot().execute({'project_id':'pilot','phase':'build'}).success
    assert blend.read_bytes()==b'original'


def test_changed_blend_cannot_render(project,monkeypatch):
    root,_=project;blend=root/'assets/scene/pilot.blend';blend.write_bytes(b'modified')
    (root/'artifacts/pilot-build.json').write_text(json.dumps({'contract':'blender-skills-pilot-v1','blend_sha256':'0'*64}))
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:pytest.fail('No subprocess allowed'))
    assert not pilot.BlenderSkillsPilot().execute({'project_id':'pilot','phase':'render'}).success


def test_wrong_blender_profile_is_not_replaced(project,monkeypatch):
    _,profile=project;profile['version']='4.5.15'
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:pytest.fail('No subprocess allowed'))
    assert not pilot.BlenderSkillsPilot().execute({'project_id':'pilot','phase':'build'}).success


def test_build_uses_isolated_offline_fixed_runtime(project,monkeypatch):
    root,profile=project;calls=[]
    def run(args,**kwargs):
        calls.append((args,kwargs))
        (root/'assets/scene/pilot.blend').write_bytes(b'own synthetic blend')
        (root/'artifacts/pilot-build.json').write_text(json.dumps({'contract':'blender-skills-pilot-v1'}))
        return SimpleNamespace(returncode=0,stdout='Synthetic Blender process',stderr='')
    monkeypatch.setattr(pilot.subprocess,'run',run)
    result=pilot.BlenderSkillsPilot().execute({'project_id':'pilot','phase':'build'})
    assert result.success and result.data['blend_sha256']==pilot.digest(root/'assets/scene/pilot.blend')
    args,kwargs=calls[0]
    assert args[0]==profile['executable'] and '--offline-mode' in args and '--disable-autoexec' in args
    assert str(pilot.SCRIPT) in args and kwargs['env']=={'TEMP':'isolated'}


def test_subprocess_failure_is_explicit(project,monkeypatch):
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stdout='',stderr='Synthetic shader error'))
    result=pilot.BlenderSkillsPilot().execute({'project_id':'pilot','phase':'build'})
    assert not result.success and 'Synthetic shader error' in result.error


def test_new_manifest_and_director_are_valid():
    from lib.pipeline_loader import load_pipeline,get_stage_skill
    manifest=load_pipeline('blender-skills-pilot')
    assert [s['name'] for s in manifest['stages']]==['idea','scene_plan','assets','compose']
    assert all(stage['human_approval_default'] for stage in manifest['stages'][:3])
    assert Path('skills/'+get_stage_skill(manifest,'assets')+'.md').is_file()


def test_candidate_qa_identity_rejected_before_import(tmp_path):
    import ast,hashlib
    root=tmp_path;folder=root/'references/blender-skills';folder.mkdir(parents=True)
    (folder/'qa_check.py').write_text('raise RuntimeError("must never execute")')
    tree=ast.parse(Path('tools/graphics/templates/blender-skills-pilot.py').read_text())
    fn=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='skills_qa')
    scope={'hashlib':hashlib}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'<qa identity guard>','exec'),scope)
    with pytest.raises(AssertionError,match='identity changed'):scope['skills_qa'](root)


def test_completed_render_is_not_run_again(project,monkeypatch):
    root,_=project;blend=root/'assets/scene/pilot.blend';blend.write_bytes(b'own scene')
    (root/'artifacts/pilot-build.json').write_text(json.dumps({'contract':'blender-skills-pilot-v1','blend_sha256':pilot.digest(blend)}))
    (root/'renders/blender-skills-pilot.mp4').write_bytes(b'preserve completed render')
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:pytest.fail('Do not rerender'))
    result=pilot.BlenderSkillsPilot().execute({'project_id':'pilot','phase':'render'})
    assert not result.success and 'without rerendering' in result.error
