"""Download failures reproduced with tiny synthetic files, no real model weights."""
import json
import struct

import pytest
from scripts.check_local_models import inspect_model, required_models, main


def model_file(path, *, payload=b'abcd', offsets=None):
    header = json.dumps({'weight': {'dtype': 'U8', 'shape': [4],
                                   'data_offsets': offsets or [0, 4]}}).encode()
    path.write_bytes(struct.pack('<Q', len(header)) + header + payload)
    return path


def test_readable_header_does_not_claim_verified_weights(tmp_path):
    path = model_file(tmp_path / 'valid.safetensors')
    before = path.read_bytes()
    status, detail = inspect_model(path)
    assert status == 'HEADER_OK'
    assert 'checksum not verified' in detail
    assert path.read_bytes() == before


@pytest.mark.parametrize('content', [b'<!doctype html><html>download page</html>',
    b'\xef\xbb\xbf \n<HTML>error</HTML>', b'', b'123',
    b'version https://git-lfs.github.com/spec/v1\noid sha256:123',
    struct.pack('<Q', 100) + b'{}', struct.pack('<Q', 2) + b'[]',
    struct.pack('<Q', 2) + b'{}', struct.pack('<Q', 2**60)])
def test_bad_downloads_fail_without_mutation(tmp_path, content):
    path = tmp_path / 'bad.safetensors'
    path.write_bytes(content)
    assert inspect_model(path)[0] == 'INVALID'
    assert path.read_bytes() == content


@pytest.mark.parametrize('payload,offsets', [(b'ab', [0, 4]), (b'abcd', [1, 4]),
    (b'abcde', [0, 4]), (b'abcd', [0, True]), (b'abcd', [4, 1])])
def test_truncation_and_bad_offsets(tmp_path, payload, offsets):
    path = model_file(tmp_path / 'bad.safetensors', payload=payload, offsets=offsets)
    assert inspect_model(path)[0] == 'INVALID'


def test_missing_file(tmp_path):
    assert inspect_model(tmp_path / 'missing.safetensors')[0] == 'MISSING'


def test_exact_graph_stacks_separate_i2v_from_t2v():
    t2v, i2v = required_models('t2v'), required_models('i2v')
    assert len(t2v) == len(i2v) == 6
    assert len(required_models('all')) == 10
    assert all('_t2v_' in str(p) for p in t2v if p.parent.name == 'loras')
    assert all('_i2v_' in str(p) for p in i2v if p.parent.name == 'loras')


def test_cli_nonzero_on_missing_and_zero_on_readable_stack(tmp_path, capsys):
    assert main(['--models-dir', str(tmp_path), '--operation', 'i2v']) == 1
    for relative in required_models('i2v'):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        model_file(path)
    assert main(['--models-dir', str(tmp_path), '--operation', 'i2v']) == 0
    assert 'checksum' in capsys.readouterr().out
