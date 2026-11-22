"""Read saved delivery receipts without scanning resource disks or hashing video."""
from pathlib import Path
from lib import production_studio as studio


def catalog(limit=500):
    rows=[];errors=[];scanned=0;truncated=False
    for marker in sorted(studio.PROJECTS_DIR.glob('*/production_request.json')):
        if scanned>=limit:truncated=True;break
        scanned+=1
        try:
            if marker.is_symlink() or marker.parent.is_symlink():continue
            project=studio.project_path(marker.parent.name)
            request=studio.read_json(marker)
            receipt=studio.read_json(project/'final_delivery.json',{})
            verification=studio.read_json(project/'render_verification.json',{})
            if not receipt and not verification:continue
            outputs=[]
            for record in receipt.get('outputs',[]) if receipt.get('copied') else verification.get('outputs',[]):
                path=Path(record['path'])
                if not path.is_absolute():path=project/path
                available=path.is_file() and not path.is_symlink()
                outputs.append({'path':str(path),'available':available,'bytes':record.get('bytes'),
                    'sha256_saved':record.get('sha256'),'integrity_rechecked':False})
            rows.append({'project_id':project.name,'title':request.get('title',project.name),
                'delivery_mode':receipt.get('mode','project_renders'),'copied':receipt.get('copied',False),
                'delivered_at':receipt.get('delivered_at'),'verification_status':verification.get('status','unknown'),
                'football_selection':verification.get('football_selection') if verification.get('status')=='passed' else None,
                'outputs':outputs,'studio_url':'/studio?project='+project.name})
        except (OSError,ValueError,KeyError,TypeError) as exc:
            errors.append({'project_id':marker.parent.name,'message':str(exc)[:600]})
    return {'projects':rows,'errors':errors,'scanned':scanned,'truncated':truncated,
        'projects_root':str(studio.PROJECTS_DIR),'root_available':studio.PROJECTS_DIR.is_dir(),'generation_started':False,
        'note':'Recibos guardados del disco de proyectos activo. Disponibilidad actual sin volver a verificar integridad o calidad; no recorre los discos de modelos.'}
