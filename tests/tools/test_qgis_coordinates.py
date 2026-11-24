"""Numerical fixtures only; no GIS layers, maps or user documents."""
import hashlib
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
from lib.qgis_coordinates_worker import validate_payload
from lib.pipeline_loader import load_pipeline_readonly
from lib.production_agent import LocalAgent
from tools.analysis import qgis_coordinates as gis
from tools.tool_registry import ToolRegistry

INPUT = {'project_id': 'fixture', 'source_crs': 'EPSG:4326', 'target_crs': 'EPSG:3857', 'points': [[0, 0], [12.5, 45]]}
RESULT = {'points': [[0, 0], [1391493.6349159195, 5621521.486192066]], 'qgis_version': 'fixture',
          'maps_generated': False, 'layers_loaded': False, 'model_inference': False}


class QgisCoordinatesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for target, name, value in ((studio, 'project_path', Mock(return_value=self.root)),
                                     (gis, 'runtime', Mock(return_value=(self.root / 'python3.exe', {'PROJ_NETWORK': 'OFF'})))):
            replacement = patch.object(target, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def process(self, result=None, returncode=0):
        return Mock(stdout=json.dumps(RESULT if result is None else result).encode(), stderr=b'', returncode=returncode)

    def test_isolated_runtime_process_and_provenance(self):
        before = dict(os.environ)
        with patch.object(gis.subprocess, 'run', return_value=self.process()) as run:
            r = gis.QgisCoordinates().execute(INPUT)
        self.assertTrue(r.success, r.error)
        self.assertEqual(dict(os.environ), before)
        self.assertEqual(run.call_args.args[0][1:3], ['-s', '-B'])
        self.assertFalse(run.call_args.kwargs['shell'])
        env = run.call_args.kwargs['env']
        self.assertEqual(env['PROJ_NETWORK'], 'OFF')
        self.assertEqual(env['QT_QPA_PLATFORM'], 'offscreen')
        self.assertNotIn('PYQGIS_STARTUP', env)
        self.assertFalse(Path(env['OPENMONTAGE_QGIS_PROFILE']).exists())
        raw = run.call_args.kwargs['input']
        self.assertEqual(r.data['provenance']['input_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertFalse(r.data['maps_generated'])

    def test_invalid_coordinates_rejected_before_native_launch(self):
        for points in ([[0, 90]], [[181, 0]], [[float('inf'), 0]], [[float('nan'), 0]],
                       [[True, 0]], [[0]], [], [[0, 0]] * 1001):
            with self.subTest(points=points[:1]), patch.object(gis.subprocess, 'run') as run:
                r = gis.QgisCoordinates().execute({**INPUT, 'points': points})
                self.assertFalse(r.success)
                run.assert_not_called()

    def test_unsupported_crs_and_unknown_arguments_rejected(self):
        for changes in ({'target_crs': 'EPSG:4326'}, {'source_crs': 'https://remote/crs'},
                        {'source_crs': 'EPSG:32616'}, {'output_path': 'map.png'}):
            with patch.object(gis.subprocess, 'run') as run:
                self.assertFalse(gis.QgisCoordinates().execute({**INPUT, **changes}).success)
                run.assert_not_called()
        with self.assertRaises(ValueError):
            validate_payload([])

    def test_inverse_domain_and_finite_point_validation(self):
        data = {k: INPUT[k] for k in ('source_crs', 'target_crs', 'points')}
        data.update(source_crs='EPSG:3857', target_crs='EPSG:4326', points=[[20037508.342789244, 0]])
        validate_payload(data)
        data['points'] = [[20037509, 0]]
        with self.assertRaisesRegex(ValueError, 'QGIS_POINT_INVALID'):
            validate_payload(data)

    def test_process_errors_timeout_invalid_json_and_unavailable_runtime(self):
        for response in (self.process({'error': 'missing grid'}, 1), self.process([], 0),
                         Mock(stdout=b'not json', stderr=b'DLL load failure', returncode=1),
                         Mock(stdout=b'x' * 250001, stderr=b'', returncode=0)):
            with patch.object(gis.subprocess, 'run', return_value=response):
                self.assertFalse(gis.QgisCoordinates().execute(INPUT).success)
        with patch.object(gis.subprocess, 'run', side_effect=subprocess.TimeoutExpired('worker', 60)):
            self.assertIn('QGIS_TIMEOUT', gis.QgisCoordinates().execute(INPUT).error)
        with patch.object(gis, 'runtime', side_effect=ValueError('QGIS_RUNTIME_MISSING')):
            self.assertEqual(gis.QgisCoordinates().get_status().value, 'unavailable')
            self.assertFalse(gis.QgisCoordinates().execute(INPUT).success)

    def test_api_origin_and_agent_bridge(self):
        app = FastAPI()
        app.include_router(create_studio_router())
        with patch.object(gis.subprocess, 'run', return_value=self.process()), TestClient(app) as client:
            response = client.post('/api/studio/applications/qgis/transform', json=INPUT)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertFalse(response.json()['maps_generated'])
            self.assertEqual(client.post('/api/studio/applications/qgis/transform', json={**INPUT, 'points': [[0, 90]]}).status_code, 400)
            self.assertEqual(client.post('/api/studio/applications/qgis/transform', json=INPUT, headers={'Origin': 'https://remote.example'}).status_code, 403)
        registry = ToolRegistry()
        registry.register_module(gis)
        agent = LocalAgent.__new__(LocalAgent)
        agent.pid, agent.path, agent.registry = 'fixture', self.root, registry
        agent.request = {'pipeline': 'animation'}
        agent.manifest = load_pipeline_readonly('animation')
        agent.reads = {'skills/' + agent.manifest['stages'][0]['skill'] + '.md'}
        agent.event = Mock()
        with patch.object(gis.subprocess, 'run', return_value=self.process()):
            r = agent.dispatch('execute_tool', {'name': 'qgis_coordinates', 'inputs': INPUT})
        self.assertTrue(r['success'], r['error'])
        self.assertEqual(r['cost_usd'], 0)
        with self.assertRaisesRegex(ValueError, 'otro proyecto'):
            agent.dispatch('execute_tool', {'name': 'qgis_coordinates', 'inputs': {**INPUT, 'project_id': 'outside'}})


def native_available():
    try:
        gis.runtime()
        return True
    except (OSError, ValueError):
        return False


@unittest.skipUnless(os.environ.get('OPENMONTAGE_QGIS_NATIVE_QA') == '1' and native_available(), 'optional native QGIS numerical QA')
class NativeQgisCoordinatesTests(unittest.TestCase):
    def test_actual_pyqgis_forward_inverse_with_independent_mercator_formula(self):
        with tempfile.TemporaryDirectory() as d, patch.object(studio, 'project_path', return_value=Path(d)):
            first = gis.QgisCoordinates().execute(INPUT)
            self.assertTrue(first.success, first.error)
            x, y = first.data['points'][1]
            self.assertAlmostEqual(x, 6378137 * math.radians(12.5), places=5)
            self.assertAlmostEqual(y, 6378137 * math.log(math.tan(math.pi / 4 + math.radians(45) / 2)), places=5)
            inverse = gis.QgisCoordinates().execute({**INPUT, 'source_crs': 'EPSG:3857', 'target_crs': 'EPSG:4326', 'points': first.data['points']})
        self.assertTrue(inverse.success, inverse.error)
        self.assertAlmostEqual(inverse.data['points'][1][0], 12.5, places=10)
        self.assertAlmostEqual(inverse.data['points'][1][1], 45, places=10)
        self.assertLess(first.data['roundtrip_max_error'], 1e-10)
        self.assertFalse(inverse.data['layers_loaded'])
