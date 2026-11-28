"""Read saved queue timings without estimating speed or starting generation."""
from datetime import datetime

from lib import production_queue as queue
from lib import production_studio as studio
from lib.stage_timing import summarize
from lib.editorial_freshness import current as verification_current,delivery_current,selection_index


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
        approved_stages = []
        first_decisions = {}
        verification_status = None
        final_copy_registered = False
        try:
            if item.get('projects_root',str(studio.PROJECTS_DIR.resolve()))!=str(studio.PROJECTS_DIR.resolve()):
                raise ValueError('Proyecto en otro disco')
            project = studio.project_path(item['project_id'])
            verification=studio.read_json(project/'render_verification.json',{})
            delivery=studio.read_json(project/'final_delivery.json',{})
            usage = studio.read_json(project/'resource_usage.json')
            if history and isinstance(usage,dict):
                recorded=usage.get('recorded_at')
                started=item.get('started_at')
                if not isinstance(recorded,str) or not isinstance(started,str) or recorded<started:
                    usage=None
            reviews = studio.read_json(project/'editorial_reviews.json',[])
            selection=selection_index(project)
            if isinstance(verification,dict):
                verification_status=verification.get('status') if verification_current(verification,reviews,selection) else 'superseded' if verification.get('status')=='passed' else verification.get('status')
            if isinstance(delivery,dict):
                final_copy_registered=delivery_current(verification,delivery,reviews,selection)
            if isinstance(reviews,list):
                for review in reviews:
                    if (isinstance(review,dict) and isinstance(review.get('stage'),str)
                            and review.get('decision') in ('approved','revision_requested')):
                        first_decisions.setdefault(review['stage'],review['decision'])
            request = studio.read_json(project/'production_request.json', {})
            if isinstance(request, dict) and isinstance(request.get('pipeline'), str):
                manifest = studio.load_pipeline_readonly(request['pipeline'])
                for stage in manifest['stages']:
                    name = stage.get('name')
                    if not isinstance(name, str) or not name or name == 'publish':
                        continue
                    checkpoint = studio.read_json(project/('checkpoint_'+name+'.json'), {})
                    if isinstance(checkpoint, dict) and checkpoint.get('status') == 'completed' and checkpoint.get('human_approved') is True:
                        approved_stages.append(name)
            events=studio.read_json(project/'job.json', {}).get('events', [])
            if not history:
                stages=summarize(events,item.get('started_at'),item.get('finished_at'))
            elif isinstance(item.get('started_at'),str):
                stages=summarize(events,item['started_at'],item.get('finished_at'))
        except (OSError, ValueError, TypeError, KeyError):
            pass
        rows.append({'project_id': item['project_id'], 'projects_root':item.get('projects_root',str(studio.PROJECTS_DIR.resolve())), 'title': item.get('title'),
                     'status': item['status'], 'started_at': item.get('started_at'),
                     'finished_at': item.get('finished_at'), 'elapsed_seconds': duration,
                     'message': item.get('message', ''),
                     'progress': item.get('progress'), 'stage_active_seconds': stages,
                     'approved_stages': approved_stages,
                     'verification_status':verification_status,
                     'final_copy_registered':final_copy_registered,
                     'editorial_first_decisions': first_decisions,
                     'resource_usage': usage, 'retry_count_recorded': len(history),
                     'retry_history': history})
    observed = [row['elapsed_seconds'] for row in rows if row['elapsed_seconds'] is not None]
    ram = [row['resource_usage']['host_ram_peak_mb'] for row in rows
           if isinstance(row['resource_usage'],dict) and type(row['resource_usage'].get('host_ram_peak_mb')) is int]
    vram = [row['resource_usage']['gpu_vram_peak_mb'] for row in rows
            if isinstance(row['resource_usage'],dict) and type(row['resource_usage'].get('gpu_vram_peak_mb')) is int]
    prior_usage=[entry.get('resource_usage') for row in rows for entry in row['retry_history']]
    ram.extend(usage['host_ram_peak_mb'] for usage in prior_usage
               if isinstance(usage,dict) and type(usage.get('host_ram_peak_mb')) is int)
    vram.extend(usage['gpu_vram_peak_mb'] for usage in prior_usage
                if isinstance(usage,dict) and type(usage.get('gpu_vram_peak_mb')) is int)
    causes = {}
    for row in rows:
        for entry in row['retry_history']:
            status = entry.get('status')
            if status in ('blocked','stopped','interrupted','awaiting_input','awaiting_human'):
                causes[status] = causes.get(status, 0) + 1
    first_decisions = [decision for row in rows for decision in row['editorial_first_decisions'].values()]
    first_approvals = first_decisions.count('approved')
    saved=studio.read_json(studio.CONFIG_DIR/'production_pilots.json',[])
    frozen=saved[-1] if isinstance(saved,list) and saved and isinstance(saved[-1],dict) else None
    current_root=str(studio.PROJECTS_DIR.resolve())
    valid_frozen=(frozen and frozen.get('projects_root')==current_root and
                  isinstance(frozen.get('project_ids'),list) and len(frozen['project_ids'])==10)
    if valid_frozen:
        by_id={row['project_id']:row for row in rows if row['projects_root']==current_root}
        pilot=[by_id[pid] for pid in frozen['project_ids'] if pid in by_id]
        missing=sum(pid not in by_id for pid in frozen['project_ids'])
    else:
        pilot=rows[:10]
        missing=0
    finished=[row for row in pilot if row['status']=='completed']
    pilot_ram=[usage['host_ram_peak_mb'] for row in pilot
               for usage in [row['resource_usage'],*(entry.get('resource_usage') for entry in row['retry_history'])]
               if isinstance(usage,dict) and type(usage.get('host_ram_peak_mb')) is int]
    pilot_vram=[usage['gpu_vram_peak_mb'] for row in pilot
                for usage in [row['resource_usage'],*(entry.get('resource_usage') for entry in row['retry_history'])]
                if isinstance(usage,dict) and type(usage.get('gpu_vram_peak_mb')) is int]
    pilot_decisions=[decision for row in pilot for decision in row['editorial_first_decisions'].values()]
    pilot_report={
        'target_projects':10,'queue_projects_considered':len(pilot),
        'queue_projects_total':len(rows),
        'projects':[{'project_id':row['project_id'],'title':row['title'],'status':row['status']} for row in pilot],
        'missing_from_queue':missing,
        'saved_pilot_on_other_root':bool(frozen and frozen.get('projects_root')!=current_root),
        'frozen':bool(valid_frozen),'frozen_at':frozen.get('created_at') if valid_frozen else None,
        'completed':len(finished),
        'blocked_or_waiting':sum(row['status'] in ('blocked','interrupted','awaiting_input','awaiting_human','stopped') for row in pilot),
        'completed_with_duration':sum(row['elapsed_seconds'] is not None for row in finished),
        'completed_with_ram':sum(isinstance(row['resource_usage'],dict) and type(row['resource_usage'].get('host_ram_peak_mb')) is int for row in finished),
        'completed_with_vram':sum(isinstance(row['resource_usage'],dict) and type(row['resource_usage'].get('gpu_vram_peak_mb')) is int for row in finished),
        'completed_with_render_verification':sum(row['verification_status']=='passed' for row in finished),
        'completed_with_final_copy':sum(row['final_copy_registered'] for row in finished),
        'completed_elapsed_seconds_total':round(sum(row['elapsed_seconds'] for row in finished if row['elapsed_seconds'] is not None),3),
        'ram_peak_mb':max(pilot_ram) if pilot_ram else None,
        'vram_peak_mb':max(pilot_vram) if pilot_vram else None,
        'retries_recorded':sum(row['retry_count_recorded'] for row in pilot),
        'editorial_first_decisions_count':len(pilot_decisions),
        'first_pass_approval_rate':round(pilot_decisions.count('approved')/len(pilot_decisions),3) if pilot_decisions else None,
        'scope':'fixed_ten_project_cohort' if valid_frozen else 'first_ten_current_queue_records_not_a_frozen_cohort',
    }
    pilot_report['measurements_complete']=(len(pilot)==10 and len(finished)==10 and
        pilot_report['completed_with_duration']==10 and pilot_report['completed_with_ram']==10 and
        pilot_report['completed_with_vram']==10)
    return {'queue_status': state['status'], 'projects': rows,
            'pilot_candidate':pilot_report,
            'completed_runs_measured': len(observed),
            'elapsed_seconds_total': round(sum(observed), 3),
            'ram_peak_mb': max(ram) if ram else None, 'vram_peak_mb': max(vram) if vram else None,
            'retries_recorded': sum(row['retry_count_recorded'] for row in rows),
            'retry_causes_by_status': causes,
            'approved_stage_count': sum(len(row['approved_stages']) for row in rows),
            'editorial_first_decisions_count':len(first_decisions),
            'first_pass_approval_rate':round(first_approvals/len(first_decisions),3) if first_decisions else None,
            'generation_started': False, 'estimate_48_per_week': None,
            'note': 'La cola mide inicio-fin del intento actual con esperas. Las etapas muestran tiempo activo del intento actual; los históricos desde esta versión conservan su propio desglose. La tasa editorial usa la primera decisión explícita registrada por etapa; no incluye etapas sin decisión ni datos anteriores a este registro. Las aprobaciones automáticas no cuentan. Las causas de reintento agrupan estados guardados. Los máximos RAM y VRAM incluyen muestras guardadas de intentos previos; son del equipo y GPU completos, no atribuibles al proyecto. No predice capacidad semanal.'}
