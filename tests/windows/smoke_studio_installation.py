"""Real isolated-environment web startup; no models or production requests."""
from pathlib import Path
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request


def main():
    root = Path(__file__).resolve().parents[2]
    python = root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    env = dict(os.environ)
    for key in ('PYTHONHOME', 'PYTHONPATH'):
        env.pop(key, None)
    env['PYTHONNOUSERSITE'] = '1'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with tempfile.TemporaryFile(mode='w+b') as log:
        process = subprocess.Popen([str(python), '-m', 'backlot', 'serve', '--port', str(port)],
                                   cwd=root, env=env, stdout=log, stderr=log,
                                   stdin=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    raise RuntimeError('El servidor termino antes de estar disponible')
                try:
                    with opener.open(f'http://127.0.0.1:{port}/api/health', timeout=1) as response:
                        health = json.load(response)
                    if health.get('app') != 'backlot' or health.get('ok') is not True:
                        raise RuntimeError('Respuesta inesperada de salud')
                    break
                except (urllib.error.URLError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError('El servidor no estuvo disponible en 30 segundos') from None
                    time.sleep(0.2)
            with opener.open(f'http://127.0.0.1:{port}/studio', timeout=5) as response:
                html = response.read(500_001).decode('utf-8')
                assert response.status == 200 and '/ui/studio.js' in html
            with opener.open(f'http://127.0.0.1:{port}/ui/studio.js', timeout=5) as response:
                assert response.status == 200 and len(response.read(500_001)) > 100
            with opener.open(f'http://127.0.0.1:{port}/api/studio/bootstrap', timeout=5) as response:
                bootstrap = json.load(response)
                assert isinstance(bootstrap['settings'], dict)
                assert isinstance(bootstrap['projects'], list)
            print('PASS: isolated Python server, loopback health, Studio HTML, JavaScript and bootstrap.')
        except Exception:
            log.seek(0)
            print(log.read(16_000).decode('utf-8', errors='replace'))
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == '__main__':
    main()
