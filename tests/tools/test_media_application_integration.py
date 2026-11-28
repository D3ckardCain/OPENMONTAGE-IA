"""Managed CLI bindings never launch installers or independent consoles."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib import external_applications as applications


class MediaApplicationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        configuration = patch.object(applications.studio, 'CONFIG_DIR', self.root / 'config')
        configuration.start()
        self.addCleanup(configuration.stop)
        self.desktop = {'avogadro': {'executable': 'saved-avogadro'}}
        applications.studio.save_json(
            applications.studio.CONFIG_DIR / 'applications.json', self.desktop)
        applications.studio.configure({'model': 'saved-model', 'max_turns': 42})
        self.identifiers = ('ffmpeg', 'ffprobe', 'yt-dlp', 'deno')

    def test_configure_preserves_settings_and_desktop_bindings_without_execution(self):
        with patch.object(applications.subprocess, 'Popen') as launch:
            for identifier in self.identifiers:
                executable = self.root / (identifier + '.exe')
                executable.touch()
                result = applications.configure(identifier, {'executable': str(executable)})
                self.assertFalse(result['launched'])
                key = applications.CATALOG[identifier]['setting']
                self.assertEqual(applications.studio.settings()[key], str(executable))
            launch.assert_not_called()
        self.assertEqual(applications.configuration(), self.desktop)
        settings = applications.studio.settings()
        self.assertEqual(settings['model'], 'saved-model')
        self.assertEqual(settings['max_turns'], 42)

    def test_catalog_classifies_cli_tools_as_managed(self):
        rows = {row['id']: row for row in applications.catalog()}
        for identifier in self.identifiers:
            self.assertEqual(rows[identifier]['mode'], 'managed_cli')
            self.assertEqual(rows[identifier]['integration'], 'managed_pipeline')

    def test_desktop_launch_rejects_cli_tools(self):
        with patch.object(applications.subprocess, 'Popen') as launch:
            for identifier in self.identifiers:
                with self.subTest(application=identifier), self.assertRaises(ValueError):
                    applications.launch(identifier, 'fixture')
            launch.assert_not_called()
