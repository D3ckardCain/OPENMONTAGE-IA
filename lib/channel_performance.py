"""Bounded local imports of period-specific, user supplied video performance."""
import csv
import hashlib
import io
import re
import uuid
from datetime import date

from lib import production_studio as studio
from lib.channel_dossiers import _digest
from lib.video_observations import video_id

FIELDS=('video_url','period_start','period_end','impressions','clicks','views',
        'average_view_duration_seconds','video_duration_seconds')


def _integer(value,name):
    if not value or not value.isascii() or not value.isdecimal():
        raise ValueError('Número entero inválido: '+name)
    number=int(value)
    if number>10**15:raise ValueError('Número fuera de rango: '+name)
    return number


def _seconds(value,name):
    if not value:return None
    try:number=float(value)
    except ValueError:raise ValueError('Duración inválida: '+name) from None
    if not 0<number<=10**7 or number!=number:raise ValueError('Duración inválida: '+name)
    return round(number,3)


def _folder():return studio.CONFIG_DIR/'research/channel_performance'


def import_csv(csv_text):
    if not isinstance(csv_text,str) or not csv_text or len(csv_text.encode('utf-8'))>200000:
        raise ValueError('CSV vacío o demasiado grande')
    reader=csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff'),newline=''))
    if reader.fieldnames!=list(FIELDS):
        raise ValueError('Usa exactamente las ocho columnas de la plantilla, en ese orden')
    rows=[];keys=set()
    for raw in reader:
        if len(rows)>=500:raise ValueError('Máximo 500 filas por archivo')
        if None in raw or any(value is None for value in raw.values()):raise ValueError('Fila CSV incompleta')
        identifier=video_id(raw['video_url'])
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',raw['period_start']) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',raw['period_end']):
            raise ValueError('Fechas ISO inválidas')
        try:start=date.fromisoformat(raw['period_start']);end=date.fromisoformat(raw['period_end'])
        except ValueError:raise ValueError('Fechas ISO inválidas') from None
        if start>end:raise ValueError('El periodo termina antes de empezar')
        key=(identifier,start,end)
        if key in keys:raise ValueError('Video y periodo repetidos en el archivo')
        keys.add(key)
        impressions=_integer(raw['impressions'],'impressions') if raw['impressions'] else None
        clicks=_integer(raw['clicks'],'clicks') if raw['clicks'] else None
        views=_integer(raw['views'],'views') if raw['views'] else None
        if clicks is not None and impressions is None:raise ValueError('Clicks requiere impressions del mismo periodo')
        if clicks is not None and clicks>impressions:raise ValueError('Clicks supera impressions')
        average=_seconds(raw['average_view_duration_seconds'],'average_view_duration_seconds')
        duration=_seconds(raw['video_duration_seconds'],'video_duration_seconds')
        rows.append({'video_id':identifier,'video_url':'https://www.youtube.com/watch?v='+identifier,
            'period_start':start.isoformat(),'period_end':end.isoformat(),
            'impressions':impressions,'clicks':clicks,'views':views,
            'average_view_duration_seconds':average,'video_duration_seconds':duration,
            'clicks_per_impression_percent':round(100*clicks/impressions,3) if clicks is not None and impressions else None,
            'average_watch_percent':round(100*average/duration,3) if average is not None and duration else None})
    if not rows:raise ValueError('El CSV no contiene filas')
    record={'id':uuid.uuid4().hex,'source':'CSV aportado por el usuario (sin verificar contra plataforma)',
            'imported_at_utc':studio.now(),'rows':rows,'csv_sha256':hashlib.sha256(csv_text.encode('utf-8')).hexdigest()}
    record['sha256']=_digest(record)
    with studio.LOCK:
        folder=_folder()
        if len(list(folder.glob('*.json')) if folder.is_dir() else [])>=50:
            raise ValueError('Límite de 50 importaciones locales alcanzado')
        studio.save_json(folder/(record['id']+'.json'),record)
    return summary(record)


def read(identifier):
    if not isinstance(identifier,str) or len(identifier)!=32 or any(c not in '0123456789abcdef' for c in identifier):
        raise ValueError('ID de importación inválido')
    record=studio.read_json(_folder()/(identifier+'.json'))
    if not record:raise FileNotFoundError('Importación no encontrada')
    checksum=record.get('sha256')
    if record.get('id')!=identifier or _digest({k:v for k,v in record.items() if k!='sha256'})!=checksum:
        raise ValueError('Importación alterada')
    return record


def summary(record,offset=0,limit=20):
    return {'id':record['id'],'source':record['source'],'imported_at_utc':record['imported_at_utc'],
            'sha256':record['sha256'],'row_total':len(record['rows']),
            'offset':offset,'rows':record['rows'][offset:offset+limit],
            'next_offset':offset+limit if limit and offset+limit<len(record['rows']) else None,
            'limits':'Cifras aportadas por CSV. Clicks/impressions es una relación calculada, no CTR oficial. Duración media/duración del video no es una curva de retención.'}


def list_saved(offset=0,limit=10):
    paths=sorted(_folder().glob('*.json'),reverse=True) if _folder().is_dir() else []
    return {'total':len(paths),'offset':offset,
            'imports':[summary(read(path.stem),0,0) for path in paths[offset:offset+limit]],
            'next_offset':offset+limit if offset+limit<len(paths) else None}
