"""Synthetic numeric fixtures exercise the installed isolated sports libraries."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from lib import production_studio as studio
from lib.pipeline_loader import load_pipeline_readonly
from lib.production_agent import LocalAgent
from tools.tool_registry import ToolRegistry
from tools.analysis import sports_coordinates as sports


@unittest.skipUnless(sports.python_path().is_file(), 'optional isolated sports runtime not provisioned')
class SportsCoordinatesIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / 'fixture'
        self.project.mkdir()
        replacement = patch.object(studio, 'project_path', return_value=self.project)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.metadata = {'pitch_length_m': 105, 'pitch_width_m': 68,
                         'unit': 'normalized', 'origin': 'top_left', 'y_axis': 'down'}
        self.data = {'source': self.metadata, 'target': {**self.metadata, 'unit': 'm', 'origin': 'bottom_left', 'y_axis': 'up'},
                     'points': [[0, 0], [0.5, 0.5], [1, 1]]}
        self.inputs = {'project_id': 'fixture', 'input_path': 'coordinates.json', 'output_path': 'artifacts/coordinates.json'}

    def execute(self, data=None):
        studio.save_json(self.project / 'coordinates.json', data if data is not None else self.data)
        return sports.SportsCoordinates().execute(self.inputs)

    def test_metric_bridge_preserves_provenance_and_orientation(self):
        result = self.execute()
        self.assertTrue(result.success, result.error)
        report = studio.read_json(self.project / 'artifacts/coordinates.json')
        self.assertEqual(report['points'], [[0, 68], [52.5, 34], [105, 0]])
        self.assertEqual(report['mplsoccer_statsbomb']['points'], [[0, 0], [60, 40], [120, 80]])
        self.assertLess(report['roundtrip_max_error_m'], 1e-8)
        self.assertFalse(report['figures_generated'])
        self.assertEqual(report['provenance']['input_sha256'], hashlib.sha256((self.project / 'coordinates.json').read_bytes()).hexdigest())
        self.assertFalse(report['provenance']['network_accessed'])
        self.assertIn('metadata_origin', report['provenance'])

    def test_centered_centimeters_and_distances(self):
        data = {'source': {**self.metadata, 'unit': 'cm', 'origin': 'center', 'y_axis': 'up'},
                'target': {**self.metadata, 'unit': 'm', 'origin': 'center', 'y_axis': 'down'},
                'points': [[0, 0], [300, 400], [-5250, -3400]]}
        result = self.execute(data)
        self.assertTrue(result.success, result.error)
        report = studio.read_json(self.project / 'artifacts/coordinates.json')
        self.assertAlmostEqual(report['consecutive_distances_m'][0], 5)
        self.assertAlmostEqual(report['points'][1][0], 3)
        self.assertAlmostEqual(report['points'][1][1], -4)
        self.assertEqual(report['points'][2], [-52.5, 34])

    def test_asymmetric_dimensions_and_centered_normalized_target(self):
        self.data['source'].update(pitch_length_m=100, pitch_width_m=60)
        self.data['target'] = {**self.data['source'], 'origin': 'center', 'y_axis': 'up'}
        result = self.execute()
        self.assertTrue(result.success, result.error)
        self.assertEqual(result.data['points_preview'], [[-0.5, 0.5], [0, 0], [0.5, -0.5]])

    def test_missing_and_inconsistent_metadata_are_rejected(self):
        for key in self.metadata:
            data = json.loads(json.dumps(self.data))
            del data['source'][key]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'SPORTS_METADATA_INVALID'):
                sports.worker(json.dumps(data).encode())
        self.data['target']['pitch_length_m'] = 110
        self.assertIn('SPORTS_DIMENSIONS_MISMATCH', self.execute().error)

    def test_invalid_units_and_orientation_are_rejected(self):
        for fields in ({'unit': 'yards'}, {'origin': 'unknown'}, {'y_axis': 'sideways'},
                       {'y_axis': 'up'}, {'pitch_length_m': None}, {'pitch_width_m': 0}):
            data = json.loads(json.dumps(self.data))
            data['source'].update(fields)
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                sports.worker(json.dumps(data).encode())

    def test_outside_or_nonfinite_points_are_rejected_without_clipping(self):
        for points in ([[1.1, 0]], [[True, 0]], [[float('nan'), 0]], [], [[1]], [[0, 0]] * 1001):
            data = {**self.data, 'points': points}
            with self.subTest(points=points[:2]), self.assertRaises(ValueError):
                sports.worker(json.dumps(data).encode())

    def test_no_overwrite_and_workspace_escape(self):
        output = self.project / 'artifacts/coordinates.json'
        output.parent.mkdir()
        output.write_bytes(b'original')
        with patch.object(sports, 'worker') as worker:
            result = self.execute()
            self.assertIn('SPORTS_OUTPUT_EXISTS', result.error)
            self.assertEqual(output.read_bytes(), b'original')
            for fields in ({'input_path': str(self.root / 'outside.json')}, {'output_path': '../outside.json'},
                           {'output_path': 'unexpected.json'}):
                self.inputs.update(fields)
                self.assertFalse(self.execute().success)
            worker.assert_not_called()

    def test_timeout_and_invalid_worker_output(self):
        with patch.object(sports.subprocess, 'run', side_effect=subprocess.TimeoutExpired('worker', 45)):
            self.assertIn('SPORTS_TIMEOUT', self.execute().error)
        with patch.object(sports.subprocess, 'run', return_value=subprocess.CompletedProcess('worker', 0, b'not json', b'')):
            self.assertIn('SPORTS_OUTPUT_INVALID', self.execute().error)

    def test_diagnostic_registry_and_agent_execution(self):
        registry = ToolRegistry()
        registry.register_module(sports)
        agent = LocalAgent.__new__(LocalAgent)
        agent.pid, agent.path = 'fixture', self.project
        agent.registry = registry
        agent.request = {'pipeline': 'animation'}
        agent.manifest = load_pipeline_readonly('animation')
        agent.reads = {'skills/' + agent.manifest['stages'][0]['skill'] + '.md'}
        agent.event = Mock()
        result = agent.dispatch('execute_tool', {'name': 'sports_coordinates_doctor', 'inputs': {}})
        self.assertTrue(result['success'], result['error'])
        self.assertEqual(result['data']['versions'], {'kloppy': '3.19.1', 'mplsoccer': '1.8.1'})
        studio.save_json(self.project / 'coordinates.json', self.data)
        result = agent.dispatch('execute_tool', {'name': 'sports_coordinates', 'inputs': self.inputs})
        self.assertTrue(result['success'], result['error'])
        self.assertEqual(result['cost_usd'], 0)
