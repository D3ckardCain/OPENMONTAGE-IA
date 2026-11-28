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
    if 'points' not in data or set(data)-{'operation','revision','track','points','bypass'}:
        raise ValueError('Indica points explícitamente; usa [] para quitar la automatización')
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


def value_at(points,t):
    if t<=points[0]['seconds']:return points[0]['gain']
    for a,b in zip(points,points[1:]):
        if t<b['seconds']:
            return a['gain']+(b['gain']-a['gain'])*(t-a['seconds'])/(b['seconds']-a['seconds'])
    return points[-1]['gain']


def ripple(edl,removed):
    """Opt-in map of both prepared envelopes, including bypassed ones.

    Remove [a,b), hold the surviving left limit up to one output sample before
    the join and take the original right limit at the join (right wins).
    """
    intervals=[]
    for a,b in sorted(removed):
        if intervals and a<=intervals[-1][1]+1e-12:intervals[-1]=(intervals[-1][0],max(b,intervals[-1][1]))
        else:intervals.append((a,b))
    from lib.studio_timeline_ops import _ripple_time
    sample=1/48000
    for lane,settings in edl.get('volume_automation',{}).items():
        points=normalize(settings)['points']
        if not points:continue
        # Existing points at a are removed; at b survive at the joined time.
        mapped=[{'seconds':_ripple_time(p['seconds'],intervals),'gain':p['gain']} for p in points
                if not any(a<=p['seconds']<b for a,b in intervals)]
        anchors=[]
        for a,b in intervals:
            join=_ripple_time(b,intervals)
            anchors.append({'seconds':join,'gain':value_at(points,b)})
            if join>=sample:
                anchors.append({'seconds':join-sample,'gain':value_at(points,a-sample)})
        # Boundary anchors supersede points closer than one sample. Never
        # silently decimate a long envelope to fit the editor's bounded limit.
        mapped=[p for p in mapped if all(abs(p['seconds']-a['seconds'])>=sample-1e-12 for a in anchors)]
        combined=sorted(mapped+anchors,key=lambda p:p['seconds'])
        result=[]
        for point in combined:
            if result and point['seconds']-result[-1]['seconds']<sample-1e-12:
                result[-1]=point  # Right-most boundary wins in a sub-sample collision.
            else:result.append(point)
        if len(result)>32:
            raise ValueError('Ripple superaría 32 puntos por pista; reduce puntos o conserva tiempos absolutos')
        settings.update(normalize({'points':result,'bypass':settings.get('bypass',False)}))
