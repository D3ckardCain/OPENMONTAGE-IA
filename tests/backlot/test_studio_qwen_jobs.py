"""Synthetic offline request/receipt tests, not Qwen synthesis evidence."""
import json
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
import wave

import pytest

from lib import production_studio as studio, studio_editor as editor, model_adapters
from lib import studio_qwen_jobs as jobs


def wav(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
        stream.writeframes(b'\x88\x13\x78\xec' * 1200)


@pytest.fixture
def context(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path / 'projects')
    monkeypatch.setattr(studio, 'CONFIG_DIR', tmp_path / 'config')
    monkeypatch.setattr(jobs, 'ACTIVE', {})
    monkeypatch.setattr(editor, 'EXPORTING', set())
    monkeypatch.setattr(model_adapters, 'diagnostics', lambda *a, **k: {'ready': True, 'problems': []})
    monkeypatch.setattr(jobs, '_fingerprint', lambda inputs, info: (editor.edit_digest(inputs), {'execution': 'synthetic_fixture'}))
    value = editor.create('Synthetic Qwen request fixture')
    pid = value['project_id']
    calls = []

    def provider(inputs, work, control):
        calls.append(inputs)
        wav(work / 'voice.wav')
        return SimpleNamespace(success=True, error=None, data={'synthetic_fixture': True})

    monkeypatch.setattr(jobs, 'run_native', provider)
    yield pid, calls
    for control in list(jobs.ACTIVE.values()):
        control.event.set()
    deadline = time.monotonic() + 4
    while jobs.ACTIVE and time.monotonic() < deadline:
        time.sleep(.01)
    assert not jobs.ACTIVE


def payload(key='a' * 32, **extra):
    return {'request_id': key, 'revision': 0, 'profile': 'voice-design', 'language': 'Spanish',
            'text': 'Texto sintético, no voz real en esta prueba', 'instruction': 'Dicción clara',
            'device': 'cuda', 'max_new_tokens': 64, 'seed': 42, **extra}


def finished(pid, key):
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        value = jobs.status(pid, key)
        if value['state'] not in ('running', 'cancelling'):
            return value
        time.sleep(.01)
    pytest.fail('Synthetic worker did not finish within its bounded fixture')


def test_completed_request_reuses_receipt_without_provider_or_edl_mutation(context):
    pid, calls = context
    before = (studio.project_path(pid) / editor.ARTIFACT).read_bytes()
    started = jobs.start(pid, payload())
    assert started['state'] == 'running'
    result = finished(pid, 'a' * 32)
    assert result['state'] == 'completed'
    assert result['result']['listening_verified'] is False
    assert jobs.start(pid, payload())['reused_request']
    assert len(calls) == 1 and not editor.EXPORTING
    assert (studio.project_path(pid) / editor.ARTIFACT).read_bytes() == before
    assert jobs.requests(pid)['rows'][0]['request_id'] == 'a' * 32
    with pytest.raises(editor.Conflict):
        jobs.start(pid, payload(text='Different input'))


@pytest.mark.parametrize('change', ['wave', 'receipt'])
def test_altered_completed_output_is_not_reused_as_success(context, change):
    pid, calls = context
    jobs.start(pid, payload())
    result = finished(pid, 'a' * 32)
    output = studio.project_path(pid) / result['result']['relative_path']
    target = output if change == 'wave' else Path(str(output) + '.json')
    target.write_bytes(b'changed explicit fixture')
    assert jobs.status(pid, 'a' * 32)['state'] == 'invalid'
    assert jobs.start(pid, payload())['state'] == 'invalid'
    assert len(calls) == 1


def test_missing_runtime_never_creates_worker_claim_or_work(context, monkeypatch):
    pid, calls = context
    monkeypatch.setattr(model_adapters, 'diagnostics', lambda *a, **k: {'ready': False, 'problems': ['CUDA fixture unavailable']})
    with pytest.raises(ValueError, match='CUDA fixture unavailable'):
        jobs.start(pid, payload())
    assert not calls and not jobs.ACTIVE and not editor.EXPORTING
    assert not (studio.project_path(pid) / 'artifacts/qwen_previews/active.claim').exists()


def test_base_reference_requires_authorization_and_same_id_does_not_repeat(context):
    pid, calls = context
    root = studio.project_path(pid)
    reference = root / 'assets/reference.wav'
    wav(reference)
    value = editor.state(pid)
    value['edit_decisions']['sources']['reference'] = {'path': 'assets/reference.wav', 'kind': 'audio',
        'duration': .1, 'sha256': editor.digest(reference), **editor.identity(reference)}
    studio.save_json(root / editor.ARTIFACT, value)
    data = payload(profile='qwen-tts-17b-base', reference_source_id='reference', reference_text='Explicit synthetic reference', reference_authorized=False)
    with pytest.raises(ValueError, match='autorización'):
        jobs.start(pid, data)
    data['reference_authorized'] = True
    jobs.start(pid, data)
    assert finished(pid, 'a' * 32)['state'] == 'completed'
    assert jobs.start(pid, data)['reused_request']
    assert len(calls) == 1


def test_cancel_owned_real_child_does_not_claim_real_model_inference(context, monkeypatch):
    pid, _ = context
    from lib.studio_render_process import execute

    def waiting(inputs, work, control):
        execute([sys.executable, '-c', 'import time;time.sleep(10)'], work, control, timeout=15,
                env={**os.environ, 'OPENMONTAGE_QA_CONTROL': 'synthetic'})
        raise AssertionError('Fixture must be cancelled')

    monkeypatch.setattr(jobs, 'run_native', waiting)
    jobs.start(pid, payload())
    control = jobs.ACTIVE[(pid, 'a' * 32)]
    deadline = time.monotonic() + 3
    while control.process is None and time.monotonic() < deadline:
        time.sleep(.01)
    assert control.process is not None
    from lib.production_queue import inspect
    assert inspect()['local_task_active']
    with pytest.raises(editor.Conflict):
        editor.command(pid, {'operation': 'save', 'revision': 0})
    with pytest.raises(editor.Conflict):
        jobs.start(pid, payload(key='b' * 32))
    assert jobs.cancel(pid, 'a' * 32)['state'] == 'cancelling'
    value = finished(pid, 'a' * 32)
    assert value['state'] == 'cancelled' and value['worker_exited']
    assert value['termination_requested'] and not value['inference_stop_confirmed']
    assert value['cancel_origin'] == 'user' and 'result' not in value
    assert control.process.poll() is not None and not editor.EXPORTING


def test_interrupted_receipt_is_not_automatically_relaunched(context):
    pid, calls = context
    project, path, claim = jobs._paths(pid, 'a' * 32)
    studio.save_json(path, {'project_id': pid, 'request_id': 'a' * 32, 'state': 'running',
                           'inputs': {}, 'relative_work': 'assets/audio/qwen/' + 'a' * 32})
    assert jobs.status(pid, 'a' * 32)['state'] == 'interrupted'
    assert not calls


def test_worker_failure_preserves_request_and_releases_project(context, monkeypatch):
    pid, _ = context
    monkeypatch.setattr(jobs, 'run_native', lambda *a: SimpleNamespace(success=False, error='Explicit worker failure', data={}))
    jobs.start(pid, payload())
    value = finished(pid, 'a' * 32)
    assert value['state'] == 'failed' and value['error'] == 'Explicit worker failure'
    assert not jobs.ACTIVE and not editor.EXPORTING


def test_preview_parameters_are_bounded_without_launching_worker(context):
    pid, calls = context
    for extra in [{'text': 'x' * 301}, {'max_new_tokens': True}, {'seed': -1}, {'device': 'auto'}]:
        with pytest.raises(ValueError):
            jobs.start(pid, payload(**extra))
    assert not calls and not jobs.ACTIVE
