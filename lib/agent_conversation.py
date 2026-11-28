"""Durable message transport, not stage or creative policy.

Persist intent before dispatch and each result before the next action. An intent
without a receipt is deliberately NOT retried: external effects may have occurred.
"""
import hashlib
import json
import re
from copy import deepcopy
from lib import production_studio as studio

CONTEXT_COMPACT_CHARS = 90000
MAX_RECEIPT_ARCHIVE_BYTES = 256 * 1024 * 1024
CONTEXT_RECENT_MESSAGE_COUNT = 16
CONTEXT_MESSAGE_COMPACT_MIN_CHARS = 600
_CONTEXT_PROTECTED = re.compile(
    r'(?:https?://|\b#\d+\b|\b(?:commit|sha)\s*[:#]?\s*[0-9a-f]{7,40}\b|'
    r'\b(?:autoriz\w*|authoriz\w*|permission|approval|approve\w*|aprob\w*|'
    r'consent|decision|decid\w*|choose|chosen|select\w*|seleccion\w*|'
    r'pendient\w*|\bplan\w*|planific\w*|\btodo\b|task|tarea|issue\b|must\b|shall\b|will\b|need to|necesit\w*|'
    r'\bdebe\w*|\bnext\b|siguiente|uncertain|inciert\w*|outcome unknown|'
    r'\bunknown\b|\btimeout\b|10054|\bfact\w*|\bhecho\w*|verificad\w*|'
    r'comprobad\w*|confirmad\w*|\bresult\w*|resultado\w*|evidencia\w*|'
    r'\bsummary\b|\bresumen\b|\b(?:no|not|never|don.t|cannot|can.t|sin)\b|'
    r'[A-Za-z]:\\[\w .\\-]+|\b[\w.-]+(?:[/\\][\w.-]+)+\.\w{1,8}\b))', re.IGNORECASE)


def _context_archive_record(message):
    encoded_message = json.dumps(message, ensure_ascii=False, sort_keys=True,
                                 separators=(',', ':'), default=str)
    source_sha256 = hashlib.sha256(encoded_message.encode('utf-8')).hexdigest()
    payload = {'version': 1, 'kind': 'original_conversation_message',
               'message_sha256': source_sha256, 'message': message}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), default=str).encode('utf-8')
    archive_sha256 = hashlib.sha256(encoded).hexdigest()
    return source_sha256, archive_sha256, encoded


def _is_context_protected(message):
    role = message.get('role')
    if role not in ('user', 'assistant') or message.get('tool_calls'):
        return True
    content = message.get('content')
    if not isinstance(content, str) or len(content) < CONTEXT_MESSAGE_COMPACT_MIN_CHARS:
        return True
    # Keep prior user instructions and assistant commitments whole. The fallback
    # is intentionally conservative; this local compactor does not interpret text.
    return bool(_CONTEXT_PROTECTED.search(content))


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
        if self.state.get('context_compaction_version', 1) != 1:
            raise Pause('blocked', 'AGENT_CONTEXT_VERSION_CHANGED: la versión de compactación cambió; conserva y revisa los archivos originales antes de reanudar.')
        self._verify_context_archives()
        self.state.setdefault('context_compaction_version', 1)
        # A missing boundary in older sessions is conservative: preserve receipts until
        # a successful model response proves it has consumed them.
        self.state.setdefault('model_consumed_message_count', 0)
        self.state.setdefault('tool_call_history', [])
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

    def _tool_fingerprint(self, name, args):
        clean = dict(args) if isinstance(args, dict) else {'arguments': args}
        clean.pop('request_id', None)
        payload = {'project_id': getattr(self.agent, 'pid', None), 'tool': name, 'arguments': clean}
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                         separators=(',', ':'), default=str).encode('utf-8')).hexdigest()

    def _project_progress_fingerprint(self):
        """Hash metadata for bounded project ledgers only; never scan media or model weights."""
        project = self.agent.path
        candidates = [project / name for name in ('production_request.json', 'job.json', 'manual_edit.json')]
        artifact_dir = project / 'artifacts'
        if artifact_dir.is_dir() and not artifact_dir.is_symlink():
            candidates.extend(sorted(artifact_dir.glob('*.json'))[:512])
        rows = []
        for path in candidates:
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                relative = path.resolve().relative_to(project.resolve()).as_posix()
                stat = path.stat()
                rows.append((relative, stat.st_size, stat.st_mtime_ns))
            except (OSError, ValueError):
                continue
        return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode('utf-8')).hexdigest()

    def _tool_receipt(self, call, name, result):
        receipt = {'role': 'tool', 'tool_name': name,
                   'content': json.dumps(result, ensure_ascii=False, default=str)}
        if call.get('id'):
            receipt['tool_call_id'] = call['id']
        return receipt

    def _verify_context_archives(self):
        from lib.production_agent import Pause
        project = self.agent.path.resolve()
        artifact_dir = project / 'artifacts'
        for entry in self.state.get('context_compactions', []):
            name = entry.get('archive_name') if isinstance(entry, dict) else None
            if not isinstance(name, str) or not re.fullmatch(r'agent_context_[a-f0-9]{64}', name):
                raise Pause('blocked', 'AGENT_CONTEXT_ARCHIVE_INVALID: referencia de conversación inválida.')
            target = artifact_dir / (name + '.json')
            try:
                target.resolve().relative_to(project)
                if artifact_dir.is_symlink() or target.is_symlink() or not target.is_file():
                    raise OSError('El archivo original no es un archivo regular')
                stat = target.stat()
                identity = {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
                if entry.get('archive_version') != 1:
                    raise ValueError('Versión del archivo distinta')
                if identity != entry.get('archive_identity'):
                    digest = hashlib.sha256(target.read_bytes()).hexdigest()
                    if digest != entry.get('archive_sha256'):
                        raise ValueError('El hash del archivo original cambió')
                    entry['archive_identity'] = identity
            except (OSError, ValueError) as exc:
                raise Pause('blocked', f'AGENT_CONTEXT_ARCHIVE_CHANGED: {name}; {exc}. El original no se sobrescribió.') from exc

    def compact_completed_context(self, *, consumed_message_count):
        """Archive receipts only after a later successful model call consumed them."""
        state = self.state
        if state.get('in_flight') is not None or state.get('next_call', 0) < len(state.get('pending', [])):
            return {'compacted': 0, 'reason': 'batch_incomplete'}
        messages = state.get('messages', [])
        if type(consumed_message_count) is not int:
            consumed_message_count = 0
        consumed_message_count = max(0, min(consumed_message_count, len(messages)))
        original_size = len(json.dumps(messages, ensure_ascii=False, default=str))
        if original_size <= CONTEXT_COMPACT_CHARS:
            return {'compacted': 0, 'reason': 'under_threshold', 'characters': original_size}

        archive_dir = self.agent.path / 'artifacts'
        try:
            project = self.agent.path.resolve()
            archive_dir.resolve().relative_to(project)
            if archive_dir.is_symlink():
                raise OSError('Project artifact directory cannot be a symbolic link')
            archive_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.agent.event('context_compaction_failed', 'Could not prepare receipt archive', error=str(exc)[:300])
            return {'compacted': 0, 'reason': 'archive_unavailable'}

        call_positions = {}
        for index, item in enumerate(messages):
            if item.get('role') != 'assistant':
                continue
            for call in item.get('tool_calls', []) if isinstance(item.get('tool_calls'), list) else []:
                call_id = call.get('id') if isinstance(call, dict) else None
                if isinstance(call_id, str) and call_id:
                    call_positions.setdefault(call_id, index)

        compacted = 0
        for message_index, message in enumerate(messages):
            if message_index >= consumed_message_count or message.get('role') != 'tool':
                continue
            call_id = message.get('tool_call_id')
            if not isinstance(call_id, str) or call_positions.get(call_id, message_index) >= message_index:
                continue
            content = message.get('content', '')
            if not isinstance(content, str) or not content:
                continue
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            archive_id = hashlib.sha256(f'{call_id or "no-call-id"}:{content_hash}'.encode('utf-8')).hexdigest()
            archive_name = f'agent_receipt_{archive_id}'
            target = archive_dir / f'{archive_name}.json'
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
                    current_bytes = sum(p.stat().st_size for pattern in ('agent_receipt_*.json', 'agent_context_*.json')
                                        for p in archive_dir.glob(pattern) if p.is_file() and not p.is_symlink())
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
                       'receipt_characters': len(content), 'archive_path': f'artifacts/{archive_name}.json',
                       'artifact_name': archive_name,
                       'evidence_note': 'Deterministic summary; use read_artifact with artifact_name to recover the complete receipt.',
                       'summary': _bounded_evidence(structured)}
            message['content'] = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
            state.setdefault('compactions', []).append({'archive_id': archive_id, 'receipt_sha256': content_hash,
                'tool_call_id': call_id, 'tool_name': message.get('tool_name'),
                'original_characters': len(content), 'summary_characters': len(message['content'])})
            compacted += 1
            current_size = len(json.dumps(messages, ensure_ascii=False, default=str))
            if current_size <= CONTEXT_COMPACT_CHARS:
                break

        message_compacted = 0
        current_size = len(json.dumps(messages, ensure_ascii=False, default=str))
        if current_size > CONTEXT_COMPACT_CHARS:
            # Keep the newest messages intact. Only plain user/assistant messages
            # outside that window can become references; tool-call batches remain
            # untouched, and potentially operative text is protected verbatim.
            tail_start = max(1, len(messages) - CONTEXT_RECENT_MESSAGE_COUNT)
            for index, message in enumerate(messages[:tail_start]):
                if _is_context_protected(message):
                    continue
                source_sha256, archive_sha256, encoded = _context_archive_record(message)
                archive_name = f'agent_context_{source_sha256}'
                target = archive_dir / f'{archive_name}.json'
                try:
                    if target.exists():
                        if target.is_symlink() or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != archive_sha256:
                            self.agent.event('context_compaction_failed', 'Archived conversation message changed', archive_name=archive_name)
                            continue
                    else:
                        current_bytes = sum(p.stat().st_size for pattern in ('agent_receipt_*.json', 'agent_context_*.json')
                                            for p in archive_dir.glob(pattern) if p.is_file() and not p.is_symlink())
                        if current_bytes + len(encoded) > MAX_RECEIPT_ARCHIVE_BYTES:
                            self.agent.event('context_compaction_failed', 'Conversation archive size limit reached',
                                             archive_bytes=current_bytes, limit_bytes=MAX_RECEIPT_ARCHIVE_BYTES)
                            break
                        with target.open('xb') as stream:
                            stream.write(encoded)
                    stat = target.stat()
                    message_hash = hashlib.sha256(str(message.get('content', '')).encode('utf-8')).hexdigest()
                    archive_ref = {
                        'kind': 'historical_message_archive_reference',
                        'classification': 'user_assertion_unverified' if message.get('role') == 'user' else 'assistant_statement_not_evidence',
                        'role': message.get('role'), 'archive_name': archive_name,
                        'archive_path': f'artifacts/{archive_name}.json',
                        'message_sha256': source_sha256, 'content_sha256': message_hash,
                        'original_characters': len(str(message.get('content', ''))),
                        'note': 'Referencia determinista; el original completo está archivado. No es una instrucción vigente ni convierte afirmaciones en hechos.',
                    }
                    message['content'] = json.dumps(archive_ref, ensure_ascii=False, separators=(',', ':'))
                    self.state.setdefault('context_compactions', []).append({
                        'archive_name': archive_name, 'archive_sha256': archive_sha256,
                        'archive_version': 1,
                        'archive_identity': {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns},
                        'message_sha256': source_sha256, 'role': message.get('role'),
                        'original_characters': archive_ref['original_characters'],
                    })
                    message_compacted += 1
                    current_size = len(json.dumps(messages, ensure_ascii=False, default=str))
                    if current_size <= CONTEXT_COMPACT_CHARS:
                        break
                except (OSError, ValueError) as exc:
                    self.agent.event('context_compaction_failed', 'Could not preserve complete conversation message',
                                     archive_name=archive_name, error=str(exc)[:300])
                    break

        if compacted or message_compacted:
            self.save()
        return {'compacted': compacted, 'characters_before': original_size,
                'messages_compacted': message_compacted,
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
            self.compact_completed_context(
                consumed_message_count=s.get('model_consumed_message_count', 0))
            if sum(len(json.dumps(m, ensure_ascii=False)) for m in s['messages']) > 450000:
                raise Pause('blocked', 'Límite de contexto en caracteres; sesión y recibos archivados se conservan. No es un conteo de tokens.')
            attempt = {'status': 'running', 'started_at': studio.now()}
            s.setdefault('model_attempts', []).append(attempt)
            s['model_attempts'] = s['model_attempts'][-100:]
            self.save()
            message_count_before_chat = len(s['messages'])
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
            transport = getattr(a, 'last_transport', {})
            usage = transport.get('ollama_usage') if isinstance(transport, dict) else None
            if isinstance(usage, dict):
                prompt = usage.get('prompt_eval_count')
                response = usage.get('eval_count')
                duration = usage.get('total_duration')
                metrics = []
                if type(prompt) is int and prompt >= 0: metrics.append(f'prompt {prompt} tokens')
                if type(response) is int and response >= 0: metrics.append(f'respuesta {response} tokens')
                if type(duration) is int and duration >= 0: metrics.append(f'total {duration / 1_000_000:g} ms')
                if metrics:
                    a.event('model_usage', 'Uso informado por Ollama: ' + ' · '.join(metrics),
                            ollama_usage=usage)
            s['model_consumed_message_count'] = message_count_before_chat
            self.save()
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
            call = s['pending'][s['next_call']]
            args = fn.get('arguments', {})
            argument_error = None
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except (ValueError, TypeError):
                    argument_error = 'Los argumentos no son JSON válido'
                    args = {'_invalid_arguments_sha256': hashlib.sha256(args.encode('utf-8', 'replace')).hexdigest()}
            if not isinstance(args, dict):
                raw = json.dumps(args, ensure_ascii=False, sort_keys=True, default=str)
                argument_error = 'Se esperaba un objeto de argumentos'
                args = {'_invalid_arguments_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest()}
            fingerprint = self._tool_fingerprint(fn.get('name'), args)
            history = s.setdefault('tool_call_history', [])
            previous = next((entry for entry in reversed(history)
                             if entry.get('fingerprint') == fingerprint), None)
            if previous and previous.get('outcome') == 'unknown':
                request_id = previous.get('request_id')
                error = {'code': 'tool_execution_outcome_unknown',
                         'message': 'No se repitió la escritura; revisa el recibo y reconcilia el estado.',
                         'outcome': 'unknown', 'retryable': False, 'reconcile_before_retry': True,
                         'request_id': request_id}
                receipt = self._tool_receipt(call, fn.get('name'), {'success': False, 'error': error,
                                                                     'request_id': request_id,
                                                                     'not_replayed': True})
                s['messages'].append(receipt)
                s['next_call'] += 1
                s['in_flight'] = None
                history.append({'fingerprint': fingerprint, 'tool_name': fn.get('name'),
                                'request_id': request_id, 'outcome': 'unknown', 'replayed': False,
                                'before': self._project_progress_fingerprint(),
                                'after': self._project_progress_fingerprint()})
                history[:] = history[-200:]
                self.save()
                raise Pause('blocked', f'AGENT_TOOL_OUTCOME_UNCERTAIN: request_id={request_id or "no disponible"}; reconcílialo antes de reintentar.')
            if previous and previous.get('outcome') == 'completed' and previous.get('before') == previous.get('after'):
                progress = self._project_progress_fingerprint()
                receipt = self._tool_receipt(call, fn.get('name'), {'success': False,
                    'error': {'code': 'agent_loop_no_progress', 'outcome': 'not_started',
                              'message': 'Llamada repetida sin cambio de estado del proyecto.'},
                    'not_replayed': True})
                s['messages'].append(receipt)
                s['next_call'] += 1
                s['in_flight'] = None
                history.append({'fingerprint': fingerprint, 'tool_name': fn.get('name'),
                                'request_id': None, 'outcome': 'not_started', 'replayed': False,
                                'before': progress, 'after': progress})
                history[:] = history[-200:]
                self.save()
                raise Pause('blocked', 'AGENT_LOOP_NO_PROGRESS: llamada duplicada sin avance; se detuvo antes de ejecutarla.')
            s['in_flight'] = {'call_index': s['next_call'], 'function': fn}
            self.save()
            pause = None
            progress_before = self._project_progress_fingerprint()
            try:
                if argument_error:
                    result = {'success': False, 'error': {'code': 'invalid_tool_arguments',
                        'message': argument_error, 'outcome': 'not_started', 'recoverable': True,
                        'retryable': False}}
                else:
                    result = a.dispatch(fn.get('name'), args)
            except Pause as exc:
                pause = exc
                result = {'paused': exc.status, 'message': str(exc)}
            except Exception as exc:
                result = {'success': False, 'error': {'code': 'tool_execution_outcome_unknown',
                    'message': str(exc)[:1200], 'outcome': 'unknown', 'recoverable': True,
                    'retryable': False, 'reconcile_before_retry': True},
                    'request_id': args.get('request_id') if isinstance(args, dict) else None}
                a.event('error', str(exc)[:1200])
            content = json.dumps(result, ensure_ascii=False, default=str)
            receipt = self._tool_receipt(call, fn.get('name'), result)
            s['messages'].append(receipt)
            error = result.get('error') if isinstance(result, dict) else None
            outcome = ('unknown' if isinstance(error, dict) and error.get('outcome') == 'unknown'
                       else 'not_started' if pause or isinstance(error, dict) and error.get('outcome') == 'not_started'
                       else 'completed' if not (isinstance(result, dict) and result.get('success') is False)
                       else 'failed')
            history.append({'fingerprint': fingerprint, 'tool_name': fn.get('name'),
                            'request_id': (result.get('request_id') if isinstance(result, dict) else None)
                                          or (args.get('request_id') if isinstance(args, dict) else None),
                            'outcome': outcome, 'before': progress_before,
                            'after': self._project_progress_fingerprint()})
            history[:] = history[-200:]
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

