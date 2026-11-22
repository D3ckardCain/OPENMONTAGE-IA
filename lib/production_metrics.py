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
        history = item.get('retry_history', [])
        if not isinstance(history, list):
            history = []
        history = [entry for entry in history if isinstance(entry, dict)][-20:]
        duration = _seconds(item.get('started_at'), item.get('finished_at'))
        stages = {}
        usage = None
        try:
            project = studio.project_path(item['project_id'])
            usage = studio.read_json(project/'resource_usage.json')
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
                     'progress': item.get('progress'), 'stage_active_seconds': stages,
                     'resource_usage': usage, 'retry_count_recorded': len(history),
                     'retry_history': history})
    observed = [row['elapsed_seconds'] for row in rows if row['elapsed_seconds'] is not None]
    ram = [row['resource_usage']['host_ram_peak_mb'] for row in rows
           if isinstance(row['resource_usage'],dict) and type(row['resource_usage'].get('host_ram_peak_mb')) is int]
    vram = [row['resource_usage']['gpu_vram_peak_mb'] for row in rows
            if isinstance(row['resource_usage'],dict) and type(row['resource_usage'].get('gpu_vram_peak_mb')) is int]
    return {'queue_status': state['status'], 'projects': rows,
            'completed_runs_measured': len(observed),
            'elapsed_seconds_total': round(sum(observed), 3),
            'ram_peak_mb': max(ram) if ram else None, 'vram_peak_mb': max(vram) if vram else None,
            'retries_recorded': sum(row['retry_count_recorded'] for row in rows),
            'generation_started': False, 'estimate_48_per_week': None,
            'note': 'La cola mide inicio-fin con esperas. Las etapas muestran tiempo activo hasta cada checkpoint. RAM es del equipo completo y VRAM de la GPU NVIDIA más ocupada, muestreadas durante el último intento; no se atribuyen al proyecto. Los picos entre muestras pueden faltar. No predice capacidad semanal.'}
