"""New stereo-balance contract only; no old suites, voice synthesis or renders."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit, studio_editor_render as render
from lib.studio_audio_balance import filter_suffix
from tests.backlot.test_studio_editor import project, command, add


def test_balance_history_reopen_and_neutral_render_identity(project):
    pid, key, _ = project
    clip = add(pid, key)
    original = edit.state(pid)
    balanced = command(pid, 'audio_balance', id=clip, balance=-.4)
    assert balanced['edit_decisions']['cuts'][0]['stereo_balance'] == -.4
    assert balanced['render_sha256'] != original['render_sha256']
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions'] == original['edit_decisions']
    command(pid, 'redo'); command(pid, 'save')
    assert edit.state(pid)['render_sha256'] == balanced['render_sha256']
    neutral = command(pid, 'audio_balance', id=clip, balance=0)
    assert neutral['render_sha256'] == original['render_sha256']
    assert 'stereo_balance' not in neutral['edit_decisions']['cuts'][0]


def test_invalid_balance_silent_source_and_lock_are_atomic(project):
    pid, key, _ = project
    clip = add(pid, key)
    for invalid in (True, '0.5', float('nan'), float('inf'), -1.001, 1.001, None):
        before = edit.state(pid)
        with pytest.raises(ValueError): command(pid, 'audio_balance', id=clip, balance=invalid)
        assert edit.state(pid) == before
    before = edit.state(pid)
    with pytest.raises(ValueError): command(pid, 'audio_balance', id=clip, track='unknown', balance=0)
    assert edit.state(pid) == before
    command(pid, 'flags', id=clip, locked=True)
    before = edit.state(pid)
    with pytest.raises(edit.Conflict): command(pid, 'audio_balance', id=clip, balance=.4)
    assert edit.state(pid) == before
    edl = deepcopy(before['edit_decisions']); edl['cuts'][0]['locked'] = False
    edl['sources'][key]['audio'] = False
    with pytest.raises(ValueError, match='no contiene audio'):
        edit._apply_edit(edl, dict(operation='audio_balance', id=clip, balance=1))


def test_balance_batch_rollback_and_copy_clock_preservation(project):
    from lib.studio_timeline_ops import _ripple_sources
    pid, key, _ = project
    clip = add(pid, key)
    command(pid, 'audio_balance', id=clip, balance=.25)
    before = edit.state(pid)
    with pytest.raises(ValueError):
        command(pid, 'batch', operations=[dict(operation='audio_balance', id=clip, balance=-1),
                                         dict(operation='audio_balance', id=clip, balance=2)])
    assert edit.state(pid) == before
    value = command(pid, 'split', id=clip, at=5)
    assert [c['stereo_balance'] for c in value['edit_decisions']['cuts']] == [.25, .25]
    pieces = _ripple_sources([{**value['edit_decisions']['cuts'][0], 'start_seconds': 1}], [(2, 3)])
    assert len(pieces) == 2 and all(c['stereo_balance'] == .25 for c in pieces)


def test_preview_export_video_audio_channels_use_same_filter(project):
    pid, key, _ = project
    clip = add(pid, key)
    # Registered fixture is mocked, tests below inspect graph only, not AV.
    value = command(pid, 'audio_balance', id=clip, balance=-.4)
    edl = value['edit_decisions']
    audio = deepcopy(edl['cuts'][0]); audio.update(id='independent-audio', start_seconds=2)
    edl['audio_tracks'].append(audio)
    edit._apply_edit(edl, dict(operation='audio_balance', track='audio', id=audio['id'], balance=1))
    for preview in (True, False):
        _, filters, _, _ = render.plan(pid, edl, preview)
        assert any('c0=1*c0|c1=0.6*c1' in line and '[a0]' in line for line in filters)
        assert any('c0=0*c0|c1=1*c1' in line and '[a1]' in line for line in filters)
    assert filter_suffix({}) == filter_suffix({'stereo_balance': 0}) == ''


def test_agent_api_uses_same_revision_and_undo(project, monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid, key, _ = project
    clip = add(pid, key)
    client = TestClient(create_app(), base_url='http://127.0.0.1:4750')
    def transport(path, data=None, **kwargs):
        url = '/api/studio/editor/' + path
        response = client.get(url) if data is None else client.post(url, json=data)
        assert response.status_code == 200, response.text
        return response.json()
    monkeypatch.setattr(bridge, 'request', transport)
    assert 'audio_balance' in client.get('/api/studio/editor/capabilities').json()['commands']
    result = bridge.StudioProjectEdit().execute(dict(project_id=pid, action='command', command=dict(
        operation='audio_balance', id=clip, balance=.75, revision=edit.state(pid)['revision'])))
    assert result.success and edit.state(pid)['edit_decisions']['cuts'][0]['stereo_balance'] == .75
    assert edit.state(pid)['events'][-1]['origin'] == 'agent'
    command(pid, 'undo')
    assert 'stereo_balance' not in edit.state(pid)['edit_decisions']['cuts'][0]
