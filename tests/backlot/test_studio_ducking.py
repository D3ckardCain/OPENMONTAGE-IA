"""Only new editor ducking contracts. Render/audio evidence recorded separately."""
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit, studio_editor_render as render, studio_ducking as duck
from tests.backlot.test_studio_editor import project, command, add


def music(pid,key):
    from lib import production_studio as studio
    value=edit.state(pid);audio_key='audio-fixture'
    value['edit_decisions']['sources'][audio_key]={**value['edit_decisions']['sources'][key],'kind':'audio'}
    studio.save_json(studio.project_path(pid)/edit.ARTIFACT,value)
    return command(pid,'add',source_id=audio_key)['edit_decisions']['audio_tracks'][-1]['id']


def test_history_bypass_clear_reopen_identity(project):
    pid,key,_=project;add(pid,key);mid=music(pid,key);baseline=edit.state(pid)['render_sha256']
    value=command(pid,'audio_ducking',music_ids=[mid],settings={});active=value['render_sha256'];assert active!=baseline
    value=command(pid,'audio_ducking',music_ids=[mid],settings={'bypass':True})
    assert value['render_sha256']==baseline and value['edit_decisions']['audio_tracks'][0]['ducking_music']
    command(pid,'undo');assert edit.state(pid)['render_sha256']==active
    command(pid,'redo');command(pid,'save');assert edit.state(pid)['edit_decisions']['audio_ducking']['bypass']
    value=command(pid,'audio_ducking',settings=None)
    assert 'audio_ducking' not in value['edit_decisions'] and 'ducking_music' not in value['edit_decisions']['audio_tracks'][0]
    assert value['render_sha256']==baseline


@pytest.mark.parametrize('settings,ids',[({'threshold_db':True},None),({'release_ms':float('nan')},None),
    ({'attack_ms':1},None),({'ratio':21},None),({'bypass':1},None),({'expression':'evil'},None),
    ({},[]),({},['missing']),({},[1]),('invalid',None)])
def test_invalid_atomic(project,settings,ids):
    pid,key,_=project;add(pid,key);mid=music(pid,key);before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'audio_ducking',music_ids=[mid] if ids is None else ids,settings=settings)
    assert edit.state(pid)==before


def test_locks_and_remove_music_no_dangling_references(project):
    pid,key,_=project;add(pid,key);mid=music(pid,key)
    command(pid,'flags',track='audio',id=mid,locked=True)
    with pytest.raises(edit.Conflict):command(pid,'audio_ducking',music_ids=[mid],settings={})
    command(pid,'flags',track='audio',id=mid,locked=False)
    command(pid,'audio_ducking',music_ids=[mid],settings={})
    value=command(pid,'remove',track='audio',id=mid)
    assert duck.effective(value['edit_decisions']) is None


def test_new_graph_branches_and_passthrough_identity(project):
    pid,key,_=project;add(pid,key);mid=music(pid,key);music(pid,key)
    value=command(pid,'audio_ducking',music_ids=[mid],settings={})
    graphs=[render.plan(pid,value['edit_decisions'],preview)[1] for preview in (False,True)]
    assert graphs[0][1:]==graphs[1][1:]  # Preview scales video, never audio.
    joined=';'.join(graphs[0]);assert 'asplit=2[duck_voice_out][duck_voice_key]' in joined
    assert 'makeup=1:mix=1:detection=rms' in joined and '[duck_voice_out][duck_music_out][a2]amix=' in joined
    for settings in ({'bypass':True},{'enabled':False},{'ratio':1}):
        command(pid,'audio_ducking',music_ids=[mid],settings=settings)
        assert 'sidechaincompress' not in ';'.join(render.plan(pid,edit.state(pid)['edit_decisions'])[1])


def test_split_music_inherits_role_and_agent_api(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;add(pid,key);mid=music(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def request(path,data=None):
        r=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert r.status_code==200,r.text
        return r.json()
    monkeypatch.setattr(bridge,'request',request)
    assert 'audio_ducking' in request('capabilities')['commands']
    result=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'command','command':{'operation':'audio_ducking','revision':edit.state(pid)['revision'],'music_ids':[mid],'settings':{}}})
    assert result.success and edit.state(pid)['events'][-1]['origin']=='agent'
    value=command(pid,'split',track='audio',id=mid,at=5)
    assert all(c['ducking_music'] for c in value['edit_decisions']['audio_tracks'])
