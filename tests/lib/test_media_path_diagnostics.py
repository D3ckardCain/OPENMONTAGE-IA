"""Only filesystem failure fixtures; no real drive/model/tool execution."""
import stat
from types import SimpleNamespace

import pytest

from lib import reference_analysis as ref


@pytest.mark.parametrize('failure,root_failure,message', [
    (FileNotFoundError(), FileNotFoundError(), 'no está disponible'),
    (FileNotFoundError(), None, 'no existe'),
    (PermissionError(), None, 'Acceso denegado'),
    (OSError('I/O fixture'), None, 'I/O fixture'),
    (FileNotFoundError(), PermissionError(), 'Acceso denegado a la raíz'),
    (FileNotFoundError(), OSError('root I/O'), 'root I/O'),
])
def test_missing_drive_file_denial_and_io_are_distinct(monkeypatch, failure, root_failure, message):
    class FakePath:
        anchor = 'Z:\\'
        def __init__(self, value): self.value = value
        def stat(self):
            error = root_failure if self.value == self.anchor else failure
            if error is not None: raise error
            return SimpleNamespace(st_mode=stat.S_IFDIR)
    monkeypatch.setattr(ref, 'Path', FakePath)
    with pytest.raises(ValueError, match=message):
        ref._checked_executable('Z:\\tools\\ffmpeg.exe', 'ffmpeg')


def test_configured_path_is_not_replaced_and_success_does_not_execute(tmp_path, monkeypatch):
    path = tmp_path / 'ffmpeg.exe'
    path.write_bytes(b'not executed')
    settings = {'ffmpeg_path': str(path)}
    monkeypatch.setattr(ref.studio, 'settings', lambda: settings)
    def forbidden(*args): raise AssertionError('Configured path must not fall back')
    monkeypatch.setattr(ref.shutil, 'which', forbidden)
    assert ref.executable('ffmpeg') == str(path)
    path.unlink()
    with pytest.raises(ValueError, match='no existe'):
        ref.executable('ffmpeg')
    assert settings == {'ffmpeg_path': str(path)}
    with pytest.raises(ValueError, match='no es un archivo'):
        ref._checked_executable(str(tmp_path), 'ffmpeg')
