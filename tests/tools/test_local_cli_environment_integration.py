"""Saved CLIs enter the server environment without changing Windows settings."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lib import local_cli_environment as cli
from lib import external_applications as applications


class LocalCliEnvironmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.node = self.root / 'node.exe'
        for name in ('node.exe', 'npm.cmd', 'npx.cmd'):
            (self.root / name).touch()
        for target, name, value in ((cli.studio, 'CONFIG_DIR', self.root / 'config'),
                                     (cli, 'find_media', lambda name: None)):
            replacement = patch.object(target, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def test_saved_node_and_previous_configuration_preserved(self):
        previous = {'blender': {'executable': 'saved-blender'}, 'qgis': {'executable': 'saved-qgis'}}
        cli.studio.save_json(cli.studio.CONFIG_DIR / 'applications.json', previous)
        applications.configure('node', {'executable': str(self.node)})
        for name, value in previous.items():
            self.assertEqual(applications.configuration()[name], value)
        before = dict(os.environ)
        env = cli.configured_environment({'PATH': 'original', 'EXAMPLE': 'preserved'})
        self.assertEqual(env['PATH'], str(self.root) + os.pathsep + 'original')
        self.assertEqual(env['EXAMPLE'], 'preserved')
        self.assertEqual(dict(os.environ), before)
        self.assertEqual(cli.configured_environment(env), env)

    def test_partial_embedded_runtime_and_missing_disk_do_not_break_startup(self):
        applications.configure('node', {'executable': str(self.node)})
        (self.root / 'npx.cmd').unlink()
        self.assertEqual(cli.configured_environment({'PATH': 'original'}), {'PATH': 'original'})
        self.node.unlink()
        self.assertEqual(cli.configured_environment({'PATH': 'original'}), {'PATH': 'original'})

    def test_media_paths_shared_with_server_and_deduplicated(self):
        media = self.root / 'media/ffmpeg.exe'
        with patch.object(cli, 'find_media', return_value=str(media)):
            env = cli.configured_environment({'PATH': 'original'})
        self.assertEqual(env['PATH'], str(media.parent) + os.pathsep + 'original')

    def test_node_is_managed_and_cannot_open_console_or_installer(self):
        applications.configure('node', {'executable': str(self.node)})
        with patch.object(applications.subprocess, 'Popen') as launch:
            with self.assertRaises(ValueError):
                applications.launch('node', 'fixture')
            installer = self.root / 'node-setup.exe'
            installer.touch()
            with self.assertRaises(ValueError):
                applications.configure('node', {'executable': str(installer)})
            launch.assert_not_called()

    def test_server_applies_configured_environment_before_starting_uvicorn(self):
        from backlot import __main__ as backlot_cli
        with patch.dict(os.environ, {'PATH': 'original'}), patch.object(cli, 'configured_environment',
                return_value={'PATH': 'server-only'}), patch('backlot.runtime.StudioServer') as server:
            server.return_value.started = True
            self.assertEqual(backlot_cli.cmd_serve(4751), 0)
            self.assertEqual(os.environ['PATH'], 'server-only')
            server.assert_called_once()
            config = server.call_args.args[0]
            self.assertEqual((config.host, config.port, config.log_level), ('127.0.0.1', 4751, 'warning'))
            server.return_value.run.assert_called_once_with()
