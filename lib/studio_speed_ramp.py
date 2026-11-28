"""Reviewed stepped speed envelope, with one shared invertible timeline map."""
from copy import deepcopy
from collections import Counter
import uuid
import math
from fractions import Fraction

CONTRACT='speed-source-knots-hold-v1'


def propose(edl,clip_id,points,follow_volume=False):
    from lib import studio_editor as edit
    from lib.studio_word_clock import inspect
    from lib.studio_audio_processing import effective
    if type(follow_volume) is not bool:raise ValueError('follow_volume requiere booleano')
    clip=edit._item(edl['cuts'],clip_id);fps=edl['output']['fps']
    if clip.get('kind')=='gap' or clip.get('locked'):raise ValueError('Selecciona vídeo desbloqueado')
    if any(c.get('transition',{}).get('type')=='crossfade' for c in edl['cuts']):raise ValueError('Curva escalonada aún no admite crossfade; no se modifica el montaje')
    if clip.get('fade_in',0) or clip.get('fade_out',0):raise ValueError('Revisa/quita fundidos del clip antes de dividir su velocidad')
    if (effective(clip.get('audio_processing')) or {}).get('compressor',{}).get('enabled'):raise ValueError('Compresor del clip tendría reinicios por tramo; usa bypass antes de revisar')
    if not isinstance(points,list) or not 2<=len(points)<=8:raise ValueError('Velocidad escalonada requiere2–8 puntos')
    checked=[];previous=-1
    for p in points:
        if not isinstance(p,dict) or set(p)!={'source_seconds','speed'}:raise ValueError('Punto requiere source_seconds y speed')
        x=edit.number(p['source_seconds'],clip['in_seconds'],clip['out_seconds']);rate=edit.number(p['speed'],.25,4)
        if x<=previous or x>=clip['out_seconds']:raise ValueError('Puntos de fuente crecientes, anteriores a la salida')
        checked.append({'source_seconds':x,'speed':rate});previous=x
    if checked[0]['source_seconds']!=clip['in_seconds']:raise ValueError('El primer punto debe coincidir con la entrada del clip')
    datasets=[d for d in edl.get('candidate_sets',[]) if d.get('source_id')==clip['source_id']]
    if len(datasets)>8 or sum(len(d.get('words',[])) for d in datasets)>10000:raise ValueError('Presupuesto de revisión:8 conjuntos y10000 palabras; reduce el montaje de trabajo')
    before_reports={d['id']:inspect(edl,d['id']) for d in datasets}
    for report in before_reports.values():
        for word in report['words']:
            if word['clip_id']==clip_id and any(word['source']['start_seconds']<p['source_seconds']<word['source']['end_seconds'] for p in checked[1:]):raise ValueError('Un cambio de velocidad cortaría la palabra guardada: '+word['text'])
    index=edl['cuts'].index(clip);start=sum(edit.frames(c,fps)/fps for c in edl['cuts'][:index]);old_length=edit.frames(clip,fps)/fps;end=start+old_length
    old_knots=[start];new_knots=[start];pieces=[];segments=[]
    for i,p in enumerate(checked):
        a=p['source_seconds'];b=checked[i+1]['source_seconds'] if i+1<len(checked) else clip['out_seconds']
        n=math.floor((b-a)/p['speed']*fps+.5)
        if n<1:raise ValueError('Tramo de velocidad inferior a un fotograma')
        exact_rate=(Fraction(str(b))-Fraction(str(a)))*fps/n
        actual=float(exact_rate)
        # Stored word clock uses decimal Fractions. Round the float upward
        # if needed so an exact source-end word never falls epsilon beyond n/fps.
        while Fraction(str(actual))<exact_rate:actual=math.nextafter(actual,math.inf)
        if not .25<=actual<=4:raise ValueError('Cuantización excede velocidad0,25–4; separa más los puntos')
        piece={**deepcopy(clip),'in_seconds':a,'out_seconds':b,'speed':actual}
        if i:piece['id']=uuid.uuid4().hex
        piece.pop('transition',None)
        piece['speed_ramp']={'contract':CONTRACT,'original_clip_id':clip_id,'segment':i,'requested_speed':p['speed'],'points':deepcopy(checked)}
        pieces.append(piece);old_knots.append(start+(b-clip['in_seconds'])/(clip['out_seconds']-clip['in_seconds'])*old_length);new_knots.append(new_knots[-1]+n/fps)
        segments.append({'source':[a,b],'output_frames':n,'requested_speed':p['speed'],'effective_speed':actual})
    if 'transition' in clip:pieces[-1]['transition']=deepcopy(clip['transition'])
    delta=new_knots[-1]-end
    def warp(t):
        if t<=start:return t
        if t>=end:return t+delta
        for a,b,x,y in zip(old_knots,old_knots[1:],new_knots,new_knots[1:]):
            if a<=t<=b:return x+(t-a)*(y-x)/(b-a)
        raise ValueError('Tiempo fuera del mapa')
    def retime_items(items):
        result=[]
        for item in items:
            a=item['start_seconds'];b=a+(item['out_seconds']-item['in_seconds'])/item['speed']
            edges=[a]+[t for t in old_knots if a<t<b]+[b]
            affected=any(abs(warp(t)-t)>1e-9 for t in edges)
            if item.get('locked') and affected:raise ValueError('La curva movería un recurso bloqueado')
            if item.get('motion') and a<end and b>start:raise ValueError('Animación procedural de capa requiere remapeo específico; no se modifica')
            if len(edges)>2 and ((effective(item.get('audio_processing')) or {}).get('compressor',{}).get('enabled') or item.get('fade_in',0) or item.get('fade_out',0)):raise ValueError('Audio con compresor/fundidos cruzaría tramos; revisa o usa bypass antes')
            for j,(left,right) in enumerate(zip(edges,edges[1:])):
                scale=(warp(right)-warp(left))/(right-left);speed=item['speed']/scale
                if not .25<=speed<=4:raise ValueError('La velocidad vinculada de audio/capa excedería0,25–4')
                value={**deepcopy(item),'start_seconds':warp(left),'in_seconds':item['in_seconds']+(left-a)*item['speed'],
                       'out_seconds':item['in_seconds']+(right-a)*item['speed'],'speed':speed}
                if j:value['id']=uuid.uuid4().hex
                for key in ('fade_in','fade_out'):
                    if key in value:value[key]*=scale
                result.append(value)
        return result
    out=deepcopy(edl)
    if abs(delta)>1e-9 and any(c.get('locked') for c in out['cuts'][index+1:]):raise ValueError('La curva movería vídeo posterior bloqueado')
    out['cuts'][index:index+1]=pieces
    out['audio_tracks']=retime_items(edl['audio_tracks']);out['layers']=retime_items(edl.get('layers',[]))
    for key in ('titles','cues'):
        for item in out.get(key,[]):
            if item.get('locked') and (warp(item['start_seconds'])!=item['start_seconds'] or warp(item['end_seconds'])!=item['end_seconds']):raise ValueError('Etiqueta bloqueada afectada')
            item['start_seconds']=warp(item['start_seconds']);item['end_seconds']=warp(item['end_seconds'])
    for item in out.get('markers',[]):item['seconds']=warp(item['seconds'])
    if follow_volume:
        from lib.studio_volume_automation import value_at,normalize
        for lane,settings in out.get('volume_automation',{}).items():
            points2=settings['points']
            if not points2:continue
            times=sorted(set(p['seconds'] for p in points2)|{t for t in old_knots if points2[0]['seconds']<t<points2[-1]['seconds']})
            out['volume_automation'][lane]=normalize({'bypass':settings.get('bypass',False),'points':[{'seconds':warp(t),'gain':value_at(points2,t)} for t in times]})
    edit._validate_edit(out)
    for key,old in before_reports.items():
        after=inspect(out,key)
        token=lambda w:(w['set_id'],w['word_index'],w['source']['start_seconds'],w['source']['end_seconds'])
        if Counter(map(token,old['words']))!=Counter(map(token,after['words'])):raise ValueError('La cuantización perdería palabras completas; cambia los puntos')
    from lib.studio_subtitle_karaoke import validate_render
    validate_render(out)
    report={'contract':CONTRACT,'clip_id':clip_id,'input_edl_sha256':edit.edit_digest(edl),'points':checked,'segments':segments,
        'old_montage_knots':old_knots,'new_montage_knots':new_knots,'duration_before':edit.duration(edl),'duration_after':edit.duration(out),
        'follow_volume':follow_volume,'protected_word_sets':list(before_reports),'audio_pieces':len(out['audio_tracks']),'layer_pieces':len(out['layers']),
        'warnings':['Curva escalonada hold; no rampa suave ni optical flow. Audio vinculado se retima también, sin conservar su tempo original.',
                    'Palabras protegidas según tiempos guardados; no alineación acústica nueva. Puntos de volumen absolutos salvo opción explícita.']}
    return report,out


def project_plan(pid,data):
    from lib import studio_editor as edit
    if set(data)-{'id','points','follow_volume'}:raise ValueError('Propuesta admite puntos escalonados hold; no parámetros extra')
    value=edit.state(pid);report,_=propose(value['edit_decisions'],data['id'],data['points'],data.get('follow_volume',False))
    return {'project_id':pid,'revision':value['revision'],**report}


def apply(edl,data):
    if data.get('operation')!='clip_speed_ramp':return False
    from lib import studio_editor as edit
    if set(data)-{'operation','revision','id','points','follow_volume','reviewed','input_edl_sha256'}:raise ValueError('Esta entrega admite escalones hold, no curvas suaves ni parámetros extra')
    if data.get('reviewed') is not True:raise ValueError('Revisa el mapa de tiempos antes de aplicar')
    if data.get('input_edl_sha256')!=edit.edit_digest(edl):raise edit.Conflict('La propuesta de velocidad quedó obsoleta; recupera estado')
    _,out=propose(edl,data['id'],data['points'],data.get('follow_volume',False));edl.clear();edl.update(out)
    return True
