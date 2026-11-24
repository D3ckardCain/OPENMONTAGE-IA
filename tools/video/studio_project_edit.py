"""Agent access to the same revisioned manual project that Studio edits."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from tools.base_tool import BaseTool, ToolResult, ToolStatus


def request(path, data=None, timeout=120):
    # A single Studio process owns writes, including calls from external agents.
    # Never run a second filesystem writer with only an in-process lock.
    port = int(os.environ.get('BACKLOT_PORT', '4750'))
    if not 1 <= port <= 65535:
        raise ValueError('Puerto Studio inválido')
    url = f'http://127.0.0.1:{port}/api/studio/editor/' + path
    payload = None if data is None else json.dumps(data, allow_nan=False).encode('utf-8')
    req = Request(url, data=payload, headers={'Content-Type':'application/json'})
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as exc:
        try:
            detail = json.load(exc).get('detail', str(exc))
        except (ValueError, OSError):
            detail = str(exc)
        return {'_error': str(detail), '_conflict': exc.code == 409}


class StudioProjectEdit(BaseTool):
    name = 'studio_project_edit'
    version = '1.0.0'
    capability = 'video_post'
    provider = 'local'
    description = 'Read and edit the shared Studio manual project; no inference. Revision required for writes.'
    install_instructions = 'Inicia la instancia actualizada de Studio local (BACKLOT_PORT o 4750); no requiere modelos ni paquetes nuevos.'
    capabilities = ['read', 'revisioned_edit', 'register_project_media', 'local_render', 'render_status']
    side_effects = ['Writes the selected manual project through the running local Studio server']
    not_good_for = ['Starting inference', 'Editing production pipeline artifacts', 'Editing while Studio is stopped']
    input_schema = {'type': 'object', 'required': ['project_id', 'action'], 'properties': {
        'project_id': {'type': 'string'}, 'action': {'enum': ['read', 'command', 'register', 'render', 'render_status']},
        'command': {'type': 'object'}, 'relative_path': {'type': 'string'}, 'revision': {'type': 'integer'},
        'preview': {'type': 'boolean'}}}

    def get_status(self):
        try:
            value = request('projects', timeout=2)
            return ToolStatus.AVAILABLE if isinstance(value, list) else ToolStatus.UNAVAILABLE
        except (ValueError, OSError, URLError):
            return ToolStatus.UNAVAILABLE

    def execute(self, inputs):
        try:
            pid = inputs['project_id']
            path = quote(pid, safe='')
            action = inputs['action']
            if action == 'read':
                value = request(path)
            elif action == 'command':
                value = request(path + '/agent-command', inputs['command'])
            elif action == 'register':
                value = request(path + '/agent-register', {'relative_path': inputs['relative_path'], 'revision': inputs['revision']})
            elif action == 'render_status':
                value = request(path + '/render')
            elif action == 'render':
                value = request(path + '/agent-render', {'revision':inputs['revision'], 'preview':inputs.get('preview', False)})
            else:
                raise ValueError('Acción no disponible')
            if not isinstance(value, dict):
                raise ValueError('La respuesta de Studio no corresponde a un proyecto editable')
            if '_error' in value:
                return ToolResult(success=False, error=value['_error'], data={'conflict': value['_conflict']})
            value = {k:v for k,v in value.items() if k not in ('undo', 'redo')}
            return ToolResult(success=True, data={'project_id': pid, **value, 'origin': 'agent'})
        except (ValueError, TypeError, KeyError, OSError, URLError) as exc:
            return ToolResult(success=False, error='Studio local no disponible o solicitud inválida: ' + str(exc), data={'conflict': False})
