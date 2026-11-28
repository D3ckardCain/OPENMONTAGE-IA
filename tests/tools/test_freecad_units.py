"""Native numeric CAD parameters only; no documents, geometry or GUI."""
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backlot.studio_routes import create_studio_router
from lib import production_studio as studio
from lib import freecad_runtime
from lib.freecad_units_worker import validate_payload
from lib.pipeline_loader import load_pipeline_readonly
from lib.production_agent import LocalAgent
from tools.analysis import freecad_units as units
from tools.tool_registry import ToolRegistry

INPUT = {'project_id': 'fixture', 'source_unit': 'in', 'target_unit': 'mm', 'values': [1, 2, 0, -1]}
RESULT = {'values': [25.4, 50.8, 0, -25.4], 'geometry_created': False, 'documents_created': False}


class FreecadUnitsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for target, name, value in ((studio, 'project_path', Mock(return_value=self.root)),
                                     (units, 'python_environment', Mock(return_value=(self.root / 'python.exe', {})))):
            replacement = patch.object(target, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def process(self, data=RESULT, code=0):
        return Mock(stdout=json.dumps(data).encode(), stderr=b'', returncode=code)

    def test_child_environment_and_no_mutation(self):
        before = dict(os.environ)
        with patch.object(units.subprocess, 'run', return_value=self.process()) as run:
            r = units.FreecadUnits().execute(INPUT)
        self.assertTrue(r.success, r.error)
        self.assertEqual(dict(os.environ), before)
        self.assertEqual(run.call_args.args[0][1:3], ['-I', '-B'])
        self.assertFalse(run.call_args.kwargs['shell'])
        env = run.call_args.kwargs['env']
        self.assertTrue(all(not Path(env[k]).exists() for k in ('FREECAD_USER_HOME', 'FREECAD_USER_DATA', 'FREECAD_USER_TEMP')))
        self.assertEqual(len(r.data['provenance']['input_sha256']), 64)
        self.assertFalse(r.data['geometry_created'])

    def test_incompatible_units_arbitrary_expressions_and_unknown_fields(self):
        for changes in ({'target_unit': 's'}, {'source_unit': '__import__(os)'}, {'source_unit': 'C'},
                        {'values': []}, {'values': [True]}, {'values': [float('nan')]},
                        {'values': [float('inf')]}, {'values': [1e13]}, {'values': [0] * 1001}, {'output_path': 'solid.step'}):
            with patch.object(units.subprocess, 'run') as run:
                self.assertFalse(units.FreecadUnits().execute({**INPUT, **changes}).success)
                run.assert_not_called()
        with self.assertRaises(ValueError):
            validate_payload([])

    def test_missing_project_blocks_native_work(self):
        with patch.object(studio, 'project_path', side_effect=FileNotFoundError('missing')), patch.object(units.subprocess, 'run') as run:
            self.assertFalse(units.FreecadUnits().execute(INPUT).success)
            run.assert_not_called()

    def test_timeout_bad_json_oversize_and_native_error(self):
        for response in (self.process({'error': 'incompatible'}, 1), self.process([], 0),
                         Mock(stdout=b'not json', stderr=b'DLL error', returncode=1),
                         Mock(stdout=b'x' * 150001, stderr=b'', returncode=0)):
            with patch.object(units.subprocess, 'run', return_value=response):
                self.assertFalse(units.FreecadUnits().execute(INPUT).success)
        with patch.object(units.subprocess, 'run', side_effect=subprocess.TimeoutExpired('worker', 45)):
            self.assertIn('FREECAD_TIMEOUT', units.FreecadUnits().execute(INPUT).error)

    def test_api_origin_and_agent_bridge(self):
        app = FastAPI()
        app.include_router(create_studio_router())
        with patch.object(units.subprocess, 'run', return_value=self.process()), TestClient(app) as client:
            r = client.post('/api/studio/applications/freecad/units', json=INPUT)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()['values'][0], 25.4)
            self.assertEqual(client.post('/api/studio/applications/freecad/units', json={**INPUT, 'target_unit': 's'}).status_code, 400)
            self.assertEqual(client.post('/api/studio/applications/freecad/units', json=INPUT, headers={'Origin': 'https://remote.example'}).status_code, 403)
        registry = ToolRegistry()
        registry.register_module(units)
        agent = LocalAgent.__new__(LocalAgent)
        agent.pid, agent.path, agent.registry = 'fixture', self.root, registry
        agent.request = {'pipeline': 'animation'}
        agent.manifest = load_pipeline_readonly('animation')
        agent.reads = {'skills/' + agent.manifest['stages'][0]['skill'] + '.md'}
        agent.event = Mock()
        with patch.object(units.subprocess, 'run', return_value=self.process()):
            result = agent.dispatch('execute_tool', {'name': 'freecad_units', 'inputs': INPUT})
        self.assertTrue(result['success'], result['error'])
        with self.assertRaisesRegex(ValueError, 'otro proyecto'):
            agent.dispatch('execute_tool', {'name': 'freecad_units', 'inputs': {**INPUT, 'project_id': 'outside'}})


class FreecadRuntimeTests(unittest.TestCase):
    def test_bundled_python_environment_rejects_foreign_runtime_and_preserves_parent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'bin').mkdir()
            for name in ('FreeCAD.exe', 'bin/python.exe', 'bin/FreeCAD.pyd'):
                (root / name).touch()
            with patch.object(freecad_runtime, 'configuration', return_value={'freecad': {'executable': str(root / 'FreeCAD.exe')}}), patch.dict(os.environ, {'PYTHONHOME': 'comfy', 'PYQGIS_STARTUP': 'foreign.py', 'FREECAD_USER_HOME': 'existing'}):
                before = dict(os.environ)
                python, env = freecad_runtime.python_environment()
                self.assertEqual(python, root / 'bin/python.exe')
                self.assertEqual(dict(os.environ), before)
                self.assertFalse(any(k.startswith(('PYTHON', 'PYQGIS', 'FREECAD')) for k in env))
                (root / 'bin/FreeCAD.pyd').unlink()
                with self.assertRaisesRegex(ValueError, 'FREECAD_RUNTIME_MISSING'):
                    freecad_runtime.python_environment()


def native_available():
    try:
        freecad_runtime.python_environment()
        return True
    except (OSError, ValueError):
        return False


@unittest.skipUnless(os.environ.get('OPENMONTAGE_FREECAD_NATIVE_QA') == '1' and native_available(), 'optional native FreeCAD numeric QA')
class NativeFreecadUnitsTests(unittest.TestCase):
    def test_native_dimensions_and_inverse_without_gui_or_documents(self):
        cases = [('in', 'mm', 1, 25.4), ('m', 'cm', 2, 200), ('m^2', 'cm^2', 1, 10000),
                 ('m^3', 'mm^3', 1, 1e9), ('deg', 'rad', 180, math.pi), ('kg', 'g', 2, 2000),
                 ('h', 'min', 1, 60), ('kN', 'N', 2, 2000), ('MPa', 'Pa', 2, 2e6)]
        with tempfile.TemporaryDirectory() as d, patch.object(studio, 'project_path', return_value=Path(d)):
            for source, target, value, expected in cases:
                with self.subTest(source=source, target=target):
                    r = units.FreecadUnits().execute({**INPUT, 'source_unit': source, 'target_unit': target, 'values': [value]})
                    self.assertTrue(r.success, r.error)
                    self.assertAlmostEqual(r.data['values'][0], expected, delta=max(1e-10, abs(expected) * 1e-12))
                    self.assertLess(r.data['roundtrip_max_error'], 1e-10)
                    self.assertTrue(r.data['temporary_profile_verified'])
                    self.assertFalse(r.data['documents_created'])
                    self.assertFalse(r.data['geometry_created'])
                    self.assertFalse(r.data['gui_loaded'])
