"""Read-only readiness checks for sports image/video exports."""
from lib.media_executables import require_media


def png_requirements():
    try:
        from PIL import Image,ImageDraw,ImageFont
    except ImportError:
        return {'available':False,'font':None,'missing':['Pillow no está instalado en el Python de la app.']}
    for candidate in ('DejaVuSans.ttf','arial.ttf'):
        try:
            font=ImageFont.truetype(candidate,24)
            return {'available':True,'font':getattr(font,'path',candidate),'missing':[]}
        except OSError:pass
    return {'available':False,'font':None,'missing':['No se encuentra una fuente TrueType DejaVu Sans o Arial.']}


def video_requirements():
    png=png_requirements();missing=list(png['missing']);executables={}
    for name in ('ffmpeg','ffprobe'):
        try:executables[name]=require_media(name)
        except (ValueError,OSError) as exc:
            executables[name]=None;missing.append(name+': '+str(exc))
    return {'available':not missing,'png':png,'executables':executables,'missing':missing,
            'scope':'Presencia y configuración local; no comprueba todavía el codificador ni ejecuta un render.',
            'downloads_started':False,'models_loaded':False}
