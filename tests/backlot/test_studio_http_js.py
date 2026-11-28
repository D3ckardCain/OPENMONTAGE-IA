"""Only the new E02 transport contract; no browser/Studio/model dependencies."""
from pathlib import Path
import shutil
import subprocess
import pytest


def test_studio_http_contract():
    node=shutil.which('node')
    if not node:
        pytest.skip('Node local no disponible; no se instala automáticamente')
    root=Path(__file__).resolve().parents[2]
    result=subprocess.run([node,'--test','tests/js/studio-http.test.mjs'],cwd=root,
                          capture_output=True,text=True,encoding='utf-8',timeout=30)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
