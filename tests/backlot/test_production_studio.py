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


@pytest.mark.parametrize('reference,expected',[
    ('https://youtu.be/abcdefghijk?feature=share','https://www.youtube.com/watch?v=abcdefghijk'),
    ('https://www.youtube.com/shorts/abcdefghijk','https://www.youtube.com/watch?v=abcdefghijk'),
    ('https://www.youtube.com/@example',None),('https://external.invalid/video',None)])
def test_reference_handoff_does_not_start_download_or_analysis(isolated,monkeypatch,reference,expected):
    from lib import reference_analysis
    def forbidden(*a,**k):raise AssertionError('Reading project state must not start media work')
    monkeypatch.setattr(reference_analysis,'start',forbidden)
    monkeypatch.setattr(reference_analysis,'download_reference',forbidden)
    pid=studio.create_production({'title':'Referencia elegida','brief':'Crear una investigación original',
        'pipeline':'animated-explainer','language':'es','reference':reference,'automatic':False})['project_id']
    state=isolated.get('/api/studio/projects/'+pid).json()
    assert state['reference_video_url']==expected
    assert state['request']['reference']==reference
    assert not (studio.project_path(pid)/'reference_analysis').exists()
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
    monkeypatch.setattr('lib.render_verification.executable',lambda name:'/fixture/'+name)
    monkeypatch.setattr('lib.checkpoint.get_completed_stages',lambda *a:[s['name'] for s in worker.manifest['stages']])
    p=studio.project_path(pid)/'renders'/'fixture.mp4';p.parent.mkdir(exist_ok=True);p.write_bytes(b'not a video')
    studio.save_json(worker.artifact_path('render_report'),{'outputs':[{'path':str(p)}]})
    monkeypatch.setattr(agent.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout=json.dumps({'format':{'duration':'1'},'streams':[{'codec_type':'audio'}]})))
    with pytest.raises(ValueError,match='video'):worker.verify_outputs()
    monkeypatch.setattr(agent.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout=json.dumps({'format':{'duration':'1'},'streams':[{'codec_type':'video','width':64,'height':64,'codec_name':'mpeg4'}]})))
    assert worker.verify_outputs()[0]['path']==str(p)
    p.unlink()
    with pytest.raises(ValueError,match='no existe'):worker.verify_outputs()

def test_guided_checkpoint_waits_and_explicit_approval_resumes(isolated,monkeypatch):
    from tests.contracts.test_phase0_contracts import sample_artifact
    pid=studio.create_production({'title':'Aprobaciones','brief':'Video original','pipeline':'hybrid','language':'es','automatic':False})['project_id'];worker=agent.LocalAgent(pid)
    stage=worker.manifest['stages'][0]
    worker.instruction('skills/'+stage['skill']+'.md')
    with pytest.raises(agent.Pause) as pause:
        worker.dispatch('checkpoint',{'stage':'idea','status':'completed','artifacts':{'brief':sample_artifact('brief')}})
    assert pause.value.status=='awaiting_human'
    cp=studio.read_json(studio.project_path(pid)/'checkpoint_idea.json')
    assert cp['status']=='awaiting_human'
    assert not cp['human_approved']
    started=[]
    monkeypatch.setattr(agent,'start',lambda p:started.append(p) or {'started':True})
    agent.approve(pid)
    cp=studio.read_json(studio.project_path(pid)/'checkpoint_idea.json')
    assert cp['status']=='completed' and cp['human_approved']
    assert started==[pid]

def test_image_review_sends_actual_project_image_to_transport(isolated):
    from PIL import Image
    pid=project();p=studio.project_path(pid)/'assets'/'sample.png';p.parent.mkdir(exist_ok=True)
    Image.new('RGB',(12,12),'red').save(p)
    messages=[]
    def chat(m,t):
        messages.extend(m);return {'content':'Synthetic review fixture'}
    worker=agent.LocalAgent(pid,chat=chat)
    result=worker.dispatch('inspect_image',{'path':str(p),'question':'Revisar composición'})
    assert result['scope']=='single_image'
    import base64,io
    image=Image.open(io.BytesIO(base64.b64decode(messages[-1]['images'][0])))
    assert image.size==(12,12)
    with pytest.raises(ValueError):worker.dispatch('inspect_image',{'path':str(studio.PROJECTS_DIR.parent/'private.png'),'question':'Revisar'})

def test_automatic_agent_walks_pipeline_to_real_fixture_export(isolated):
    """Exercise orchestration with a synthetic model, not generative quality."""
    import shutil,subprocess
    from tests.contracts.test_phase0_contracts import sample_artifact
    from lib.checkpoint import CANONICAL_STAGE_ARTIFACTS
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):pytest.skip('FFmpeg required for media contract')
    pid=studio.create_production({'title':'Synthetic transport end-to-end','brief':'Contract fixture only','pipeline':'hybrid','language':'es','automatic':True})['project_id']
    worker=agent.LocalAgent(pid)
    output=studio.project_path(pid)/'renders'/'fixture.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=64x64:d=0.2','-c:v','mpeg4','-y',str(output)],check=True,timeout=20)
    messages=[]
    for stage in worker.manifest['stages']:
        if stage['name']=='publish':continue
        def call(name,args):return {'role':'assistant','tool_calls':[{'function':{'name':name,'arguments':args}}]}
        messages.append(call('read_instruction',{'path':'skills/'+stage['skill']+'.md'}))
        name=CANONICAL_STAGE_ARTIFACTS[stage['name']];artifact=sample_artifact(name)
        if name=='edit_decisions':artifact['render_runtime']='ffmpeg'
        if name=='render_report':
            artifact['outputs'][0].update(path=str(output),resolution='64x64',duration_seconds=0.2,fps=25,codec='mpeg4')
            artifact['outputs'][0].pop('audio_codec',None)
            artifact['outputs'][0].pop('file_size_bytes',None)
        messages.append(call('checkpoint',{'stage':stage['name'],'status':'completed','artifacts':{name:artifact}}))
    messages.append(call('finish',{'blocked':False,'message':'Synthetic fixture export verified'}))
    stream=iter(messages);worker._chat=lambda m,t:next(stream)
    worker.run();state=studio.production_state(pid)
    assert state['job']['status']=='rendered',state['job']
    assert state['outputs'][0]['name']=='fixture.mp4'
    assert next(x for x in state['stages'] if x['name']=='publish')['status']=='pending'

def test_agent_can_author_composition_files_without_overwriting_checkpoints(isolated):
    worker=agent.LocalAgent(project())
    worker.dispatch('write_project_file',{'path':'assets/captions.srt','content':'1\n00:00:00,000 --> 00:00:01,000\nHola\n'})
    worker.dispatch('write_project_file',{'path':'workspaces/composition/src/Root.tsx','content':'export const Title = () => <div>Original</div>;'})
    result=worker.dispatch('read_project_file',{'path':'assets/captions.srt'})
    assert 'Hola' in result['content']
    assert any(x['path']=='workspaces/composition/src/Root.tsx' for x in worker.dispatch('project_files',{})['files'])
    for path in ['checkpoint_research.json','../outside.txt','assets/malicious.exe']:
        with pytest.raises(ValueError):worker.dispatch('write_project_file',{'path':path,'content':'invalid'})
    group=studio.resource_catalog()['groups'][0]
    assert worker.dispatch('model_catalog',{'group_id':group['id']})['group']['files'][0]['download_url']

def test_studio_cli_opens_actual_studio_url(monkeypatch):
    from backlot import __main__ as cli
    urls=[]
    monkeypatch.setattr(cli,'_server_alive',lambda port:True)
    monkeypatch.setattr(cli.webbrowser,'open',lambda url:urls.append(url))
    assert cli.main(['studio'])==0
    assert urls[0].endswith('/studio')
    urls.clear()
    assert cli.main(['open','video-existing'])==0
    assert urls[0].endswith('/p/video-existing')

def test_adapter_settings_and_diagnostics_are_reachable_in_studio(isolated,monkeypatch):
    from lib import model_adapters
    monkeypatch.setattr(model_adapters,'diagnostics',lambda family:{'family':family,'ready':False,'inference_verified':False})
    assert len(isolated.get('/api/studio/adapters').json())==46
    cfg={'python_executable':__import__('sys').executable,'model_dir':str(studio.CONFIG_DIR/'weights')}
    assert isolated.post('/api/studio/adapters/kokoro',json=cfg).status_code==200
    assert model_adapters.configuration('kokoro')['model_dir']==cfg['model_dir']
    assert isolated.post('/api/studio/adapters/unknown',json={}).status_code==400
    assert isolated.post('/api/studio/adapters/kokoro',json={},headers={'Origin':'https://evil.invalid'}).status_code==403
    agent.ACTIVE['fixture']=(None,threading.Event())
    assert isolated.post('/api/studio/adapters/kokoro',json={}).status_code==409


def test_agent_can_inspect_and_bind_only_project_workflows(isolated,monkeypatch):
    from lib import model_comfy_adapter,model_adapters
    pid=project();worker=agent.LocalAgent(pid)
    path=studio.project_path(pid)/'workspaces/graph.json';studio.save_json(path,{'1':{'class_type':'Fixture','inputs':{}}})
    monkeypatch.setattr(model_comfy_adapter,'validate_graph',lambda *a:None)
    bound=worker.dispatch('bind_workflow',{'family':'wan','path':str(path),'output_node':'1'})
    assert bound['workflow_path']==str(path)
    with pytest.raises(ValueError):worker.dispatch('bind_workflow',{'family':'wan','path':str(studio.CONFIG_DIR/'outside.json'),'output_node':'1'})
    with pytest.raises(ValueError):worker.dispatch('bind_workflow',{'family':'kokoro','path':str(path),'output_node':'1'})


def test_real_language_projects_have_guided_checkpoints_and_independent_workspaces(isolated):
    parent=project()
    response=isolated.post('/api/studio/language-versions/'+parent,json={'languages':['en','ko']})
    assert response.status_code==200
    versions=response.json()['versions']
    assert len({entry['project_id'] for entry in versions})==2
    for entry in versions:
        path=studio.project_path(entry['project_id'])
        state=isolated.get('/api/studio/projects/'+entry['project_id']).json()
        assert state['request']['language']==entry['language']
        assert state['request']['automatic'] is False and state['request']['publish_authorized'] is False
        assert state['job']['status']=='ready' and state['outputs']==[]
        checkpoint=studio.read_json(path/'checkpoint_research.json')
        assert checkpoint['artifacts']['decision_log']['decisions'][0]['selected']=='guided'
    assert isolated.post('/api/studio/language-versions/'+parent,json={'languages':['en','ko']}).json()['versions'][0]['status']=='existing'


def test_agent_can_read_language_resources_without_model_execution(isolated,monkeypatch):
    from lib import language_versions
    pid=project();seen=[]
    def resources(project_id):
        seen.append(project_id)
        return {'target_language':'es','candidates':[{'family':'kokoro','matching_local_voices':['ef_dora']}],'generation_started':False}
    monkeypatch.setattr(language_versions,'local_requirements',resources)
    producer=agent.LocalAgent(pid,chat=lambda *args:None,cancel=threading.Event())
    result=producer.dispatch('language_resources',{})
    assert result['candidates'][0]['matching_local_voices']==['ef_dora']
    assert seen==[pid] and result['generation_started'] is False
