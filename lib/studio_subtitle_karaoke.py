"""Highlight exact stored ASR word occurrences; no alignment, ASR or invented time."""
import re
from lib import studio_editor as edit,studio_word_clock as clock

CONTRACT='stored-word-highlight-v1'


def normalize(value):
    if not isinstance(value,dict) or set(value)-{'enabled','set_id','highlight_color','inactive_color','word_data_sha256'}:
        raise ValueError('Configuración karaoke desconocida')
    result={'enabled':False,'set_id':'','highlight_color':'#FFD24D','inactive_color':'#FFFFFF',**value}
    if type(result['enabled']) is not bool or not isinstance(result['set_id'],str):raise ValueError('Karaoke requiere enabled booleano y set_id')
    for name in ('highlight_color','inactive_color'):
        if not isinstance(result[name],str) or not re.fullmatch('#[0-9A-Fa-f]{6}',result[name]):raise ValueError('Color karaoke requiere #RRGGBB')
        result[name]=result[name].upper()
    return result


def report(edl,set_id):
    inspected=clock.inspect(edl,set_id);blockers=[];items=[];words=inspected['words']
    dataset=next(v for v in edl['candidate_sets'] if v['id']==set_id)
    ranges=dataset['coverage']['processed_ranges']
    if len(words)>2000 or len(edl['cues'])>400:raise ValueError('Karaoke limitado a2000 palabras y400 cues por montaje')
    if not edl['cues']:blockers.append('No hay cues que vincular a las palabras guardadas')
    for index,cue in enumerate(edl['cues']):
        a,b=cue['start_seconds'],cue['end_seconds'];selected=[];partial=False
        for word in words:
            x,y=word['timeline']['start_seconds'],word['timeline']['end_seconds']
            if x<b and y>a:
                if x<a-.001 or y>b+.001:partial=True
                else:selected.append(word)
        tokens=list(re.finditer(r'\S+',cue['text']));cursor=0;bound=[];previous=a
        for word in selected:
            lexemes=re.findall(r'\S+',word['text']);actual=[m.group() for m in tokens[cursor:cursor+len(lexemes)]]
            start,end=word['timeline']['start_seconds'],word['timeline']['end_seconds']
            if not lexemes or lexemes!=actual or start<previous-.001 or round(end*100)<=round(start*100):
                partial=True;break
            bound.append({'text':word['text'].strip(),'span':[tokens[cursor].start(),tokens[cursor+len(lexemes)-1].end()],
                          'start_seconds':start,'end_seconds':end,'occurrence_id':word['occurrence_id'],
                          'source':word['source'],'timing_evidence':word['timing_evidence']})
            previous=end;cursor+=len(lexemes)
        if partial or not bound or cursor!=len(tokens):blockers.append(f'Cue{index+1}: texto/tiempos no corresponden a palabras completas; revisa o reaplica el borrador')
        items.append({'index':index,'text':cue['text'],'start_seconds':a,'end_seconds':b,'words':bound})
    return {'contract':CONTRACT,'set_id':set_id,'ready':not blockers,'blockers':blockers,'cues':items,
            'input_edl_sha256':edit.edit_digest(edl),'word_data_sha256':inspected['word_data_sha256'],
            'source_sha256':inspected['source_sha256'],'transcript_sha256':inspected['transcript_sha256'],
            'timebase':inspected['timebase'],'warnings':inspected['warnings']+['ASS redondea a centésimas; no acredita alineación perceptiva nueva.'],
            'asr_provenance':inspected['asr_provenance'],'declared_processed_ranges':ranges,'source_file_rehashed':False}


def apply(edl,data):
    if data.get('operation')!='subtitle_karaoke':return False
    value=normalize({**edl.get('subtitle_karaoke',{}),**{k:data[k] for k in ('enabled','set_id','highlight_color','inactive_color') if k in data}})
    if value['enabled']:
        result=report(edl,value['set_id'])
        if data.get('reviewed') is not True:raise ValueError('Revisa palabras y tiempos antes de activar karaoke')
        if not result['ready']:raise ValueError('; '.join(result['blockers'][:5]))
        if data.get('input_edl_sha256')!=result['input_edl_sha256'] or data.get('word_data_sha256')!=result['word_data_sha256']:
            raise edit.Conflict('La revisión karaoke quedó obsoleta; vuelve a consultarla')
        value['word_data_sha256']=result['word_data_sha256']
    edl['subtitle_karaoke']=value
    return True


def validate_render(edl):
    settings=normalize(edl.get('subtitle_karaoke',{}))
    if edl['subtitle_style'].get('mode')!='burn' or not settings['enabled']:return None
    result=report(edl,settings['set_id'])
    if not result['ready'] or result['word_data_sha256']!=settings.get('word_data_sha256'):
        raise ValueError('Karaoke obsoleto o incompatible: revisa las palabras/cues o desactívalo antes de exportar')
    return result


def ass(edl,width,height):
    from lib.scene_burned_subtitles import _ass
    settings=normalize(edl.get('subtitle_karaoke',{}))
    if not settings['enabled']:
        return _ass(edl['cues'],width,height,edl['subtitle_style'],edl.get('subtitle_layout',{}).get('safe_area'))
    result=report(edl,settings['set_id'])
    if not result['ready'] or result['word_data_sha256']!=settings.get('word_data_sha256'):
        raise ValueError('Revisa la vinculación karaoke antes de descargar ASS')
    cues=[];highlights=[]
    for cue in result['cues']:
        start,end=round(cue['start_seconds']*100),round(cue['end_seconds']*100)
        bounds=sorted({start,end,*[max(start,min(end,round(w[k]*100))) for w in cue['words'] for k in ('start_seconds','end_seconds')]})
        for a,b in zip(bounds,bounds[1:]):
            active=next((w for w in cue['words'] if round(w['start_seconds']*100)<=a and b<=round(w['end_seconds']*100)),None)
            cues.append({'text':cue['text'],'start_seconds':a/100,'end_seconds':b/100})
            highlights.append({'span':active['span'] if active else None,'active':settings['highlight_color'],'inactive':settings['inactive_color']})
    return _ass(cues,width,height,edl['subtitle_style'],edl.get('subtitle_layout',{}).get('safe_area'),highlights)


def project_report(pid,set_id):
    value=edit.state(pid);return {'project_id':pid,'revision':value['revision'],**report(value['edit_decisions'],set_id)}
