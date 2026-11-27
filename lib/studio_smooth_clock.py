"""Continuous source-speed ramps: analytic integral/inverse and FFmpeg expression."""
import math

CONTRACT='continuous-source-speed-linear-v1'


def parts(m):
    points=m['points'];result=[];prefix=0.
    for a,b in zip(points,points[1:]):
        x,y=a['source_seconds'],b['source_seconds'];v=a['speed'];k=(b['speed']-v)/(y-x)
        length=(y-x)/v if abs(k)<1e-12 else math.log1p((b['speed']-v)/v)/k
        result.append((x,y,v,k,prefix,prefix+length));prefix+=length
    return result,prefix


def validate(m):
    from lib.studio_editor import number
    if not isinstance(m,dict) or set(m)!={'contract','points','old_start_seconds','old_duration_seconds','fps','output_frames'} or m['contract']!=CONTRACT:raise ValueError('Mapa suave desconocido')
    if type(m['fps']) is not int or not 1<=m['fps']<=60 or type(m['output_frames']) is not int or not 1<=m['output_frames']<=120*m['fps']:raise ValueError('Rampa: presupuesto120s y FPS entero')
    number(m['old_start_seconds'],0,7200);number(m['old_duration_seconds'],.001,120)
    if not isinstance(m['points'],list) or not 2<=len(m['points'])<=8:raise ValueError('Rampa continua requiere2–8 puntos con ambos extremos')
    previous=-1
    for p in m['points']:
        if not isinstance(p,dict) or set(p)!={'source_seconds','speed'}:raise ValueError('Punto continuo inválido')
        x=number(p['source_seconds'],0,7200);number(p['speed'],.25,4)
        if x-previous<.001:raise ValueError('Puntos continuos crecientes y separados al menos1ms')
        previous=x
    if m['points'][-1]['source_seconds']-m['points'][0]['source_seconds']>30:raise ValueError('Primera entrega: máximo30s de fuente por rampa')
    _,total=parts(m);scale=m['output_frames']/m['fps']/total
    if any(not .25-1e-10<=p['speed']/scale<=4+1e-10 for p in m['points']):raise ValueError('Cuantización desplazaría velocidad fuera0,25–4')
    return m


def scale(m):return m['output_frames']/m['fps']/parts(m)[1]


def forward(m,t):
    start=m['old_start_seconds'];end=start+m['old_duration_seconds'];duration=m['output_frames']/m['fps']
    if t<=start:return t
    if t>=end:return t+duration-m['old_duration_seconds']
    lo=m['points'][0]['source_seconds'];hi=m['points'][-1]['source_seconds'];x=lo+(t-start)*(hi-lo)/m['old_duration_seconds']
    segments,total=parts(m)
    for a,b,v,k,p,q in segments:
        if x<=b:
            elapsed=(x-a)/v if abs(k)<1e-12 else math.log1p(k*(x-a)/v)/k
            return start+(p+elapsed)*duration/total
    return start+duration


def inverse(m,t):
    start=m['old_start_seconds'];duration=m['output_frames']/m['fps'];old=m['old_duration_seconds']
    if t<=start:return t
    if t>=start+duration:return t-duration+old
    segments,total=parts(m);raw=(t-start)*total/duration
    for a,b,v,k,p,q in segments:
        if raw<=q:
            x=a+(raw-p)*v if abs(k)<1e-12 else a+v*math.expm1(k*(raw-p))/k
            lo=m['points'][0]['source_seconds'];hi=m['points'][-1]['source_seconds']
            return start+(x-lo)*old/(hi-lo)
    return start+old


def inverse_array(m,t):
    import numpy as np
    start=m['old_start_seconds'];duration=m['output_frames']/m['fps'];old=m['old_duration_seconds'];segments,total=parts(m)
    values=np.asarray(t,dtype='float64');result=values.copy();after=values>=start+duration;result[after]=values[after]-duration+old
    raw=(values-start)*total/duration;lo=m['points'][0]['source_seconds'];hi=m['points'][-1]['source_seconds']
    for a,b,v,k,p,q in segments:
        mask=(values>start)&(values<start+duration)&(raw>=p)&(raw<=q)
        x=a+(raw[mask]-p)*v if abs(k)<1e-12 else a+v*np.expm1(k*(raw[mask]-p))/k
        result[mask]=start+(x-lo)*old/(hi-lo)
    return result


def item_seconds(clip):
    w=clip.get('time_warp')
    if not w:return (clip['out_seconds']-clip['in_seconds'])/clip['speed']
    old=w['old_start_seconds'];end=old+(clip['out_seconds']-clip['in_seconds'])/w['old_speed']
    return forward(w['map'],end)-forward(w['map'],old)


def source_offset(clip,source_time):
    w=clip['time_warp'];old=w['old_start_seconds']
    if source_time<=clip['in_seconds']:return 0.
    if source_time>=clip['out_seconds']:return item_seconds(clip)
    return forward(w['map'],old+(source_time-clip['in_seconds'])/w['old_speed'])-forward(w['map'],old)


def expression(m,t):
    start=m['old_start_seconds'];old=m['old_duration_seconds'];duration=m['output_frames']/m['fps'];lo=m['points'][0]['source_seconds'];hi=m['points'][-1]['source_seconds']
    x=f'({lo:.17g}+(({t})-{start:.17g})*{(hi-lo)/old:.17g})';segments,total=parts(m);expr=f'{duration:.17g}'
    for a,b,v,k,p,q in reversed(segments):
        piece=f'(({x}-{a:.17g})/{v:.17g})' if abs(k)<1e-12 else f'(log(max(1e-12,1+{k/v:.17g}*({x}-{a:.17g})))/{k:.17g})'
        value=f'(({p:.17g}+{piece})*{duration/total:.17g})';expr=f'if(lte({x},{b:.17g}),{value},{expr})'
    return f'if(lte(({t}),{start:.17g}),({t}),if(gte(({t}),{start+old:.17g}),({t})+{duration-old:.17g},{start:.17g}+{expr}))'


def video_pts(clip,absolute=False):
    w=clip.get('time_warp')
    if not w:return f'(PTS-STARTPTS)/{clip["speed"]}'+(f'+{clip["start_seconds"]}/TB' if absolute else '')
    t=f'({w["old_start_seconds"]:.17g}+(PTS-STARTPTS)*TB/{w["old_speed"]:.17g})'
    value=expression(w['map'],t)
    if not absolute:value=f'({value}-{forward(w["map"],w["old_start_seconds"]):.17g})'
    return "'("+value+")/TB'"
