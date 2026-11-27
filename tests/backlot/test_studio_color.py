from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit,studio_editor_render as render,production_studio as studio,studio_color as color
from tools.video.studio_project_edit import StudioProjectEdit
from tests.backlot.test_studio_editor import project,command,add


def test_color_shared_history_reopen_and_bypass_digest(project):
    pid,key,_=project;clip=add(pid,key);before=edit.state(pid)
    command(pid,'clip_color',id=clip,color={'exposure_ev':.5,'saturation':.8})
    active=edit.state(pid);assert active['render_sha256']!=before['render_sha256']
    edit.command(pid,{'operation':'clip_color','revision':active['revision'],'id':clip,'color':{**active['edit_decisions']['cuts'][0]['color'],'bypass':True}},'agent')
    bypass=edit.state(pid);assert bypass['render_sha256']==before['render_sha256']
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==active['edit_decisions']
    command(pid,'redo');command(pid,'save')
    assert studio.read_json(studio.project_path(pid)/edit.ARTIFACT)['edit_decisions']==bypass['edit_decisions']


@pytest.mark.parametrize('value',[{'exposure_ev':3},{'gamma':float('nan')},{'bypass':'true'},{'lut':'../../bad'}])
def test_color_bad_settings_atomic(project,value):
    pid,key,_=project;clip=add(pid,key);before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'clip_color',id=clip,color=value)
    assert edit.state(pid)==before


def test_color_lock_split_and_graph_shared(project):
    pid,key,_=project;clip=add(pid,key)
    command(pid,'clip_color',id=clip,color={'exposure_ev':1,'contrast':1.2})
    command(pid,'split',id=clip,at=5);e=edit.state(pid)['edit_decisions']
    assert e['cuts'][0]['color']==e['cuts'][1]['color']
    for preview in [True,False]:
        graph=';'.join(render.plan(pid,e,preview)[1]);assert 'exposure=exposure=1' in graph and 'contrast=1.2' in graph
    command(pid,'clip',id=clip,locked=True)
    with pytest.raises(edit.Conflict):command(pid,'clip_color',id=clip,color=None)


def test_hsl_hue_is_bounded_persisted_reversible_and_shared_by_preview_export(project):
    pid,key,_=project;clip=add(pid,key);before=edit.state(pid)
    command(pid,'clip_color',id=clip,color={'hue_degrees':45})
    active=edit.state(pid);assert active['edit_decisions']['cuts'][0]['color']['hue_degrees']==45
    assert active['render_sha256']!=before['render_sha256']
    for preview in [True,False]:
        graph=';'.join(render.plan(pid,active['edit_decisions'],preview)[1])
        assert 'hue=H=45' in graph
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
    command(pid,'redo');command(pid,'save')
    assert edit.state(pid)['edit_decisions']['cuts'][0]['color']['hue_degrees']==45
    current=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'clip_color',id=clip,color={'hue_degrees':181})
    assert edit.state(pid)==current


def test_color_http_and_agent_read_contract(project,monkeypatch):
    pid,key,_=project;clip=add(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    monkeypatch.setattr(color,'compare',lambda p,c,t:{'project_id':p,'clip_id':c,'time':t})
    response=client.get(f'/api/studio/editor/{pid}/color-compare',params={'clip_id':clip,'clip_seconds':1.25})
    assert response.json()['time']==1.25
    from tools.video import studio_project_edit as bridge
    monkeypatch.setattr(bridge,'request',lambda p,data=None:client.get('/api/studio/editor/'+p).json())
    result=StudioProjectEdit().execute({'project_id':pid,'action':'color_compare','clip_id':clip,'clip_seconds':1.25})
    assert result.success and result.data['clip_id']==clip
