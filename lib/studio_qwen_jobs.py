"""Bounded Qwen previews on the existing native worker and owned-child control.

One explicit request, no scheduler, automatic retry, weight download or fallback.
"""
from copy import deepcopy
import array
import json
import math
import os
from pathlib import Path
import re
import threading
import wave

from lib import production_studio as studio, studio_editor as editor
from lib import qwen_tts_local as qwen
from lib.bg_remove_local import checksum
from lib.studio_render_process import Control, Cancelled

ACTIVE = {}


class QwenControl(Control):
    def check(self):
        if self.event.is_set():
            raise Cancelled('Preescucha cancelada; no se publica la salida parcial')


def _paths(pid, key):
    if not isinstance(key, str) or not re.fullmatch('[a-f0-9]{32}', key):
        raise ValueError('request_id debe ser 32 caracteres hexadecimales minúsculos')
    project = studio.project_path(pid)
    folder = project / 'artifacts/qwen_previews'
    folder.resolve().relative_to(project.resolve())
    path, claim = folder / (key + '.json'), folder / 'active.claim'
    if path.is_symlink() or claim.is_symlink():
        raise ValueError('Registro enlazado no permitido')
    return project, path, claim


def _inputs(edl, data):
    temporary = deepcopy(edl)
    qwen.save_plan(temporary, data)
    plan = temporary['qwen_tts_plan']
    if len(plan['text']) > 300:
        raise ValueError('Preescucha acotada: máximo300caracteres; el plan puede conservar más')
    device = data.get('device', 'cuda')
    if device not in ('cpu', 'cuda'):
        raise ValueError('Dispositivo Qwen desconocido')
    tokens = data.get('max_new_tokens', 128)
    seed = data.get('seed', 42)
    if type(tokens) is not int or not 8 <= tokens <= 256:
        raise ValueError('Presupuesto de preescucha:8–256tokens nuevos')
    if type(seed) is not int or not 0 <= seed <= 2147483647:
        raise ValueError('Semilla fuera de límites')
    return {**plan, 'device': device, 'max_new_tokens': tokens, 'seed': seed}


def _fingerprint(inputs, info):
    from lib.qwen_tts_runtime import binding
    runtime = binding(info['python_executable'])
    spec = qwen.PROFILES[inputs['profile']]
    value = {'contract': 'qwen-preview-v1', 'inputs': inputs,
             'main_sha256': spec['main_sha256'], 'tokenizer_sha256': qwen.TOKEN_SHA,
             'official_revision': spec['revision'], 'model_license': 'Apache-2.0',
             'model_card': 'https://huggingface.co/Qwen/' + spec['folder'].replace('Qwen--', '') + '/blob/' + spec['revision'] + '/README.md',
             'runtime': runtime,
             'worker_sha256': checksum(Path(__file__).with_name('model_adapter_worker.py')),
             'adapter_sha256': checksum(Path(__file__).with_name('model_adapters.py'))}
    return editor.edit_digest(value), value


def _result(project, record):
    result = record['result']
    output = editor.media_path(project, result['relative_path'])
    receipt_path = Path(str(output) + '.json')
    if output.stat().st_size > 10000000 or receipt_path.is_symlink() or receipt_path.stat().st_size > 64000:
        raise ValueError('Salida/recibo fuera de presupuesto o enlazado')
    if checksum(output) != result['wave_sha256'] or checksum(receipt_path) != record['receipt_sha256']:
        raise ValueError('Cambió el WAV o recibo completado; no se reutiliza como éxito')
    receipt = studio.read_json(receipt_path)
    if receipt.get('fingerprint') != record['fingerprint']:
        raise ValueError('Recibo no corresponde a la solicitud')
    return {**result, 'url': '/media/' + record['project_id'] + '/' + result['relative_path']}


def status(pid, request_id):
    with studio.LOCK:
        project, path, _ = _paths(pid, request_id)
        if path.is_file() and path.stat().st_size > 64000:
            raise ValueError('Registro Qwen fuera de presupuesto')
        record = studio.read_json(path)
        if not record:
            raise FileNotFoundError('Solicitud Qwen no encontrada')
        if (not isinstance(record, dict) or record.get('request_id') != request_id
                or record.get('project_id') != pid or not isinstance(record.get('inputs'), dict)
                or record.get('relative_work') != 'assets/audio/qwen/' + request_id):
            raise ValueError('Registro de solicitud Qwen inválido')
        value = deepcopy(record)
        control = ACTIVE.get((pid, request_id))
        if value['state'] in ('running', 'cancelling') and control is None:
            value.update(state='interrupted', error='Servidor cambiado; salida y cierre del worker sin acreditar. No se repite automáticamente.')
        progress = project / value['relative_work'] / 'progress.json'
        if progress.is_file() and progress.stat().st_size <= 64000:
            try:
                value['progress'] = json.loads(progress.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                value['progress_warning'] = 'Progreso no legible; no se infiere finalización'
        if value['state'] == 'completed':
            try:
                value['result'] = _result(project, record)
            except (ValueError, OSError, KeyError) as exc:
                value.update(state='invalid', error=str(exc))
        if control and control.process is not None:
            value['worker_pid'] = control.process.pid
        return value


def requests(pid):
    project = studio.project_path(pid)
    folder = project / 'artifacts/qwen_previews'
    folder.resolve().relative_to(project.resolve())
    paths = sorted(folder.glob('*.json'), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    rows = []
    for path in paths[:20]:
        if path.is_symlink() or not re.fullmatch('[a-f0-9]{32}', path.stem) or path.stat().st_size > 64000:
            continue
        record = studio.read_json(path, {})
        if not isinstance(record, dict) or not isinstance(record.get('inputs'), dict):
            continue
        rows.append({'request_id': path.stem, 'state': record.get('state'),
                     'profile': record['inputs'].get('profile'), 'started_at': record.get('started_at')})
    return {'rows': rows, 'note': 'Índice guardado; abrir una solicitud reconcilia estado y salida. No inicia síntesis.'}


def start(pid, data, origin='user'):
    from lib.model_adapters import diagnostics
    key = data.get('request_id')
    project, path, claim = _paths(pid, key)
    with editor.guard(pid, origin):
        value = editor.state(pid)
        editor._revision(value, data.get('revision'))
        inputs = _inputs(value['edit_decisions'], data)
        if path.exists():
            current = status(pid, key)
            if {k: v for k, v in current['inputs'].items() if k != 'reference_audio'} != inputs:
                raise editor.Conflict('request_id pertenece a otras entradas; no se sustituye')
            return {**current, 'reused_request': True}
        if ACTIVE or claim.exists():
            raise editor.Conflict('Existe una preescucha Qwen activa o sin reconciliar; consulta su estado')
        info = diagnostics(inputs['profile'], device=inputs['device'])
        if not info['ready']:
            raise ValueError('; '.join(info['problems']))
        if inputs['function'] == 'authorized_voice_clone':
            source = value['edit_decisions']['sources'][inputs['reference_source_id']]
            reference = editor.source(pid, inputs['reference_source_id'])
            if source['duration'] > 30 or reference.stat().st_size > 10000000:
                raise ValueError('Referencia de preescucha: hasta30s/10MB')
            if checksum(reference) != inputs['reference_sha256']:
                raise editor.Conflict('Cambió la referencia; vuelve a registrarla')
            inputs['reference_audio'] = str(reference)
        fingerprint, provenance = _fingerprint(inputs, info)
        relative = 'assets/audio/qwen/' + key
        work = project / relative
        work.resolve().relative_to(project.resolve())
        if work.exists():
            raise editor.Conflict('La carpeta de esta solicitud ya existe; no se sobrescribe')
        path.parent.mkdir(parents=True, exist_ok=True)
        with claim.open('x', encoding='utf-8') as stream:
            json.dump({'request_id': key, 'server_pid': os.getpid()}, stream)
        record = dict(contract='qwen-preview-v1', project_id=pid, request_id=key,
                      state='running', inputs=inputs, fingerprint=fingerprint,
                      provenance=provenance, relative_work=relative, started_at=studio.now(),
                      server_pid=os.getpid(), origin=origin)
        control = QwenControl(key)
        try:
            studio.save_json(path, record)
        except Exception:
            if studio.read_json(claim, {}).get('request_id') == key:
                claim.unlink(missing_ok=True)
            raise
        ACTIVE[(pid, key)] = control
        editor.EXPORTING.add(pid)
        response = deepcopy(record)
        try:
            threading.Thread(target=_worker, args=(pid, key, record, control), daemon=True).start()
        except RuntimeError:
            ACTIVE.pop((pid, key), None)
            editor.EXPORTING.discard(pid)
            claim.unlink(missing_ok=True)
            record.update(state='failed', error='No se pudo iniciar el worker', completed_at=studio.now())
            studio.save_json(path, record)
            raise
        return response


def cancel(pid, request_id, origin='user'):
    with studio.LOCK:
        _, path, _ = _paths(pid, request_id)
        record = studio.read_json(path)
        control = ACTIVE.get((pid, request_id))
        if record and record['state'] == 'cancelled':
            return status(pid, request_id)
        if not control or not record or record['state'] not in ('running', 'cancelling'):
            raise editor.Conflict('Este servidor no posee un worker activo de esa solicitud')
        record.update(state='cancelling', cancel_origin=origin, cancel_requested_at=studio.now(),
                      worker_alive_at_request=control.process is not None and control.process.poll() is None)
        studio.save_json(path, record)
        control.event.set()
        return record


def run_native(inputs, work, control):
    from tools.tool_registry import registry
    registry.ensure_discovered('tools.models')
    tool = registry.get('model_' + inputs['profile'].replace('-', '_'))
    if tool is None:
        raise ValueError('Adaptador Qwen no registrado')
    payload = {key: inputs[key] for key in ['text', 'language', 'device', 'max_new_tokens', 'seed']}
    if inputs['function'] == 'voice_design':
        payload['instruction'] = inputs['instruction']
    else:
        payload.update(reference_audio=inputs['reference_audio'], reference_text=inputs['reference_text'],
                       reference_authorized=inputs['reference_authorized'])
    return tool.execute({**payload, 'output_dir': str(work.resolve()), 'timeout': 300}, control=control)


def _worker(pid, key, record, control):
    project, path, claim = _paths(pid, key)
    try:
        work = project / record['relative_work']
        work.mkdir(parents=True, exist_ok=False)
        control.check()
        result = run_native(record['inputs'], work, control)
        control.check()
        if not result.success:
            raise ValueError(result.error or 'Qwen no devolvió una salida válida')
        output = work / 'voice.wav'
        if output.stat().st_size > 10000000:
            raise ValueError('La preescucha excede10MB')
        with wave.open(str(output), 'rb') as stream:
            frames, rate = stream.getnframes(), stream.getframerate()
            if not frames or not 8000 <= rate <= 96000 or stream.getnchannels() != 1:
                raise ValueError('WAV mono de preescucha no válido')
            if stream.getsampwidth() != 2 or frames / rate > 30:
                raise ValueError('WAV debe ser PCM16 y durar hasta30s')
            raw = stream.readframes(frames + 1)
            if len(raw) != frames * 2:
                raise ValueError('WAV parcial')
            samples = array.array('h')
            samples.frombytes(raw)
            import sys
            if sys.byteorder != 'little':
                samples.byteswap()
            peak = max(abs(sample) for sample in samples)
            rms = math.sqrt(sum(sample * sample for sample in samples) / frames)
            if peak < 16 or rms < 8:
                raise ValueError('Salida sin señal suficiente; no se acredita voz')
        receipt = dict(contract='qwen-preview-v1', fingerprint=record['fingerprint'],
                       inputs=record['inputs'], provenance=record['provenance'],
                       wave_sha256=checksum(output), frames=frames, sample_rate=rate,
                       duration_seconds=frames / rate, worker=result.data,
                       peak_pcm16=peak, rms_pcm16=rms,
                       listening_verified=False, cost_usd=0)
        receipt_path = Path(str(output) + '.json')
        studio.save_json(receipt_path, receipt)
        with studio.LOCK:
            control.check()
            record.update(state='completed', completed_at=studio.now(),
                          receipt_sha256=checksum(receipt_path),
                          result=dict(relative_path=output.relative_to(project).as_posix(),
                                      wave_sha256=receipt['wave_sha256'], duration_seconds=frames / rate,
                                      sample_rate=rate, listening_verified=False,
                                      execution={key: result.data.get(key) for key in ['device', 'dtype', 'forward_count', 'gpu_peak_allocated_bytes', 'gpu_peak_reserved_bytes']}))
    except Exception as exc:
        record.update(state='failed', error=str(exc)[:1800], completed_at=studio.now())
    finally:
        with studio.LOCK:
            persisted = studio.read_json(path, {})
            for field in ('cancel_origin', 'cancel_requested_at', 'worker_alive_at_request'):
                if field in persisted:
                    record[field] = persisted[field]
            record.update(worker_started=control.process is not None,
                          owned_worker_pid=control.process.pid if control.process is not None else None,
                          worker_exited=control.process is None or control.stopped,
                          termination_requested=control.terminated)
            if control.event.is_set():
                exited = control.process is None or control.stopped
                progress = studio.read_json(project / record['relative_work'] / 'progress.json', {})
                record.update(state='cancelled' if exited else 'failed',
                              worker_started=control.process is not None, worker_exited=exited,
                              inference_observed=progress.get('forward_count', 0) > 0,
                              inference_stop_confirmed=bool(control.terminated and control.stopped and progress.get('forward_count', 0) > 0
                                  and progress.get('worker_pid') == control.process.pid),
                              error='Worker detenido; parcial no publicado' if exited else 'Cierre no confirmado; proyecto permanece bloqueado')
                record.pop('result', None)
                record.pop('receipt_sha256', None)
            studio.save_json(path, record)
            if control.process is None or control.stopped:
                ACTIVE.pop((pid, key), None)
                editor.EXPORTING.discard(pid)
                if studio.read_json(claim, {}).get('request_id') == key:
                    claim.unlink(missing_ok=True)
