"""OSGeo4W Qt5 process environment; never changes the host Python or PATH."""
import os
from pathlib import Path


def environment(executable):
    executable = Path(executable).resolve()
    if executable.name.casefold() not in ('qgis-bin.exe', 'qgis-ltr-bin.exe') or executable.parent.name.casefold() != 'bin':
        raise ValueError('QGIS_RUNTIME_INVALID: selecciona bin/qgis-bin.exe o bin/qgis-ltr-bin.exe de OSGeo4W')
    root = executable.parent.parent
    prefix = root / 'apps' / ('qgis-ltr' if executable.name.casefold() == 'qgis-ltr-bin.exe' else 'qgis')
    qt = root / 'apps' / 'Qt5'
    python = [path for path in (root / 'apps').glob('Python3*') if (path / 'Lib' / 'os.py').is_file()]
    required = [executable, prefix / 'bin' / 'qgis_core.dll', prefix / 'python' / 'qgis' / '__init__.py',
                qt / 'bin' / 'Qt5Core.dll', qt / 'plugins' / 'platforms' / 'qwindows.dll',
                root / 'share' / 'proj' / 'proj.db']
    missing = [str(path) for path in required if not path.is_file()]
    if missing or len(python) != 1 or not (root / 'apps' / 'gdal' / 'share' / 'gdal').is_dir():
        raise ValueError('QGIS_RUNTIME_INCOMPLETE: faltan recursos Qt5/GDAL/PROJ/Python de la distribución; ' + ', '.join(missing))
    python = python[0]
    blocked = ('PYTHON', 'QT_', 'QGIS', 'GDAL', 'PROJ', 'OSGEO', 'O4W_', 'VIRTUAL_ENV', 'CONDA')
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(blocked) and key.upper() != 'PATH'}
    windows = Path(os.environ.get('SystemRoot', r'C:\Windows'))
    env.update({
        'PATH': ';'.join(str(path) for path in (prefix / 'bin', qt / 'bin', python / 'Scripts', root / 'bin',
                                               windows / 'System32', windows, windows / 'System32' / 'Wbem')),
        'OSGEO4W_ROOT': str(root), 'QGIS_PREFIX_PATH': prefix.as_posix(),
        'QT_PLUGIN_PATH': ';'.join(str(path) for path in (prefix / 'qtplugins', qt / 'plugins')),
        'QT_QPA_PLATFORM_PLUGIN_PATH': str(qt / 'plugins' / 'platforms'),
        'PYTHONHOME': str(python), 'PYTHONPATH': str(prefix / 'python'), 'PYTHONNOUSERSITE': '1',
        'PYTHONUTF8': '1', 'PYTHONEXECUTABLE': str(root / 'bin' / 'python3.exe'),
        'GDAL_DATA': str(root / 'apps' / 'gdal' / 'share' / 'gdal'),
        'PROJ_DATA': str(root / 'share' / 'proj'), 'PROJ_LIB': str(root / 'share' / 'proj'),
        'PROJ_NETWORK': 'OFF', 'GDAL_DRIVER_PATH': str(root / 'apps' / 'gdal' / 'lib' / 'gdalplugins'),
        'GDAL_FILENAME_IS_UTF8': 'YES', 'VSI_CACHE': 'TRUE', 'VSI_CACHE_SIZE': '1000000',
    })
    for key, relative in (('PREFIX', ''), ('BINARIES', 'bin'), ('PLUGINS', 'plugins'),
                          ('LIBRARIES', 'lib'), ('TRANSLATIONS', 'translations'), ('HEADERS', 'include')):
        env['O4W_QT_' + key] = (qt / relative).as_posix()
    return env


def launch_options(executable, profiles):
    profiles = Path(profiles).resolve()
    env = environment(executable)
    profiles.mkdir(parents=True, exist_ok=True)
    return ([str(executable), '--profiles-path', str(profiles), '--profile', 'openmontage',
             '--noplugins', '--noversioncheck'], {'env': env})
