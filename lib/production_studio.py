"""Production workspaces, local configuration and resource evidence.

This module persists user requests and reports dependencies. It makes no creative
choices, downloads no weights and never treats inventory metadata as inference.
"""
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import threading
import uuid
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit
import urllib.request
from lib.paths import REPO_ROOT, PROJECTS_DIR
from lib.checkpoint import init_project, get_next_stage, write_checkpoint
from lib.pipeline_loader import list_pipelines, load_pipeline_readonly

LOCK = threading.RLock()
CONFIG_DIR = REPO_ROOT / '.backlot' / 'studio'

def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_json(path, default=None):
    path = Path(path)
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.is_file() else default


def local_url(value):
    p = urlsplit(value)
    if p.scheme != 'http' or p.hostname not in ('localhost','127.0.0.1','::1') or p.username or p.password or p.query or p.fragment or p.path not in ('','/'):
        raise ValueError('El servidor debe ser HTTP local, sin credenciales ni rutas adicionales')
    _ = p.port
    return value.rstrip('/')


def settings():
    defaults = {'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188',
                'model':'','resource_roots':[],'max_turns':120,'ffmpeg_path':'','ffprobe_path':'','yt_dlp_path':'','deno_path':''}
    return {**defaults, **read_json(CONFIG_DIR/'settings.json',{})}


def configure(data):
    allowed={'ollama_url','comfyui_url','model','resource_roots','max_turns','ffmpeg_path','ffprobe_path','yt_dlp_path','deno_path'}
    if set(data)-allowed:raise ValueError('Configuración desconocida')
    value={**settings(),**data}
    for key in ('ffmpeg_path','ffprobe_path','yt_dlp_path','deno_path'):
        if not isinstance(value[key],str) or len(value[key])>4000 or (value[key] and not Path(value[key]).is_absolute()):raise ValueError('Usa ruta absoluta para '+key)
    for k in ('ollama_url','comfyui_url'):value[k]=local_url(value[k])
    if not isinstance(value['model'],str) or len(value['model'])>200:raise ValueError('Modelo inválido')
    if type(value['max_turns']) is not int or not 1<=value['max_turns']<=300:raise ValueError('Límite inválido')
    roots=value['resource_roots']
    if not isinstance(roots,list) or len(roots)>8 or any(not isinstance(p,str) or not Path(p).is_absolute() for p in roots):
        raise ValueError('Usa hasta ocho carpetas absolutas de recursos')
    with LOCK:save_json(CONFIG_DIR/'settings.json',value)
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def local_request(base, path, data=None, timeout=4):
    base=local_url(base)
    body=None if data is None else json.dumps(data).encode()
    request=urllib.request.Request(base+path,data=body,headers={'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=timeout) as response:
        raw=response.read(16_000_001)
        if len(raw)>16_000_000:raise ValueError('Respuesta local demasiado grande')
        return json.loads(raw)


def runtime_status():
    cfg=settings();result={'settings':cfg,'models':[],'ollama_ready':False,'comfyui_ready':False,
                           'ffmpeg_ready':bool(Path(cfg['ffmpeg_path']).is_file()) if cfg['ffmpeg_path'] else bool(shutil.which('ffmpeg')),'problems':[]}
    try:
        reply=local_request(cfg['ollama_url'],'/api/tags')
        result['models']=[m['name'] for m in reply.get('models',[]) if isinstance(m.get('name'),str)]
        result['ollama_ready']=cfg['model'] in result['models']
        if not result['ollama_ready']:result['problems'].append('Selecciona un modelo instalado en Ollama. Los pesos descargados no se registran automáticamente.')
    except Exception:result['problems'].append('Ollama no responde. Inicia el servidor local; no se usa un proveedor de pago como alternativa.')
    try:
        stats=local_request(cfg['comfyui_url'],'/system_stats')
        result['comfyui_ready']=isinstance(stats.get('system'),dict)
        result['devices']=[{'name':x.get('name'),'vram_total':x.get('vram_total')} for x in stats.get('devices',[])]
    except Exception:result['problems'].append('ComfyUI no responde. Los proyectos de generación necesitan un runtime y workflows compatibles.')
    if not result['ffmpeg_ready']:result['problems'].append('Falta FFmpeg para montaje y exportación.')
    result['resource_roots']=[{'path':p,'accessible':Path(p).is_dir()} for p in cfg['resource_roots']]
    result['inference_verified']=False
    return result


def pipelines():
    result=[]
    for name in list_pipelines():
        if name=='framework-smoke':continue
        m=load_pipeline_readonly(name)
        result.append({'name':name,'description':m.get('description',''),'stability':m.get('stability'),
                       'stages':[s['name'] for s in m['stages']]})
    return result


def project_path(project_id):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,99}',project_id):raise ValueError('Proyecto inválido')
    p=(PROJECTS_DIR/project_id).resolve()
    p.relative_to(PROJECTS_DIR.resolve())
    if not (p/'production_request.json').is_file():raise FileNotFoundError('Proyecto de producción no encontrado')
    return p


def create_production(data):
    from lib.paths import PROJECTS_DIR as startup_projects
    if PROJECTS_DIR == startup_projects and PROJECTS_DIR != REPO_ROOT/'projects' and not PROJECTS_DIR.is_dir():
        raise ValueError('El disco o carpeta de proyectos no está disponible. Conéctalo antes de crear una producción; no se guardará en otro disco.')
    allowed={'title','brief','pipeline','language','reference','automatic','research_idea','performance_import_id'}
    if set(data)-allowed:raise ValueError('Campos desconocidos')
    for name in ('title','brief','pipeline','language'):
        if not isinstance(data.get(name),str) or not data[name].strip():raise ValueError('Completa título, solicitud, pipeline e idioma')
    if len(data['title'])>150 or len(data['brief'])>12000 or len(str(data.get('reference','')))>2000:raise ValueError('Solicitud demasiado larga')
    if type(data.get('automatic',False)) is not bool:raise ValueError('Política automática inválida')
    if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*',data['language']):raise ValueError('Idioma inválido')
    if not isinstance(data.get('reference',''),str):raise ValueError('Referencia inválida')
    linked_idea=None;dossier=None;idea_sha256=None;observations=None;observations_sha256=None
    performance=None
    if data.get('performance_import_id') is not None:
        from lib.channel_performance import read as read_performance
        performance=read_performance(data['performance_import_id'])
    if data.get('research_idea') is not None:
        from lib.channel_ideas import read_draft
        from lib.channel_dossiers import read as read_dossier, _digest
        ref=data['research_idea']
        if not isinstance(ref,dict) or set(ref)!={'channel_id','snapshot_id','idea_id'}:
            raise ValueError('Vínculo de investigación inválido')
        linked_idea=read_draft(ref['channel_id'],ref['idea_id'])
        dossier=read_dossier(ref['channel_id'],ref['snapshot_id'])
        if linked_idea['snapshot_id']!=dossier['id'] or linked_idea['snapshot_sha256']!=dossier['report_sha256']:
            raise ValueError('La propuesta no corresponde al expediente')
        if data.get('reference') not in [item['url'] for item in linked_idea['references']]:
            raise ValueError('La referencia elegida no está en la propuesta')
        idea_sha256=_digest(linked_idea)
        from lib.video_observations import read as read_observations
        selected={item['id'] for item in linked_idea['references']}
        observations=[row for row in read_observations() if row.get('video_id') in selected]
        observations_sha256=_digest(observations)
    if data['pipeline']=='framework-smoke':raise ValueError('Pipeline reservado para pruebas')
    manifest=load_pipeline_readonly(data['pipeline'])
    pid='video-'+uuid.uuid4().hex[:12]
    with LOCK:
        p=init_project(pid,title=data['title'],pipeline_type=data['pipeline'],pipeline_dir=PROJECTS_DIR)
        save_json(p/'production_request.json',{**data,'performance_import_sha256':performance['sha256'] if performance else None,'research_idea_sha256':idea_sha256,
            'research_observations_sha256':observations_sha256,'project_id':pid,'created_at':now(),'budget_usd':0,'publish_authorized':False})
        if linked_idea is not None:
            save_json(p/'artifacts/channel_idea_source.json',linked_idea)
            save_json(p/'artifacts/channel_research_snapshot.json',dossier)
            save_json(p/'artifacts/video_observations_snapshot.json',observations)
        if performance is not None:
            save_json(p/'artifacts/channel_performance_snapshot.json',performance)
        decision={'version':'1.0','project_id':pid,'decisions':[{'decision_id':'approval-start','stage':manifest['stages'][0]['name'],
          'category':'approval_policy','subject':'Production stage automation','options_considered':[
           {'option_id':'automatic','label':'Automatizar producción local, detener antes de publicar','score':1 if data.get('automatic') else 0,'reason':'Selección explícita del usuario'},
           {'option_id':'guided','label':'Aprobación por etapa','score':0 if data.get('automatic') else 1,'reason':'Selección explícita del usuario'}],
          'selected':'automatic' if data.get('automatic') else 'guided','reason':'Autorización del formulario; presupuesto cero; sin publicación externa','user_visible':True,'user_approved':True}]}
        first=manifest['stages'][0]['name']
        write_checkpoint(PROJECTS_DIR,pid,first,'in_progress',{'decision_log':decision},pipeline_type=data['pipeline'])
        save_json(p/'job.json',{'status':'ready','updated_at':now(),'message':'Proyecto creado. Comprueba el runtime e inicia los agentes.','events':[]})
    return {'project_id':pid,'studio_url':'/studio?project='+pid,'board_url':'/p/'+pid}


def production_state(pid):
    p=project_path(pid);request=read_json(p/'production_request.json')
    manifest=load_pipeline_readonly(request['pipeline'])
    job=read_json(p/'job.json',{})
    stages=[]
    for s in manifest['stages']:
        cp=read_json(p/('checkpoint_'+s['name']+'.json'),{})
        stages.append({'name':s['name'],'status':cp.get('status','pending'),'error':cp.get('error')})
    artifacts=[]
    for f in sorted((p/'artifacts').glob('*.json')):
        if f.is_file() and not f.is_symlink():artifacts.append({'name':f.name,'url':f'/media/{pid}/artifacts/{f.name}'})
    outputs=[{'name':f.name,'url':f'/media/{pid}/renders/{f.name}'} for f in sorted((p/'renders').glob('*')) if f.is_file() and not f.is_symlink()]
    from lib.reference_analysis import youtube_url
    try:reference_video_url=youtube_url(request.get('reference',''))
    except ValueError:reference_video_url=None
    from lib.project_translation import summary as translation_summary
    from lib.editorial_freshness import current as verification_current,delivery_current,selection_index,research_index,stale_reasons
    verification=read_json(p/'render_verification.json')
    delivery=read_json(p/'final_delivery.json')
    reviews=read_json(p/'editorial_reviews.json',[])
    selection=selection_index(p)
    research=research_index(p)
    current=verification_current(verification,reviews,selection,research)
    from lib.project_channel_evidence import summary as channel_research_summary
    from lib.project_channel_performance import verified as verified_performance
    try:
        performance=verified_performance(p,request)
        performance_state={'status':'verified','id':performance['id'],'row_total':len(performance['rows']),
            'imported_at_utc':performance['imported_at_utc']} if performance else None
    except (ValueError,TypeError,KeyError,OSError):
        performance_state={'status':'invalid','message':'Copia de rendimiento ausente o alterada.'}
    return {'request':request,'job':job,'stages':stages,'artifacts':artifacts,'outputs':outputs,
        'channel_research':channel_research_summary(p,request),
        'channel_performance':performance_state,
        'translation':translation_summary(pid),
        'reference_video_url':reference_video_url,'render_verification':verification,
        'verification_current':current,'verification_reasons':stale_reasons(verification,reviews,selection,research) if verification else [],
        'final_copy_current':delivery_current(verification,delivery,reviews,selection,research),
        'delivery_retry':read_json(p/'delivery_retry.json'),
        'final_delivery':delivery,'board_url':'/p/'+pid}


def import_inventory(data):
    files=data.get('Ficheros')
    if not isinstance(files,list) or len(files)>200000:raise ValueError('Inventario inválido o demasiado grande')
    for f in files:
        if not isinstance(f,dict) or not isinstance(f.get('FullName'),str) or type(f.get('Length')) is not int or f['Length']<0:raise ValueError('Entrada inválida')
    identity=str(data.get('Serie') or 'sin-serie')
    if not re.fullmatch(r'[A-Za-z0-9-]{1,60}',identity):raise ValueError('Serie inválida')
    snapshot={'Nombre':str(data.get('Nombre','')),'Serie':identity,'Fecha':data.get('Fecha'),'Ficheros':files,'imported_at':now(),'live_scan':False}
    with LOCK:save_json(CONFIG_DIR/'inventories'/(identity+'.json'),snapshot)
    return {'files':len(files),'serial':identity,'live_scan':False}


def resource_catalog():
    inventories=[]
    for p in (CONFIG_DIR/'inventories').glob('*.json'):
        snapshot=read_json(p);inventories.append(snapshot)
    def key(path):return path.replace('\\','/').casefold().split('openmontaje-ia/',1)[-1]
    index={};by_file={}
    for snap in inventories:
        for f in snap['Ficheros']:
            normalized=key(f['FullName'])
            record={'serial':snap['Serie'],'path':f['FullName'],'bytes':f['Length'],'captured_at':snap['Fecha']}
            index.setdefault(normalized,[]).append(record)
            by_file.setdefault((normalized.rsplit('/',1)[-1],f['Length']),[]).append(record)
    groups=[]
    for path in sorted((REPO_ROOT/'docs'/'models').glob('*.json')):
        manifest=read_json(path);entries={f['destination']:f for f in manifest.get('files',[])}
        for group in manifest.get('groups',[]):
            items=[]
            for dest in group.get('files',[]):
                e=entries[dest];matches=index.get(key(dest),[])
                expected=e.get('size_bytes')
                temporary=[record for suffix in ('.fdmdownload','.fdmdownload.reserva','.part','.crdownload') for record in index.get(key(dest)+suffix,[])]
                good=[m for m in matches if expected is not None and m['bytes']==expected]
                elsewhere=[m for m in by_file.get((key(dest).rsplit('/',1)[-1],expected),[]) if key(m['path'])!=key(dest)] if isinstance(expected,int) and expected>0 else []
                status='recorded_size_match' if good else 'possible_elsewhere_size_match' if elsewhere else 'recorded_path_size_unknown' if matches and expected is None else 'recorded_size_mismatch' if matches else 'temporary_download_recorded' if temporary else 'not_recorded'
                items.append({'name':e['path'],'destination_folder':str(Path(dest).parent),'filename':dest.replace('\\','/').split('/')[-1],
                              'size_bytes':expected,'download_url':e.get('url'),'inventory_matches':good,
                              'inventory_path_matches':matches,'inventory_temporary_matches':temporary,'inventory_other_locations':elsewhere[:20],
                              'other_locations_count':len(elsewhere),'other_locations_partial':len(elsewhere)>20,'size_verified':bool(good),
                              'status':status,'inference_verified':False})
            groups.append({'id':group['id'],'label':group.get('name',group['id']),'files':items,'source_catalog':path.name})
    return {'inventories':[{k:v for k,v in x.items() if k!='Ficheros'} for x in inventories], 'groups':groups,
            'notes':['Registro por ruta/tamaño, no prueba de instalación ni de inferencia.','Si no consta, revisa ambos discos antes de descargar.','No todos los modelos tienen adaptador de ejecución integrado.']}
