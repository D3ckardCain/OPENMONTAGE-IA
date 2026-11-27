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
    version = '3.9.0'
    capability = 'video_post'
    provider = 'local'
    description = 'Read and edit the shared Studio project; explicit bounded Qwen preview/start/status/cancel. Revision required for writes.'
    install_instructions = 'Inicia la instancia actualizada de Studio local (BACKLOT_PORT o 4750); no requiere modelos ni paquetes nuevos.'
    capabilities = ['subtitle_karaoke', 'subtitle_quality', 'mix_meter_start', 'mix_meter_status', 'mix_meter_cancel', 'sfx_catalog', 'sfx_insert', 'sfx_receipt', 'read', 'revisioned_edit', 'register_project_media', 'local_render', 'render_status', 'render_cancel', 'capabilities', 'subtitle_words', 'subtitle_draft', 'silence_proposal', 'chatterbox_profiles', 'qwen_profiles', 'qwen_start', 'qwen_status', 'qwen_cancel']
    side_effects = ['Writes the selected manual project through the running local Studio server', 'qwen_start explicitly runs a bounded local synthesis worker']
    not_good_for = ['Unbounded inference or automatic model downloads', 'Editing production pipeline artifacts', 'Editing while Studio is stopped']
    input_schema = {'type': 'object', 'required': ['project_id', 'action'], 'properties': {
        'project_id': {'type': 'string'}, 'action': {'enum': ['subtitle_karaoke', 'subtitle_quality', 'mix_meter_start', 'mix_meter_status', 'mix_meter_cancel', 'sfx_catalog', 'sfx_insert', 'sfx_receipt', 'read', 'command', 'register', 'render', 'render_status', 'render_cancel', 'capabilities', 'subtitle_words', 'subtitle_draft', 'silence_proposal', 'chatterbox_profiles', 'qwen_profiles', 'qwen_start', 'qwen_status', 'qwen_cancel']},
        'sfx': {'type':'object','description':'Local catalogue query or explicit insertion with request_id, revision, asset_id and montage start/in/out; never inference.'},
        'proposal': {'type': 'object', 'description': 'Read-only silence proposal with revision, EDL/word hashes and explicit source-clock analysis. Does not analyze media or apply cuts.'},
        'set_id': {'type': 'string'},
        'request_id': {'type':'string'}, 'meter': {'type':'object','description':'Optional start_seconds and duration_seconds, maximum 120 seconds of the existing final rendered mix; never auto-render.'}, 'qwen': {'type':'object'},
        'command': {'type': 'object'}, 'relative_path': {'type': 'string'}, 'revision': {'type': 'integer'},
        'preview': {'type': 'boolean'}, 'attempt': {'type': 'string'}}}

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
            if action == 'subtitle_karaoke':
                value=request(path+'/subtitles/karaoke?set_id='+quote(inputs['set_id'],safe=''))
            elif action == 'subtitle_quality':
                value=request(path+'/subtitles/quality')
            elif action == 'mix_meter_start':
                value = request(path+'/agent-mix-meter',{**inputs.get('meter',{}),'request_id':inputs['request_id'],'revision':inputs['revision']})
            elif action in ('mix_meter_status','mix_meter_cancel'):
                target=path+'/mix-meter/requests/'+quote(inputs['request_id'],safe='')
                value=request(target) if action=='mix_meter_status' else request(target+'/cancel',{})
            elif action == 'sfx_catalog':
                from urllib.parse import urlencode
                value = request('sfx?'+urlencode(inputs.get('sfx',{})))
            elif action == 'sfx_insert':
                value = request(path+'/agent-sfx/insert',inputs['sfx'])
            elif action == 'sfx_receipt':
                value = request(path+'/sfx/requests/'+quote(inputs['request_id'],safe=''))
            elif action == 'capabilities':
                value = request('capabilities')
            elif action == 'qwen_profiles':
                value = request('qwen/profiles')
            elif action == 'chatterbox_profiles':
                value = request('chatterbox/profiles')
            elif action == 'qwen_start':
                value = request(path + '/agent-qwen/preview', inputs['qwen'])
            elif action == 'qwen_status':
                value = request(path + '/qwen/requests/' + quote(inputs['request_id'],safe=''))
            elif action == 'qwen_cancel':
                value = request(path + '/agent-qwen/requests/' + quote(inputs['request_id'],safe='') + '/cancel', {})
            elif action == 'read':
                value = request(path)
            elif action == 'subtitle_words':
                value = request(path + '/subtitle-words?set_id=' + quote(inputs['set_id'],safe=''))
            elif action == 'subtitle_draft':
                value = request(path + '/subtitle-draft?set_id=' + quote(inputs['set_id'],safe=''))
            elif action == 'silence_proposal':
                value = request(path + '/silence-proposal', inputs['proposal'])
            elif action == 'command':
                value = request(path + '/agent-command', inputs['command'])
            elif action == 'register':
                value = request(path + '/agent-register', {'relative_path': inputs['relative_path'], 'revision': inputs['revision']})
            elif action == 'render_status':
                value = request(path + '/render')
            elif action == 'render_cancel':
                value = request(path + '/agent-render/cancel', {'attempt': inputs['attempt']})
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
