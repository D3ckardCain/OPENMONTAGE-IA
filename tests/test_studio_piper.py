"""Focused local contract checks; synthesis evidence is recorded separately."""
from pathlib import Path
import pytest
from lib import studio_piper as piper


def test_catalog_does_not_claim_presence_is_synthesis():
    voices = piper.catalog()
    assert len(voices) == 4
    assert all(not v['tested'] for v in voices)
    assert isinstance(next(v for v in voices if v['id'] == 'en_GB-vctk-medium')['blocked'], bool)


@pytest.mark.parametrize('speaker', [-1, 2, '0', True])
def test_reject_unknown_speaker_before_subprocess(monkeypatch, tmp_path, speaker):
    monkeypatch.setattr(piper, 'catalog', lambda: [dict(id='test', available=True, blocked=False, speakers={'M':0,'F':1})])
    with pytest.raises(ValueError, match='Hablante'):
        piper.synthesize('hello', 'test', speaker, tmp_path/'test.wav')
    assert not (tmp_path/'test.wav').exists()


def test_legacy_vctk_blocked_before_subprocess(monkeypatch, tmp_path):
    monkeypatch.setattr(piper, 'catalog', lambda: [dict(id='legacy', available=True, blocked=True)])
    with pytest.raises(ValueError, match='Lessac'):
        piper.synthesize('hello', 'legacy', 0, tmp_path/'test.wav')


def test_api_catalog_and_audio_path_guard():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backlot.editor_routes import create_editor_router
    async def body(request, *args):
        return await request.json()
    app = FastAPI()
    app.include_router(create_editor_router(body))
    client = TestClient(app)
    response = client.get('/api/studio/editor/piper/voices')
    assert response.status_code == 200
    assert len(response.json()) == 4
    assert client.get('/api/studio/editor/test/piper/audio/settings.json').status_code == 400
