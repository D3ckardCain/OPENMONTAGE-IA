"""Read saved queue timings without estimating speed or starting generation."""
from datetime import datetime

from lib import production_queue as queue
from lib import production_studio as studio


def _seconds(start, end):
    try:
        first, last = datetime.fromisoformat(start), datetime.fromisoformat(end)
        if first.tzinfo is None or last.tzinfo is None:
            return None
        elapsed = (last - first).total_seconds()
        return round(elapsed, 3) if elapsed >= 0 else None
    except (TypeError, ValueError):
        return None


def snapshot():
    state = queue.read()
    rows = []
    for item in state['items']:
        duration = _seconds(item.get('started_at'), item.get('finished_at'))
        stages = {}
        try:
            project = studio.project_path(item['project_id'])
            for event in studio.read_json(project/'job.json', {}).get('events', []):
                if event.get('kind') != 'stage_timing':
                    continue
                stage, elapsed = event.get('stage'), event.get('elapsed_seconds')
                if (not isinstance(stage, str) or not stage or type(elapsed) not in (int,float)
                        or not 0 <= elapsed <= 86400):
                    continue
                stages[stage] = round(stages.get(stage, 0) + elapsed, 3)
        except (OSError, ValueError, TypeError, KeyError):
            pass
        rows.append({'project_id': item['project_id'], 'title': item.get('title'),
                     'status': item['status'], 'started_at': item.get('started_at'),
                     'finished_at': item.get('finished_at'), 'elapsed_seconds': duration,
                     'message': item.get('message', ''),
                     'progress': item.get('progress'), 'stage_active_seconds': stages})
    observed = [row['elapsed_seconds'] for row in rows if row['elapsed_seconds'] is not None]
    return {'queue_status': state['status'], 'projects': rows,
            'completed_runs_measured': len(observed),
            'elapsed_seconds_total': round(sum(observed), 3),
            'ram_peak_mb': None, 'vram_peak_mb': None,
            'generation_started': False, 'estimate_48_per_week': None,
            'note': 'La cola mide inicio-fin con esperas. Las etapas muestran tiempo activo del productor al cerrar un checkpoint; pueden faltar sesiones antiguas o interrumpidas. No equivale a tiempo de GPU ni predice capacidad semanal.'}
