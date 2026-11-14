import json
import threading
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import production_agent as agent
from tools.base_tool import ToolRuntime,ToolTier,ToolStatus,ToolResult

@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(agent,'ACTIVE',{})
    return TestClient(create_app(),base_url='http://127.0.0.1:4750')

def project():
    return studio.create_production({'title':'Prueba de producción','brief':'Investigar y crear un video original','pipeline':'animated-explainer','language':'es','automatic':False})['project_id']

def test_create_state_and_policy(isolated):
    pid=project();state=isolated.get('/api/studio/projects/'+pid).json()
    assert state['request']['budget_usd']==0
    assert state['request']['publish_authorized'] is False
    assert state['job']['status']=='ready'
    cp=studio.read_json(studio.project_path(pid)/'checkpoint_research.json')
    assert cp['artifacts']['decision_log']['decisions'][0]['selected']=='guided'
    assert 'De una idea a un video' in isolated.get('/studio').text
    assert '/studio' in isolated.get('/').text

def test_invalid_inputs_and_origin(isolated):
    assert isolated.post('/api/studio/projects',json={},headers={'Origin':'https://other.invalid'}).status_code==403
    assert isolated.post('/api/studio/projects',content='x'*20001).status_code==413
    assert isolated.post('/api/studio/settings',json={'ollama_url':'https://paid.invalid'}).status_code==400
    assert isolated.get('/api/studio/projects/missing').status_code==404

@pytest.mark.parametrize('url',['http://localhost@evil.invalid','http://127.0.0.1/x','http://127.0.0.1?x=1','https://localhost','http://localhost:bad'])
def test_remote_runtime_denied(url):
    with pytest.raises(ValueError):studio.local_url(url)

def test_two_inventories_are_preserved(isolated):
    for serial in ['ADATA','SEAGATE']:
        r=isolated.post('/api/studio/inventories',json={'Serie':serial,'Ficheros':[{'FullName':'D:\\OPENMONTAJE-IA\\x','Length':1}]})
        assert r.status_code==200
    assert len(studio.resource_catalog()['inventories'])==2
    assert all(not x['live_scan'] for x in studio.resource_catalog()['inventories'])

def test_transport_emits_validated_artifact_then_blocks_without_faking_render(isolated):
    pid=project();calls=iter([
      {'role':'assistant','tool_calls':[{'function':{'name':'write_artifact','arguments':{'name':'source_notes','data':{'sources':['fixture evidence']}}}}]},
      {'role':'assistant','tool_calls':[{'function':{'name':'finish','arguments':{'blocked':True,'message':'Falta un runtime de generación compatible'}}}]}])
    worker=agent.LocalAgent(pid,chat=lambda m,t:next(calls));worker.run()
    state=studio.production_state(pid)
    assert state['job']['status']=='blocked'
    assert not state['outputs']
    assert studio.read_json(studio.project_path(pid)/'artifacts/source_notes.json')['sources']==['fixture evidence']
    with pytest.raises(ValueError,match='etapas'):worker.verify_outputs()

def test_invalid_canonical_artifact_and_decision_rewrite_rejected(isolated):
    worker=agent.LocalAgent(project())
    with pytest.raises(Exception):worker.dispatch('write_artifact',{'name':'script','data':{}})
    with pytest.raises(ValueError):worker.dispatch('write_artifact',{'name':'decision_log','data':{}})
    with pytest.raises(ValueError):worker.dispatch('read_artifact',{'name':'../../private'})

def test_paid_hybrid_publish_denied(isolated):
    worker=agent.LocalAgent(project())
    for runtime,tier in [(ToolRuntime.API,ToolTier.GENERATE),(ToolRuntime.HYBRID,ToolTier.CORE),(ToolRuntime.LOCAL,ToolTier.PUBLISH)]:
        tool=SimpleNamespace(runtime=runtime,tier=tier)
        worker.registry=SimpleNamespace(get=lambda name:tool)
        with pytest.raises(ValueError,match='locales'):worker.dispatch('execute_tool',{'name':'fake','inputs':{}})

def test_local_tool_real_execution_and_path_contract(isolated):
    pid=project();worker=agent.LocalAgent(pid)
    stage=worker.manifest['stages'][0]
    worker.instruction('skills/'+stage['skill']+'.md')
    seen=[]
    def execute(inputs):
        seen.append(inputs)
        studio.save_json(inputs['output_path'],{'actual':'tool execution'})
        return ToolResult(success=True,data={'path':inputs['output_path']})
    tool=SimpleNamespace(name='fixture-local',runtime=ToolRuntime.LOCAL,tier=ToolTier.CORE,agent_skills=[],
      input_schema={'type':'object','properties':{'output_path':{'type':'string'}}},estimate_cost=lambda x:0,
      get_status=lambda:ToolStatus.AVAILABLE,install_instructions='Fixture',execute=execute)
    worker.registry=SimpleNamespace(get=lambda name:tool)
    for path in [None,str(studio.PROJECTS_DIR.parent/'outside.json')]:
        with pytest.raises(ValueError):worker.dispatch('execute_tool',{'name':'fixture-local','inputs':{} if path is None else {'output_path':path}})
    result=worker.dispatch('execute_tool',{'name':'fixture-local','inputs':{'output_path':'assets/fixture.json'}})
    assert result['success']
    assert studio.read_json(studio.project_path(pid)/'assets/fixture.json')=={'actual':'tool execution'}
    assert len(seen)==1

def test_clarifications_and_interrupted_resume_state(isolated):
    pid=project();p=studio.project_path(pid)
    studio.save_json(p/'job.json',{'status':'running'})
    assert isolated.get('/api/studio/projects/'+pid).json()['job']['status']=='interrupted'
    assert isolated.post('/api/studio/clarifications/'+pid,json={'message':'Duración de 60 segundos'}).status_code==200
    assert studio.read_json(p/'user_clarifications.json')[0]['message']=='Duración de 60 segundos'
    agent.ACTIVE[pid]=(None,threading.Event())
    assert isolated.post('/api/studio/settings',json={}).status_code==409
    assert isolated.post('/api/studio/clarifications/'+pid,json={'message':'x'}).status_code==409

def test_export_verification_requires_real_video_stream(isolated,monkeypatch):
    pid=project();worker=agent.LocalAgent(pid)
    monkeypatch.setattr('lib.checkpoint.get_completed_stages',lambda *a:[s['name'] for s in worker.manifest['stages']])
    p=studio.project_path(pid)/'renders'/'fixture.mp4';p.parent.mkdir(exist_ok=True);p.write_bytes(b'not a video')
    studio.save_json(worker.artifact_path('render_report'),{'outputs':[{'path':str(p)}]})
    monkeypatch.setattr(agent.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout=json.dumps({'format':{'duration':'1'},'streams':[{'codec_type':'audio'}]})))
    with pytest.raises(ValueError,match='video'):worker.verify_outputs()
    monkeypatch.setattr(agent.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout=json.dumps({'format':{'duration':'1'},'streams':[{'codec_type':'video'}]})))
    assert worker.verify_outputs()[0]['path']==str(p)
    p.unlink()
    with pytest.raises(ValueError,match='no existe'):worker.verify_outputs()
