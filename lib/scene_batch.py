"""Prepare a local, reviewable I2V scene manifest without generating media."""
import hashlib
import json
import re
import subprocess
import threading
import uuid
from pathlib import Path
from PIL import Image
from jsonschema import ValidationError

from lib import production_studio as studio
from schemas.artifacts import validate_artifact


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def _prompts(value,ids,label):
    if not isinstance(value,dict) or set(value)!=set(ids):
        raise ValueError('Indica exactamente un prompt de '+label+' por ID de escena')
    if any(not isinstance(text,str) or not text.strip() or len(text)>5000 for text in value.values()):
        raise ValueError('Prompt de '+label+' vacío o demasiado largo')


def prepare(project_id,data):
    if not isinstance(data,dict) or set(data)!={'aspect_ratio','image_prompts','motion_prompts','character_anchors'}:
        raise ValueError('Indica formato, prompts de imagen, prompts de movimiento y anclas de personajes')
    if data['aspect_ratio'] not in ('9:16','16:9'):raise ValueError('Formato admitido: 9:16 o 16:9')
    project=studio.project_path(project_id)
    checkpoint=studio.read_json(project/'checkpoint_scene_plan.json',{})
    if (checkpoint.get('status')!='completed' or checkpoint.get('human_approved') is not True or
            checkpoint.get('project_id')!=project_id):
        raise ValueError('Aprueba primero el plan de escenas del proyecto')
    plan=checkpoint.get('artifacts',{}).get('scene_plan')
    if not isinstance(plan,dict):raise ValueError('Falta el plan de escenas aprobado')
    try:validate_artifact('scene_plan',plan)
    except ValidationError as exc:raise ValueError('Plan de escenas inválido: '+exc.message[:300]) from exc
    scenes=plan['scenes']
    if len(scenes)>240:raise ValueError('Admite hasta 240 escenas por manifiesto')
    ids=[scene['id'] for scene in scenes]
    if len(set(ids))!=len(ids) or any(not isinstance(i,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',i) for i in ids):
        raise ValueError('Usa IDs de escena únicos y estables')
    _prompts(data['image_prompts'],ids,'imagen')
    _prompts(data['motion_prompts'],ids,'movimiento')
    anchors=data['character_anchors']
    if not isinstance(anchors,dict) or len(anchors)>30 or any(
        not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',key) or
        not isinstance(value,str) or not value.strip() or len(value)>2000 for key,value in anchors.items()
    ):raise ValueError('Anclas de personajes inválidas')
    rows=[];previous=0.0
    for order,scene in enumerate(scenes,1):
        start,end=scene['start_seconds'],scene['end_seconds']
        if (type(start) not in (float,int) or type(end) not in (float,int) or
                start<previous or end<=start or end-start>120):
            raise ValueError('Orden o duración de escenas inválidos')
        previous=end
        characters=list(dict.fromkeys(action['character_id'] for action in scene.get('character_actions',[])))
        if any(character not in anchors for character in characters):
            raise ValueError('Falta un ancla visual para un personaje de '+scene['id'])
        creative={'scene_id':scene['id'],'order':order,'start_seconds':start,'end_seconds':end,
            'description':scene['description'],'character_ids':characters,
            'character_anchors':{name:anchors[name] for name in characters},
            'image_prompt':data['image_prompts'][scene['id']].strip(),
            'motion_prompt':data['motion_prompts'][scene['id']].strip(),
            'aspect_ratio':data['aspect_ratio']}
        rows.append({**creative,'creative_sha256':_digest(creative),'status':'planned',
                     'image':None,'takes':[],'approved_take_id':None,'identity_reviewed':False})
    manifest={'version':1,'project_id':project_id,'scene_plan_sha256':_digest(plan),
              'scene_count':len(rows),'duration_seconds':previous,'aspect_ratio':data['aspect_ratio'],
              'scenes':rows,'generation_started':False}
    path=project/'artifacts/scene_batch.json'
    with studio.LOCK:
        if path.is_symlink():raise ValueError('Manifiesto de escenas inválido')
        existing=studio.read_json(path)
        if existing:
            if existing!=manifest:raise ValueError('Ya hay un manifiesto distinto; revísalo antes de cambiar escenas')
            return {'manifest':existing,'created':False}
        studio.save_json(path,manifest)
    return {'manifest':manifest,'created':True}


def read(project_id):
    path=studio.project_path(project_id)/'artifacts/scene_batch.json'
    if path.is_symlink():raise ValueError('Manifiesto de escenas inválido')
    return studio.read_json(path,{'available':False,'generation_started':False})


def approved_plan(project_id):
    project=studio.project_path(project_id)
    checkpoint=studio.read_json(project/'checkpoint_scene_plan.json',{})
    if (checkpoint.get('status')!='completed' or checkpoint.get('human_approved') is not True or
            checkpoint.get('project_id')!=project_id):
        raise ValueError('Aprueba primero el plan de escenas del proyecto')
    plan=checkpoint.get('artifacts',{}).get('scene_plan')
    if not isinstance(plan,dict):raise ValueError('Falta el plan de escenas aprobado')
    try:validate_artifact('scene_plan',plan)
    except ValidationError as exc:raise ValueError('Plan de escenas inválido: '+exc.message[:300]) from exc
    scenes=plan['scenes']
    if len(scenes)>240:raise ValueError('Admite hasta 240 escenas por manifiesto')
    ids=[scene['id'] for scene in scenes]
    if len(set(ids))!=len(ids) or any(not isinstance(i,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',i) for i in ids):
        raise ValueError('Usa IDs de escena únicos y estables')
    return {'scene_plan_sha256':_digest(plan),'scenes':[
        {'id':scene['id'],'description':scene['description'],'start_seconds':scene['start_seconds'],
         'end_seconds':scene['end_seconds'],
         'character_ids':list(dict.fromkeys(action['character_id'] for action in scene.get('character_actions',[])))}
        for scene in scenes]}


def _media(project,relative,kind):
    if not isinstance(relative,str) or len(relative)>500 or '\\' in relative:
        raise ValueError('Indica una ruta relativa dentro del proyecto')
    parts=Path(relative).parts
    if not parts or any(part in ('','.', '..') for part in parts) or Path(relative).is_absolute():
        raise ValueError('Ruta de medio inválida')
    path=project.joinpath(*parts)
    path.resolve().relative_to(project.resolve())
    if any(project.joinpath(*parts[:n]).is_symlink() for n in range(1,len(parts)+1)):
        raise ValueError('No se admiten enlaces simbólicos en la ruta')
    if not path.is_file() or path.is_symlink():raise ValueError('Archivo local ausente o enlace no permitido')
    size=path.stat().st_size
    if not 0<size<2_000_000_000:raise ValueError('Archivo vacío o mayor de 2 GB')
    if kind=='image':
        if path.suffix.lower() not in ('.jpg','.jpeg','.png'):raise ValueError('Formato de imagen inválido')
        with Image.open(path) as image:
            if image.format not in ('PNG','JPEG') or image.width*image.height>16_000_000:raise ValueError('Imagen inválida')
            image.verify()
    else:
        if path.suffix.lower() not in ('.mp4','.webm','.mov'):raise ValueError('Formato de video inválido')
        from lib.media_executables import require_media
        probe=subprocess.run([require_media('ffprobe'),'-v','error','-show_entries','stream=codec_type,width,height:format=duration','-of','json',str(path)],capture_output=True,text=True,timeout=30)
        if probe.returncode:raise ValueError('Video no reconocido por ffprobe')
        details=json.loads(probe.stdout)
        streams=[s for s in details.get('streams',[]) if s.get('codec_type')=='video']
        duration=float(details.get('format',{}).get('duration',0))
        if not streams or not 0<duration<=120 or not streams[0].get('width') or not streams[0].get('height'):
            raise ValueError('Video sin pista válida o duración superior a 120 segundos')
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    result={'path':relative,'sha256':digest.hexdigest(),'bytes':size,'url':'/media/'+project.name+'/'+relative}
    if kind=='video':result['duration_seconds']=duration
    return result


def record_media(project_id,data):
    if not isinstance(data,dict) or set(data)!={'scene_id','kind','relative_path'} or data['kind'] not in ('image','video'):
        raise ValueError('Indica escena, tipo de medio y ruta local')
    project=studio.project_path(project_id)
    media=_media(project,data['relative_path'],data['kind'])
    with studio.LOCK:
        path=project/'artifacts/scene_batch.json'
        manifest=read(project_id)
        if not manifest.get('scenes'):raise ValueError('Prepara antes el manifiesto de escenas')
        if approved_plan(project_id)['scene_plan_sha256']!=manifest['scene_plan_sha256']:
            raise ValueError('El plan aprobado cambió; revisa el manifiesto')
        scene=next((s for s in manifest['scenes'] if s['scene_id']==data['scene_id']),None)
        if scene is None:raise ValueError('Escena desconocida')
        if data['kind']=='image':
            if scene['image'] and scene['image']!=media:raise ValueError('La escena ya tiene otra imagen; revisa la dependencia antes de cambiarla')
            scene['image']=media
        else:
            if not scene['image']:raise ValueError('Registra primero la imagen de la escena')
            if len(scene['takes'])>=8 and media not in scene['takes']:raise ValueError('Máximo ocho tomas por escena')
            if media not in scene['takes']:scene['takes'].append(media)
        scene['status']='approved' if scene['approved_take_id'] else 'ready_for_review' if scene['takes'] else 'image_ready'
        studio.save_json(path,manifest)
    return {'scene':scene,'generation_started':manifest['generation_started']}


def approve_take(project_id,data):
    if (not isinstance(data,dict) or set(data)!={'scene_id','sha256','identity_reviewed'} or
            not isinstance(data['sha256'],str) or data['identity_reviewed'] is not True):
        raise ValueError('Indica escena, SHA-256 y confirma la revisión visual de identidad')
    project=studio.project_path(project_id)
    with studio.LOCK:
        manifest=read(project_id)
        if not manifest.get('scenes'):raise ValueError('Prepara antes el manifiesto de escenas')
        if approved_plan(project_id)['scene_plan_sha256']!=manifest['scene_plan_sha256']:
            raise ValueError('El plan aprobado cambió; revisa el manifiesto')
        scene=next((s for s in manifest['scenes'] if s['scene_id']==data['scene_id']),None)
        if scene is None:raise ValueError('Escena desconocida')
        take=next((t for t in scene['takes'] if t['sha256']==data['sha256']),None)
        if take is None:raise ValueError('Toma no registrada')
        if _media(project,take['path'],'video')['sha256']!=take['sha256']:
            raise ValueError('La toma cambió en disco')
        scene['approved_take_id']=take['sha256'];scene['identity_reviewed']=True;scene['status']='approved'
        studio.save_json(project/'artifacts/scene_batch.json',manifest)
    return {'scene':scene}


def start_preview(project_id,scene_id):
    """Start one explicitly requested WAN I2V preview; never advance to another scene."""
    from lib import model_adapters,production_agent as agent,reference_analysis
    if model_adapters.configuration('wan').get('preset')!='wan22-14b-i2v-4step':
        raise ValueError('Selecciona explícitamente el perfil WAN I2V de cuatro pasos')
    if not model_adapters.diagnostics('wan')['ready']:
        raise ValueError('El adaptador WAN I2V local no está preparado')
    project=studio.project_path(project_id)
    with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
        if agent.ACTIVE or reference_analysis.ACTIVE:
            raise ValueError('Espera a que termine la tarea local activa')
        manifest=read(project_id)
        if not manifest.get('scenes') or approved_plan(project_id)['scene_plan_sha256']!=manifest['scene_plan_sha256']:
            raise ValueError('Prepara y revisa el plan vigente antes de generar')
        scene=next((s for s in manifest['scenes'] if s['scene_id']==scene_id),None)
        if not scene or not scene['image']:raise ValueError('Registra primero una imagen de la escena')
        if scene['approved_take_id'] or len(scene['takes'])>=8:raise ValueError('La escena está aprobada o alcanzó ocho tomas')
        image=_media(project,scene['image']['path'],'image')
        if image['sha256']!=scene['image']['sha256']:raise ValueError('La imagen cambió desde su registro')
        if image['bytes']>8_000_000:raise ValueError('Imagen superior a 8 MB para el adaptador I2V')
        previous=scene.get('active_attempt') if scene['status']=='generation_failed' else None
        if not isinstance(previous,str) or not re.fullmatch('[0-9a-f]{32}',previous):previous=None
        prior=studio.read_json(project/'assets/video'/scene_id/str(previous)/'comfy-wan-job.json',{}) if previous else {}
        attempt=previous if prior.get('prompt_id') else uuid.uuid4().hex
        scene['status']='generating';scene['last_error']=None;scene['active_attempt']=attempt
        manifest['generation_started']=True
        studio.save_json(project/'artifacts/scene_batch.json',manifest)
        token=threading.Event()
        thread=threading.Thread(target=_preview_worker,args=(project_id,scene_id,attempt,token),daemon=True,name='scene-preview-'+project_id)
        agent.ACTIVE[project_id]=(thread,token)
        thread.start()
    return {'started':True,'scene_id':scene_id,'attempt':attempt}


def _preview_worker(project_id,scene_id,attempt,token):
    from lib import production_agent as agent
    project=studio.project_path(project_id)
    try:
        scene=next(s for s in read(project_id)['scenes'] if s['scene_id']==scene_id)
        output=project/'assets/video'/scene_id/attempt
        image=project/scene['image']['path']
        from lib.model_comfy_adapter import execute_workflow
        width,height=(288,512) if scene['aspect_ratio']=='9:16' else (512,288)
        inputs={'project_id':project_id,'input_path':str(image),'image_sha256':scene['image']['sha256'],
                'text':scene['motion_prompt'],'output_dir':str(output),'width':width,'height':height,
                'frames':49,'fps':12,'steps':4,'timeout':1800}
        prior=studio.read_json(output/'comfy-wan-job.json',{})
        if prior.get('prompt_id'):inputs['resume_prompt_id']=prior['prompt_id']
        else:output.mkdir(parents=True,exist_ok=False)
        result=execute_workflow('wan',inputs,output)
        videos=[Path(p) for p in result['outputs'] if Path(p).suffix.lower() in ('.mp4','.webm','.mov')]
        if not videos:raise ValueError('El workflow no devolvió una toma de video')
        for path in videos[:8]:record_media(project_id,{'scene_id':scene_id,'kind':'video','relative_path':path.relative_to(project).as_posix()})
        with studio.LOCK:
            manifest=read(project_id)
            scene=next(s for s in manifest['scenes'] if s['scene_id']==scene_id)
            if scene.get('active_attempt')==attempt:
                scene['active_attempt']=None
                studio.save_json(project/'artifacts/scene_batch.json',manifest)
    except Exception as exc:
        with studio.LOCK:
            manifest=read(project_id)
            scene=next(s for s in manifest['scenes'] if s['scene_id']==scene_id)
            if scene.get('active_attempt')==attempt:
                scene['status']='generation_failed';scene['last_error']=str(exc)[:1800]
                studio.save_json(project/'artifacts/scene_batch.json',manifest)
    finally:
        with agent.ACTIVE_LOCK:
            if agent.ACTIVE.get(project_id,(None,None))[1] is token:agent.ACTIVE.pop(project_id,None)
