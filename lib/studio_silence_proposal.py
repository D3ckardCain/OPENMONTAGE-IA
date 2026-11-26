"""Read-only source silence proposals in the existing frame-quantized EDL clock."""
from fractions import Fraction
import math

from lib import studio_editor as editor, studio_word_clock as clock

CONTRACT = 'studio-silence-proposal-v1'


def _time(value, high=7200):
    return Fraction(str(editor.number(value, 0, high)))


def _merge(rows):
    result = []
    for a, b in sorted(rows):
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(b, result[-1][1]))
        else:
            result.append((a, b))
    return result


def _ranges(rows, duration):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise ValueError('Se requieren1–500 intervalos explícitos')
    result = []
    for row in rows:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError('Intervalo fuente no válido')
        a, b = (_time(v, duration) for v in row)
        if b <= a:
            raise ValueError('Intervalo vacío o invertido')
        result.append((a, b))
    return _merge(result)


def _covered(a, b, ranges):
    return any(x <= a and b <= y for x, y in ranges)


def draft(edl, data):
    if data.get('input_edl_sha256') != editor.edit_digest(edl):
        raise editor.Conflict('La base de silencios quedó obsoleta; vuelve a prepararla')
    if data.get('guides') is not None:
        raise ValueError('Primera fase: una fuente guía explícita; combinación multiguía aún no disponible')
    report = clock.inspect(edl, data['set_id'])
    if data.get('word_data_sha256') != report['word_data_sha256']:
        raise editor.Conflict('Las palabras cambiaron; vuelve a preparar la propuesta')
    source_id = report['source_id']; source = edl['sources'][source_id]
    analysis = data['analysis']
    if not isinstance(analysis, dict):
        raise ValueError('Falta un análisis de silencios declarado')
    if analysis.get('source_id') != source_id or analysis.get('source_sha256') != source['sha256']:
        raise editor.Conflict('El análisis no corresponde a la fuente/huella de las palabras')
    method = analysis.get('method')
    if method not in ('ffmpeg.silencedetect', 'synthetic_fixture'):
        raise ValueError('Método no admitido; reutiliza intervalos de silencedetect o fixtures etiquetados')
    if analysis.get('clock') != 'source_seconds':
        raise ValueError('Se requieren segundos de fuente, no tiempos del montaje')
    threshold = editor.number(analysis['threshold_db'], -120, 0)
    minimum = _time(analysis['min_silence_seconds'], 10)
    if minimum <= 0:
        raise ValueError('La duración mínima de detección debe ser positiva')
    duration = source['duration']
    coverage = _ranges(analysis['processed_ranges'], duration)
    raw = analysis['intervals']
    silences = [] if raw == [] else _ranges(raw, duration)
    if any(not _covered(a, b, coverage) for a, b in silences):
        raise ValueError('Silencio fuera de la cobertura procesada declarada')
    padding = _time(data.get('padding_seconds', .1), 2)
    word_padding = _time(data.get('word_padding_seconds', .08), 2)
    min_cut = _time(data.get('min_cut_seconds', .1), 10)
    if min_cut <= 0:
        raise ValueError('La duración mínima del corte debe ser positiva')
    dataset = next(s for s in edl['candidate_sets'] if s['id'] == data['set_id'])
    protected = _merge([(max(Fraction(0), _time(w['start']) - word_padding),
                         min(_time(duration), _time(w['end']) + word_padding)) for w in dataset['words']])
    allowed = []
    for start, end in silences:
        if end - start < minimum or end - start <= 2 * padding:
            continue
        pieces = [(start + padding, end - padding)]
        for a, b in protected:
            pieces = [(x, y) for lo, hi in pieces for x, y in
                      ((lo, min(hi, a)), (max(lo, b), hi)) if y > x]
            if not pieces:
                break
        allowed.extend(pieces)
    if len(allowed) > 2000:
        raise ValueError('Propuesta superior a2000 fragmentos; acota el análisis')
    candidates = []; blockers = []; fps = edl['output']['fps']
    for clip in report['clips']:
        original = next(c for c in edl['cuts'] if c['id'] == clip['clip_id'])
        if original.get('kind') == 'gap':
            continue
        if not clip['source_inspected']:
            blockers.append('Fuente sin guía/palabras: ' + clip['clip_id']); continue
        if clip['boundary_review_required'] or not clip['coverage_complete_declared']:
            blockers.append('Palabras cortadas/cero o cobertura ASR parcial: ' + clip['clip_id']); continue
        a, b = (_time(original[k]) for k in ('in_seconds', 'out_seconds'))
        if not _covered(a, b, coverage):
            blockers.append('Cobertura acústica parcial: ' + clip['clip_id']); continue
        offset = Fraction(*clip['timeline']['start_rational'])
        limit = Fraction(*clip['timeline']['end_rational'])
        speed = Fraction(*clip['speed_rational'])
        for lo, hi in allowed:
            lo, hi = max(lo, a), min(hi, b)
            if hi <= lo:
                continue
            # Round strictly inward: never extend a cut into a protected word.
            first = math.ceil((offset + (lo - a) / speed) * fps)
            last = math.floor(min(limit, offset + (hi - a) / speed) * fps)
            if last <= first or Fraction(last - first, fps) < min_cut:
                continue
            start, end = Fraction(first, fps), Fraction(last, fps)
            candidates.append(dict(id=clip['clip_id'] + ':' + str(first) + ':' + str(last),
                clip_id=clip['clip_id'], source_id=source_id,
                source=clock._span(a + (start - offset) * speed, a + (end - offset) * speed),
                timeline=clock._span(start, end), frames=[first, last],
                reason='declared_acoustic_interval_minus_padding_and_stored_words',
                reviewed=False, selected=False))
            if len(candidates) > 2000:
                raise ValueError('Propuesta superior a2000 ocurrencias; acota el montaje')
    return dict(contract=CONTRACT, ready_for_review=not blockers, apply_available=False,
        blockers=blockers, candidates=candidates if not blockers else [],
        input_edl_sha256=report['input_edl_sha256'], word_data_sha256=report['word_data_sha256'],
        transcript_sha256=report['transcript_sha256'], source_sha256=report['source_sha256'],
        analysis_sha256=editor.edit_digest(analysis), set_id=data['set_id'], source_id=source_id,
        timebase=report['timebase'], analysis_provenance=dict(method=method, clock='source_seconds',
            threshold_db=threshold, min_silence_seconds=float(minimum),
            evidence='synthetic_not_measured' if method == 'synthetic_fixture' else 'declared_not_independently_verified',
            processed_ranges=[clock._span(a, b) for a, b in coverage],
            normalized_intervals=[clock._span(a, b) for a, b in silences]),
        parameters=dict(padding_seconds=float(padding), word_padding_seconds=float(word_padding),
                        min_cut_seconds=float(min_cut)),
        source_file_rehashed=False, media_read=False, project_modified=False,
        warnings=['Propuesta numérica: no detecta audio, no VAD, no inferencia.',
                  'Palabras ausentes no prueban silencio; se requieren intervalos acústicos explícitos.',
                  'Una sola guía; no comprueba otras voces/pistas ni contexto semántico.',
                  'Aplicación ripple, escucha de límites y revisión sobre waveform aún no disponibles.'])


def project_draft(pid, data):
    value = editor.state(pid)
    editor._revision(value, data.get('revision'))
    return dict(project_id=pid, revision=value['revision'], **draft(value['edit_decisions'], data))
