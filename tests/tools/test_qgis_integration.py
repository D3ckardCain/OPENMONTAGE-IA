"""Synthetic OSGeo4W layouts, no QGIS process, layers or maps."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from lib import external_applications as applications
from lib import qgis_runtime


class QgisIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.install = self.root / 'QGIS with spaces & accents'
        self.executable = self.install / 'bin/qgis-ltr-bin.exe'
        for name in ('bin/qgis-ltr-bin.exe', 'apps/qgis-ltr/bin/qgis_core.dll',
                     'apps/qgis-ltr/python/qgis/__init__.py', 'apps/Qt5/bin/Qt5Core.dll',
                     'apps/Qt5/plugins/platforms/qwindows.dll', 'share/proj/proj.db',
                     'apps/Python312/Lib/os.py'):
            path = self.install / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        (self.install / 'apps/gdal/share/gdal').mkdir(parents=True)
        for target, name, value in ((applications.studio, 'CONFIG_DIR', self.root / 'config'),
                                     (applications.studio, 'project_path', Mock(return_value=self.root)),
                                     (applications, 'CHILDREN', {})):
            replacement = patch.object(target, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        self.saved = {name: {'executable': 'saved-' + name} for name in
                      ('blender', 'freecad', 'krita', 'kinovea', 'openscad', 'rhubarb')}
        applications.studio.save_json(applications.studio.CONFIG_DIR / 'applications.json', self.saved)
        applications.configure('qgis', {'executable': str(self.executable)})

    def test_environment_is_local_and_discards_foreign_runtime(self):
        foreign = {'PYTHONHOME': 'comfy', 'PYTHONPATH': 'studio', 'VIRTUAL_ENV': 'venv',
                   'QT_PLUGIN_PATH': 'foreign', 'QGIS_PLUGINPATH': 'foreign', 'PROJ_NETWORK': 'ON',
                   'PATH': 'foreign-dlls', 'QT_QPA_PLATFORM': 'offscreen'}
        with patch.dict(os.environ, foreign):
            before = dict(os.environ)
            env = qgis_runtime.environment(self.executable)
            self.assertEqual(dict(os.environ), before)
        self.assertNotIn('foreign-dlls', env['PATH'])
        self.assertNotIn('VIRTUAL_ENV', env)
        self.assertNotIn('QGIS_PLUGINPATH', env)
        self.assertNotIn('QT_QPA_PLATFORM', env)
        self.assertEqual(env['PYTHONHOME'], str(self.install / 'apps/Python312'))
        self.assertEqual(env['PROJ_NETWORK'], 'OFF')
        self.assertEqual(env['PYTHONNOUSERSITE'], '1')
        self.assertEqual(env['QGIS_PREFIX_PATH'], (self.install / 'apps/qgis-ltr').as_posix())

    def test_launch_reuses_binding_with_separate_profile_and_safe_arguments(self):
        source = self.root / 'project & quoted.qgz'
        source.touch()
        child = Mock(pid=321)
        child.poll.return_value = None
        with patch.object(applications.subprocess, 'Popen', return_value=child) as launch:
            result = applications.launch('qgis', 'fixture', source.name)
            args = launch.call_args.args[0]
            self.assertEqual(args[0], str(self.executable))
            self.assertEqual(args[-1], str(source))
            self.assertIn('--noplugins', args)
            self.assertIn('--noversioncheck', args)
            self.assertIn(str(applications.studio.CONFIG_DIR / 'qgis'), args)
            self.assertFalse(launch.call_args.kwargs['shell'])
            self.assertEqual(launch.call_args.kwargs['env']['PROJ_NETWORK'], 'OFF')
            self.assertEqual(result['status'], 'launched_not_verified')
            with self.assertRaises(ValueError):
                applications.launch('qgis', 'fixture')
            self.assertEqual(launch.call_count, 1)

    def test_registration_preserves_existing_configurations(self):
        saved = applications.configuration()
        for name, value in self.saved.items():
            self.assertEqual(saved[name], value)
        row = next(row for row in applications.catalog() if row['id'] == 'qgis')
        self.assertTrue(row['file_found'])
        self.assertEqual(row['integration'], 'project_file_handoff')
        self.assertFalse(row['inference_verified'])

    def test_missing_resources_block_launch(self):
        (self.install / 'apps/Qt5/plugins/platforms/qwindows.dll').unlink()
        with patch.object(applications.subprocess, 'Popen') as launch:
            with self.assertRaisesRegex(ValueError, 'QGIS_RUNTIME_INCOMPLETE'):
                applications.launch('qgis', 'fixture')
            launch.assert_not_called()

    def test_installer_and_arbitrary_batch_are_rejected(self):
        with patch.object(applications.subprocess, 'Popen') as launch:
            for name in ('QGIS-setup.exe', 'qgis-ltr.bat', 'QGIS.msi'):
                path = self.root / name
                path.touch()
                with self.assertRaises(ValueError):
                    applications.configure('qgis', {'executable': str(path)})
            launch.assert_not_called()

    def test_only_project_files_inside_workspace_are_passed(self):
        with patch.object(applications.subprocess, 'Popen') as launch:
            for name in ('anything.py', '../outside.qgz'):
                with self.assertRaises(ValueError):
                    applications.launch('qgis', 'fixture', name)
            launch.assert_not_called()

    def test_invalid_or_ambiguous_runtime_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'QGIS_RUNTIME_INVALID'):
            qgis_runtime.environment(self.root / 'qgis-ltr.bat')
        other = self.install / 'apps/Python313/Lib/os.py'
        other.parent.mkdir(parents=True)
        other.touch()
        with self.assertRaisesRegex(ValueError, 'QGIS_RUNTIME_INCOMPLETE'):
            qgis_runtime.environment(self.executable)
