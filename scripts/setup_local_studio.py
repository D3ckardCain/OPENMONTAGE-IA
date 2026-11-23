"""Prepare an isolated Studio environment; uses only stdlib before installation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import venv


def environment_python(root: Path) -> Path:
    return root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def inspect(root: Path) -> dict:
    """Read-only report, without importing application code or probing models."""
    requirements = root / 'requirements.txt'
    report = {
        'root': str(root),
        'bootstrap_python': sys.version.split()[0],
        'supported_python': sys.version_info[:2] == (3, 11),
        'source_present': all((root / p).is_file() for p in (
            'requirements.txt', 'OPENMONTAGE_ESTUDIO.cmd', 'backlot/server.py')),
        'environment_present': environment_python(root).is_file(),
        'requirements_sha256': hashlib.sha256(requirements.read_bytes()).hexdigest()
        if requirements.is_file() else None,
    }
    state = root / '.backlot/setup/environment.json'
    report['dependency_state'] = 'not_recorded'
    try:
        if state.stat().st_size > 64_000:
            raise ValueError('Recibo demasiado grande')
        previous = json.loads(state.read_text(encoding='utf-8'))
        if not isinstance(previous, dict) or previous.get('owner') != 'openmontage-studio-setup' or previous.get('root') != str(root):
            raise ValueError('Recibo de otra copia')
        status = previous.get('status')
        if status not in {'preparing', 'installing', 'ready', 'failed'}:
            raise ValueError('Estado de recibo invalido')
        report['dependency_state'] = (
            'environment_missing' if not report['environment_present'] else
            'requirements_changed' if previous.get('requirements_sha256') != report['requirements_sha256'] else
            'ready_recorded_not_reverified' if status == 'ready' else status)
    except FileNotFoundError:
        pass
    except (OSError, ValueError, UnicodeError):
        report['dependency_state'] = 'receipt_unreadable'
    return report


def setup(root: Path, wheelhouse: Path | None = None) -> dict:
    report = inspect(root)
    if not report['source_present']:
        raise ValueError('Faltan archivos del estudio; termina primero la extraccion.')
    if not report['supported_python']:
        raise ValueError('Utiliza Python 3.11, la version validada para este instalador.')
    if wheelhouse is not None and not wheelhouse.is_dir():
        raise ValueError('No existe la carpeta de paquetes offline.')
    target = root / '.venv'
    state_dir = root / '.backlot' / 'setup'
    state_path = state_dir / 'environment.json'
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError('.venv no es una carpeta local administrable.')
    if target.exists():
        try:
            if state_path.stat().st_size > 64_000:
                raise ValueError('Recibo demasiado grande')
            previous = json.loads(state_path.read_text(encoding='utf-8'))
            if not isinstance(previous, dict):
                raise ValueError('Recibo invalido')
        except (OSError, ValueError):
            raise ValueError('Ya existe .venv sin recibo de este instalador; se conserva.') from None
        if previous.get('root') != str(root) or previous.get('owner') != 'openmontage-studio-setup':
            raise ValueError('El recibo no corresponde a esta copia; se conserva .venv.')
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = state_dir / 'installation.lock'
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError('Ya hay una instalacion activa o interrumpida. Revisa installation.lock antes de reintentar.') from None
    os.close(lock_fd)
    report.update(owner='openmontage-studio-setup', status='preparing',
                  offline=wheelhouse is not None, started_at=datetime.now(timezone.utc).isoformat())

    def save() -> None:
        temporary = state_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(state_path)

    try:
        save()
        # Never clear an existing environment or install into the caller's Python.
        venv.EnvBuilder(with_pip=True, clear=False).create(target)
        python = environment_python(root)
        cfg = target / 'pyvenv.cfg'
        if 'include-system-site-packages = false' not in cfg.read_text(encoding='utf-8').lower():
            raise ValueError('El entorno no esta aislado de paquetes del sistema.')
        clean_env = dict(os.environ)
        for key in ('PYTHONHOME', 'PYTHONPATH', 'PIP_TARGET', 'PIP_PREFIX', 'PIP_USER'):
            clean_env.pop(key, None)
        clean_env.update(PYTHONNOUSERSITE='1', PIP_CONFIG_FILE=os.devnull)
        report['status'] = 'installing'
        save()
        command = [str(python), '-I', '-m', 'pip', '--isolated', '--disable-pip-version-check',
                   'install', '--no-input']
        if wheelhouse is not None:
            command.extend(['--no-index', '--only-binary=:all:', '--find-links', str(wheelhouse)])
        else:
            command.extend(['--index-url', 'https://pypi.org/simple'])
        command.extend(['-r', str(root / 'requirements.txt')])
        subprocess.run(command, cwd=root, env=clean_env, check=True)
        subprocess.run([str(python), '-I', '-m', 'pip', '--isolated', 'check'],
                       cwd=root, env=clean_env, check=True)
        # Import only the local web server prerequisites, never the model registry.
        subprocess.run([str(python), '-I', '-c',
                        'import fastapi, uvicorn, yaml, pydantic, requests, jsonschema, dotenv'],
                       cwd=root, env=clean_env, check=True)
        report.update(status='ready', environment_present=True,
                      completed_at=datetime.now(timezone.utc).isoformat())
        save()
        return report
    except (Exception, KeyboardInterrupt) as exc:
        report.update(status='failed', error=str(exc) or type(exc).__name__)
        save()
        raise
    finally:
        lock.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description='Preparar el entorno local del estudio sin modelos ni APIs.')
    parser.add_argument('--check', action='store_true', help='Diagnostico sin modificar archivos')
    parser.add_argument('--wheelhouse', type=Path, help='Carpeta completa de wheels para instalar sin red')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        report = inspect(root) if args.check else setup(root, args.wheelhouse.resolve() if args.wheelhouse else None)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not args.check:
            print('ENTORNO PREPARADO. Abre OPENMONTAGE_ESTUDIO.cmd. No se han probado modelos.')
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f'No se pudo preparar el entorno: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
