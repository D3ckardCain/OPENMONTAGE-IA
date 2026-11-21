"""Real HTTP/project/queue integration with simulated chat; no model or network."""
import threading
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio,production_agent as agent,production_queue as queue,reference_analysis


def test_versions_reference_and_queue_share_state_without_bypassing_blockers(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'settings')
    monkeypatch.setattr(agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',set())
    monkeypatch.setattr(queue,'WORKER',None)
    monkeypatch.setattr(queue,'PAUSE',threading.Event())
    monkeypatch.setattr(studio,'local_request',lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('No runtime requests in integration test')))
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    created=client.post('/api/studio/projects',json={'title':'Original research','brief':'Investigate facts and create original material','pipeline':'animated-explainer','language':'es','reference':'https://youtu.be/abcdefghijk','automatic':False})
    assert created.status_code==200
    base=created.json()['project_id']
    studio.save_json(studio.project_path(base)/'reference_analysis.json',{'status':'partial','transcript':{'language':'en','text':'Reference evidence'},'gaps':['Visual model not installed'],'external_fact_check':'not_performed'})
    assert client.post('/api/studio/reference-language/'+base,json={'language':'en'}).status_code==200
    assert client.post('/api/studio/language-versions/'+base,json={'languages':['en-US']}).status_code==400
    response=client.post('/api/studio/language-versions/'+base,json={'languages':['ko','de']})
    assert response.status_code==200
    identifiers=[item['project_id'] for item in response.json()['versions']]
    assert client.post('/api/studio/reference-reuse/'+base,json={'project_ids':identifiers}).status_code==200
    result=client.post('/api/studio/queue/enqueue-batch',json={'project_ids':identifiers}).json()
    assert result['generation_started'] is False and result['added']==identifiers
    seen=[];original=agent.LocalAgent
    def producer(pid,cancel):
        seen.append(pid)
        def chat(messages,tools):
            assert 'Reference evidence' in messages[1]['content']
            return {'role':'assistant','tool_calls':[{'function':{'name':'finish','arguments':{'blocked':True,'message':'Fixture dependency not installed'}}}]}
        return original(pid,chat=chat,cancel=cancel)
    monkeypatch.setattr(agent,'LocalAgent',producer)
    started=client.post('/api/studio/queue/start',json={})
    assert started.status_code==200
    with queue.LOCK:worker=queue.WORKER
    if worker:worker.join(timeout=10);assert not worker.is_alive()
    assert seen==identifiers[:1]
    queue_state=client.get('/api/studio/queue').json()
    assert queue_state['status']=='paused'
    assert [item['status'] for item in queue_state['items']]==['blocked','pending']
    versions=client.get('/api/studio/language-versions/'+base).json()
    assert versions['summary']['blocked']==1
    assert not agent.ACTIVE
    for pid in identifiers:
        state=client.get('/api/studio/projects/'+pid).json()
        assert state['outputs']==[] and state['request']['publish_authorized'] is False
        assert state['request']['automatic'] is False
        assert studio.read_json(studio.project_path(pid)/'reference_analysis.json')['status']=='partial'
