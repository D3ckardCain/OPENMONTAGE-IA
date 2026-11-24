"""Mock model protocol, real dispatch validation; no live inference in CI."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backlot.studio_routes import create_studio_router
from lib import local_agent_probe as probe_module
from lib import production_studio as studio, production_agent as agent, production_queue as queue, reference_analysis
from tools.analysis.freecad_units import FreecadUnits
from tools.base_tool import ToolResult, ToolStatus


class AgentProbeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.pid = 'agent-probe-synthetic001'
        self.args = {'name': 'freecad_units', 'inputs': {'project_id': self.pid,
                     'source_unit': 'in', 'target_unit': 'mm', 'values': [1]}}
        self.message = {'role': 'assistant', 'content': '', 'tool_calls': [
            {'function': {'name': 'execute_tool', 'arguments': self.args}}]}
        self.requests = []
        for target, name, value in ((studio, 'PROJECTS_DIR', self.root), (queue, 'WORKER', None),
                                    (agent, 'ACTIVE', {}), (reference_analysis, 'ACTIVE', set()),
                                    (studio, 'settings', Mock(return_value={'ollama_url': 'http://127.0.0.1:11434', 'model': 'fixture-local'})),
                                    (probe_module.uuid, 'uuid4', Mock(return_value=SimpleNamespace(hex='synthetic001'))),
                                    (studio, 'local_request', Mock(side_effect=self.request)),
                                    (FreecadUnits, 'get_status', Mock(return_value=ToolStatus.AVAILABLE)),
                                    (FreecadUnits, 'execute', Mock(return_value=ToolResult(success=True, data={'values': [25.4], 'provenance': {'fixture': True}}, cost_usd=0))),
                                    (agent.LocalAgent, 'chat', Mock(return_value=self.message))):
            replacement = patch.object(target, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def request(self, base, path, data=None, **kwargs):
        self.requests.append((path, data))
        if path == '/api/tags':return {'models': [{'name': 'fixture-local', 'digest': 'local-digest'}]}
        if path == '/api/show':return {'capabilities': ['tools', 'thinking']}
        if path == '/api/ps':return {'models': []}
        raise AssertionError('unexpected endpoint ' + path)

    def test_exact_call_reaches_native_tool_and_cleans_own_fixture(self):
        r = probe_module.probe()
        self.assertTrue(r['passed'])
        self.assertTrue(r['model_unloaded_verified'])
        self.assertFalse(r['creative_content_generated'])
        self.assertTrue(r['synthetic_text_inference_performed'])
        FreecadUnits.execute.assert_called_once_with(self.args['inputs'])
        self.assertEqual(agent.LocalAgent.chat.call_args.kwargs['context_tokens'], 4096)
        self.assertEqual(agent.LocalAgent.chat.call_args.kwargs['max_output_tokens'], 128)
        self.assertFalse(agent.LocalAgent.chat.call_args.kwargs['thinking'])
        self.assertFalse(agent.ACTIVE)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_unexpected_call_or_arguments_never_dispatch(self):
        for message in ({'tool_calls': None}, {'tool_calls': [{'function': None}]}, {'tool_calls': []}, {'tool_calls': [{'function': {'name': 'launch_app', 'arguments': self.args}}]},
                        {'tool_calls': [{'function': {'name': 'execute_tool', 'arguments': {**self.args, 'name': 'blender_world'}}}]}):
            agent.LocalAgent.chat.return_value = message
            with self.assertRaisesRegex(ValueError, 'AGENT_PROBE_PROTOCOL'):
                probe_module.probe()
            FreecadUnits.execute.assert_not_called()
            self.assertFalse(agent.ACTIVE)
            self.assertFalse((self.root / self.pid).exists())

    def test_active_work_loaded_model_or_remote_model_block_probe(self):
        with patch.object(agent, 'ACTIVE', {'existing': object()}):
            with self.assertRaisesRegex(ValueError, 'AGENT_PROBE_BUSY'):probe_module.probe()
        with patch.object(queue, 'WORKER', object()):
            with self.assertRaisesRegex(ValueError, 'AGENT_PROBE_BUSY'):probe_module.probe()
        with patch.object(reference_analysis, 'ACTIVE', {'existing'}):
            with self.assertRaisesRegex(ValueError, 'AGENT_PROBE_BUSY'):probe_module.probe()
        original = studio.local_request.side_effect
        studio.local_request.side_effect = lambda base, path, data=None, **kw: {'models': [{}]} if path == '/api/ps' else original(base, path, data, **kw)
        with self.assertRaisesRegex(ValueError, 'AGENT_PROBE_BUSY'):probe_module.probe()
        studio.local_request.side_effect = original
        studio.settings.return_value = {'ollama_url': 'http://127.0.0.1:11434', 'model': 'fixture:cloud'}
        with self.assertRaisesRegex(ValueError, 'AGENT_PROBE_MODEL'):probe_module.probe()
        FreecadUnits.execute.assert_not_called()

    def test_model_or_tool_failure_releases_reservation_without_production(self):
        agent.LocalAgent.chat.side_effect = OSError('local timeout')
        with self.assertRaises(OSError):probe_module.probe()
        self.assertFalse(agent.ACTIVE)
        self.assertEqual(list(self.root.iterdir()), [])
        agent.LocalAgent.chat.side_effect = None
        FreecadUnits.execute.return_value = ToolResult(success=False, error='native failure', cost_usd=0)
        with self.assertRaisesRegex(ValueError, 'AGENT_PROBE_TOOL'):probe_module.probe()
        self.assertFalse(agent.ACTIVE)

    def test_api_requires_explicit_empty_post_and_same_origin(self):
        app = FastAPI()
        app.include_router(create_studio_router())
        with TestClient(app) as client:
            self.assertEqual(client.get('/api/studio/agent/probe-tools').status_code, 405)
            self.assertEqual(client.post('/api/studio/agent/probe-tools', json={'prompt': 'arbitrary'}).status_code, 400)
            self.assertEqual(client.post('/api/studio/agent/probe-tools', json={}, headers={'Origin': 'https://remote.example'}).status_code, 403)
            r = client.post('/api/studio/agent/probe-tools', json={})
            self.assertEqual(r.status_code, 200, r.text)
            self.assertTrue(r.json()['passed'])

    def test_studio_bootstrap_remains_available_and_hides_live_probe_fixture(self):
        app = FastAPI()
        app.include_router(create_studio_router())
        message = self.message
        with TestClient(app) as client:
            def while_model_waits(*args, **kwargs):
                self.assertTrue((self.root / self.pid / 'production_request.json').is_file())
                response = client.get('/api/studio/bootstrap')
                self.assertEqual(response.status_code, 200, response.text)
                self.assertNotIn(self.pid, [p['project_id'] for p in response.json()['projects']])
                return message
            agent.LocalAgent.chat.side_effect = while_model_waits
            self.assertTrue(probe_module.probe()['passed'])


class AgentTransportOptionsTests(unittest.TestCase):
    def instance(self):
        result = agent.LocalAgent.__new__(agent.LocalAgent)
        result.cancel = Mock()
        result.cancel.is_set.return_value = False
        result._chat = None
        result.config = {'model': 'local', 'ollama_url': 'http://127.0.0.1:11434'}
        return result

    def test_defaults_preserved_and_explicit_probe_options_only_affect_request(self):
        worker = self.instance()
        with patch.object(studio, 'local_request', return_value={'message': {'role': 'assistant', 'content': ''}}) as request:
            worker.chat([])
            self.assertEqual(request.call_args.args[2]['options'], {'num_ctx': 32768, 'num_predict': 8192})
            self.assertNotIn('think', request.call_args.args[2])
            worker.chat([], context_tokens=4096, max_output_tokens=128, thinking=False)
            data = request.call_args.args[2]
            self.assertEqual(data['options'], {'num_ctx': 4096, 'num_predict': 128})
            self.assertFalse(data['think'])
            self.assertEqual(data['keep_alive'], 0)
        self.assertEqual(worker.config, {'model': 'local', 'ollama_url': 'http://127.0.0.1:11434'})

    def test_invalid_runtime_options_rejected_before_http(self):
        worker = self.instance()
        with patch.object(studio, 'local_request') as request:
            for kwargs in ({'context_tokens': True}, {'context_tokens': 100000}, {'max_output_tokens': 100000}, {'thinking': 'yes'}):
                with self.assertRaises(ValueError):worker.chat([], **kwargs)
            request.assert_not_called()
