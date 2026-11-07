"""Offline, read-only size/SHA256 check of the pinned candidate manifest.

No tensors are deserialized and no model, executable, GPU or network is used.
Default group: wan. Hashing is explicit because the complete list is over 1 TB.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

MANIFEST = Path(__file__).resolve().parents[1] / 'docs/model_download_manifest.json'
PREFIX = 'C:/OPENMONTAJE-IA/'


def relative_destination(destination: str) -> Path:
    if not isinstance(destination, str):
        raise ValueError('Destination must be a string')
    value = destination.replace('\\', '/')
    if not value.startswith(PREFIX):
        raise ValueError('Destination is outside the expected project root')
    tail = value[len(PREFIX):]
    parts = PurePosixPath(tail).parts
    if not parts or PurePosixPath(tail).is_absolute() or any(
        p in ('.', '..') or ':' in p for p in parts
    ):
        raise ValueError('Invalid relative destination')
    return Path(*parts)


def select_entries(manifest: dict, groups: list[str]) -> list[dict]:
    if not isinstance(manifest, dict):
        raise ValueError('Manifest must be an object')
    if not isinstance(manifest.get('files'), list) or not manifest['files']:
        raise ValueError('Manifest must contain a non-empty files list')
    if not isinstance(manifest.get('groups'), list) or not manifest['groups']:
        raise ValueError('Manifest must contain a non-empty groups list')
    if not groups:
        raise ValueError('Select at least one group')
    entries = {}
    canonical_destinations = set()
    for entry in manifest['files']:
        if not isinstance(entry, dict):
            raise ValueError('File entries must be objects')
        destination = entry['destination']
        canonical = relative_destination(destination).as_posix().casefold()
        if canonical in canonical_destinations:
            raise ValueError('Duplicate destination in manifest')
        if type(entry['size_bytes']) is not int or entry['size_bytes'] < 0:
            raise ValueError('Invalid expected size')
        digest = entry.get('sha256')
        if digest is not None and not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Invalid expected SHA256')
        entries[destination] = entry
        canonical_destinations.add(canonical)
    group_map = {}
    for group in manifest['groups']:
        if not isinstance(group, dict):
            raise ValueError('Group entries must be objects')
        name = group.get('id')
        if not isinstance(name, str) or not name.strip() or name == 'all':
            raise ValueError('Invalid or reserved group ID')
        if name in group_map:
            raise ValueError('Duplicate group ID in manifest')
        destinations = group.get('files')
        if not isinstance(destinations, list) or not destinations:
            raise ValueError('Each group must contain a non-empty files list')
        for destination in destinations:
            if not isinstance(destination, str) or destination not in entries:
                raise ValueError('Group references an unknown destination')
        group_map[name] = group
    unknown = set(groups) - group_map.keys() - {'all'}
    if unknown:
        raise ValueError('Unknown groups: ' + ', '.join(sorted(unknown)))
    chosen = list(group_map) if 'all' in groups else groups
    selected = {}
    for name in chosen:
        for destination in group_map[name]['files']:
            if destination not in entries:
                raise ValueError('Group references an unknown destination')
            selected[destination] = entries[destination]
    return list(selected.values())


def verify_file(path: Path, entry: dict, sha256: bool = False) -> tuple[str, str]:
    try:
        before = path.stat()
        if not path.is_file():
            return 'INVALID', 'expected a regular file'
        if before.st_size != entry['size_bytes']:
            return 'SIZE_MISMATCH', f'expected {entry["size_bytes"]}, found {before.st_size} bytes'
        if not sha256:
            return 'SIZE_OK', 'size only; content and identity not verified'
        expected = entry.get('sha256')
        if not expected:
            return 'HASH_UNAVAILABLE', 'size matches; manifest has no authoritative SHA256'
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                digest.update(block)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (
            after.st_size, after.st_mtime_ns, after.st_ino
        ):
            return 'CHANGED', 'file changed during verification; retry after download finishes'
        if digest.hexdigest() != expected:
            return 'HASH_MISMATCH', 'content differs from the pinned download'
        return 'SHA256_OK', 'matches the SHA256 recorded in the pinned manifest'
    except FileNotFoundError:
        return 'MISSING', 'file not found'
    except OSError as exc:
        return 'UNREADABLE', str(exc)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('C:/OPENMONTAJE-IA'))
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    parser.add_argument('--groups', nargs='+', default=['wan'])
    parser.add_argument('--sha256', action='store_true', help='Read complete files and compare known SHA256 hashes')
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        entries = select_entries(manifest, args.groups)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    failed = 0
    unverified = 0
    for entry in entries:
        relative = relative_destination(entry['destination'])
        status, detail = verify_file(args.root / relative, entry, args.sha256)
        print(f'{status}: {relative.as_posix()}\n  {detail}')
        failed += status not in {'SIZE_OK', 'SHA256_OK', 'HASH_UNAVAILABLE'}
        unverified += status in {'SIZE_OK', 'HASH_UNAVAILABLE'}
    print(f'{len(entries)} files; {failed} failures; {unverified} without content verification.')
    print('Read-only check. License eligibility, dependencies, inference quality and speed are not verified.')
    return 1 if failed else (3 if args.sha256 and unverified else 0)


if __name__ == '__main__':
    raise SystemExit(main())
