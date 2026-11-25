"""Recover one explicit Piper request from evidence; never retry uncertain work."""
import hashlib
import json
import os
import re
import wave
from pathlib import Path
from lib import production_studio as studio, studio_editor as editor, studio_piper as piper
from lib.bg_remove_local import checksum

ACTIVE = set()  # Same lock as editor/Studio; not a second queue or scheduler.


def _key(value):
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{32}', value):
        raise ValueError('request_id debe ser 32 dígitos hexadecimales minúsculos')
    return value


def _paths(pid, key):
    project = studio.project_path(pid)
    folder = project/'artifacts'/'piper_previews'
    folder.resolve().relative_to(project.resolve())
    return project, folder/(key+'.json'), folder/(key+'.claim')


def _fingerprint(inputs):
    voice = next((v for v in piper.catalog() if v['id'] == inputs['voice']), None)
    if not voice or not voice['available'] or voice['blocked']:
        raise ValueError('Paquete Piper no disponible o bloqueado')
    text, speaker = inputs['text'], inputs['speaker_id']
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:
        raise ValueError('Texto requerido: 1 a 1000 caracteres')
    if type(speaker) is not int or speaker not in voice['speakers'].values():
        raise ValueError('Hablante no pertenece a esta voz')
    cfg = piper.configuration()
    folder = Path(cfg['voices_root'])/inputs['voice']
    files = {}
    for item in voice['files']:
        path = folder/item['name']
        actual = checksum(path)
        if actual != item['sha256']:
            raise ValueError('Cambió un recurso Piper: '+item['name'])
        files[item['name']] = actual
    python = Path(cfg['python'])
    # Explicit scope: executable, package metadata and worker code, not a full env audit.
    metadata = sorted((python.parent.parent/'Lib'/'site-packages').glob('*.dist-info/METADATA'))
    runtime = {str(path.resolve()): checksum(path) for path in [python, *metadata,
               Path(piper.__file__), Path(__file__), Path(__file__).with_name('piper_worker.py')]}
    value = dict(contract=1, inputs=inputs, files=files, runtime=runtime, revision=voice['revision'])
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def _receipt(project, record):
    output = editor.media_path(project, record['relative_path'])
    receipt_path = Path(str(output)+'.json')
    if receipt_path.is_symlink():
        raise ValueError('Recibo enlazado no permitido')
    receipt = studio.read_json(receipt_path)
    inputs = record['inputs']
    expected_text = hashlib.sha256(inputs['text'].encode('utf-8')).hexdigest()
    if not isinstance(receipt,dict) or receipt.get('text_sha256') != expected_text or receipt.get('speaker_id') != inputs['speaker_id']:
        raise ValueError('Recibo incompleto o incompatible con esta solicitud')
    if Path(receipt.get('output','')).resolve() != output.resolve():
        raise ValueError('El recibo corresponde a otra salida')
    if receipt.get('wave_sha256') != checksum(output):
        raise ValueError('Cambió el WAV completado')
    provenance = receipt.get('provenance')
    if not isinstance(provenance,dict) or provenance.get('id') != inputs['voice']:
        raise ValueError('El recibo corresponde a otra voz')
    try:
        with wave.open(str(output),'rb') as stream:
            if not stream.getnframes() or stream.getnframes()!=receipt.get('frames') or stream.getframerate()!=receipt.get('sample_rate'):
                raise ValueError('WAV/recibo no coherentes')
            expected = stream.getnframes()*stream.getnchannels()*stream.getsampwidth()
            actual = 0
            while chunk := stream.readframes(65536):
                actual += len(chunk)
            if actual != expected:
                raise ValueError('WAV parcial; no se acredita como completo')
    except (wave.Error,EOFError) as exc:
        raise ValueError('WAV inválido; no se acredita como completo') from exc
    if record.get('receipt_sha256') and checksum(receipt_path)!=record['receipt_sha256']:
        raise ValueError('Cambió el recibo completado')
    if _fingerprint(inputs) != record['fingerprint']:
        raise ValueError('Cambiaron recursos o runtime de la solicitud')
    return {**receipt, 'relative_path':record['relative_path'], 'request_id':record['request_id']}


def status(pid, request_id):
    key = _key(request_id)
    with studio.LOCK:
        project, path, claim = _paths(pid,key)
        record = studio.read_json(path)
        if not record:
            if claim.exists():
                return dict(request_id=key,state='interrupted',error='Reserva sin estado; no se repite automáticamente')
            raise FileNotFoundError('Solicitud Piper no encontrada')
        if not isinstance(record,dict) or record.get('request_id')!=key or record.get('state') not in ('running','completed','failed','invalid','interrupted'):
            raise ValueError('Estado de solicitud inválido')
        result = None
        if record['state']=='completed' or (record['state']=='running' and (pid,key) not in ACTIVE):
            try:
                result = _receipt(project,record)
                record.update(state='completed',receipt_sha256=checksum(Path(str(project/record['relative_path'])+'.json')))
            except (ValueError,OSError,KeyError,TypeError) as exc:
                record.update(state='invalid' if record['state']=='completed' else 'interrupted',error=str(exc))
            studio.save_json(path,record)
        return {**record, 'result':result}  # No inference, stop or automatic relaunch.


def preview(pid, data):
    import uuid
    key = _key(data.get('request_id',uuid.uuid4().hex))
    inputs = dict(voice=data.get('voice'), speaker_id=data.get('speaker_id',0), text=data.get('text'))
    with studio.LOCK:
        project,path,claim = _paths(pid,key)
        if path.exists() or claim.exists():
            current = status(pid,key)
            if current.get('inputs') != inputs:
                raise editor.Conflict('El request_id ya pertenece a otras entradas')
            if current['state']=='completed':
                return {**current['result'], 'reused':True}
            raise editor.Conflict('Solicitud '+current['state']+'; recupera estado, no se repite el proveedor')
        if ACTIVE:
            raise editor.Conflict('Ya hay una preescucha Piper activa en este servidor')
        fingerprint = _fingerprint(inputs)
        relative = 'assets/audio/piper-'+key+'.wav'
        output = project/relative
        output.parent.resolve().relative_to(project.resolve())
        if output.exists() or Path(str(output)+'.json').exists():
            raise editor.Conflict('La salida ya existe; no se sobrescribe')
        path.parent.mkdir(parents=True,exist_ok=True)
        try:
            with claim.open('x',encoding='utf-8') as stream:
                json.dump(dict(request_id=key,server_pid=os.getpid()),stream)
        except FileExistsError as exc:
            raise editor.Conflict('Otra instancia reservó esta solicitud') from exc
        record = dict(request_id=key,state='running',inputs=inputs,fingerprint=fingerprint,
                      relative_path=relative,server_pid=os.getpid(),started_at=studio.now())
        studio.save_json(path,record)
        ACTIVE.add((pid,key))
    try:
        piper.synthesize(inputs['text'],inputs['voice'],inputs['speaker_id'],output)
        with studio.LOCK:
            result = _receipt(project,record)
            record.update(state='completed',completed_at=studio.now(),
                          receipt_sha256=checksum(Path(str(output)+'.json')))
            studio.save_json(path,record)
        return {**result, 'reused':False}
    except Exception as exc:
        with studio.LOCK:
            record.update(state='failed',error=str(exc),completed_at=studio.now())
            studio.save_json(path,record)
        raise
    finally:
        with studio.LOCK:
            ACTIVE.discard((pid,key))
