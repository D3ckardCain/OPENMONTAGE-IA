"""Focused JavaScript contract test for editor-owned context actions."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_studio_context_menu_contract():
    node = os.environ.get('OPENMONTAGE_TEST_NODE') or shutil.which('node')
    if not node:
        pytest.skip('Node.js is not on PATH; run tests/js/editor-context-menu.test.mjs with the prepared runtime')
    result = subprocess.run(
        [node, '--test', 'tests/js/editor-context-menu.test.mjs'],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, timeout=30,
    )
    assert result.returncode == 0, (result.stdout + result.stderr).decode('utf-8', 'replace')
