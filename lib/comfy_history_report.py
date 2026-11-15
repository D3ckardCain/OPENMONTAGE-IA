"""Offline summaries of ComfyUI history; never submit or modify jobs.

History proves execution status, not visual quality or decoded media duration.
"""
from __future__ import annotations

import math
import hashlib
import json
import re


def _timestamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return value
    return None


def summarize_history(history: dict) -> list[dict]:
    """Accept the mapping returned by GET /history; do not access the server.

    Elapsed time uses execution_start/success timestamps (milliseconds).
    Missing completion is unknown, never inferred from output previews.
    """
    if not isinstance(history, dict):
        raise ValueError('El historial debe ser un objeto JSON')
    results = []
    for prompt_id, entry in history.items():
        if not isinstance(entry, dict):
            raise ValueError('Entrada de historial inválida')
        status = entry.get('status') or {}
        if not isinstance(status, dict):
            raise ValueError('Estado de historial inválido')
        messages = status.get('messages') or []
        if not isinstance(messages, list):
            raise ValueError('Mensajes de historial inválidos')
        start = end = None
        for message in messages:
            if not isinstance(message, (list, tuple)) or len(message) != 2 or not isinstance(message[1], dict):
                continue
            event, data = message
            stamp = _timestamp(data.get('timestamp'))
            if event == 'execution_start' and stamp is not None:
                start = stamp if start is None else min(start, stamp)
            if event == 'execution_success' and stamp is not None:
                end = stamp if end is None else max(end, stamp)
        failed = status.get('status_str') == 'error' or any(
            isinstance(m, (list, tuple)) and m and m[0] in ('execution_error', 'execution_interrupted')
            for m in messages
        )
        completed = status.get('completed') is True and status.get('status_str') == 'success' and not failed
        artifacts = []
        outputs = entry.get('outputs') or {}
        if not isinstance(outputs, dict):
            raise ValueError('Salidas de historial inválidas')
        for node_id, output in outputs.items():
            if not isinstance(output, dict):
                continue
            for kind in ('images', 'video', 'gifs', 'audio'):
                if not isinstance(output.get(kind) or [], list):
                    raise ValueError('Lista de archivos inválida')
                for item in output.get(kind) or []:
                    if isinstance(item, dict) and isinstance(item.get('filename'), str):
                        artifact = {k: item.get(k, default) for k, default in (
                            ('filename', ''), ('subfolder', ''), ('type', 'output'))}
                        artifact.update(node_id=str(node_id), kind=kind)
                        if artifact not in artifacts:
                            artifacts.append(artifact)
        results.append({
            'prompt_id': str(prompt_id),
            'status': 'failed' if failed else 'completed' if completed else 'unknown',
            'elapsed_seconds': (end - start) / 1000 if completed and start is not None and end is not None and end >= start else None,
            'artifacts': artifacts,
            'visual_quality': 'not_reviewed',
            'media_duration_seconds': None,
            'source': 'comfyui_history',
        })
    return results


def saved_reports(project_id):
    from lib import production_studio as studio
    path = studio.project_path(project_id) / 'comfy_history_reports.json'
    with studio.LOCK:
        return studio.read_json(path, [])


def save_report(project_id, history):
    """Save normalized evidence only; identical imports reuse the same record."""
    from lib import production_studio as studio
    jobs = summarize_history(history)
    if not jobs:
        raise ValueError('El historial no contiene trabajos')
    jobs.sort(key=lambda job: job['prompt_id'])
    digest = hashlib.sha256(json.dumps(jobs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    path = studio.project_path(project_id) / 'comfy_history_reports.json'
    with studio.LOCK:
        reports = studio.read_json(path, [])
        for report in reports:
            if report['id'] == digest:
                return {**report, 'duplicate': True}
        if len(reports) >= 100:
            raise ValueError('El proyecto ya contiene 100 informes; no se borraron registros anteriores')
        report = {'id': digest, 'project_id': project_id, 'imported_at': studio.now(),
                  'source': 'uploaded_history', 'persisted': True, 'jobs': jobs}
        studio.save_json(path, [*reports, report])
        return {**report, 'duplicate': False}


CONTEXT_FIELDS = ('equipment', 'cpu', 'gpu', 'vram', 'ram', 'storage', 'test_conditions')


def annotate_report(project_id, report_id, context):
    """Append user declarations without replacing history-derived evidence."""
    from lib import production_studio as studio
    if not isinstance(context, dict) or set(context) - set(CONTEXT_FIELDS):
        raise ValueError('Campos de ficha desconocidos')
    normalized = {}
    for field in CONTEXT_FIELDS:
        value = context.get(field, '')
        if not isinstance(value, str) or len(value) > 2000:
            raise ValueError('Campo de ficha inválido: ' + field)
        normalized[field] = value.strip()
    if not any(normalized.values()):
        raise ValueError('Completa al menos un dato de la prueba')
    if not re.fullmatch('[a-f0-9]{64}', report_id):
        raise ValueError('Identificador de informe inválido')
    path = studio.project_path(project_id) / 'comfy_history_reports.json'
    with studio.LOCK:
        reports = studio.read_json(path, [])
        for report in reports:
            if report['id'] != report_id:
                continue
            versions = report.setdefault('context_versions', [])
            if versions and versions[-1]['values'] == normalized:
                return report
            if len(versions) >= 100:
                raise ValueError('Se alcanzó el máximo de 100 fichas por informe')
            versions.append({'recorded_at': studio.now(), 'source': 'user_declared',
                             'verified': False, 'values': normalized})
            studio.save_json(path, reports)
            return report
        raise FileNotFoundError('Informe no encontrado en este proyecto')
