"""Persistent registry of data disks; app and configuration remain on the SSD."""
import json
import os
import shutil
from pathlib import Path


def config_path(repo):return Path(repo)/'.backlot/storage.json'


def read_config(repo):
    path=config_path(repo)
    if not path.is_file():return {'volumes':[],'active_projects_dir':None,'final_outputs_dir':None}
    data=json.loads(path.read_text(encoding='utf-8'))
    if 'projects_dir' in data:
        data={'volumes':[{'name':'Datos','projects_dir':data['projects_dir']}],'active_projects_dir':data['projects_dir']}
    if not isinstance(data.get('volumes'),list) or not isinstance(data.get('active_projects_dir'),str):raise ValueError('Configuración de discos inválida')
    if not Path(data['active_projects_dir']).is_absolute():raise ValueError('La carpeta activa debe ser absoluta')
    data.setdefault('final_outputs_dir',None)
    return data


def configured_projects(repo):
    value=read_config(repo)['active_projects_dir']
    return Path(value) if value else None


def projects_directory(repo):
    override=os.environ.get('OPENMONTAGE_PROJECTS_DIR')
    if override:
        path=Path(override)
        if not path.is_absolute():raise ValueError('OPENMONTAGE_PROJECTS_DIR debe ser una ruta absoluta')
        return path
    return configured_projects(repo) or Path(repo)/'projects'


def describe(repo,active):
    config=read_config(repo);saved=config['active_projects_dir'];active=Path(active)
    volumes=[]
    for volume in config['volumes']:
        path=Path(volume['projects_dir']);available=path.is_dir()
        try:usage=shutil.disk_usage(path) if available else None
        except OSError:usage=None;available=False
        volumes.append({**volume,'available':available,'free_bytes':usage.free if usage else None,
            'total_bytes':usage.total if usage else None,'active_now':path.resolve()==active.resolve()})
    return {'application_dir':str(repo),'active_projects_dir':str(active),
        'configured_projects_dir':saved,'volumes':volumes,
        'final_outputs_dir':config.get('final_outputs_dir'),
        'final_outputs_available':Path(config['final_outputs_dir']).is_dir() if config.get('final_outputs_dir') else None,
        'environment_override':bool(os.environ.get('OPENMONTAGE_PROJECTS_DIR')),
        'restart_required':bool(saved and Path(saved).resolve()!=active.resolve()),
        'available':active.is_dir(),'automatic_migration':False,'simultaneous_project_roots':False}


def readiness(repo,active):
    """Check configured data locations without writing or starting workloads."""
    config=read_config(repo);checks=[];problems=[]
    locations=[('Trabajo',Path(active))]
    if config.get('final_outputs_dir'):locations.append(('Videos finales',Path(config['final_outputs_dir'])))
    for role,path in locations:
        check={'role':role,'path':str(path),'available':path.is_dir(),'free_bytes':None}
        if not check['available']:problems.append(role+': la carpeta o el disco no está disponible')
        else:
            try:
                check['free_bytes']=shutil.disk_usage(path).free
                if check['free_bytes']==0:problems.append(role+': el disco no tiene espacio libre')
            except OSError:problems.append(role+': no se pudo consultar el espacio disponible')
        checks.append(check)
    return {'ready':not problems,'checks':checks,'problems':problems,
        'scope':'storage_only','write_test_performed':False,
        'note':'No estima el tamaño de una producción ni confirma modelos, permisos de escritura o rendimiento.'}


def configure(repo,data,save_json):
    if set(data)-{'volumes','active_projects_dir','final_outputs_dir'} or not {'volumes','active_projects_dir'}<=set(data):raise ValueError('Indica volumes, active_projects_dir y opcionalmente final_outputs_dir')
    volumes=data['volumes'];selected=data['active_projects_dir']
    if not isinstance(volumes,list) or not 1<=len(volumes)<=16:raise ValueError('Registra entre 1 y 16 discos o carpetas de datos')
    normalized=[];paths=set()
    for item in volumes:
        if not isinstance(item,dict) or set(item)!={'name','projects_dir'}:raise ValueError('Ficha de disco inválida')
        name=item['name'];value=item['projects_dir']
        if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ValueError('Indica un nombre de disco de hasta 80 caracteres')
        if not isinstance(value,str) or len(value)>4000 or not Path(value).is_absolute():raise ValueError('Usa una carpeta absoluta por disco')
        key=os.path.normcase(str(Path(value).resolve()))
        if key in paths:raise ValueError('Carpeta de datos repetida')
        paths.add(key);normalized.append({'name':name.strip(),'projects_dir':str(Path(value).resolve())})
    if not isinstance(selected,str) or not Path(selected).is_absolute():raise ValueError('Selecciona un disco activo')
    active=Path(selected).resolve()
    if os.path.normcase(str(active)) not in paths:raise ValueError('El disco activo no está registrado')
    if not active.is_dir():raise ValueError('La carpeta del disco seleccionado no está disponible; conecta el disco antes de seleccionarlo')
    final=data.get('final_outputs_dir') or None
    if final is not None:
        if not isinstance(final,str) or len(final)>4000 or not Path(final).is_absolute() or not Path(final).is_dir():raise ValueError('Elige una carpeta absoluta existente para los videos finales')
        final=str(Path(final).resolve())
    save_json(config_path(repo),{'volumes':normalized,'active_projects_dir':str(active),'final_outputs_dir':final})
    return {'saved':True,'restart_required':True,'files_moved':False,'volumes':len(normalized)}
