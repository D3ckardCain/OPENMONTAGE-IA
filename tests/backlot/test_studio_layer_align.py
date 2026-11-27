from copy import deepcopy
import pytest
from lib import studio_editor as edit,studio_editor_render as render,studio_smooth_speed as smooth,production_studio as studio
from tests.backlot.test_studio_editor import project,command,add


def seed(pid,key):
    clip=add(pid,key);command(pid,'layer_add',source_id=key,in_seconds=0,out_seconds=7,start_seconds=1,x=.7,y=.1,width=.25,height=.25)
    return clip,edit.state(pid)['edit_decisions']['layers'][0]['id']


def test_alignment_shared_undo_reopen_and_render_positions(project):
    pid,key,_=project;_,layer=seed(pid,key);before=edit.state(pid)
    value=edit.command(pid,{'operation':'layer_align','id':layer,'revision':before['revision'],'horizontal':'center','vertical':'middle','margin':.05},'agent')
    c=value['edit_decisions']['layers'][0];assert c['x']==c['y']==.375
    _,filters,width,height=render.plan(pid,value['edit_decisions']);graph=';'.join(filters)
    assert f'overlay=x={round(width*.375)}:y={round(height*.375)}' in graph
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
    command(pid,'redo');command(pid,'save');assert studio.read_json(studio.project_path(pid)/edit.ARTIFACT)['edit_decisions']['layers'][0]['x']==.375


@pytest.mark.parametrize('params',[{'horizontal':'bad'},{'horizontal':'keep','vertical':'keep'},{'margin':.5},{'margin':float('nan')}])
def test_bad_alignment_atomic(project,params):
    pid,key,_=project;_,layer=seed(pid,key);before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'layer_align',id=layer,**{'horizontal':'left','vertical':'top',**params})
    assert edit.state(pid)==before


def test_alignment_retains_smooth_map_and_rejects_locked_animation(project):
    pid,key,_=project;clip,layer=seed(pid,key);e=edit.state(pid)['edit_decisions'];p=[{'source_seconds':0,'speed':1},{'source_seconds':5,'speed':1.5},{'source_seconds':10,'speed':1}]
    r=smooth.project_plan(pid,{'id':clip,'points':p,'audio_mode':'continuous_resample_pitch_changes'})
    command(pid,'clip_smooth_speed',id=clip,points=p,audio_mode='continuous_resample_pitch_changes',reviewed=True,input_edl_sha256=r['input_edl_sha256'])
    before=edit.state(pid);old=deepcopy(before['edit_decisions']['layers'][0]['time_warp'])
    command(pid,'layer_align',id=layer,horizontal='right',vertical='bottom',margin=.1)
    assert edit.state(pid)['edit_decisions']['layers'][0]['time_warp']==old
    value=edit.state(pid);value['edit_decisions']['layers'][0]['locked']=True;studio.save_json(studio.project_path(pid)/edit.ARTIFACT,value)
    with pytest.raises(edit.Conflict):command(pid,'layer_align',id=layer,horizontal='left')


def test_animation_survives_rejected_static_alignment(project):
    pid,key,_=project;_,layer=seed(pid,key);value=edit.state(pid)
    value['edit_decisions']['layers'][0]['motion']={'dx':.02,'dy':0,'duration_seconds':2,'phase_seconds':0}
    studio.save_json(studio.project_path(pid)/edit.ARTIFACT,value);before=edit.state(pid)
    with pytest.raises(ValueError,match='animación'):command(pid,'layer_align',id=layer,horizontal='center')
    assert edit.state(pid)==before


@pytest.mark.parametrize('width,height',[(640,360),(360,640),(320,320),(320,400)])
def test_alignment_graph_tracks_output_proportions(project,width,height):
    pid,key,_=project;_,layer=seed(pid,key);command(pid,'output_custom',width=width,height=height,fps=25)
    command(pid,'layer_align',id=layer,horizontal='right',vertical='bottom',margin=.05)
    e=edit.state(pid)['edit_decisions'];_,graph,w,h=render.plan(pid,e)
    assert (w,h)==(width,height) and f'overlay=x={round(width*.7)}:y={round(height*.7)}' in ';'.join(graph)
