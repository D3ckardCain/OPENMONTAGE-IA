"""Word-grounded proposals on the existing EDL. No ASR/model execution or I/O."""
from copy import deepcopy
import hashlib
import json
import re
import uuid


def text(words):
    return ''.join(w['word'] if w['word'][:1].isspace() else ' ' + w['word'] for w in words).strip()


def candidate(dataset, first, last, reason):
    from lib.studio_editor import number
    words = dataset['words']
    if type(first) is not int or type(last) is not int or not 0 <= first <= last < len(words):
        raise ValueError('Indica índices de palabra válidos, inclusivos y desde cero')
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 2000:
        raise ValueError('Cada propuesta necesita un motivo de 1 a 2000 caracteres')
    requested = [first, last]
    # Conservative lexical boundary expansion. Not a claim of semantic quality.
    while first > 0 and not re.search(r'[.!?…][\"”\)\]]*\s*$', words[first - 1]['word']):
        first -= 1
    while last + 1 < len(words) and not re.search(r'[.!?…][\"”\)\]]*\s*$', words[last]['word']):
        last += 1
    start, end = words[first]['start'], max(w['end'] for w in words[first:last + 1])
    number(end, start + .001)
    if not any(a <= start and end <= b for a, b in dataset['coverage']['processed_ranges']):
        raise ValueError('El contexto de la frase cruza cobertura no procesada; aporta ese fragmento antes de seleccionar')
    return {'id': uuid.uuid4().hex, 'requested_word_span': requested, 'word_span': [first, last],
            'start_seconds': start, 'end_seconds': end,
            'text': text(words[first:last + 1]), 'reason': reason.strip(),
            'context_before': text(words[max(0, first - 35):first]),
            'context_after': text(words[last + 1:last + 36]),
            'boundary_method': 'whole_sentence_lexical_v1',
            'context_confirmed': False, 'status': 'pending',
            'warnings': ['Revisar antecedentes, negaciones, cifras y final de la idea; límites de frase no garantizan contexto semántico.']}


def import_set(edl, data):
    from lib.studio_editor import number
    source_id = data['source_id']
    source = edl['sources'][source_id]
    if source['kind'] != 'video':
        raise ValueError('Los candidatos de vídeo requieren una fuente de vídeo registrada')
    transcript = data['transcript']
    if not isinstance(transcript, dict):
        raise ValueError('Se requiere el JSON existente del ASR')
    if transcript.get('source_sha256') and transcript['source_sha256'] != source['sha256']:
        raise ValueError('La huella de fuente declarada por el ASR no coincide con el medio registrado')
    raw = transcript.get('word_timestamps')
    if not isinstance(raw, list) or not 1 <= len(raw) <= 5000:
        raise ValueError('Se requieren de 1 a 5000 word_timestamps reales; no se inventan tiempos desde segmentos')
    offset = number(data.get('time_offset', 0), 0, source['duration'])
    ranges = data.get('processed_ranges')
    if not isinstance(ranges, list) or not 1 <= len(ranges) <= 100:
        raise ValueError('Declara processed_ranges del ASR; ausencia de palabras no prueba cobertura')
    checked = []
    for interval in ranges:
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError('Cobertura requiere pares [inicio, fin] en segundos de la fuente')
        start = number(interval[0], 0, source['duration'])
        end = number(interval[1], start + .001, source['duration'])
        checked.append([start, end])
    merged = []
    for a, b in sorted(checked):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    words = []
    for index, word in enumerate(raw):
        if not isinstance(word, dict) or not isinstance(word.get('word'), str) or not word['word'].strip() or len(word['word']) > 500:
            raise ValueError('Palabra vacía o estructura ASR inválida')
        start = number(word.get('start'), 0, source['duration']) + offset
        end = number(word.get('end'), 0, source['duration']) + offset
        number(end, start, source['duration'])
        if words and start < words[-1]['start']:
            raise ValueError('Palabras fuera de orden; no se reordenan ni corrigen silenciosamente')
        if not any(a <= start and end <= b for a, b in merged):
            raise ValueError('Una palabra queda fuera de la cobertura declarada')
        words.append({**deepcopy(word), 'index': index, 'start': start, 'end': end})
    payload = json.dumps(transcript, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')
    coverage_seconds = sum(b - a for a, b in merged)
    missing = []
    cursor = 0
    for start, end in merged:
        if start > cursor:
            missing.append([cursor, start])
        cursor = end
    if cursor < source['duration']:
        missing.append([cursor, source['duration']])
    dataset = {'id': uuid.uuid4().hex, 'source_id': source_id, 'source_sha256': source['sha256'],
               'transcript_sha256': hashlib.sha256(payload).hexdigest(),
               'transcript_original': deepcopy(transcript), 'words': words,
               'provenance': {'binding': 'explicit_registered_source', 'time_offset': offset,
                              'language': transcript.get('language'), 'model_size': transcript.get('model_size'),
                              'coverage_evidence': 'declared_not_independently_verified'},
               'coverage': {'processed_ranges': merged, 'processed_seconds': coverage_seconds,
                            'unprocessed_ranges': missing,
                            'selection_scope': 'proposed_word_spans_only_not_full_editorial_review',
                            'source_seconds': source['duration'], 'fraction': coverage_seconds / source['duration'],
                            'word_count': len(words), 'complete': coverage_seconds >= source['duration'] - .001},
               'candidates': []}
    proposals = data.get('proposals')
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= 50:
        raise ValueError('Aporta de 1 a 50 propuestas editoriales por índices de palabra y motivo')
    for proposal in proposals:
        if not isinstance(proposal, dict):
            raise ValueError('Propuesta inválida')
        dataset['candidates'].append(candidate(dataset, proposal.get('first_word'), proposal.get('last_word'), proposal.get('reason')))
    return dataset


def apply_candidates(edl, data):
    from lib import studio_editor as edit
    op = data.get('operation')
    if op == 'candidate_import':
        if len(edl.get('candidate_sets', [])) >= 10:
            raise ValueError('Límite de esta entrega: 10 conjuntos de candidatos por proyecto')
        dataset = import_set(edl, data)
        edl.setdefault('candidate_sets', []).append(dataset)
    elif op in ('candidate_propose', 'candidate_review', 'candidate_insert'):
        dataset = edit._item(edl.get('candidate_sets', []), data['set_id'])
        if dataset['source_sha256'] != edl['sources'][dataset['source_id']]['sha256']:
            raise ValueError('La fuente del candidato cambió; vuelve a revisar procedencia')
        if op == 'candidate_propose':
            if len(dataset['candidates']) >= 50:
                raise ValueError('Límite: 50 candidatos por conjunto')
            dataset['candidates'].append(candidate(dataset, data.get('first_word'), data.get('last_word'), data.get('reason')))
            return True
        item = edit._item(dataset['candidates'], data['id'])
        if op == 'candidate_review':
            if data.get('status') not in ('pending', 'accepted', 'rejected'):
                raise ValueError('Estado de revisión desconocido')
            if 'first_word' in data or 'last_word' in data:
                revised = candidate(dataset, data['first_word'], data['last_word'], data.get('reason', item['reason']))
                item.update({**revised, 'id': item['id']})
            if data['status'] == 'accepted' and data.get('context_confirmed') is not True:
                raise ValueError('Confirma revisión de negaciones y contexto antes de aceptar')
            note = data.get('review_note', '')
            if not isinstance(note, str) or len(note) > 2000:
                raise ValueError('Nota de revisión inválida')
            item.update(status=data['status'], context_confirmed=data.get('context_confirmed') is True, review_note=note)
        else:
            if item['status'] != 'accepted' or not item['context_confirmed']:
                raise ValueError('Acepta y revisa el contexto del candidato antes de insertarlo')
            if any(c.get('candidate_ref', {}).get('candidate_id') == item['id'] for c in edl['cuts']):
                raise ValueError('El candidato ya está en el montaje; duplica el clip explícitamente si lo necesitas')
            # Reuse the existing add/trim contract; one enclosing commit/undo.
            edit._apply_edit(edl, {'operation': 'add', 'source_id': dataset['source_id']})
            clip = edl['cuts'][-1]
            edit._apply_edit(edl, {'operation': 'trim', 'id': clip['id'], 'in_seconds': item['start_seconds'], 'out_seconds': item['end_seconds']})
            clip['candidate_ref'] = {'set_id': dataset['id'], 'candidate_id': item['id'],
                                     'transcript_sha256': dataset['transcript_sha256'], 'word_span': list(item['word_span']),
                                     'text': item['text'], 'reason': item['reason']}
    else:
        return False
    return True
