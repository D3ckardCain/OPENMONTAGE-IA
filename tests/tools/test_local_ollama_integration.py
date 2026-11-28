"""Local service tests mock processes/HTTP; no real model or inference."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from lib import local_ollama


class LocalOllamaTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.exe = self.root / 'ollama.exe'
        self.exe.touch()

    def test_existing_service_preserved_without_claiming_cloud_settings(self):
        with patch.object(local_ollama, 'version', return_value='existing'), patch.object(local_ollama.subprocess, 'Popen') as spawn:
            result = local_ollama.start(self.exe, self.root / 'models', self.root / 'logs')
        self.assertFalse(result['started'])
        self.assertFalse(result['cloud_disabled_verified'])
        spawn.assert_not_called()
        self.assertFalse((self.root / 'models').exists())

    def test_new_process_gets_local_only_environment_without_mutating_parent(self):
        process = Mock(pid=123)
        process.poll.return_value = None
        before = dict(os.environ)
        with patch.object(local_ollama, 'version', side_effect=[OSError('not running'), '0.40.17']), patch.object(
                local_ollama.subprocess, 'Popen', return_value=process) as spawn:
            result = local_ollama.start(self.exe, self.root / 'models', self.root / 'logs')
        env = spawn.call_args.kwargs['env']
        self.assertEqual(spawn.call_args.args[0], [str(self.exe), 'serve'])
        self.assertEqual(env['OLLAMA_NO_CLOUD'], '1')
        self.assertEqual(env['OLLAMA_HOST'], '127.0.0.1:11434')
        self.assertEqual(env['OLLAMA_MODELS'], str(self.root / 'models'))
        self.assertFalse(spawn.call_args.kwargs['shell'])
        self.assertEqual(dict(os.environ), before)
        self.assertFalse(result['inference_performed'])
        self.assertFalse(result['cloud_disabled_verified'])

    def test_invalid_executables_ports_and_paths_rejected(self):
        with patch.object(local_ollama.subprocess, 'Popen') as spawn:
            for executable, models, port in ((self.root / 'setup.exe', self.root / 'models', 11434),
                                             (self.exe, Path('relative'), 11434),
                                             (self.exe, self.root / 'models', 80)):
                with self.assertRaises(ValueError):
                    local_ollama.start(executable, models, self.root / 'logs', port)
            spawn.assert_not_called()

    def test_early_exit_reports_its_log(self):
        process = Mock()
        process.poll.return_value = 1
        with patch.object(local_ollama, 'version', side_effect=OSError('missing')), patch.object(
                local_ollama.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'OLLAMA_START_FAILED'):
                local_ollama.start(self.exe, self.root / 'models', self.root / 'logs')
