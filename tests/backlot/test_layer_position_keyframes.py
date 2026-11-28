"""New position curves: revisioned operations, source clocks and real graph."""
import pytest
from lib import studio_editor as edit, studio_editor_render as render
from lib.studio_layer_keyframes import validate, overlay_position
from tests.backlot.test_studio_editor import project, command, add


def curve():
    return {'clock':'source_seconds','points':[
        {'seconds':1,'x':0,'y':0,'interpolation':'smooth'},
        {'seconds':3,'x':.5,'y':.25,'interpolation':'hold'},
        {'seconds':5,'x':.25,'y':.5,'interpolation':'linear'}]}


def test_revision_undo_redo_reopen_and_source_clock_after_ripple(project):
    pid,key,_=project;clip=add(pid,key)
    value=command(pid,'layer_add',source_id=key,in_seconds=1,out_seconds=5,start_seconds=2,width=.5,height=.5,x=0,y=0)
    layer=value['edit_decisions']['layers'][0]['id'];before=edit.state(pid)
    value=command(pid,'layer_position_keyframes',id=layer,keyframes=curve());digest=value['render_sha256']
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
    assert edit.state(pid)['render_sha256']==before['render_sha256']
    command(pid,'redo');assert edit.state(pid)['render_sha256']==digest
    command(pid,'save');assert edit.state(pid)['edit_decisions']['layers'][0]['position_keyframes']==curve()
    _,filters,_,_=render.plan(pid,edit.state(pid)['edit_decisions'])
    assert any('overlay=x=' in f and 'if(lt(' in f and 't-2.0' in f for f in filters)
    from lib.studio_timeline_ops import _ripple_sources
    original=edit.state(pid)['edit_decisions']['layers'][0]
    pieces=_ripple_sources([original],[(3,4)])
    assert len(pieces)==2 and pieces[1]['in_seconds']==3
    assert all(p['position_keyframes']==curve() for p in pieces)
    assert '3.0+(t-3)' in overlay_position(pieces[1],320,180)[0]


@pytest.mark.parametrize('change',[
    lambda c:c['points'][0].update(x=float('nan')),
    lambda c:c['points'][0].update(seconds=6),
    lambda c:c['points'][1].update(seconds=1),
    lambda c:c['points'][1].update(x=.51),
    lambda c:c['points'][0].update(interpolation='eval(t)'),
    lambda c:c.update(clock='timeline_seconds'),
])
def test_invalid_curve_rolls_back(project,change):
    pid,key,_=project;add(pid,key)
    value=command(pid,'layer_add',source_id=key,in_seconds=1,out_seconds=5,width=.5,height=.5,x=0,y=0)
    layer=value['edit_decisions']['layers'][0]['id'];before=edit.state(pid);value=curve();change(value)
    with pytest.raises(ValueError):command(pid,'layer_position_keyframes',id=layer,keyframes=value)
    assert edit.state(pid)==before


def test_resize_revalidates_curve_and_remove_restores_static(project):
    pid,key,_=project;add(pid,key)
    value=command(pid,'layer_add',source_id=key,in_seconds=1,out_seconds=5,width=.5,height=.5,x=0,y=0)
    layer=value['edit_decisions']['layers'][0]['id'];command(pid,'layer_position_keyframes',id=layer,keyframes=curve());before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'layer_update',id=layer,width=.75)
    assert edit.state(pid)==before
    with pytest.raises(ValueError):command(pid,'layer_update',id=layer,motion={'dx':0,'dy':0,'duration_seconds':1})
    with pytest.raises(ValueError):command(pid,'layer_position_keyframes',id=layer)
    assert edit.state(pid)==before
    command(pid,'layer_position_keyframes',id=layer,keyframes=None)
    assert 'position_keyframes' not in edit.state(pid)['edit_decisions']['layers'][0]


def test_agent_api_curve_is_same_user_document(project,monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    from tools.video.studio_project_edit import StudioProjectEdit
    pid,key,_=project;add(pid,key)
    value=command(pid,'layer_add',source_id=key,in_seconds=1,out_seconds=5,width=.5,height=.5,x=0,y=0)
    layer=value['edit_decisions']['layers'][0]['id'];before=edit.state(pid)
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def transport(path,data=None):
        url='/api/studio/editor/'+path
        response=client.get(url) if data is None else client.post(url,json=data)
        assert response.status_code==200,response.text
        return response.json()
    monkeypatch.setattr('tools.video.studio_project_edit.request',transport)
    result=StudioProjectEdit().execute({'project_id':pid,'action':'command','command':{
        'operation':'layer_position_keyframes','revision':before['revision'],'id':layer,'keyframes':curve()}})
    assert result.success,result.error
    assert result.data['edit_decisions']==edit.state(pid)['edit_decisions']
    assert edit.state(pid)['events'][-1]['origin']=='agent'
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
