"""Explicit version probes for configured tools; never invoke self-updaters."""
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from lib import production_studio as studio
from lib import external_applications as applications
from lib import update_center as updates

_COMMANDS={'yt-dlp':['--ignore-config','--no-plugin-dirs','--version'],'deno':['--version']}


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


def compare(identifier,online=True):
    if identifier not in _COMMANDS:raise ValueError('Comprobación disponible solo para yt-dlp y Deno')
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
    output=process.stdout.decode('utf-8',errors='replace').strip()
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
