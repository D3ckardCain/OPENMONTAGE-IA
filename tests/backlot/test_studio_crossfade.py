"""New centred crossfade cases only; no previously approved suites."""
from copy import deepcopy
import re
import subprocess
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit, studio_editor_render as render
from lib.studio_crossfade import handles
from tests.backlot.test_studio_editor import project, command, add


def pair(project):
    pid, key, _ = project
    first = add(pid, key)
    command(pid, 'trim', id=first, in_seconds=1, out_seconds=4)
    second = add(pid, key)
    command(pid, 'trim', id=second, in_seconds=5, out_seconds=8)
    return pid, first, second


def test_crossfade_keeps_clock_other_tracks_history_and_reopen(project):
    pid, first, second = pair(project)
    key = project[1]
    command(pid, 'layer_add', source_id=key, in_seconds=1, out_seconds=3, start_seconds=2)
    command(pid, 'title_add', text='Prueba', start_seconds=2, end_seconds=4)
    command(pid, 'marker_add', seconds=3, label='Corte original')
    command(pid, 'subtitles', srt='1\n00:00:02,500 --> 00:00:03,500\nContexto conservado.\n')
    before = edit.state(pid)
    value = command(pid, 'transition', id=second, type='crossfade', duration_seconds=1)
    edl = value['edit_decisions']
    assert edit.duration(edl) == edit.duration(before['edit_decisions']) == 6
    for field in ('layers', 'titles', 'markers', 'cues', 'sources', 'audio_tracks'):
        assert edl.get(field) == before['edit_decisions'].get(field)
    assert edl['cuts'][0] == before['edit_decisions']['cuts'][0]
    assert handles(edl, 0) == (0, .5) and handles(edl, 1) == (.5, 0)
    digest = value['render_sha256']
    command(pid, 'undo'); assert edit.state(pid)['edit_decisions'] == before['edit_decisions']
    command(pid, 'redo'); command(pid, 'save')
    assert edit.state(pid)['render_sha256'] == digest
    command(pid, 'transition', id=second, type='none')
    assert edit.state(pid)['edit_decisions'] == before['edit_decisions']


def test_source_handles_fades_locks_and_gaps_reject_atomically(project):
    pid, first, second = pair(project)
    command(pid, 'transition', id=second, type='crossfade', duration_seconds=1)
    for operation, data in [
        ('trim', dict(id=first, in_seconds=7, out_seconds=10)),
        ('trim', dict(id=second, in_seconds=0, out_seconds=3)),
        ('clip', dict(id=first, fade_out=.1)),
        ('delete_keep_gap', dict(ids=[first])),
        ('output_custom', dict(width=640, height=360, fps=29)),
    ]:
        before = edit.state(pid)
        with pytest.raises(ValueError): command(pid, operation, **data)
        assert edit.state(pid) == before
    command(pid, 'flags', id=first, locked=True)
    before = edit.state(pid)
    with pytest.raises(edit.Conflict): command(pid, 'transition', id=second, type='none')
    assert edit.state(pid) == before


def test_quantization_speed_and_window_overlap(project):
    pid, first, second = pair(project)
    value = command(pid, 'transition', id=second, type='crossfade', duration_seconds=1.1)
    assert value['edit_decisions']['cuts'][1]['transition']['duration_seconds'] == 26/24
    command(pid, 'clip', id=first, speed=2)
    _, filters, _, _ = render.plan(pid, edit.state(pid)['edit_decisions'])
    assert any('end=5.083333333333333' in f for f in filters)
    third = add(pid, project[1]); command(pid, 'trim', id=third, in_seconds=5, out_seconds=8)
    before = edit.state(pid)
    with pytest.raises(ValueError, match='transiciones exceden'):
        command(pid, 'batch', operations=[
            dict(operation='transition', id=third, type='crossfade', duration_seconds=1),
            dict(operation='trim', id=second, in_seconds=5, out_seconds=5.5),
        ])
    assert edit.state(pid) == before


def test_preview_export_mixed_transitions_keep_absolute_offsets(project):
    pid, first, second = pair(project)
    command(pid, 'transition', id=second, type='crossfade', duration_seconds=1)
    third = add(pid, project[1]); command(pid, 'trim', id=third, in_seconds=2, out_seconds=5)
    value = command(pid, 'transition', id=third, type='dip_black', duration_seconds=.25)
    edl = value['edit_decisions']
    graphs = [render.plan(pid, edl, preview)[1] for preview in (False, True)]
    # Output sizes differ by design; the transition/mix clocks must be identical.
    assert graphs[0][6:] == graphs[1][6:]
    assert any('xfade=transition=fade:duration=1:offset=2.5' in f for f in graphs[0])
    assert any('acrossfade=d=1:o=1:c1=tri:c2=tri' in f for f in graphs[0])
    assert any('concat=n=2:v=1:a=1' in f for f in graphs[0])
    assert any('fade=t=out:st=3.25:d=0.25' in f for f in graphs[0])
    assert any('trim=end_frame=216' in f for f in graphs[0])


def test_agent_api_crossfade_capability_and_revision(project, monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid, first, second = pair(project)
    client = TestClient(create_app(), base_url='http://127.0.0.1:4750')
    def transport(path, data=None):
        response = client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path, json=data)
        assert response.status_code == 200, response.text
        return response.json()
    monkeypatch.setattr(bridge, 'request', transport)
    assert 'crossfade' in client.get('/api/studio/editor/capabilities').json()['commands']
    value = bridge.StudioProjectEdit().execute(dict(project_id=pid, action='command', command=dict(
        operation='transition', type='crossfade', id=second, duration_seconds=1, revision=edit.state(pid)['revision'])))
    assert value.success and edit.state(pid)['events'][-1]['origin'] == 'agent'


def test_crossfade_base_audio_has_exact_sample_grid_before_joins(project):
    pid, first, second = pair(project)
    command(pid, 'transition', id=second, type='crossfade', duration_seconds=1)
    third = add(pid, project[1]); command(pid, 'trim', id=third, in_seconds=2, out_seconds=3)
    edl = edit.state(pid)['edit_decisions']
    _, filters, _, _ = render.plan(pid, edl)
    tracks = [line for line in filters if line.startswith(('[0:a:0]', '[1:a:0]', '[2:a:0]'))]
    for line, count in zip(tracks, (168000, 168000, 48000)):
        assert f'asetpts=N/SR/TB,apad,atrim=end_sample={count},asetpts=N/SR/TB' in line
    assert edit.duration(edl) == 7


def test_crossfade_render_contract_only_invalidates_crossfade_outputs(project, monkeypatch):
    from lib import studio_crossfade
    pid, first, second = pair(project)
    plain = deepcopy(edit.state(pid)['edit_decisions']); plain_digest = edit.render_digest(plain)
    cross = command(pid, 'transition', id=second, type='crossfade', duration_seconds=1)['edit_decisions']
    cross_digest = edit.render_digest(cross)
    monkeypatch.setattr(studio_crossfade, 'RENDER_CONTRACT', 'future-engine-contract')
    assert edit.render_digest(plain) == plain_digest
    assert edit.render_digest(cross) != cross_digest


def test_real_ffmpeg_mixed_join_audio_pts_are_contiguous(project):
    from lib.media_executables import find_media
    executable = find_media('ffmpeg')
    if not executable:
        pytest.skip('Existing FFmpeg unavailable; never download it from a test')
    pid, first, second = pair(project)
    third = add(pid, project[1]); command(pid, 'trim', id=third, in_seconds=2, out_seconds=3)
    fourth = add(pid, project[1]); command(pid, 'trim', id=fourth, in_seconds=2, out_seconds=3)
    command(pid, 'transition', id=second, type='crossfade', duration_seconds=1)
    command(pid, 'transition', id=fourth, type='crossfade', duration_seconds=.5)
    command(pid, 'output_custom', width=64, height=64, fps=8)
    edl = edit.state(pid)['edit_decisions']
    _, filters, _, _ = render.plan(pid, edl)
    args = []
    for frequency in (440, 880, 660, 330):
        args += ['-f', 'lavfi', '-i', 'color=c=blue:s=64x64:r=8:d=10[out0];'
                 f'sine=frequency={frequency}:sample_rate=48000:duration=10[out1]']
    filters[-1] = filters[-1].replace('[mix]', ',ashowinfo[mix]')
    filters.append('[montage]nullsink')
    process = subprocess.run([executable, '-nostdin', '-v', 'info', *args,
        '-filter_complex', ';'.join(filters), '-map', '[mix]', '-f', 'null', '-'],
        capture_output=True, timeout=20)
    assert process.returncode == 0, process.stderr.decode('utf-8', 'replace')[-2000:]
    frames = re.findall(r'ashowinfo[^\n]*\bpts:(-?\d+)[^\n]*nb_samples:(\d+)', process.stderr.decode())
    assert frames
    cursor = 0
    for pts, count in frames:
        assert int(pts) == cursor, 'Audio packet overlap/gap at a mixed crossfade/hard join'
        cursor += int(count)
    assert cursor == round(edit.duration(edl) * 48000)


def test_removing_crossfade_restores_exact_non_cross_graph_and_digest(project):
    pid, first, second = pair(project)
    third = add(pid, project[1])
    command(pid, 'transition', id=third, type='dip_black', duration_seconds=.25)
    baseline = edit.state(pid)
    graph = render.plan(pid, baseline['edit_decisions'])
    assert any('concat=n=3:v=1:a=1' in line for line in graph[1])
    assert not any('xfade=' in line for line in graph[1])
    command(pid, 'transition', id=second, type='crossfade', duration_seconds=1)
    value = command(pid, 'transition', id=second, type='none')
    assert value['render_sha256'] == baseline['render_sha256']
    assert render.plan(pid, value['edit_decisions']) == graph
