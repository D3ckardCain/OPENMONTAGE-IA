"""Explicit, read-only SHA-256 verification of a project's saved final files."""
import hashlib
import re
from pathlib import Path

from lib import production_studio as studio
from lib.editorial_freshness import current,delivery_current,selection_index
from lib.storage_layout import read_config


def _checked_path(raw,base):
    if not isinstance(raw,str) or not raw:return None
    candidate=Path(raw)
    if not candidate.is_absolute():candidate=base/candidate
    if candidate.is_symlink():return None
    try:
        candidate.resolve().relative_to(base.resolve())
    except (OSError,ValueError):return None
    return candidate


def _check(path,expected):
    if path is None:return 'invalid_path'
    if not path.is_file():return 'missing'
    try:
        before=path.stat()
        sha=hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(4*1024*1024),b''):sha.update(chunk)
        after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):return 'changed_during_check'
        return 'matches' if sha.hexdigest()==expected else 'hash_mismatch'
    except OSError:return 'unreadable'


def inspect(project_id):
    project=studio.project_path(project_id)
    verification=studio.read_json(project/'render_verification.json',{})
    delivery=studio.read_json(project/'final_delivery.json',{})
    reviews=studio.read_json(project/'editorial_reviews.json',[])
    index=selection_index(project)
    verified=verification.get('outputs',[]) if isinstance(verification,dict) else []
    if not isinstance(verified,list) or len(verified)>16:raise ValueError('Se admiten hasta 16 salidas verificadas por consulta')
    receipts=delivery.get('outputs',[]) if isinstance(delivery,dict) and delivery.get('copied') is True else []
    if not isinstance(receipts,list) or len(receipts)>16:raise ValueError('Recibo final inválido o demasiado grande')
    copied={row.get('source'):row for row in receipts if isinstance(row,dict) and isinstance(row.get('source'),str)}
    verified_paths=[row.get('path') for row in verified if isinstance(row,dict) and isinstance(row.get('path'),str)]
    copied_manifest_valid=(not isinstance(delivery,dict) or delivery.get('copied') is not True or
                           (len(copied)==len(receipts)==len(verified_paths)==len(verified) and
                            set(copied)==set(verified_paths)))
    configured=read_config(studio.REPO_ROOT).get('final_outputs_dir')
    final_root=Path(configured).resolve()/project_id if configured else None
    outputs=[]
    for row in verified:
        if not isinstance(row,dict):raise ValueError('Recibo de verificación inválido')
        expected=row.get('sha256')
        if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('Falta SHA-256 válido en el recibo')
        source=_checked_path(row.get('path'),project/'renders')
        source_result=_check(source,expected)
        dest=copied.get(row.get('path'))
        final_result=None
        if isinstance(delivery,dict) and delivery.get('copied') is True:
            if not isinstance(dest,dict) or dest.get('sha256')!=expected:
                final_result='receipt_mismatch'
            else:
                final_result=_check(_checked_path(dest.get('path'),final_root),expected) if final_root else 'destination_not_configured'
        outputs.append({'source':str(source) if source else None,'source_result':source_result,
                        'final_path':dest.get('path') if isinstance(dest,dict) else None,'final_result':final_result})
    return {'project_id':project_id,'verification_current':current(verification,reviews,index),
            'final_copy_current':delivery_current(verification,delivery,reviews,index),
            'outputs':outputs,'receipt_manifest_matches':copied_manifest_valid,
            'all_files_match':bool(outputs) and copied_manifest_valid and all(
                row['source_result']=='matches' and row['final_result'] in (None,'matches') for row in outputs),
            'generation_started':False,'integrity_rechecked':True,
            'note':'SHA-256 calculado ahora en archivos locales; la calidad editorial y los derechos no se verifican.'}
