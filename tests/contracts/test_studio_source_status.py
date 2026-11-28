import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    'studio_source_status', Path(__file__).resolve().parents[2] / 'scripts/check_studio_source.py')
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    receipt = {'repository': source.REPOSITORY, 'branch': source.BRANCH, 'revision': 'a' * 40}
    (tmp_path / 'INSTALACION_LOCAL.json').write_text(json.dumps(receipt), encoding='utf-8')
    def forbidden(*args):
        raise AssertionError('Unexpected networking')
    monkeypatch.setattr(source, 'remote_json', forbidden)
    return tmp_path


def test_offline_receipt_does_not_certify_current_files(prepared):
    before = list(prepared.iterdir())
    result = source.inspect(prepared)
    assert result['status'] == 'recorded_revision_only'
    assert result['local_files_verified'] is False and result['network_checked'] is False
    assert list(prepared.iterdir()) == before


@pytest.mark.parametrize('relation,state', [
    ('ahead', 'branch_ahead_of_recorded_revision'),
    ('behind', 'branch_behind_recorded_revision'),
    ('diverged', 'branch_diverged_from_receipt')])
def test_commit_relationship_is_not_treated_as_automatic_upgrade(prepared, monkeypatch, relation, state):
    calls = []
    def remote(path):
        calls.append(path)
        return {'object': {'type': 'commit', 'sha': 'b' * 40}} if len(calls) == 1 else {'status': relation}
    monkeypatch.setattr(source, 'remote_json', remote)
    result = source.inspect(prepared, True)
    assert result['status'] == state and result['installation_started'] is False
    assert len(calls) == 2 and calls[1].startswith('compare/' + 'a' * 40 + '...' + 'b' * 40)


def test_matching_branch_only_certifies_recorded_commit(prepared, monkeypatch):
    monkeypatch.setattr(source, 'remote_json', lambda path: {'object': {'sha': 'a' * 40, 'type': 'commit'}})
    result = source.inspect(prepared, True)
    assert result['status'] == 'recorded_revision_matches_branch'
    assert result['local_files_verified'] is False


@pytest.mark.parametrize('remote', [None, [], {}, {'object': {'sha': '../bad', 'type': 'commit'}}])
def test_bad_remote_keeps_local_evidence(prepared, monkeypatch, remote):
    monkeypatch.setattr(source, 'remote_json', lambda path: remote)
    # Non-object transport is rejected by remote_json; mock that same boundary here.
    if not isinstance(remote, dict):
        def fail(path):
            raise ValueError('Invalid response')
        monkeypatch.setattr(source, 'remote_json', fail)
    result = source.inspect(prepared, True)
    assert result['status'] == 'remote_comparison_unavailable'
    assert result['recorded_revision'] == 'a' * 40


@pytest.mark.parametrize('data', ['[]', '{broken', '{"repository":"attacker/repo"}', 'x' * 16001])
def test_invalid_receipt_never_selects_remote_source(prepared, data):
    (prepared / 'INSTALACION_LOCAL.json').write_text(data)
    assert source.inspect(prepared, True)['status'] == 'receipt_unreadable'


def test_missing_receipt_does_not_guess_git_origin(tmp_path):
    assert source.inspect(tmp_path)['status'] == 'origin_not_recorded'
