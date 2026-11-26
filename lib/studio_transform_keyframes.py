"""Deterministic source-clock curves and bounded FFmpeg frame commands."""
import bisect
import math

FIELDS = {'scale': (.05, 4), 'rotation': (-3600, 3600), 'opacity': (0, 1)}
INTERPOLATIONS = ('linear', 'hold', 'smooth', 'bezier')


def controls(point):
    mode = point.get('interpolation')
    if mode not in INTERPOLATIONS:
        raise ValueError('Interpolación: linear, hold, smooth o bezier')
    if mode != 'bezier':
        if 'control_points' in point:
            raise ValueError('Los controles Bézier requieren interpolación bezier')
        return
    values = point.get('control_points')
    if not isinstance(values, list) or len(values) != 4 or any(
        type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in values
    ):
        raise ValueError('Bézier requiere control_points [x1,y1,x2,y2], valores finitos0–1')


def validate(value, source_duration):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {'clock', 'curves'} or value['clock'] != 'source_seconds':
        raise ValueError('Curvas: reloj source_seconds y curves requeridos')
    curves = value['curves']
    if not isinstance(curves, dict) or not curves or set(curves)-set(FIELDS):
        raise ValueError('Curvas disponibles: scale, rotation, opacity')
    result = {}
    for field, points in curves.items():
        if not isinstance(points, list) or not 2 <= len(points) <= 32:
            raise ValueError('Cada curva requiere de2 a32 puntos')
        low, high = FIELDS[field]
        previous = -1
        for point in points:
            if not isinstance(point, dict) or set(point)-{'seconds','value','interpolation','control_points'} or not {'seconds','value','interpolation'} <= set(point):
                raise ValueError('Punto de curva requiere seconds, value e interpolation')
            seconds, number = point['seconds'], point['value']
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in (seconds, number)):
                raise ValueError('Las curvas requieren números finitos')
            if not previous < seconds <= source_duration or seconds < 0:
                raise ValueError('Tiempos de fuente crecientes y dentro del medio')
            if not low <= number <= high:
                raise ValueError(f'{field}: intervalo permitido {low}–{high}')
            controls(point)
            previous = seconds
        result[field] = points
    return {'clock':'source_seconds', 'curves':result}


def progress(point, amount):
    p = max(0, min(1, amount))
    mode = point['interpolation']
    if mode == 'hold':
        return 1. if p >= 1 else 0.
    if mode == 'smooth':
        return p*p*(3-2*p)
    if mode == 'bezier':
        if p in (0, 1):
            return float(p)
        x1,y1,x2,y2 = point['control_points']
        low,high = 0.,1.
        for _ in range(24):
            t = (low+high)/2
            x = 3*(1-t)**2*t*x1+3*(1-t)*t*t*x2+t**3
            if x < p:low = t
            else:high = t
        t = (low+high)/2
        return 3*(1-t)**2*t*y1+3*(1-t)*t*t*y2+t**3
    return p


def evaluate(points, axis, seconds):
    index = bisect.bisect_right([p['seconds'] for p in points], seconds)
    if index == 0:return points[0][axis]
    if index == len(points):return points[-1][axis]
    a,b = points[index-1:index+1]
    p = progress(a,(seconds-a['seconds'])/(b['seconds']-a['seconds']))
    return a[axis]+(b[axis]-a[axis])*p


def enhanced(layer):
    return bool(layer.get('transform_keyframes') or any(p['interpolation']=='bezier' for p in layer.get('position_keyframes',{}).get('points',[])))


def sample(layer, timeline_seconds):
    clock = layer['in_seconds']+(timeline_seconds-layer['start_seconds'])*layer['speed']
    result = dict(x=layer['x'],y=layer['y'],scale=1.,rotation=0.,opacity=layer['opacity'])
    if layer.get('position_keyframes'):
        for field in ('x','y'):result[field] = evaluate(layer['position_keyframes']['points'],field,clock)
    elif layer.get('motion'):
        motion = layer['motion'];p = max(0,min(1,(timeline_seconds-layer['start_seconds']+motion.get('phase_seconds',0))/motion['duration_seconds']))
        result.update(x=layer['x']+motion['dx']*p,y=layer['y']+motion['dy']*p)
    for field,points in layer.get('transform_keyframes',{}).get('curves',{}).items():
        result[field] = evaluate(points,'value',clock)
    return result


def dimensions(layer, width, height):
    w,h = max(2,round(width*layer['width']/2)*2),max(2,round(height*layer['height']/2)*2)
    points = layer.get('transform_keyframes',{}).get('curves',{}).get('scale',[])
    maximum = max([1.]+[p['value'] for p in points])
    diagonal = math.ceil(math.hypot(w,h)*maximum/2)*2
    return w,h,diagonal,diagonal


def validate_budget(edl):
    from lib.studio_editor import PRESETS
    out=edl['output'];width,height=(out['width'],out['height']) if out.get('ratio')=='custom' else PRESETS[out['ratio']]
    pixels=sum(dimensions(layer,width,height)[2]**2 for layer in edl.get('layers',[]) if enhanced(layer))
    if pixels>32*1024**2:
        raise ValueError('Capas animadas: límite local32MP de lienzos intermedios; reduce escala, tamaño o salida')


def commands(layer, width, height, index, timeline_seconds):
    w,h,bw,bh = dimensions(layer,width,height);value = sample(layer,timeline_seconds)
    return {f'scale@kfscale{index} w':max(2,round(w*value['scale']/2)*2),
            f'scale@kfscale{index} h':max(2,round(h*value['scale']/2)*2),
            f'rotate@kfrotate{index} angle':value['rotation']*math.pi/180,
            f'colorchannelmixer@kfalpha{index} aa':value['opacity'],
            f'overlay@kfoverlay{index} x':width*value['x']+w/2-bw/2,
            f'overlay@kfoverlay{index} y':height*value['y']+h/2-bh/2}


def filters(layer, width, height, fps, index):
    w,h,bw,bh = dimensions(layer,width,height);first = sample(layer,math.floor(layer['start_seconds']*fps+.5)/fps)
    sw,sh = max(2,round(w*first['scale']/2)*2),max(2,round(h*first['scale']/2)*2)
    chain = (f",format=rgba,sendcmd=f=keyframes-layer{index}.txt,scale@kfscale{index}=w={sw}:h={sh}:eval=frame,"
             f"setsar=1,pad={bw}:{bh}:(ow-iw)/2:(oh-ih)/2:color=0x00000000:eval=frame,"
             f"rotate@kfrotate{index}=angle={first['rotation']*math.pi/180}:ow={bw}:oh={bh}:fillcolor=none,"
             f"colorchannelmixer@kfalpha{index}=aa={first['opacity']}")
    x,y = width*first['x']+w/2-bw/2,height*first['y']+h/2-bh/2
    return chain,f'overlay@kfoverlay{index}=x={x}:y={y}'


def write_commands(work, layer, width, height, fps, index, control=None):
    """Small derived ASCII files, relative to the owned render directory."""
    end = layer['start_seconds']+(layer['out_seconds']-layer['in_seconds'])/layer['speed']
    first = max(0,math.floor(layer['start_seconds']*fps+.5))
    last = math.ceil(end*fps)
    previous = {}
    path = work/f'keyframes-layer{index}.txt'
    with path.open('x',encoding='ascii') as stream:
        for frame in range(first,last):
            if control and frame%64==0:control.check()
            values = commands(layer,width,height,index,frame/fps)
            changed = {k:f'{v:.9f}' for k,v in values.items() if f'{v:.9f}'!=previous.get(k)}
            if changed:
                stamp = max(0,frame/fps-1e-7)
                stream.write(f'{stamp:.9f} [enter] '+','.join(f'{key} {value}' for key,value in changed.items())+';\n')
                previous.update(changed)
    return path
