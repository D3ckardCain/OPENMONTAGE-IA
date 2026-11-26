"""Small own presets expanded into the existing editable titles/layers, not another timeline."""
import textwrap
import uuid
from lib import studio_editor as editor

RENDER_CONTRACT = 'editable-components-v1-mobile-safe'

SAFE = {'youtube':(.08,.08,.12,.12),'tiktok':(.08,.18,.14,.23),
        'instagram':(.08,.15,.14,.23),'facebook':(.08,.15,.14,.23),'local':(.08,.08,.12,.12)}


def apply(edl,data):
    op=data.get('operation')
    if op=='component_remove':
        group=data['id'];items=[c for key in ('titles','layers') for c in edl.get(key,[]) if c.get('component_id')==group]
        if not items:raise ValueError('Componente no encontrado')
        if any(c.get('locked') for c in items):raise editor.Conflict('Componente contiene elementos bloqueados')
        for key in ('titles','layers'):edl[key]=[c for c in edl.get(key,[]) if c.get('component_id')!=group]
        return
    kind=data['kind']
    if kind not in ('evidence_card','comparison','collage'):raise ValueError('Componente no disponible')
    start=editor.number(data['start_seconds']);end=editor.number(data['end_seconds'],start,7200)
    if end-start<1/edl['output']['fps']:raise ValueError('Componente requiere al menos un fotograma')
    platform=data.get('platform','local')
    if platform not in SAFE:raise ValueError('Perfil de zona segura desconocido')
    source_label=data.get('source_label','')
    source_url=data.get('source_url','')
    if not isinstance(source_label,str) or not source_label.strip() or len(source_label)>40:raise ValueError('Conserva una etiqueta de fuente1–40caracteres')
    if not isinstance(source_url,str) or len(source_url)>1000:raise ValueError('Referencia de fuente inválida')
    group=uuid.uuid4().hex;left,right,top,bottom=SAFE[platform];center=(left+1-right)/2
    origin=dict(kind=kind,source_label=source_label,source_url=source_url,
                rights=data.get('rights','not_verified'),safe_platform=platform,
                safe_insets=[left,right,top,bottom],scope='snapshot_at_creation_not_verified_fact_or_platform_guarantee')
    def title(text,x,position='center',columns=20):
        if not isinstance(text,str) or not text.strip() or len(text)>120:raise ValueError('Texto de componente1–120caracteres')
        wrapped='\n'.join('\n'.join(textwrap.wrap(line,columns)) for line in text.splitlines())
        editor._apply_edit(edl,dict(operation='title_add',text=wrapped,
            start_seconds=start,end_seconds=end,size=56,position=position))
        item=edl['titles'][-1];item.update(component_id=group,component_origin=dict(origin),
            component_layout=dict(anchor_x=x,top=top,bottom=bottom))
    if not edl['cuts']:
        if start!=0:raise ValueError('Un lienzo inicial requiere inicio0')
        edl['cuts']=[dict(id=uuid.uuid4().hex,kind='gap',source_id=None,source=None,
            in_seconds=0,out_seconds=end,gap_duration=end,speed=1,muted=True,gain=0,
            fade_in=0,fade_out=0,start_seconds=0)]
        edl['output']['background']='#0d1117'
    if end>editor.duration(edl)+1e-9:raise ValueError('El componente debe caber en el montaje')
    if kind=='evidence_card':
        if not isinstance(data['text'],str) or len(data['text'])>48:raise ValueError('Tarjeta breve: hasta48caracteres de contenido')
        title(data['text']+'\nFuente: '+source_label,center,'top',24)
    elif kind=='comparison':
        span=(1-left-right)/2
        if any(not isinstance(data[k],str) or len(data[k])>40 for k in ('left_text','right_text')):raise ValueError('Comparativa: hasta40caracteres por lado')
        title(data['left_text'],left+span/2,'center',10)
        title(data['right_text'],left+span*1.5,'center',10)
    else:
        source_ids=data.get('source_ids')
        if not isinstance(source_ids,list) or not 1<=len(source_ids)<=2:raise ValueError('Collage usa1–2vídeos propios/autorizados registrados')
        # Solid clean background, not a blurred poster containing the same subjects.
        if any(c.get('kind')!='gap' for c in edl['cuts']):raise ValueError('Preset collage requiere fondo limpio de intervalos vacíos; no fabrica una máscara ni elimina sujetos')
        for i,source_id in enumerate(source_ids):
            source=edl['sources'][source_id];seconds=min(end-start,source['duration'])
            editor._apply_edit(edl,dict(operation='layer_add',source_id=source_id,in_seconds=0,out_seconds=seconds,
                start_seconds=start,speed=1,x=left+i*.38,y=top+.12,width=.32,height=.32,opacity=1,fit='crop',
                motion=dict(dx=.02,dy=.02,duration_seconds=end-start,phase_seconds=0)))
            edl['layers'][-1].update(component_id=group,component_origin=dict(origin))
        if not isinstance(data['text'],str) or len(data['text'])>48:raise ValueError('Título de collage: hasta48caracteres')
        title(data['text'],center,'bottom',24)


def title_ass(title,width,height):
    from lib.scene_burned_subtitles import _ass
    layout=title['component_layout']
    y={'top':layout['top']+.13,'center':.5,'bottom':1-layout['bottom']-.08}[title['position']]
    line_count=max(1,len(title['text'].splitlines()))
    vertical_room=2*min(y-layout['top'],1-layout['bottom']-y)*height
    font_pixels=min(title['size']*width/1440,vertical_room/(1.25*line_count))
    style={**title,'size':max(1,font_pixels)*1080/height}
    text=_ass([title],width,height,style)
    lines=text.splitlines()
    # ASS opaque text box on the existing renderer; no browser/CDN/resources.
    for i,line in enumerate(lines):
        if line.startswith('Style: '):
            fields=line.split(',');fields[5]='&H0017110D';fields[15]='3';fields[16]='6';fields[17]='0';fields[18]='5';lines[i]=','.join(fields)
        elif line.startswith('Dialogue: '):
            fields=line.split(',',9)
            y={'top':layout['top']+.13,'center':.5,'bottom':1-layout['bottom']-.08}[title['position']]
            fields[9]='{\\an5\\pos('+str(round(width*layout['anchor_x']))+','+str(round(height*y))+')}'+fields[9]
            lines[i]=','.join(fields)
    return '\n'.join(lines)+'\n'
