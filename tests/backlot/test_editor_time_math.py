"""Run dependency-free Node tests for the actual browser timeline arithmetic."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_browser_timeline_arithmetic():
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node is unavailable; run tests/js/editor-time.test.mjs on the prepared Node runtime')
    result = subprocess.run([node, '--test', 'tests/js/editor-time.test.mjs'],
                            cwd=Path(__file__).resolve().parents[2], capture_output=True, timeout=30)
    assert result.returncode == 0, (result.stdout + result.stderr).decode('utf-8', 'replace')
