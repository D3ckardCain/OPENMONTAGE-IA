"""Explicit project reading limits and burn-only safe area. No ASR or accounts."""
from copy import deepcopy
import re
import textwrap

DEFAULT={'max_lines':2,'max_chars_per_line':42,'max_cps':20.,
         'safe_area':{'left':.05,'right':.05,'top':.1,'bottom':.12}}


def normalize(value):
    from lib.studio_editor import number
    if not isinstance(value,dict) or set(value)-set(DEFAULT):raise ValueError('Política de subtítulos desconocida')
    result=deepcopy(DEFAULT);result.update(value)
    for key,lo,hi in [('max_lines',1,4),('max_chars_per_line',10,80)]:
        if type(result[key]) is not int or not lo<=result[key]<=hi:raise ValueError('Límite de lectura fuera de intervalo')
    result['max_cps']=number(result['max_cps'],5,40)
    safe=result['safe_area']
    if not isinstance(safe,dict) or set(safe)!=set(DEFAULT['safe_area']):raise ValueError('Área segura requiere left/right/top/bottom')
    result['safe_area']={k:number(v,0,.4) for k,v in safe.items()}
    return result


def reflow(text,width):
    # Explicit formatting proposal: never drop words, negations or punctuation.
    words=re.findall(r'\S+',text)
    return '\n'.join(textwrap.wrap(' '.join(words),width=width,break_long_words=False,break_on_hyphens=False))


def _timing_audit(cues, duration):
    """Describe cue interval defects without guessing corrected timestamps."""
    warnings={};overlaps=[];out_of_range=[];invalid_intervals=[];valid=[]
    for index,cue in enumerate(cues):
        warnings[index]=[]
        if not isinstance(cue,dict):
            warnings[index].append('Intervalo temporal inválido')
            invalid_intervals.append(index)
            continue
        start=cue.get('start_seconds');end=cue.get('end_seconds')
        valid_numbers=(type(start) in (int,float) and math.isfinite(start) and
                       type(end) in (int,float) and math.isfinite(end))
        if not valid_numbers or start<0 or end<=start:
            warnings[index].append('Intervalo temporal inválido')
            invalid_intervals.append(index)
            continue
        if end>duration+.02:
            warnings[index].append('Fuera de duración del montaje')
            out_of_range.append(index)
        valid.append((start,end,index))
    active_end=None;active_index=None
    for start,end,index in sorted(valid):
        if active_end is not None and start<active_end:
            overlaps.append({'earlier_index':active_index,'later_index':index,
                             'overlap_seconds':min(active_end,end)-start})
            warnings[index].append(f'Se solapa con subtítulo #{active_index+1}')
        if active_end is None or end>active_end:
            active_end,active_index=end,index
    return warnings,{'duration_seconds':duration,'invalid_interval_cues':invalid_intervals,
                     'out_of_range_cues':out_of_range,'overlaps':overlaps,
                     'scope':'Comparación temporal contra el montaje; no propone ni mueve tiempos'}


def report(edl):
    from lib.studio_editor import edit_digest,duration as video_duration
    policy=normalize(edl.get('subtitle_layout',{}));items=[];proposed=deepcopy(edl['cues'])
    duration=video_duration(edl)
    timing_warnings,timing=_timing_audit(edl['cues'],duration)
    for index,cue in enumerate(edl['cues']):
        text=cue.get('text','') if isinstance(cue,dict) else ''
        if not isinstance(text,str):text=''
        lines=text.split('\n');count=len(text.replace('\n',''))
        start=cue.get('start_seconds') if isinstance(cue,dict) else None
        end=cue.get('end_seconds') if isinstance(cue,dict) else None
        valid_interval=(type(start) in (int,float) and math.isfinite(start) and
                        type(end) in (int,float) and math.isfinite(end) and end>start)
        cps=count/(end-start) if valid_interval else None
        warnings=list(timing_warnings[index])
        if len(lines)>policy['max_lines']:warnings.append('Demasiadas líneas')
        if max(map(len,lines))>policy['max_chars_per_line']:warnings.append('Línea demasiado larga')
        if cps is not None and cps>policy['max_cps']:warnings.append('Velocidad de lectura alta')
        if isinstance(proposed[index],dict) and isinstance(proposed[index].get('text'),str):
            proposed[index]['text']=reflow(proposed[index]['text'],policy['max_chars_per_line'])
        items.append({'index':index,'start_seconds':start,'end_seconds':end,
                      'text':text,'lines':len(lines),'max_line_chars':max(map(len,lines)),
                      'cps':cps,'cps_available':cps is not None,'warnings':warnings,
                      'proposed_text':proposed[index].get('text','') if isinstance(proposed[index],dict) else ''})
    return {'contract':'subtitle-reading-layout-v1','input_edl_sha256':edit_digest(edl),'policy':policy,
            'cues':items,'warning_cues':sum(bool(x['warnings']) for x in items),
            'timing_warning_cues':sum(bool(timing_warnings[index]) for index in timing_warnings),
            'timing':timing,'proposed_cues':proposed,
            'scope':'Reading/timing warnings, not measured comprehension or glyph bounds; line breaks never invent word timing',
            'soft_style_supported':False,'burn_safe_area_supported':True}

def apply(edl,data):
    from lib import studio_editor as edit
    op=data.get('operation')
    if op=='subtitle_layout':
        value=data['layout']
        if value is None:edl.pop('subtitle_layout',None)
        else:edl['subtitle_layout']=normalize(value)
    elif op=='subtitle_reflow':
        result=report(edl)
        if data.get('reviewed') is not True:raise ValueError('Revisa la propuesta de saltos de línea')
        if data.get('input_edl_sha256')!=result['input_edl_sha256']:raise edit.Conflict('El borrador quedó obsoleto; vuelve a consultar')
        edl['cues']=result['proposed_cues']
    else:return False
    return True


def project_report(pid):
    from lib import studio_editor as edit
    value=edit.state(pid)
    return {'project_id':pid,'revision':value['revision'],**report(value['edit_decisions'])}
