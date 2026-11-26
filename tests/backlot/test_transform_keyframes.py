"""Only new scalar curves/Bézier/budget/command clock; legacy tests stay untouched."""
from copy import deepcopy
import pytest
from lib import studio_editor as edit,studio_editor_render as render
from lib.studio_transform_keyframes import validate,sample,progress,write_commands
from tests.backlot.test_studio_editor import project,command,add


def curves():
    return {'clock':'source_seconds','curves':{
        'scale':[{'seconds':1,'value':.5,'interpolation':'linear'},{'seconds':5,'value':1.5,'interpolation':'linear'}],
        'rotation':[{'seconds':1,'value':0,'interpolation':'smooth'},{'seconds':5,'value':450,'interpolation':'linear'}],
        'opacity':[{'seconds':1,'value':0,'interpolation':'bezier','control_points':[.25,.1,.25,1]},{'seconds':5,'value':1,'interpolation':'hold'}]}}


def layer_project(project):
    pid,key,_=project;add(pid,key)
    value=command(pid,'layer_add',source_id=key,in_seconds=1,out_seconds=5,start_seconds=2,width=.25,height=.25,x=.2,y=.2)
    return pid,value['edit_decisions']['layers'][0]['id']


def test_three_properties_history_and_reopen(project):
    pid,layer=layer_project(project);before=edit.state(pid)
    value=command(pid,'layer_transform_keyframes',id=layer,keyframes=curves());digest=value['render_sha256']
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
    command(pid,'redo');command(pid,'save');value=edit.state(pid)
    assert value['edit_decisions']['layers'][0]['transform_keyframes']==curves()
    assert value['render_sha256']==digest and digest!=before['render_sha256']
    item=value['edit_decisions']['layers'][0];middle=sample(item,4)
    assert middle['scale']==1 and middle['rotation']==225
    assert middle['opacity']==pytest.approx(.8024034,abs=1e-6)
    command(pid,'layer_transform_keyframes',id=layer,keyframes=None)
    assert 'transform_keyframes' not in edit.state(pid)['edit_decisions']['layers'][0]


@pytest.mark.parametrize('mutate',[
    lambda v:v['curves']['scale'][0].update(value=0),
    lambda v:v['curves']['scale'][0].update(value=4.01),
    lambda v:v['curves']['rotation'][0].update(value=float('inf')),
    lambda v:v['curves']['opacity'][0].update(value=True),
    lambda v:v['curves']['opacity'][0].update(value=1.01),
    lambda v:v['curves']['opacity'][0].update(control_points=[.2,.3,1.1,0]),
    lambda v:v['curves']['opacity'][0].pop('control_points'),
    lambda v:v['curves']['scale'][1].update(seconds=1),
    lambda v:v['curves'].update(unknown=[]),
])
def test_bad_scalar_curve_is_atomic(project,mutate):
    pid,layer=layer_project(project);before=edit.state(pid);value=curves();mutate(value)
    with pytest.raises(ValueError):command(pid,'layer_transform_keyframes',id=layer,keyframes=value)
    assert edit.state(pid)==before


def test_source_clock_survives_ripple_and_fractional_start(project,tmp_path):
    from lib.studio_timeline_ops import _ripple_sources
    pid,layer=layer_project(project);value=command(pid,'layer_transform_keyframes',id=layer,keyframes=curves());original=value['edit_decisions']['layers'][0]
    pieces=_ripple_sources([original],[(3,4)])
    assert sample(pieces[1],3)==sample(original,4)
    item={**original,'start_seconds':.1,'speed':2};work=tmp_path/'commands';work.mkdir()
    path=write_commands(work,item,320,180,24,0);lines=path.read_text().splitlines()
    assert lines[0].startswith('0.083333233 ') and 'colorchannelmixer@kfalpha0 aa' in lines[0]
    assert len(lines)<100 and 'rotate@kfrotate0 angle' in lines[-1]


def test_bezier_position_uses_same_frame_commands_and_budget(project):
    pid,layer=layer_project(project)
    value=command(pid,'layer_position_keyframes',id=layer,keyframes={'clock':'source_seconds','points':[
        {'seconds':1,'x':.1,'y':.1,'interpolation':'bezier','control_points':[.25,.1,.25,1]},
        {'seconds':5,'x':.5,'y':.5,'interpolation':'linear'}]})
    edl=value['edit_decisions'];assert sample(edl['layers'][0],4)['x']==pytest.approx(.42096136,abs=1e-6)
    _,filters,_,_=render.plan(pid,edl)
    assert any('sendcmd=f=keyframes-layer0.txt' in f for f in filters)
    before=edit.state(pid);huge=curves();huge['curves']['scale'][1]['value']=4
    command(pid,'layer_transform_keyframes',id=layer,keyframes=huge)
    checkpoint=edit.state(pid)
    with pytest.raises(ValueError,match='32MP'):command(pid,'layer_update',id=layer,width=1,height=1,x=0,y=0)
    assert edit.state(pid)==checkpoint


def test_bezier_handles_and_outer_values():
    assert progress({'interpolation':'bezier','control_points':[0,0,1,1]},.37)==pytest.approx(.37,abs=1e-6)
    assert progress({'interpolation':'hold'},.999)==0
    for controls in ([0,0,0,0],[1,1,1,1],[1,0,0,1]):
        assert all(0<=progress({'interpolation':'bezier','control_points':controls},p)<=1 for p in (.01,.5,.99))


def test_frame_grid_half_rounding_and_cancel_before_command_generation(tmp_path):
    from lib.studio_transform_keyframes import filters
    layer=dict(in_seconds=1,out_seconds=5,start_seconds=.0625,speed=1,width=.25,height=.25,x=0,y=0,opacity=1,transform_keyframes=curves())
    graph,_=filters(layer,320,180,8,0)
    assert 'aa='+str(sample(layer,.125)['opacity']) in graph
    class Cancel:
        def check(self):raise RuntimeError('Owned render cancelled')
    layer['start_seconds']=0
    with pytest.raises(RuntimeError,match='cancelled'):write_commands(tmp_path,layer,320,180,8,0,Cancel())
    assert (tmp_path/'keyframes-layer0.txt').stat().st_size==0
