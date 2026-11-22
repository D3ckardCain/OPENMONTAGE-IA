from lib import production_metrics, production_queue


def test_saved_queue_timings_report_only_measured_runs(monkeypatch):
    monkeypatch.setattr(production_queue, 'read', lambda: {'status': 'paused', 'items': [
        {'project_id': 'one', 'title': 'Primero', 'status': 'completed',
         'started_at': '2026-11-22T10:00:00+00:00',
         'finished_at': '2026-11-22T10:02:30+00:00', 'message': 'Terminado'},
        {'project_id': 'two', 'title': 'Segundo', 'status': 'blocked',
         'started_at': '2026-11-22T10:03:00+00:00', 'message': 'Falta un recurso'},
    ]})
    result=production_metrics.snapshot()
    assert result['completed_runs_measured']==1
    assert result['elapsed_seconds_total']==150
    assert result['projects'][0]['elapsed_seconds']==150
    assert result['projects'][1]['elapsed_seconds'] is None
    assert result['ram_peak_mb'] is None and result['estimate_48_per_week'] is None
    assert result['generation_started'] is False


def test_invalid_or_reversed_timestamps_never_make_up_a_duration():
    assert production_metrics._seconds('bad', '2026-11-22T10:00:00+00:00') is None
    assert production_metrics._seconds('2026-11-22T10:01:00+00:00',
                                       '2026-11-22T10:00:00+00:00') is None


def test_stage_timings_are_summed_only_from_saved_valid_events(tmp_path, monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    studio.save_json(tmp_path/'one/production_request.json',{})
    studio.save_json(tmp_path/'one/job.json',{'events':[
        {'kind':'stage_timing','stage':'research','elapsed_seconds':3.5},
        {'kind':'stage_timing','stage':'research','elapsed_seconds':2},
        {'kind':'stage_timing','stage':'script','elapsed_seconds':7},
        {'kind':'stage_timing','stage':'script','elapsed_seconds':-1},
        {'kind':'stage','stage':'edit','elapsed_seconds':999},
    ]})
    monkeypatch.setattr(production_queue,'read',lambda:{'status':'paused','items':[
        {'project_id':'one','status':'completed'}]})
    result=production_metrics.snapshot()['projects'][0]
    assert result['stage_active_seconds']=={'research':5.5,'script':7}


def test_studio_metrics_endpoint_does_not_start_work(monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    monkeypatch.setattr(production_queue, 'read', lambda: {'status':'paused','items':[]})
    response=TestClient(create_app(),base_url='http://127.0.0.1:4750').get('/api/studio/production-metrics')
    assert response.status_code==200
    assert response.json()['projects']==[] and response.json()['generation_started'] is False
