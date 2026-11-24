"""SPADL fixtures, actual schema when prepared; no provider events or figures."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backlot.studio_routes import create_studio_router
from lib import production_studio as studio, isolated_library_operation as transport
from lib.production_agent import LocalAgent
from lib.pipeline_loader import load_pipeline_readonly
from tools.analysis import socceraction_spadl as module
from tools.tool_registry import ToolRegistry

ROW = {'game_id': 0, 'original_event_id': None, 'action_id': 0, 'period_id': 1, 'time_seconds': 0.,
       'team_id': 2, 'player_id': 0, 'start_x': 10., 'start_y': 20., 'end_x': 30., 'end_y': 40.,
       'bodypart_id': 0, 'type_id': 0, 'result_id': 1}
INPUT = {'project_id': 'fixture', 'coordinate_system': 'spadl_105x68_bottom_left_home_to_right', 'actions': [ROW]}


class SpadlContracts(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for target, key, value in ((studio, 'project_path', Mock(return_value=self.root)),):
            p = patch.object(target, key, value);p.start();self.addCleanup(p.stop)

    def test_transport_errors_missing_runtime_and_input_schema(self):
        with patch.object(transport, 'RUNTIME_ROOT', self.root), patch.object(transport.subprocess, 'run') as run:
            r = module.SocceractionSpadl().execute(INPUT)
            self.assertIn('LIBRARY_RUNTIME_MISSING', r.error)
            self.assertFalse(module.SocceractionSpadl().execute({**INPUT, 'script': 'arbitrary'}).success)
            self.assertFalse(module.SocceractionSpadl().execute({**INPUT, 'coordinate_system': 'pixels'}).success)
            run.assert_not_called()

    def test_api_and_dispatch_use_same_tool(self):
        output = Mock(success=True, error=None, cost_usd=0, artifacts=[], data={'valid': True, 'action_count': 1})
        app = FastAPI();app.include_router(create_studio_router())
        with patch.object(module.SocceractionSpadl, 'execute', return_value=output), TestClient(app) as client:
            r = client.post('/api/studio/libraries/socceraction/spadl/validate', json=INPUT)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertTrue(r.json()['valid'])
            self.assertEqual(client.post('/api/studio/libraries/socceraction/spadl/validate', json=INPUT, headers={'Origin': 'https://remote.example'}).status_code, 403)
            self.assertEqual(client.get('/api/studio/tools?name=missing').status_code, 200)
        registry=ToolRegistry();registry.register_module(module)
        worker=LocalAgent.__new__(LocalAgent);worker.pid='fixture';worker.path=self.root;worker.registry=registry
        worker.request={'pipeline':'animation'};worker.manifest=load_pipeline_readonly('animation')
        worker.reads={'skills/'+worker.manifest['stages'][0]['skill']+'.md'};worker.event=Mock()
        with patch.object(module.SocceractionSpadl,'get_status',return_value=transport.ToolStatus.AVAILABLE), patch.object(module.SocceractionSpadl,'execute',return_value=output):
            self.assertTrue(worker.dispatch('execute_tool',{'name':'socceraction_spadl_validate','inputs':INPUT})['success'])
            with self.assertRaisesRegex(ValueError,'otro proyecto'):
                worker.dispatch('execute_tool',{'name':'socceraction_spadl_validate','inputs':{**INPUT,'project_id':'outside'}})


@unittest.skipUnless(module.SocceractionSpadl().python().is_file(), 'optional prepared Socceraction runtime')
class NativeSpadl(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        p=patch.object(studio,'project_path',return_value=self.root);p.start();self.addCleanup(p.stop)

    def test_real_schema_and_provenance(self):
        original=copy.deepcopy(INPUT)
        r=module.SocceractionSpadl().execute(INPUT)
        self.assertTrue(r.success,r.error);self.assertTrue(r.data['valid'])
        self.assertEqual(INPUT,original)
        self.assertEqual(r.data['versions']['socceraction'],'1.5.3')
        self.assertEqual(len(r.data['provenance']['input_sha256']),64)
        self.assertFalse(r.data['provenance']['network_accessed'])
        self.assertFalse(r.data['coordinates_transformed'])

    def test_invalid_native_bounds_types_enums_names_and_duplicates(self):
        for change in ({'start_x':106.},{'end_y':69.},{'period_id':6},{'result_id':99},
                       {'action_id':1.5},{'time_seconds':True},{'type_name':'shot'},{'unknown':0}):
            r=module.SocceractionSpadl().execute({**INPUT,'actions':[{**ROW,**change}]})
            self.assertFalse(r.success,str(change));self.assertFalse(r.data['valid'])
            self.assertTrue(r.data['issues'])
        r=module.SocceractionSpadl().execute({**INPUT,'actions':[ROW,ROW]})
        self.assertFalse(r.success);self.assertEqual(r.data['issues'][0]['reason'],'duplicate_action_in_game')
