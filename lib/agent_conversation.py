"""Durable message transport, not stage or creative policy.

Persist intent before dispatch and each result before the next action. An intent
without a receipt is deliberately NOT retried: external effects may have occurred.
"""
import hashlib
import json
from lib import production_studio as studio


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
        self.state = old or {'version': 2, 'request_sha256': digest, 'messages': initial,
                             'pending': [], 'next_call': 0, 'in_flight': None, 'reads': []}
        for path in self.state['reads']:
            instance.instruction(path)
        # Fresh state/clarifications arrive only after any saved tool batch is complete.
        self.refresh = initial if old else None
        self.save()

    def save(self):
        self.state.update(updated_at=studio.now(), reads=sorted(self.agent.reads))
        studio.save_json(self.path, self.state)

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
            if sum(len(json.dumps(m)) for m in s['messages']) > 450000:
                raise Pause('blocked', 'Límite de contexto; sesión conservada.')
            message = a.chat(s['messages'], self.tools, **self.chat_options)
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
