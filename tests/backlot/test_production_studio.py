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
    assert state['channel_research'] is None
    assert state['job']['status']=='ready'
    cp=studio.read_json(studio.project_path(pid)/'checkpoint_research.json')
    assert cp['artifacts']['decision_log']['decisions'][0]['selected']=='guided'
    assert 'De una idea a un video' in isolated.get('/studio').text


def test_project_copies_verified_research_idea_link(isolated):
    from lib.channel_dossiers import save
    from lib.channel_ideas import create
    channel='UC'+'a'*22
    source=save({'source':'YouTube Data API','channel_id':channel,'retrieved_at_utc':'2026-11-22T00:00:00Z',
                 'since_utc':'2026-10-23T00:00:00Z','cutoff_at_utc':'2026-11-22T00:00:00Z',
                 'complete_period':False,'publications':[{'id':'abcdefghijk','title':'Otro video','viewCount':100},
                                                       {'id':'bbbbbbbbbbb','title':'Segundo video','viewCount':200}]})
    idea=create({'channel_id':channel,'snapshot_id':source['id'],'video_ids':['abcdefghijk'],
                 'title':'Enfoque original para el canal','angle':'Investigar y producir un relato nuevo con hechos y fuentes comprobables.',
                 'audience':'Creadores','language':'es','format':'long'})
    from lib.video_observations import add
    observation={'views':100,'vph':12,'engagement_percent':2.7,'outlier_ratio':1.5,'seo_score':40,'notes':'Observación manual'}
    add({'video_url':'https://www.youtube.com/watch?v=abcdefghijk',**observation})
    add({'video_url':'https://www.youtube.com/watch?v=bbbbbbbbbbb',**observation})
    payload={'title':idea['title'],'brief':idea['angle'],'pipeline':'animated-explainer','language':'es',
             'reference':'https://www.youtube.com/watch?v=abcdefghijk','automatic':False,
             'research_idea':{'channel_id':channel,'snapshot_id':source['id'],'idea_id':idea['id']}}
    response=isolated.post('/api/studio/projects',json=payload)
    assert response.status_code==200,response.text
    project=studio.project_path(response.json()['project_id'])
    assert studio.read_json(project/'artifacts/channel_idea_source.json')['snapshot_sha256']==source['report_sha256']
    assert studio.read_json(project/'artifacts/channel_research_snapshot.json')['report_sha256']==source['report_sha256']
    assert studio.read_json(project/'production_request.json')['research_idea']==payload['research_idea']
    from lib.channel_dossiers import _digest
    assert studio.read_json(project/'production_request.json')['research_idea_sha256']==_digest(idea)
    state=isolated.get('/api/studio/projects/'+response.json()['project_id']).json()
    assert state['channel_research']['status']=='verified'
    assert state['channel_research']['complete_period'] is False
    assert state['channel_research']['publication_total']==2
    assert state['channel_research']['vidiq_observation_total']==1
    publications=isolated.get('/api/studio/channel-research/'+response.json()['project_id']+'?limit=1').json()
    assert publications['publication_total']==2 and publications['next_offset']==1
    manual=isolated.get('/api/studio/vidiq-observations/'+response.json()['project_id']+'?limit=1').json()
    assert manual['observation_total']==1 and manual['observations'][0]['video_id']=='abcdefghijk'
    assert isolated.get('/api/studio/channel-research/'+response.json()['project_id']+'?limit=51').status_code==422
    worker=agent.LocalAgent(response.json()['project_id'])
    first=worker.dispatch('project_channel_evidence',{'limit':1})
    assert first['publication_total']==2 and first['next_offset']==1
    assert first['publications'][0]['id']=='abcdefghijk'
    assert worker.dispatch('project_channel_evidence',{'offset':1,'limit':1})['next_offset'] is None
    observed=worker.dispatch('project_vidiq_observations',{'limit':1})
    assert observed['observation_total']==1 and observed['observations'][0]['video_id']=='abcdefghijk'
    assert observed['next_offset'] is None
    observation_path=project/'artifacts/video_observations_snapshot.json'
    copied_observations=studio.read_json(observation_path)
    studio.save_json(observation_path,[{**copied_observations[0],'vph':999}])
    with pytest.raises(ValueError,match='alteradas'):
        worker.dispatch('project_vidiq_observations',{})
    assert isolated.get('/api/studio/projects/'+response.json()['project_id']).json()['channel_research']['status']=='invalid'
    assert isolated.get('/api/studio/vidiq-observations/'+response.json()['project_id']).status_code==400
    with pytest.raises(ValueError,match='alteradas'):
        agent.start(response.json()['project_id'])
    from lib import production_queue
    production_queue.enqueue(response.json()['project_id'])
    queued=production_queue.inspect()['items'][0]
    assert queued['ready'] is False
    assert any('Investigación del proyecto no válida' in problem for problem in queued['problems'])
    assert isolated.post('/api/studio/projects/'+response.json()['project_id']+'/restore-channel-research',json={}).status_code==400
    studio.save_json(observation_path,copied_observations)
    observation_path.unlink()
    add({'video_url':'https://www.youtube.com/watch?v=abcdefghijk',**{**observation,'vph':24}})
    assert isolated.get('/api/studio/projects/'+response.json()['project_id']).json()['channel_research']['status']=='missing'
    recovered=isolated.post('/api/studio/projects/'+response.json()['project_id']+'/restore-channel-research',json={})
    assert recovered.status_code==200 and recovered.json()['restored'] is True
    assert studio.read_json(observation_path)==copied_observations
    assert isolated.post('/api/studio/projects/'+response.json()['project_id']+'/restore-channel-research',json={}).json()['restored'] is False
    source_copy=studio.read_json(project/'artifacts/channel_research_snapshot.json')
    copied=studio.read_json(project/'artifacts/channel_research_snapshot.json')
    copied['report']['publications'][0]['viewCount']=999
    studio.save_json(project/'artifacts/channel_research_snapshot.json',copied)
    with pytest.raises(ValueError,match='alterado'):
        worker.dispatch('project_channel_evidence',{})
    assert isolated.get('/api/studio/projects/'+response.json()['project_id']).json()['channel_research']['status']=='invalid'
    with pytest.raises(ValueError,match='alterado'):
        agent.start(response.json()['project_id'])
    studio.save_json(project/'artifacts/channel_research_snapshot.json',source_copy)
    idea_copy=studio.read_json(project/'artifacts/channel_idea_source.json')
    altered={**idea_copy,'title':'Título cambiado'}
    studio.save_json(project/'artifacts/channel_idea_source.json',altered)
    with pytest.raises(ValueError,match='alterado'):
        worker.dispatch('project_channel_evidence',{})
    with pytest.raises(ValueError,match='alterado'):
        agent.start(response.json()['project_id'])
    bad={**payload,'reference':'https://www.youtube.com/watch?v=bbbbbbbbbbb'}
    assert isolated.post('/api/studio/projects',json=bad).status_code==400


def test_restore_legacy_research_only_when_existing_copy_matches(isolated):
    from lib.channel_dossiers import save
    from lib.channel_ideas import create
    channel='UC'+'c'*22
    source=save({'source':'YouTube Data API','channel_id':channel,'retrieved_at_utc':'2026-11-22T00:00:00Z',
                 'since_utc':'2026-10-23T00:00:00Z','cutoff_at_utc':'2026-11-22T00:00:00Z',
                 'complete_period':True,'publications':[{'id':'abcdefghijk','title':'Video fuente','viewCount':100}]})
    idea=create({'channel_id':channel,'snapshot_id':source['id'],'video_ids':['abcdefghijk'],
                 'title':'Un enfoque editorial propio','angle':'Narrar un tema con investigación y revisión de fuentes originales.',
                 'audience':'Creadores','language':'es','format':'long'})
    response=isolated.post('/api/studio/projects',json={
        'title':idea['title'],'brief':idea['angle'],'pipeline':'animated-explainer','language':'es',
        'reference':'https://www.youtube.com/watch?v=abcdefghijk','automatic':False,
        'research_idea':{'channel_id':channel,'snapshot_id':source['id'],'idea_id':idea['id']}})
    assert response.status_code==200
    pid=response.json()['project_id'];path=studio.project_path(pid)
    (path/'artifacts/channel_research_snapshot.json').unlink()
    request=studio.read_json(path/'production_request.json');request.pop('research_idea_sha256')
    studio.save_json(path/'production_request.json',request)
    assert isolated.get('/api/studio/projects/'+pid).json()['channel_research']['status']=='missing'
    with pytest.raises(ValueError,match='alterado'):
        agent.start(pid)
    restored=isolated.post('/api/studio/projects/'+pid+'/restore-channel-research',json={})
    assert restored.status_code==200 and restored.json()['restored'] is True
    assert isolated.get('/api/studio/projects/'+pid).json()['channel_research']['status']=='verified'
    assert studio.read_json(path/'production_request.json')['research_idea_sha256']
    assert isolated.post('/api/studio/projects/'+pid+'/restore-channel-research',json={}).json()['restored'] is False
    (path/'artifacts/channel_research_snapshot.json').unlink()
    altered=studio.read_json(path/'artifacts/channel_idea_source.json');altered['title']='Manipulado'
    studio.save_json(path/'artifacts/channel_idea_source.json',altered)
    assert isolated.post('/api/studio/projects/'+pid+'/restore-channel-research',json={}).status_code==400
    assert not (path/'artifacts/channel_research_snapshot.json').exists()


def test_project_and_final_catalog_label_verification_before_editorial_revision(isolated):
    from lib.final_catalog import catalog
    pid=project();path=studio.project_path(pid)
    studio.save_json(path/'render_verification.json',{
        'status':'passed','finished_at':'2026-11-22T10:00:00+00:00','outputs':[]})
    studio.save_json(path/'final_delivery.json',{'copied':True,'outputs':[]})
    studio.save_json(path/'editorial_reviews.json',[
        {'decision':'revision_requested','stage':'idea','at':'2026-11-22T10:01:00+00:00'}])
    state=isolated.get('/api/studio/projects/'+pid).json()
    assert state['render_verification']['status']=='passed'
    assert state['verification_current'] is False and state['final_copy_current'] is False
    row=next(row for row in catalog()['projects'] if row['project_id']==pid)
    assert row['verification_current'] is False and row['final_copy_current'] is False


def test_delivery_retry_rejects_verification_before_editorial_revision(isolated,monkeypatch,tmp_path):
    from lib import final_delivery
    from lib.checkpoint import get_pipeline_stages
    pid=project();path=studio.project_path(pid)
    req=studio.read_json(path/'production_request.json')
    monkeypatch.setattr('lib.checkpoint.get_completed_stages',lambda *args:get_pipeline_stages(req['pipeline']))
    monkeypatch.setattr(final_delivery,'read_config',lambda *args:{'final_outputs_dir':str(tmp_path)})
    studio.save_json(path/'render_verification.json',{
        'status':'passed','finished_at':'2026-11-22T10:00:00+00:00'})
    studio.save_json(path/'editorial_reviews.json',[
        {'decision':'revision_requested','at':'2026-11-22T10:01:00+00:00'}])
    with pytest.raises(ValueError,match='revisión o selección deportiva actual'):
        final_delivery.retry_verified_delivery(pid)


def test_new_verification_does_not_reuse_old_final_copy_receipt(isolated):
    pid=project();path=studio.project_path(pid)
    source=str(path/'renders/final.mp4')
    studio.save_json(path/'render_verification.json',{
        'status':'passed','finished_at':'2026-11-22T10:02:00+00:00',
        'outputs':[{'path':source,'sha256':'b'*64}]})
    studio.save_json(path/'final_delivery.json',{
        'copied':True,'delivered_at':'2026-11-22T10:01:00+00:00',
        'outputs':[{'source':source,'sha256':'a'*64}]})
    state=isolated.get('/api/studio/projects/'+pid).json()
    assert state['verification_current'] is True
    assert state['final_copy_current'] is False


def test_new_football_selection_marks_prior_render_as_superseded(isolated):
    from lib.final_catalog import catalog
    pid=project();path=studio.project_path(pid)
    studio.save_json(path/'render_verification.json',{
        'status':'passed','finished_at':'2026-11-22T10:00:00+00:00',
        'football_selection':{'selection_id':'a'*64,'sha256':'b'*64},'outputs':[]})
    index=path/'artifacts/football_comparison_selection.json'
    studio.save_json(index,{'selection_id':'a'*64,'sha256':'b'*64})
    assert isolated.get('/api/studio/projects/'+pid).json()['verification_current'] is True
    studio.save_json(index,{'selection_id':'c'*64,'sha256':'d'*64})
    assert isolated.get('/api/studio/projects/'+pid).json()['verification_current'] is False
    assert next(row for row in catalog()['projects'] if row['project_id']==pid)['verification_current'] is False


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
    import time
    pid=studio.create_production({'title':'Aprobaciones','brief':'Video original','pipeline':'hybrid','language':'es','automatic':False})['project_id'];worker=agent.LocalAgent(pid)
    worker._timed_stage='idea';worker._stage_timer=time.monotonic()-2
    stage=worker.manifest['stages'][0]
    worker.instruction('skills/'+stage['skill']+'.md')
    with pytest.raises(agent.Pause) as pause:
        worker.dispatch('checkpoint',{'stage':'idea','status':'completed','artifacts':{'brief':sample_artifact('brief')}})
    assert pause.value.status=='awaiting_human'
    cp=studio.read_json(studio.project_path(pid)/'checkpoint_idea.json')
    assert cp['status']=='awaiting_human'
    assert not cp['human_approved']
    timings=[event for event in studio.read_json(studio.project_path(pid)/'job.json')['events']
             if event['kind']=='stage_timing']
    assert len(timings)==1 and timings[0]['stage']=='idea'
    assert timings[0]['outcome']=='awaiting_human' and timings[0]['elapsed_seconds']>=2
    started=[]
    monkeypatch.setattr(agent,'start',lambda p:started.append(p) or {'started':True})
    agent.approve(pid)
    cp=studio.read_json(studio.project_path(pid)/'checkpoint_idea.json')
    assert cp['status']=='completed' and cp['human_approved']
    assert started==[pid]


def test_editorial_revision_preserves_checkpoint_and_does_not_start_generation(isolated,monkeypatch):
    from tests.contracts.test_phase0_contracts import sample_artifact
    pid=studio.create_production({'title':'Revisión','brief':'Video original','pipeline':'hybrid','language':'es','automatic':False})['project_id']
    worker=agent.LocalAgent(pid)
    stage=worker.manifest['stages'][0]
    worker.instruction('skills/'+stage['skill']+'.md')
    with pytest.raises(agent.Pause):
        worker.dispatch('checkpoint',{'stage':'idea','status':'completed','artifacts':{'brief':sample_artifact('brief')}})
    monkeypatch.setattr(agent,'start',lambda _:pytest.fail('La revisión no debe iniciar generación'))
    with pytest.raises(ValueError,match='Describe'):agent.request_revision(pid,' ')
    result=agent.request_revision(pid,'Cambiar el encuadre')
    assert result['generation_started'] is False
    path=studio.project_path(pid)
    cp=studio.read_json(path/'checkpoint_idea.json')
    assert cp['status']=='failed' and cp['review']['reason']=='Cambiar el encuadre'
    assert studio.read_json(path/'editorial_reviews.json')[0]['decision']=='revision_requested'
    assert studio.read_json(path/'job.json')['status']=='awaiting_input'
    assert list((path/'history').glob('checkpoint_idea_*.json'))
    with pytest.raises(ValueError,match='pendiente'):agent.approve(pid)
    seen=[]
    def chat(messages,tools):
        seen.append(json.loads(messages[1]['content']))
        return {'content':'Pausar para revisar'}
    agent.LocalAgent(pid,chat=chat).run()
    assert seen[0]['next_stage']=='idea'
    assert seen[0]['pending_editorial_revision']['reason']=='Cambiar el encuadre'
    assert studio.read_json(path/'job.json')['status']=='awaiting_input'


def test_revision_route_rejects_unexpected_fields_and_blank_reason(isolated):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    pid=studio.create_production({'title':'Revisión','brief':'Video','pipeline':'hybrid','language':'es','automatic':False})['project_id']
    assert client.post('/api/studio/revision/'+pid,json={'reason':' ','extra':1}).status_code==400
    assert client.post('/api/studio/revision/'+pid,json={'reason':' '}).status_code==400

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
    assert len(isolated.get('/api/studio/adapters').json())==47
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


def test_agent_inventory_summary_keeps_unknown_sizes_and_candidates(isolated,monkeypatch):
    states=['recorded_size_match','recorded_path_size_unknown','recorded_size_mismatch','possible_elsewhere_size_match','temporary_download_recorded','not_recorded']
    monkeypatch.setattr(studio,'resource_catalog',lambda:{'inventories':[],'notes':[],'groups':[{'id':'fixture','label':'Fixture','files':[{'status':state} for state in states]}]})
    producer=agent.LocalAgent(project(),chat=lambda *args:None,cancel=threading.Event())
    result=producer.dispatch('model_catalog',{})
    assert result['groups'][0]['inventory_status_counts']=={state:1 for state in states}
    assert result['groups'][0]['recorded']==1
    assert 'no significa ausente' in result['interpretation']


def test_agent_download_plan_requires_group_and_never_starts_download(isolated,monkeypatch):
    from lib import download_plan
    calls=[]
    def plan(group_id):calls.append(group_id);return {'downloads_started':0,'planned_files':1}
    monkeypatch.setattr(download_plan,'plan',plan)
    producer=agent.LocalAgent(project(),chat=lambda *args:None,cancel=threading.Event())
    result=producer.dispatch('model_download_plan',{'group_id':'madlad'})
    assert calls==['madlad'] and result['downloads_started']==0
    with pytest.raises(Exception):producer.dispatch('model_download_plan',{})


def test_producer_can_consult_saved_translation_without_regeneration(isolated):
    pid=project();path=studio.project_path(pid)
    studio.save_json(path/'translation_task.json',{'status':'completed','language':'es','text':'fixture translation','segments':[{'index':0,'translation':'fixture translation'}]})
    producer=agent.LocalAgent(pid,chat=lambda *args:None,cancel=threading.Event())
    report=producer.dispatch('project_translation',{'offset':0,'limit':1})
    assert report['segments'][0]['translation']=='fixture translation'
    state=isolated.get('/api/studio/projects/'+pid).json()
    assert state['translation']['saved_translation_available'] is True
    assert 'text' not in state['translation']
    assert not agent.ACTIVE


def test_round_comparison_preview_requires_verified_pair(isolated, monkeypatch):
    from lib import world_cup_open_goals

    def compare(round, players):
        assert round == 'final' and players[1]['team'] == 'France'
        return {'ready_for_script': False, 'records': [], 'unresolved': players}

    monkeypatch.setattr(world_cup_open_goals, 'compare', compare)
    path = '/api/studio/football/round-goals'
    players = [{'name': 'Messi', 'team': 'Argentina'}, {'name': 'Mbappé', 'team': 'France'}]
    result = isolated.post(path, json={'round': 'final', 'players': players})
    assert result.status_code == 200
    assert result.json()['preview_svg'] is None
    assert isolated.post(path, json={'round': 'qualifying', 'players': players}).status_code == 400


def test_qatar_edition_preview_uses_explicit_metrics(isolated, monkeypatch):
    from lib import world_cup_edition_desk
    from tools.football.ligamx import ranking_urls, tournament_scope

    tournament = ('world_cup_2022', 2022, 'final_tournament')
    scope = tournament_scope(tournament)
    urls = ranking_urls(tournament)
    queries = [{'url': urls[metric], 'retrieved_at': '2026-11-21'} for metric in ('goals', 'shots')]
    rows = []
    for entity, name in [('a', 'Messi'), ('b', 'Mbappé')]:
        stats = {'goals': 2, 'shots': 4}
        facts = [dict(metric=metric, value=value, entity_id=entity, scope=scope,
                      source_url=query['url'], retrieved_at=query['retrieved_at'])
                 for (metric, value), query in zip(stats.items(), queries)]
        rows.append(dict(entity_id=entity, identity={'entity_id': entity, 'name': name},
                         facts=facts, statistics=stats))
    report = dict(source='AS', type='player_comparison', scope=scope, queries=queries, records=rows,
                  ready_for_script=True, failed_metrics={}, unresolved=[])
    monkeypatch.setattr(world_cup_edition_desk, 'compare_edition',
                        lambda players, edition: {'report': report, 'display_metrics': ['goals', 'shots']})
    path = '/api/studio/football/round-goals'
    result = isolated.post(path, json={'round': 'edition', 'players': [
        {'name': 'Messi', 'team': 'Argentina'}, {'name': 'Mbappé', 'team': 'France'},
    ]})
    assert result.status_code == 200
    payload = {**result.json(), 'metrics': ['shots']}
    payload.pop('display_metrics')
    preview = isolated.post(path + '/preview', json=payload)
    assert preview.status_code == 200
    assert 'Tiros' in preview.json()['preview_svg']
    assert '>Goles<' not in preview.json()['preview_svg']
    dossier = isolated.post(path + '/dossier', json=payload)
    assert dossier.status_code == 200
    evidence = dossier.json()
    assert evidence['status'] == 'selection_previewed'
    assert evidence['selected_metrics'] == ['shots']
    assert len(evidence['selected_evidence']) == 2
    assert all(row['selected_facts'][0]['source_url'] == urls['shots']
               for row in evidence['selected_evidence'])
    import hashlib
    unsigned = {key: value for key, value in evidence.items() if key != 'sha256'}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
    assert hashlib.sha256(encoded).hexdigest() == evidence['sha256']
    pid = project()
    saved = isolated.post(path + '/projects/' + pid, json=payload)
    assert saved.status_code == 200 and saved.json()['duplicate'] is False
    again = isolated.post(path + '/projects/' + pid, json=payload)
    assert again.status_code == 200 and again.json()['duplicate'] is True
    assert saved.json()['selection']['selection_id'] == again.json()['selection']['selection_id']
    folder = studio.project_path(pid) / 'artifacts' / 'football_comparisons'
    assert len(list(folder.glob('*.json'))) == 1
    selected = agent.LocalAgent(pid, chat=lambda *args: None).dispatch('football_saved_selection', {})
    assert selected['available'] and selected['selected_metrics'] == ['shots']
    assert selected['selected_evidence'][0]['selected_facts'][0]['source_url'] == urls['shots']
    revision = isolated.post(path + '/projects/' + pid, json={**payload, 'metrics': ['goals']})
    assert revision.status_code == 200 and revision.json()['duplicate'] is False
    assert len(list(folder.glob('*.json'))) == 2
    assert agent.LocalAgent(pid, chat=lambda *args: None).dispatch(
        'football_saved_selection', {})['selected_metrics'] == ['goals']
    complete = agent.LocalAgent(pid, chat=lambda *args: None).dispatch(
        'football_saved_selection', {'include_report': True})
    assert complete['report'] == report
    assert complete['selected_metrics'] == ['goals']
    assert 'report' not in agent.LocalAgent(pid, chat=lambda *args: None).dispatch(
        'football_saved_selection', {})
    from tools.graphics.sports_card import render
    assert 'Goles' in render(complete['report'], complete['selected_metrics'])
    with pytest.raises(ValueError, match='reservado'):
        agent.LocalAgent(pid, chat=lambda *args: None).dispatch('write_artifact', {
            'name': 'football_comparison_selection', 'data': {}})
    altered = {**payload, 'report': {**report, 'scope': {**scope, 'season': 2023}}}
    assert isolated.post(path + '/dossier', json=altered).status_code == 400
    assert isolated.post(path + '/projects/' + pid, json=altered).status_code == 400
    payload['metrics'] = ['saves']
    assert isolated.post(path + '/preview', json=payload).status_code == 400
    assert isolated.post(path + '/dossier', json=payload).status_code == 400
    archived = studio.project_path(pid) / revision.json()['selection']['dossier_path']
    tampered = studio.read_json(archived)
    tampered['selected_evidence'][0]['selected_facts'][0]['value'] = 999
    studio.save_json(archived, tampered)
    with pytest.raises(ValueError, match='cambió'):
        agent.LocalAgent(pid, chat=lambda *args: None).dispatch('football_saved_selection', {})


def test_partial_edition_report_cannot_be_exported(isolated, monkeypatch):
    from lib import world_cup_edition_desk
    from lib.football_comparisons import metric_matrix

    report = {'scope': {'competition': 'j1', 'season': 2025, 'phase': 'league'},
              'records': [], 'ready_for_script': False, 'failed_metrics': {'shots': 'timeout'}}
    monkeypatch.setattr(world_cup_edition_desk, 'compare_edition',
                        lambda players, edition: {'report': report, 'display_metrics': ['goals'],
                                                  'metric_matrix': metric_matrix(None)})
    path = '/api/studio/football/round-goals'
    result = isolated.post(path, json={'round': 'edition', 'edition': 'j1:2025:league',
                                       'players': [{'name': 'A'}, {'name': 'B'}]})
    assert result.status_code == 200
    assert result.json()['export_token'] is None
    assert len(result.json()['metric_matrix']) == 54
    assert all(row['values'] == [None, None] and row['display_metric'] is None
               for row in result.json()['metric_matrix'])


def test_euro_edition_can_preview_verified_metric(isolated, monkeypatch):
    from tools.football.official_uefa import OfficialUEFA

    origin = {'url': 'https://compstats.uefa.com/example', 'consultado_utc': '2026-11-21'}
    scope = {'competitionId': '3', 'seasonYear': 2024, 'phase': 'TOURNAMENT'}

    def execute(self, args):
        from tools.base_tool import ToolResult
        rows = [{'id': str(i), 'nombre': name, 'estadisticas': {'goals': i},
                 'fuente_estadisticas': origin, 'fuente_por_metrica': {'goals': origin}}
                for i, name in enumerate(args['names'], 1)]
        report = {'fuente': 'UEFA', 'tipo': 'comparativa_jugadores', 'alcance': scope,
                  'consultas': [origin], 'registros': rows, 'ready_for_script': True}
        return ToolResult(success=True, data=report, cost_usd=0, from_cache=False)

    monkeypatch.setattr(OfficialUEFA, 'execute', execute)
    path = '/api/studio/football/round-goals'
    result = isolated.post(path, json={'round': 'edition', 'edition': 'euro:2024:TOURNAMENT',
                                       'players': [{'name': 'A'}, {'name': 'B'}]})
    assert result.status_code == 200
    payload = result.json()
    assert payload['export_token']
    preview = isolated.post(path + '/preview', json={'report': payload['report'],
                                                      'export_token': payload['export_token'],
                                                      'metrics': ['goals']})
    assert preview.status_code == 200
    assert '<svg' in preview.json()['preview_svg']
    dossier = isolated.post(path + '/dossier', json={'report': payload['report'],
                                                      'export_token': payload['export_token'],
                                                      'metrics': ['goals']})
    assert dossier.status_code == 200
    assert len([row for row in dossier.json()['metric_matrix'] if row['standard']]) == 54
    assert dossier.json()['selected_evidence'][0]['selected_facts'][0]['source_url'] == origin['url']


def test_fifa_partial_metrics_allow_verified_goals_only(isolated, monkeypatch):
    from lib import world_cup_edition_desk

    scope = {'competition_id': '17', 'season_id': '255711',
             'phase': 'season_aggregate_as_published'}
    source = {'url': 'https://fdh-api.fifa.com/v1/stats/season/99/players.json',
              'retrieved_at': '2026-11-21'}
    rows = [{'entity_id': str(i), 'identity': {'fdh_player_id': str(i), 'name': name},
             'statistics': {'Goals': {'value': i, 'source_flag': True, 'unit': None}},
             'missing_metrics': ['Assists']}
            for i, name in enumerate(('A', 'B'), 1)]
    report = {'source': 'FIFA', 'type': 'player_comparison', 'scope': scope,
              'queries': [source], 'records': rows, 'ready_for_script': False}
    monkeypatch.setattr(world_cup_edition_desk, 'compare_edition',
                        lambda players, edition: {'report': report, 'display_metrics': ['Goals'],
                                                   'errors': []})
    path = '/api/studio/football/round-goals'
    response = isolated.post(path, json={'round': 'edition',
        'edition': 'fifa_world_cup:2022:season_aggregate_as_published',
        'players': [{'name': 'A'}, {'name': 'B'}]})
    assert response.status_code == 200
    token = response.json()['export_token']
    assert token
    preview = isolated.post(path + '/preview', json={'report': report, 'export_token': token,
                                                      'metrics': ['Goals']})
    assert preview.status_code == 200
    assert '<svg' in preview.json()['preview_svg']
    dossier = isolated.post(path + '/dossier', json={'report': report, 'export_token': token,
                                                      'metrics': ['Goals']})
    assert dossier.status_code == 200
    assert dossier.json()['selected_evidence'][0]['selected_facts'][0]['source_url'] == source['url']
    blocked = isolated.post(path + '/preview', json={'report': report, 'export_token': token,
                                                      'metrics': ['Assists']})
    assert blocked.status_code == 400


def test_desk_displays_wrong_phase_as_source_error(isolated, monkeypatch):
    from tools.football.official_fifa import OfficialFIFA
    from tools.base_tool import ToolResult

    monkeypatch.setattr(OfficialFIFA, 'execute', lambda self, args: ToolResult(
        success=True, data={'source': 'FIFA', 'type': 'player_comparison',
                            'scope': {'competition_id': '17', 'season_id': '255711',
                                      'phase': 'qualifying'}, 'records': [],
                            'ready_for_script': True}, cost_usd=0, from_cache=False))
    result = isolated.post('/api/studio/football/round-goals', json={
        'round': 'edition', 'edition': 'fifa_world_cup:2022:season_aggregate_as_published',
        'players': [{'name': 'A'}, {'name': 'B'}]})
    assert result.status_code == 200
    assert result.json()['report'] is None
    assert result.json()['export_token'] is None
    assert any('otra competición, edición o fase' in error for error in result.json()['errors'])


def test_desk_lists_japanese_editions_with_explicit_phases(isolated):
    data = isolated.get('/api/studio/football/desk-editions').json()
    editions = {option['id']: option for option in data['editions']}
    for key in ('j1:2025:league', 'j2:2025:league', 'j3:2025:league', 'leaguecup:2025:cup'):
        assert editions[key]['team_filter'] is False
    premier = editions['premier:2024-2025:regular_season']
    assert premier['team_filter'] is True
    assert 'jornada 29' in premier['label']
    euro = editions['euro:2024:TOURNAMENT']
    assert euro['team_filter'] is False
    assert 'torneo final' in euro['label']
    for competition in ('champions', 'europa', 'conference'):
        option = editions[f'{competition}:2025:TOURNAMENT']
        assert option['team_filter'] is False
        assert '2024/25' in option['label']
    women = editions['women_champions:2025:TOURNAMENT']
    assert women['team_filter'] is False
    assert 'femenina' in women['label']
    nations = editions['nations:2025:TOURNAMENT']
    assert nations['team_filter'] is False
    assert '2024/25' in nations['label']
    fifa = editions['fifa_world_cup:2022:season_aggregate_as_published']
    assert fifa['team_filter'] is True
    assert 'fase sin acreditar' in fifa['label']
