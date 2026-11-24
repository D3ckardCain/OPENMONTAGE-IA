"""One constrained model-selected native unit conversion; no production loop."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import threading
import uuid
from lib import production_studio as studio
from lib import production_agent as agent

SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def probe():
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('AGENT_PROBE_CHANGED: reinicia Studio tras cambiar el diagnóstico')
    from lib import production_queue as queue, reference_analysis
    from tools.analysis import freecad_units
    from tools.tool_registry import ToolRegistry
    pid = 'agent-probe-' + uuid.uuid4().hex
    path = studio.PROJECTS_DIR / pid
    path.resolve().relative_to(studio.PROJECTS_DIR.resolve())
    with queue.LOCK, agent.ACTIVE_LOCK, reference_analysis.LOCK:
        if queue.WORKER is not None or agent.ACTIVE or reference_analysis.ACTIVE:
            raise ValueError('AGENT_PROBE_BUSY: espera a que termine la tarea local')
        agent.ACTIVE[pid] = (threading.current_thread(), threading.Event())
    created = False
    try:
        config = studio.settings()
        base, model = studio.local_url(config['ollama_url']), config['model']
        if not model or model.endswith(':cloud'):
            raise ValueError('AGENT_PROBE_MODEL: selecciona un modelo local preparado')
        tags = studio.local_request(base, '/api/tags').get('models', [])
        tag = next((row for row in tags if row.get('name') == model), None)
        if tag is None or tag.get('remote_host') or tag.get('remote_model'):
            raise ValueError('AGENT_PROBE_MODEL: se requiere un modelo local instalado')
        if studio.local_request(base, '/api/ps').get('models'):
            raise ValueError('AGENT_PROBE_BUSY: hay modelos cargados; no se alteran')
        show = studio.local_request(base, '/api/show', {'model': model})
        if show.get('remote_host') or show.get('remote_model') or 'tools' not in show.get('capabilities', []):
            raise ValueError('AGENT_PROBE_MODEL: no se acredita herramienta local')
        registry = ToolRegistry()
        registry.register_module(freecad_units)
        if freecad_units.FreecadUnits().get_status().value != 'available':
            raise ValueError('AGENT_PROBE_TOOL: falta el FreeCAD preparado')
        path.mkdir()
        created = True
        studio.save_json(path / 'production_request.json', {
            'project_id': pid, 'title': 'Diagnóstico sintético de herramientas',
            'pipeline': 'animation', 'diagnostic_fixture': True})
        instance = agent.LocalAgent(pid, registry=registry)
        skill = instance.manifest['stages'][0]['skill']
        instance.instruction('skills/' + skill + '.md')
        inputs = {'project_id': pid, 'source_unit': 'in', 'target_unit': 'mm', 'values': [1]}
        expected = {'name': 'freecad_units', 'inputs': inputs}
        schema = {'type': 'object', 'additionalProperties': False, 'required': ['name', 'inputs'],
                  'properties': {'name': {'type': 'string', 'enum': ['freecad_units']},
                                 'inputs': {'type': 'object', 'additionalProperties': False,
                                            'required': list(inputs), 'properties': {
                                                key: {'enum': [value]} for key, value in inputs.items()}}}}
        tool = {'type': 'function', 'function': {'name': 'execute_tool',
                'description': 'Run only this fixed synthetic unit conversion; no media or CAD geometry.', 'parameters': schema}}
        message = instance.chat([{'role': 'user', 'content': 'Protocol fixture only. Call execute_tool exactly once with these exact arguments: ' + json.dumps(expected) + '. No other task.'}],
                                [tool], context_tokens=4096, max_output_tokens=128,
                                thinking=False if 'thinking' in show.get('capabilities', []) else None)
        calls = message.get('tool_calls', [])
        if not isinstance(calls, list) or len(calls) != 1 or not isinstance(calls[0], dict):
            raise ValueError('AGENT_PROBE_PROTOCOL: se requiere una sola llamada')
        function = calls[0].get('function', {})
        if not isinstance(function, dict) or function.get('name') != 'execute_tool' or function.get('arguments') != expected:
            raise ValueError('AGENT_PROBE_PROTOCOL: nombre o argumentos no coinciden; no se ejecutó nada')
        if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != SOURCE_SHA256:
            raise ValueError('AGENT_PROBE_CHANGED: código cambió antes del despacho')
        result = instance.dispatch('execute_tool', function['arguments'])
        if not result['success'] or result['data'].get('values') != [25.4]:
            raise ValueError('AGENT_PROBE_TOOL: la conversión nativa no se confirmó')
        loaded = studio.local_request(base, '/api/ps').get('models')
        return {'passed': True, 'scope': 'one_synthetic_tool_call_not_production_director',
                'model': model, 'model_manifest_digest': tag.get('digest'),
                'called_function': 'execute_tool', 'called_tool': 'freecad_units',
                'input_units': 'in', 'output_units': 'mm', 'input_values': [1], 'output_values': [25.4],
                'context_tokens': 4096, 'max_output_tokens': 128, 'keep_alive': 0,
                'model_unloaded_verified': loaded == [], 'tool_provenance': result['data'].get('provenance'),
                'geometry_created': False, 'creative_content_generated': False,
                'synthetic_text_inference_performed': True, 'cost_usd': 0,
                'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'probe_sha256': SOURCE_SHA256}
    finally:
        try:
            if created:
                # Only the UUID directory this invocation created, always confined to PROJECTS_DIR.
                path.resolve().relative_to(studio.PROJECTS_DIR.resolve())
                shutil.rmtree(path)
        finally:
            with agent.ACTIVE_LOCK:
                agent.ACTIVE.pop(pid, None)
