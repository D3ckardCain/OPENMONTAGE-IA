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


def test_studio_metrics_endpoint_does_not_start_work(monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    monkeypatch.setattr(production_queue, 'read', lambda: {'status':'paused','items':[]})
    response=TestClient(create_app(),base_url='http://127.0.0.1:4750').get('/api/studio/production-metrics')
    assert response.status_code==200
    assert response.json()['projects']==[] and response.json()['generation_started'] is False
