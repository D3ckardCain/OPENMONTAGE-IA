import threading
from types import SimpleNamespace
import pytest
from lib import production_studio as studio,production_agent as agent,reference_analysis
from lib import project_translation as translation

@pytest.fixture
def project(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    monkeypatch.setattr(agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',set())
    studio.save_json(tmp_path/'fixture/production_request.json',{'language':'ko'})
    yield tmp_path/'fixture'
    with agent.ACTIVE_LOCK:active=agent.ACTIVE.get('fixture')
    if active and active[0]:active[0].join(timeout=5)


def test_translation_task_uses_project_language_and_preserves_script(project,monkeypatch):
    from tools.models import local_adapters
    seen=[];finish=threading.Event()
    def execute(self,inputs):
        seen.append(inputs);finish.wait(timeout=3)
        return SimpleNamespace(success=True,data={'result':{'text':'fixture translation','segments':[],'resumed_segments':2}})
    monkeypatch.setattr(local_adapters.model_madlad,'execute',execute)
    studio.save_json(project/'artifacts/script.json',{'fixture':'approved'})
    assert translation.start('fixture',{'text':'Hello'})['production_started'] is False
    with agent.ACTIVE_LOCK:thread=agent.ACTIVE['fixture'][0]
    with pytest.raises(ValueError,match='activa'):translation.start('fixture',{'text':'Other'})
    finish.set();thread.join(timeout=5)
    report=translation.read('fixture')
    assert report['status']=='completed' and report['resumed_segments']==2
    assert seen[0]['language']=='ko' and seen[0]['device']=='cpu'
    assert studio.read_json(project/'artifacts/script.json')=={'fixture':'approved'}
    assert not agent.ACTIVE


def test_failed_task_and_restart_are_reported_without_auto_execution(project,monkeypatch):
    from tools.models import local_adapters
    monkeypatch.setattr(local_adapters.model_madlad,'execute',lambda *args:SimpleNamespace(success=False,error='Missing model'))
    translation.start('fixture',{'text':'Hello'})
    with agent.ACTIVE_LOCK:active=agent.ACTIVE.get('fixture')
    if active:active[0].join(timeout=5)
    assert translation.read('fixture')['status']=='failed'
    studio.save_json(project/'translation_task.json',{'status':'running'})
    assert translation.read('fixture')['status']=='interrupted'
    assert studio.read_json(project/'translation_task.json')['status']=='running'


def test_translation_api_rejects_external_paths_and_does_not_start_on_get(project):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.get('/api/studio/translation/fixture').json()['status']=='not_started'
    assert client.post('/api/studio/translation/fixture',json={'text':'Hi','output_dir':'elsewhere'}).status_code==400
    assert not (project/'translation_task.json').exists()
