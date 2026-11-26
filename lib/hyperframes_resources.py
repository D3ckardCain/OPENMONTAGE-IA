"""Reviewed local GSAP resource; no download, CDN fallback or model calls."""
import hashlib
import json
from pathlib import Path

GSAP_VERSION = '3.14.2'
GSAP_SHA256 = 'c174bfce53a729418d57a8ad8625e7247c793a22fef8e2851e3cfa3de9cd8280'


def inspect_gsap(package_dir):
    root = Path(package_dir).resolve()
    manifest = root / 'package.json'
    source = root / 'dist/gsap.min.js'
    if not manifest.is_file() or manifest.stat().st_size > 100000:
        raise ValueError('Local GSAP manifest missing or exceeds100KB; no CDN fallback')
    metadata = json.loads(manifest.read_text(encoding='utf-8'))
    if metadata.get('name') != 'gsap' or metadata.get('version') != GSAP_VERSION:
        raise ValueError('Local GSAP must be the reviewed3.14.2 package')
    if not source.is_file() or not 0 < source.stat().st_size <= 2000000:
        raise ValueError('Local GSAP script missing or exceeds2MB; no CDN fallback')
    source.resolve().relative_to(root)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != GSAP_SHA256:
        raise ValueError('Local GSAP SHA256 differs from reviewed resource; preserved')
    if not metadata.get('license'):
        raise ValueError('Local GSAP license metadata missing')
    return source, manifest, {'version': GSAP_VERSION, 'sha256': digest,
                              'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
                              'license': metadata['license'], 'mode': 'local_verified'}


def stage_gsap(inspected, workspace):
    from lib.hyperframes_staging import stage
    source, manifest, receipt = inspected
    js = stage(source, workspace)
    attribution = stage(manifest, workspace)
    if (hashlib.sha256(js.read_bytes()).hexdigest() != receipt['sha256'] or
            hashlib.sha256(attribution.read_bytes()).hexdigest() != receipt['manifest_sha256']):
        raise ValueError('Local GSAP changed during staging; do not render this workspace')
    receipt = dict(receipt, src=js.relative_to(workspace.resolve()).as_posix(),
                   attribution=attribution.relative_to(workspace.resolve()).as_posix())
    (workspace / '.openmontage-gsap.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt
