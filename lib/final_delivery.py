"""Copy verified renders to the configured final-output disk, preserving originals."""
import hashlib
import shutil
import uuid
import re
from pathlib import Path
from lib import production_studio as studio
from lib.storage_layout import read_config


def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def deliver(project_id,outputs):
    project=studio.project_path(project_id)
    configured=read_config(studio.REPO_ROOT).get('final_outputs_dir')
    if not configured:return {'mode':'project_renders','copied':False,'outputs':outputs}
    root=Path(configured)
    if not root.is_dir():raise ValueError('El disco de videos finales no está conectado. Se conservó la copia de trabajo.')
    root=root.resolve();folder=root/project_id
    if folder.is_symlink():raise ValueError('El destino final del proyecto no puede ser un enlace simbólico')
    checked=[]
    for item in outputs:
        verified=item.get('verified_sha256')
        if not isinstance(verified,str) or not re.fullmatch('[0-9a-f]{64}',verified):
            raise ValueError('Falta el SHA-256 de la verificación técnica; no se entregó')
        source=Path(item['path'])
        if not source.is_absolute():source=project/source
        source=source.resolve();source.relative_to((project/'renders').resolve())
        if not source.is_file() or not source.stat().st_size:raise ValueError('Falta el render verificado')
        checksum=digest(source)
        if verified!=checksum:raise ValueError('El render cambió después de su verificación; no se entregó')
        checked.append((source,checksum))
    folder.mkdir(exist_ok=True)
    records=[]
    for source,checksum in checked:
        if digest(source)!=checksum:raise ValueError('El render cambió antes de copiar; no se entregó')
        dest=folder/(source.stem+'-'+checksum[:12]+source.suffix)
        if dest.is_symlink():raise ValueError('El archivo final no puede ser un enlace simbólico')
        if dest.exists():
            if digest(dest)!=checksum:raise ValueError('Hay un archivo distinto en el destino; no se sobrescribió')
        else:
            if shutil.disk_usage(root).free<source.stat().st_size:raise ValueError('No hay espacio suficiente en el disco de finales')
            temp=folder/('.delivery-'+uuid.uuid4().hex+'.tmp')
            try:
                shutil.copyfile(source,temp)
                if digest(temp)!=checksum:raise ValueError('La copia final no superó la comprobación de integridad')
                temp.replace(dest)
            finally:temp.unlink(missing_ok=True)
        records.append({'source':str(source),'path':str(dest),'sha256':checksum,'bytes':dest.stat().st_size})
    report={'mode':'dedicated_final_directory','copied':True,'outputs':records,'delivered_at':studio.now()}
    studio.save_json(project/'final_delivery.json',report)
    return report


def retry_verified_delivery(project_id):
    """Recover disk delivery from saved evidence, without rerendering/inference."""
    from lib.checkpoint import get_completed_stages
    from lib.pipeline_loader import load_pipeline_readonly
    project=studio.project_path(project_id)
    request=studio.read_json(project/'production_request.json')
    manifest=load_pipeline_readonly(request['pipeline'])
    required={stage['name'] for stage in manifest['stages'] if stage['name']!='publish'}
    complete=set(get_completed_stages(studio.PROJECTS_DIR,project_id,request['pipeline']))
    if not required<=complete:raise ValueError('Quedan etapas de producción sin completar')
    if not read_config(studio.REPO_ROOT).get('final_outputs_dir'):raise ValueError('Configura el destino de videos finales antes de reintentar la entrega')
    evidence=studio.read_json(project/'render_verification.json',{})
    if evidence.get('status')!='passed':raise ValueError('Falta una verificación técnica aprobada')
    from lib.editorial_freshness import current as verification_current,selection_index
    if not verification_current(evidence,studio.read_json(project/'editorial_reviews.json',[]),selection_index(project)):
        raise ValueError('La verificación no corresponde a la revisión o selección deportiva actual; verifica el render actualizado')
    receipts={}
    for record in evidence.get('outputs',[]):
        path=Path(record['path']).resolve();path.relative_to((project/'renders').resolve())
        checksum=record.get('sha256')
        if not record.get('full_decode_passed') or not isinstance(checksum,str) or not re.fullmatch('[0-9a-f]{64}',checksum):raise ValueError('Evidencia de render incompleta')
        if str(path) in receipts:raise ValueError('Evidencia repetida')
        receipts[str(path)]=checksum
    outputs=studio.read_json(project/'artifacts/render_report.json',{}).get('outputs',[])
    from lib.render_verification import declarations_digest
    if evidence.get('declared_outputs_sha256')!=declarations_digest(outputs):raise ValueError('El informe de render cambió desde la verificación; verifica la exportación de nuevo')
    current=[];paths=[]
    for item in outputs:
        path=Path(item['path'])
        if not path.is_absolute():path=project/path
        path=path.resolve();path.relative_to((project/'renders').resolve());paths.append(str(path))
        current.append({**item,'path':str(path),'verified_sha256':receipts.get(str(path))})
    if not current or len(paths)!=len(set(paths)) or set(paths)!=set(receipts):raise ValueError('El informe actual no coincide con los renders verificados')
    retry_path=project/'delivery_retry.json'
    studio.save_json(retry_path,{'status':'running','started_at':studio.now(),'generation_started':False})
    try:
        result=deliver(project_id,current)
        report={'status':'completed','finished_at':studio.now(),'generation_started':False,'delivery':result}
        studio.save_json(retry_path,report)
        job=studio.read_json(project/'job.json',{})
        events=job.get('events',[]);events.append({'at':studio.now(),'kind':'delivery','message':'Entrega final recuperada sin volver a generar'})
        studio.save_json(project/'job.json',{**job,'status':'rendered','message':'Entrega final recuperada; publicación no ejecutada.',
            'updated_at':studio.now(),'events':events[-500:]})
        return report
    except Exception as exc:
        studio.save_json(retry_path,{'status':'failed','finished_at':studio.now(),'generation_started':False,'error':str(exc)[:1800]})
        raise
