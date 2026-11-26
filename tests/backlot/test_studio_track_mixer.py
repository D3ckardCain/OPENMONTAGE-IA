"""New logical-lane mixer contracts; no media render, model or previous suites."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit, studio_editor_render as render
from lib import studio_track_mixer as mixer
from tests.backlot.test_studio_editor import project, command, add


def test_history_reopen_and_neutral_render_identity(project):
    pid,key,_=project;add(pid,key);baseline=edit.state(pid)['render_sha256']
    value=command(pid,'track_mixer',mixer={'audio':{'gain':.3},'video':{'muted':True}})
    changed=value['render_sha256'];assert changed!=baseline
    command(pid,'undo');assert edit.state(pid)['render_sha256']==baseline
    command(pid,'redo');command(pid,'save')
    assert edit.state(pid)['edit_decisions']['track_mixer']['audio']['gain']==.3
    value=command(pid,'track_mixer',mixer={})
    assert value['render_sha256']==baseline and 'track_mixer' not in value['edit_decisions']


@pytest.mark.parametrize('bad',[{'video':{'gain':True}},{'video':{'gain':float('inf')}},
    {'video':{'gain':5}},{'audio':{'solo':1}},{'audio':{'muted':'yes'}},{'other':{}},
    {'audio':{'filter':'evil'}},None])
def test_invalid_mixer_atomic(project,bad):
    pid,key,_=project;add(pid,key);before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'track_mixer',mixer=bad)
    assert edit.state(pid)==before


def test_solo_mute_and_clip_flags_compose_without_edits(project):
    pid,key,_=project;clip=add(pid,key)
    command(pid,'flags',id=clip,locked=True,solo=True)
    before=deepcopy(edit.state(pid)['edit_decisions']['cuts'])
    value=command(pid,'track_mixer',mixer={'video':{'gain':.5},'audio':{'solo':True}})
    assert mixer.gain(value['edit_decisions'],'video')==0
    assert value['edit_decisions']['cuts']==before
    value=command(pid,'track_mixer',mixer={'video':{'solo':True,'muted':True},'audio':{'solo':True,'gain':.4}})
    assert mixer.gain(value['edit_decisions'],'video')==0
    assert mixer.gain(value['edit_decisions'],'audio')==.4
    with pytest.raises(edit.Conflict):edit.command(pid,{'operation':'track_mixer','revision':0,'mixer':{}})


def test_shared_graph_after_processing_fades_and_before_delay(project):
    pid,key,_=project;clip=add(pid,key)
    command(pid,'clip',id=clip,gain=.7,fade_in=.1)
    value=command(pid,'track_mixer',mixer={'video':{'gain':.5},'audio':{'muted':True}})
    edl=deepcopy(value['edit_decisions']);audio=deepcopy(edl['cuts'][0]);audio.update(id='audio-test',start_seconds=2);edl['audio_tracks']=[audio]
    graphs=[render.plan(pid,edl,preview)[1] for preview in (True,False)]
    for graph in graphs:
        video=next(f for f in graph if f.startswith('[0:a:0]'))
        extra=next(f for f in graph if f.startswith('[1:a:0]'))
        assert video.index('volume=0.7')<video.index('afade=')<video.index('volume=0.5')
        assert extra.index('volume=0')<extra.index('adelay=2000')
    assert [f for f in graphs[0] if ':a:0]' in f]==[f for f in graphs[1] if ':a:0]' in f]


def test_agent_same_command_and_capability(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;add(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def transport(path,data=None):
        result=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert result.status_code==200,result.text
        return result.json()
    monkeypatch.setattr(bridge,'request',transport)
    assert 'track_mixer' in transport('capabilities')['commands']
    result=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'command','command':{
        'operation':'track_mixer','revision':edit.state(pid)['revision'],'mixer':{'audio':{'gain':.2}}}})
    assert result.success and edit.state(pid)['events'][-1]['origin']=='agent'


def test_effective_identity_keeps_neutral_solo_metadata(project):
    pid,key,_=project;add(pid,key);baseline=edit.state(pid)['render_sha256']
    value=command(pid,'track_mixer',mixer={'video':{'solo':True},'audio':{'solo':True}})
    assert value['render_sha256']==baseline
    assert value['edit_decisions']['track_mixer']['audio']['solo']
