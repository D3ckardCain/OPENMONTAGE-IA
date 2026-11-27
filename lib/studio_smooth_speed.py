"""Reviewed continuous ramp, no cuts or hidden pitch-preservation claim."""
from copy import deepcopy
from collections import Counter
import math
from lib import studio_smooth_clock as clock


def propose(edl,clip_id,points,audio_mode):
    from lib import studio_editor as edit
    from lib.studio_word_clock import inspect
    import importlib.util
    if importlib.util.find_spec('numpy') is None:raise ValueError('Rampa no disponible: falta NumPy en el entorno del adaptador; no se instala automáticamente')
    if audio_mode!='continuous_resample_pitch_changes':raise ValueError('Modo preparado: remuestreo continuo con cambio de tono; conservar tono aún no disponible')
    items=edl['cuts']+edl['audio_tracks']+edl.get('layers',[])
    if any(c.get('time_warp') for c in items):raise ValueError('Hay una rampa continua activa; deshaz antes de cambiar su mapa o duración')
    if any(c.get('transition') for c in edl['cuts']):raise ValueError('Primera rampa continua no admite transiciones; conserva el montaje y revísalas')
    c=edit._item(edl['cuts'],clip_id)
    if c.get('kind')=='gap' or c.get('locked'):raise ValueError('Rampa requiere vídeo desbloqueado')
    if c.get('fade_in',0) or c.get('fade_out',0):raise ValueError('Fundidos del clip requieren remapeo propio; no se quitan automáticamente')
    if not isinstance(points,list) or not 2<=len(points)<=8:raise ValueError('Rampa continua requiere2–8 puntos, incluidos entrada y salida')
    pts=[]
    for p in points:
        if not isinstance(p,dict) or set(p)!={'source_seconds','speed'}:raise ValueError('Punto continuo requiere fuente y velocidad')
        pts.append({'source_seconds':edit.number(p['source_seconds'],c['in_seconds'],c['out_seconds']),'speed':edit.number(p['speed'],.25,4)})
    if pts[0]['source_seconds']!=c['in_seconds'] or pts[-1]['source_seconds']!=c['out_seconds']:raise ValueError('Incluye ambos extremos del clip; no se infieren velocidades finales')
    start=sum(edit.frames(x,edl['output']['fps'])/edl['output']['fps'] for x in edl['cuts'][:edl['cuts'].index(c)])
    old_duration=edit.frames(c,edl['output']['fps'])/edl['output']['fps']
    m={'contract':clock.CONTRACT,'points':pts,'old_start_seconds':start,'old_duration_seconds':old_duration,'fps':edl['output']['fps'],'output_frames':1}
    # Validate ordering before integrating or dividing point spans.
    if any(b['source_seconds']-a['source_seconds']<.001 for a,b in zip(pts,pts[1:])):raise ValueError('Puntos continuos crecientes y separados al menos1ms')
    raw_duration=clock.parts(m)[1];m['output_frames']=math.floor(raw_duration*m['fps']+.5);clock.validate(m)
    out=deepcopy(edl);primary=edit._item(out['cuts'],clip_id);warp=lambda t:clock.forward(m,t)
    def bind(item,old_start,role):
        old_speed=item['speed'];old_end=old_start+(item['out_seconds']-item['in_seconds'])/old_speed
        if role=='primary':old_speed=(item['out_seconds']-item['in_seconds'])/old_duration;old_end=old_start+old_duration
        changed=old_start<start+old_duration and old_end>start
        if item.get('locked') and (changed or abs(warp(old_start)-old_start)>1e-9):raise ValueError('La rampa afectaría un recurso bloqueado')
        if changed:
            if any(item.get(k) for k in ('motion','transform_keyframes','position_keyframes')):raise ValueError('Capa animada requiere remapeo de sus keyframes; no se descarta')
            if item.get('fade_in',0) or item.get('fade_out',0):raise ValueError('Fundidos vinculados requieren remapeo específico')
            if role!='layer' and edl['sources'][item['source_id']].get('audio') and (item['out_seconds']-item['in_seconds'])/old_speed>60:raise ValueError('Presupuesto: máximo60s de audio vinculado por rampa')
            item['time_warp']={'contract':clock.CONTRACT,'map':deepcopy(m),'old_start_seconds':old_start,'old_speed':old_speed,'role':role,'audio_mode':audio_mode}
            duration=warp(old_end)-warp(old_start);average=(item['out_seconds']-item['in_seconds'])/duration
            if not .25<=average<=4:raise ValueError('Velocidad efectiva vinculada fuera0,25–4')
            item['speed']=average
        if role!='primary':item['start_seconds']=warp(old_start)
    bind(primary,start,'primary')
    for item in out['audio_tracks']:bind(item,item['start_seconds'],'audio')
    for item in out.get('layers',[]):bind(item,item['start_seconds'],'layer')
    end=start+old_duration;delta=m['output_frames']/m['fps']-old_duration
    if abs(delta)>1e-9 and any(x.get('locked') for x in out['cuts'][out['cuts'].index(primary)+1:]):raise ValueError('Vídeo posterior bloqueado sería desplazado')
    for key in ('cues','titles'):
        for item in out.get(key,[]):
            if item.get('locked') and (warp(item['start_seconds'])!=item['start_seconds'] or warp(item['end_seconds'])!=item['end_seconds']):raise ValueError('Etiqueta bloqueada sería desplazada')
            item['start_seconds']=warp(item['start_seconds']);item['end_seconds']=warp(item['end_seconds'])
    for item in out.get('markers',[]):item['seconds']=warp(item['seconds'])
    # Volume automation retains its explicitly absolute clock. No approximation.
    edit._validate_edit(out)
    datasets=[d for d in edl.get('candidate_sets',[]) if d.get('source_id')==c['source_id']]
    if len(datasets)>8 or sum(len(d.get('words',[])) for d in datasets)>10000:raise ValueError('Presupuesto de palabras excedido')
    for d in datasets:
        a,b=inspect(edl,d['id']),inspect(out,d['id']);token=lambda w:(w['word_index'],w['source']['start_seconds'],w['source']['end_seconds'])
        if Counter(map(token,a['words']))!=Counter(map(token,b['words'])):raise ValueError('El nuevo reloj perdería palabras completas; no se aplica')
    from lib.studio_subtitle_karaoke import validate_render
    validate_render(out)
    return {'contract':clock.CONTRACT,'clip_id':clip_id,'input_edl_sha256':edit.edit_digest(edl),'map':m,'audio_mode':audio_mode,
      'duration_before':edit.duration(edl),'duration_after':edit.duration(out),'protected_word_sets':[d['id'] for d in datasets],
      'warnings':['Velocidad continua lineal entre puntos en reloj fuente; no Bézier ni optical flow.','Audio por remuestreo: cambia tono; sin garantía de naturalidad ni preservación de tono.','Volumen conserva tiempos absolutos; edición posterior de duración requiere deshacer esta rampa.']},out


def project_plan(pid,data):
    from lib import studio_editor as edit
    if set(data)-{'id','points','audio_mode'}:raise ValueError('Parámetros de rampa continua desconocidos')
    s=edit.state(pid);r,_=propose(s['edit_decisions'],data['id'],data['points'],data.get('audio_mode'))
    return {'project_id':pid,'revision':s['revision'],**r}


def apply(edl,data):
    if data.get('operation')!='clip_smooth_speed':return False
    from lib import studio_editor as edit
    if set(data)-{'operation','revision','id','points','audio_mode','reviewed','input_edl_sha256'}:raise ValueError('Parámetros continuos desconocidos')
    if data.get('reviewed') is not True:raise ValueError('Revisa el mapa y acepta el cambio de tono antes de aplicar')
    if data.get('input_edl_sha256')!=edit.edit_digest(edl):raise edit.Conflict('La propuesta continua quedó obsoleta; recupera estado')
    _,out=propose(edl,data['id'],data['points'],data.get('audio_mode'));edl.clear();edl.update(out);return True


def validate(edl):
    maps=set();primary=[]
    for c in edl['cuts']+edl['audio_tracks']+edl.get('layers',[]):
        w=c.get('time_warp')
        if not w:continue
        if set(w)!={'contract','map','old_start_seconds','old_speed','role','audio_mode'} or w['contract']!=clock.CONTRACT or w['audio_mode']!='continuous_resample_pitch_changes':raise ValueError('Rampa persistente desconocida')
        clock.validate(w['map'])
        from lib.studio_editor import number
        number(w['old_speed'],.25,4);number(w['old_start_seconds'],0,7200)
        if w['role'] not in ('primary','audio','layer'):raise ValueError('Rol de rampa inválido')
        if w['map']['fps']!=edl['output']['fps']:raise ValueError('FPS de rampa y proyecto distintos')
        from lib.studio_editor import edit_digest
        maps.add(edit_digest(w['map']))
        if w['role']=='primary':
            primary.append(c)
            if c['in_seconds']!=w['map']['points'][0]['source_seconds'] or c['out_seconds']!=w['map']['points'][-1]['source_seconds']:raise ValueError('Extremos de rampa y fuente distintos')
    if maps and (len(maps)!=1 or len(primary)!=1):raise ValueError('Primera entrega: un único mapa continuo con clip principal')
    if primary:
        from lib.studio_editor import frames
        c=primary[0];start=sum(frames(x,edl['output']['fps'])/edl['output']['fps'] for x in edl['cuts'][:edl['cuts'].index(c)])
        if abs(start-c['time_warp']['map']['old_start_seconds'])>1e-8:raise ValueError('El mapa continuo no coincide con la posición del clip principal')
