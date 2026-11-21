from copy import deepcopy

import pytest

from lib.comfy_history_report import summarize_history


def test_completed_job_reports_time_and_preserves_source():
    history = {'job': {'status': {'completed': True, 'status_str': 'success', 'messages': [
        ['execution_start', {'timestamp': 1000}],
        ['execution_success', {'timestamp': 4887860}],
    ]}, 'outputs': {'9': {'video': [{'filename': 'clip.mp4', 'subfolder': 'video'}]}}}}
    original = deepcopy(history)
    report = summarize_history(history)[0]
    assert report['status'] == 'completed'
    assert report['elapsed_seconds'] == 4886.86
    assert report['artifacts'][0]['filename'] == 'clip.mp4'
    assert report['visual_quality'] == 'not_reviewed'
    assert report['media_duration_seconds'] is None
    assert history == original


@pytest.mark.parametrize('event', ['execution_error', 'execution_interrupted'])
def test_failure_cannot_be_mistaken_for_success(event):
    report = summarize_history({'job': {'status': {'completed': True, 'status_str': 'success',
        'messages': [[event, {}]]}, 'outputs': {'1': {'images': [{'filename': 'preview.png'}]}}}})[0]
    assert report['status'] == 'failed'
    assert report['elapsed_seconds'] is None


def test_missing_history_data_is_not_inferred_as_running_or_complete():
    report = summarize_history({'job': {'outputs': {'1': {'video': [{'filename': 'clip.mp4'}]}}}})[0]
    assert report['status'] == 'unknown'
    assert report['elapsed_seconds'] is None
    assert summarize_history({}) == []


@pytest.mark.parametrize('start,end', [(2000, 1000), (None, 5000), (True, 5000), (float('nan'), 5000)])
def test_invalid_timestamps_never_produce_performance_numbers(start, end):
    report = summarize_history({'job': {'status': {'completed': True, 'status_str': 'success',
        'messages': [['execution_start', {'timestamp': start}], ['execution_success', {'timestamp': end}]]}}})[0]
    assert report['elapsed_seconds'] is None
