"""Recovery reuses saved proof; it never invokes a decoder or model."""
import threading
import pytest
from lib import production_studio as studio,storage_layout as storage,final_delivery as delivery
from lib.render_verification import declarations_digest
from lib.pipeline_loader import load_pipeline_readonly


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'REPO_ROOT',tmp_path/'app')
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'working')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    project=studio.PROJECTS_DIR/'one'
    studio.save_json(project/'production_request.json',{'pipeline':'hybrid','reference':''})
    source=project/'renders/final.mp4';source.parent.mkdir();source.write_bytes(b'previously verified fixture')
    outputs=[{'path':str(source),'resolution':'64x64','duration_seconds':1}]
    studio.save_json(project/'artifacts/render_report.json',{'outputs':outputs})
    studio.save_json(project/'render_verification.json',{'status':'passed','declared_outputs_sha256':declarations_digest(outputs),
        'outputs':[{'path':str(source),'sha256':delivery.digest(source),'full_decode_passed':True}]})
    stages=[s['name'] for s in load_pipeline_readonly('hybrid')['stages'] if s['name']!='publish']
    monkeypatch.setattr('lib.checkpoint.get_completed_stages',lambda *a:stages)
    finals=tmp_path/'finals';finals.mkdir()
    storage.configure(studio.REPO_ROOT,{'volumes':[{'name':'Work','projects_dir':str(studio.PROJECTS_DIR)}],
        'active_projects_dir':str(studio.PROJECTS_DIR),'final_outputs_dir':str(finals)},studio.save_json)
    return project,source,finals


def test_delivery_can_resume_after_disk_reconnect_without_rerendering(prepared,monkeypatch):
    project,source,finals=prepared;finals.rmdir()
    def forbidden(*args,**kwargs):raise AssertionError('Recovery must not decode or infer')
    monkeypatch.setattr('lib.render_verification.verify',forbidden)
    with pytest.raises(ValueError,match='conectado'):delivery.retry_verified_delivery('one')
    assert studio.read_json(project/'delivery_retry.json')['status']=='failed'
    finals.mkdir();result=delivery.retry_verified_delivery('one')
    assert result['status']=='completed' and not result['generation_started']
    assert len(list(finals.rglob('*.mp4')))==1 and source.exists()
    assert studio.read_json(project/'job.json')['status']=='rendered'
    delivery.retry_verified_delivery('one')
    assert len(list(finals.rglob('*.mp4')))==1


@pytest.mark.parametrize('change',['source','report','proof','stages'])
def test_recovery_rejects_stale_or_incomplete_evidence(prepared,monkeypatch,change):
    project,source,finals=prepared
    if change=='source':source.write_bytes(b'changed')
    elif change=='report':
        report=studio.read_json(project/'artifacts/render_report.json');report['outputs'][0]['duration_seconds']=99
        studio.save_json(project/'artifacts/render_report.json',report)
    elif change=='proof':studio.save_json(project/'render_verification.json',{'status':'failed'})
    else:monkeypatch.setattr('lib.checkpoint.get_completed_stages',lambda *a:[])
    with pytest.raises(ValueError):delivery.retry_verified_delivery('one')
    assert not list(finals.rglob('*.mp4')) and source.exists()


def test_recovery_route_refuses_active_production_and_client_supplied_paths(prepared,monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    from lib import production_agent,reference_analysis
    monkeypatch.setattr(production_agent,'ACTIVE',{'other':(None,threading.Event())})
    monkeypatch.setattr(reference_analysis,'ACTIVE',set())
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.post('/api/studio/final-delivery/one/retry',json={}).status_code==409
    monkeypatch.setattr(production_agent,'ACTIVE',{})
    assert client.post('/api/studio/final-delivery/one/retry',json={'path':'outside.mp4'}).status_code==400
    assert client.post('/api/studio/final-delivery/one/retry',json={}).json()['status']=='completed'


def test_copy_reserves_the_task_slot_without_blocking_configuration_responses(prepared,monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    from lib import production_agent,reference_analysis
    monkeypatch.setattr(production_agent,'ACTIVE',{})
    monkeypatch.setattr(reference_analysis,'ACTIVE',set())
    entered=threading.Event();release=threading.Event();results=[]
    def copying(pid):
        entered.set()
        if not release.wait(5):raise AssertionError('Test did not release its simulated copy')
        return {'status':'completed','generation_started':False}
    monkeypatch.setattr(delivery,'retry_verified_delivery',copying)
    with TestClient(create_app(),base_url='http://127.0.0.1:4750') as client:
        thread=threading.Thread(target=lambda:results.append(client.post('/api/studio/final-delivery/one/retry',json={})))
        thread.start()
        try:
            assert entered.wait(3)
            assert client.post('/api/studio/applications/ffmpeg',json={}).status_code==409
            assert client.post('/api/studio/final-delivery/one/retry',json={}).status_code==409
        finally:release.set();thread.join(timeout=5)
        assert not thread.is_alive() and results[0].status_code==200
        assert not production_agent.ACTIVE
