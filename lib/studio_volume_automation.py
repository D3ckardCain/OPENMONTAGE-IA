"""Linear gain envelopes on absolute montage time, shared by both lanes."""
from copy import deepcopy

RENDER_CONTRACT = 'track-volume-linear-sample-v1'


def normalize(value):
    from lib.studio_editor import number
    if not isinstance(value,dict) or set(value)-{'points','bypass'} or type(value.get('bypass',False)) is not bool:
        raise ValueError('Automatización: puntos y bypass booleano exclusivamente')
    points=value.get('points',[])
    if not isinstance(points,list) or len(points)>32:
        raise ValueError('Máximo 32 puntos por pista')
    result=[]
    for point in points:
        if not isinstance(point,dict) or set(point)!={'seconds','gain'}:
            raise ValueError('Cada punto requiere seconds y gain')
        item={'seconds':number(point['seconds'],0,7200),'gain':number(point['gain'],0,4)}
        if result and item['seconds']-result[-1]['seconds']<1/48000-1e-12:
            raise ValueError('Puntos ordenados, separados al menos una muestra a 48 kHz')
        result.append(item)
    return {'points':result,'bypass':value.get('bypass',False)}


def apply(edl,data):
    if data.get('operation')!='track_volume_points':return False
    lane=data.get('track')
    if lane not in ('video','audio'):raise ValueError('Pista de automatización desconocida')
    value=normalize({k:data[k] for k in ('points','bypass') if k in data})
    lanes=edl.setdefault('volume_automation',{})
    if value['points']:lanes[lane]=deepcopy(value)
    else:lanes.pop(lane,None)
    if not lanes:edl.pop('volume_automation',None)
    return True


def validate(edl):
    values=edl.get('volume_automation',{})
    if not isinstance(values,dict) or set(values)-{'video','audio'}:
        raise ValueError('Pistas de automatización desconocidas')
    for value in values.values():normalize(value)


def effective(edl,lane):
    value=normalize(edl.get('volume_automation',{}).get(lane,{}))
    from lib.studio_track_mixer import gain
    if value['bypass'] or gain(edl,lane)==0 or not value['points'] or all(p['gain']==1 for p in value['points']):return None
    return value['points']


def expression(points):
    # Hold first/last; linear amplitude, not logarithmic dB. No user expressions.
    result=f"{points[-1]['gain']:.12g}"
    for a,b in reversed(list(zip(points,points[1:]))):
        slope=(b['gain']-a['gain'])/(b['seconds']-a['seconds'])
        line=f"({a['gain']:.12g}+{slope:.12g}*(t-{a['seconds']:.12g}))"
        result=f"if(lt(t,{b['seconds']:.12g}),{line},{result})"
    return f"if(lt(t,{points[0]['seconds']:.12g}),{points[0]['gain']:.12g},{result})"


def suffix(edl,lane):
    points=effective(edl,lane)
    if not points:return ''
    expr=expression(points)
    return f",aeval=exprs='val(0)*({expr})|val(1)*({expr})':c=stereo,aformat=sample_fmts=fltp:channel_layouts=stereo"
