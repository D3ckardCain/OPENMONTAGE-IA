"""No Torch import or weight read: metadata-bound preparation and GPU budget."""
import json
from types import SimpleNamespace

from lib import qwen_tts_runtime as runtime


def fixture(tmp_path, monkeypatch):
    python = tmp_path / 'env/Scripts/python.exe'
    python.parent.mkdir(parents=True)
    python.write_bytes(b'python-fixture')
    metadata = tmp_path / 'env/Lib/site-packages/torch-2.6.0+cu124.dist-info/METADATA'
    metadata.parent.mkdir(parents=True)
    metadata.write_text('Version: 2.6.0+cu124', encoding='utf-8')
    receipt = tmp_path / 'runtime.json'
    monkeypatch.setattr(runtime, 'RECEIPT', receipt)
    receipt.write_text(json.dumps(dict(binding=runtime.binding(python), cuda_available=True,
        bfloat16_supported=True, torch_version='2.6.0+cu124', device_name='fixture GPU')), encoding='utf-8')
    return python, metadata, receipt


def test_runtime_receipt_bound_to_metadata(tmp_path, monkeypatch):
    python, metadata, _ = fixture(tmp_path, monkeypatch)
    assert runtime.prepared(python)['available']
    metadata.write_text('Version: changed', encoding='utf-8')
    value = runtime.prepared(python)
    assert not value['available'] and 'runtime' in value['reason']


def test_bf16_missing_is_not_prepared(tmp_path, monkeypatch):
    python, _, receipt = fixture(tmp_path, monkeypatch)
    value = json.loads(receipt.read_text(encoding='utf-8'))
    value['bfloat16_supported'] = False
    receipt.write_text(json.dumps(value), encoding='utf-8')
    assert not runtime.prepared(python)['available']


def test_gpu_budget_only_uses_sizes_and_no_cpu_fallback(tmp_path, monkeypatch):
    python, _, _ = fixture(tmp_path, monkeypatch)
    folder = tmp_path / 'model'
    (folder / 'speech_tokenizer').mkdir(parents=True)
    (folder / 'model.safetensors').write_bytes(b'not real weights')
    (folder / 'speech_tokenizer/model.safetensors').write_bytes(b'not weights')
    monkeypatch.setattr(runtime.shutil, 'which', lambda _: 'nvidia-smi-fixture')
    monkeypatch.setattr(runtime.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='0, 2048, 8192'))
    assert runtime.preflight(python, folder)['allowed']
    monkeypatch.setattr(runtime.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='0, 512, 8192'))
    result = runtime.preflight(python, folder)
    assert not result['allowed'] and result['model_loaded'] is False and result['device'] == 'cuda'


def test_windows_worker_preserves_venv_without_redirector(tmp_path):
    python = tmp_path / 'env/Scripts/python.exe'
    python.parent.mkdir(parents=True)
    python.write_bytes(b'launcher')
    base = tmp_path / 'base/python.exe'
    base.parent.mkdir()
    base.write_bytes(b'base')
    (tmp_path / 'env/pyvenv.cfg').write_text('home = ' + str(base.parent), encoding='utf-8')
    original = {'HF_HUB_OFFLINE': '1'}
    command, env = runtime.controlled_command(python, ['-B', 'worker.py'], original, windows=True)
    assert command == [str(base), '-B', 'worker.py']
    assert env['__PYVENV_LAUNCHER__'] == str(python.resolve())
    assert original == {'HF_HUB_OFFLINE': '1'}


def test_non_windows_command_does_not_require_redirector_config(tmp_path):
    command, env = runtime.controlled_command(tmp_path / 'python', ['-B'], {'x': 'y'}, windows=False)
    assert command == [str(tmp_path / 'python'), '-B'] and env == {'x': 'y'}
