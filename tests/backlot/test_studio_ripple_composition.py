"""Global ripple through the actual shared API, on copies of the official fixture.

Media bytes/probe are synthetic. These tests do not claim AV playback or rendering.
"""
from copy import deepcopy
import json
import shutil

import pytest
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import production_studio as studio, studio_editor as edit, studio_editor_render as render
from tests.backlot.test_studio_editor import project, command, add
from tests.backlot.test_studio_timeline_ops import audio_source


@pytest.fixture
def ripple_copy(project, monkeypatch):
    original, video, _ = project
    ids = []
    for _ in range(3):
        clip = add(original, video)
        command(original, 'trim', id=clip, in_seconds=0, out_seconds=2)
        ids.append(clip)
    audio = audio_source(original, monkeypatch)
    value = command(original, 'add', source_id=audio)
    audio_id = value['edit_decisions']['audio_tracks'][0]['id']
    command(original, 'audio_trim_position', id=audio_id, in_seconds=1, out_seconds=2, start_seconds=4)
    command(original, 'layer_add', source_id=video, in_seconds=1, out_seconds=2, start_seconds=4)
    command(original, 'title_add', text='Manual title', start_seconds=4, end_seconds=5, size=80, position='top')
    command(original, 'subtitles', srt='1\n00:00:04,000 --> 00:00:05,000\nManual cue\n')
    command(original, 'marker_add', seconds=4.5, label='Following')
    source = studio.project_path(original)
    preserved = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    clone = original + '-ripple-copy'
    target = studio.PROJECTS_DIR / clone
    assert target.resolve().is_relative_to(studio.PROJECTS_DIR.resolve())
    shutil.copytree(source, target)
    metadata = studio.read_json(target / 'project.json')
    studio.save_json(target / 'project.json', {**metadata, 'project_id': clone})
    try:
        yield clone, video, audio_id, ids
    finally:
        assert {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()} == preserved


def api_command(client, pid, operation, origin='user', **params):
    revision = client.get('/api/studio/editor/' + pid).json()['revision']
    route = '/agent-command' if origin == 'agent' else '/command'
    return client.post('/api/studio/editor/' + pid + route,
                       json={'operation': operation, 'revision': revision, **params})


def accepted(client, pid, operation, **params):
    response = api_command(client, pid, operation, **params)
    assert response.status_code == 200, response.text
    return response.json()


def test_documented_ripple_layer_title_sync_undo_redo_reopen(ripple_copy):
    pid, _, _, ids = ripple_copy
    before = deepcopy(edit.state(pid))
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        response = api_command(client, pid, 'ripple_delete', ids=[ids[1]])
        assert response.status_code == 200, response.text
        after = response.json()
        edl = after['edit_decisions']
        assert edit.duration(edl) == 4
        assert [c['id'] for c in edl['cuts']] == [ids[0], ids[2]]
        assert edl['layers'][0]['start_seconds'] == 2
        assert edl['titles'][0]['start_seconds'] == 2 and edl['titles'][0]['end_seconds'] == 3
        assert edl['audio_tracks'][0]['start_seconds'] == 2
        assert [(c['start_seconds'], c['end_seconds']) for c in edl['cues']] == [(2, 3)]
        assert edl['markers'][0]['seconds'] == 2.5
        assert edl['sources'] == before['edit_decisions']['sources']
        assert after['revision'] == before['revision'] + 1
        for key in ('layers', 'audio_tracks'):
            assert edl[key][0]['id'] == before['edit_decisions'][key][0]['id']
            assert edl[key][0]['in_seconds'] == 1 and edl[key][0]['out_seconds'] == 2
        _, filters, _, _ = render.plan(pid, edl)
        assert any('+2.0/TB' in f and '[layer0]' in f for f in filters)
        assert api_command(client, pid, 'undo', origin='agent').json()['edit_decisions'] == before['edit_decisions']
        assert api_command(client, pid, 'redo').json()['edit_decisions'] == edl
        assert api_command(client, pid, 'save', origin='agent').status_code == 200
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as reopened:
        saved = reopened.get('/api/studio/editor/' + pid).json()
        assert saved['edit_decisions'] == edl
        assert saved['render_sha256'] == after['render_sha256']
        assert json.loads((studio.project_path(pid) / edit.ARTIFACT).read_text(encoding='utf-8')) == saved
        assert api_command(reopened, pid, 'undo').json()['edit_decisions'] == before['edit_decisions']
        assert api_command(reopened, pid, 'redo', origin='agent').json()['edit_decisions'] == edl


@pytest.mark.parametrize('speed,expected', [
    (.5, [(1, 1, 1.5), (2, 2.5, 3)]),
    (1, [(1, 1, 2), (2, 4, 5)]),
    (2, [(1, 1, 3), (2, 7, 9)]),
])
def test_crossing_layers_audio_titles_cues_split_with_source_mapping(ripple_copy, speed, expected):
    pid, _, audio, ids = ripple_copy
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        initial = edit.state(pid)['edit_decisions']
        layer, title = initial['layers'][0], initial['titles'][0]
        accepted(client, pid, 'layer_update', id=layer['id'], start_seconds=1, in_seconds=1,
                 out_seconds=1+4*speed, speed=speed)
        accepted(client, pid, 'audio_trim_position', id=audio, start_seconds=1,
                 in_seconds=1, out_seconds=1+4*speed)
        accepted(client, pid, 'clip', id=audio, track='audio', speed=speed, fade_in=.5, fade_out=.5)
        accepted(client, pid, 'title_update', id=title['id'], text=title['text'], start_seconds=1,
                 end_seconds=5, size=title['size'], position=title['position'])
        accepted(client, pid, 'subtitles', srt='1\n00:00:01,000 --> 00:00:05,000\nCrossing cue\n')
        before = edit.state(pid)['edit_decisions']
        after = accepted(client, pid, 'ripple_delete', ids=[ids[1]])['edit_decisions']
        for key in ('layers', 'audio_tracks'):
            assert [(c['start_seconds'], c['in_seconds'], c['out_seconds']) for c in after[key]] == expected
            assert len({c['id'] for c in after[key]}) == 2
            assert after[key][0]['id'] == before[key][0]['id']
            assert all(c['source_id'] == before[key][0]['source_id'] and c['speed'] == speed for c in after[key])
        assert [(c['fade_in'], c['fade_out']) for c in after['audio_tracks']] == [(.5, 0), (0, .5)]
        assert [(t['start_seconds'], t['end_seconds']) for t in after['titles']] == [(1, 2), (2, 3)]
        assert len({t['id'] for t in after['titles']}) == 2
        assert after['titles'][0]['id'] == title['id']
        assert all((t['text'], t['size'], t['position']) == (title['text'], 80, 'top') for t in after['titles'])
        assert [(c['start_seconds'], c['end_seconds'], c['text']) for c in after['cues']] == [(1, 2, 'Crossing cue'), (2, 3, 'Crossing cue')]
        assert all((l['x'], l['y'], l['width'], l['height'], l['opacity']) == (.65, .05, .3, .3, 1) for l in after['layers'])
        assert after['sources'] == before['sources']
        assert accepted(client, pid, 'undo')['edit_decisions'] == before
        assert accepted(client, pid, 'redo', origin='agent')['edit_decisions'] == after


def test_nonadjacent_removals_share_one_global_clock(ripple_copy):
    pid, video, audio, ids = ripple_copy
    fourth = add(pid, video)
    command(pid, 'trim', id=fourth, in_seconds=0, out_seconds=2)
    value = edit.state(pid)['edit_decisions']
    command(pid, 'layer_update', id=value['layers'][0]['id'], in_seconds=0, out_seconds=8, start_seconds=0)
    command(pid, 'title_update', id=value['titles'][0]['id'], text='Whole', start_seconds=0, end_seconds=8)
    command(pid, 'audio_trim_position', id=audio, in_seconds=0, out_seconds=8, start_seconds=0)
    command(pid, 'subtitles', srt='1\n00:00:00,000 --> 00:00:08,000\nWhole cue\n')
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        before = edit.state(pid)['edit_decisions']
        after = accepted(client, pid, 'ripple_delete', ids=[ids[0], ids[2]])['edit_decisions']
        assert edit.duration(after) == 4
        for key in ('layers', 'audio_tracks'):
            assert [(c['start_seconds'], c['in_seconds'], c['out_seconds']) for c in after[key]] == [(0, 2, 4), (2, 6, 8)]
        for key in ('titles', 'cues'):
            assert [(c['start_seconds'], c['end_seconds']) for c in after[key]] == [(0, 2), (2, 4)]
        assert after['markers'] == []
        assert accepted(client, pid, 'undo')['edit_decisions'] == before
        assert accepted(client, pid, 'redo')['edit_decisions'] == after


def test_touching_boundaries_and_gap_delete_do_not_shift_earlier_elements(ripple_copy):
    pid, _, audio, ids = ripple_copy
    value = edit.state(pid)['edit_decisions']
    command(pid, 'layer_update', id=value['layers'][0]['id'], start_seconds=0, in_seconds=0, out_seconds=2)
    command(pid, 'title_update', id=value['titles'][0]['id'], text='Before', start_seconds=0, end_seconds=2)
    command(pid, 'audio_trim_position', id=audio, start_seconds=0, in_seconds=0, out_seconds=2)
    command(pid, 'subtitles', srt='1\n00:00:00,000 --> 00:00:02,000\nBefore\n')
    command(pid, 'marker_add', seconds=2, label='Start removed')
    command(pid, 'marker_add', seconds=4, label='End removed')
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        before = edit.state(pid)['edit_decisions']
        gap = accepted(client, pid, 'delete_keep_gap', ids=[ids[1]])['edit_decisions']
        assert edit.duration(gap) == 6
        assert all(gap[k] == before[k] for k in ('layers', 'titles', 'audio_tracks', 'cues', 'markers'))
        accepted(client, pid, 'undo')
        after = accepted(client, pid, 'ripple_delete', ids=[ids[1]])['edit_decisions']
        assert all(after[k] == before[k] for k in ('layers', 'titles', 'audio_tracks', 'cues'))
        assert [(m['label'], m['seconds']) for m in after['markers']] == [('End removed', 2), ('Following', 2.5)]


def test_split_layers_keep_compositing_order(ripple_copy):
    pid, video, _, ids = ripple_copy
    layer = edit.state(pid)['edit_decisions']['layers'][0]
    command(pid, 'layer_update', id=layer['id'], start_seconds=1, in_seconds=0, out_seconds=4, opacity=.2)
    command(pid, 'layer_add', source_id=video, start_seconds=1, in_seconds=1, out_seconds=5, opacity=.8)
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        before = edit.state(pid)['edit_decisions']
        after = accepted(client, pid, 'ripple_delete', ids=[ids[1]])['edit_decisions']
        assert [c['opacity'] for c in after['layers']] == [.2, .2, .8, .8]
        assert [c['start_seconds'] for c in after['layers']] == [1, 2, 1, 2]
        assert after['layers'][0]['id'] == before['layers'][0]['id']
        assert after['layers'][2]['id'] == before['layers'][1]['id']
        assert len({c['id'] for c in after['layers']}) == 4
        assert accepted(client, pid, 'undo')['edit_decisions'] == before
        assert accepted(client, pid, 'redo')['edit_decisions'] == after


@pytest.mark.parametrize('selection', ['last', 'all'])
def test_elements_fully_inside_removed_time_are_removed_together(ripple_copy, selection):
    pid, _, _, ids = ripple_copy
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        before = edit.state(pid)['edit_decisions']
        after = accepted(client, pid, 'ripple_delete', ids=ids if selection == 'all' else [ids[2]])['edit_decisions']
        assert edit.duration(after) == (0 if selection == 'all' else 4)
        assert all(after[k] == [] for k in ('layers', 'titles', 'audio_tracks', 'cues', 'markers'))
        assert accepted(client, pid, 'undo')['edit_decisions'] == before


@pytest.mark.parametrize('kind', ['video', 'audio', 'layers', 'titles'])
def test_ripple_respects_locks_and_rolls_back_every_track(ripple_copy, kind):
    pid, _, audio, ids = ripple_copy
    if kind in ('video', 'audio'):
        command(pid, 'flags', track=kind, id=audio if kind == 'audio' else ids[2], locked=True)
    else:
        # Persisted lock metadata is respected; this does not add a new lock UI.
        value = edit.state(pid)
        value['edit_decisions'][kind][0]['locked'] = True
        value['edit_sha256'] = edit.edit_digest(value['edit_decisions'])
        value['render_sha256'] = edit.render_digest(value['edit_decisions'])
        studio.save_json(studio.project_path(pid)/edit.ARTIFACT, value)
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        before = edit.state(pid)
        response = api_command(client, pid, 'ripple_delete', ids=[ids[1]])
        assert response.status_code == 409 and edit.state(pid) == before


@pytest.mark.parametrize('transition_index', [1, 2])
def test_ripple_cannot_change_outgoing_transition_of_locked_predecessor(ripple_copy, transition_index):
    pid, _, _, ids = ripple_copy
    command(pid, 'transition', id=ids[transition_index], duration_seconds=.25)
    command(pid, 'flags', id=ids[0], locked=True)
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        before = edit.state(pid)
        assert api_command(client, pid, 'ripple_delete', ids=[ids[1]]).status_code == 409
        assert edit.state(pid) == before


def test_transition_on_surviving_boundary_remains_and_invalid_first_boundary_rejects(ripple_copy):
    pid, _, _, ids = ripple_copy
    command(pid, 'transition', id=ids[2], duration_seconds=.25)
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        before = edit.state(pid)
        after = accepted(client, pid, 'ripple_delete', ids=[ids[0]])['edit_decisions']
        assert after['cuts'][1]['transition'] == before['edit_decisions']['cuts'][2]['transition']
        assert accepted(client, pid, 'undo')['edit_decisions'] == before['edit_decisions']
        accepted(client, pid, 'transition', id=ids[1], duration_seconds=.25)
        checkpoint = edit.state(pid)
        assert api_command(client, pid, 'ripple_delete', ids=[ids[0]]).status_code == 400
        assert edit.state(pid) == checkpoint


@pytest.mark.parametrize('limit', ['layers', 'titles', 'subframe'])
def test_ripple_rejects_fragment_limits_without_partial_changes(ripple_copy, limit):
    pid, video, _, ids = ripple_copy
    if limit == 'layers':
        for _ in range(3):
            command(pid, 'layer_add', source_id=video, in_seconds=0, out_seconds=4, start_seconds=1)
    elif limit == 'titles':
        for _ in range(19):
            command(pid, 'title_add', text='Crossing', start_seconds=1, end_seconds=5)
    else:
        layer = edit.state(pid)['edit_decisions']['layers'][0]
        command(pid, 'layer_update', id=layer['id'], start_seconds=1.99, in_seconds=0, out_seconds=2.51)
    with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
        before = edit.state(pid)
        assert api_command(client, pid, 'ripple_delete', ids=[ids[1]]).status_code == 400
        assert edit.state(pid) == before
