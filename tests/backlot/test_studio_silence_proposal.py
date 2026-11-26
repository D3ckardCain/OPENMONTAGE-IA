"""New numeric silence contract only: no audio, FFmpeg, ASR or renderer calls."""
from copy import deepcopy
from unittest.mock import patch

import pytest

from lib import studio_editor as editor, studio_silence_proposal as silence


@pytest.fixture
def edl():
    value = editor._empty(); value['output']['fps'] = 25
    value['sources'] = {'s': dict(kind='video', sha256='a' * 64, duration=6,
                                  audio=True, path='assets/never-read.mp4')}
    value['cuts'] = [dict(id='c', source_id='s', in_seconds=0, out_seconds=6, speed=1)]
    value['candidate_sets'] = [dict(id='set', source_id='s', source_sha256='a' * 64,
        transcript_sha256='b' * 64, coverage=dict(processed_ranges=[[0, 6]]),
        provenance=dict(language='es', binding='synthetic_no_model'),
        words=[dict(index=0, word='No', start=.9, end=1.1),
               dict(index=1, word='borres.', start=3, end=3.4)])]
    value['cues'] = [dict(start_seconds=3, end_seconds=3.4, text='No borres.')]
    return value


def payload(edl):
    return dict(revision=0, set_id='set', input_edl_sha256=editor.edit_digest(edl),
                word_data_sha256=editor.edit_digest(edl['candidate_sets'][0]['words']),
                analysis=dict(source_id='s', source_sha256='a' * 64, clock='source_seconds',
                              method='synthetic_fixture', threshold_db=-35,
                              min_silence_seconds=.3, processed_ranges=[[0, 6]],
                              intervals=[[.5, 2.5]]))


def test_protects_negation_rounds_inward_and_never_touches_project_or_media(edl):
    before = deepcopy(edl)
    with patch('subprocess.Popen') as spawn, patch.object(editor, 'digest') as hash_file:
        report = silence.draft(edl, payload(edl))
    assert report['ready_for_review'] and not report['apply_available']
    assert report['analysis_provenance']['evidence'] == 'synthetic_not_measured'
    assert [c['frames'] for c in report['candidates']] == [[15, 20], [30, 60]]
    assert all(not c['selected'] and not c['reviewed'] for c in report['candidates'])
    assert edl == before and not report['media_read'] and not report['project_modified']
    assert edl['candidate_sets'][0]['words'][0]['word'] == 'No'
    spawn.assert_not_called(); hash_file.assert_not_called()


def test_unordered_overlaps_are_unioned_without_duplicate_candidates(edl):
    data = payload(edl); data['analysis']['intervals'] = [[1, 2.5], [.5, 1.5], [.5, 1.5]]
    report = silence.draft(edl, data)
    assert len(report['analysis_provenance']['normalized_intervals']) == 1
    assert len(report['candidates']) == 2


@pytest.mark.parametrize('fps', [24, 30, 60])
def test_speed_reorder_and_repeated_source_keep_separate_frame_occurrences(edl, fps):
    edl['output']['fps'] = fps
    edl['cuts'] = [dict(id='fast', source_id='s', in_seconds=0, out_seconds=6, speed=2),
                   dict(id='again', source_id='s', in_seconds=0, out_seconds=6, speed=1)]
    report = silence.draft(edl, payload(edl)); candidates = report['candidates']
    expected = 3 if fps == 24 else 4  # The short fast fragment falls below100ms after inward24fps rounding.
    assert len(candidates) == expected and len({c['id'] for c in candidates}) == expected
    assert next(c for c in candidates if c['clip_id'] == 'again')['timeline']['start_seconds'] >= 3.6
    for c in candidates:
        a, b = c['source']['start_seconds'], c['source']['end_seconds']
        assert b <= .82 + 1e-9 or a >= 1.18 - 1e-9
        assert c['frames'][1] > c['frames'][0]


@pytest.mark.parametrize('field', ['edl', 'words', 'source'])
def test_stale_or_different_binding_rejected(edl, field):
    data = payload(edl)
    if field == 'edl':
        edl['cuts'][0]['speed'] = 2
    elif field == 'words':
        edl['candidate_sets'][0]['words'][0]['word'] = 'Nunca'
        data['input_edl_sha256'] = editor.edit_digest(edl)
    else:
        data['analysis']['source_sha256'] = 'f' * 64
    with pytest.raises(editor.Conflict):
        silence.draft(edl, data)


@pytest.mark.parametrize('intervals', [[[float('nan'), 1]], [[0, float('inf')]], [[True, 2]], [[2, 1]], [[0, 7]]])
def test_bad_numbers_or_source_limits_rejected(edl, intervals):
    data = payload(edl); data['analysis']['intervals'] = intervals
    with pytest.raises(ValueError):
        silence.draft(edl, data)


def test_no_intervals_never_infers_silence_from_word_gaps(edl):
    data = payload(edl); data['analysis']['intervals'] = []
    assert silence.draft(edl, data)['candidates'] == []


def test_padding_can_eliminate_a_silence_without_creating_a_cut(edl):
    data = payload(edl); data['padding_seconds'] = 1.1
    assert silence.draft(edl, data)['candidates'] == []


def test_invalid_threshold_and_rational_fps_rejected_without_conversion(edl):
    data = payload(edl); data['analysis']['threshold_db'] = float('nan')
    with pytest.raises(ValueError):
        silence.draft(edl, data)
    edl['output']['fps'] = 29.97
    with pytest.raises(ValueError, match='FPS entero'):
        silence.draft(edl, payload(edl))


@pytest.mark.parametrize('case', ['acoustic', 'asr', 'partial_word', 'zero_word', 'other_source'])
def test_incomplete_coverage_and_boundary_words_block_entire_proposal(edl, case):
    if case == 'asr':
        edl['candidate_sets'][0]['coverage']['processed_ranges'] = [[0, 4]]
    if case == 'partial_word':
        edl['cuts'][0]['in_seconds'] = 1
    if case == 'zero_word':
        edl['candidate_sets'][0]['words'][0]['end'] = .9
    if case == 'other_source':
        edl['sources']['x'] = {**edl['sources']['s'], 'sha256': 'f' * 64}
        edl['cuts'].append(dict(id='x', source_id='x', in_seconds=0, out_seconds=1, speed=1))
    data = payload(edl)
    if case == 'acoustic':
        data['analysis']['processed_ranges'] = [[0, 3]]
    result = silence.draft(edl, data)
    assert not result['ready_for_review'] and not result['candidates'] and result['blockers']


def test_multiple_guides_and_wrong_clock_are_explicitly_unsupported(edl):
    data = payload(edl); data['guides'] = ['s', 'other']
    with pytest.raises(ValueError, match='multiguía'):
        silence.draft(edl, data)
    del data['guides']; data['analysis']['clock'] = 'timeline_seconds'
    with pytest.raises(ValueError, match='segundos de fuente'):
        silence.draft(edl, data)


def test_read_only_api_agent_contract_and_stale_revision(edl, monkeypatch, tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backlot.editor_routes import create_editor_router
    from lib import production_studio as studio
    from tools.video import studio_project_edit as agent
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path)
    initial = editor.create('Silence numeric QA'); pid = initial['project_id']
    initial['edit_decisions'] = edl
    path = tmp_path / pid / editor.ARTIFACT; studio.save_json(path, initial); before = path.read_bytes()
    async def body(request, *args):
        return await request.json()
    app = FastAPI(); app.include_router(create_editor_router(body)); client = TestClient(app)
    base = '/api/studio/editor/'
    def request(route, data=None, **kw):
        response = client.get(base + route) if data is None else client.post(base + route, json=data)
        return response.json() if response.status_code == 200 else {'_error': response.json()['detail'], '_conflict': response.status_code == 409}
    monkeypatch.setattr(agent, 'request', request)
    result = agent.StudioProjectEdit().execute(dict(project_id=pid, action='silence_proposal', proposal=payload(edl)))
    assert result.success and result.data['ready_for_review']
    assert path.read_bytes() == before and not list((tmp_path / pid / 'assets').rglob('*.mp4'))
    caps = client.get(base + 'capabilities').json()
    assert caps['silence_proposal']['read_only'] and not caps['silence_proposal']['apply_available']
    data = payload(edl); data['revision'] = 1
    assert client.post(base + pid + '/silence-proposal', json=data).status_code == 409
    data = payload(edl); data['analysis']['clock'] = 'timeline_seconds'
    assert client.post(base + pid + '/silence-proposal', json=data).status_code == 400
    assert path.read_bytes() == before
