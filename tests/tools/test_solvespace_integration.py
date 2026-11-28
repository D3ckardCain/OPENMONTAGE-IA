"""SolveSpace handoff regression tests. No installed applications execute."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lib import external_applications as applications


class SolveSpaceIntegrationTests(unittest.TestCase):
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
                         'freecad': {'executable': 'saved-freecad'},
                         'krita': {'executable': 'saved-krita'},
                         'kinovea': {'executable': 'saved-kinovea'}}
        applications.studio.save_json(applications.studio.CONFIG_DIR / 'applications.json', self.existing)
        self.executable = self.root / 'solvespace_single_core_x64.exe'
        self.executable.touch()
        applications.configure('solvespace', {'executable': str(self.executable)})
        self.project = self.root / 'project'
        self.project.mkdir()

    def test_configuration_preserves_existing_bindings(self):
        saved = applications.configuration()
        for key, value in self.existing.items():
            self.assertEqual(saved[key], value)
        row = next(row for row in applications.catalog() if row['id'] == 'solvespace')
        self.assertEqual(row['executable'], str(self.executable))
        self.assertTrue(row['configured'] and row['file_found'])
        self.assertEqual(row['integration'], 'project_file_handoff')
        self.assertFalse(row['inference_verified'])
        self.assertFalse(row.get('automation_tools'))

    def test_launch_passes_design_to_solvespace(self):
        source = self.project / 'design.slvs'
        source.touch()
        child = Mock(pid=123)
        child.poll.return_value = None
        with patch.object(applications.studio, 'project_path', return_value=self.project), patch.object(
                applications.subprocess, 'Popen', return_value=child) as launch:
            result = applications.launch('solvespace', 'fixture', 'design.slvs')
        self.assertEqual(launch.call_args.args[0], [str(self.executable), str(source)])
        self.assertFalse(launch.call_args.kwargs['shell'])
        self.assertEqual(result['status'], 'launched_not_verified')

    def test_launch_rejects_unsupported_or_outside_files(self):
        (self.project / 'unsupported.exe').touch()
        (self.root / 'outside.slvs').touch()
        with patch.object(applications.studio, 'project_path', return_value=self.project), patch.object(
                applications.subprocess, 'Popen') as launch:
            for filename in ['unsupported.exe', '../outside.slvs']:
                with self.subTest(filename=filename), self.assertRaises(ValueError):
                    applications.launch('solvespace', 'fixture', filename)
            launch.assert_not_called()
