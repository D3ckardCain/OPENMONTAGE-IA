"""Explicit version probes for configured tools; never invoke self-updaters."""
import os
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from lib import production_studio as studio
from lib import external_applications as applications
from lib import update_center as updates

_COMMANDS={'yt-dlp':['--ignore-config','--no-plugin-dirs','--version'],'deno':['--version'],'ffmpeg':['-version'],'ffprobe':['-version']}


def _version(identifier,value,release=False):
    if not isinstance(value,str) or len(value)>64:return None
    if release and value.startswith('v'):value=value[1:]
    if identifier=='yt-dlp':
        if not re.fullmatch(r'\d{4}\.\d{2}\.\d{2}',value):return None
        try:date=datetime.strptime(value,'%Y.%m.%d')
        except ValueError:return None
        return date.year,date.month,date.day
    if not re.fullmatch(r'(0|[1-9]\d{0,5})\.(0|[1-9]\d{0,5})\.(0|[1-9]\d{0,5})',value):return None
    return tuple(int(part) for part in value.split('.'))


def _compare(identifier,online=True):
    if identifier not in _COMMANDS:raise ValueError('Aplicación sin comprobación de versión configurada')
    if type(online) is not bool:raise ValueError('Modo de consulta inválido')
    item=applications.CATALOG[identifier]
    configured=studio.settings().get(item['setting'],'')
    result={'id':identifier,'checked_at':studio.now(),'local_version':None,'latest_version':None,
            'update_available':None,'network_checked':False,'remote_query_attempted':False,
            'process_attempted':False,'process_started':False,'installation_started':False,'configuration_changed':False,
            'note':'Consulta explícita de versión del ejecutable configurado. No ejecuta autoupdate, instaladores, descargas de modelos ni modifica la configuración. Una versión mayor no acredita compatibilidad.'}
    if not isinstance(configured,str) or not configured:return {**result,'status':'local_unavailable'}
    path=Path(configured)
    if not path.is_absolute() or path.name.casefold() not in {name.casefold() for name in item['executables']}:
        return {**result,'status':'local_unavailable'}
    try:
        if not path.is_file():return {**result,'status':'local_unavailable'}
        before=path.stat()
        env={**os.environ,'DENO_NO_UPDATE_CHECK':'1'}
        if identifier in ('ffmpeg','ffprobe'):
            env.pop('FFREPORT',None)
            env['AV_LOG_FORCE_NOCOLOR']='1'
        result['process_attempted']=True
        process=subprocess.run([str(path),*_COMMANDS[identifier]],stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False,
                               timeout=5,check=False,cwd=str(path.parent),env=env)
        result['process_started']=True
        after=path.stat()
    except subprocess.TimeoutExpired:return {**result,'process_started':True,'status':'version_probe_failed'}
    except OSError:return {**result,'status':'version_probe_failed'}
    if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        return {**result,'status':'executable_changed_during_probe'}
    if process.returncode!=0 or len(process.stdout)>16_384:return {**result,'status':'version_probe_failed'}
    result.update(local_executable=str(path),executable_fingerprint=_fingerprint(after))
    output=process.stdout.decode('utf-8',errors='replace').strip()
    if identifier in ('ffmpeg','ffprobe'):
        match=re.match(re.escape(identifier)+r' version (\S{1,120})(?:\s|$)',output)
        token=match.group(1) if match else None
        pattern=r'(?:n?\d+\.\d+(?:\.\d+)?(?:[-+][\w.+-]+)?|N-\d+-g[0-9a-f]+(?:[-+][\w.+-]+)?|\d{4}-\d{2}-\d{2}-git-[0-9a-f]+(?:[-+][\w.+-]+)?)'
        if not token or not re.fullmatch(pattern,token):return {**result,'status':'local_version_unrecognized'}
        return {**result,'local_version':token,'status':'local_version_checked' if not online else 'release_review_required',
                'source_url':'https://ffmpeg.org/download.html'}
    match=re.fullmatch(r'\d{4}\.\d{2}\.\d{2}',output) if identifier=='yt-dlp' else re.match(r'deno (\S+)(?:\s|$)',output)
    local=match.group(0) if identifier=='yt-dlp' and match else match.group(1) if match else None
    local_parts=_version(identifier,local)
    if local_parts is None:return {**result,'status':'local_version_unrecognized'}
    result['local_version']=local
    if not online:return {**result,'status':'local_version_checked'}
    result['remote_query_attempted']=True
    try:release=updates.check('application',identifier)
    except ValueError:return {**result,'status':'remote_unavailable'}
    latest=release.get('tag')
    result.update(latest_version=str(latest)[:120],source_url=release.get('source_url'),
                  published_at=release.get('published_at'),network_checked=True)
    remote_parts=_version(identifier,latest,release=True)
    if remote_parts is None:return {**result,'status':'comparison_inconclusive'}
    state='update_available' if remote_parts>local_parts else 'versions_match' if remote_parts==local_parts else 'local_newer_than_release'
    return {**result,'status':state,'update_available':remote_parts>local_parts}


_HISTORY_LIMIT=128_000
_STATUSES={'local_unavailable','version_probe_failed','executable_changed_during_probe',
           'local_version_unrecognized','local_version_checked','remote_unavailable',
           'release_review_required','comparison_inconclusive','update_available','versions_match','local_newer_than_release'}


def _fingerprint(info):
    return {'size':info.st_size,'mtime_ns':info.st_mtime_ns,'inode':info.st_ino,'device':info.st_dev}


def _history_path(identifier):
    if not isinstance(identifier,str) or identifier not in _COMMANDS:raise ValueError('Aplicación no admitida')
    return studio.CONFIG_DIR/'application_versions'/(identifier+'.json')


def _read_history(identifier):
    path=_history_path(identifier)
    try:
        if not path.exists():return []
        if path.is_symlink() or path.stat().st_size>_HISTORY_LIMIT:raise ValueError()
        with path.open('rb') as stream:raw=stream.read(_HISTORY_LIMIT+1)
        if len(raw)>_HISTORY_LIMIT:raise ValueError()
        data=json.loads(raw)
        if not isinstance(data,dict) or data.get('id')!=identifier or not isinstance(data.get('records'),list) or len(data['records'])>20:raise ValueError()
        for record in data['records']:
            if not isinstance(record,dict) or record.get('status') not in _STATUSES:raise ValueError()
            when=record.get('checked_at')
            if not isinstance(when,str) or len(when)>80 or datetime.fromisoformat(when).tzinfo is None:raise ValueError()
            for key in ('local_version','latest_version'):
                value=record.get(key)
                if value is not None and (not isinstance(value,str) or len(value)>120):raise ValueError()
            executable=record.get('local_executable');fingerprint=record.get('executable_fingerprint')
            if executable is not None:
                if not isinstance(executable,str) or len(executable)>4096:raise ValueError()
                candidate=Path(executable)
                if not candidate.is_absolute() or candidate.name.casefold() not in {name.casefold() for name in applications.CATALOG[identifier]['executables']}:raise ValueError()
            if fingerprint is not None:
                if not isinstance(fingerprint,dict) or set(fingerprint)!={'size','mtime_ns','inode','device'} or any(type(value) is not int for value in fingerprint.values()):raise ValueError()
        return data['records']
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
        raise ValueError('No se puede utilizar el historial local de versiones') from exc


def compare(identifier,online=True):
    result=_compare(identifier,online)
    record={key:result.get(key) for key in ('checked_at','status','local_version','latest_version','local_executable','executable_fingerprint')}
    try:
        with studio.LOCK:
            records=(_read_history(identifier)+[record])[-20:]
            data={'id':identifier,'records':records}
            if len(json.dumps(data,ensure_ascii=False,indent=2).encode('utf-8'))>_HISTORY_LIMIT:raise ValueError('Límite de historial')
            studio.save_json(_history_path(identifier),data)
        return {**result,'history_saved':True}
    except (OSError,ValueError):
        return {**result,'history_saved':False,'history_warning':'La comprobación terminó, pero no se pudo guardar el historial; el resultado actual se conserva.'}


def history(identifier):
    configured=studio.settings().get(applications.CATALOG[identifier]['setting'],'') if identifier in _COMMANDS else ''
    with studio.LOCK:records=_read_history(identifier)
    rows=[]
    for record in reversed(records):
        executable=record.get('local_executable');expected=record.get('executable_fingerprint')
        state='not_recorded'
        if executable and expected:
            if configured!=executable:state='configuration_changed'
            else:
                try:state='metadata_match' if _fingerprint(Path(executable).stat())==expected else 'metadata_changed'
                except OSError:state='unavailable'
        rows.append({**{key:record.get(key) for key in ('checked_at','status','local_version','latest_version','local_executable')},
                     'historical':True,'executable_state':state,'current_version_verified':False})
    return {'id':identifier,'rows':rows,'network_checked':False,'process_started':False,
            'note':'Resultados históricos de hasta veinte consultas por aplicación. Coincidir en metadatos no equivale a verificar contenido o versión actual; vuelve a comprobar explícitamente el ejecutable si hace falta.'}


def _media_release(token):
    match=re.match(r'n?(\d{1,3})\.(\d{1,3})(?:\.(\d{1,3}))?(?=$|[-+])',token)
    return tuple(int(value or 0) for value in match.groups()) if match else None


def media_versions():
    ffmpeg=compare('ffmpeg',False);ffprobe=compare('ffprobe',False)
    status='media_versions_inconclusive'
    if ffmpeg['status']==ffprobe['status']=='local_version_checked':
        left=ffmpeg['local_version'];right=ffprobe['local_version']
        if left==right:status='version_labels_match'
        elif _media_release(left) is not None and _media_release(right) is not None:
            status='same_release_different_labels' if _media_release(left)==_media_release(right) else 'version_mismatch'
        else:status='build_labels_differ'
    return {'status':status,'applications':[ffmpeg,ffprobe],'network_checked':False,
            'compatibility_verified':False,'configuration_changed':False,'checked_at':studio.now(),
            'note':'Comparación de identificadores de versión locales; una coincidencia no acredita bibliotecas, codecs, filtros, arquitectura ni compatibilidad real. Las diferencias requieren revisión, no provocan instalación ni sustitución automática.'}
