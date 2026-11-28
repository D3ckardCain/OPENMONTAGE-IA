"""New focal regressions: synthetic words and metadata only, no ASR/real audio."""
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import studio_editor as edit, production_studio as studio
from tests.backlot.test_studio_editor import project, command


def payload(key):
    words = ['Antes.', 'No', 'recomiendo', 'quitar', 'la', 'protección.', 'Eso', 'sería', 'un', 'error.']
    return {'source_id': key, 'transcript': {'language': 'es', 'model_size': 'synthetic_no_model',
            'word_timestamps': [{'word': word, 'start': i * .5, 'end': i * .5 + .4} for i, word in enumerate(words)]},
            'processed_ranges': [[0, 5]], 'proposals': [{'first_word': 2, 'last_word': 4, 'reason': 'Advertencia técnica que requiere negación y frase completa'}]}


def test_negation_context_word_times_and_partial_coverage_persist(project):
    pid, key, source = project
    before = source.read_bytes()
    before_render = edit.state(pid)['render_sha256']
    result = command(pid, 'candidate_import', **payload(key))
    dataset = result['edit_decisions']['candidate_sets'][0]
    assert result['render_sha256'] == before_render
    item = dataset['candidates'][0]
    assert item['requested_word_span'] == [2, 4] and item['word_span'] == [1, 5]
    assert item['text'] == 'No recomiendo quitar la protección.'
    assert item['start_seconds'] == .5 and item['end_seconds'] == 2.9
    assert item['context_before'] == 'Antes.' and item['context_after'] == 'Eso sería un error.'
    assert item['status'] == 'pending' and item['context_confirmed'] is False
    assert dataset['coverage']['fraction'] == .5 and dataset['coverage']['complete'] is False
    assert dataset['coverage']['unprocessed_ranges'] == [[5., 10.]]
    assert dataset['source_sha256'] == edit.digest(source)
    assert dataset['transcript_original'] == payload(key)['transcript']
    saved = studio.read_json(studio.project_path(pid) / edit.ARTIFACT)
    assert saved['edit_decisions'] == result['edit_decisions']
    command(pid, 'undo')
    assert 'candidate_sets' not in edit.state(pid)['edit_decisions']
    command(pid, 'redo')
    assert edit.state(pid)['edit_decisions']['candidate_sets'][0] == dataset
    assert source.read_bytes() == before


def test_review_required_insert_reuses_trim_undo_and_shared_agent_route(project):
    pid, key, _ = project
    value = command(pid, 'candidate_import', **payload(key))
    dataset = value['edit_decisions']['candidate_sets'][0]
    item = dataset['candidates'][0]
    args = {'set_id': dataset['id'], 'id': item['id']}
    with pytest.raises(ValueError, match='contexto'):
        command(pid, 'candidate_insert', **args)
    with pytest.raises(ValueError, match='Confirma'):
        command(pid, 'candidate_review', status='accepted', **args)
    client = TestClient(create_app(), base_url='http://127.0.0.1')
    response = client.post(f'/api/studio/editor/{pid}/agent-command', json={
        'operation': 'candidate_review', 'revision': edit.state(pid)['revision'],
        'status': 'accepted', 'context_confirmed': True, **args})
    assert response.status_code == 200
    accepted = edit.state(pid)['edit_decisions']
    result = command(pid, 'candidate_insert', **args)
    clip = result['edit_decisions']['cuts'][0]
    assert (clip['in_seconds'], clip['out_seconds']) == (.5, 2.9)
    assert clip['candidate_ref']['word_span'] == [1, 5]
    assert clip['candidate_ref']['transcript_sha256'] == dataset['transcript_sha256']
    with pytest.raises(ValueError, match='ya está'):
        command(pid, 'candidate_insert', **args)
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions'] == accepted
    command(pid, 'redo')
    assert len(edit.state(pid)['edit_decisions']['cuts']) == 1


@pytest.mark.parametrize('case', ['missing_words', 'missing_coverage', 'bad_time', 'out_of_order', 'bad_span', 'gap', 'missing_reason', 'wrong_source_hash'])
def test_invalid_input_rolls_back_without_downloading_or_mutation(project, case):
    pid, key, _ = project
    data = payload(key)
    if case == 'missing_words': data['transcript'].pop('word_timestamps')
    if case == 'missing_coverage': data.pop('processed_ranges')
    if case == 'bad_time': data['transcript']['word_timestamps'][1]['end'] = 99
    if case == 'out_of_order': data['transcript']['word_timestamps'][2]['start'] = 0
    if case == 'bad_span': data['proposals'][0]['first_word'] = True
    if case == 'missing_reason': data['proposals'][0]['reason'] = ''
    if case == 'wrong_source_hash': data['transcript']['source_sha256'] = '0' * 64
    if case == 'gap': data['processed_ranges'] = [[0, 1.4], [1.5, 5]]
    before = deepcopy(edit.state(pid))
    with pytest.raises(ValueError): command(pid, 'candidate_import', **data)
    assert edit.state(pid) == before


def test_coverage_union_offset_and_correction_reset_acceptance(project):
    pid, key, _ = project
    data = payload(key);data.update(time_offset=2, processed_ranges=[[2, 5], [4, 7]])
    result = command(pid, 'candidate_import', **data)
    dataset = result['edit_decisions']['candidate_sets'][0]
    assert dataset['coverage']['processed_seconds'] == 5
    assert dataset['coverage']['processed_ranges'] == [[2., 7.]]
    assert dataset['candidates'][0]['start_seconds'] == 2.5
    args = {'set_id': dataset['id'], 'id': dataset['candidates'][0]['id']}
    command(pid, 'candidate_review', status='accepted', context_confirmed=True, **args)
    result = command(pid, 'candidate_review', status='pending', first_word=6, last_word=8, **args)
    candidate = result['edit_decisions']['candidate_sets'][0]['candidates'][0]
    assert candidate['status'] == 'pending' and not candidate['context_confirmed']
    assert candidate['text'] == 'Eso sería un error.'
    with pytest.raises(edit.Conflict):
        edit.command(pid, {'operation': 'candidate_propose', 'revision': 0, 'set_id': dataset['id'], 'first_word': 0, 'last_word': 0, 'reason': 'stale'})


def test_existing_agent_tool_and_reframe_contract_are_shared(project, monkeypatch):
    from tools.video import studio_project_edit as tool
    from lib.studio_editor_effects import transform_filter
    pid, key, _ = project
    client = TestClient(create_app(), base_url='http://127.0.0.1')
    def request(path, data=None, **kwargs):
        response = client.get('/api/studio/editor/' + path) if data is None else client.post('/api/studio/editor/' + path, json=data)
        assert response.status_code == 200
        return response.json()
    monkeypatch.setattr(tool, 'request', request)
    result = tool.StudioProjectEdit().execute({'project_id': pid, 'action': 'command', 'command': {
        'operation': 'candidate_import', 'revision': edit.state(pid)['revision'], **payload(key)}})
    assert result.success
    dataset = edit.state(pid)['edit_decisions']['candidate_sets'][0]
    args = {'set_id': dataset['id'], 'id': dataset['candidates'][0]['id']}
    command(pid, 'candidate_review', status='accepted', context_confirmed=True, **args)
    value = command(pid, 'candidate_insert', **args)
    clip = value['edit_decisions']['cuts'][0]
    framed = command(pid, 'transform', id=clip['id'], fit='crop', zoom=1.5, focus_x=.8, focus_y=.5)
    transform = framed['edit_decisions']['cuts'][0]['transform']
    assert 'crop=1080:1920:(iw-ow)*0.8' in transform_filter(1080, 1920, transform)
    assert studio.read_json(studio.project_path(pid) / edit.ARTIFACT)['edit_decisions'] == framed['edit_decisions']
    command(pid, 'undo')
    assert 'transform' not in edit.state(pid)['edit_decisions']['cuts'][0]
    command(pid, 'redo')
    assert edit.state(pid)['edit_decisions']['cuts'][0]['transform'] == transform


def test_repeated_words_select_exact_occurrence_and_rejection_does_not_insert(project):
    pid, key, _ = project
    data = payload(key)
    data['transcript']['word_timestamps'] = [{'word': word, 'start': i, 'end': i + .5}
        for i, word in enumerate(['No', 'es', 'igual.', 'No', 'es', 'igual.'])]
    data['processed_ranges'] = [[0, 6]]
    data['proposals'] = [{'first_word': 4, 'last_word': 4, 'reason': 'Segunda aparición explícita'}]
    value = command(pid, 'candidate_import', **data)
    dataset = value['edit_decisions']['candidate_sets'][0]
    item = dataset['candidates'][0]
    assert item['word_span'] == [3, 5] and item['start_seconds'] == 3
    args = {'set_id': dataset['id'], 'id': item['id']}
    command(pid, 'candidate_review', status='rejected', **args)
    with pytest.raises(ValueError, match='Acepta'):
        command(pid, 'candidate_insert', **args)
    value = command(pid, 'candidate_propose', set_id=dataset['id'], first_word=1, last_word=1, reason='Otra propuesta reutiliza el mismo ASR')
    assert len(value['edit_decisions']['candidate_sets'][0]['candidates']) == 2
    assert len(value['edit_decisions']['candidate_sets']) == 1
    assert value['edit_decisions']['cuts'] == []


def test_zero_duration_asr_token_is_kept_without_invented_alignment(project):
    pid, key, _ = project
    data = payload(key)
    data['transcript']['word_timestamps'][1]['end'] = .5
    result = command(pid, 'candidate_import', **data)
    dataset = result['edit_decisions']['candidate_sets'][0]
    assert dataset['words'][1]['start'] == dataset['words'][1]['end'] == .5
    assert dataset['candidates'][0]['text'].startswith('No recomiendo')
