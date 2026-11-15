from fastapi.testclient import TestClient
from jsonschema import validate
from lib import production_studio as studio
from lib.production_agent import LocalAgent, TOOLS
from lib.wan_presets import catalog
from backlot.server import create_app


def test_agent_can_select_every_catalogued_wan_profile():
    spec=next(t['function'] for t in TOOLS if t['function']['name']=='select_wan_preset')
    assert set(spec['parameters']['properties']['preset']['enum'])=={p['id'] for p in catalog()}
    for profile in catalog():validate({'preset':profile['id']},spec['parameters'])


def test_agent_source_query_is_scoped_and_requires_no_runtime(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'one'/'production_request.json',{})
    studio.save_json(tmp_path/'two'/'production_request.json',{})
    studio.save_json(tmp_path/'one'/'source_image.json',{'filename':'one.png'})
    agent=LocalAgent.__new__(LocalAgent);agent.pid='one'
    result=agent.dispatch('project_source_image',{})
    assert result['image']['filename']=='one.png' and result['project_id']=='one'
    agent.pid='two'
    assert agent.dispatch('project_source_image',{})['image'] is None


def test_image_change_is_rejected_while_project_agents_are_active(tmp_path,monkeypatch):
    from lib import production_agent
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'one'/'production_request.json',{})
    monkeypatch.setattr(production_agent,'ACTIVE',{'one':object()})
    with TestClient(create_app(),base_url='http://127.0.0.1:4750') as client:
        assert client.post('/api/studio/source-images/one',json={'image_base64':'invalid'}).status_code==409
        assert client.get('/api/studio/source-images/one').status_code==200
