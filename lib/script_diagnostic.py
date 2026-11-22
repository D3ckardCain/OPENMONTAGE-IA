"""Read-only editorial checks on a project's existing script artifact."""
import re
import math

from jsonschema import ValidationError
from schemas.artifacts import validate_artifact
from lib import production_studio as studio


def inspect(pid, words_per_minute=150):
    if type(words_per_minute) is not int or not 80 <= words_per_minute <= 220:
        raise ValueError('Velocidad fuera del rango de 80 a 220 palabras por minuto')
    path = studio.project_path(pid)/'artifacts/script.json'
    if not path.is_file():
        return {'status':'missing','message':'Todavía no hay guion guardado en este proyecto.'}
    if path.is_symlink() or path.stat().st_size > 500000:
        raise ValueError('Guion inválido o demasiado grande')
    script = studio.read_json(path)
    try:
        validate_artifact('script', script)
    except (ValidationError, TypeError) as exc:
        raise ValueError('El guion no cumple el esquema de producción') from exc
    sections = script['sections']
    if len(sections) > 200 or not math.isfinite(script['total_duration_seconds']):
        raise ValueError('Cantidad o duración de secciones inválida')
    rows=[];previous_end=None;ids=set()
    for section in sections:
        identifier=section['id']
        if identifier in ids:raise ValueError('ID de sección repetido')
        ids.add(identifier)
        start,end=section['start_seconds'],section['end_seconds']
        if not math.isfinite(start) or not math.isfinite(end) or end<=start or (previous_end is not None and start<previous_end):
            raise ValueError('Secciones solapadas o con duración inválida')
        words=len(re.findall(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ]+(?:['’][\w]+)?\b",section['text'],re.UNICODE))
        span=end-start
        estimated=round(words*60/words_per_minute,1)
        rows.append({'id':identifier,'label':section.get('label') or identifier,
            'start_seconds':start,'end_seconds':end,'word_count':words,
            'estimated_speech_seconds':estimated,'allocated_seconds':span,
            'speech_overrun_seconds':round(max(0,estimated-span),1),
            'gap_before_seconds':round(start-previous_end,1) if previous_end is not None else round(start,1),
            'has_source_ref':bool(section.get('source_ref','').strip()),
            'has_voice_directions':bool(section.get('speaker_directions','').strip() or section.get('delivery_cues')),
            'has_visual_cues':bool(section.get('enhancement_cues'))})
        previous_end=end
    total=script['total_duration_seconds']
    if previous_end>total:raise ValueError('Secciones exceden la duración total')
    return {'status':'review','title':script['title'],'words_per_minute':words_per_minute,
        'total_duration_seconds':total,'word_count':sum(row['word_count'] for row in rows),
        'estimated_speech_seconds':round(sum(row['estimated_speech_seconds'] for row in rows),1),
        'trailing_gap_seconds':round(total-previous_end,1),'sections':rows,
        'source_ref_missing':sum(not row['has_source_ref'] for row in rows),
        'voice_directions_missing':sum(not row['has_voice_directions'] for row in rows),
        'visual_cues_missing':sum(not row['has_visual_cues'] for row in rows),
        'limits':'La velocidad es una estimación; pausas, locución y edición cambian el tiempo real. Una referencia escrita no verifica un hecho. Revisa afirmaciones, derechos, pronunciación y voz antes de aprobar.'}
