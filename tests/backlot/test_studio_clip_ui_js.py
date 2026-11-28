"""Only new E03/E04 JS cases; no old browser suite or audiovisual claim."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_candidate_and_crop_ui_javascript():
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node unavailable; run editor-candidates-ui/crop-preview.test.mjs on prepared runtime')
    result = subprocess.run([node, '--test', 'tests/js/editor-candidates-ui.test.mjs', 'tests/js/editor-candidate-review.test.mjs', 'tests/js/editor-crop-preview.test.mjs'],
                            cwd=Path(__file__).resolve().parents[2], capture_output=True, timeout=30)
    assert result.returncode == 0, (result.stdout + result.stderr).decode('utf-8', 'replace')
