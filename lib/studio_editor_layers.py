"""Small, real FFmpeg composition primitives for the revisioned manual EDL."""
import uuid


def apply_composition(edl, data):
    from lib import studio_editor as edit
    op=data.get('operation')
    if op=='transition':
        item=edit._item(edl['cuts'],data['id']);index=edl['cuts'].index(item)
        if index==0:raise ValueError('La transición requiere un corte anterior')
        if item.get('locked') or edl['cuts'][index-1].get('locked'):
            raise edit.Conflict('La transición afecta un clip bloqueado')
        kind=data.get('type','dip_black')
        if kind=='none':item.pop('transition',None)
        elif kind=='dip_black':
            fps=edl['output']['fps'];seconds=edit.number(data['duration_seconds'],1/fps,2)
            seconds=int(seconds*fps+.5)/fps
            item['transition']={'type':kind,'duration_seconds':seconds}
        else:raise ValueError('Solo disponible: paso por negro sin solapamiento')
    elif op in ('layer_add','layer_update','layer_remove','layer_move'):
        layers=edl.setdefault('layers',[])
        if op=='layer_remove':layers.remove(edit._item(layers,data['id']))
        elif op=='layer_move':
            item=edit._item(layers,data['id']);index=data['index']
            if type(index) is not int or not 0<=index<len(layers):raise ValueError('Orden de capa fuera de límites')
            layers.insert(index,layers.pop(layers.index(item)))
        else:
            old={} if op=='layer_add' else edit._item(layers,data['id'])
            value={**old,**{k:data[k] for k in ('source_id','in_seconds','out_seconds','start_seconds','speed','x','y','width','height','opacity') if k in data}}
            source=edl['sources'][value['source_id']]
            if source['kind']!='video':raise ValueError('Capa visual requiere una fuente de vídeo registrada')
            value['source']=source['path']
            value['in_seconds']=edit.number(value.get('in_seconds',0))
            value['out_seconds']=edit.number(value.get('out_seconds',source['duration']),value['in_seconds']+.001,source['duration'])
            value['start_seconds']=edit.number(value.get('start_seconds',0))
            value['speed']=edit.number(value.get('speed',1),.25,4)
            for k,default,low in [('x',.65,0),('y',.05,0),('width',.3,.05),('height',.3,.05),('opacity',1,0)]:
                value[k]=edit.number(value.get(k,default),low,1)
            if value['x']+value['width']>1.000001 or value['y']+value['height']>1.000001:
                raise ValueError('La capa debe quedar dentro del lienzo')
            if op=='layer_add':
                if len(layers)>=4:raise ValueError('Límite de esta entrega:4 capas visuales')
                layers.append({**value,'id':uuid.uuid4().hex})
            else:old.update(value)
    else:return False
    return True


def validate_composition(edl):
    from lib import studio_editor as edit
    fps=edl['output']['fps'];cuts=edl['cuts']
    for index,item in enumerate(cuts):
        incoming=item.get('transition',{}).get('duration_seconds',0)
        outgoing=cuts[index+1].get('transition',{}).get('duration_seconds',0) if index+1<len(cuts) else 0
        if index==0 and incoming:raise ValueError('Quita la transición del primer clip antes de reordenar/borrar')
        if incoming+outgoing>edit.frames(item,fps)/fps+1e-8:
            raise ValueError('Las transiciones exceden la duración del clip; acórtalas o quítalas primero')
    for layer in edl.get('layers',[]):
        seconds=(layer['out_seconds']-layer['in_seconds'])/layer['speed']
        if seconds<1/fps or layer['start_seconds']+seconds>edit.duration(edl)+.001:
            raise ValueError('La capa debe caber en la duración del montaje; ajusta su intervalo primero')


def transition_filters(cuts,index,seconds):
    incoming=cuts[index].get('transition',{}).get('duration_seconds',0)
    outgoing=cuts[index+1].get('transition',{}).get('duration_seconds',0) if index+1<len(cuts) else 0
    video=audio=''
    for name,start,duration in [('in',0,incoming),('out',seconds-outgoing,outgoing)]:
        if duration:
            video+=f',fade=t={name}:st={start}:d={duration}:color=black'
            audio+=f',afade=t={name}:st={start}:d={duration}'
    return video,audio
