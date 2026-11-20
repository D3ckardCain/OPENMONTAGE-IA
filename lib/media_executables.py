"""Common media binary lookup using command-center configuration."""


def require_media(name):
    if name not in ('ffmpeg','ffprobe'):raise ValueError('Herramienta multimedia desconocida')
    from lib.reference_analysis import executable
    return executable(name)


def find_media(name):
    try:return require_media(name)
    except (ValueError,OSError):return None


def media_environment(base_env=None):
    """Expose media binaries to child processes without modifying system PATH."""
    import os
    from pathlib import Path
    from lib import production_studio as studio
    settings=studio.settings();folders=[]
    for name in ('ffmpeg','ffprobe'):
        path=require_media(name) if settings.get(name+'_path') else find_media(name)
        if path:
            folder=str(Path(path).resolve().parent)
            if folder not in folders:folders.append(folder)
    env=dict(os.environ)
    if base_env:env.update(base_env)
    if folders:env['PATH']=os.pathsep.join([*folders,env.get('PATH','')])
    return env
