"""Run the provisioning shell against fake CLIs: no sudo, apt or network executes."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash') or str(Path('C:/Program Files/Git/usr/bin/bash.exe'))


def shell_path(path):
    value = Path(path).resolve().as_posix()
    return '/' + value[0].lower() + value[2:] if os.name == 'nt' else value


@unittest.skipUnless(Path(BASH).is_file(), 'bash not available for isolated CI shell test')
class MediaCliProvisioningTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'log.txt'
        self.env = dict(os.environ, PATH=shell_path(self.bin), MEDIA_CI_LOG=shell_path(self.log), MOCK_CLI_BIN=shell_path(self.bin))
        self.write('timeout', '#!/bin/sh\nprintf "timeout %s\\n" "$*" >> "$MEDIA_CI_LOG"\nshift 2\nexec "$@"\n')
        self.write('sudo', '''#!/bin/sh
printf "sudo %s\\n" "$*" >> "$MEDIA_CI_LOG"
case "$*" in
  *update*) if [ "${MEDIA_CI_FAIL_UPDATE:-0}" = 1 ]; then exit 7; fi ;;
  *install*)
    for name in ffmpeg ffprobe; do
      printf '#!/bin/sh\\nexit 0\\n' > "$MOCK_CLI_BIN/$name"
      /bin/chmod +x "$MOCK_CLI_BIN/$name"
    done ;;
esac
''')

    def write(self, name, content):
        path = self.bin / name
        path.write_text(content, encoding='utf-8', newline='\n')
        path.chmod(0o755)

    def run_script(self):
        return subprocess.run([BASH, '--noprofile', '--norc', shell_path(ROOT / '.github/scripts/ensure-media-cli.sh')],
                              env=self.env, capture_output=True, timeout=15)

    def test_both_existing_tools_skip_package_network(self):
        for name in ('ffmpeg', 'ffprobe'):
            self.write(name, '#!/bin/sh\nexit 0\n')
        process = self.run_script()
        self.assertEqual(process.returncode, 0, process.stderr.decode(errors='replace'))
        self.assertFalse(self.log.exists())

    def test_missing_or_partial_cli_runs_bounded_install_and_checks_both(self):
        self.write('ffmpeg', '#!/bin/sh\nexit 0\n')
        process = self.run_script()
        self.assertEqual(process.returncode, 0, process.stderr.decode(errors='replace'))
        log = self.log.read_text()
        self.assertIn('--kill-after=10s 90s sudo apt-get', log)
        self.assertIn('--kill-after=10s 180s sudo apt-get', log)
        self.assertIn('Acquire::Retries=1', log)
        self.assertIn('install -y ffmpeg', log)
        self.assertTrue((self.bin / 'ffprobe').exists())

    def test_failed_update_does_not_attempt_install(self):
        self.env['MEDIA_CI_FAIL_UPDATE'] = '1'
        process = self.run_script()
        self.assertEqual(process.returncode, 7)
        self.assertNotIn('install -y ffmpeg', self.log.read_text())
