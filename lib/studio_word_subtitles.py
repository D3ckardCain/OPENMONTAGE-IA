"""Conservative subtitle candidates from stored word clocks; no ASR or media I/O."""
from copy import deepcopy
from lib import studio_editor as editor, studio_word_clock as clock
from lib.scene_subtitles import parse_srt

CONTRACT = 'studio-word-subtitles-v1'


def draft(edl, set_id):
    report = clock.inspect(edl, set_id)
    blockers = []
    for clip in report['clips']:
        original = next(c for c in edl['cuts'] if c['id'] == clip['clip_id'])
        if original.get('kind') == 'gap':
            continue
        if not clip['source_inspected']:
            blockers.append('Fuente no cubierta por este conjunto: ' + clip['clip_id'])
        elif clip['boundary_review_required'] or not clip['coverage_complete_declared']:
            blockers.append('Revisa palabras cortadas/cero o cobertura parcial: ' + clip['clip_id'])
    words = report['words']
    if len(words) > 2000:
        blockers.append('Borrador limitado a2000 ocurrencias; divide el montaje antes de prepararlo')
    previous = 0
    for word in words:
        a, b = (round(word['timeline'][k] * 1000) for k in ('start_seconds', 'end_seconds'))
        if a < previous or b <= a:
            blockers.append('Solape o intervalo no representable en milisegundos: ' + word['occurrence_id'])
        previous = b
        if any(c in word['text'] for c in ('\x00', '\n', '\r')) or len(word['text'].strip()) > 400:
            blockers.append('Texto de palabra no representable sin modificarlo: ' + word['occurrence_id'])
    if not words:
        blockers.append('No hay palabras completas para preparar subtítulos')
    cues = []
    groups = []
    if not blockers:
        group = []
        for word in words:
            text = ' '.join(w['text'].strip() for w in group + [word])
            if group and (word['clip_id'] != group[-1]['clip_id'] or
                          word['language'] != group[-1]['language'] or word['speaker'] != group[-1]['speaker'] or
                          len(group) >= 6 or len(text) > 80 or
                          word['timeline']['start_seconds'] - group[-1]['timeline']['end_seconds'] > .6 or
                          word['timeline']['end_seconds'] - group[0]['timeline']['start_seconds'] > 4):
                groups.append(group)
                group = []
            group.append(word)
        if group:
            groups.append(group)
        cues = [dict(start_seconds=round(g[0]['timeline']['start_seconds'], 3),
                     end_seconds=round(g[-1]['timeline']['end_seconds'], 3),
                     text=' '.join(w['text'].strip() for w in g)) for g in groups]
        try:
            # Reuse exactly the editor's SRT representability/size/overlap rules.
            parsed = parse_srt(editor.srt({'cues': cues}), report['duration_seconds'])
            if parsed != cues:
                blockers.append('El formato SRT cambiaría el borrador; revisa sus tiempos/texto')
        except ValueError as exc:
            blockers.append(str(exc))
    return dict(contract=CONTRACT, set_id=set_id, ready=not blockers, blockers=blockers,
                input_edl_sha256=report['input_edl_sha256'], word_data_sha256=report['word_data_sha256'],
                source_sha256=report['source_sha256'], transcript_sha256=report['transcript_sha256'],
                source_binding=report['source_binding'], source_file_rehashed=False,
                asr_provenance=report['asr_provenance'], timebase=report['timebase'],
                cues=cues if not blockers else [],
                word_groups=deepcopy(groups) if not blockers else [],
                warnings=report['warnings'] + ['Agrupación mecánica (hasta seis palabras); no revisión semántica ni calidad de lectura.',
                 'Tiempos SRT redondeados a milisegundos; los racionales originales quedan en procedencia.',
                 'No cambia el idioma del proyecto ni acredita silencio en huecos. Revisar antes de aplicar.'])


def apply(edl, data):
    candidate = draft(edl, data['set_id'])
    if data.get('input_edl_sha256') != candidate['input_edl_sha256'] or data.get('word_data_sha256') != candidate['word_data_sha256']:
        raise editor.Conflict('El borrador quedó obsoleto; vuelve a prepararlo')
    if not candidate['ready']:
        raise ValueError('Borrador bloqueado: ' + '; '.join(candidate['blockers'][:5]))
    if data.get('reviewed') is not True:
        raise ValueError('Revisa texto, contexto y tiempos antes de aplicar el borrador')
    if edl['cues'] and data.get('replace_existing') is not True:
        raise ValueError('Confirma explícitamente reemplazar los subtítulos existentes')
    edl['cues'] = deepcopy(candidate['cues'])
    # Historical derivation, never a claim that later manual edits remain aligned.
    edl['subtitle_word_origin'] = {**candidate, 'applied_cues_sha256': editor.edit_digest(edl['cues']),
                                  'scope': 'snapshot_at_apply_not_live_alignment'}


def project_draft(pid, set_id):
    value = editor.state(pid)
    return dict(project_id=pid, revision=value['revision'], **draft(value['edit_decisions'], set_id))
