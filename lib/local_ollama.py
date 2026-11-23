"""Start an explicitly prepared Ollama service on loopback, without inference."""
import json
import os
from pathlib import Path
import subprocess
import time
from lib.production_studio import local_request
import uuid


def version(port=11434):
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('OLLAMA_PORT_INVALID: puerto local inválido')
    result = local_request('http://127.0.0.1:' + str(port), '/api/version', timeout=2)
    if not isinstance(result, dict) or not isinstance(result.get('version'), str):
        raise ValueError('OLLAMA_RESPONSE_INVALID: falta versión local')
    return result['version']


def start(executable, models_dir, log_dir, port=11434):
    executable, models_dir, log_dir = map(Path, (executable, models_dir, log_dir))
    if not executable.is_absolute() or executable.name.casefold() not in ('ollama.exe', 'ollama') or not executable.is_file():
        raise ValueError('OLLAMA_EXECUTABLE_INVALID: indica el ejecutable preparado')
    if not models_dir.is_absolute() or not log_dir.is_absolute():
        raise ValueError('OLLAMA_PATH_INVALID: indica carpetas absolutas')
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('OLLAMA_PORT_INVALID: puerto local inválido')
    try:
        running = version(port)
    except (OSError, ValueError):
        running = None
    if running:
        # Never replace an existing service or infer its settings from a successful ping.
        return {'started': False, 'already_running': True, 'version': running,
                'cloud_disabled_verified': False, 'inference_performed': False}
    env = dict(os.environ, OLLAMA_HOST='127.0.0.1:' + str(port), OLLAMA_MODELS=str(models_dir),
               OLLAMA_NO_CLOUD='1', OLLAMA_NUM_PARALLEL='1', OLLAMA_MAX_LOADED_MODELS='1',
               OLLAMA_CONTEXT_LENGTH='4096')
    models_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / ('ollama-' + uuid.uuid4().hex + '.log')
    with log_path.open('xb') as log:
        process = subprocess.Popen([str(executable), 'serve'], env=env, cwd=str(executable.parent),
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), shell=False)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ValueError('OLLAMA_START_FAILED: revisa ' + str(log_path))
        try:
            running = version(port)
            log_text = log_path.read_text(encoding='utf-8', errors='replace')
            verified = 'Ollama cloud disabled: true' in log_text
            return {'started': True, 'already_running': False, 'pid': process.pid,
                    'version': running, 'log_path': str(log_path), 'models_dir': str(models_dir),
                    'cloud_disabled_requested': True, 'cloud_disabled_verified': verified,
                    'host': env['OLLAMA_HOST'], 'inference_performed': False}
        except OSError:
            time.sleep(0.25)
    raise ValueError('OLLAMA_START_TIMEOUT: revisa ' + str(log_path))
