"""Version comparisons use fake executables and synthetic process output."""
import subprocess
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import application_updates as versions
from lib import production_studio as studio


@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    def configure(identifier,output,tag):
        executable=tmp_path/('yt-dlp' if identifier=='yt-dlp' else 'deno')
        executable.write_bytes(b'fixture, never execute')
        studio.save_json(studio.CONFIG_DIR/'settings.json',{'yt_dlp_path':str(executable)} if identifier=='yt-dlp' else {'deno_path':str(executable)})
        calls=[]
        def run(args,**kwargs):
            calls.append((args,kwargs))
            return SimpleNamespace(returncode=0,stdout=output.encode())
        monkeypatch.setattr(versions.subprocess,'run',run)
        monkeypatch.setattr(versions.updates,'check',lambda *args:{'tag':tag,'source_url':'https://github.com/official/releases'})
        return calls,executable
    return configure


@pytest.mark.parametrize('identifier,local,remote,state',[
    ('yt-dlp','2026.11.09','2026.11.10','update_available'),
    ('yt-dlp','2026.11.10','2026.11.10','versions_match'),
    ('yt-dlp','2026.11.11','2026.11.10','local_newer_than_release'),
    ('deno','deno 2.9.0 (stable, release)\nv8 1.0','v2.10.0','update_available'),
    ('deno','deno 2.10.0','v2.10.0','versions_match'),
    ('deno','deno 3.0.0','v2.10.0','local_newer_than_release'),
    ('deno','deno 2.10.0','v3.0.0-rc.1','comparison_inconclusive'),
])
def test_stable_versions_are_compared_numerically(setup,identifier,local,remote,state):
    calls,executable=setup(identifier,local,remote)
    result=versions.compare(identifier)
    assert result['status']==state and result['installation_started'] is False
    assert result['configuration_changed'] is False and len(calls)==1
    command,options=calls[0]
    assert command==[str(executable),*versions._COMMANDS[identifier]]
    assert options['shell'] is False and options['timeout']==5 and options['stdin']==subprocess.DEVNULL
    assert not any(arg in ('-U','--update','upgrade') for arg in command)


@pytest.mark.parametrize('identifier,output',[
    ('deno','deno 3.0.0-rc.1'),('deno','broken'),('yt-dlp','2026.99.20'),('yt-dlp','2026.11.20.1')])
def test_unrecognized_or_prerelease_local_version_is_not_claimed_current(setup,monkeypatch,identifier,output):
    setup(identifier,output,'v3.0.0')
    monkeypatch.setattr(versions.updates,'check',lambda *args:pytest.fail('Unrecognized versions should not query releases'))
    assert versions.compare(identifier)['status']=='local_version_unrecognized'


def test_local_only_api_and_agent_do_not_query_network(setup,monkeypatch):
    from lib.production_agent import LocalAgent
    calls,executable=setup('deno','deno 2.10.0','v2.11.0')
    monkeypatch.setattr(versions.updates,'check',lambda *args:pytest.fail('Offline version probe reached network'))
    args={'identifier':'deno','online':False}
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.post('/api/studio/updates/application-version',json=args)
    assert response.status_code==200,response.text
    assert response.json()['local_version']=='2.10.0' and response.json()['network_checked'] is False
    worker=LocalAgent.__new__(LocalAgent)
    assert worker.dispatch('update_application_version',args)['status']=='local_version_checked'
    assert client.post('/api/studio/updates/application-version',json={**args,'arguments':['upgrade']}).status_code==400
    assert client.post('/api/studio/updates/application-version',json=args,headers={'Origin':'https://other.example'}).status_code==403


def test_missing_or_unsupported_tool_does_not_execute(setup,monkeypatch):
    calls,executable=setup('deno','deno 2.10.0','v2.11.0');executable.unlink()
    assert versions.compare('deno')['status']=='local_unavailable' and not calls
    with pytest.raises(ValueError):versions.compare('blender')
    with pytest.raises(ValueError):versions.compare('deno','false')


def test_timeout_and_remote_failure_remain_inconclusive(setup,monkeypatch):
    setup('deno','deno 2.10.0','v2.11.0')
    def timeout(*args,**kwargs):raise subprocess.TimeoutExpired('fixture',5)
    original=versions.subprocess.run
    monkeypatch.setattr(versions.subprocess,'run',timeout)
    assert versions.compare('deno')['status']=='version_probe_failed'
    monkeypatch.setattr(versions.subprocess,'run',original)
    def offline(*args):raise ValueError('offline')
    monkeypatch.setattr(versions.updates,'check',offline)
    result=versions.compare('deno')
    assert result['status']=='remote_unavailable' and result['local_version']=='2.10.0'
    assert result['update_available'] is None


def test_failed_launch_does_not_claim_a_started_process(setup,monkeypatch):
    setup('deno','deno 2.10.0','v2.11.0')
    def denied(*args,**kwargs):raise OSError('permission denied')
    monkeypatch.setattr(versions.subprocess,'run',denied)
    result=versions.compare('deno')
    assert result['status']=='version_probe_failed' and result['process_started'] is False
    assert result['process_attempted'] is True


def test_version_history_is_offline_and_detects_changed_executable(setup,monkeypatch):
    calls,executable=setup('deno','deno 2.10.0','v2.11.0')
    result=versions.compare('deno')
    assert result['history_saved'] is True
    monkeypatch.setattr(versions.subprocess,'run',lambda *args,**kwargs:pytest.fail('History must not execute'))
    monkeypatch.setattr(versions.updates,'check',lambda *args:pytest.fail('History must not reach network'))
    report=versions.history('deno')
    assert report['rows'][0]['executable_state']=='metadata_match'
    assert report['rows'][0]['current_version_verified'] is False
    assert report['rows'][0]['local_version']=='2.10.0'
    executable.write_bytes(b'changed executable')
    assert versions.history('deno')['rows'][0]['executable_state']=='metadata_changed'
    assert len(calls)==1


def test_history_api_and_agent_detect_configuration_change(setup,monkeypatch):
    from lib.production_agent import LocalAgent
    setup('deno','deno 2.10.0','v2.11.0');versions.compare('deno',False)
    studio.save_json(studio.CONFIG_DIR/'settings.json',{'deno_path':'other'})
    monkeypatch.setattr(versions.subprocess,'run',lambda *args,**kwargs:pytest.fail('No process allowed'))
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    response=client.get('/api/studio/updates/application-version-history',params={'identifier':'deno'})
    assert response.status_code==200 and response.json()['rows'][0]['executable_state']=='configuration_changed'
    worker=LocalAgent.__new__(LocalAgent)
    assert worker.dispatch('update_application_version_history',{'identifier':'deno'})['process_started'] is False


def test_history_storage_is_bounded(setup):
    setup('deno','deno 2.10.0','v2.11.0')
    for _ in range(22):versions.compare('deno',False)
    assert len(versions.history('deno')['rows'])==20


def test_history_failure_preserves_fresh_version(setup,monkeypatch):
    setup('deno','deno 2.10.0','v2.11.0')
    def deny(*args):raise OSError('disk full')
    monkeypatch.setattr(studio,'save_json',deny)
    result=versions.compare('deno')
    assert result['status']=='update_available' and result['local_version']=='2.10.0'
    assert result['history_saved'] is False and result['history_warning']


def test_corrupt_history_is_not_used_or_overwritten(setup):
    setup('deno','deno 2.10.0','v2.11.0')
    path=versions._history_path('deno');path.parent.mkdir();path.write_text('broken')
    with pytest.raises(ValueError,match='historial'):versions.history('deno')
    result=versions.compare('deno')
    assert result['local_version']=='2.10.0' and result['history_saved'] is False
    assert path.read_text()=='broken'
