"""Studio lifecycle with simulated model/native SDK; socket tests live separately."""
import time
from unittest.mock import Mock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backlot.studio_routes import create_studio_router
from lib import production_studio as studio, production_agent as agent
from lib import local_inference_probe as probe, production_queue as queue, reference_analysis
from tools.analysis.freecad_units import FreecadUnits
from tools.base_tool import ToolResult, ToolStatus


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    monkeypatch.setattr(agent,'ACTIVE',{})
    monkeypatch.setattr(queue,'WORKER',None)
    monkeypatch.setattr(reference_analysis,'ACTIVE',set())
    monkeypatch.setattr(probe,'prepared_model',lambda:('http://127.0.0.1:11434','fixture-local',{'digest':'fixture'}, {'capabilities':['thinking']}))
    monkeypatch.setattr(studio,'settings',lambda:{'model':'fixture-local','ollama_url':'http://127.0.0.1:11434'})
    monkeypatch.setattr(studio,'local_request',lambda base,path,*a,**kw:{'version':'fixture'} if path=='/api/version' else {'models':[]})
    monkeypatch.setattr(FreecadUnits,'get_status',lambda self:ToolStatus.AVAILABLE)
    native=Mock(return_value=ToolResult(success=True,data={'values':[25.4],'provenance':{'simulated':True}},cost_usd=0))
    monkeypatch.setattr(FreecadUnits,'execute',native)
    original=agent.LocalAgent.chat
    def fake_chat(self,messages,tools=None,**options):
        if self._chat:return original(self,messages,tools,**options)
        if options['max_output_tokens']==16:
            state=studio.read_json(self.path/'inference_probe.json')
            assert not state['model_unloaded_verified']
            assert state['previous_result']['model_unloaded_verified']
            return {'role':'assistant','content':'OK'}
        self.last_transport={'request_sent':True,'response_open':True,'content_chunks':3,'done_received':False,'transport_closed':False}
        options['progress'](self.last_transport)
        if not self.cancel.wait(3):raise ValueError('test did not cancel')
        self.last_transport={**self.last_transport,'transport_closed':True,'socket_shutdown_requested':True,'server_inference_stopped':'not_verified'}
        raise agent.Pause('stopped','simulated cancellation')
    monkeypatch.setattr(agent.LocalAgent,'chat',fake_chat)
    app=FastAPI();app.include_router(create_studio_router())
    with TestClient(app) as c:yield c,native
    for thread,stop in list(agent.ACTIVE.values()):stop.set();thread.join(timeout=4)


def wait(client,url,predicate):
    deadline=time.monotonic()+4
    while time.monotonic()<deadline:
        r=client.get(url).json()
        if predicate(r):return r
        time.sleep(.01)
    pytest.fail('fixture state timeout: '+str(r))


def test_studio_stop_persisted_cancellation_and_resume_without_replaying_tool(client):
    c,native=client
    started=c.post('/api/studio/agent/probe-cancellation',json={})
    assert started.status_code==200,started.text
    task=started.json();url=task['status_url'];pid=task['project_id']
    wait(c,url,lambda r:r.get('transport',{}).get('content_chunks')==3)
    assert c.post('/api/studio/agent/probe-cancellation',json={}).status_code==400
    assert c.post(task['stop_url'],json={}).json()['requested']
    stopped=wait(c,url,lambda r:r.get('status')=='stopped' and not r['active'])
    assert stopped['model_unloaded_verified'] and stopped['receipts_unchanged']
    assert stopped['job']['status']=='stopped'
    assert stopped['model_attempts'][-1]['status']=='cancelled'
    assert stopped['model_attempts'][-1]['transport']['transport_closed']
    before=probe._receipts(studio.project_path(pid))
    assert c.post(url+'/resume',json={}).status_code==200
    resumed=wait(c,url,lambda r:r.get('status')=='completed' and not r['active'])
    assert resumed['resumed'] and resumed['receipts_unchanged']
    assert probe._receipts(studio.project_path(pid))==before
    native.assert_called_once()
    with pytest.raises(ValueError,match='fixtures'):agent.start(pid)
    assert c.post(url+'/resume',json={}).status_code==400


def test_probe_routes_reject_unbounded_requests_without_starting_task(client):
    c,native=client;url='/api/studio/agent/probe-cancellation'
    assert c.get(url).status_code==405
    assert c.post(url,json={'prompt':'unbounded'}).status_code==400
    assert c.post(url,json={},headers={'Origin':'https://remote.example'}).status_code==403
    assert c.get(url+'/ordinary-project').status_code==400
    assert not agent.ACTIVE
    native.assert_not_called()
