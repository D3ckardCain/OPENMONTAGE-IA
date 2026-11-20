"""Share saved reference evidence across registered language versions, not media."""
import hashlib
import json
from lib import production_studio as studio,production_agent as agent,reference_analysis


def reuse(base_id,version_ids):
    if not isinstance(version_ids,list) or not 1<=len(version_ids)<=10 or any(not isinstance(pid,str) for pid in version_ids):raise ValueError('Selecciona entre 1 y 10 versiones')
    if len(set(version_ids))!=len(version_ids):raise ValueError('No repitas versiones')
    with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
        if agent.ACTIVE or reference_analysis.ACTIVE:raise ValueError('Espera a que termine la tarea local antes de compartir el análisis')
        base=studio.project_path(base_id)
        report=reference_analysis.read(base_id)
        if report.get('status') not in ('completed','partial'):raise ValueError('El proyecto base necesita un análisis terminado o parcial')
        # Serialize a snapshot; later changes to the base report do not alter it.
        payload=json.dumps(report,ensure_ascii=False,sort_keys=True)
        if len(payload.encode())>8000000:raise ValueError('El informe supera el límite de 8 MB')
        checksum=hashlib.sha256(payload.encode()).hexdigest()
        ledger=studio.read_json(base/'language_versions.json',{'versions':{}})
        allowed={entry['project_id'] for entry in ledger['versions'].values()}
        request=studio.read_json(base/'production_request.json')
        targets=[]
        for pid in version_ids:
            if pid not in allowed:raise ValueError('Selecciona únicamente versiones registradas de este proyecto')
            path=studio.project_path(pid)
            if studio.read_json(path/'production_request.json').get('reference','')!=request.get('reference',''):raise ValueError('La referencia de la versión no coincide con la del proyecto base')
            previous=studio.read_json(path/'reference_analysis.json',{})
            if previous and previous.get('reuse',{}).get('snapshot_sha256')!=checksum:raise ValueError('La versión ya tiene otro análisis; se conservó sin sobrescribir')
            targets.append((pid,path,previous))
        results=[]
        for pid,path,previous in targets:
            if previous:results.append({'project_id':pid,'status':'existing'});continue
            snapshot={**report,'reuse':{'base_project_id':base_id,'projects_root':str(studio.PROJECTS_DIR.resolve()),
                'snapshot_sha256':checksum,'copied_at':studio.now(),'media_copied':False},
                'reuse_note':'Evidencia del proyecto base; rutas y fotogramas pertenecen al original. No supone traducción ni investigación externa.'}
            try:studio.save_json(path/'reference_analysis.json',snapshot)
            except OSError as exc:
                results.append({'project_id':pid,'status':'failed','message':str(exc)[:600]});break
            results.append({'project_id':pid,'status':'shared'})
    return {'versions':results,'generation_started':False,'media_copied':False,'network_requests_started':0}
