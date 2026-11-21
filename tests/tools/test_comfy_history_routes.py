from fastapi.testclient import TestClient

from backlot.server import create_app


def test_history_import_is_offline_and_does_not_submit(monkeypatch):
    import requests
    def forbidden(*args, **kwargs):
        raise AssertionError('El informe no debe abrir conexiones')
    monkeypatch.setattr(requests.sessions.Session, 'request', forbidden)
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        response = client.post('/api/studio/comfy-history/report', json={
            'job': {'status': {'completed': True, 'status_str': 'success'},
                    'outputs': {'9': {'video': [{'filename': 'existing.mp4'}]}}}})
        assert response.status_code == 200
        result = response.json()
        assert result['persisted'] is False
        assert result['jobs'][0]['status'] == 'completed'
        assert result['jobs'][0]['artifacts'][0]['filename'] == 'existing.mp4'


def test_bad_history_and_foreign_origins_are_rejected():
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        for entry in ({'status': ['bad']}, {'outputs': ['bad']}, {'status': {'messages': 'bad'}},
                      {'outputs': {'1': {'video': 'bad'}}}):
            assert client.post('/api/studio/comfy-history/report', json={'job': entry}).status_code == 400
        assert client.post('/api/studio/comfy-history/report', json=[],).status_code == 400
        assert client.post('/api/studio/comfy-history/report', json={},
                           headers={'origin': 'https://other.invalid'}).status_code == 403


def test_panel_exposes_import_without_remote_playback():
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        page = client.get('/studio')
        assert page.status_code == 200
        assert 'id="comfy-history"' in page.text
        assert 'id="comfy-history-result"' in page.text


def test_project_reports_survive_reload_and_deduplicate(tmp_path, monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path)
    for pid in ('one', 'two'):
        studio.save_json(tmp_path / pid / 'production_request.json', {'project_id': pid})
    history = {'job': {'status': {'completed': True, 'status_str': 'success'}}}
    url = '/api/studio/comfy-history/projects/one'
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        first = client.post(url, json=history).json()
        assert first['persisted'] is True and first['duplicate'] is False
        second = client.post(url, json=history).json()
        assert second['duplicate'] is True and second['id'] == first['id']
        assert client.post(url, json={}).status_code == 400
        assert client.post('/api/studio/comfy-history/projects/missing', json=history).status_code == 404
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        assert len(client.get(url).json()['reports']) == 1
        assert client.get('/api/studio/comfy-history/projects/two').json()['reports'] == []
        changed = {'job': {'status': {'completed': True, 'status_str': 'error'}}}
        assert client.post(url, json=changed).json()['duplicate'] is False
        reports = client.get(url).json()['reports']
        assert len(reports) == 2
        assert reports[0]['jobs'][0]['status'] == 'completed'
        assert reports[1]['jobs'][0]['status'] == 'failed'


def test_context_versions_preserve_evidence_and_reject_unknown_fields(tmp_path, monkeypatch):
    from lib import production_studio as studio
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path)
    studio.save_json(tmp_path / 'one' / 'production_request.json', {})
    base = '/api/studio/comfy-history/projects/one'
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        saved = client.post(base, json={'job': {'status': {'completed': True, 'status_str': 'success'}}}).json()
        url = base + '/' + saved['id'] + '/context'
        first = client.post(url, json={'equipment': 'Laptop', 'vram': '8 GB'}).json()
        assert first['jobs'] == saved['jobs']
        assert first['context_versions'][0]['verified'] is False
        assert client.post(url, json={'equipment': 'Laptop', 'vram': '8 GB'}).status_code == 200
        updated = client.post(url, json={'equipment': 'PC grande', 'vram': 'Sin confirmar'}).json()
        assert len(updated['context_versions']) == 2
        assert updated['context_versions'][0]['values']['equipment'] == 'Laptop'
        assert updated['jobs'] == saved['jobs']
        for invalid in ({}, {'gpu': 5060}, {'elapsed_seconds': 1}, {'cpu': 'x' * 2001}):
            assert client.post(url, json=invalid).status_code == 400
        missing = base + '/' + 'a' * 64 + '/context'
        assert client.post(missing, json={'equipment': 'test'}).status_code == 404
        assert client.get(base).json()['reports'][0]['context_versions'] == updated['context_versions']
