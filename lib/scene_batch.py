"""Prepare a local, reviewable I2V scene manifest without generating media."""
import hashlib
import json
import re
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
