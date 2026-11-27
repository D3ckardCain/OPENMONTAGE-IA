"""Bounded per-cut SDR color; one numeric filter shared by preview/export."""
from copy import deepcopy
import base64
import io
import subprocess
import threading

CONTRACT='clip-sdr-color-v1'
DEFAULT={'bypass':False,'exposure_ev':0.,'contrast':1.,'saturation':1.,'gamma':1.}
COMPARE_LOCK=threading.Lock()


def histogram(png):
    """Exact bins of this small display image, not calibrated HDR scopes."""
    from PIL import Image
    with Image.open(io.BytesIO(png)) as image:
        if image.width>960 or image.height>270 or image.width%2:raise ValueError('Comparación fuera de presupuesto de píxeles')
        image=image.convert('RGB');half=image.width//2;result={}
        for label,box in [('before',(0,0,half,image.height)),('after',(half,0,image.width,image.height))]:
            crop=image.crop(box);channels=crop.histogram();total=crop.width*crop.height
            result[label]={'pixels':total,'rgb_bins_32':{name:[sum(channels[c*256+i:c*256+i+8]) for i in range(0,256,8)] for c,name in enumerate(('red','green','blue'))},
                'channel_at_0':{name:channels[c*256] for c,name in enumerate(('red','green','blue'))},
                'channel_at_255':{name:channels[c*256+255] for c,name in enumerate(('red','green','blue'))}}
        return {'contract':'display-frame-rgb-histogram-v1','range':'8-bit RGB0..255;32bins of8','includes_padding':True,'scope':'Only decoded comparison frame including borders; extremes do not prove clipping; not calibrated luminance/HDR/waveform/vectorscope',**result}


def normalize(value):
    from lib.studio_editor import number
    if not isinstance(value,dict) or set(value)-set(DEFAULT):raise ValueError('Ajustes de color desconocidos')
    result={**DEFAULT,**value}
    if type(result['bypass']) is not bool:raise ValueError('Bypass requiere booleano')
    for key,low,high in [('exposure_ev',-2,2),('contrast',.25,2),('saturation',0,2),('gamma',.5,2)]:result[key]=number(result[key],low,high)
    return result


def effective(value):
    if value is None:return None
    v=normalize(value)
    return None if v['bypass'] or v==DEFAULT else v


def suffix(value,curves=None):
    from lib.studio_color_curves import suffix as curves_suffix
    bypass=normalize(value)['bypass'] if value is not None else False
    tail=curves_suffix(curves,bypass)
    v=effective(value)
    if not v:return tail
    return (f",format=gbrpf32le,exposure=exposure={v['exposure_ev']:.12g}"
            f",format=yuv444p,eq=contrast={v['contrast']:.12g}:saturation={v['saturation']:.12g}:gamma={v['gamma']:.12g}"+tail)


def apply(edl,data):
    if data.get('operation')!='clip_color':return False
    from lib import studio_editor as edit
    item=edit._item(edl['cuts'],data['id'])
    if item.get('locked'):raise edit.Conflict('Clip bloqueado')
    if item.get('kind')=='gap':raise ValueError('Color requiere un clip de vídeo')
    if data['color'] is None:item.pop('color',None)
    else:item['color']=normalize(data['color'])
    return True


def compare(pid,clip_id,clip_seconds):
    """A/B is split from one decoded frame, not two independent seeks."""
    from lib import studio_editor as edit
    from lib.studio_editor_effects import transform_filter
    from lib.media_executables import require_media
    state=edit.state(pid);edl=state['edit_decisions'];clip=edit._item(edl['cuts'],clip_id)
    if clip.get('kind')=='gap':raise ValueError('El intervalo vacío no tiene fotograma')
    seconds=edit.number(clip_seconds,0,(clip['out_seconds']-clip['in_seconds'])/clip['speed']-.001)
    time=clip['in_seconds']+seconds*clip['speed'];path=edit.source(pid,clip['source_id'])
    if clip.get('time_warp'):
        from lib.studio_smooth_clock import forward,inverse
        warp=clip['time_warp'];time=clip['in_seconds']+(inverse(warp['map'],forward(warp['map'],warp['old_start_seconds'])+seconds)-warp['old_start_seconds'])*warp['old_speed']
    color=deepcopy(clip.get('color'));saved=normalize(color or {})
    # Compare a configured effect even when playback/export is bypassed; receipt says so.
    proposed={**saved,'bypass':False};out=edl['output'];w,h=(out['width'],out['height']) if out['ratio']=='custom' else edit.PRESETS[out['ratio']]
    scale=min(480/w,270/h);w=max(2,round(w*scale/2)*2);h=max(2,round(h*scale/2)*2)
    graph=(f'[0:v]{transform_filter(w,h,clip.get("transform"))},setsar=1,split=2[a][b];'
           f'[a]format=yuv444p[before];[b]null{suffix(proposed,clip.get("color_curves"))},format=yuv444p[after];'
           '[before][after]hstack=inputs=2,format=rgb24[out]')
    if not COMPARE_LOCK.acquire(blocking=False):raise edit.Conflict('Comparación ocupada; espera el resultado vigente')
    try:
        result=subprocess.run([str(require_media('ffmpeg')),'-hide_banner','-loglevel','error','-nostdin',
          '-threads','1','-filter_complex_threads','1','-ss',str(time),'-i',str(path),'-filter_complex',graph,
          '-map','[out]','-an','-frames:v','1','-c:v','png','-f','image2pipe','pipe:1'],capture_output=True,timeout=20)
    except subprocess.TimeoutExpired as exc:raise ValueError('Comparación superó20s; no se repite automáticamente') from exc
    finally:COMPARE_LOCK.release()
    if result.returncode or not result.stdout.startswith(b'\x89PNG'):raise ValueError('No se pudo decodificar comparación: '+result.stderr.decode('utf-8',errors='replace')[-600:])
    if edit.state(pid)['edit_sha256']!=state['edit_sha256']:raise edit.Conflict('El montaje cambió; descarta esta comparación')
    return {'contract':CONTRACT,'project_id':pid,'revision':state['revision'],'clip_id':clip_id,
       'source_id':clip['source_id'],'source_sha256':edl['sources'][clip['source_id']]['sha256'],
       'requested_source_seconds':time,'clip_seconds':seconds,'color':proposed,'saved_bypass':saved['bypass'],
       'width':w*2,'height':h,'image_data_url':'data:image/png;base64,'+base64.b64encode(result.stdout).decode('ascii'),
       'histogram':histogram(result.stdout),
       'scope':'One decoded selected-clip frame split before/after; no titles, layers, transitions or audio; requested time is not measured PTS'}
