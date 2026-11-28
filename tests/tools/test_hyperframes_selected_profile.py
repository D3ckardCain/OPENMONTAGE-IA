"""Selected native runtime: no real CLI, downloads, doctor or renders."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from lib import production_studio as studio, hyperframes_profile_store as store, hyperframes_runtime as runtime


@pytest.fixture
def profile(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'CONFIG_DIR', tmp_path / 'config')
    monkeypatch.setattr(store, '_CHILD', None)
    paths={name:str(tmp_path/name) for name in store.FIELDS}
    for key in ('node','browser'):
        Path(paths[key]).write_bytes(b'executable-fixture')
    for key in ('package_dir','gsap_package_dir','scratch'):
        Path(paths[key]).mkdir()
    for key,name,version in [('package_dir','hyperframes','0.9.96'),('gsap_package_dir','gsap','3.14.2')]:
        (Path(paths[key])/'package.json').write_text(json.dumps({'name':name,'version':version,'bin':{'hyperframes':'entry.js'}}))
    (Path(paths['package_dir'])/'entry.js').write_text('// fixture')
    gsap=Path(paths['gsap_package_dir'])/'dist';gsap.mkdir();(gsap/'gsap.min.js').write_text('// fixture')
    monkeypatch.setattr(runtime,'media_environment',lambda:dict(os.environ,PATH='media-fixture'))
    monkeypatch.setattr(runtime,'find_media',lambda _:paths['node'])
    calls=[]
    def run(command,**kwargs):
        calls.append((command,kwargs))
        return SimpleNamespace(returncode=0,stdout='v22.23.5\n' if len(command)==2 else '0.9.96\n',stderr='')
    monkeypatch.setattr(runtime.subprocess,'run',run)
    return paths,calls


def test_selection_persisted_without_parent_env_mutation(profile):
    value,calls=profile;old=dict(os.environ)
    saved=store.save(value,0)
    assert saved['revision']==1 and store.read()['profile']==value and dict(os.environ)==old
    assert not calls
    env=runtime.environment()
    assert env['HYPERFRAMES_PACKAGE_DIR']==value['package_dir']
    assert env['HYPERFRAMES_GSAP_PACKAGE_DIR']==value['gsap_package_dir']
    assert env['OPENMONTAGE_HF_NODE']==value['node'] and 'media-fixture' in env['PATH']


def test_guard_node_option_has_portable_path_with_no_backslash_escapes(profile):
    value,_=profile
    from lib.hyperframes_offline_profile import environment
    env=environment(value,Path(value['scratch'])/'network.jsonl')
    assert env['NODE_OPTIONS'].startswith('--require="')
    assert '\\' not in env['NODE_OPTIONS'] and env['NODE_OPTIONS'].endswith('hyperframes_network_guard.cjs"')


def test_same_selection_is_idempotent_and_other_stale_selection_rejected(profile):
    from lib.studio_editor import Conflict
    value,_=profile;store.save(value,0)
    assert store.save(value,0)['unchanged'] and store.read()['revision']==1
    with pytest.raises(Conflict):store.save({**value,'scratch':str(Path(value['scratch']).parent)},0)


def test_selected_execution_probe_is_not_doctor_or_render(profile):
    value,calls=profile;store.save(value,0)
    assert not runtime.check()['runtime_available']
    report=store.execute_probe()
    assert report['availability']['runtime_available'] and report['availability']['selected_profile_execution_verified']
    assert report['availability']['cli_probe_status']=='not_run' and not report['availability']['render_validated']
    cli=[c for c in calls if len(c[0])>2]
    assert len(cli)==1 and cli[0][0][-1]=='--version' and cli[0][1]['env']['HYPERFRAMES_GSAP_PACKAGE_DIR']==value['gsap_package_dir']


def test_modified_resource_invalidates_probe_without_hash(profile):
    value,_=profile;store.save(value,0);store.execute_probe()
    (Path(value['gsap_package_dir'])/'dist/gsap.min.js').write_text('// changed fixture')
    assert not runtime.check()['runtime_available']


@pytest.mark.parametrize('case',['version','missing','relative'])
def test_invalid_profile_never_replaces_selection(profile,case):
    value,_=profile
    if case=='version':(Path(value['package_dir'])/'package.json').write_text('{"name":"hyperframes","version":"other"}')
    if case=='missing':Path(value['browser']).unlink()
    if case=='relative':value['node']='relative.exe'
    with pytest.raises(ValueError):store.save(value,0)
    assert store.read()['profile'] is None


def test_bad_selected_profile_is_reported_without_fallback(profile):
    value,_=profile;store.save(value,0);Path(value['browser']).unlink()
    report=runtime.check()
    assert not report['local_requirements_met'] and not report['runtime_available']
    assert 'Perfil seleccionado' in report['reasons'][0]


def test_child_bridge_reuses_selection_and_owns_project_log(profile):
    value,_=profile;store.save(value,0);store.execute_probe()
    log=Path(value['scratch'])/'project-artifacts/network.jsonl'
    store.use_child_profile(value,log)
    env=runtime.environment()
    assert env['OPENMONTAGE_HF_NETWORK_LOG']==str(log.resolve())
    assert runtime.check()['runtime_available']
    assert store.read()['profile']==value


def test_child_override_does_not_inherit_other_profile_proof(profile,monkeypatch):
    value,_=profile;store.save(value,0);store.execute_probe()
    changed={**value,'scratch':str(Path(value['scratch']).parent)}
    monkeypatch.setenv('OPENMONTAGE_HF_PROFILE_REVISION','1')
    store.use_child_profile(changed,Path(value['scratch'])/'child.jsonl')
    assert 'OPENMONTAGE_HF_PROFILE_REVISION' not in runtime.environment()
    assert not runtime.check()['selected_profile_execution_verified']
