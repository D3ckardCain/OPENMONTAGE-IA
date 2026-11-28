"""Persistent queue transport with simulated producers; no AI or media work."""
import threading
from pathlib import Path
import pytest
from lib import production_studio as studio,production_queue as queue,production_agent as agent,reference_analysis


@pytest.fixture
def isolated(tmp_path,monkeypatch):
    from lib import storage_layout
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',set())
    monkeypatch.setattr(queue,'WORKER',None)
    monkeypatch.setattr(queue,'PAUSE',threading.Event())
    monkeypatch.setattr(studio,'settings',lambda:{'model':'fixture:latest','ollama_url':'http://127.0.0.1:11434'})
    monkeypatch.setattr(studio,'local_request',lambda *args,**kwargs:{'models':[{'name':'fixture:latest'}]})
    monkeypatch.setattr(storage_layout,'readiness',lambda *args:{'ready':True,'problems':[]})
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
            if status=='rendered':
                studio.save_json(studio.PROJECTS_DIR/pid/'render_verification.json',{
                    'status':'passed','outputs':[{'full_decode_passed':True,'path':'/fixture/final.mp4','sha256':'a'*64}]})
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
    with pytest.raises(ValueError,match='vuelve a ponerlo pendiente'):queue.start()
    assert started==[] and queue.read()['items'][0]['status']=='interrupted'
    queue.retry(queue.read()['items'][0]['id']);queue.start();wait()
    assert started==['first']


def test_retry_preserves_prior_cause_and_resets_current_duration(isolated):
    queue.enqueue('first')
    studio.save_json(studio.PROJECTS_DIR/'first/resource_usage.json',{
        'host_ram_peak_mb':2500,'gpu_vram_peak_mb':800,'recorded_at':'2026-11-22T10:02:00+00:00'})
    studio.save_json(studio.PROJECTS_DIR/'first/job.json',{'events':[
        {'kind':'stage_timing','stage':'script','elapsed_seconds':6,'at':'2026-11-22T10:01:00+00:00'}]})
    value=queue._load();item=value['items'][0]
    item.update(status='blocked',message='Falta un modelo',
                started_at='2026-11-22T10:00:00+00:00',finished_at='2026-11-22T10:02:00+00:00')
    queue._save(value)
    queue.retry(item['id'])
    current=queue.read()['items'][0]
    assert current['status']=='pending' and 'started_at' not in current and 'finished_at' not in current
    assert current['retry_history'][0]['message']=='Falta un modelo'
    assert current['retry_history'][0]['started_at']=='2026-11-22T10:00:00+00:00'
    assert current['retry_history'][0]['finished_at']=='2026-11-22T10:02:00+00:00'
    assert current['retry_history'][0]['resource_usage']['host_ram_peak_mb']==2500
    assert current['retry_history'][0]['stage_active_seconds']=={'script':6}
    value=queue._load();value['items'][0].update(status='blocked',message='Faltó otra etapa',
        started_at='2026-11-22T10:10:00+00:00',finished_at='2026-11-22T10:11:00+00:00')
    queue._save(value)
    queue.retry(item['id'])
    history=queue.read()['items'][0]['retry_history']
    assert len(history)==2 and 'resource_usage' not in history[1]
    assert history[1]['stage_active_seconds']=={}


def test_freeze_pilot_requires_ten_projects_and_preserves_order(isolated):
    queue.enqueue('first')
    with pytest.raises(ValueError,match='diez proyectos'):queue.freeze_pilot()
    for index in range(9):
        pid=f'pilot-{index}'
        studio.save_json(studio.PROJECTS_DIR/pid/'production_request.json',{'title':pid})
        queue.enqueue(pid)
    result=queue.freeze_pilot()
    assert result['generation_started'] is False
    assert result['pilot']['project_ids'][0]=='first'
    assert len(result['pilot']['project_ids'])==10
    with pytest.raises(ValueError,match='ya están fijados'):queue.freeze_pilot()
    assert queue.WORKER is None


def test_approval_cannot_be_bypassed_by_requeueing(isolated,monkeypatch):
    started=fake_producer(monkeypatch)
    queue.enqueue('first')
    studio.save_json(studio.PROJECTS_DIR/'first/job.json',{'status':'awaiting_human'})
    with pytest.raises(ValueError,match='requiere aprobación'):queue.start()
    assert queue.read()['items'][0]['status']=='pending' and started==[]


def test_rendered_projects_are_not_generated_again_and_wrong_disk_blocks(isolated,monkeypatch):
    started=fake_producer(monkeypatch)
    queue.enqueue('first');studio.save_json(studio.PROJECTS_DIR/'first/job.json',{'status':'rendered'})
    studio.save_json(studio.PROJECTS_DIR/'first/render_verification.json',{'status':'passed','outputs':[{'full_decode_passed':True,'path':'/fixture/final.mp4','sha256':'a'*64}]})
    queue.start();wait();assert started==[] and queue.read()['status']=='completed'
    queue.enqueue('second');value=queue._load();value['items'][1]['projects_root']=str(isolated/'other-disk');queue._save(value)
    with pytest.raises(ValueError,match='disco original'):queue.start()
    assert started==[] and queue.read()['items'][1]['status']=='pending'


def test_start_checks_later_queue_item_before_running_first(isolated,monkeypatch):
    started=fake_producer(monkeypatch)
    queue.enqueue('first');queue.enqueue('second')
    studio.save_json(studio.PROJECTS_DIR/'second/job.json',{'status':'awaiting_human'})
    before=queue._path().read_bytes()
    with pytest.raises(ValueError,match='second: La etapa requiere aprobación'):queue.start()
    assert started==[] and queue._path().read_bytes()==before
    studio.save_json(studio.PROJECTS_DIR/'second/job.json',{'status':'ready'})
    queue.start();wait()
    assert started==['first','second']


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


def test_inspection_is_read_only_and_detects_missing_projects_and_gates(isolated,monkeypatch):
    from lib import storage_layout
    monkeypatch.setattr(storage_layout,'readiness',lambda *args:{'ready':True,'problems':[]})
    monkeypatch.setattr(agent,'start',lambda *args:pytest.fail('inspection started production'))
    queue.enqueue('first');queue.enqueue('second')
    before=(studio.CONFIG_DIR/'production_queue.json').read_bytes()
    assert queue.inspect()['ready'] is True
    studio.save_json(studio.PROJECTS_DIR/'first/job.json',{'status':'awaiting_human'})
    (studio.PROJECTS_DIR/'second/production_request.json').unlink()
    report=queue.inspect()
    assert report['ready'] is False
    assert 'aprobación' in report['items'][0]['problems'][0]
    assert report['items'][1]['problems']
    assert (studio.CONFIG_DIR/'production_queue.json').read_bytes()==before


def test_inspection_requires_selected_model_and_handles_offline_ollama(isolated,monkeypatch):
    from lib import storage_layout
    monkeypatch.setattr(storage_layout,'readiness',lambda *args:{'ready':True,'problems':[]})
    queue.enqueue('first')
    monkeypatch.setattr(studio,'settings',lambda:{'model':'','ollama_url':'http://127.0.0.1:11434'})
    report=queue.inspect()
    assert report['ready'] is False and report['model_status']['configured'] is None
    monkeypatch.setattr(studio,'settings',lambda:{'model':'missing:latest','ollama_url':'http://127.0.0.1:11434'})
    report=queue.inspect()
    assert report['ready'] is False and report['model_status']['checked'] is True
    def offline(*args,**kwargs):raise OSError('offline')
    monkeypatch.setattr(studio,'local_request',offline)
    report=queue.inspect()
    assert report['ready'] is False and report['model_status']['checked'] is False
    assert report['generation_started'] is False


def test_start_refuses_missing_local_model_without_changing_queue(isolated,monkeypatch):
    queue.enqueue('first')
    before=queue._path().read_bytes()
    monkeypatch.setattr(studio,'settings',lambda:{'model':'','ollama_url':'http://127.0.0.1:11434'})
    monkeypatch.setattr(agent,'start',lambda *args:pytest.fail('No debe iniciar el agente'))
    with pytest.raises(ValueError,match='Selecciona un modelo'):queue.start()
    assert queue._path().read_bytes()==before and queue.WORKER is None
    monkeypatch.setattr(studio,'settings',lambda:{'model':'missing:latest','ollama_url':'http://127.0.0.1:11434'})
    with pytest.raises(ValueError,match='no aparece instalado'):queue.start()
    assert queue._path().read_bytes()==before


def test_rendered_project_can_be_reconciled_without_ollama(isolated,monkeypatch):
    queue.enqueue('first')
    studio.save_json(studio.PROJECTS_DIR/'first/job.json',{'status':'rendered'})
    studio.save_json(studio.PROJECTS_DIR/'first/render_verification.json',{'status':'passed','outputs':[{'full_decode_passed':True,'path':'/fixture/final.mp4','sha256':'a'*64}]})
    monkeypatch.setattr(studio,'settings',lambda:{'model':'','ollama_url':'http://127.0.0.1:11434'})
    monkeypatch.setattr(agent,'start',lambda *args:pytest.fail('Ya estaba renderizado'))
    queue.start();wait()
    assert queue.read()['items'][0]['status']=='completed'


def test_rendered_project_with_new_selection_cannot_be_marked_completed(isolated,monkeypatch):
    queue.enqueue('first')
    path=studio.PROJECTS_DIR/'first'
    studio.save_json(path/'job.json',{'status':'rendered'})
    studio.save_json(path/'render_verification.json',{'status':'passed',
        'football_selection':{'selection_id':'a'*64,'sha256':'b'*64},
        'outputs':[{'full_decode_passed':True,'path':'/fixture/final.mp4','sha256':'a'*64}]})
    studio.save_json(path/'artifacts/football_comparison_selection.json',{
        'selection_id':'c'*64,'sha256':'d'*64})
    monkeypatch.setattr(agent,'start',lambda *args:pytest.fail('No debe regenerar ni reconciliar'))
    assert queue.inspect()['ready'] is False
    with pytest.raises(ValueError,match='verificación vigente'):queue.start()
    assert queue.read()['items'][0]['status']=='pending'


def test_inspection_covers_disks_empty_queue_and_interrupted_records(isolated,monkeypatch):
    from lib import storage_layout
    monkeypatch.setattr(storage_layout,'readiness',lambda *args:{'ready':False,'problems':['Videos finales: disco desconectado']})
    assert queue.inspect()['ready'] is False
    queue.enqueue('first');value=queue._load();value['items'][0]['projects_root']=str(isolated/'elsewhere');value['items'][0]['status']='interrupted';queue._save(value)
    report=queue.inspect()
    assert len(report['items'][0]['problems'])==2
    assert report['storage']['problems']==['Videos finales: disco desconectado']
    assert report['generation_started'] is False


def test_inspection_api_does_not_mutate_queue(isolated,monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    from lib import storage_layout
    monkeypatch.setattr(storage_layout,'readiness',lambda *args:{'ready':True,'problems':[]})
    queue.enqueue('first');before=queue._path().read_bytes()
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.get('/api/studio/queue/inspect')
    assert response.status_code==200
    assert response.json()['ready'] is True
    assert queue._path().read_bytes()==before


def test_progress_uses_checkpoints_and_never_persists_derived_fields(isolated,monkeypatch):
    monkeypatch.setattr(studio,'load_pipeline_readonly',lambda name:{'stages':[{'name':'script'},{'name':'assets'},{'name':'publish'}]})
    studio.save_json(studio.PROJECTS_DIR/'first/production_request.json',{'title':'first','pipeline':'fixture'})
    studio.save_json(studio.PROJECTS_DIR/'first/checkpoint_script.json',{'status':'completed'})
    studio.save_json(studio.PROJECTS_DIR/'first/checkpoint_assets.json',{'status':'awaiting_human'})
    studio.save_json(studio.PROJECTS_DIR/'first/job.json',{'status':'awaiting_human','message':'Revisa imágenes','updated_at':'fixture-time'})
    queue.enqueue('first');value=queue._load();value['items'][0]['status']='awaiting_human';queue._save(value)
    progress=queue.read()['items'][0]['progress']
    assert progress['completed_stages']==1 and progress['total_stages']==2
    assert progress['message']=='Revisa imágenes' and progress['updated_at']=='fixture-time'
    assert progress['stages'][1]['status']=='awaiting_human'
    queue.retry(queue.read()['items'][0]['id'])
    assert 'progress' not in queue._load()['items'][0]


def test_missing_project_does_not_hide_other_queue_progress(isolated):
    queue.enqueue('first');queue.enqueue('second')
    (studio.PROJECTS_DIR/'first/production_request.json').unlink()
    report=queue.read()
    assert report['items'][0]['progress']['available'] is False
    assert report['items'][1]['progress']['available'] is True
    value=queue._load();value['items'][1]['projects_root']=str(isolated/'other');queue._save(value)
    assert queue.read()['items'][1]['progress']['available'] is False


@pytest.mark.parametrize('task',['producer','analysis','delivery'])
def test_inspection_never_reports_ready_while_local_task_is_active(isolated,monkeypatch,task):
    from lib import storage_layout
    monkeypatch.setattr(storage_layout,'readiness',lambda *args:{'ready':True,'problems':[]})
    queue.enqueue('first')
    if task=='analysis':reference_analysis.ACTIVE.add('other')
    else:agent.ACTIVE['other']=(None,threading.Event())
    report=queue.inspect()
    assert report['ready'] is False
    assert report['local_task_active'] is True
    assert report['problems']
    assert report['worker_active'] is False
    assert report['generation_started'] is False


def test_batch_enqueue_is_atomic_and_keeps_existing_status(isolated):
    queue.enqueue('first');value=queue._load();value['items'][0]['status']='blocked';queue._save(value)
    report=queue.enqueue_many(['first','second'])
    assert report['added']==['second'] and report['existing']==['first']
    assert report['generation_started'] is False
    assert queue.read()['items'][0]['status']=='blocked'
    before=queue._path().read_bytes()
    with pytest.raises(FileNotFoundError):queue.enqueue_many(['second','missing'])
    assert queue._path().read_bytes()==before


def test_batch_rejects_duplicates_and_capacity_without_partial_save(isolated):
    with pytest.raises(ValueError):queue.enqueue_many(['first','first'])
    queue.enqueue('first');value=queue._load();value['items']=value['items']*100;queue._save(value)
    before=queue._path().read_bytes()
    with pytest.raises(ValueError,match='100'):queue.enqueue_many(['second'])
    assert queue._path().read_bytes()==before


def test_batch_api_adds_only_without_starting(isolated):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    result=client.post('/api/studio/queue/enqueue-batch',json={'project_ids':['first','second']})
    assert result.status_code==200 and result.json()['generation_started'] is False
    assert client.post('/api/studio/queue/enqueue-batch',json={'project_ids':['first'],'start':True}).status_code==400
