"""Durable message transport, not stage or creative policy.

Persist intent before dispatch and each result before the next action. An intent
without a receipt is deliberately NOT retried: external effects may have occurred.
"""
import hashlib
import json
from copy import deepcopy
from lib import production_studio as studio

CONTEXT_COMPACT_CHARS = 90000
MAX_RECEIPT_ARCHIVE_BYTES = 256 * 1024 * 1024


def _bounded_evidence(value, depth=0):
    """Keep identifiers and a small preview; the exact receipt stays archived."""
    if isinstance(value, str):
        if len(value) <= 480:
            return value
        raw = value.encode('utf-8')
        return {'_omitted_text': True, 'characters': len(value),
                'sha256': hashlib.sha256(raw).hexdigest(),
                'preview': value[:220] + ' … ' + value[-120:]}
    if isinstance(value, list):
        if len(value) <= 8 and depth < 3:
            return [_bounded_evidence(item, depth + 1) for item in value]
        keep = value[:3] + value[-2:] if len(value) > 5 else value
        return {'_omitted_items': max(0, len(value) - len(keep)), 'count': len(value),
                'items': [_bounded_evidence(item, depth + 1) for item in keep]}
    if isinstance(value, dict):
        if depth >= 3:
            encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            return {'_omitted_object': True, 'keys': sorted(str(k) for k in value)[:24],
                    'characters': len(encoded), 'sha256': hashlib.sha256(encoded.encode('utf-8')).hexdigest()}
        priority = ('status', 'error', 'message', 'project_id', 'revision', 'attempt', 'request_id',
                    'id', 'path', 'url', 'artifact', 'sha256', 'source_sha256', 'bytes', 'count',
                    'provenance', 'source', 'source_url', 'license', 'scope', 'operation', 'version')
        keys = list(value)
        ordered = [key for key in priority if key in value] + sorted((key for key in keys if key not in priority), key=str)
        selected = ordered[:24]
        result = {str(key): _bounded_evidence(value[key], depth + 1) for key in selected}
        if len(keys) > len(selected):
            result['_omitted_keys'] = len(keys) - len(selected)
        return result
    if value is None or type(value) in (bool, int, float):
        return value
    return str(value)[:240]


class Conversation:
    def __init__(self, instance, initial, *, tools, chat_options=None):
        from lib.production_agent import Pause
        self.agent, self.tools = instance, tools
        self.chat_options = chat_options or {}
        self.path = instance.path / 'agent_session.json'
        digest = hashlib.sha256(json.dumps(instance.request, sort_keys=True).encode()).hexdigest()
        old = studio.read_json(self.path, {})
        if old and old.get('version') != 2:
            # Keep legacy evidence; it has no per-call receipt and is not replayable.
            studio.save_json(instance.path / 'agent_session_legacy.json', old)
            old = {}
        if old and old.get('request_sha256') != digest:
            raise Pause('blocked', 'AGENT_SESSION_REQUEST_CHANGED: solicitud cambió; conserva y revisa la sesión antes de reanudar.')
        if old.get('in_flight') is not None:
            raise Pause('blocked', 'AGENT_SESSION_UNCERTAIN: llamada sin recibo; verifica sus efectos antes de reanudar. No se repite automáticamente.')
        self.state = old or {'version': 2, 'request_sha256': digest, 'messages': deepcopy(initial),
                             'pending': [], 'next_call': 0, 'in_flight': None, 'reads': []}
        for attempt in self.state.get('model_attempts', []):
            if attempt.get('status') == 'running':
                attempt.update(status='interrupted_unknown', finished_at=studio.now())
        for path in self.state['reads']:
            instance.instruction(path)
        # Fresh state/clarifications arrive only after any saved tool batch is complete.
        self.refresh = deepcopy(initial) if old else None
        self.save()

    def save(self):
        self.state.update(updated_at=studio.now(), reads=sorted(self.agent.reads))
        studio.save_json(self.path, self.state)

    def compact_completed_context(self):
        """Archive bulky old tool receipts only at a completed call-batch boundary."""
        state = self.state
        if state.get('in_flight') is not None or state.get('next_call', 0) < len(state.get('pending', [])):
            return {'compacted': 0, 'reason': 'batch_incomplete'}
        messages = state.get('messages', [])
        original_size = len(json.dumps(messages, ensure_ascii=False, default=str))
        if original_size <= CONTEXT_COMPACT_CHARS:
            return {'compacted': 0, 'reason': 'under_threshold', 'characters': original_size}

        archive_dir = self.agent.path / 'agent-session-archive'
        try:
            project = self.agent.path.resolve()
            archive_dir.resolve().relative_to(project)
            if archive_dir.is_symlink():
                raise OSError('Receipt archive cannot be a symbolic link')
            archive_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.agent.event('context_compaction_failed', 'Could not prepare receipt archive', error=str(exc)[:300])
            return {'compacted': 0, 'reason': 'archive_unavailable'}

        compacted = 0
        for message in messages:
            if message.get('role') != 'tool':
                continue
            content = message.get('content', '')
            if not isinstance(content, str) or len(content) <= 16000:
                continue
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            call_id = message.get('tool_call_id')
            archive_id = hashlib.sha256(f'{call_id or "no-call-id"}:{content_hash}'.encode('utf-8')).hexdigest()
            target = archive_dir / f'{archive_id}.json'
            if target.exists():
                if target.is_symlink() or not target.is_file():
                    self.agent.event('context_compaction_failed', 'Archived receipt is not a regular file', archive_id=archive_id)
                    continue
                try:
                    existing = json.loads(target.read_text(encoding='utf-8'))
                    if not isinstance(existing, dict) or existing.get('receipt_sha256') != content_hash or existing.get('content') != content:
                        raise ValueError('Archived receipt identity changed')
                except (OSError, ValueError, TypeError) as exc:
                    self.agent.event('context_compaction_failed', 'Archived receipt could not be verified',
                                     archive_id=archive_id, error=str(exc)[:300])
                    continue
            else:
                try:
                    current_bytes = sum(p.stat().st_size for p in archive_dir.iterdir() if p.is_file() and not p.is_symlink())
                    record = {'version': 1, 'archive_id': archive_id, 'tool_name': message.get('tool_name'),
                              'tool_call_id': call_id, 'receipt_sha256': content_hash,
                              'receipt_characters': len(content), 'content': content}
                    encoded = json.dumps(record, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                    if current_bytes + len(encoded) > MAX_RECEIPT_ARCHIVE_BYTES:
                        self.agent.event('context_compaction_failed', 'Receipt archive size limit reached',
                                         archive_bytes=current_bytes, limit_bytes=MAX_RECEIPT_ARCHIVE_BYTES)
                        break
                    with target.open('xb') as stream:
                        stream.write(encoded)
                except FileExistsError:
                    pass
                except OSError as exc:
                    self.agent.event('context_compaction_failed', 'Could not preserve complete receipt',
                                     archive_id=archive_id, error=str(exc)[:300])
                    break

            try:
                structured = json.loads(content)
            except (ValueError, TypeError):
                structured = {'text': content}
            summary = {'compacted': True, 'tool_name': message.get('tool_name'),
                       'tool_call_id': call_id, 'receipt_sha256': content_hash,
                       'receipt_characters': len(content), 'archive_path': f'agent-session-archive/{archive_id}.json',
                       'evidence_note': 'Deterministic summary; the complete receipt is preserved at the archive path.',
                       'summary': _bounded_evidence(structured)}
            message['content'] = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
            state.setdefault('compactions', []).append({'archive_id': archive_id, 'receipt_sha256': content_hash,
                'tool_call_id': call_id, 'tool_name': message.get('tool_name'),
                'original_characters': len(content), 'summary_characters': len(message['content'])})
            compacted += 1
            current_size = len(json.dumps(messages, ensure_ascii=False, default=str))
            if current_size <= CONTEXT_COMPACT_CHARS:
                break

        if compacted:
            self.save()
        return {'compacted': compacted, 'characters_before': original_size,
                'characters_after': len(json.dumps(messages, ensure_ascii=False, default=str))}

    def turn(self):
        from lib.production_agent import Pause
        a, s = self.agent, self.state
        if a.cancel.is_set():
            raise Pause('stopped', 'Detenido entre acciones; resultados guardados para reanudar.')
        if s['next_call'] >= len(s['pending']):
            if self.refresh:
                # Replace system instructions with current ones; retain the tool receipts.
                s['messages'][0] = self.refresh[0]
                s['messages'].extend(self.refresh[1:])
                self.refresh = None
            self.compact_completed_context()
            if sum(len(json.dumps(m, ensure_ascii=False)) for m in s['messages']) > 450000:
                raise Pause('blocked', 'Límite de contexto en caracteres; sesión y recibos archivados se conservan. No es un conteo de tokens.')
            attempt = {'status': 'running', 'started_at': studio.now()}
            s.setdefault('model_attempts', []).append(attempt)
            s['model_attempts'] = s['model_attempts'][-100:]
            self.save()
            try:
                message = a.chat(s['messages'], self.tools, **self.chat_options)
                if a.cancel.is_set():
                    raise Pause('stopped', 'Respuesta descartada tras solicitar cancelación')
            except BaseException as exc:
                attempt.update(status='cancelled' if isinstance(exc, Pause) and exc.status=='stopped' else 'error',
                               finished_at=studio.now(), transport=getattr(a,'last_transport',{}))
                self.save()
                raise
            attempt.update(status='completed', finished_at=studio.now(), transport=getattr(a,'last_transport',{}))
            calls = message.get('tool_calls', [])
            if not isinstance(calls, list) or len(calls) > 16 or any(
                    not isinstance(c, dict) or not isinstance(c.get('function'), dict) for c in calls):
                raise ValueError('AGENT_PROTOCOL: lote de llamadas inválido')
            s['messages'].append(message)
            s.update(pending=calls, next_call=0)
            self.save()
            if not calls:
                raise Pause('awaiting_input', message.get('content') or 'El modelo no emitió llamadas de herramientas.')
        while s['next_call'] < len(s['pending']):
            if a.cancel.is_set():
                raise Pause('stopped', 'Detenido entre acciones; resultados guardados para reanudar.')
            fn = s['pending'][s['next_call']]['function']
            s['in_flight'] = {'call_index': s['next_call'], 'function': fn}
            self.save()
            pause = None
            try:
                args = fn.get('arguments', {})
                if isinstance(args, str):
                    args = json.loads(args)
                result = a.dispatch(fn.get('name'), args)
            except Pause as exc:
                pause = exc
                result = {'paused': exc.status, 'message': str(exc)}
            except Exception as exc:
                result = {'error': str(exc)[:1200]}
                a.event('error', str(exc)[:1200])
            content = json.dumps(result, ensure_ascii=False, default=str)
            if len(content) > 100000:
                content = json.dumps({'error': 'Resultado demasiado grande; solicita una capacidad o artefacto concreto.'})
            receipt = {'role': 'tool', 'tool_name': fn.get('name'), 'content': content}
            call = s['pending'][s['next_call']]
            if call.get('id'):
                receipt['tool_call_id'] = call['id']
            s['messages'].append(receipt)
            s.update(next_call=s['next_call'] + 1, in_flight=None)
            if pause:
                # Remaining calls in this model batch have no authority past a gate.
                for discarded in s['pending'][s['next_call']:]:
                    skipped = {'role': 'tool', 'tool_name': discarded['function'].get('name'),
                               'content': json.dumps({'error': 'Llamada no ejecutada: pausa de control.'})}
                    if discarded.get('id'):
                        skipped['tool_call_id'] = discarded['id']
                    s['messages'].append(skipped)
                s['pending'] = s['pending'][:s['next_call']]
                s['messages'].append({'role': 'user', 'content': 'El resto del lote se descartó por una pausa de control; consulta el estado actual antes de nuevas acciones.'})
            self.save()
            if pause:
                raise pause
