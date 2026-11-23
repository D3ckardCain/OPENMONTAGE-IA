"""Installation lifecycle tests: no dependency downloads or model execution."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SPEC = importlib.util.spec_from_file_location(
    'studio_setup', Path(__file__).resolve().parents[2] / 'scripts/setup_local_studio.py')
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


@pytest.fixture
def source(tmp_path, monkeypatch):
    for name in ('requirements.txt', 'OPENMONTAGE_ESTUDIO.cmd', 'backlot/server.py'):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# fixture', encoding='utf-8')
    monkeypatch.setattr(setup.sys, 'version_info', (3, 11, 0))
    return tmp_path


def fake_venv(monkeypatch):
    def create(self, target):
        executable = setup.environment_python(target.parent)
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text('fixture')
        (target / 'pyvenv.cfg').write_text('include-system-site-packages = false\n')
    monkeypatch.setattr(setup.venv.EnvBuilder, 'create', create)


def test_check_is_read_only(source):
    before = sorted(source.rglob('*'))
    assert setup.inspect(source)['source_present']
    assert sorted(source.rglob('*')) == before


def test_existing_environment_is_preserved(source):
    sentinel = source / '.venv' / 'important.txt'
    sentinel.parent.mkdir()
    sentinel.write_text('keep')
    with pytest.raises(ValueError, match='sin recibo'):
        setup.setup(source)
    assert sentinel.read_text() == 'keep'
    assert not (source / '.backlot').exists()


def test_offline_install_uses_only_target_environment(source, monkeypatch):
    fake_venv(monkeypatch)
    calls = []
    monkeypatch.setattr(setup.subprocess, 'run', lambda cmd, **kw: calls.append((cmd, kw)))
    monkeypatch.setenv('PYTHONPATH', 'foreign')
    monkeypatch.setenv('PIP_TARGET', 'foreign')
    wheels = source / 'wheels'
    wheels.mkdir()
    report = setup.setup(source, wheels)
    assert report['status'] == 'ready'
    command, options = calls[0]
    assert command[0] == str(setup.environment_python(source))
    assert '--no-index' in command and '--index-url' not in command
    assert command[command.index('--find-links') + 1] == str(wheels)
    assert 'PYTHONPATH' not in options['env'] and 'PIP_TARGET' not in options['env']
    assert len(calls) == 3
    assert not (source / '.backlot/setup/installation.lock').exists()


def test_failed_install_can_retry_without_removing_files(source, monkeypatch):
    fake_venv(monkeypatch)
    def fail(cmd, **kw):
        raise subprocess.CalledProcessError(1, cmd)
    monkeypatch.setattr(setup.subprocess, 'run', fail)
    with pytest.raises(subprocess.CalledProcessError):
        setup.setup(source)
    receipt = source / '.backlot/setup/environment.json'
    assert json.loads(receipt.read_text())['status'] == 'failed'
    sentinel = source / '.venv' / 'sentinel'
    sentinel.write_text('preserved')
    monkeypatch.setattr(setup.subprocess, 'run', lambda *a, **kw: None)
    assert setup.setup(source)['status'] == 'ready'
    assert sentinel.read_text() == 'preserved'


def test_missing_source_and_wrong_python_do_not_mutate(source, monkeypatch):
    monkeypatch.setattr(setup.sys, 'version_info', (3, 10, 0))
    with pytest.raises(ValueError, match='Python 3.11'):
        setup.setup(source)
    assert not (source / '.backlot').exists()
    (source / 'requirements.txt').unlink()
    with pytest.raises(ValueError, match='extraccion'):
        setup.setup(source)


def test_active_installation_is_not_overwritten(source):
    lock = source / '.backlot/setup/installation.lock'
    lock.parent.mkdir(parents=True)
    lock.write_text('active')
    with pytest.raises(ValueError, match='activa'):
        setup.setup(source)
    assert lock.read_text() == 'active'


def test_receipt_is_historical_and_changed_requirements_are_detected(source, monkeypatch):
    fake_venv(monkeypatch)
    monkeypatch.setattr(setup.subprocess, 'run', lambda *a, **kw: None)
    setup.setup(source)
    assert setup.inspect(source)['dependency_state'] == 'ready_recorded_not_reverified'
    (source / 'requirements.txt').write_text('different==1.0')
    assert setup.inspect(source)['dependency_state'] == 'requirements_changed'
    setup.environment_python(source).unlink()
    assert setup.inspect(source)['dependency_state'] == 'environment_missing'


@pytest.mark.parametrize('data', ['[]', '{broken', 'x' * 64001])
def test_invalid_receipt_cannot_authorize_existing_environment(source, data):
    (source / '.venv').mkdir()
    receipt = source / '.backlot/setup/environment.json'
    receipt.parent.mkdir(parents=True)
    receipt.write_text(data)
    assert setup.inspect(source)['dependency_state'] == 'receipt_unreadable'
    with pytest.raises(ValueError):
        setup.setup(source)


def test_real_isolated_environment_without_network(tmp_path):
    """Verify venv layout on each OS without ensurepip or downloading anything."""
    target = tmp_path / '.venv'
    setup.venv.EnvBuilder(with_pip=False).create(target)
    result = subprocess.run([str(setup.environment_python(tmp_path)), '-I', '-c',
                             'import sys; print(sys.prefix != sys.base_prefix)'],
                            capture_output=True, text=True, check=True)
    assert result.stdout.strip() == 'True'
