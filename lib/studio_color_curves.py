"""Explicit bounded PCHIP RGB curves; no LUT files or external profiles."""
IDENTITY=[[0.,0.],[1.,1.]]
CHANNELS=('master','red','green','blue')


def normalize(value):
    from lib.studio_editor import number
    if not isinstance(value,dict) or set(value)!={'interpolation','channels'} or value['interpolation']!='pchip':raise ValueError('Curvas requieren interpolation=pchip y channels')
    channels=value['channels']
    if not isinstance(channels,dict) or not channels or set(channels)-set(CHANNELS):raise ValueError('Canales: master, red, green, blue')
    result={}
    for channel,points in channels.items():
        if not isinstance(points,list) or not 2<=len(points)<=8:raise ValueError('Cada curva requiere2–8 puntos')
        checked=[];previous=-1
        for point in points:
            if not isinstance(point,list) or len(point)!=2:raise ValueError('Punto requiere [entrada,salida]')
            x,y=[number(v,0,1) for v in point]
            if x<=previous:raise ValueError('Entradas de curva estrictamente crecientes')
            checked.append([x,y]);previous=x
        if checked[0][0]!=0 or checked[-1][0]!=1:raise ValueError('Curva debe incluir entrada0 y1')
        if checked!=IDENTITY:result[channel]=checked
    return {'interpolation':'pchip','channels':result}


def effective(value,bypass=False):
    if value is None:return None
    v=normalize(value)
    return v if v['channels'] and not bypass else None


def suffix(value,bypass=False):
    v=effective(value,bypass)
    if not v:return ''
    return ',curves=interp=pchip:'+':'.join(k+"='"+' '.join(f'{x:.12g}/{y:.12g}' for x,y in v['channels'][k])+"'" for k in CHANNELS if k in v['channels'])


def apply(edl,data):
    if data.get('operation')!='clip_color_curves':return False
    from lib import studio_editor as edit
    item=edit._item(edl['cuts'],data['id'])
    if item.get('locked'):raise edit.Conflict('Clip bloqueado')
    if item.get('kind')=='gap':raise ValueError('Curvas requieren clip de vídeo')
    if data['curves'] is None:item.pop('color_curves',None)
    else:
        v=normalize(data['curves'])
        if v['channels']:item['color_curves']=v
        else:item.pop('color_curves',None)
    return True
