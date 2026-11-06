"""Corrupt downloads, shared groups and relocatable Windows archive layout."""
import hashlib
import json
from pathlib import Path
import pytest
from scripts.verify_model_downloads import relative_destination, select_entries, verify_file, main


def entry(content=b'abcd', destination='C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae/test.safetensors'):
    return {'destination': destination, 'size_bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}


def manifest(e):
    return {'files': [e], 'groups': [{'id': 'wan', 'files': [e['destination']]},
                                    {'id': 'shared', 'files': [e['destination']]}]}


def test_same_size_wrong_content_is_detected_only_by_hash(tmp_path):
    p = tmp_path / 'model'; p.write_bytes(b'xxxx')
    assert verify_file(p, entry())[0] == 'SIZE_OK'
    assert verify_file(p, entry(), True)[0] == 'HASH_MISMATCH'
    assert p.read_bytes() == b'xxxx'


def test_expected_digest_and_file_unchanged(tmp_path):
    p = tmp_path / 'model'; p.write_bytes(b'abcd')
    assert verify_file(p, entry(), True)[0] == 'SHA256_OK'
    assert p.read_bytes() == b'abcd'


def test_size_missing_directory_and_unknown_hash(tmp_path):
    p = tmp_path / 'file'
    assert verify_file(p, entry())[0] == 'MISSING'
    p.write_bytes(b'ab')
    assert verify_file(p, entry(), True)[0] == 'SIZE_MISMATCH'
    assert verify_file(tmp_path, entry())[0] == 'INVALID'
    p.write_bytes(b'abcd'); e = entry(); e['sha256'] = None
    assert verify_file(p, e, True)[0] == 'HASH_UNAVAILABLE'


@pytest.mark.parametrize('destination', ['C:/else/file', 'C:/OPENMONTAJE-IA/../outside',
    'C:/OPENMONTAJE-IA/C:/outside', 'C:/OPENMONTAJE-IA//absolute', 'C:/OPENMONTAJE-IA/', 123])
def test_invalid_destination_rejected(destination):
    with pytest.raises(ValueError): relative_destination(destination)


def test_windows_paths_and_group_deduplication():
    e = entry()
    assert relative_destination(e['destination'].replace('/', '\\')).parts[0] == 'ComfyUI_windows_portable'
    assert select_entries(manifest(e), ['all']) == [e]
    assert select_entries(manifest(e), ['wan', 'shared']) == [e]
    with pytest.raises(ValueError): select_entries(manifest(e), ['missing'])


@pytest.mark.parametrize('mutation', ['digest', 'size', 'duplicate', 'reference'])
def test_bad_manifest_rejected_before_file_access(mutation):
    e = entry(); m = manifest(e)
    if mutation == 'digest': e['sha256'] = 'untrusted'
    elif mutation == 'size': e['size_bytes'] = True
    elif mutation == 'duplicate': m['files'].append(e)
    else: m['groups'][0]['files'].append('missing')
    with pytest.raises(ValueError): select_entries(m, ['wan'])


def test_cli_remapped_root_and_hash_reporting(tmp_path, capsys):
    e = entry(); p = tmp_path / relative_destination(e['destination']); p.parent.mkdir(parents=True)
    p.write_bytes(b'abcd'); index = tmp_path / 'manifest.json'; index.write_text(json.dumps(manifest(e)))
    args = ['--root', str(tmp_path), '--manifest', str(index)]
    assert main(args) == 0
    assert 'SIZE_OK' in capsys.readouterr().out
    assert main(args + ['--sha256']) == 0
    assert 'SHA256_OK' in capsys.readouterr().out
    p.write_bytes(b'xxxx')
    assert main(args + ['--sha256']) == 1


def test_real_manifest_has_unique_destinations_and_all_groups_resolve():
    p = Path(__file__).parents[2] / 'docs/model_download_manifest.json'
    m = json.loads(p.read_text())
    assert len(select_entries(m, ['all'])) == 375
    assert len(select_entries(m, ['wan'])) == 12


def test_cli_hash_requested_but_unavailable_is_incomplete(tmp_path, capsys):
    e = entry(); e['sha256'] = None
    p = tmp_path / relative_destination(e['destination']); p.parent.mkdir(parents=True); p.write_bytes(b'abcd')
    index = tmp_path / 'manifest.json'; index.write_text(json.dumps(manifest(e)))
    assert main(['--root', str(tmp_path), '--manifest', str(index), '--sha256']) == 3
    assert 'HASH_UNAVAILABLE' in capsys.readouterr().out


def test_file_changed_while_hashing_is_not_certified(tmp_path, monkeypatch):
    p = tmp_path / 'model'; p.write_bytes(b'abcd')
    original = hashlib.sha256
    expected = entry()
    class ChangingHash:
        def __init__(self): self.digest = original()
        def update(self, block):
            self.digest.update(block)
            p.write_bytes(b'changed-during-read')
        def hexdigest(self): return self.digest.hexdigest()
    monkeypatch.setattr('scripts.verify_model_downloads.hashlib.sha256', ChangingHash)
    assert verify_file(p, expected, True)[0] == 'CHANGED'
