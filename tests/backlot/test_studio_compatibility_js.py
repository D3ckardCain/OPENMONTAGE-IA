"""Run only new dependency-free compatibility checks, not old browser suites."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_studio_compatibility_javascript():
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node unavailable; run tests/js/studio-compatibility.test.mjs on prepared runtime')
    result = subprocess.run([node, '--test', 'tests/js/studio-compatibility.test.mjs'],
                            cwd=Path(__file__).resolve().parents[2], capture_output=True, timeout=30)
    assert result.returncode == 0, (result.stdout + result.stderr).decode('utf-8', 'replace')
