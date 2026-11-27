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


def report(edl):
    from lib.studio_editor import edit_digest
    policy=normalize(edl.get('subtitle_layout',{}));items=[];proposed=deepcopy(edl['cues'])
    for index,cue in enumerate(edl['cues']):
        lines=cue['text'].split('\n');count=len(cue['text'].replace('\n',''));cps=count/(cue['end_seconds']-cue['start_seconds'])
        warnings=[]
        if len(lines)>policy['max_lines']:warnings.append('Demasiadas líneas')
        if max(map(len,lines))>policy['max_chars_per_line']:warnings.append('Línea demasiado larga')
        if cps>policy['max_cps']:warnings.append('Velocidad de lectura alta')
        proposed[index]['text']=reflow(cue['text'],policy['max_chars_per_line'])
        items.append({'index':index,'start_seconds':cue['start_seconds'],'end_seconds':cue['end_seconds'],
                      'text':cue['text'],'lines':len(lines),'max_line_chars':max(map(len,lines)),
                      'cps':cps,'warnings':warnings,'proposed_text':proposed[index]['text']})
    return {'contract':'subtitle-reading-layout-v1','input_edl_sha256':edit_digest(edl),'policy':policy,
            'cues':items,'warning_cues':sum(bool(x['warnings']) for x in items),'proposed_cues':proposed,
            'scope':'Reading warnings, not measured comprehension; line breaks never invent word timing',
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
