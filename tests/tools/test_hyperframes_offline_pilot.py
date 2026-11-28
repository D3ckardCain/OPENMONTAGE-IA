"""New pilot boundaries only; previously approved adapter tests are not repeated."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.hyperframes_offline_profile import environment
from tools.video.hyperframes_offline_pilot import HyperFramesOfflinePilot


def test_profile_is_child_only_and_does_not_prepare_missing_files(tmp_path, monkeypatch):
    monkeypatch.setenv('HYPERFRAMES_NO_AUTO_INSTALL', 'original')
    node = tmp_path / 'node.exe'; node.touch()
    browser = tmp_path / 'chrome.exe'; browser.touch()
    package = tmp_path / 'package'; package.mkdir(); (package / 'package.json').write_text('{}')
    profile = dict(node=str(node), browser=str(browser), package_dir=str(package),
                   scratch=str(tmp_path / 'scratch'))
    env = environment(profile, tmp_path / 'network.jsonl')
    import os
    assert os.environ['HYPERFRAMES_NO_AUTO_INSTALL'] == 'original'
    assert env['HYPERFRAMES_NO_AUTO_INSTALL'] == '1'
    assert env['CI'] == '1' and env['HYPERFRAMES_SKIP_SKILLS'] == '1'
    assert not (tmp_path / 'scratch').exists()
    browser.unlink()
    with pytest.raises(ValueError, match='Missing prepared browser'):
        environment(profile, tmp_path / 'network.jsonl')
    assert not browser.exists()


def test_pilot_rejects_another_project_before_any_process():
    with patch('subprocess.Popen') as spawn:
        result = HyperFramesOfflinePilot().execute({'project_id': 'original', 'phase': 'render'})
    assert not result.success
    spawn.assert_not_called()


def test_pilot_never_clobbers_an_existing_workspace(tmp_path):
    workspace = tmp_path / 'hyperframes'; workspace.mkdir()
    original = workspace / 'index.html'; original.write_text('preserved')
    with pytest.raises(ValueError, match='do not overwrite'):
        HyperFramesOfflinePilot().build(tmp_path)
    assert original.read_text() == 'preserved'


def test_changed_authored_workspace_blocks_render_before_spawn(tmp_path):
    root = tmp_path / 'qa132-hyperframes-offline'; root.mkdir()
    (root / 'project.json').write_text(json.dumps({'pipeline_type': 'hyperframes-offline-pilot'}))
    (root / 'hyperframes').mkdir(); (root / 'hyperframes/index.html').write_text('changed')
    (root / 'artifacts').mkdir()
    (root / 'artifacts/pilot-build.json').write_text(json.dumps({'html_sha256': 'old'}))
    with patch('lib.checkpoint.PROJECTS_DIR', tmp_path), patch('subprocess.Popen') as spawn:
        result = HyperFramesOfflinePilot().execute({'project_id': root.name, 'phase': 'render'})
    assert not result.success and 'changed' in result.error
    spawn.assert_not_called()
