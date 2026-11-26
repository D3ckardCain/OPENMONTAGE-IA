import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from lib import blender_profiles as profiles,external_applications as apps,production_studio as studio
from tools.graphics import blender_world


@pytest.fixture
def configured(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    rows={}
    for key,version in [('old','4.5.15'),('new','5.3.0')]:
        folder=tmp_path/key;folder.mkdir();exe=folder/'blender.exe';exe.write_bytes(b'fixture')
        resources=folder/'profile';resources.mkdir()
        value={'label':key,'version':version,'executable':str(exe),'user_resources':str(resources) if key=='new' else None}
        profiles.register(key,value);rows[key]=value
    studio.save_json(studio.CONFIG_DIR/'applications.json',{'blender':{'executable':rows['old']['executable']},'freecad':{'executable':'retained'},'krita':{'executable':'retained2'}})
    return rows


def test_selection_is_shared_and_preserves_other_applications(configured):
    assert profiles.resolve()['id']=='old'
    assert profiles.select('new')['profile_id']=='new'
    assert blender_world.find_blender()==Path(configured['new']['executable'])
    assert apps.configuration()['freecad']=={'executable':'retained'}
    assert apps.configuration()['krita']=={'executable':'retained2'}
    row=next(x for x in apps.catalog() if x['id']=='blender')
    assert row['profile_contract']==1
    assert [p['id'] for p in row['profiles'] if p['selected']]==['new']


def test_environment_is_process_local_and_removes_inherited_python(configured,monkeypatch):
    monkeypatch.setenv('BLENDER_USER_CONFIG','old-config');monkeypatch.setenv('PYTHONPATH','old-python')
    import os
    before=dict(os.environ);env=profiles.environment(profiles.resolve('new'))
    assert env['BLENDER_USER_RESOURCES']==configured['new']['user_resources']
    assert 'BLENDER_USER_CONFIG' not in env and 'PYTHONPATH' not in env and env['PYTHONNOUSERSITE']=='1'
    assert Path(env['TEMP']).is_relative_to(Path(configured['new']['user_resources'])) and env['TMP']==env['TEMP']
    assert dict(os.environ)==before and profiles.environment(profiles.resolve('old'))==before


@pytest.mark.parametrize('case',['unknown','missing_executable','missing_resources','unbound_path','invalid_registry'])
def test_no_silent_fallback(configured,monkeypatch,case):
    monkeypatch.setenv('BLENDER_PATH',configured['old']['executable'])
    inputs={'operation':'doctor','profile_id':'new'}
    if case=='unknown':inputs['profile_id']='other'
    if case=='missing_executable':Path(configured['new']['executable']).unlink()
    if case=='missing_resources':Path(configured['new']['user_resources']).rmdir()
    if case=='unbound_path':
        studio.save_json(studio.CONFIG_DIR/'applications.json',{'blender':{'executable':'not-registered'}});inputs.pop('profile_id')
    if case=='invalid_registry':studio.save_json(studio.CONFIG_DIR/'blender_profiles.json',{'schema_version':2,'profiles':{}})
    monkeypatch.setattr(blender_world.subprocess,'run',lambda *a,**k:pytest.fail('No process should start'))
    result=blender_world.BlenderWorld().execute(inputs)
    assert not result.success and result.error


def test_doctor_rejects_version_or_resource_mismatch(configured,monkeypatch):
    outputs=[{'version':'5.4.0','user_resources':configured['new']['user_resources']},{'version':'5.3.0','user_resources':'different'}]
    for value in outputs:
        monkeypatch.setattr(blender_world.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='OPENMONTAGE_BLENDER=5.3.0\nOPENMONTAGE_PROFILE='+json.dumps(value),stderr=''))
        assert not blender_world.BlenderWorld().execute({'operation':'doctor','profile_id':'new'}).success


def test_launch_uses_explicit_profile_and_does_not_change_default(configured,monkeypatch,tmp_path):
    monkeypatch.setattr(studio,'project_path',lambda _:tmp_path)
    monkeypatch.setattr(apps,'CHILDREN',{})
    calls=[]
    monkeypatch.setattr(apps.subprocess,'Popen',lambda args,**kw:(calls.append((args,kw)) or SimpleNamespace(pid=42,poll=lambda:None)))
    result=apps.launch('blender','qa',profile_id='new')
    assert result['profile_id']=='new' and calls[0][0][0]==configured['new']['executable']
    assert '--offline-mode' in calls[0][0] and '--disable-autoexec' in calls[0][0]
    assert calls[0][1]['env']['BLENDER_USER_RESOURCES']==configured['new']['user_resources']
    assert profiles.resolve()['id']=='old'
    with pytest.raises(ValueError):apps.launch('krita','qa',profile_id='new')


def test_modern_profile_requires_isolation(configured):
    value={**configured['new'],'user_resources':None}
    with pytest.raises(ValueError,match='aisladas'):profiles.register('unsafe',value)


def test_api_and_agent_catalog_share_profiles_and_guard_active_jobs(configured,monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backlot.studio_routes import create_studio_router
    from lib import production_agent,reference_analysis
    from tools.desktop.application_center import ApplicationCatalog
    monkeypatch.setattr(production_agent,'ACTIVE',{});monkeypatch.setattr(reference_analysis,'ACTIVE',{})
    app=FastAPI();app.include_router(create_studio_router());client=TestClient(app)
    contract=client.get('/api/studio/applications/blender/profiles').json()
    assert contract['selection_supported'] and contract['profile_contract']==1 and len(contract['profiles'])==2
    row=next(r for r in client.get('/api/studio/applications').json()['applications'] if r['id']=='blender')
    agent_row=next(r for r in ApplicationCatalog().execute({}).data['applications'] if r['id']=='blender')
    assert row['profiles']==agent_row['profiles']
    assert client.post('/api/studio/applications/blender/profile',json={'profile_id':'new'}).status_code==200
    assert profiles.resolve()['id']=='new'
    assert client.post('/api/studio/applications/blender/profile',json={'profile_id':'absent'}).status_code==400
    monkeypatch.setattr(production_agent,'ACTIVE',{'qa':True})
    assert client.post('/api/studio/applications/blender/profile',json={'profile_id':'old'}).status_code==409
    assert profiles.resolve()['id']=='new'


@pytest.mark.parametrize('version',[(4,5),(5,3),(6,0)])
def test_changed_runtime_api_branches_without_geometry(version,monkeypatch):
    path=Path('tools/graphics/templates/blender-world-runtime.py')
    tree=ast.parse(path.read_text(encoding='utf-8'))
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('configure_engine','action_curves')]
    ns={'bpy':SimpleNamespace(app=SimpleNamespace(version=version))}
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(path),'exec'),ns)
    scene=SimpleNamespace(render=SimpleNamespace(engine='unchanged'),eevee=SimpleNamespace(taa_render_samples=64))
    if version==(6,0):
        with pytest.raises(RuntimeError):ns['configure_engine'](scene,8)
        assert scene.render.engine=='unchanged';return
    assert ns['configure_engine'](scene,8)==('BLENDER_EEVEE_NEXT' if version==(4,5) else 'BLENDER_EEVEE')
    curves=[object()];action=SimpleNamespace(fcurves=curves);animated=SimpleNamespace(animation_data=SimpleNamespace(action=action,action_slot='slot'))
    monkeypatch.setitem(sys.modules,'bpy_extras',SimpleNamespace(anim_utils=SimpleNamespace(action_get_channelbag_for_slot=lambda a,s:SimpleNamespace(fcurves=curves))))
    assert ns['action_curves'](animated)==curves
