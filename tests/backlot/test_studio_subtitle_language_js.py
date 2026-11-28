"""New language selector contract only, no old browser suite."""
from pathlib import Path
import shutil
import subprocess
import pytest


def test_subtitle_language_selector_javascript():
    node=shutil.which('node')
    if node is None:
        pytest.skip('Prepared Node unavailable')
    result=subprocess.run([node,'--test','tests/js/editor-subtitle-language.test.mjs'],
        cwd=Path(__file__).resolve().parents[2],capture_output=True,timeout=20)
    assert result.returncode==0,(result.stdout+result.stderr).decode('utf-8','replace')
