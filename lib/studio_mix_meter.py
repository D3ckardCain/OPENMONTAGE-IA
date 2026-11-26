"""Bounded, cached analysis of the current encoded final mix. Never renders."""
from copy import deepcopy
import math
import re
import threading

from lib import production_studio as studio, studio_editor as edit, studio_editor_render as render
from lib.media_executables import require_media
from lib.studio_render_process import Control, Cancelled, execute

CONTRACT = 'encoded-final-mix-meter-v1'
ACTIVE = {}


def _rid(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', value):
        raise ValueError('Identificador de medición inválido')
    return value


def _path(pid, rid):
    return studio.project_path(pid)/'artifacts/mix_meter/requests'/(_rid(rid)+'.json')


def _identity(path):
    stat = path.stat()
    return dict(bytes=stat.st_size, mtime_ns=stat.st_mtime_ns, device=stat.st_dev, inode=stat.st_ino)


def parse(stderr):
    text = stderr.decode('utf-8', 'replace') if isinstance(stderr, bytes) else stderr
    def value(pattern, source=text):
        found = re.findall(pattern, source)
        if not found:
            raise ValueError('FFmpeg no devolvió las métricas esperadas')
        number = float(found[-1])
        if number == -math.inf:
            return None  # Silence, never a JSON infinity or a fictitious 0 dB.
        if not math.isfinite(number):
            raise ValueError('Métrica no finita de FFmpeg')
        return number
    overall = text.rsplit('Overall', 1)[-1]
    result = {'rms_dbfs':value(r'RMS level dB:\s*([-+\w.]+)',overall),
              'sample_peak_dbfs':value(r'Peak level dB:\s*([-+\w.]+)',overall),
              'true_peak_dbfs':value(r'True peak:\s*\n\s*Peak:\s*([-+\w.]+)'),
              'integrated_lufs':value(r'Integrated loudness:\s*\n\s*I:\s*([-+\w.]+)'),
              'loudness_range_lu':value(r'Loudness range:\s*\n\s*LRA:\s*([-+\w.]+)'),
              'samples_per_channel':int(value(r'Number of samples:\s*([\d.]+)',overall))}
    result['loudness_below_gate'] = result['integrated_lufs'] is None or result['integrated_lufs'] <= -70
    result['sample_peak_at_or_above_full_scale'] = result['sample_peak_dbfs'] is not None and result['sample_peak_dbfs'] >= 0
    result['true_peak_above_full_scale'] = result['true_peak_dbfs'] is not None and result['true_peak_dbfs'] > 0
    return result


def status(pid, request_id):
    with studio.LOCK:
        value = studio.read_json(_path(pid,request_id))
        if value is None:
            raise FileNotFoundError('No existe recibo de esta medición; no se reenvía automáticamente')
        value = deepcopy(value)
        if value['status'] in ('running','cancelling') and pid not in ACTIVE:
            value.update(status='interrupted',error='Servidor reiniciado; medición incompleta, sin reintento automático')
        current = render.status(pid)
        value['current'] = bool(current.get('current') and current.get('path')==value['source']['path']
                                and current.get('sha256')==value['source']['sha256'])
        if value['current']:
            try:
                value['current'] = _identity(edit.media_path(studio.project_path(pid),value['source']['path'])) == value['source']['identity']
            except (OSError,ValueError):
                value['current'] = False
        return value


def start(pid, data, origin='user'):
    if origin not in ('user','agent') or not isinstance(data,dict) or set(data)-{'request_id','revision','start_seconds','duration_seconds'}:
        raise ValueError('Solicitud de medición no admitida')
    rid = _rid(data.get('request_id'))
    intent = edit.edit_digest(data)
    with studio.LOCK:
        old=studio.read_json(_path(pid,rid))
        if old:
            if old['intent']!=intent:raise edit.Conflict('El identificador ya corresponde a otra solicitud')
            return status(pid,rid)
    with edit.guard(pid,origin):
        old = studio.read_json(_path(pid,rid))
        if old:
            if old['intent'] != intent:
                raise edit.Conflict('El identificador ya corresponde a otra solicitud')
            return status(pid,rid)
        state=edit.state(pid);edit._revision(state,data.get('revision'));saved=render.status(pid)
        if saved.get('status')!='completed' or not saved.get('current') or not saved.get('sha256'):
            raise edit.Conflict('Prepara un montaje vigente antes de medir: no se renderiza automáticamente')
        total=edit.number(saved['duration'],.001,7200)
        start_at=edit.number(data.get('start_seconds',0),0,max(0,total-.001))
        seconds=edit.number(data.get('duration_seconds',min(120,total-start_at)),.001,min(120,total-start_at))
        path=edit.media_path(studio.project_path(pid),saved['path'])
        source={'path':saved['path'],'sha256':saved['sha256'],'identity':_identity(path),
                'render_sha256':state['render_sha256'],'preview':saved.get('preview',False)}
        executable=require_media('ffmpeg')
        from pathlib import Path
        engine={'path':str(executable),'identity':_identity(Path(executable))}
        coverage={'start_seconds':start_at,'duration_seconds':seconds,'total_seconds':total,
                  'partial':start_at>0 or seconds<total,'clock':'encoded render seconds'}
        key=edit.edit_digest({'source':source,'coverage':coverage,'engine':engine,'contract':CONTRACT})
        cache=studio.project_path(pid)/'artifacts/mix_meter/cache'/(key+'.json')
        cached=studio.read_json(cache)
        job={'request_id':rid,'intent':intent,'contract':CONTRACT,'status':'completed' if cached else 'running',
             'source':source,'engine':engine,'coverage':coverage,'origin':origin,'measurement_origin':origin,
             'created_at':studio.now(),'cache_hit':bool(cached)}
        if cached:
            job.update(metrics=cached['metrics'],completed_at=cached['completed_at'])
        else:
            if pid in ACTIVE or len(ACTIVE)>=2:
                raise edit.Conflict('Ya hay una medición activa; recupera su recibo antes de iniciar otra')
            control=Control(rid)
        studio.save_json(_path(pid,rid),job)
        if not cached:
            ACTIVE[pid]=(rid,control)
            edit.EXPORTING.add(pid)  # Existing queue/runtime guards see this owned read task.
            try:
                threading.Thread(target=_worker,args=(pid,job,path,cache,control),daemon=True).start()
            except Exception as exc:
                try:
                    job.update(status='failed',error='No se pudo iniciar la medición: '+str(exc))
                    studio.save_json(_path(pid,rid),job)
                finally:
                    ACTIVE.pop(pid,None);edit.EXPORTING.discard(pid)
                raise ValueError(job['error']) from exc
        return status(pid,rid)


def cancel(pid, rid):
    with studio.LOCK:
        job=status(pid,rid)
        if job['status'] in ('completed','cancelled','failed','interrupted'):
            return job
        owner=ACTIVE.get(pid)
        if not owner or owner[0]!=rid:
            raise edit.Conflict('La medición cambió; consulta su recibo')
        job.update(status='cancelling',cancel_requested_at=studio.now());studio.save_json(_path(pid,rid),job)
        owner[1].event.set()
        return job


def _worker(pid, job, path, cache, control):
    try:
        # Same owned-child termination/kill and bounded stderr as the renderer.
        command=[job['engine']['path'],'-nostdin','-nostats','-v','info',*edit.INPUT_OPTIONS,
                 '-ss',str(job['coverage']['start_seconds']),'-i',str(path),'-t',str(job['coverage']['duration_seconds']),
                 '-map','0:a:0','-vn','-sn','-dn','-af',
                 'aresample=48000,ebur128=peak=true:framelog=verbose,'
                 'astats=metadata=0:reset=0:measure_perchannel=none:measure_overall=Peak_level+RMS_level+Number_of_samples',
                 '-f','null','-']
        result=execute(command,path.parent,control,timeout=60)
        control.check()
        if result.returncode:
            raise ValueError('FFmpeg no pudo medir la mezcla: '+result.stderr.decode('utf-8','replace')[-500:])
        metrics=parse(result.stderr)
        if _identity(path)!=job['source']['identity']:
            raise edit.Conflict('El render cambió durante la lectura; no se publica esta medición')
        if abs(metrics['samples_per_channel']/48000-job['coverage']['duration_seconds'])>.05:
            raise ValueError('La lectura no cubrió el intervalo completo solicitado')
        control.check();job.update(status='completed',metrics=metrics,completed_at=studio.now())
    except Cancelled:
        job.update(status='cancelled',completed_at=studio.now(),error='Medición cancelada; no se publica resultado')
    except Exception as exc:
        job.update(status='failed',completed_at=studio.now(),error=str(exc))
    finally:
        with studio.LOCK:
            persisted=studio.read_json(_path(pid,job['request_id']),{})
            if persisted.get('cancel_requested_at'):
                job['cancel_requested_at']=persisted['cancel_requested_at']
            job.update(decoder_started=control.process is not None,process_stopped=control.stopped)
            if control.event.is_set() and control.stopped:
                job.update(status='cancelled',error='Medición cancelada; proceso propio detenido')
                job.pop('metrics',None)
            stopped=control.process is None or control.process.poll() is not None
            if not stopped:
                job.update(status='failed',error='No se confirmó cierre del decodificador propio; proyecto bloqueado para inspección')
                job.pop('metrics',None)
            try:
                if job['status']=='completed':studio.save_json(cache,{'metrics':job['metrics'],'completed_at':job['completed_at']})
                studio.save_json(_path(pid,job['request_id']),job)
            finally:
                if stopped:
                    ACTIVE.pop(pid,None)
                    edit.EXPORTING.discard(pid)
