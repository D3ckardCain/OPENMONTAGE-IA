"""Prepared libraries are diagnostic-only and use separate interpreters."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools.analysis import prepared_library_doctor as doctor
from tools.tool_registry import ToolRegistry


class PreparedLibraryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_unknown_library_rejected_before_process(self):
        with patch.object(doctor.subprocess, 'run') as run:
            result = doctor.PreparedLibraryDoctor().execute({'library': '../musetalk'})
            self.assertFalse(result.success)
            self.assertIn('LIBRARY_INPUT_INVALID', result.error)
            run.assert_not_called()

    def test_missing_runtime_has_clear_error(self):
        with patch.object(doctor, 'RUNTIME_ROOT', self.root):
            result = doctor.PreparedLibraryDoctor().execute({'library': 'socceraction'})
        self.assertIn('LIBRARY_RUNTIME_MISSING', result.error)

    def test_isolated_command_and_structured_provenance(self):
        python = self.root / 'socceraction/venv' / ('Scripts/python.exe' if doctor.os.name == 'nt' else 'bin/python')
        python.parent.mkdir(parents=True)
        python.touch()
        (self.root / 'socceraction/source-provenance.json').write_text(json.dumps({'commit': 'a' * 40, 'verified_files': 168}))
        payload = {'runtime': 'socceraction', 'versions': {'socceraction': '1.5.3'}, 'geometry_generated': False}
        with patch.object(doctor, 'RUNTIME_ROOT', self.root), patch.object(doctor.subprocess, 'run',
                return_value=subprocess.CompletedProcess('probe', 0, json.dumps(payload).encode(), b'')) as run:
            result = doctor.PreparedLibraryDoctor().execute({'library': 'socceraction'})
        self.assertTrue(result.success, result.error)
        self.assertEqual(run.call_args.args[0], [str(python), '-I', '-B', str(doctor.WORKER), 'socceraction'])
        self.assertFalse(run.call_args.kwargs['shell'])
        self.assertEqual(result.data['provenance']['prepared_commit'], 'a' * 40)
        self.assertFalse(result.data['provenance']['installed_files_rehashed'])
        self.assertEqual(result.cost_usd, 0)

    def test_timeout_and_bad_output(self):
        python = self.root / 'socceraction/venv' / ('Scripts/python.exe' if doctor.os.name == 'nt' else 'bin/python')
        python.parent.mkdir(parents=True)
        python.touch()
        with patch.object(doctor, 'RUNTIME_ROOT', self.root):
            with patch.object(doctor.subprocess, 'run', side_effect=subprocess.TimeoutExpired('probe', 60)):
                self.assertIn('LIBRARY_TIMEOUT', doctor.PreparedLibraryDoctor().execute({'library': 'socceraction'}).error)
            with patch.object(doctor.subprocess, 'run', return_value=subprocess.CompletedProcess('probe', 0, b'broken', b'')):
                self.assertIn('LIBRARY_OUTPUT_INVALID', doctor.PreparedLibraryDoctor().execute({'library': 'socceraction'}).error)

    def test_registry_exposes_diagnostic_contract(self):
        registry = ToolRegistry()
        registry.register_module(doctor)
        self.assertIsNotNone(registry.get('prepared_library_doctor'))
        self.assertEqual(doctor.PreparedLibraryDoctor().runtime.value, 'local')

    def test_real_prepared_libraries_offline(self):
        for name in doctor.NAMES:
            runtime = doctor.RUNTIME_ROOT / name / 'venv'
            if not runtime.is_dir():
                continue
            with self.subTest(name=name):
                result = doctor.PreparedLibraryDoctor().execute({'library': name})
                self.assertTrue(result.success, result.error)
                self.assertFalse(result.data['network_accessed'])
                self.assertFalse(result.data['real_input_read'])
                self.assertFalse(result.data['geometry_generated'])
                self.assertFalse(result.data['model_inference_performed'])
                self.assertTrue(result.data['synthetic_checks'])
