"""Named Blender bindings shared by Studio and tools; no automatic migration."""
import os
import re
from pathlib import Path
from lib import production_studio as studio


def _path():
    return studio.CONFIG_DIR/'blender_profiles.json'


def _validate(identifier, value):
    if not isinstance(identifier,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{0,63}',identifier):
        raise ValueError('Identificador de perfil Blender inválido')
    if not isinstance(value,dict) or set(value)!={'label','executable','version','user_resources'}:
        raise ValueError('Perfil Blender requiere label/executable/version/user_resources')
    if not isinstance(value['label'],str) or not 1<=len(value['label'])<=120:
        raise ValueError('Nombre de perfil Blender inválido')
    if not isinstance(value['version'],str) or not re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,3}',value['version']):
        raise ValueError('Versión de perfil Blender inválida')
    executable=value['executable']
    if not isinstance(executable,str) or not Path(executable).is_absolute() or Path(executable).name.casefold() not in ('blender.exe','blender'):
        raise ValueError('Ejecutable de perfil Blender inválido')
    resources=value['user_resources']
    if resources is not None and (not isinstance(resources,str) or not Path(resources).is_absolute()):
        raise ValueError('Directorio de preferencias Blender inválido')
    if value['version'].split('.')[0]=='5' and resources is None:
        raise ValueError('Blender 5 requiere preferencias aisladas en su perfil')
    return value


def registered():
    path=_path()
    if not path.exists():return {}
    if path.is_symlink() or path.stat().st_size>64000:raise ValueError('Registro de perfiles Blender inválido')
    data=studio.read_json(path,None)
    if not isinstance(data,dict) or set(data)!={'schema_version','profiles'} or data['schema_version']!=1 or not isinstance(data['profiles'],dict) or len(data['profiles'])>16:
        raise ValueError('Registro de perfiles Blender inválido')
    return {key:_validate(key,value) for key,value in data['profiles'].items()}


def register(identifier,value):
    value=_validate(identifier,value)
    if not Path(value['executable']).is_file():raise ValueError('Ejecutable Blender no disponible')
    if value['user_resources'] is not None and not Path(value['user_resources']).is_dir():
        raise ValueError('Perfil aislado Blender no disponible')
    with studio.LOCK:
        rows=registered()
        if any(key!=identifier and Path(row['executable']).resolve()==Path(value['executable']).resolve() for key,row in rows.items()):
            raise ValueError('Ese ejecutable ya tiene un perfil Blender')
        rows[identifier]=dict(value)
        if len(rows)>16:raise ValueError('Límite de perfiles Blender')
        studio.save_json(_path(),{'schema_version':1,'profiles':rows})
    return {'saved':True,'launched':False,'profile_id':identifier}


def catalog():
    from lib.external_applications import configuration
    configured=configuration().get('blender',{}).get('executable','')
    return [{'id':key,**row,'selected':bool(configured and Path(configured)==Path(row['executable'])),
             'file_found':Path(row['executable']).is_file(),
             'profile_available':row['user_resources'] is None or Path(row['user_resources']).is_dir(),
             'isolation':'dedicated_user_resources' if row['user_resources'] else 'existing_user_preferences'}
            for key,row in registered().items()]


def resolve(profile_id=None):
    from lib.external_applications import configuration
    rows=registered()
    if profile_id is not None:
        if not isinstance(profile_id,str) or profile_id not in rows:raise ValueError('Perfil Blender desconocido; no se usa otra versión')
        return dict(id=profile_id,**rows[profile_id])
    configured=configuration().get('blender',{}).get('executable','')
    found=next((dict(id=key,**row) for key,row in rows.items() if configured and Path(configured)==Path(row['executable'])),None)
    if rows and not found:raise ValueError('La ruta Blender activa no corresponde a un perfil registrado; selecciona explícitamente una versión')
    return found


def environment(profile):
    env=dict(os.environ)
    if profile and profile.get('user_resources'):
        resources=Path(profile['user_resources'])
        if not resources.is_dir():raise ValueError('Perfil Blender aislado no disponible; no se usan preferencias globales')
        env={key:value for key,value in env.items() if not key.upper().startswith(('BLENDER_USER_','BLENDER_SYSTEM_')) and key.upper() not in ('PYTHONPATH','PYTHONHOME')}
        env['BLENDER_USER_RESOURCES']=str(resources)
        env['PYTHONNOUSERSITE']='1'
        temporary=resources/'temp'
        temporary.mkdir(exist_ok=True)
        env['TEMP']=env['TMP']=str(temporary)
    return env


def select(profile_id):
    from lib.external_applications import configure
    profile=resolve(profile_id)
    environment(profile)  # Refuse absent isolation before changing the active binding.
    result=configure('blender',{'executable':profile['executable']})
    return {**result,'profile_id':profile_id,'version':profile['version']}
