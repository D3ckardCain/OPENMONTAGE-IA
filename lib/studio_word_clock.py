"""Read existing ASR word spans in the frame-quantized EDL clock; no I/O/ASR."""
from copy import deepcopy
from fractions import Fraction
import re
from lib import studio_editor as editor


def _time(value,low=0,high=7200):
    return Fraction(str(editor.number(value,low,high)))


def _span(start,end):
    return {'start_seconds':float(start),'end_seconds':float(end),
            'start_rational':[start.numerator,start.denominator],
            'end_rational':[end.numerator,end.denominator]}


def inspect(edl,set_id):
    dataset=next((s for s in edl.get('candidate_sets',[]) if s.get('id')==set_id),None)
    if not dataset:
        raise ValueError('Selecciona un conjunto ASR guardado en el proyecto')
    source=edl['sources'][dataset['source_id']]
    if source['kind']!='video' or source['sha256']!=dataset['source_sha256']:
        raise ValueError('Cambió la fuente del conjunto ASR; revisa su procedencia')
    if not isinstance(dataset.get('transcript_sha256'),str) or not re.fullmatch('[a-f0-9]{64}',dataset['transcript_sha256']):
        raise ValueError('Falta la huella de transcripción guardada')
    fps=edl['output']['fps']
    if type(fps) is not int or not 1<=fps<=60:
        raise ValueError('Este EDL requiere FPS entero1–60; no se cambia su cadencia')
    words=dataset.get('words')
    if not isinstance(words,list) or not 1<=len(words)<=5000 or len(edl['cuts'])>200:
        raise ValueError('Límite de inspección:5000palabras y200cortes')
    coverage=dataset.get('coverage',{}).get('processed_ranges')
    if not isinstance(coverage,list) or not 1<=len(coverage)<=100:
        raise ValueError('Falta cobertura ASR declarada')
    ranges=[]
    for row in coverage:
        if not isinstance(row,list) or len(row)!=2:
            raise ValueError('Cobertura ASR inválida')
        a,b=(_time(v,0,source['duration']) for v in row)
        if b<=a or ranges and a<ranges[-1][1]:
            raise ValueError('Cobertura ASR no normalizada')
        ranges.append((a,b))
    checked=[];previous=Fraction(-1)
    for index,word in enumerate(words):
        if not isinstance(word,dict) or word.get('index')!=index or type(word.get('index')) is not int or not isinstance(word.get('word'),str) or not word['word'].strip():
            raise ValueError('Índices/texto de palabras guardadas no válidos')
        a,b=(_time(word[k],0,source['duration']) for k in ('start','end'))
        if b<a or a<previous or not any(x<=a and b<=y for x,y in ranges):
            raise ValueError('Tiempos/orden/cobertura de palabras no coherentes')
        checked.append((word,a,b));previous=a
    occurrences=[];clips=[];cursor=Fraction(0);ids=set();excluded_total=0
    for clip in edl['cuts']:
        if clip['id'] in ids:raise ValueError('ID de clip repetido')
        ids.add(clip['id'])
        a,b=(_time(clip[k]) for k in ('in_seconds','out_seconds'))
        speed=_time(clip['speed'],.25,4)
        if b<=a:raise ValueError('Intervalo de clip no válido')
        frames=editor.frames(clip,fps)
        if frames<1:raise ValueError('Clip sin fotogramas de salida')
        end=cursor+Fraction(frames,fps)
        if end>7200:raise ValueError('Montaje superior a7200s')
        info=dict(clip_id=clip['id'],timeline=_span(cursor,end),frames=frames,source_inspected=False)
        if clip.get('kind')!='gap' and clip.get('source_id')==dataset['source_id']:
            if b>_time(source['duration']):raise ValueError('Clip fuera de su fuente')
            omitted=[];retained=0;outside=0
            for word,start,finish in checked:
                zero=finish==start
                if (zero and not a<=start<b) or (not zero and (finish<=a or start>=b)):
                    outside+=1;continue
                reason='zero_duration' if zero else 'partial_source_word' if start<a or finish>b else None
                out_start=cursor+(start-a)/speed;out_end=cursor+(finish-a)/speed
                if clip.get('time_warp'):
                    from lib.studio_smooth_clock import source_offset
                    out_start=cursor+Fraction(str(source_offset(clip,float(start))))
                    out_end=cursor+Fraction(str(source_offset(clip,float(finish))))
                if not reason and (out_start<cursor or out_end>end):reason='partial_frame_quantization'
                if reason:
                    omitted.append(dict(word_index=word['index'],text=word['word'],source=_span(start,finish),reason=reason))
                    continue
                timing=word.get('timing_status','unknown')
                if timing not in ('measured','estimated','imputed','unknown'):timing='unknown'
                occurrences.append(dict(occurrence_id=clip['id']+':'+set_id+':'+str(word['index']),
                    clip_id=clip['id'],set_id=set_id,word_index=word['index'],text=word['word'],
                    source=_span(start,finish),timeline=_span(out_start,out_end),
                    speaker=deepcopy(word.get('speaker',word.get('speaker_id'))),
                    language=word.get('language',dataset.get('provenance',{}).get('language')),
                    timing_status=timing,timing_evidence='declared_not_independently_verified'))
                retained+=1
            covered=sum((min(b,y)-max(a,x) for x,y in ranges if x<b and y>a),Fraction(0))
            info.update(source_inspected=True,source=_span(a,b),speed_rational=[speed.numerator,speed.denominator],
                retained_words=retained,outside_word_count=outside,excluded_words=omitted,
                boundary_review_required=bool(omitted),coverage_complete_declared=covered==b-a,
                coverage_evidence='declared_not_independently_verified')
            excluded_total+=len(omitted)
            if len(occurrences)+excluded_total>20000:raise ValueError('Informe superior a20000ocurrencias; inspecciona un montaje menor')
        clips.append(info);cursor=end
    return dict(contract='studio-word-clock-v1',set_id=set_id,source_id=dataset['source_id'],
        source_sha256=dataset['source_sha256'],transcript_sha256=dataset['transcript_sha256'],
        input_edl_sha256=editor.edit_digest(edl),word_data_sha256=editor.edit_digest(words),
        timebase=dict(clock='frame_quantized_edl',unit='seconds',output_fps=[fps,1],intervals='half_open'),
        source_file_rehashed=False,source_binding='registered_metadata',
        asr_provenance={key:deepcopy(dataset.get('provenance',{}).get(key)) for key in
                        ('binding','time_offset','language','model_size','coverage_evidence')},
        source_clock='stored_words_already_include_import_offset_not_added_again',
        duration_seconds=float(cursor),words=occurrences,clips=clips,excluded_word_occurrences=excluded_total,
        warnings=['Solo conversión de reloj; no ASR, alineación ni medición de audio nuevos.',
                  'Palabras completas conservadas; las cortadas/no positivas se reportan, no se reconstruyen.',
                  'Ausencia de palabras no prueba silencio ni contexto semántico completo.'])


def project_report(pid,set_id):
    value=editor.state(pid)
    return dict(project_id=pid,revision=value['revision'],**inspect(value['edit_decisions'],set_id))
