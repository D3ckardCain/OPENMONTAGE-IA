"""Manual transitions/layers: real graph, rollback and shared revision contracts."""
import pytest

from lib import studio_editor as edit, studio_editor_render as render
from tests.backlot.test_studio_editor import project, command, add


def test_dip_black_keeps_duration_and_is_reversible(project):
    pid,key,_=project;first=add(pid,key);second=add(pid,key)
    before=edit.state(pid)
    value=command(pid,'transition',id=second,type='dip_black',duration_seconds=.25)
    edl=value['edit_decisions'];assert edit.duration(edl)==20
    _,filters,_,_=render.plan(pid,edl)
    assert any('fade=t=out:st=9.75:d=0.25' in f for f in filters)
    assert any('fade=t=in:st=0:d=0.25' in f for f in filters)
    assert any('afade=t=out:st=9.75:d=0.25' in f for f in filters)
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
    for params in [{'id':first},{'id':second,'type':'crossfade'},{'id':second,'duration_seconds':0}]:
        with pytest.raises(ValueError):command(pid,'transition',**{'id':second,'duration_seconds':.25,**params})
    command(pid,'transition',id=second,duration_seconds=1)
    checkpoint=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'trim',id=second,in_seconds=0,out_seconds=.5)
    assert edit.state(pid)==checkpoint
    command(pid,'split',id=second,at=5)
    assert 'transition' not in edit.state(pid)['edit_decisions']['cuts'][-1]


def test_layers_source_bounds_order_hash_and_undo(project):
    pid,key,_=project;add(pid,key);before=edit.state(pid)
    value=command(pid,'layer_add',source_id=key,in_seconds=1,out_seconds=3,start_seconds=2,x=.5,y=0,width=.5,height=.5,opacity=.75)
    first=value['edit_decisions']['layers'][0]['id'];digest=value['render_sha256']
    args,filters,_,_=render.plan(pid,value['edit_decisions'])
    assert args.count('-i')==2
    assert any('setpts=(PTS-STARTPTS)/1.0+2.0/TB' in f and 'aa=0.75' in f for f in filters)
    assert any('overlay=x=960:y=0:eof_action=pass:repeatlast=0' in f for f in filters)
    assert digest!=before['render_sha256']
    command(pid,'layer_add',source_id=key,in_seconds=0,out_seconds=1)
    command(pid,'layer_move',id=first,index=1)
    assert edit.state(pid)['edit_decisions']['layers'][1]['id']==first
    command(pid,'undo');command(pid,'undo')
    assert edit.state(pid)['render_sha256']==digest
    checkpoint=edit.state(pid)
    for params in [{'start_seconds':9},{'x':.9},{'opacity':True},{'source_id':'absent'}]:
        with pytest.raises(ValueError):command(pid,'layer_update',id=first,**params)
        assert edit.state(pid)==checkpoint
    command(pid,'layer_remove',id=first)
    assert edit.state(pid)['render_sha256']==before['render_sha256']


def test_layers_prevent_silent_truncation_and_nonvideo_sources(project):
    pid,key,_=project;clip=add(pid,key)
    command(pid,'layer_add',source_id=key,in_seconds=0,out_seconds=2,start_seconds=8)
    with pytest.raises(ValueError):command(pid,'trim',id=clip,in_seconds=0,out_seconds=5)
    command(pid,'undo')
    assert not edit.state(pid)['edit_decisions'].get('layers')


def test_layered_soft_subtitle_input_maps_after_layer_inputs(project,monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace
    pid,key,_=project;add(pid,key)
    command(pid,'layer_add',source_id=key,in_seconds=0,out_seconds=2)
    command(pid,'subtitles',srt='1\n00:00:00,000 --> 00:00:01,000\nManual caption\n')
    value=edit.state(pid);args,filters,width,height=render.plan(pid,value['edit_decisions'])
    calls=[]
    def execute(args,*a,**kw):
        calls.append(args);Path(args[-1]).write_bytes(b'mock, not audiovisual evidence')
        return SimpleNamespace(returncode=0,stderr=b'')
    monkeypatch.setattr(render,'execute',execute);monkeypatch.setattr(render,'require_media',lambda _: 'ffmpeg')
    job={'status':'running','attempt':'layer-input-map','revision':value['revision'],'width':width,'height':height}
    render._worker(pid,value['edit_decisions'],job,args,filters)
    assert job['status']=='completed' and '2:s:0' in calls[0] and calls[0].count('-i')==3
