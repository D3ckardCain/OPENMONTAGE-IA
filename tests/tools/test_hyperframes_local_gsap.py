"""Focused delta for binding local JS selection; no runtime render or old suites."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from lib import hyperframes_resources as resources
from tools.video.hyperframes_compose import HyperFramesCompose


def package(tmp_path):
    folder = tmp_path / 'gsap'; (folder / 'dist').mkdir(parents=True)
    data = b'/* fixture license */ window.gsap = {};'
    (folder / 'dist/gsap.min.js').write_bytes(data)
    (folder / 'package.json').write_text(json.dumps({'name': 'gsap', 'version': '3.14.2',
                                                   'license': 'fixture-license'}))
    return folder, hashlib.sha256(data).hexdigest()


def inputs(workspace, folder):
    return {'operation': 'scaffold_workspace', 'workspace_path': str(workspace),
            'local_gsap_package_dir': str(folder),
            'edit_decisions': {'cuts': [{'type': 'text_card', 'text': 'Synthetic',
                                        'in_seconds': 0, 'out_seconds': 1}]}}


def test_valid_local_resource_staged_with_attribution_and_reused(tmp_path):
    folder, expected = package(tmp_path); workspace = tmp_path / 'workspace'
    with patch.object(resources, 'GSAP_SHA256', expected), patch('subprocess.Popen') as spawn:
        result = HyperFramesCompose().execute(inputs(workspace, folder))
        assert result.success, result.error
        receipt = result.data['gsap_resource']
        target = workspace / receipt['src']; before = target.stat()
        html = (workspace / 'index.html').read_text()
        assert 'cdn.jsdelivr.net' not in html and receipt['src'] in html
        assert (workspace / receipt['attribution']).read_bytes() == (folder / 'package.json').read_bytes()
        again = HyperFramesCompose().execute(inputs(workspace, folder))
        assert again.success
        assert target.stat().st_mtime_ns == before.st_mtime_ns
        assert len(list((workspace / 'assets').glob('*.js'))) == 1
        spawn.assert_not_called()


def test_bad_hash_preserves_source_and_creates_no_workspace(tmp_path):
    folder, _ = package(tmp_path); workspace = tmp_path / 'workspace'
    source = folder / 'dist/gsap.min.js'; before = source.read_bytes()
    result = HyperFramesCompose().execute(inputs(workspace, folder))
    assert not result.success and 'SHA256' in result.error
    assert source.read_bytes() == before and not workspace.exists()


def test_missing_explicit_resource_does_not_fall_back_to_cdn(tmp_path):
    workspace = tmp_path / 'workspace'
    with patch('subprocess.Popen') as spawn:
        result = HyperFramesCompose().execute(inputs(workspace, tmp_path / 'missing'))
    assert not result.success and 'no CDN fallback' in result.error
    assert not workspace.exists(); spawn.assert_not_called()


def test_incompatible_package_version_rejected_before_staging(tmp_path):
    folder, expected = package(tmp_path); metadata = folder / 'package.json'
    data = json.loads(metadata.read_text()); data['version'] = '0.0.0'; metadata.write_text(json.dumps(data))
    with patch.object(resources, 'GSAP_SHA256', expected):
        result = HyperFramesCompose().execute(inputs(tmp_path / 'workspace', folder))
    assert not result.success and 'reviewed3.14.2' in result.error
    assert not (tmp_path / 'workspace').exists()


def test_shared_child_profile_applies_without_tool_specific_input(tmp_path, monkeypatch):
    folder, expected = package(tmp_path)
    monkeypatch.setenv('HYPERFRAMES_GSAP_PACKAGE_DIR', str(folder))
    args = inputs(tmp_path / 'workspace', folder)
    del args['local_gsap_package_dir']
    with patch.object(resources, 'GSAP_SHA256', expected):
        result = HyperFramesCompose().execute(args)
    assert result.success, result.error
    assert result.data['gsap_resource']['mode'] == 'local_verified'
