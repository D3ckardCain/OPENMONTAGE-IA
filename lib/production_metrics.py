"""Read saved queue timings without estimating speed or starting generation."""
from datetime import datetime

from lib import production_queue as queue


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
        rows.append({'project_id': item['project_id'], 'title': item.get('title'),
                     'status': item['status'], 'started_at': item.get('started_at'),
                     'finished_at': item.get('finished_at'), 'elapsed_seconds': duration,
                     'message': item.get('message', ''),
                     'progress': item.get('progress')})
    observed = [row['elapsed_seconds'] for row in rows if row['elapsed_seconds'] is not None]
    return {'queue_status': state['status'], 'projects': rows,
            'completed_runs_measured': len(observed),
            'elapsed_seconds_total': round(sum(observed), 3),
            'ram_peak_mb': None, 'vram_peak_mb': None,
            'generation_started': False, 'estimate_48_per_week': None,
            'note': 'Duración entre inicio y fin registrados por la cola; incluye esperas y no mide cada etapa. No equivale a tiempo de GPU ni predice capacidad semanal.'}
