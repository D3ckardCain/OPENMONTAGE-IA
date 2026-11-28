"""Shared agent contract and native controlled-worker wiring, no model inference."""
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('action,suffix,body', [
    ('qwen_start', '/agent-qwen/preview', {'request_id': 'a' * 32, 'revision': 0}),
    ('qwen_status', '/qwen/requests/' + 'a' * 32, None),
    ('qwen_cancel', '/agent-qwen/requests/' + 'a' * 32 + '/cancel', {}),
])
def test_agent_routes_to_single_studio_owner(monkeypatch, action, suffix, body):
    from tools.video import studio_project_edit as module
    calls = []
    def request(path, data=None):
        calls.append((path, data))
        return {'state': 'synthetic_transport_fixture'}
    monkeypatch.setattr(module, 'request', request)
    result = module.StudioProjectEdit().execute({'project_id': 'qa', 'action': action,
        'request_id': 'a' * 32, 'qwen': {'request_id': 'a' * 32, 'revision': 0}})
    assert result.success and calls == [('qa' + suffix, body)]


def test_native_qwen_uses_owned_control_and_offline_env(tmp_path, monkeypatch):
    from lib import model_adapters as adapters, studio_render_process as process, qwen_tts_runtime as runtime
    from lib import qwen_tts_local, production_studio as studio
    from tools.models.local_adapters import model_voice_design
    monkeypatch.setattr(adapters, 'diagnostics', lambda *a, **k: dict(ready=True, backend='native',
        model_dir=str(tmp_path), python_executable='fixture-python', device='cuda'))
    monkeypatch.setattr(adapters, 'configuration', lambda _: {})
    monkeypatch.setattr(qwen_tts_local, 'resources', lambda *a: {'resources_verified': True})
    monkeypatch.setattr(studio, 'settings', lambda: {})
    seen = []
    def command(python, args, env):
        assert python == 'fixture-python' and args[0] == '-B'
        assert env['HF_HUB_OFFLINE'] == '1'
        seen.append('prepared')
        return ['owned-base', *args], {**env, '__PYVENV_LAUNCHER__': python}
    monkeypatch.setattr(runtime, 'controlled_command', command)
    control = process.Control('fixture')
    def execute(command, work, owned, **kwargs):
        assert owned is control and command[0] == 'owned-base'
        assert kwargs['env']['__PYVENV_LAUNCHER__'] == 'fixture-python'
        request = studio.read_json(command[-2])
        assert Path(request['progress_path']).parent == work
        output = work / 'voice.wav'
        output.write_bytes(b'synthetic-output-contract-fixture')
        studio.save_json(command[-1], {'success': True, 'outputs': [str(output)]})
        seen.append('executed')
        return SimpleNamespace(returncode=0, stderr=b'')
    monkeypatch.setattr(process, 'execute', execute)
    result = model_voice_design().execute({'output_dir': str(tmp_path / 'out'), 'text': 'fixture',
        'language': 'Spanish', 'instruction': 'fixture', 'device': 'cuda'}, control=control)
    assert result.success, result.error
    assert seen == ['prepared', 'executed']
