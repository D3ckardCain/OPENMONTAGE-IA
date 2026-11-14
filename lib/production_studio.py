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
                'model':'','resource_roots':[],'max_turns':120}
    return {**defaults, **read_json(CONFIG_DIR/'settings.json',{})}


def configure(data):
    allowed={'ollama_url','comfyui_url','model','resource_roots','max_turns'}
    if set(data)-allowed:raise ValueError('Configuración desconocida')
    value={**settings(),**data}
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
                           'ffmpeg_ready':bool(shutil.which('ffmpeg')),'problems':[]}
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
    allowed={'title','brief','pipeline','language','reference','automatic'}
    if set(data)-allowed:raise ValueError('Campos desconocidos')
    for name in ('title','brief','pipeline','language'):
        if not isinstance(data.get(name),str) or not data[name].strip():raise ValueError('Completa título, solicitud, pipeline e idioma')
    if len(data['title'])>150 or len(data['brief'])>12000 or len(str(data.get('reference','')))>2000:raise ValueError('Solicitud demasiado larga')
    if type(data.get('automatic',False)) is not bool:raise ValueError('Política automática inválida')
    if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*',data['language']):raise ValueError('Idioma inválido')
    if not isinstance(data.get('reference',''),str):raise ValueError('Referencia inválida')
    if data['pipeline']=='framework-smoke':raise ValueError('Pipeline reservado para pruebas')
    manifest=load_pipeline_readonly(data['pipeline'])
    pid='video-'+uuid.uuid4().hex[:12]
    with LOCK:
        p=init_project(pid,title=data['title'],pipeline_type=data['pipeline'],pipeline_dir=PROJECTS_DIR)
        save_json(p/'production_request.json',{**data,'project_id':pid,'created_at':now(),'budget_usd':0,'publish_authorized':False})
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
    return {'request':request,'job':job,'stages':stages,'artifacts':artifacts,'outputs':outputs,'board_url':'/p/'+pid}


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
    def key(path):return path.replace('\\','/').split('OPENMONTAJE-IA/',1)[-1].casefold()
    index={}
    for snap in inventories:
        for f in snap['Ficheros']:index.setdefault(key(f['FullName']),[]).append({'serial':snap['Serie'],'path':f['FullName'],'bytes':f['Length'],'captured_at':snap['Fecha']})
    groups=[]
    for path in sorted((REPO_ROOT/'docs'/'models').glob('*.json')):
        manifest=read_json(path);entries={f['destination']:f for f in manifest.get('files',[])}
        for group in manifest.get('groups',[]):
            items=[]
            for dest in group.get('files',[]):
                e=entries[dest];matches=index.get(key(dest),[])
                good=[m for m in matches if m['bytes']==e['size_bytes']]
                items.append({'name':e['path'],'destination_folder':str(Path(dest).parent),'filename':dest.replace('\\','/').split('/')[-1],
                              'size_bytes':e['size_bytes'],'download_url':e.get('url'),'inventory_matches':good,
                              'status':'recorded_size_match' if good else 'not_recorded','inference_verified':False})
            groups.append({'id':group['id'],'label':group.get('name',group['id']),'files':items,'source_catalog':path.name})
    return {'inventories':[{k:v for k,v in x.items() if k!='Ficheros'} for x in inventories], 'groups':groups,
            'notes':['Registro por ruta/tamaño, no prueba de instalación ni de inferencia.','Si no consta, revisa ambos discos antes de descargar.','No todos los modelos tienen adaptador de ejecución integrado.']}
