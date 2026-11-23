"""Read-only comparison of a prepared source receipt with the development branch."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
from urllib.parse import quote

REPOSITORY = 'D3ckardCain/OPENMONTAGE-IA'
BRANCH = 'feat/local-agent-research-foundation'
SHA = re.compile(r'^[0-9a-f]{40}$')
LIMIT = 1_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def remote_json(path: str) -> dict:
    request = urllib.request.Request(
        f'https://api.github.com/repos/{REPOSITORY}/{path}',
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'OPENMONTAGE-source-review/1'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=8) as response:
            raw = response.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError('Respuesta de GitHub demasiado grande')
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError('Respuesta de GitHub invalida')
        return data
    except (OSError, urllib.error.URLError, ValueError) as exc:
        raise ValueError('No se pudo consultar GitHub') from exc


def inspect(root: Path, online: bool = False) -> dict:
    if type(online) is not bool:
        raise ValueError('online debe ser booleano')
    report = {
        'repository': REPOSITORY, 'branch': BRANCH, 'status': 'origin_not_recorded',
        'recorded_revision': None, 'remote_revision': None, 'network_checked': False,
        'remote_query_attempted': False, 'installation_started': False,
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'local_files_verified': False,
        'note': 'Compara el commit del recibo de preparacion, no el contenido actual del codigo. '
                'Conserva la copia y su configuracion; no descarga, instala ni sustituye archivos.',
    }
    receipt = root / 'INSTALACION_LOCAL.json'
    try:
        if not receipt.exists():
            return report
        if receipt.is_symlink() or receipt.stat().st_size > 16_000:
            raise ValueError('Recibo invalido')
        raw = receipt.read_bytes()
        if len(raw) > 16_000:
            raise ValueError('Recibo demasiado grande')
        data = json.loads(raw.decode('utf-8-sig'))
        if not isinstance(data, dict) or data.get('repository') != REPOSITORY or data.get('branch') != BRANCH:
            raise ValueError('Origen del recibo no admitido')
        revision = data.get('revision')
        if not isinstance(revision, str) or not SHA.fullmatch(revision):
            raise ValueError('Revision invalida')
        report.update(recorded_revision=revision, status='recorded_revision_only')
    except (OSError, ValueError, UnicodeError):
        return {**report, 'status': 'receipt_unreadable'}
    if not online:
        return report
    report['remote_query_attempted'] = True
    try:
        remote = remote_json('git/ref/heads/' + quote(BRANCH, safe=''))
        obj = remote.get('object')
        latest = obj.get('sha') if isinstance(obj, dict) else None
        if not isinstance(latest, str) or not SHA.fullmatch(latest) or obj.get('type') != 'commit':
            raise ValueError('Commit remoto invalido')
        report.update(network_checked=True, remote_revision=latest)
        if latest == revision:
            return {**report, 'status': 'recorded_revision_matches_branch'}
        comparison = remote_json(f'compare/{revision}...{latest}?per_page=1')
        relation = comparison.get('status')
        states = {'ahead': 'branch_ahead_of_recorded_revision',
                  'behind': 'branch_behind_recorded_revision', 'diverged': 'branch_diverged_from_receipt'}
        if relation not in states:
            raise ValueError('Relacion entre commits no concluyente')
        return {**report, 'status': states[relation],
                'comparison_url': f'https://github.com/{REPOSITORY}/compare/{revision}...{latest}'}
    except ValueError:
        return {**report, 'status': 'remote_comparison_unavailable'}


def main() -> None:
    parser = argparse.ArgumentParser(description='Consultar el origen del estudio sin modificar archivos.')
    parser.add_argument('--online', action='store_true', help='Consultar explicitamente GitHub')
    args = parser.parse_args()
    print(json.dumps(inspect(Path(__file__).resolve().parent.parent, args.online),
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
