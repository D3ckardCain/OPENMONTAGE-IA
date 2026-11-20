"""Persistent queue transport with simulated producers; no AI or media work."""
import threading
from pathlib import Path
import pytest
from lib import production_studio as studio,production_queue as queue,production_agent as agent,reference_analysis


@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',set())
    monkeypatch.setattr(queue,'WORKER',None)
    monkeypatch.setattr(queue,'PAUSE',threading.Event())
    for pid in ('first','second'):
        studio.save_json(studio.PROJECTS_DIR/pid/'production_request.json',{'title':pid})
        studio.save_json(studio.PROJECTS_DIR/pid/'job.json',{'status':'ready'})
    yield tmp_path
    queue.PAUSE.set()
    if queue.WORKER is not None:queue.WORKER.join(timeout=5)


def wait():
    with queue.LOCK:worker=queue.WORKER
    if worker:worker.join(timeout=5);assert not worker.is_alive()


def fake_producer(monkeypatch,status='rendered',pause_after_first=False):
    started=[]
    def start(pid):
        assert not agent.ACTIVE
        started.append(pid)
        def work():
            studio.save_json(studio.PROJECTS_DIR/pid/'job.json',{'status':status,'message':'Fixture result'})
            if pause_after_first:queue.pause()
            with agent.ACTIVE_LOCK:agent.ACTIVE.pop(pid,None)
        thread=threading.Thread(target=work)
        with agent.ACTIVE_LOCK:agent.ACTIVE[pid]=(thread,threading.Event())
        thread.start();return {'started':True}
    monkeypatch.setattr(agent,'start',start)
    return started


def test_enqueue_is_persistent_and_does_not_start_production(isolated,monkeypatch):
    def forbidden(*args):raise AssertionError('enqueue cannot start models')
    monkeypatch.setattr(agent,'start',forbidden)
    assert queue.enqueue('first')['generation_started'] is False
    assert queue.read()['items'][0]['status']=='pending'
    assert studio.read_json(studio.CONFIG_DIR/'production_queue.json')['items'][0]['project_id']=='first'
    with pytest.raises(ValueError,match='ya está'):queue.enqueue('first')


def test_fifo_runs_one_producer_at_a_time(isolated,monkeypatch):
    started=fake_producer(monkeypatch)
    queue.enqueue('first');queue.enqueue('second');queue.start();wait()
    assert started==['first','second']
    assert queue.read()['status']=='completed'


@pytest.mark.parametrize('status',['blocked','awaiting_human','awaiting_input','stopped'])
def test_blocked_or_gated_project_stops_the_queue(isolated,monkeypatch,status):
    started=fake_producer(monkeypatch,status)
    queue.enqueue('first');queue.enqueue('second');queue.start();wait()
    assert started==['first'] and queue.read()['status']=='paused'
    assert queue.read()['items'][1]['status']=='pending'


def test_pause_finishes_current_project_and_preserves_next(isolated,monkeypatch):
    started=fake_producer(monkeypatch,pause_after_first=True)
    queue.enqueue('first');queue.enqueue('second');queue.start();wait()
    assert started==['first'] and queue.read()['items'][0]['status']=='completed'
    assert queue.read()['items'][1]['status']=='pending'


def test_restart_requires_review_before_generation(isolated,monkeypatch):
    started=fake_producer(monkeypatch)
    queue.enqueue('first');value=queue._load();value['status']='running';value['items'][0]['status']='starting';queue._save(value)
    assert queue.read()['items'][0]['status']=='interrupted'
    queue.start();wait();assert started==[]
    queue.retry(queue.read()['items'][0]['id']);queue.start();wait()
    assert started==['first']


def test_approval_cannot_be_bypassed_by_requeueing(isolated,monkeypatch):
    started=fake_producer(monkeypatch)
    queue.enqueue('first')
    studio.save_json(studio.PROJECTS_DIR/'first/job.json',{'status':'awaiting_human'})
    queue.start();wait();item=queue.read()['items'][0]
    assert item['status']=='awaiting_human' and started==[]
    queue.retry(item['id']);queue.start();wait();assert started==[]


def test_rendered_projects_are_not_generated_again_and_wrong_disk_blocks(isolated,monkeypatch):
    started=fake_producer(monkeypatch)
    queue.enqueue('first');studio.save_json(studio.PROJECTS_DIR/'first/job.json',{'status':'rendered'})
    queue.start();wait();assert started==[] and queue.read()['status']=='completed'
    queue.enqueue('second');value=queue._load();value['items'][1]['projects_root']=str(isolated/'other-disk');queue._save(value)
    queue.start();wait();assert started==[] and queue.read()['items'][1]['status']=='blocked'


def test_active_local_work_prevents_start(isolated):
    queue.enqueue('first');agent.ACTIVE['manual']=(None,threading.Event())
    with pytest.raises(ValueError,match='activa'):queue.start()


def test_queue_api_does_not_start_on_enqueue(isolated):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.post('/api/studio/queue/enqueue',json={'project_id':'first'}).json()['generation_started'] is False
    assert client.get('/api/studio/queue').json()['items'][0]['project_id']=='first'
    assert client.post('/api/studio/queue/start',json={'automatic':True}).status_code==400


def test_edit_preserves_files_and_changes_execution_order(isolated,monkeypatch):
    started=fake_producer(monkeypatch)
    queue.enqueue('first');queue.enqueue('second')
    identifier=queue.read()['items'][1]['id']
    queue.edit(identifier,'up');queue.start();wait()
    assert started==['second','first']
    assert queue.edit(identifier)['project_files_deleted'] is False
    assert (studio.PROJECTS_DIR/'second/production_request.json').is_file()
    assert (studio.PROJECTS_DIR/'second/job.json').is_file()
    assert len(queue.read()['items'])==1


def test_edit_rejects_active_invalid_and_nonpending_records(isolated,monkeypatch):
    queue.enqueue('first');identifier=queue.read()['items'][0]['id']
    with pytest.raises(ValueError,match='extremo'):queue.edit(identifier,'up')
    with pytest.raises(ValueError,match='Dirección'):queue.edit(identifier,'bad')
    with pytest.raises(ValueError,match='inexistente'):queue.edit('missing')
    monkeypatch.setattr(queue,'WORKER',object())
    with pytest.raises(ValueError,match='Pausa'):queue.edit(identifier)
    monkeypatch.setattr(queue,'WORKER',None)
    value=queue._load();value['items'][0]['status']='blocked';queue._save(value)
    with pytest.raises(ValueError,match='pendientes'):queue.edit(identifier,'down')


def test_edit_api_validates_input_without_deleting_project(isolated):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    queue.enqueue('first');queue.enqueue('second');identifier=queue.read()['items'][1]['id']
    assert client.post('/api/studio/queue/move',json={'id':identifier,'direction':'up'}).status_code==200
    assert client.post('/api/studio/queue/remove',json={'id':identifier,'delete':True}).status_code==400
    assert client.post('/api/studio/queue/remove',json={'id':identifier}).json()['project_files_deleted'] is False
    assert (studio.PROJECTS_DIR/'second/production_request.json').is_file()
