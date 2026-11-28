"""Metadata-bound CUDA preparation; discovery never imports Torch or weights."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from lib.hyperframes_staging import identity

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / '.runtime/qwen-tts/runtime.json'


def controlled_command(python, arguments, env, *, windows=None):
    """Avoid the Windows venv redirector child; keep its exact venv context."""
    command = [str(python), *arguments]
    environment = dict(env)
    if windows is None:
        windows = os.name == 'nt'
    if not windows:
        return command, environment
    python = Path(python).resolve()
    config = python.parent.parent / 'pyvenv.cfg'
    if not config.is_file() or config.stat().st_size > 16000:
        raise ValueError('Se requiere pyvenv.cfg local para controlar el worker Windows')
    values = dict(line.split('=', 1) for line in config.read_text(encoding='utf-8').splitlines() if '=' in line)
    home = next((v.strip() for k, v in values.items() if k.strip() == 'home'), '')
    base = Path(home) / 'python.exe'
    if not home or not base.is_absolute() or not base.is_file() or base.resolve() == python:
        raise ValueError('Python base Windows no identificado; no se inicia un lanzador sin control')
    environment['__PYVENV_LAUNCHER__'] = str(python)
    return [str(base), *arguments], environment


def binding(python):
    python = Path(python).resolve()
    metadata = sorted((python.parent.parent / 'Lib/site-packages').glob('torch-*.dist-info/METADATA'))
    if len(metadata) != 1 or metadata[0].stat().st_size > 256000:
        raise ValueError('Torch metadata ausente o ambigua en el entorno Qwen')
    return {'python': str(python), 'python_identity': identity(python),
            'torch_metadata': str(metadata[0]),
            'torch_metadata_sha256': hashlib.sha256(metadata[0].read_bytes()).hexdigest()}


def prepared(python):
    try:
        if not RECEIPT.is_file() or RECEIPT.stat().st_size > 64000:
            raise ValueError('Runtime CUDA aún no acreditado por importación aislada')
        value = json.loads(RECEIPT.read_text(encoding='utf-8'))
        if value.get('binding') != binding(python):
            raise ValueError('Cambió el runtime; renovar diagnóstico CUDA sin cargar pesos')
        if value.get('cuda_available') is not True or value.get('bfloat16_supported') is not True:
            raise ValueError('El runtime preparado no acredita CUDA/BF16')
        return {'available': True, 'torch_version': value['torch_version'],
                'device_name': value['device_name'], 'binding': value['binding']}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {'available': False, 'reason': str(exc)}


def preflight(python, folder):
    value = prepared(python)
    result = {'device': 'cuda', 'dtype': 'bfloat16', 'model_loaded': False,
              'allowed': False, 'estimate_not_peak_measurement': True, 'runtime': value}
    if not value['available']:
        result['reason'] = value['reason']
        return result
    executable = shutil.which('nvidia-smi')
    if not executable:
        result['reason'] = 'No se puede consultar VRAM libre sin cargar el modelo'
        return result
    try:
        proc = subprocess.run([executable, '--query-gpu=index,memory.free,memory.total',
                               '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5)
        if proc.returncode:
            raise ValueError('nvidia-smi no confirmó memoria disponible')
        row = next(line for line in proc.stdout.splitlines() if line.split(',')[0].strip() == '0')
        _, free, total = [int(part.strip()) for part in row.split(',')]
        required = sum((Path(folder) / name).stat().st_size for name in
                       ['model.safetensors', 'speech_tokenizer/model.safetensors']) + 1024**3
        result.update(available_bytes=free * 1024**2, total_bytes=total * 1024**2,
                      required_with_minimum_headroom_bytes=required,
                      allowed=free * 1024**2 >= required)
        if not result['allowed']:
            result['reason'] = 'VRAM libre por debajo del presupuesto; no se carga ni cambia a CPU'
    except (OSError, ValueError, StopIteration, subprocess.SubprocessError) as exc:
        result['reason'] = str(exc)
    return result
