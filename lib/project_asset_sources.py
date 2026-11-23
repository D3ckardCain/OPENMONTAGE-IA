"""Project-scoped provenance ledger for local media proposed for production."""
import hashlib
from functools import lru_cache
from pathlib import Path
import os
from itertools import islice
from urllib.parse import urlsplit

from lib import production_studio as studio
from lib.channel_dossiers import _digest


def _record_path(project):return project/'artifacts/asset_sources.json'


@lru_cache(maxsize=128)
def _hash_file(path,key):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def _checksum(path):
    before=path.stat()
    key=(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
    digest=_hash_file(str(path),key)
    after=path.stat()
    if key!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):
        raise ValueError('El medio cambió durante la comprobación')
    return digest


def _asset(project,relative):
    if not isinstance(relative,str) or len(relative)>300 or '\\' in relative:
        raise ValueError('Ruta relativa de medio inválida')
    path=Path(relative)
    if not path.parts or path.is_absolute() or '..' in path.parts or path.parts[0] not in ('assets','source_images','thumbnails'):
        raise ValueError('El medio debe estar dentro de assets, source_images o thumbnails del proyecto')
    target=project/path
    if any((project.joinpath(*path.parts[:index])).is_symlink() for index in range(1,len(path.parts)+1)):
        raise ValueError('No se admiten enlaces simbólicos')
    if not target.is_file() or target.stat().st_size>100_000_000:
        raise ValueError('Medio ausente o superior a 100 MB; los clips grandes requieren un flujo aparte')
    return target


def _url(value):
    if not value:return
    parsed=urlsplit(value)
    if len(value)>1000 or parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Usa URL HTTPS sin credenciales')


def read(pid):
    project=studio.project_path(pid);path=_record_path(project)
    if path.is_symlink():raise ValueError('Registro de procedencia alterado')
    record=studio.read_json(path)
    if record is None:return {'status':'empty','revision':None,'entries':[],
        'limits':'Las declaraciones del operador no certifican licencias; verifica condiciones vigentes y autoría antes de publicar.'}
    if (not isinstance(record,dict) or record.get('project_id')!=pid
            or record.get('revision')!=_digest({k:v for k,v in record.items() if k!='revision'})
            or not isinstance(record.get('entries'),list)):
        raise ValueError('Registro de procedencia alterado')
    for entry in record['entries']:
        target=_asset(project,entry['path'])
        if _checksum(target)!=entry['sha256']:raise ValueError('Medio del registro alterado')
    return {'status':'draft',**record,
        'limits':'Declaraciones locales del operador, sin verificación externa de licencias o autoría. Una licencia puede cambiar; revisa antes de publicar.'}


def save(pid,data):
    if not isinstance(data,dict) or set(data)!={'entry','expected_revision'} or not isinstance(data['entry'],dict):
        raise ValueError('Entrada de procedencia inválida')
    item=data['entry'];fields={'path','source_kind','source_url','license_url','creator','license_name','commercial_use','modifications','notes'}
    if set(item)!=fields or item['source_kind'] not in ('own','stock','public_domain','generated'):
        raise ValueError('Campos de procedencia inválidos')
    for name,max_length in (('path',300),('source_url',1000),('license_url',1000),('creator',200),('license_name',200),('notes',1000)):
        if not isinstance(item[name],str) or len(item[name])>max_length:raise ValueError('Campo de procedencia inválido: '+name)
    for name in ('commercial_use','modifications'):
        if item[name] not in ('yes','no','unknown'):raise ValueError('Condición de uso inválida: '+name)
    _url(item['source_url']);_url(item['license_url'])
    if item['source_kind']=='stock' and (not item['source_url'] or not item['license_url']):
        raise ValueError('El stock requiere URL de origen y de licencia')
    project=studio.project_path(pid);target=_asset(project,item['path'])
    digest=_checksum(target)
    with studio.LOCK:
        previous=read(pid)
        if data['expected_revision']!=previous['revision']:
            raise ValueError('El registro cambió; recárgalo antes de guardar')
        entries=[row for row in previous['entries'] if row['path']!=item['path']]
        if len(entries)>=20:raise ValueError('Máximo 20 medios registrados')
        record={'project_id':pid,'entries':entries+[{**item,'sha256':digest,'recorded_at_utc':studio.now()}]}
        record['revision']=_digest(record)
        studio.save_json(_record_path(project),record)
    return read(pid)


MEDIA_SUFFIXES={'.png','.jpg','.jpeg','.webp','.gif','.mp4','.mov','.mkv','.webm','.wav','.mp3','.flac','.srt'}


def coverage(pid,offset=0,limit=20):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=50:
        raise ValueError('Página inválida')
    project=studio.project_path(pid)
    registered={item['path']:item for item in read(pid)['entries']}
    rows=[];scanned=0;examined=0;complete=True;skipped_links=0
    for root in ('assets','source_images','thumbnails'):
        folder=project/root
        if folder.is_symlink():skipped_links+=1;continue
        if not folder.is_dir():continue
        stack=[(folder,0)]
        while stack:
            parent,depth=stack.pop()
            with os.scandir(parent) as entries:
                children=list(islice(entries,max(0,2001-examined)))
            examined+=len(children)
            if examined>2000:complete=False;children=children[:max(0,len(children)-(examined-2000))]
            children.sort(key=lambda entry:entry.name)
            for child in children:
                if child.is_symlink():skipped_links+=1;continue
                if child.is_dir(follow_symlinks=False):
                    if depth<5:stack.append((Path(child.path),depth+1))
                    else:complete=False
                    continue
                if not child.is_file(follow_symlinks=False) or Path(child.name).suffix.lower() not in MEDIA_SUFFIXES:continue
                scanned+=1
                if scanned>1000:complete=False;break
                relative=Path(child.path).relative_to(project).as_posix()
                row=registered.get(relative)
                rows.append({'path':relative,'bytes':child.stat(follow_symlinks=False).st_size,
                    'status':'registered' if row else 'unregistered',
                    'source_kind':row['source_kind'] if row else None,
                    'commercial_use':row['commercial_use'] if row else None})
            if scanned>1000 or examined>2000:break
        if scanned>1000 or examined>2000:break
    rows.sort(key=lambda row:row['path'])
    count=len(rows)
    return {'total':count,'registered_total':sum(row['status']=='registered' for row in rows),
        'unregistered_total':sum(row['status']=='unregistered' for row in rows),
        'offset':offset,'rows':rows[offset:offset+limit],
        'next_offset':offset+limit if offset+limit<count else None,
        'complete_scan':complete,'skipped_symlinks':skipped_links,
        'limits':'Solo extensiones multimedia en assets, source_images y thumbnails; máximo 1000 medios, 2000 entradas exploradas y profundidad 6. Un archivo registrado aún requiere revisar derechos y vigencia de licencia.'}
