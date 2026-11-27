"""Offline contract/API tests: text and mocked media, never generated AV fixtures."""
from copy import deepcopy
from html import unescape
import json
from pathlib import Path
from types import SimpleNamespace
import threading

import pytest
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import production_studio as studio, production_agent as agent
from lib import studio_editor as edit, studio_editor_render as render
from tools.video.studio_project_edit import StudioProjectEdit


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path / 'projects')
    monkeypatch.setattr(agent, 'ACTIVE', {})
    monkeypatch.setattr(edit, 'EXPORTING', set())
    monkeypatch.setattr(edit, 'probe', lambda path: {'duration': 10., 'kind': 'video', 'audio': True, 'width': 640, 'height': 360})
    pid = edit.create('Montaje offline')['project_id']
    path = studio.project_path(pid) / 'assets/source.mp4'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'not-media: mocked probe, no AV fixture')
    value = edit.register(pid, 'assets/source.mp4', 0)
    key = next(iter(value['edit_decisions']['sources']))
    return pid, key, path


def command(pid, operation, **params):
    return edit.command(pid, {'operation': operation, 'revision': edit.state(pid)['revision'], **params})


def add(pid, key):
    return command(pid, 'add', source_id=key)['edit_decisions']['cuts'][-1]['id']


def test_manual_cycle_persistence_provenance_and_undo(project):
    pid, key, path = project
    original = path.read_bytes()
    clip = add(pid, key)
    command(pid, 'trim', id=clip, in_seconds=1, out_seconds=9)
    command(pid, 'split', id=clip, at=4)
    value = edit.state(pid)
    second = value['edit_decisions']['cuts'][1]['id']
    command(pid, 'move', id=second, index=0)
    command(pid, 'save')
    reloaded = studio.read_json(studio.project_path(pid) / edit.ARTIFACT)
    assert reloaded == edit.state(pid)
    assert [c['in_seconds'] for c in reloaded['edit_decisions']['cuts']] == [4, 1]
    command(pid, 'undo')
    assert [c['in_seconds'] for c in edit.state(pid)['edit_decisions']['cuts']] == [1, 4]
    command(pid, 'redo')
    command(pid, 'remove', id=clip)
    assert len(edit.state(pid)['edit_decisions']['cuts']) == 1
    assert path.read_bytes() == original
    assert reloaded['edit_decisions']['sources'][key]['sha256'] == edit.digest(path)
    assert all(e['origin'] == 'user' for e in reloaded['events'])


def test_import_copies_source_into_project_originals_and_preserves_source(project, tmp_path):
    pid, _, _ = project
    original = tmp_path / 'captura.mp4'
    original.write_bytes(b'authorized source bytes')
    client = TestClient(create_app(), base_url='http://127.0.0.1:4750')

    response = client.post(
        f'/api/studio/editor/{pid}/upload?filename=captura.mp4&revision=0',
        content=original.read_bytes(),
        headers={'Content-Type': 'application/octet-stream'},
    )

    assert response.status_code == 200, response.text
    imported = next(iter(response.json()['edit_decisions']['sources'].values()))
    assert imported['path'].startswith('originales/')
    assert (studio.project_path(pid) / imported['path']).read_bytes() == original.read_bytes()
    assert original.exists() and original.read_bytes() == b'authorized source bytes'


@pytest.mark.parametrize('params', [
    {'operation':'trim', 'in_seconds':float('nan'), 'out_seconds':8},
    {'operation':'trim', 'in_seconds':9, 'out_seconds':8},
    {'operation':'trim', 'in_seconds':0, 'out_seconds':11},
    {'operation':'clip', 'speed':float('inf')},
    {'operation':'clip', 'gain':-1}, {'operation':'clip', 'muted':'false'},
    {'operation':'split', 'at':0}, {'operation':'split', 'at':10},
    {'operation':'move', 'index':True}, {'operation':'move', 'index':-1},
    {'operation':'trim', 'track':'unknown', 'in_seconds':0, 'out_seconds':8},
    {'operation':'unknown'},
])
def test_rejected_commands_are_atomic(project, params):
    pid, key, _ = project
    clip = add(pid, key)
    before = edit.state(pid)
    with pytest.raises(ValueError):
        edit.command(pid, {'revision': before['revision'], 'id':clip, **params})
    assert edit.state(pid) == before


def test_revision_conflicts_and_agent_shared_state(project, monkeypatch):
    pid, key, _ = project
    before = edit.state(pid)
    add(pid, key)
    with pytest.raises(edit.Conflict):
        edit.command(pid, {'revision':before['revision'], 'operation':'undo'})
    agent.ACTIVE[pid] = (object(), threading.Event())
    with pytest.raises(edit.Conflict):
        command(pid, 'save')
    client = TestClient(create_app(), base_url='http://127.0.0.1:4750')
    def transport(path, data=None):
        url = '/api/studio/editor/' + path
        response = client.get(url) if data is None else client.post(url, json=data)
        if response.is_error:
            return {'_error':response.json()['detail'], '_conflict':response.status_code==409}
        return response.json()
    monkeypatch.setattr('tools.video.studio_project_edit.request', transport)
    tool = StudioProjectEdit()
    read = tool.execute({'project_id':pid, 'action':'read'})
    assert read.success
    assert 'undo' not in read.data
    result = tool.execute({'project_id':pid, 'action':'command', 'command':{'operation':'save', 'revision':read.data['revision']}})
    assert result.success
    assert edit.state(pid)['events'][-1]['origin'] == 'agent'
    assert tool.execute({'project_id':pid, 'action':'command', 'command':{'operation':'undo', 'revision':0}}).data['conflict']


@pytest.mark.parametrize('relative', ['../secret.mp4','assets/../../secret.mp4','assets\\source.mp4','C:/secret.mp4','assets/missing.mp4'])
def test_path_scope(project, relative):
    pid, _, _ = project
    with pytest.raises(ValueError):
        edit.register(pid, relative, edit.state(pid)['revision'])


def test_changed_source_and_import_identity(project, monkeypatch):
    pid, key, path = project
    path.write_bytes(b'changed file')
    with pytest.raises(edit.Conflict):
        edit.source(pid, key)
    old = edit.state(pid)
    def changing_probe(p):
        p.write_bytes(b'changed during probe')
        return {'duration':10, 'kind':'video', 'audio':True}
    monkeypatch.setattr(edit, 'probe', changing_probe)
    with pytest.raises(edit.Conflict):
        edit.register(pid, 'assets/source.mp4', old['revision'])
    assert edit.state(pid) == old


def test_audio_timing_gain_speed_and_filter_graph(project):
    pid, key, path = project
    clip = add(pid, key)
    value = edit.state(pid)
    audio_key = 'audio-source'
    value['edit_decisions']['sources'][audio_key] = {**value['edit_decisions']['sources'][key], 'kind':'audio'}
    studio.save_json(studio.project_path(pid) / edit.ARTIFACT, value)
    command(pid, 'add', source_id=audio_key)
    audio = edit.state(pid)['edit_decisions']['audio_tracks'][0]['id']
    command(pid, 'clip', track='audio', id=audio, speed=.5, gain=.5, fade_in=.2, fade_out=.3, start_seconds=2)
    command(pid, 'split', track='audio', id=audio, at=4)
    assert edit.state(pid)['edit_decisions']['audio_tracks'][1]['start_seconds'] == 10
    command(pid, 'clip', id=clip, muted=True)
    command(pid, 'output', ratio='9:16', fps=30)
    args, filters, width, height = render.plan(pid, edit.state(pid)['edit_decisions'], preview=True)
    graph = ';'.join(filters)
    assert (width, height) == (540, 960)
    assert 'atempo=0.5000' in graph and 'adelay=2000:all=1' in graph
    assert 'volume=0' in graph and 'afade=t=in' in graph and 'afade=t=out' in graph
    assert 'amix=inputs=3:duration=first:normalize=0' in graph
    assert 'force_original_aspect_ratio=decrease' in graph and 'fps=30' in graph
    assert '-protocol_whitelist' in args and str(path) in args


SRT = '1\n00:00:01,000 --> 00:00:04,000\nHola mundo\n'


def test_subtitles_split_merge_offset_validation_and_ass(project):
    pid, key, _ = project
    add(pid, key)
    command(pid, 'subtitles', srt=SRT)
    command(pid, 'cue_split', index=0, at=2, text_index=4)
    assert [c['text'] for c in edit.state(pid)['edit_decisions']['cues']] == ['Hola', 'mundo']
    command(pid, 'cue_merge', index=0)
    command(pid, 'cue_offset', seconds=1)
    value = edit.state(pid)
    assert value['edit_decisions']['cues'][0]['start_seconds'] == 2
    assert edit.parse_srt(edit.srt(value['edit_decisions']), 10) == value['edit_decisions']['cues']
    with pytest.raises(ValueError):
        command(pid, 'cue_offset', seconds=-3)
    assert edit.state(pid) == value
    command(pid, 'subtitle_style', size=40, position='top', mode='burn')
    from lib.scene_burned_subtitles import _ass
    ass = _ass(edit.state(pid)['edit_decisions']['cues'], 1920, 1080, edit.state(pid)['edit_decisions']['subtitle_style'])
    assert 'Style: Main,Arial,40,' in ass and ',8,' in ass
    clip = value['edit_decisions']['cuts'][0]['id']
    with pytest.raises(ValueError):
        command(pid, 'trim', id=clip, in_seconds=0, out_seconds=3)


def test_api_shared_state_media_and_upload(project):
    pid, key, path = project
    client = TestClient(create_app(), base_url='http://127.0.0.1:4750')
    base = '/api/studio/editor/' + pid
    assert client.get('/api/studio/editor/projects').json()[0]['project_id'] == pid
    revision = client.get(base).json()['revision']
    response = client.post(base+'/command', json={'operation':'add','source_id':key,'revision':revision})
    assert response.status_code == 200
    assert client.post(base+'/command', json={'operation':'save','revision':revision}).status_code == 409
    assert client.post(base+'/command', json={'operation':'save','revision':revision+1}, headers={'Origin':'http://remote.example'}).status_code == 403
    assert client.get(base+'/source/'+key).content == path.read_bytes()
    ranged = client.get(base+'/source/'+key, headers={'Range':'bytes=0-7'})
    assert ranged.status_code == 206 and ranged.content == path.read_bytes()[:8]
    assert client.get(base+'/source/missing').status_code == 400
    upload = client.post(base+'/upload?filename=clip.mp4&revision='+str(revision+1), content=b'offline mocked upload')
    assert upload.status_code == 200
    imported = list(upload.json()['edit_decisions']['sources'].values())[-1]
    assert imported['original_name'] == 'clip.mp4'
    assert client.post(base+'/upload?filename=bad.exe&revision=0', content=b'no').status_code == 400
    assert client.get('/api/studio/bootstrap').json()['projects'] == []
    page = unescape(client.get('/studio').text)
    assert '<!-- MANUAL_EDITOR -->' not in page
    assert 'id="edit-player" controls' in page and 'Vídeo' in page and 'Subtítulos' in page
    assert 'id="legacy-studio"' in page and 'id="applications-load"' in page


def test_export_worker_uses_snapshot_and_checks_result(project, monkeypatch):
    pid, key, _ = project
    add(pid, key)
    command(pid, 'subtitles', srt=SRT)
    calls = []
    def run(args, work, control, **kwargs):
        calls.append((args, kwargs))
        Path(args[-1]).write_bytes(b'mocked encoder output, not AV')
        return SimpleNamespace(returncode=0, stderr=b'')
    monkeypatch.setattr(render, 'execute', run)
    monkeypatch.setattr(render, 'require_media', lambda name: name)
    # Execute worker inline to make races and persistence deterministic.
    class Inline:
        def __init__(self, target, args, **kwargs): self.target, self.args = target, args
        def start(self): self.target(*self.args)
    monkeypatch.setattr(render.threading, 'Thread', Inline)
    result = render.start(pid, edit.state(pid)['revision'], True)
    assert result['status'] == 'completed'
    assert render.status(pid)['current']
    args, kwargs = calls[0]
    assert '-n' in args and '-c:s' in args and 'mov_text' in args and '-filter_complex' in args
    assert kwargs['timeout'] == 600
    assert pid not in edit.EXPORTING
    command(pid, 'save')
    assert render.status(pid)['current']
    clip = edit.state(pid)['edit_decisions']['cuts'][0]['id']
    command(pid, 'clip', id=clip, muted=True)
    assert not render.status(pid)['current']
    command(pid, 'subtitle_style', size=32, position='bottom', mode='burn')
    render.start(pid, edit.state(pid)['revision'])
    assert render.status(pid)['subtitle_mode'] == 'burn'
    assert 'ass=captions.ass' in calls[-1][0][calls[-1][0].index('-filter_complex')+1]


def test_save_reopen_preserves_render_content_identity(project):
    pid,key,_ = project
    clip = add(pid,key)
    before = edit.state(pid)
    command(pid,'save')
    saved = edit.state(pid)
    assert saved['revision'] == before['revision'] + 1
    assert saved['edit_sha256'] == before['edit_sha256']
    assert studio.read_json(studio.project_path(pid)/edit.ARTIFACT) == saved
    command(pid,'trim',id=clip,in_seconds=1,out_seconds=8)
    assert edit.state(pid)['edit_sha256'] != saved['edit_sha256']
    command(pid,'undo')
    assert edit.state(pid)['edit_sha256'] == saved['edit_sha256']


def test_export_failures_busy_and_restart_are_explicit(project, monkeypatch):
    pid, key, _ = project
    with pytest.raises(ValueError): render.start(pid, edit.state(pid)['revision'])
    add(pid, key)
    edit.EXPORTING.add(pid)
    with pytest.raises(edit.Conflict): command(pid, 'save')
    edit.EXPORTING.clear()
    studio.save_json(studio.project_path(pid)/'artifacts/manual_render.json', {'status':'running','revision':1})
    assert render.status(pid)['status'] == 'interrupted'
    value = edit.state(pid)
    args, filters, width, height = render.plan(pid, value['edit_decisions'])
    monkeypatch.setattr(render, 'require_media', lambda name:name)
    monkeypatch.setattr(render, 'execute', lambda *a, **k: SimpleNamespace(returncode=1, stderr=b'bounded failure'))
    job = {'status':'running','attempt':'test-failure','revision':value['revision'],'width':width,'height':height}
    edit.EXPORTING.add(pid)
    render._worker(pid, value['edit_decisions'], job, args, filters)
    assert render.status(pid)['status'] == 'failed'
    assert 'bounded failure' in render.status(pid)['error']
    assert pid not in edit.EXPORTING


def test_concurrent_clients_cannot_overwrite_each_other(project):
    pid, key, _ = project
    revision = edit.state(pid)['revision']
    barrier = threading.Barrier(2)
    outcomes = []
    def write():
        barrier.wait()
        try:
            edit.command(pid, {'operation':'add', 'source_id':key, 'revision':revision})
            outcomes.append('saved')
        except edit.Conflict:
            outcomes.append('conflict')
    threads = [threading.Thread(target=write) for _ in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=5)
    assert sorted(outcomes) == ['conflict', 'saved']
    assert len(edit.state(pid)['edit_decisions']['cuts']) == 1


@pytest.mark.parametrize('ratio', list(edit.PRESETS))
def test_preview_dimensions_and_frame_timebase(project, ratio):
    pid, key, _ = project
    clip = add(pid, key)
    command(pid, 'trim', id=clip, in_seconds=.001, out_seconds=1.111)
    command(pid, 'output', ratio=ratio, fps=24)
    edl = edit.state(pid)['edit_decisions']
    _, filters, width, height = render.plan(pid, edl, preview=True)
    assert width % 2 == height % 2 == 0
    expected_width, expected_height = edit.PRESETS[ratio]
    assert width * expected_height == height * expected_width
    assert edit.duration(edl) == round(1.110 * 24) / 24
    assert f'trim=duration={edit.duration(edl)}' in ';'.join(filters)
    with pytest.raises(ValueError): command(pid, 'split', id=clip, at=.002)
    assert edit.frames({'in_seconds':0,'out_seconds':2.5/24,'speed':1},24) == 3


def test_agent_transport_is_loopback_only_and_reports_conflict(monkeypatch):
    import io
    from urllib.error import HTTPError
    from tools.video import studio_project_edit as tool
    seen = []
    def open_request(req, timeout):
        seen.append((req.full_url, timeout))
        raise HTTPError(req.full_url,409,'Conflict',{},io.BytesIO(b'{"detail":"stale revision"}'))
    monkeypatch.setattr(tool,'urlopen',open_request)
    monkeypatch.setenv('BACKLOT_PORT','4750')
    result = tool.StudioProjectEdit().execute({'project_id':'edit-fixture','action':'command','command':{'operation':'save','revision':0}})
    assert not result.success and result.data['conflict'] and result.error == 'stale revision'
    assert seen == [('http://127.0.0.1:4750/api/studio/editor/edit-fixture/agent-command',120)]
    monkeypatch.setenv('BACKLOT_PORT','65536')
    assert not tool.StudioProjectEdit().execute({'project_id':'edit-fixture','action':'read'}).success


def test_thread_start_failure_releases_resource(project,monkeypatch):
    pid,key,_ = project
    add(pid,key)
    class FailedThread:
        def __init__(self, **kwargs): pass
        def start(self): raise RuntimeError('thread unavailable')
    monkeypatch.setattr(render.threading,'Thread',FailedThread)
    with pytest.raises(ValueError,match='iniciar'):
        render.start(pid,edit.state(pid)['revision'])
    assert pid not in edit.EXPORTING
    assert render.status(pid)['status'] == 'failed'


def test_tool_availability_requires_current_editor_api(monkeypatch):
    from tools.video import studio_project_edit as tool
    from tools.base_tool import ToolStatus
    seen=[]
    def unavailable(path,timeout):
        seen.append((path,timeout));return {'_error':'not found','_conflict':False}
    monkeypatch.setattr(tool,'request',unavailable)
    assert tool.StudioProjectEdit().get_status() == ToolStatus.UNAVAILABLE
    assert seen == [('projects',2)]
    monkeypatch.setattr(tool,'request',lambda path,timeout:[])
    assert tool.StudioProjectEdit().get_status() == ToolStatus.AVAILABLE


def test_srt_import_preserves_bytes_and_is_separate_from_edits(project):
    pid,key,_ = project
    add(pid,key)
    original = b'\xef\xbb\xbf' + SRT.replace('\n','\r\n').encode('utf-8')
    client = TestClient(create_app(),base_url='http://127.0.0.1:4750')
    revision = edit.state(pid)['revision']
    route = f'/api/studio/editor/{pid}/subtitles/import?filename=original.srt&revision={revision}'
    response = client.post(route,content=original)
    assert response.status_code == 200
    provenance = response.json()['edit_decisions']['subtitle_sources'][0]
    target = studio.project_path(pid)/provenance['path']
    assert target.read_bytes() == original and provenance['exact_original_bytes']
    assert provenance['sha256'] == edit.digest(target)
    command(pid,'subtitles',srt=SRT.replace('Hola mundo','Texto editado'))
    assert target.read_bytes() == original
    assert edit.state(pid)['edit_decisions']['cues'][0]['text'] == 'Texto editado'
    assert client.post(route,content=original).status_code == 409
    before = edit.state(pid)
    assert client.post(route.replace(f'revision={revision}',f'revision={before["revision"]}'),content=b'bad').status_code == 400
    assert edit.state(pid) == before


@pytest.mark.parametrize('content',[b'abc',b'abcde'])
def test_hash_read_is_bounded_when_source_changes(content):
    import io
    class ChangingFile:
        def stat(self): return SimpleNamespace(st_size=4)
        def open(self,mode): return io.BytesIO(content)
    with pytest.raises(edit.Conflict): edit.digest(ChangingFile())

