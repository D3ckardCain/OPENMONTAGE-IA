"""Transactional timeline model and compositor contracts; fixture bytes are not AV."""
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import production_studio as studio, studio_editor as edit, studio_editor_render as render
from tests.backlot.test_studio_editor import project, command, add


def audio_source(pid, monkeypatch):
    path = studio.project_path(pid) / 'assets/audio.wav'
    path.write_bytes(b'OFFLINE NON-MEDIA fixture')
    monkeypatch.setattr(edit, 'probe', lambda path: {'duration': 10., 'kind': 'audio', 'audio': True, 'width': None, 'height': None})
    value = edit.register(pid, 'assets/audio.wav', edit.state(pid)['revision'])
    return next(key for key, info in value['edit_decisions']['sources'].items() if info['kind'] == 'audio')


def test_batch_is_one_undo_and_rejects_partial_writes(project):
    pid, key, _ = project
    clip = add(pid, key)
    before = edit.state(pid)
    value = command(pid, 'batch', operations=[{'operation': 'trim', 'id': clip, 'in_seconds': 1, 'out_seconds': 9},
                                            {'operation': 'split', 'id': clip, 'at': 5}])
    assert value['revision'] == before['revision'] + 1
    assert len(value['edit_decisions']['cuts']) == 2
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions'] == before['edit_decisions']
    checkpoint = edit.state(pid)
    with pytest.raises(ValueError):
        command(pid, 'batch', operations=[{'operation': 'trim', 'id': clip, 'in_seconds': 2, 'out_seconds': 8},
                                          {'operation': 'remove', 'id': 'missing'}])
    assert edit.state(pid) == checkpoint
    with pytest.raises(ValueError):
        command(pid, 'batch', operations=[{'operation': 'undo'}])


def test_duplicate_selection_and_audio_start_are_reversible(project, monkeypatch):
    pid, key, _ = project
    first, second = add(pid, key), add(pid, key)
    before = edit.state(pid)
    value = command(pid, 'duplicate', ids=[first, second])
    cuts = value['edit_decisions']['cuts']
    assert len(cuts) == 4 and len({c['id'] for c in cuts}) == 4
    assert [c['id'] for c in cuts[:2]] == [first, second]
    assert cuts[2]['source_id'] == key and cuts[2]['in_seconds'] == 0
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions'] == before['edit_decisions']
    key = audio_source(pid, monkeypatch)
    value = command(pid, 'add', source_id=key)
    audio = value['edit_decisions']['audio_tracks'][0]
    value = command(pid, 'duplicate', track='audio', ids=[audio['id']])
    assert value['edit_decisions']['audio_tracks'][1]['start_seconds'] == 10


def test_delete_keeps_real_gap_in_compositor_and_undo(project):
    pid, key, _ = project
    first, second = add(pid, key), add(pid, key)
    before = edit.state(pid)
    value = command(pid, 'delete_keep_gap', ids=[first])
    assert edit.duration(value['edit_decisions']) == 20
    gap = value['edit_decisions']['cuts'][0]
    assert gap['kind'] == 'gap' and gap['source_id'] is None
    args, filters, _, _ = render.plan(pid, value['edit_decisions'], True)
    assert 'lavfi' in args and any('color=c=black' in part for part in args)
    assert any('concat=n=2' in line for line in filters)
    assert value['render_sha256'] != before['render_sha256']
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions'] == before['edit_decisions']


def test_ripple_splits_audio_and_adjusts_cues_markers_together(project, monkeypatch):
    pid, key, _ = project
    add(pid, key);middle = add(pid, key);add(pid, key)
    key = audio_source(pid, monkeypatch)
    value = command(pid, 'add', source_id=key)
    audio = value['edit_decisions']['audio_tracks'][0]
    command(pid, 'clip', id=audio['id'], track='audio', start_seconds=5, speed=.5)
    command(pid, 'subtitles', srt='1\n00:00:08,000 --> 00:00:12,000\nCrossing\n\n2\n00:00:22,000 --> 00:00:24,000\nFollowing\n')
    command(pid, 'marker_add', seconds=15, label='Removed')
    command(pid, 'marker_add', seconds=25, label='Following')
    before = edit.state(pid)
    value = command(pid, 'ripple_delete', ids=[middle])
    edl = value['edit_decisions']
    assert edit.duration(edl) == 20
    assert [(c['start_seconds'], c['in_seconds'], c['out_seconds']) for c in edl['audio_tracks']] == [(5, 0, 2.5), (10, 7.5, 10)]
    assert len({c['id'] for c in edl['audio_tracks']}) == 2
    assert [(c['start_seconds'], c['end_seconds']) for c in edl['cues']] == [(8, 10), (12, 14)]
    assert [(m['label'], m['seconds']) for m in edl['markers']] == [('Following', 15)]
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions'] == before['edit_decisions']


def test_locks_are_enforced_and_metadata_keeps_render_current(project):
    pid, key, _ = project
    first, second = add(pid, key), add(pid, key)
    before = edit.state(pid)
    command(pid, 'flags', id=second, locked=True)
    assert edit.state(pid)['render_sha256'] == before['render_sha256']
    for operation, params in [('trim', {'id': first, 'in_seconds': 1, 'out_seconds': 9}),
                              ('duplicate', {'ids': [first]}), ('ripple_delete', {'ids': [first]}),
                              ('move', {'id': first, 'index': 1})]:
        checkpoint = edit.state(pid)
        with pytest.raises(edit.Conflict):
            command(pid, operation, **params)
        assert edit.state(pid) == checkpoint
    studio.save_json(studio.project_path(pid) / 'artifacts/manual_render.json',
                     {'status': 'completed', 'edit_sha256': before['edit_sha256'], 'render_sha256': before['render_sha256']})
    command(pid, 'marker_add', seconds=1, label='Metadata')
    assert render.status(pid)['current'] is True
    command(pid, 'flags', id=second, locked=False)
    command(pid, 'trim', id=first, in_seconds=1, out_seconds=9)
    assert render.status(pid)['current'] is False


def test_audio_trim_position_is_atomic_and_solo_reaches_audio_graph(project, monkeypatch):
    pid, key, _ = project
    add(pid, key)
    key = audio_source(pid, monkeypatch)
    value = command(pid, 'add', source_id=key)
    audio = value['edit_decisions']['audio_tracks'][0]
    before = edit.state(pid)
    value = command(pid, 'audio_trim_position', id=audio['id'], in_seconds=2, out_seconds=8, start_seconds=3)
    assert value['edit_decisions']['audio_tracks'][0]['start_seconds'] == 3
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions'] == before['edit_decisions']
    value = command(pid, 'flags', id=audio['id'], track='audio', solo=True)
    _, filters, _, _ = render.plan(pid, value['edit_decisions'], True)
    assert any('[0:a:0]' in f and 'volume=0' in f for f in filters)
    assert any('[1:a:0]' in f and 'volume=1' in f for f in filters)


def test_capabilities_are_explicit_for_frontend_and_agent(project):
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        data = client.get('/api/studio/editor/capabilities').json()
    assert data['version'] == '2.0'
    assert {'batch', 'duplicate', 'markers', 'delete_keep_gap', 'ripple_delete'} <= set(data['commands'])
