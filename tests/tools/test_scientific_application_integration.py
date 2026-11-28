"""Desktop handoff checks use temporary files and mocked processes."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lib import external_applications as applications


class ScientificApplicationIntegrationTests(unittest.TestCase):
    applications_to_check = (
        ('avogadro', 'avogadro2.exe', 'molecule.cml'),
        ('openmodelica', 'OMEdit.exe', 'model.mo'),
    )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for target, name, value in (
            (applications.studio, 'CONFIG_DIR', self.root / 'config'),
            (applications, 'CHILDREN', {}),
            (applications.studio, 'project_path', Mock(return_value=self.root)),
        ):
            replacement = patch.object(target, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        self.existing = {
            name: {'executable': 'saved-' + name}
            for name in ('blender', 'freecad', 'krita', 'kinovea', 'openscad', 'solvespace')
        }
        applications.studio.save_json(
            applications.studio.CONFIG_DIR / 'applications.json', self.existing)
        self.executables = {}
        for identifier, filename, _ in self.applications_to_check:
            executable = self.root / filename
            executable.touch()
            self.executables[identifier] = executable
            applications.configure(identifier, {'executable': str(executable)})

    def test_configuration_preserves_existing_applications(self):
        saved = applications.configuration()
        for identifier, value in self.existing.items():
            self.assertEqual(saved[identifier], value)

    def test_catalog_reports_handoff_without_verified_automation(self):
        rows = {row['id']: row for row in applications.catalog()}
        for identifier, _, _ in self.applications_to_check:
            with self.subTest(application=identifier):
                row = rows[identifier]
                self.assertTrue(row['configured'] and row['file_found'])
                self.assertEqual(row['integration'], 'project_file_handoff')
                self.assertFalse(row['inference_verified'])
                self.assertFalse(row.get('automation_tools'))

    def test_launch_uses_saved_executable_and_project_file(self):
        for identifier, _, filename in self.applications_to_check:
            with self.subTest(application=identifier):
                source = self.root / filename
                source.touch()
                child = Mock(pid=123)
                child.poll.return_value = None
                with patch.object(applications.subprocess, 'Popen', return_value=child) as launch:
                    record = applications.launch(identifier, 'fixture', filename)
                self.assertEqual(
                    launch.call_args.args[0], [str(self.executables[identifier]), str(source)])
                self.assertFalse(launch.call_args.kwargs['shell'])
                self.assertEqual(record['status'], 'launched_not_verified')

    def test_installers_and_external_or_unsupported_files_are_rejected(self):
        installer = self.root / 'installer.exe'
        installer.touch()
        outside = self.root.parent / (self.root.name + '-outside.cml')
        outside.touch()
        self.addCleanup(outside.unlink)
        for identifier, _, _ in self.applications_to_check:
            with self.subTest(application=identifier), patch.object(
                    applications.subprocess, 'Popen') as launch:
                with self.assertRaises(ValueError):
                    applications.configure(identifier, {'executable': str(installer)})
                for filename in ('installer.exe', '../' + outside.name):
                    with self.assertRaises(ValueError):
                        applications.launch(identifier, 'fixture', filename)
                launch.assert_not_called()
