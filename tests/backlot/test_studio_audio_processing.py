"""Only the new EQ/compressor/bypass contract; no old editor suites."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit,studio_editor_render as render
from lib import studio_audio_processing as fx
from tests.backlot.test_studio_editor import project,command,add


def settings():
    result=deepcopy(fx.DEFAULT);result['eq'].update(bass_db=6,treble_db=-6)
    result['compressor'].update(enabled=True,threshold_db=-18,ratio=4,attack_ms=5,release_ms=100)
    return result


def test_processing_history_bypass_neutral_identity_and_reopen(project):
    pid,key,_=project;clip=add(pid,key);original=edit.state(pid)
    value=command(pid,'audio_processing',id=clip,processing=settings());active_digest=value['render_sha256']
    assert active_digest!=original['render_sha256']
    bypass=settings();bypass['bypass']=True
    value=command(pid,'audio_processing',id=clip,processing=bypass)
    assert value['render_sha256']==original['render_sha256'] and value['edit_sha256']!=original['edit_sha256']
    command(pid,'undo');assert edit.state(pid)['render_sha256']==active_digest
    command(pid,'redo');command(pid,'save')
    assert edit.state(pid)['edit_decisions']['cuts'][0]['audio_processing']==bypass
    command(pid,'audio_processing',id=clip,processing=None)
    assert 'audio_processing' not in edit.state(pid)['edit_decisions']['cuts'][0]
    assert edit.state(pid)['render_sha256']==original['render_sha256']


def test_invalid_processing_is_atomic_and_locks_apply(project):
    pid,key,_=project;clip=add(pid,key)
    for change in [lambda s:s.update(bypass='yes'),lambda s:s['eq'].update(bass_db=13),
                   lambda s:s['eq'].update(mid_db=True),lambda s:s['compressor'].update(attack_ms=0),
                   lambda s:s['compressor'].update(ratio=float('nan')),lambda s:s['compressor'].update(enabled=1),
                   lambda s:s.update(expression='volume=secret')]:
        value=settings();change(value);before=edit.state(pid)
        with pytest.raises(ValueError):command(pid,'audio_processing',id=clip,processing=value)
        assert edit.state(pid)==before
    command(pid,'flags',id=clip,locked=True);before=edit.state(pid)
    with pytest.raises(edit.Conflict):command(pid,'audio_processing',id=clip,processing=settings())
    assert edit.state(pid)==before


def test_active_graph_is_shared_before_gain_and_fades(project):
    pid,key,_=project;clip=add(pid,key)
    command(pid,'clip',id=clip,gain=.4,fade_in=.1)
    value=command(pid,'audio_processing',id=clip,processing=settings())
    graphs=[render.plan(pid,value['edit_decisions'],preview)[1] for preview in (False,True)]
    audio=[next(line for line in graph if line.startswith('[0:a:0]')) for graph in graphs]
    assert audio[0]==audio[1]
    assert audio[0].index('equalizer=')<audio[0].index('acompressor=')<audio[0].index('volume=0.4')<audio[0].index('afade=')
    assert 'makeup=1' in audio[0]


def test_disabled_parameters_do_not_invalidate_render_and_split_preserves_settings(project):
    pid,key,_=project;clip=add(pid,key);original=edit.state(pid)['render_sha256']
    neutral=deepcopy(fx.DEFAULT);neutral['compressor']['threshold_db']=-30
    value=command(pid,'audio_processing',id=clip,processing=neutral)
    assert value['render_sha256']==original and fx.filter_suffix(value['edit_decisions']['cuts'][0])==''
    value=command(pid,'audio_processing',id=clip,processing=settings())
    value=command(pid,'split',id=clip,at=5)
    assert all(c['audio_processing']==settings() for c in value['edit_decisions']['cuts'])


def test_agent_uses_same_processing_command_and_capability(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;clip=add(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def transport(path,data=None):
        r=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert r.status_code==200,r.text
        return r.json()
    monkeypatch.setattr(bridge,'request',transport)
    assert 'audio_processing' in client.get('/api/studio/editor/capabilities').json()['commands']
    result=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'command','command':{
        'operation':'audio_processing','revision':edit.state(pid)['revision'],'id':clip,'processing':settings()}})
    assert result.success and edit.state(pid)['events'][-1]['origin']=='agent'


def test_effective_contract_tracks_active_settings_only(project,monkeypatch):
    pid,key,_=project;clip=add(pid,key);original=edit.state(pid)['render_sha256']
    value=command(pid,'audio_processing',id=clip,processing=settings());digest=value['render_sha256']
    monkeypatch.setattr(fx,'RENDER_CONTRACT','future-processing')
    assert edit.render_digest(value['edit_decisions'])!=digest
    value['edit_decisions']['cuts'][0]['audio_processing']['bypass']=True
    assert edit.render_digest(value['edit_decisions'])==original
