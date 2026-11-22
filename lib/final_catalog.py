"""Read saved delivery receipts without scanning resource disks or hashing video."""
from pathlib import Path
from lib import production_studio as studio
from lib.editorial_freshness import current as verification_current,delivery_current,selection_index
from lib.storage_layout import read_config


def _available_path(raw, base, relative_base):
    if not isinstance(raw,str) or not raw or base is None:return None
    path=Path(raw)
    if not path.is_absolute():path=relative_base/path
    if path.is_symlink():return None
    try:path.resolve().relative_to(base.resolve())
    except (OSError,ValueError):return None
    return path


def catalog(limit=500):
    rows=[];errors=[];scanned=0;truncated=False
    configured=read_config(studio.REPO_ROOT).get('final_outputs_dir')
    for marker in sorted(studio.PROJECTS_DIR.glob('*/production_request.json')):
        if scanned>=limit:truncated=True;break
        scanned+=1
        try:
            if marker.is_symlink() or marker.parent.is_symlink():continue
            project=studio.project_path(marker.parent.name)
            request=studio.read_json(marker)
            receipt=studio.read_json(project/'final_delivery.json',{})
            verification=studio.read_json(project/'render_verification.json',{})
            reviews=studio.read_json(project/'editorial_reviews.json',[])
            selection=selection_index(project)
            current=verification_current(verification,reviews,selection)
            if not receipt and not verification:continue
            outputs=[]
            copied=receipt.get('copied') is True
            base=(Path(configured)/project.name if configured else None) if copied else project/'renders'
            for record in receipt.get('outputs',[]) if copied else verification.get('outputs',[]):
                raw=record['path']
                path=_available_path(raw,base,base if copied else project)
                available=path.is_file() if path else False
                outputs.append({'path':str(path) if path else str(raw),'available':available,'bytes':record.get('bytes'),
                    'sha256_saved':record.get('sha256'),'integrity_rechecked':False})
            rows.append({'project_id':project.name,'title':request.get('title',project.name),
                'delivery_mode':receipt.get('mode','project_renders'),'copied':receipt.get('copied',False),
                'delivered_at':receipt.get('delivered_at'),'verification_status':verification.get('status','unknown'),
                'verification_current':current,'final_copy_current':delivery_current(verification,receipt,reviews,selection),
                'football_selection':verification.get('football_selection') if verification.get('status')=='passed' else None,
                'outputs':outputs,'studio_url':'/studio?project='+project.name})
        except (OSError,ValueError,KeyError,TypeError) as exc:
            errors.append({'project_id':marker.parent.name,'message':str(exc)[:600]})
    return {'projects':rows,'errors':errors,'scanned':scanned,'truncated':truncated,
        'projects_root':str(studio.PROJECTS_DIR),'root_available':studio.PROJECTS_DIR.is_dir(),'generation_started':False,
        'note':'Recibos guardados del disco de proyectos activo. Disponibilidad actual sin volver a verificar integridad o calidad; no recorre los discos de modelos.'}
