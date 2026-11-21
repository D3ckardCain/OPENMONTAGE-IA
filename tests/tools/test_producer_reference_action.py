"""Producer/reference ownership and transport tests. No model execution."""
import threading
import pytest
from lib import production_studio as studio,production_agent as agent,reference_analysis as analysis


@pytest.fixture
def production(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(agent,'ACTIVE',{})
    monkeypatch.setattr(analysis,'ACTIVE',set())
    pid=studio.create_production({'title':'Referencia','brief':'Investigar un video original',
        'pipeline':'animated-explainer','language':'es','reference':'https://youtu.be/abcdefghijk','automatic':False})['project_id']
    path=studio.project_path(pid);(path/'reference_video.mp4').write_bytes(b'local fixture')
    cancel=threading.Event();agent.ACTIVE[pid]=(None,cancel)
    return pid,path,cancel


def test_producer_reuses_selected_local_file_without_downloading(production,monkeypatch):
    pid,path,cancel=production;seen=[]
    def forbidden(*a):raise AssertionError('Already-local reference must not be downloaded')
    monkeypatch.setattr(analysis,'download_reference',forbidden)
    def analyze(project,source,options,output):
        seen.append((project,source,options));assert project in analysis.ACTIVE
        return {'status':'partial','gaps':['Fixture: model missing'],'device':'cpu'}
    monkeypatch.setattr(analysis,'analyze',analyze)
    result=analysis.run_for_producer(pid,{'vision':False},cancel)
    assert result['status']=='partial' and seen[0][1]==path/'reference_video.mp4'
    assert seen[0][2]['vision'] is False and not analysis.ACTIVE
    assert agent.ACTIVE[pid][1] is cancel


@pytest.mark.parametrize('mode',['wrong_owner','another_project','cancelled','analysis_busy'])
def test_no_parallel_work_and_no_owner_impersonation(production,monkeypatch,mode):
    pid,path,cancel=production
    if mode=='wrong_owner':cancel=threading.Event()
    elif mode=='another_project':agent.ACTIVE['other']=(None,threading.Event())
    elif mode=='cancelled':cancel.set()
    else:analysis.ACTIVE.add('other')
    def forbidden(*a):raise AssertionError('Must fail before analysis')
    monkeypatch.setattr(analysis,'analyze',forbidden)
    with pytest.raises(ValueError):analysis.run_for_producer(pid,{},cancel)
    assert not (path/'reference_analysis').exists()


def test_downloads_only_the_project_video_and_preserves_source_for_reuse(production,monkeypatch):
    pid,path,cancel=production;(path/'reference_video.mp4').unlink();downloads=[]
    monkeypatch.setattr(analysis,'executable',lambda name:'/fixture/'+name)
    def download(project,url,output):
        downloads.append(url);source=output/'reference.mp4';source.write_bytes(b'fixture');return source
    monkeypatch.setattr(analysis,'download_reference',download)
    monkeypatch.setattr(analysis,'analyze',lambda *args:{'status':'completed'})
    analysis.run_for_producer(pid,{},cancel);analysis.run_for_producer(pid,{},cancel)
    assert downloads==['https://www.youtube.com/watch?v=abcdefghijk']
    assert analysis.selected_source(pid).is_file()
    with pytest.raises(ValueError):analysis.run_for_producer(pid,{'url':'https://youtu.be/other_video'},cancel)


def test_failures_are_recorded_and_release_analysis_slot(production,monkeypatch):
    pid,path,cancel=production
    def fail(*args):raise RuntimeError('Fixture failure')
    monkeypatch.setattr(analysis,'analyze',fail)
    result=analysis.run_for_producer(pid,{},cancel)
    assert result['status']=='failed' and not analysis.ACTIVE
    assert studio.read_json(path/'reference_analysis.json')['status']=='failed'


def test_agent_requires_stage_and_reference_instructions(production,monkeypatch):
    pid,path,cancel=production
    producer=agent.LocalAgent(pid,chat=lambda *a:None,cancel=cancel)
    with pytest.raises(ValueError,match='instrucciones'):producer.dispatch('analyze_project_reference',{})
    stage=producer.manifest['stages'][0]
    producer.instruction('skills/'+stage['skill']+'.md')
    producer.instruction('skills/meta/video-reference-analyst.md')
    monkeypatch.setattr(analysis,'analyze',lambda *args:{'status':'completed'})
    assert producer.dispatch('analyze_project_reference',{})['status']=='completed'
