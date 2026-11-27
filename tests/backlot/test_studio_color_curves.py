import pytest
from lib import studio_editor as edit,studio_color_curves as curves,studio_color as color,studio_editor_render as render,production_studio as studio
from tests.backlot.test_studio_editor import project,command,add


def setting(points=None):return {'interpolation':'pchip','channels':{'master':points or [[0,0],[.5,.7],[1,1]]}}


def test_curve_history_bypass_reset_split_and_reopen(project):
    pid,key,_=project;clip=add(pid,key);base=edit.state(pid)['render_sha256']
    command(pid,'clip_color_curves',id=clip,curves=setting());active=edit.state(pid)
    assert active['render_sha256']!=base
    command(pid,'clip_color',id=clip,color={'bypass':True});assert edit.state(pid)['render_sha256']==base
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==active['edit_decisions']
    command(pid,'redo');command(pid,'undo');command(pid,'split',id=clip,at=5)
    e=edit.state(pid)['edit_decisions'];assert e['cuts'][0]['color_curves']==e['cuts'][1]['color_curves']
    command(pid,'save');assert studio.read_json(studio.project_path(pid)/edit.ARTIFACT)['edit_decisions']==e
    command(pid,'clip_color_curves',id=clip,curves=setting([[0,0],[1,1]]));assert 'color_curves' not in edit.state(pid)['edit_decisions']['cuts'][0]


@pytest.mark.parametrize('value',[
 {'interpolation':'natural','channels':{'master':[[0,0],[1,1]]}},
 setting([[.1,0],[1,1]]),setting([[0,0],[.5,.5],[.5,.6],[1,1]]),
 setting([[0,0],[.5,float('nan')],[1,1]]),
 {'interpolation':'pchip','channels':{'master':[[0,0],[1,1]],'bad':[[0,0],[1,1]]}},
])
def test_curve_invalid_atomic(project,value):
    pid,key,_=project;clip=add(pid,key);before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'clip_color_curves',id=clip,curves=value)
    assert edit.state(pid)==before


def test_curve_filter_is_numeric_shared_and_bypass_covers_both(project):
    pid,key,_=project;clip=add(pid,key)
    edit.command(pid,{'operation':'clip_color_curves','revision':edit.state(pid)['revision'],'id':clip,'curves':setting()},'agent')
    e=edit.state(pid)['edit_decisions']
    for preview in [False,True]:assert "curves=interp=pchip:master='0/0 0.5/0.7 1/1'" in ';'.join(render.plan(pid,e,preview)[1])
    assert color.suffix({'bypass':True,'exposure_ev':1},setting())==''
    command(pid,'clip',id=clip,locked=True)
    with pytest.raises(edit.Conflict):command(pid,'clip_color_curves',id=clip,curves=None)
