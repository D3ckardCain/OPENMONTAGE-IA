"""Locate FreeCAD's bundled Python without modifying any installed runtime."""
import os
from pathlib import Path
from lib.external_applications import configuration


def python_environment():
    configured = configuration().get('freecad', {}).get('executable', '')
    if not configured:
        raise ValueError('FREECAD_RUNTIME_MISSING: registra el FreeCAD preparado')
    executable = Path(configured).resolve()
    if not executable.is_file() or executable.name.casefold() != 'freecad.exe':
        raise ValueError('FREECAD_RUNTIME_INVALID: ruta guardada no admitida')
    candidates = [executable.parent, executable.parent / 'bin']
    candidates = [p for p in candidates if (p / 'python.exe').is_file() and (p / 'FreeCAD.pyd').is_file()]
    if len(candidates) != 1:
        raise ValueError('FREECAD_RUNTIME_MISSING: no se localizó un Python/FreeCAD.pyd inequívoco')
    binary_dir = candidates[0]
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(
        ('PYTHON', 'QT_', 'QGIS', 'PYQGIS', 'PROJ', 'GDAL', 'VIRTUAL_ENV', 'CONDA', 'FREECAD')) and k.upper() != 'PATH'}
    windows = Path(os.environ.get('SystemRoot', r'C:\Windows'))
    env['PATH'] = os.pathsep.join(str(p) for p in (binary_dir, windows / 'System32', windows))
    return binary_dir / 'python.exe', env
