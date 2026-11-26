"""Resolve a reviewed local HyperFrames installation. Never npm/npx/install."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from lib.media_executables import find_media, media_environment

REVIEWED_VERSION = '0.9.96'
ROOT = Path(__file__).resolve().parents[1]
REQUIRED_CHECKS = ('Node.js', 'FFmpeg', 'FFprobe', 'Chrome', 'Memory', 'Disk', 'Frames cache', 'Settings lock') + (('/dev/shm',) if sys.platform.startswith('linux') else ())
_DOCTOR = {}  # Short-lived, identity-bound explicit checks; no catalog subprocess.


def _identity(path):
    try:
        p=Path(path);s=p.stat()
        return (str(p.resolve()),s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    except (OSError,TypeError):
        return None


def remember(current, report):
    _DOCTOR.clear()
    _DOCTOR[current['identity_key']] = (time.monotonic(), report)


def resolve():
    explicit = os.environ.get('HYPERFRAMES_PACKAGE_DIR')
    roots = [Path(explicit)] if explicit else [ROOT/'node_modules/hyperframes', ROOT/'node_modules/@hyperframes/cli']
    for root in roots:
        manifest = root/'package.json'
        if not manifest.is_file():
            continue
        try:
            if manifest.stat().st_size > 100000:
                raise ValueError('Manifest superior a100KB')
            data = json.loads(manifest.read_text(encoding='utf-8'))
            if data.get('name') not in ('hyperframes', '@hyperframes/cli'):
                raise ValueError('Paquete no corresponde a HyperFrames')
            if data.get('version') != REVIEWED_VERSION:
                raise ValueError('Versión no revisada: ' + str(data.get('version')))
            entry = data.get('bin', {}).get('hyperframes')
            if not isinstance(entry, str):
                raise ValueError('Falta bin.hyperframes')
            path = (root/entry).resolve()
            path.relative_to(root.resolve())
            if not path.is_file():
                raise ValueError('CLI local incompleto: entry ausente')
            return {'version': data['version'], 'entry': str(path), 'manifest': str(manifest.resolve())}
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            return {'error': str(exc)}
    return {'error': 'CLI local ausente; preparar explícitamente hyperframes@'+REVIEWED_VERSION+' en un entorno aislado y declarar HYPERFRAMES_PACKAGE_DIR'}


def environment():
    env = media_environment()
    env.update(HYPERFRAMES_NO_TELEMETRY='1', DO_NOT_TRACK='1')
    for name in ('ffmpeg', 'ffprobe'):
        path = find_media(name)
        if path:
            env['HYPERFRAMES_'+name.upper()+'_PATH'] = path
    return env


def check():
    package = resolve()
    node = shutil.which('node')
    major = None
    if node:
        try:
            p = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=5)
            match = re.fullmatch(r'v?(\d+)\.\d+\.\d+\s*', p.stdout)
            if p.returncode == 0 and match:
                major = int(match[1])
        except (OSError, subprocess.SubprocessError):
            pass
    ffmpeg, ffprobe = find_media('ffmpeg'), find_media('ffprobe')
    browser = os.environ.get('HYPERFRAMES_BROWSER_PATH', '')
    reasons = []
    if 'error' in package:
        reasons.append(package['error'])
    if major is None or major < 22:
        reasons.append('Node.js >=22 no comprobado en PATH')
    if not ffmpeg:
        reasons.append('FFmpeg no disponible en su ruta guardada/PATH')
    if not ffprobe:
        reasons.append('FFprobe no disponible en su ruta guardada/PATH')
    if not browser or not Path(browser).is_file():
        reasons.append('Declara HYPERFRAMES_BROWSER_PATH con un navegador ya preparado; no se descarga uno')
    key=tuple(_identity(p) for p in (package.get('manifest'),package.get('entry'),node,ffmpeg,ffprobe,browser))
    cached=_DOCTOR.get(key)
    probe=cached[1] if cached and time.monotonic()-cached[0]<60 else None
    local_ready=not reasons
    if local_ready and not probe:
        reasons.append('Requisitos locales presentes; falta doctor explícito vigente (sin render validado)')
    elif local_ready and probe.get('status')!='ok':
        reasons.append(probe.get('error') or 'Doctor falló')
    return dict(runtime_available=local_ready and bool(probe) and probe['status']=='ok', installed='entry' in package,
                local_requirements_met=local_ready, render_validated=False, identity_key=key,
                diagnostic_scope='local_metadata_and_node_version_only',
                node=node, node_major=major, ffmpeg_available=bool(ffmpeg), ffprobe_available=bool(ffprobe),
                npx_available=False, npm_package='hyperframes', npm_package_version=package.get('version'),
                npm_resolve_error=package.get('error'), cli_probe_status=probe.get('status') if probe else 'not_run', cli_probe_error=probe.get('error') if probe else None,
                entry=package.get('entry'), browser_path=browser or None, reasons=reasons)


def command(args):
    current = check()
    if not current['local_requirements_met']:
        raise ValueError('; '.join(current['reasons']))
    return [current['node'], current['entry'], *args]


def parse_doctor(value):
    if not isinstance(value, dict) or not isinstance(value.get('checks'), list):
        return {'status': 'error', 'error': 'Doctor JSON sin checks reconocibles'}
    rows = value['checks']
    required = {}
    for name in REQUIRED_CHECKS:
        found = [row for row in rows if isinstance(row, dict) and row.get('name') == name]
        if len(found) != 1 or type(found[0].get('ok')) is not bool:
            return {'status': 'error', 'error': 'Check requerido ausente/ambiguo: '+name}
        required[name] = found[0]
    failed = [name for name, row in required.items() if row['ok'] is not True]
    return {'status': 'error' if failed else 'ok', 'error': 'Requisitos fallidos: '+', '.join(failed) if failed else None,
            'required': required, 'optional': [r for r in rows if isinstance(r, dict) and r.get('name') not in required],
            'render_validated': False}
