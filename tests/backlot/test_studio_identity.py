"""Focused offline contract tests; no models, project mutations or active server."""
from fastapi.testclient import TestClient

from backlot import studio_identity as identity
from backlot.server import create_app


def test_identity_and_capabilities_share_resident_build():
    client = TestClient(create_app(), base_url='http://127.0.0.1')
    result = client.get('/api/studio/identity')
    data = result.json()
    assert result.status_code == 200 and result.headers['cache-control'] == 'no-store'
    assert data['restart_required'] is False
    assert data['revision_kind'] == 'source_sha256_at_import'
    assert data['resident']['sha256'] == data['disk']['sha256']
    caps = client.get('/api/studio/editor/capabilities').json()
    assert caps == data['editor']
    assert caps['backend_build'] == data['resident']['sha256']
    caps['commands'].clear()
    assert identity.capabilities()['commands']  # callers cannot mutate snapshot
    html = client.get('/studio')
    assert f'content="{data["ui"]["sha256"]}"' in html.text
    assert 'id="studio-compatibility"' in html.text
    assert html.headers['cache-control'] == 'no-store'


def test_disk_change_does_not_relabel_resident_or_read_models(tmp_path, monkeypatch):
    source = tmp_path / 'backlot' / 'server.py'
    source.parent.mkdir()
    source.write_text('old', encoding='utf-8')
    ui = source.parent / 'ui'
    ui.mkdir()
    (ui / 'studio.html').write_text('html', encoding='utf-8')
    monkeypatch.setattr(identity, 'ROOT', tmp_path)
    resident = identity.fingerprint(tmp_path)
    monkeypatch.setattr(identity, 'RESIDENT', resident)
    assert identity.identity()['restart_required'] is False
    (tmp_path / 'model.safetensors').write_text('ignored', encoding='utf-8')
    assert identity.identity()['restart_required'] is False
    source.write_text('new', encoding='utf-8')
    changed = identity.identity()
    assert changed['restart_required'] is True
    assert changed['resident'] == resident
    assert changed['disk']['sha256'] != resident['sha256']
    source.unlink()
    assert identity.identity()['restart_required'] is None


def test_unreadable_and_oversized_source_fail_closed(tmp_path, monkeypatch):
    source = tmp_path / 'backlot' / 'server.py'
    source.parent.mkdir()
    source.write_bytes(b'x' * 2_000_001)
    assert identity.fingerprint(tmp_path)['reason'] == 'source_too_large'
    from pathlib import Path
    def denied(*args, **kwargs):
        raise PermissionError('denied')
    monkeypatch.setattr(Path, 'open', denied)
    assert identity.fingerprint(tmp_path)['reason'] == 'source_unreadable'
