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
CONTEXT_MESSAGE_COMPACT_CHARS = 2048
CONTEXT_RECENT_MESSAGES = 12
CONTEXT_COMPACTION_VERSION = 1
MAX_RECEIPT_ARCHIVE_BYTES = 256 * 1024 * 1024


def _uncertain_session_message(in_flight):
    """Describe the saved intent without exposing tool arguments or claiming its outcome."""
    entry = in_flight if isinstance(in_flight, dict) else {}
    function = entry.get('function')
    function = function if isinstance(function, dict) else {}
    name = function.get('name')
    name = name if isinstance(name, str) and name.isascii() and name.replace('_', '').isalnum() else 'unknown'
    call_id = entry.get('tool_call_id')
    call_id = call_id if isinstance(call_id, str) and call_id.isascii() and call_id.replace('-', '').replace('_', '').isalnum() else 'unknown'
    attempt_id = entry.get('conversation_attempt_id')
    attempt_id = attempt_id if isinstance(attempt_id, str) and len(attempt_id) == 32 and all(c in '0123456789abcdef' for c in attempt_id) else 'not_recorded'
    request_id = entry.get('request_id')
    request_id = request_id if isinstance(request_id, str) and request_id.isascii() and request_id.replace('-', '').replace('_', '').isalnum() else 'not_recorded'
    return ('AGENT_SESSION_UNCERTAIN: llamada persistida antes del dispatch; su efecto no se conoce y no se repetirá. '
            f'tool={name} tool_call_id={call_id} conversation_attempt_id={attempt_id} request_id={request_id}. '
            'Comprueba recibos/artefactos del propietario antes de reanudar; no compartas los argumentos en el diagnóstico.')



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


_CONTEXT_PROTECTED = re.compile(
    r"\b(?:authoriz(?:e|ed|ation)|autoriz(?:o|ad[oa]|ación)|approval|approved|aprob(?:ad[oa]|ación)|"
    r"decision(?:es)?|decisión(?:es)?|decidid[oa]|pending tasks?|pendient(?:e|es)|todo|uncertain|incierto|in_flight|"
    r"plan|planned|planificado|must|debe|should|debería|siguiente tarea|next task)\b",
    re.IGNORECASE,
)
_CONTEXT_REFERENCE = re.compile(
    r"https?://[^\s<>\])}]+|#[0-9]+|\b[0-9a-fA-F]{40}\b|\b[0-9a-fA-F]{64}\b"
)
_CONTEXT_LABEL = re.compile(r"^\s*(?:\[)?(FACT|HECHO|PLAN|SUMMARY|RESUMEN)(?:\])?\s*:", re.IGNORECASE)


def _context_message_classification(role, content):
    """Classify only explicit labels; never infer facts or plans from prose."""
    match = _CONTEXT_LABEL.match(content[:160]) if isinstance(content, str) else None
    label = match.group(1).upper() if match else None
    if label in ("FACT", "HECHO"):
        return "explicit_fact"
    if label == "PLAN":
        return "explicit_plan"
    if label in ("SUMMARY", "RESUMEN"):
        return "explicit_summary"
    return "user_statement_unclassified" if role == "user" else "assistant_statement_unclassified"


def _complete_message_batches(messages):
    """Require every historical assistant tool call to have exactly one later result."""
    awaiting = set()
    seen = set()
    for message in messages:
        role = message.get("role")
        if awaiting:
            if role != "tool":
                return False
            call_id = message.get("tool_call_id")
            if not isinstance(call_id, str) or call_id not in awaiting:
                return False
            awaiting.remove(call_id)
            continue
        if role == "assistant" and message.get("tool_calls"):
            calls = message["tool_calls"]
            if not isinstance(calls, list) or not calls:
                return False
            for call in calls:
                call_id = call.get("id") if isinstance(call, dict) else None
                if not isinstance(call_id, str) or not call_id or call_id in seen:
                    return False
                seen.add(call_id)
                awaiting.add(call_id)
    return not awaiting


def _context_archive_record(message, index, request_sha256, messages_sha256, session_version):
    content = message.get("content", "")
    if not isinstance(content, str) or len(content) <= CONTEXT_MESSAGE_COMPACT_CHARS:
        return None
    if _CONTEXT_PROTECTED.search(content) or "AGENT_SESSION_UNCERTAIN" in content:
        return None
    refs = list(dict.fromkeys(_CONTEXT_REFERENCE.findall(content)))
    classification = _context_message_classification(message.get("role"), content)
    original_sha256 = hashlib.sha256(
        json.dumps(message, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "archive_version": CONTEXT_COMPACTION_VERSION,
        "session_version": session_version,
        "request_sha256": request_sha256,
        "source_messages_sha256": messages_sha256,
        "message_index": index,
        "role": message.get("role"),
        "classification": classification,
        "references": refs,
        "original_message_sha256": original_sha256,
        "message": deepcopy(message),
    }


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
            raise Pause('blocked', _uncertain_session_message(old['in_flight']))
        self.state = old or {'version': 2, 'request_sha256': digest, 'messages': deepcopy(initial),
                             'pending': [], 'next_call': 0, 'in_flight': None, 'reads': []}
        for attempt in self.state.get('model_attempts', []):
            if attempt.get('status') == 'running':
                attempt.update(status='interrupted_unknown', finished_at=studio.now())
        for path in self.state['reads']:
            instance.instruction(path)
        # Fresh state/clarifications arrive only after any saved tool batch is complete.
        self.refresh = deepcopy(initial) if old else None
        for message in self.state.get('messages', []):
            if not isinstance(message, dict) or message.get('role') not in ('user', 'assistant'):
                continue
            try:
                stub = json.loads(message.get('content', ''))
            except (TypeError, ValueError):
                continue
            if not isinstance(stub, dict) or not stub.get('compacted_context'):
                continue
            if stub.get('archive_version') != CONTEXT_COMPACTION_VERSION or stub.get('session_version') != self.state.get('version'):
                raise Pause('blocked', 'AGENT_CONTEXT_VERSION_CHANGED: revisa el archivo original antes de continuar.')
            if stub.get('request_sha256') != digest:
                raise Pause('blocked', 'AGENT_CONTEXT_REQUEST_CHANGED: el contexto archivado pertenece a otra solicitud.')
            name = stub.get('artifact_name')
            if not isinstance(name, str) or not re.fullmatch(r'agent_context_[0-9a-f]{64}', name):
                raise Pause('blocked', 'AGENT_CONTEXT_REFERENCE_INVALID: referencia de archivo no válida.')
            archive_path = self.agent.path / 'artifacts' / (name + '.json')
            if archive_path.is_symlink() or not archive_path.is_file():
                raise Pause('blocked', 'AGENT_CONTEXT_ARCHIVE_MISSING: recupera el mensaje original antes de continuar.')
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

        compacted = 0
        for message in messages:
            if message.get('role') != 'tool':
                continue
            content = message.get('content', '')
            if not isinstance(content, str) or len(content) <= 2048:
                continue
            try:
                structured = json.loads(content)
            except (ValueError, TypeError):
                structured = {'text': content}
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            call_id = message.get('tool_call_id')
            archive_id = hashlib.sha256(f'{call_id or "no-call-id"}:{content_hash}'.encode('utf-8')).hexdigest()
            archive_name = f'agent_receipt_{archive_id}'
            summary = {'compacted': True, 'tool_name': message.get('tool_name'),
                       'tool_call_id': call_id, 'receipt_sha256': content_hash,
                       'receipt_characters': len(content), 'archive_path': f'artifacts/{archive_name}.json',
                       'artifact_name': archive_name,
                       'evidence_note': 'Deterministic summary; use read_artifact with artifact_name to recover the complete receipt.',
                       'summary': _bounded_evidence(structured)}
            summary_content = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
            if len(summary_content) >= len(content):
                continue
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
                    current_bytes = sum(p.stat().st_size for p in archive_dir.glob('agent_receipt_*.json')
                                        if p.is_file() and not p.is_symlink())
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

            message['content'] = summary_content
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


    def compact_old_context_messages(self):
        """Archive old plain user/assistant messages without semantic summarization."""
        state = self.state
        messages = state.get('messages', [])
        if state.get('in_flight') is not None or state.get('next_call', 0) < len(state.get('pending', [])):
            return {'compacted': 0, 'reason': 'batch_incomplete'}
        attempts = state.get('model_attempts', [])
        if any(a.get('status') in ('running', 'interrupted_unknown', 'uncertain') for a in attempts if isinstance(a, dict)):
            return {'compacted': 0, 'reason': 'attempt_uncertain'}
        if any(isinstance(m, dict) and isinstance(m.get('content'), str) and 'AGENT_SESSION_UNCERTAIN' in m['content']
               for m in messages):
            return {'compacted': 0, 'reason': 'attempt_uncertain'}
        if not _complete_message_batches(messages):
            return {'compacted': 0, 'reason': 'message_batch_incomplete'}
        original_size = len(json.dumps(messages, ensure_ascii=False, default=str))
        if original_size <= CONTEXT_COMPACT_CHARS:
            return {'compacted': 0, 'reason': 'under_threshold', 'characters': original_size}
        cutoff = max(0, len(messages) - CONTEXT_RECENT_MESSAGES)
        if cutoff <= 0:
            return {'compacted': 0, 'reason': 'recent_context_preserved', 'characters': original_size}
        try:
            project = self.agent.path.resolve()
            archive_dir = self.agent.path / 'artifacts'
            if archive_dir.is_symlink():
                raise OSError('Project artifact directory cannot be a symbolic link')
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_dir.resolve().relative_to(project)
        except OSError as exc:
            self.agent.event('context_compaction_failed', 'Could not prepare context archive', error=str(exc)[:300])
            return {'compacted': 0, 'reason': 'archive_unavailable'}

        source_messages = json.dumps(messages, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)
        source_messages_sha256 = hashlib.sha256(source_messages.encode('utf-8')).hexdigest()
        request_sha256 = state.get('request_sha256')
        total_archives = 0
        for pattern in ('agent_receipt_*.json', 'agent_context_*.json'):
            for path in archive_dir.glob(pattern):
                if path.is_file() and not path.is_symlink():
                    try:
                        total_archives += path.stat().st_size
                    except OSError:
                        pass

        compacted = 0
        for index in range(cutoff):
            message = messages[index]
            if not isinstance(message, dict) or message.get('role') not in ('user', 'assistant'):
                continue
            if message.get('tool_calls') or message.get('compacted_context'):
                continue
            record = _context_archive_record(message, index, request_sha256, source_messages_sha256,
                                             state.get('version'))
            if record is None:
                continue
            encoded_record = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            archive_sha256 = hashlib.sha256(encoded_record).hexdigest()
            artifact_name = 'agent_context_' + archive_sha256
            target = archive_dir / (artifact_name + '.json')
            if len(encoded_record) >= len(str(message.get('content', ''))):
                continue
            if target.exists():
                if target.is_symlink() or not target.is_file():
                    continue
                try:
                    existing_bytes = target.read_bytes()
                    if hashlib.sha256(existing_bytes).hexdigest() != archive_sha256 or existing_bytes != encoded_record:
                        self.agent.event('context_compaction_failed', 'Context archive identity changed', artifact_name=artifact_name)
                        continue
                except OSError as exc:
                    self.agent.event('context_compaction_failed', 'Context archive could not be verified',
                                     artifact_name=artifact_name, error=str(exc)[:300])
                    continue
            else:
                if total_archives + len(encoded_record) > MAX_RECEIPT_ARCHIVE_BYTES:
                    self.agent.event('context_compaction_failed', 'Context archive size limit reached',
                                     archive_bytes=total_archives, limit_bytes=MAX_RECEIPT_ARCHIVE_BYTES)
                    break
                try:
                    with target.open('xb') as stream:
                        stream.write(encoded_record)
                    total_archives += len(encoded_record)
                except FileExistsError:
                    continue
                except OSError as exc:
                    self.agent.event('context_compaction_failed', 'Could not preserve complete context message',
                                     artifact_name=artifact_name, error=str(exc)[:300])
                    break

            stub = {
                'compacted_context': True,
                'archive_version': CONTEXT_COMPACTION_VERSION,
                'session_version': state.get('version'),
                'request_sha256': request_sha256,
                'source_messages_sha256': source_messages_sha256,
                'message_index': index,
                'role': message.get('role'),
                'classification': record['classification'],
                'references': record['references'],
                'original_message_sha256': record['original_message_sha256'],
                'archive_sha256': archive_sha256,
                'archive_path': f'artifacts/{artifact_name}.json',
                'artifact_name': artifact_name,
                'evidence_note': 'Deterministic archive pointer only; read this JSON with read_artifact and verify archive_sha256 before use. Facts/plans are classified only when the original has an explicit label; otherwise status is unclassified.',
            }
            compacted_content = json.dumps(stub, ensure_ascii=False, separators=(',', ':'))
            if len(compacted_content) >= len(str(message.get('content', ''))):
                continue
            message['content'] = compacted_content
            state.setdefault('context_compactions', []).append({
                'artifact_name': artifact_name,
                'archive_sha256': archive_sha256,
                'original_message_sha256': record['original_message_sha256'],
                'message_index': index,
                'role': message.get('role'),
                'classification': record['classification'],
                'references': record['references'],
                'source_messages_sha256': source_messages_sha256,
                'session_version': state.get('version'),
            })
            compacted += 1

        if compacted:
            self.save()
        return {'compacted': compacted, 'characters_before': original_size,
                'characters_after': len(json.dumps(messages, ensure_ascii=False, default=str))}

    def _progress_fingerprint(self):
        """Detect local project-state changes for loop control; never proof of completion."""
        import os
        digest=hashlib.sha256()
        candidates=[]
        for name in ('production_request.json',):
            p=self.agent.path/name
            if p.is_file() and not p.is_symlink():candidates.append(p)
        for pattern in ('checkpoint_*.json',):
            candidates.extend(p for p in self.agent.path.glob(pattern) if p.is_file() and not p.is_symlink())
        for root_name in ('artifacts','assets','workspaces'):
            root=self.agent.path/root_name
            if not root.is_dir() or root.is_symlink():continue
            for p in root.rglob('*'):
                if p.is_file() and not p.is_symlink() and not p.name.startswith('agent_receipt_'):
                    candidates.append(p)
                    if len(candidates)>=5000:break
        for path in sorted(set(candidates),key=lambda p:str(p)):
            try:
                stat=path.stat();relative=path.relative_to(self.agent.path).as_posix()
                digest.update(relative.encode('utf-8','replace'));digest.update(b'\\0')
                digest.update(str(stat.st_size).encode());digest.update(b':')
                digest.update(str(stat.st_mtime_ns).encode())
                if stat.st_size<=65536:
                    digest.update(path.read_bytes())
            except OSError:
                digest.update(b'unreadable')
        return digest.hexdigest()

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
            self.compact_old_context_messages()
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
            transport=getattr(a,'last_transport',{})
            usage=transport.get('ollama_usage',{}) if isinstance(transport,dict) else {}
            if isinstance(usage,dict) and usage:
                labels=(('prompt_eval_count','prompt'),('eval_count','respuesta'))
                parts=[f'{label} {usage[key]} tokens' for key,label in labels
                       if type(usage.get(key)) is int and usage[key]>=0]
                for key,label in (('load_duration','carga'),('prompt_eval_duration','prompt'),
                                  ('eval_duration','respuesta'),('total_duration','total')):
                    value=usage.get(key)
                    if type(value) is int and value>=0:parts.append(f'{label} {value/1_000_000:.1f} ms')
                if parts:
                    a.event('model_usage','Uso reportado por Ollama: '+' · '.join(parts),ollama_usage=usage)
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
            call=s['pending'][s['next_call']]
            try:
                args = fn.get('arguments', {})
                if isinstance(args, str):args = json.loads(args)
            except Exception as exc:
                args={}
                parse_error=exc
            else:parse_error=None
            signature=hashlib.sha256(json.dumps({'name':fn.get('name'),'arguments':args},ensure_ascii=False,sort_keys=True,default=str,separators=(',',':')).encode('utf-8')).hexdigest()
            progress_before=self._progress_fingerprint()
            recent=s.setdefault('tool_call_history',[])
            uncertain_previous=next((item for item in reversed(recent)
                                     if item.get('signature')==signature and item.get('outcome')=='unknown'),None)
            repeated=any(item.get('signature')==signature and item.get('before')==item.get('after')==progress_before
                         for item in recent[-2:])
            owner_request_id=None
            preflight_error=None
            if fn.get('name')=='execute_tool' and parse_error is None:
                try:
                    identity=a.dispatch('tool_preflight',args)
                    if isinstance(identity,dict) and isinstance(identity.get('request_id'),str) and identity['request_id']:
                        owner_request_id=identity['request_id']
                    else:
                        preflight_error='tool_preflight no devolvió request_id'
                except Exception as exc:
                    preflight_error=str(exc)[:500]
            attempt_seed={'request_sha256':s.get('request_sha256'),'message_count':len(s['messages']),
                          'call_index':s['next_call'],'signature':signature,'tool_call_id':call.get('id')}
            conversation_attempt_id=hashlib.sha256(json.dumps(attempt_seed,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()[:32]
            s['in_flight']={'call_index':s['next_call'],'function':fn,'tool_call_id':call.get('id'),
                            'signature':signature,'progress_before':progress_before,
                            'conversation_attempt_id':conversation_attempt_id,
                            'request_id':owner_request_id}
            self.save()
            pause = None
            try:
                if parse_error is not None:raise parse_error
                if uncertain_previous:
                    request_id=uncertain_previous.get('request_id')
                    suffix=' request_id='+str(request_id) if request_id else ''
                    raise Pause('blocked','AGENT_TOOL_OUTCOME_UNCERTAIN: la misma llamada pudo haber escrito; reconcilia su estado antes de repetirla.'+suffix)
                if repeated:raise Pause('blocked','AGENT_LOOP_NO_PROGRESS: llamada idéntica con los mismos argumentos y sin cambios de proyecto; se detuvo antes de repetirla.')
                if fn.get('name')=='execute_tool' and not owner_request_id:
                    result={'success':False,'tool':args.get('name') if isinstance(args,dict) else None,
                            'request_id':None,
                            'error':{'code':'owner_request_id_unavailable',
                                     'message':'No se ejecutó la herramienta: no se pudo obtener y persistir su request_id.',
                                     'outcome':'not_started','recoverable':True,'retryable':False,
                                     'reconcile_before_retry':False,
                                     'next_action':'Revisa tool_preflight; no reintentes una escritura incierta.'},
                            'preflight_error':preflight_error}
                else:
                    result = a.dispatch(fn.get('name'), args)
            except Pause as exc:
                pause = exc
                result = {'paused': exc.status, 'message': str(exc)}
            except Exception as exc:
                if callable(getattr(exc,'as_receipt',None)):
                    result=exc.as_receipt()
                elif isinstance(exc,json.JSONDecodeError):
                    result={'error':{'code':'invalid_tool_arguments','message':str(exc)[:1200],
                                     'outcome':'not_started','recoverable':True,'retryable':False,
                                     'reconcile_before_retry':False,'next_action':'Corrige los argumentos JSON.'}}
                else:
                    result={'error':{'code':'agent_dispatch_error','message':str(exc)[:1200],
                                     'outcome':'unknown','recoverable':True,'retryable':False,
                                     'reconcile_before_retry':True,
                                     'next_action':'Consulta revisión, recibo y artefactos antes de repetir.'}}
                a.event('error', str(exc)[:1200])
            content = json.dumps(result, ensure_ascii=False, default=str)
            receipt = {'role': 'tool', 'tool_name': fn.get('name'), 'content': content}
            progress_after=self._progress_fingerprint()
            error_value=result.get('error') if isinstance(result,dict) else None
            uncertain= isinstance(error_value,dict) and error_value.get('outcome')=='unknown'
            outcome='paused' if pause else ('unknown' if uncertain else ('error' if error_value else 'returned'))
            s.setdefault('tool_call_history',[]).append({
                'signature':signature,'name':fn.get('name'),'tool_call_id':call.get('id'),
                'conversation_attempt_id':conversation_attempt_id,
                'request_id':result.get('request_id') if isinstance(result,dict) else None,
                'before':progress_before,'after':progress_after,
                'receipt_sha256':hashlib.sha256(content.encode('utf-8')).hexdigest(),
                'outcome':outcome})
            s['tool_call_history']=s['tool_call_history'][-100:]
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
