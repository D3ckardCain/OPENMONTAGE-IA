"""Explicit, single-job candidate downloads. Installed weights are never replaced."""
import hashlib
import os
import re
import shutil
import threading
from threading import Thread
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from lib import update_center as updates
from lib import production_studio as studio

_LOCK=threading.RLock()
_JOBS={}
_ACTIVE=None
_BLOCK=4*1024*1024


def _allowed_url(url):
    parsed=urlsplit(url)
    return (parsed.scheme=='https' and not parsed.username and not parsed.password
            and parsed.port in (None,443) and parsed.hostname in (
                'huggingface.co','cdn-lfs.huggingface.co','cdn-lfs-us-1.hf.co',
                'cdn-lfs-eu-1.hf.co','cas-bridge.xethub.hf.co'))


class _Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        target=urljoin(request.full_url,newurl)
        if not _allowed_url(target):raise ValueError('Redirección fuera de los servidores de descarga admitidos')
        return super().redirect_request(request,fp,code,msg,headers,target)


def _open(url,offset):
    if not _allowed_url(url):raise ValueError('Fuente de descarga no admitida')
    headers={'User-Agent':'OpenMontage-candidate-download/1','Accept-Encoding':'identity'}
    if offset:headers['Range']='bytes='+str(offset)+'-'
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),_Redirect())
    return opener.open(urllib.request.Request(url,headers=headers),timeout=30)


def _change(job,**values):
    with _LOCK:job['report'].update(values,updated_at=studio.now())


def _check_cancel(job):
    if job['cancel'].is_set():raise InterruptedError('Descarga cancelada; parcial conservado')


def _safe_parent(path):
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('La ruta de descarga contiene un enlace')


def _hash_partial(path,expected,job):
    digest=hashlib.sha256();count=0
    if not path.exists():return digest,0
    _safe_parent(path)
    before=path.stat()
    if not path.is_file() or before.st_size>expected:raise ValueError('Parcial inválido o mayor que el candidato')
    with path.open('rb') as stream:
        while count<=before.st_size:
            _check_cancel(job)
            block=stream.read(min(_BLOCK,before.st_size-count+1))
            if not block:break
            count+=len(block);digest.update(block)
    after=path.stat()
    if count!=before.st_size or (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError('El parcial cambió durante la lectura')
    return digest,count


def _finalize(part,candidate,job,size):
    _check_cancel(job)
    _safe_parent(candidate)
    try:
        os.link(part,candidate)  # Atomic no-clobber, on filesystems supporting links.
    except FileExistsError:raise ValueError('El candidato ya existe; no se sustituye')
    except OSError:
        # exFAT and other filesystems may not support hard links. An exclusive
        # copy needs another full file's worth of space; keep partial on failure.
        if shutil.disk_usage(candidate.parent).free<size:
            raise ValueError('Falta espacio para finalizar en este sistema de archivos; parcial conservado')
        created=False
        try:
            with candidate.open('xb') as output:
                created=True
                with part.open('rb') as source:
                    while block:=source.read(_BLOCK):
                        _check_cancel(job);output.write(block)
                output.flush();os.fsync(output.fileno())
        except Exception:
            if created:candidate.unlink(missing_ok=True)
            raise
    part.unlink()


def _run(job):
    global _ACTIVE
    args=job['args']
    try:
        _change(job,status='checking')
        plan=updates.prepare_file_update(args['identifier'],args['index'],args['revision'])
        candidate=plan.get('candidate')
        if not candidate:raise ValueError('No hay candidato verificable para descargar')
        if candidate['sha256']!=args['expected_sha256']:raise ValueError('El SHA-256 no coincide con el plan revisado')
        size=candidate['size_bytes']
        if size>100_000_000_000:raise ValueError('El candidato supera el límite de 100 GB')
        path=Path(candidate['destination'])
        _change(job,candidate_destination=candidate['destination'],expected_bytes=size)
        if not path.is_absolute():raise ValueError('Ruta no disponible en este equipo')
        _safe_parent(path)
        _check_cancel(job)
        if path.exists():
            checked=updates._check_local_entry({'destination':str(path),'catalog_sha256':candidate['sha256'],'catalog_bytes':size},args['index'])
            if checked['status']!='matches_catalog':raise ValueError('El candidato existente no coincide; no se sustituye')
            _change(job,status='candidate_ready',bytes_present=size,sha256=candidate['sha256']);return
        space=updates.check_candidate_space(args['identifier'],args['index'],args['revision'])
        if space['status']!='space_available_for_candidate':raise ValueError('No hay espacio o destino disponible para una copia completa')
        _check_cancel(job)
        path.parent.mkdir(parents=True,exist_ok=True)
        part=path.with_name(path.name+'.part')
        _safe_parent(part)
        digest,offset=_hash_partial(part,size,job)
        _change(job,status='downloading',bytes_present=offset,resumed_from=offset)
        if offset<size:
            _check_cancel(job)
            with _open(candidate['url'],offset) as response:
                code=response.status
                if response.headers.get('Content-Encoding','identity').lower()!='identity':raise ValueError('Respuesta comprimida no admitida')
                if offset:
                    value=response.headers.get('Content-Range','')
                    if code!=206 or value!='bytes '+str(offset)+'-'+str(size-1)+'/'+str(size):
                        raise ValueError('La fuente no devolvió el rango solicitado; parcial conservado')
                elif code!=200:raise ValueError('Respuesta de descarga inválida')
                length=response.headers.get('Content-Length')
                if length is not None and (not length.isdigit() or int(length)!=size-offset):raise ValueError('Tamaño de respuesta distinto al candidato')
                with part.open('r+b' if part.exists() else 'xb') as output:
                    output.seek(0,2)
                    if output.tell()!=offset:raise ValueError('El parcial cambió antes de continuar')
                    count=offset
                    while count<=size:
                        _check_cancel(job)
                        block=response.read(min(_BLOCK,size-count+1))
                        if not block:break
                        if count+len(block)>size:raise ValueError('La respuesta excede el tamaño del candidato')
                        output.write(block);digest.update(block);count+=len(block)
                        _change(job,bytes_present=count)
                    output.flush();os.fsync(output.fileno())
        _change(job,status='verifying')
        if part.stat().st_size!=size or digest.hexdigest()!=candidate['sha256']:
            raise ValueError('El parcial no coincide con tamaño y SHA-256; no se activa')
        checked=updates._check_local_entry({'destination':str(part),'catalog_sha256':candidate['sha256'],'catalog_bytes':size},args['index'])
        if checked['status']!='matches_catalog':raise ValueError('El archivo parcial no supera la comprobación local final')
        _finalize(part,path,job,size)
        _change(job,status='candidate_ready',bytes_present=size,sha256=candidate['sha256'])
    except InterruptedError:
        _change(job,status='cancelled',message='Cancelado; el parcial queda disponible para reanudar.')
    except Exception as exc:
        # Avoid leaking signed redirect URLs through urllib exception messages.
        message=str(exc) if isinstance(exc,ValueError) else 'Fallo de red o disco; parcial conservado si existe.'
        _change(job,status='failed',message=message[:240])
    finally:
        with _LOCK:
            if _ACTIVE==job['report']['job_id']:_ACTIVE=None


def start(identifier,index,revision,expected_sha256):
    global _ACTIVE
    if not isinstance(revision,str) or not updates._SHA.fullmatch(revision):raise ValueError('Commit inválido')
    if type(index) is not int or index<0 or index>=len(updates._files(identifier)):raise ValueError('Archivo inválido')
    if not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256):raise ValueError('SHA-256 inválido')
    with _LOCK:
        if _ACTIVE:raise ValueError('Ya hay una descarga de candidato en curso')
        while len(_JOBS)>=20:_JOBS.pop(next(iter(_JOBS)))
        job_id=uuid.uuid4().hex
        report={'job_id':job_id,'status':'queued','id':identifier,'index':index,'remote_revision':revision,
                'bytes_present':0,'update_allowed':False,'configuration_changed':False,'updated_at':studio.now(),
                'note':'Solo obtiene un candidato separado; integridad no equivale a compatibilidad, licencia o calidad. No activa modelos ni instala dependencias.'}
        job={'args':dict(identifier=identifier,index=index,revision=revision,expected_sha256=expected_sha256),
             'report':report,'cancel':threading.Event()}
        _JOBS[job_id]=job;_ACTIVE=job_id
        try:Thread(target=_run,args=(job,),daemon=True).start()
        except Exception:
            _ACTIVE=None;_JOBS.pop(job_id);raise
        return dict(report)


def status(job_id):
    with _LOCK:
        if job_id not in _JOBS:raise ValueError('Descarga no disponible en esta sesión')
        return dict(_JOBS[job_id]['report'])


def cancel(job_id):
    with _LOCK:
        if job_id not in _JOBS:raise ValueError('Descarga no disponible en esta sesión')
        _JOBS[job_id]['cancel'].set()
        return dict(_JOBS[job_id]['report'])


def discard_partial(job_id):
    with _LOCK:
        if _ACTIVE:raise ValueError('Espera a que termine la descarga antes de descartar el parcial')
        if job_id not in _JOBS:raise ValueError('Descarga no disponible en esta sesión')
        job=_JOBS[job_id]
        if job['report']['status'] not in ('failed','cancelled'):raise ValueError('Solo se descartan parciales de descargas fallidas o canceladas')
        args=job['args']
        plan=updates.prepare_file_update(args['identifier'],args['index'],args['revision'])
        candidate=plan.get('candidate')
        if not candidate or candidate['sha256']!=args['expected_sha256']:raise ValueError('El candidato ya no corresponde al plan')
        path=Path(candidate['destination'])
        if not path.is_absolute():raise ValueError('Ruta no disponible en este equipo')
        part=path.with_name(path.name+'.part');_safe_parent(part)
        part.unlink(missing_ok=True)
        _change(job,status='partial_discarded',bytes_present=0,message='Parcial descartado; candidato final y original sin cambios.')
        return dict(job['report'])


def list_jobs(identifier,index,revision):
    with _LOCK:
        return {'rows':[dict(job['report']) for job in reversed(list(_JOBS.values()))
                        if (job['args']['identifier'],job['args']['index'],job['args']['revision'])==(identifier,index,revision)],
                'note':'Trabajos de esta sesión; los parciales del disco permanecen tras reiniciar el estudio.'}
