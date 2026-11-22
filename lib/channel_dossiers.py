"""Immutable local snapshots of bounded channel audits."""
import hashlib
import json
import re
import uuid

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
                     'complete_period':report['complete_period'],'publication_count':len(report['publications'])})
    return sorted(rows,key=lambda row:row['saved_at_utc'],reverse=True)
