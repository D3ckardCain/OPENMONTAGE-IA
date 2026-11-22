"""Original editorial drafts tied to a verified channel audit snapshot."""
import re
import uuid

from lib import production_studio as studio
from lib.channel_dossiers import read as read_dossier,CHANNEL,SNAPSHOT

VIDEO=re.compile(r'[A-Za-z0-9_-]{11}')
FIELDS={'channel_id','snapshot_id','video_ids','title','angle','audience','language','format'}


def _folder(channel_id):
    if not isinstance(channel_id,str) or not CHANNEL.fullmatch(channel_id):raise ValueError('ID de canal inválido')
    return studio.CONFIG_DIR/'research/channel_ideas'/channel_id


def create(data):
    if not isinstance(data,dict) or set(data)!=FIELDS:raise ValueError('Completa la propuesta editorial')
    channel_id=data['channel_id'];folder=_folder(channel_id)
    if not isinstance(data['snapshot_id'],str) or not SNAPSHOT.fullmatch(data['snapshot_id']):raise ValueError('ID de expediente inválido')
    dossier=read_dossier(channel_id,data['snapshot_id'])
    ids=data['video_ids']
    if not isinstance(ids,list) or not 1<=len(ids)<=5 or len(set(ids))!=len(ids) or any(not isinstance(v,str) or not VIDEO.fullmatch(v) for v in ids):
        raise ValueError('Elige de uno a cinco videos de referencia distintos')
    available={v['id']:v for v in dossier['report']['publications']}
    if any(v not in available for v in ids):raise ValueError('Referencia ajena al expediente')
    for key,minimum,maximum in [('title',8,150),('angle',30,2000),('audience',3,200)]:
        value=data[key]
        if not isinstance(value,str) or not minimum<=len(value.strip())<=maximum:raise ValueError('Texto editorial inválido: '+key)
    if data['language'] not in ('es','en') or data['format'] not in ('long','short','poster'):
        raise ValueError('Idioma o formato inválido')
    if data['title'].strip().casefold() in {str(available[v].get('title') or '').strip().casefold() for v in ids}:
        raise ValueError('Redacta un título propio distinto al de la referencia')
    record={'id':uuid.uuid4().hex,'status':'draft','created_at_utc':studio.now(),
            'channel_id':channel_id,'snapshot_id':data['snapshot_id'],'snapshot_sha256':dossier['report_sha256'],
            'source_retrieved_at_utc':dossier['report']['retrieved_at_utc'],
            'source_complete_period':dossier['report']['complete_period'],
            'references':[{'id':v,'url':'https://www.youtube.com/watch?v='+v,
                           'title':available[v].get('title'),'viewCount_at_source':available[v].get('viewCount')} for v in ids],
            'title':data['title'].strip(),'angle':data['angle'].strip(),
            'audience':data['audience'].strip(),'language':data['language'],'format':data['format'],
            'fact_review_required':True,'rights_review_required':True,'production_started':False}
    with studio.LOCK:
        if len(list(folder.glob('*.json')) if folder.is_dir() else [])>=200:raise ValueError('Límite local de propuestas alcanzado')
        studio.save_json(folder/(record['id']+'.json'),record)
    return record


def list_drafts(channel_id):
    folder=_folder(channel_id)
    rows=[]
    for path in folder.glob('*.json') if folder.is_dir() else []:
        item=studio.read_json(path)
        if item.get('id')!=path.stem or item.get('channel_id')!=channel_id:raise ValueError('Propuesta alterada')
        rows.append(item)
    return sorted(rows,key=lambda row:row['created_at_utc'],reverse=True)
