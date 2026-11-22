"""Local, attributed manual observations from a browser extension."""
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit,parse_qs

from lib import production_studio as studio

VIDEO_ID=re.compile(r'[A-Za-z0-9_-]{11}')
FIELDS={'video_url','views','vph','engagement_percent','outlier_ratio','seo_score','notes'}


def video_id(value):
    if not isinstance(value,str) or len(value)>300:raise ValueError('Enlace de video inválido')
    parsed=urlsplit(value)
    if parsed.scheme!='https' or parsed.hostname not in ('www.youtube.com','youtube.com') or parsed.path!='/watch' or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('Usa un enlace HTTPS de video de YouTube')
    params=parse_qs(parsed.query)
    identifier=params.get('v',[])
    if len(identifier)!=1 or not VIDEO_ID.fullmatch(identifier[0]):raise ValueError('ID de video inválido')
    return identifier[0]


def _number(value,name,maximum,integer=False):
    if value is None or value=='':return None
    if isinstance(value,bool) or not isinstance(value,(int,float)) or value<0 or value>maximum or value!=value:
        raise ValueError('Métrica inválida: '+name)
    if integer and int(value)!=value:raise ValueError('Métrica entera requerida: '+name)
    return int(value) if integer else round(float(value),3)


def _path():return studio.CONFIG_DIR/'research/video_observations.json'


def read(identifier=None):
    if identifier is not None and (not isinstance(identifier,str) or not VIDEO_ID.fullmatch(identifier)):
        raise ValueError('ID de video inválido')
    rows=studio.read_json(_path(),[])
    if not isinstance(rows,list):raise ValueError('Expediente de observaciones inválido')
    return [row for row in rows if identifier is None or row.get('video_id')==identifier]


def add(data):
    if not isinstance(data,dict) or set(data)!=FIELDS:raise ValueError('Completa los campos del registro')
    identifier=video_id(data['video_url'])
    notes=data['notes']
    if not isinstance(notes,str) or len(notes)>1000:raise ValueError('Notas demasiado largas')
    metrics={'views':_number(data['views'],'vistas',10**15,True),
             'vph':_number(data['vph'],'VPH',10**9),
             'engagement_percent':_number(data['engagement_percent'],'engagement',100),
             'outlier_ratio':_number(data['outlier_ratio'],'outlier',10**6),
             'seo_score':_number(data['seo_score'],'SEO',100)}
    if all(value is None for value in metrics.values()):raise ValueError('Indica al menos una cifra observada')
    row={'video_id':identifier,'video_url':'https://www.youtube.com/watch?v='+identifier,
         'source':'vidIQ Edge (transcripción manual)','observed_at_utc':datetime.now(timezone.utc).isoformat(),
         **metrics,'notes':notes.strip()}
    with studio.LOCK:
        rows=read()
        if len(rows)>=2000:raise ValueError('Límite local de observaciones alcanzado')
        rows.append(row)
        studio.save_json(_path(),rows)
    return row
