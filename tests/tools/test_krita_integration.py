"""Krita handoff regression tests. No installed applications execute."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lib import external_applications as applications


class KritaIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        configuration = patch.object(applications.studio, 'CONFIG_DIR', self.root / 'config')
        configuration.start()
        self.addCleanup(configuration.stop)
        children = patch.object(applications, 'CHILDREN', {})
        children.start()
        self.addCleanup(children.stop)
        self.existing = {'blender': {'executable': 'saved-blender'},
                         'freecad': {'executable': 'saved-freecad'}}
        applications.studio.save_json(applications.studio.CONFIG_DIR / 'applications.json', self.existing)
        self.executable = self.root / 'krita.exe'
        self.executable.touch()
        applications.configure('krita', {'executable': str(self.executable)})
        self.project = self.root / 'project'
        self.project.mkdir()

    def test_configuration_preserves_existing_bindings(self):
        saved = applications.configuration()
        for key, value in self.existing.items():
            self.assertEqual(saved[key], value)
        row = next(row for row in applications.catalog() if row['id'] == 'krita')
        self.assertEqual(row['executable'], str(self.executable))
        self.assertTrue(row['configured'] and row['file_found'])
        self.assertEqual(row['integration'], 'project_file_handoff')
        self.assertFalse(row['inference_verified'])
        self.assertFalse(row.get('automation_tools'))

    def test_launch_passes_kra_to_krita(self):
        source = self.project / 'drawing.kra'
        source.touch()
        child = Mock(pid=123)
        child.poll.return_value = None
        with patch.object(applications.studio, 'project_path', return_value=self.project), patch.object(
                applications.subprocess, 'Popen', return_value=child) as launch:
            result = applications.launch('krita', 'fixture', 'drawing.kra')
        self.assertEqual(launch.call_args.args[0], [str(self.executable), str(source)])
        self.assertFalse(launch.call_args.kwargs['shell'])
        self.assertEqual(result['status'], 'launched_not_verified')

    def test_launch_rejects_unsupported_or_outside_files(self):
        (self.project / 'unsupported.exe').touch()
        (self.root / 'outside.kra').touch()
        with patch.object(applications.studio, 'project_path', return_value=self.project), patch.object(
                applications.subprocess, 'Popen') as launch:
            for filename in ['unsupported.exe', '../outside.kra']:
                with self.subTest(filename=filename), self.assertRaises(ValueError):
                    applications.launch('krita', 'fixture', filename)
            launch.assert_not_called()
