"""Local source identity, without git, models, settings or subprocesses."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path

from lib.studio_timeline_ops import CAPABILITIES

ROOT = Path(__file__).resolve().parents[1]
API_PROTOCOL = 1


def fingerprint(root: Path, ui: bool = False) -> dict:
    """Bounded code reads; unreadable inputs never become a matching build."""
    patterns = ('backlot/ui/*.js', 'backlot/ui/*.css', 'backlot/ui/studio.html') if ui else (
        'backlot/*.py', 'lib/studio*.py', 'lib/production_studio.py',
    )
    digest = hashlib.sha256()
    try:
        paths = sorted({p for pattern in patterns for p in root.glob(pattern)})
        if not paths:
            return {'status': 'unavailable', 'reason': 'source_missing'}
        for path in paths:
            with path.open('rb') as stream:
                content = stream.read(2_000_001)
            if len(content) > 2_000_000:
                return {'status': 'unavailable', 'reason': 'source_too_large'}
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b'\0' + hashlib.sha256(content).digest())
    except OSError:
        return {'status': 'unavailable', 'reason': 'source_unreadable'}
    return {'status': 'available', 'sha256': digest.hexdigest(), 'files': len(paths)}


# Import-time source snapshot, never fresh disk bytes labelled as loaded code.
# ZIP workspaces have no trustworthy Git revision: report content identity.
RESIDENT = fingerprint(ROOT)
STARTED = datetime.now(timezone.utc).isoformat()
EDITOR_CAPABILITIES = {
    'version': '3.0', 'commands': tuple(CAPABILITIES),
    'render_cancel': True, 'shared_revision': True,
}


def capabilities() -> dict:
    return {**EDITOR_CAPABILITIES, 'commands': list(EDITOR_CAPABILITIES['commands']),
            'api_protocol': API_PROTOCOL, 'backend_build': RESIDENT.get('sha256')}


def identity() -> dict:
    current = fingerprint(ROOT)
    comparable = RESIDENT['status'] == current['status'] == 'available'
    return {
        'schema_version': 1, 'api_protocol': API_PROTOCOL,
        'revision_kind': 'source_sha256_at_import',
        'resident': dict(RESIDENT), 'disk': current, 'ui': fingerprint(ROOT, ui=True),
        'restart_required': RESIDENT['sha256'] != current['sha256'] if comparable else None,
        'pid': os.getpid(), 'loaded_at_utc': STARTED, 'editor': capabilities(),
    }
