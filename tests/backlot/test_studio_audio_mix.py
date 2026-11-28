"""Focused output-mix contracts: no render, inference, or external networking."""
from pathlib import Path

import pytest

from lib import production_studio as studio, studio_editor as edit, studio_editor_render as render
from tests.backlot.test_studio_editor import add, command, project


def test_output_mix_is_shared_reversible_persistent_and_used_by_render_plan(project, monkeypatch):
    pid, key, _ = project
    add(pid, key)
    initial = edit.state(pid)
    initial_render = initial['render_sha256']

    saved = command(pid, 'audio_mix', gain=0.8, normalize=True, target_lufs=-18.5)
    assert saved['edit_decisions']['audio_mix'] == {
        'gain': 0.8, 'normalize': True, 'target_lufs': -18.5
    }
    assert saved['render_sha256'] != initial_render
    _, filters, _, _ = render.plan(pid, saved['edit_decisions'], preview=True)
    mix = next(item for item in filters if '[premix]' in item)
    norm = next(item for item in filters if 'loudnorm=' in item)
    assert 'volume=0.8' in mix
    assert 'loudnorm=I=-18.5' in norm

    command(pid, 'undo')
    assert edit.state(pid)['render_sha256'] == initial_render
    command(pid, 'redo')
    assert edit.state(pid)['edit_decisions']['audio_mix'] == {
        'gain': 0.8, 'normalize': True, 'target_lufs': -18.5
    }
    partial = command(pid, 'audio_mix', gain=0.7)
    assert partial['edit_decisions']['audio_mix'] == {
        'gain': 0.7, 'normalize': True, 'target_lufs': -18.5
    }

    from backlot.server import create_app
    from fastapi.testclient import TestClient
    from tools.video.studio_project_edit import StudioProjectEdit

    client = TestClient(create_app(), base_url='http://127.0.0.1:4750')

    def transport(path, data=None):
        route = '/api/studio/editor/' + path
        response = client.get(route) if data is None else client.post(route, json=data)
        if response.is_error:
            return {'_error': response.json()['detail'], '_conflict': response.status_code == 409}
        return response.json()

    monkeypatch.setattr('tools.video.studio_project_edit.request', transport)
    tool = StudioProjectEdit()
    read = tool.execute({'project_id': pid, 'action': 'read'})
    result = tool.execute({
        'project_id': pid, 'action': 'command',
        'command': {'operation': 'audio_mix', 'revision': read.data['revision'],
                    'gain': 0.65, 'normalize': True, 'target_lufs': -20}
    })
    assert result.success
    assert edit.state(pid)['events'][-1]['origin'] == 'agent'
    assert edit.state(pid)['edit_decisions']['audio_mix'] == {
        'gain': 0.65, 'normalize': True, 'target_lufs': -20.0
    }
    command(pid, 'save')
    assert studio.read_json(studio.project_path(pid) / edit.ARTIFACT) == edit.state(pid)


@pytest.mark.parametrize('payload', [
    {'gain': True}, {'gain': -0.01}, {'gain': 4.01},
    {'normalize': 1}, {'normalize': 'false'},
    {'target_lufs': float('nan')}, {'target_lufs': -40.1}, {'target_lufs': -4.9},
])
def test_output_mix_rejects_invalid_values_atomically(project, payload):
    pid, key, _ = project
    add(pid, key)
    before = edit.state(pid)
    with pytest.raises(ValueError):
        command(pid, 'audio_mix', **payload)
    assert edit.state(pid) == before


def test_output_mix_controls_are_connected_and_gated_by_capability():
    root = Path(__file__).resolve().parents[2]
    js = (root / 'backlot' / 'ui' / 'studio.js').read_text(encoding='utf-8')
    html = (root / 'backlot' / 'ui' / 'studio.html').read_text(encoding='utf-8')
    assert "operation:'audio_mix'" in js
    assert "hasCapability('audio_mix')" in js
    assert 'function renderOutputMix' in js
    assert 'id="audio-output-mix-panel"' in html
    assert 'id="audio-output-mix-form"' in html
    assert 'name="target_lufs"' in html
