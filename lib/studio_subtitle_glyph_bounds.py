"""Measure one burned subtitle cue's actual local FFmpeg/libass pixel bounds."""
import hashlib
import subprocess
import tempfile
from pathlib import Path

from lib.media_executables import require_media

PIXEL_THRESHOLD = 32
MAX_DIMENSION = 8192
MAX_PIXELS = 16_777_216
MAX_CUE_CHARS = 2000


def _dimensions(edl):
    from lib.studio_editor import PRESETS
    output = edl.get('output')
    if not isinstance(output, dict):
        raise ValueError('Falta el formato de salida del montaje')
    if output.get('ratio') == 'custom':
        width, height = output.get('width'), output.get('height')
    else:
        try:
            width, height = PRESETS[output.get('ratio')]
        except (KeyError, TypeError):
            raise ValueError('Formato de salida no compatible con la medición') from None
    if type(width) is not int or type(height) is not int or width < 128 or height < 128:
        raise ValueError('Resolución de salida inválida para medir subtítulos')
    if width > MAX_DIMENSION or height > MAX_DIMENSION or width * height > MAX_PIXELS:
        raise ValueError('La resolución supera el límite de medición segura')
    return width, height


def measure(edl, cue_index):
    if type(cue_index) is not int or cue_index < 0:
        raise ValueError('Índice de subtítulo inválido')
    style = edl.get('subtitle_style')
    if not isinstance(style, dict) or style.get('mode') != 'burn':
        raise ValueError('La caja de glifos solo se mide para subtítulos quemados')
    cues = edl.get('cues')
    if not isinstance(cues, list) or cue_index >= len(cues):
        raise ValueError('No existe ese bloque de subtítulo')
    cue = cues[cue_index]
    text = cue.get('text') if isinstance(cue, dict) else None
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_CUE_CHARS:
        raise ValueError('El bloque no tiene texto medible o supera el límite de 2000 caracteres')
    width, height = _dimensions(edl)
    from lib.studio_subtitle_layout import normalize
    policy = normalize(edl.get('subtitle_layout', {}))
    from lib.scene_burned_subtitles import _ass
    script = _ass([{'start_seconds':0.0,'end_seconds':1.0,'text':text}],
                  width,height,style,policy['safe_area'])
    raw = b''
    error = ''
    try:
        with tempfile.TemporaryDirectory(prefix='om-subtitle-glyph-') as folder:
            Path(folder,'cue.ass').write_text(script,encoding='utf-8')
            result = subprocess.run(
                [require_media('ffmpeg'),'-nostdin','-v','error','-f','lavfi','-i',
                 f'color=c=black:s={width}x{height}:r=1:d=1','-vf','ass=cue.ass,format=gray',
                 '-frames:v','1','-pix_fmt','gray','-f','rawvideo','pipe:1'],
                cwd=folder,capture_output=True,timeout=20)
            if result.returncode:
                error=result.stderr.decode('utf-8',errors='replace')[-600:]
            else:
                raw=result.stdout
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError('FFmpeg local no pudo medir los glifos: '+str(exc)[:240]) from exc
    if error:
        raise ValueError('FFmpeg local no pudo medir los glifos: '+error)
    if len(raw)!=width*height:
        raise ValueError('FFmpeg devolvió un fotograma incompleto para la medición')
    left,top,right,bottom=width,height,-1,-1
    for offset,pixel in enumerate(raw):
        if pixel<=PIXEL_THRESHOLD:continue
        x,y=offset%width,offset//width
        left,top=min(left,x),min(top,y)
        right,bottom=max(right,x),max(bottom,y)
    digest=hashlib.sha256(script.encode('utf-8')).hexdigest()
    if right<0:
        return {'status':'no_glyph_pixels','bbox':None,'safe_rect':None,
                'fits_safe_area':None,'width':width,'height':height,
                'pixel_threshold':PIXEL_THRESHOLD,'ass_sha256':digest,
                'scope':'Píxeles de un cue sintético sobre fondo negro; sin vídeo real ni persistencia'}
    safe=policy['safe_area']
    safe_rect=[round(width*safe['left']),round(height*safe['top']),
               width-round(width*safe['right']),height-round(height*safe['bottom'])]
    bbox=[left,top,right+1,bottom+1]
    fits=(bbox[0]>=safe_rect[0] and bbox[1]>=safe_rect[1] and
          bbox[2]<=safe_rect[2] and bbox[3]<=safe_rect[3])
    return {'status':'measured','bbox':bbox,'safe_rect':safe_rect,
            'fits_safe_area':fits,'width':width,'height':height,
            'pixel_threshold':PIXEL_THRESHOLD,'ass_sha256':digest,
            'scope':'Píxeles de un cue sintético sobre fondo negro; sin vídeo real ni persistencia'}


def project_measure(project_id,cue_index):
    from lib import studio_editor as editor
    state=editor.state(project_id)
    return {'project_id':project_id,'revision':state['revision'],
            'cue_index':cue_index,**measure(state['edit_decisions'],cue_index)}
