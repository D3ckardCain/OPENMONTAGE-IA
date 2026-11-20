"""Common media binary lookup using command-center configuration."""


def require_media(name):
    if name not in ('ffmpeg','ffprobe'):raise ValueError('Herramienta multimedia desconocida')
    from lib.reference_analysis import executable
    return executable(name)


def find_media(name):
    try:return require_media(name)
    except (ValueError,OSError):return None
