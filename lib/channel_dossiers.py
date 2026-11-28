"""Immutable local snapshots of bounded channel audits."""
import hashlib
import json
import re
import uuid
from datetime import datetime,timezone

from lib import production_studio as studio

CHANNEL=re.compile(r'UC[A-Za-z0-9_-]{22}')
SNAPSHOT=re.compile(r'[0-9a-f]{32}')


def _folder(channel_id):
    if not isinstance(channel_id,str) or not CHANNEL.fullmatch(channel_id):
        raise ValueError('ID de canal inválido')
    return studio.CONFIG_DIR/'research/channel_audits'/channel_id


def _digest(value):
    payload=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def save(report):
    if not isinstance(report,dict) or report.get('source')!='YouTube Data API' or not isinstance(report.get('publications'),list):
        raise ValueError('Informe de auditoría inválido')
    folder=_folder(report.get('channel_id'))
    if len(report['publications'])>1000:raise ValueError('Auditoría demasiado grande')
    with studio.LOCK:
        if len(list(folder.glob('*.json')) if folder.is_dir() else [])>=50:
            raise ValueError('Límite de cincuenta auditorías guardadas para este canal')
        identifier=uuid.uuid4().hex
        record={'id':identifier,'saved_at_utc':studio.now(),'report_sha256':_digest(report),'report':report}
        studio.save_json(folder/(identifier+'.json'),record)
    return {'id':identifier,'saved_at_utc':record['saved_at_utc'],'report_sha256':record['report_sha256']}


def read(channel_id,identifier):
    folder=_folder(channel_id)
    if not isinstance(identifier,str) or not SNAPSHOT.fullmatch(identifier):raise ValueError('ID de expediente inválido')
    record=studio.read_json(folder/(identifier+'.json'))
    if not record:raise FileNotFoundError('Expediente no encontrado')
    if record.get('id')!=identifier or record.get('report',{}).get('channel_id')!=channel_id or _digest(record['report'])!=record.get('report_sha256'):
        raise ValueError('Expediente alterado')
    return record


def list_saved(channel_id):
    folder=_folder(channel_id)
    rows=[]
    for path in folder.glob('*.json') if folder.is_dir() else []:
        record=read(channel_id,path.stem)
        report=record['report']
        rows.append({'id':record['id'],'saved_at_utc':record['saved_at_utc'],
                     'report_sha256':record['report_sha256'],'retrieved_at_utc':report['retrieved_at_utc'],
                     'since_utc':report['since_utc'],'cutoff_at_utc':report['cutoff_at_utc'],
                     'window_days':round((_time(report['cutoff_at_utc'])-_time(report['since_utc'])).total_seconds()/86400,2),
                     'complete_period':report['complete_period'],'publication_count':len(report['publications'])})
    return sorted(rows,key=lambda row:row['saved_at_utc'],reverse=True)


def _time(value):
    try:
        date=datetime.fromisoformat(value.replace('Z','+00:00'))
        if date.utcoffset() is None:raise ValueError()
        return date.astimezone(timezone.utc)
    except (ValueError,TypeError,AttributeError):raise ValueError('Fechas de consulta inválidas') from None


def compare(channel_id,older_id,newer_id):
    older=read(channel_id,older_id);newer=read(channel_id,newer_id)
    before=older['report'];after=newer['report']
    hours=(_time(after['retrieved_at_utc'])-_time(before['retrieved_at_utc'])).total_seconds()/3600
    if hours<=0:raise ValueError('El segundo expediente debe tener una consulta posterior')
    before_days=round((_time(before['cutoff_at_utc'])-_time(before['since_utc'])).total_seconds()/86400,2)
    after_days=round((_time(after['cutoff_at_utc'])-_time(after['since_utc'])).total_seconds()/86400,2)
    previous={v['id']:v for v in before['publications']}
    current={v['id']:v for v in after['publications']}
    shared=sorted(previous.keys() & current.keys())
    changes=[];unknown=[];decreased=[]
    for identifier in shared:
        old,new=previous[identifier],current[identifier]
        left,right=old.get('viewCount'),new.get('viewCount')
        if type(left) is not int or type(right) is not int or left<0 or right<0:
            unknown.append(identifier);continue
        if right<left:
            decreased.append({'id':identifier,'before':left,'after':right});continue
        changes.append({'id':identifier,'url':'https://www.youtube.com/watch?v='+identifier,
                        'title':new.get('title') or old.get('title'),
                        'views_before':left,'views_after':right,'views_delta':right-left,
                        'average_views_per_hour':round((right-left)/hours,2)})
    changes.sort(key=lambda row:(-row['views_delta'],row['id']))
    return {'channel_id':channel_id,'older_id':older_id,'newer_id':newer_id,
            'older_retrieved_at_utc':before['retrieved_at_utc'],'newer_retrieved_at_utc':after['retrieved_at_utc'],
            'elapsed_hours':round(hours,2),'older_complete_period':before['complete_period'],
            'newer_complete_period':after['complete_period'],'older_window_days':before_days,
            'newer_window_days':after_days,'same_window_length':before_days==after_days,
            'shared_publication_count':len(shared),
            'new_video_ids':sorted(current.keys()-previous.keys()),
            'absent_video_ids':sorted(previous.keys()-current.keys()),
            'unknown_view_ids':unknown,'decreased_views':decreased,
            'comparable_count':len(changes),'comparable_views_delta':sum(v['views_delta'] for v in changes),
            'changes':changes,
            'note':'Solo diferencias de vistas acumuladas de los mismos videos en dos capturas. Nuevos/ausentes y cifras reducidas no entran en la suma; la lista y el periodo pueden cambiar.'}
