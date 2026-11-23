"""Expose explicitly saved local CLIs inside the Studio server process only."""
import os
from pathlib import Path
from lib import production_studio as studio
from lib.media_executables import find_media


def configured_environment(base=None):
    env = dict(os.environ if base is None else base)
    folders = []
    for name in ('ffmpeg', 'ffprobe'):
        path = find_media(name)
        if path:
            folder = str(Path(path).resolve().parent)
            if folder not in folders:
                folders.append(folder)
    configured = studio.read_json(studio.CONFIG_DIR / 'applications.json', {}).get('node', {}).get('executable')
    if configured:
        node = Path(configured)
        if node.is_absolute() and node.name.casefold() in ('node.exe', 'node') and node.is_file():
            # An embedded node.exe is not necessarily a complete Node/npm distribution.
            npm, npx = ('npm.cmd', 'npx.cmd') if node.suffix.casefold() == '.exe' else ('npm', 'npx')
            if all((node.parent / name).is_file() for name in (npm, npx)):
                folder = str(node.resolve().parent)
                if folder not in folders:
                    folders.append(folder)
    if folders:
        original = [part for part in env.get('PATH', '').split(os.pathsep) if part]
        env['PATH'] = os.pathsep.join(folders + [part for part in original if part not in folders])
    return env
