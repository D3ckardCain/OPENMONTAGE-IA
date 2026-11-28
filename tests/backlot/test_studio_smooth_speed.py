from copy import deepcopy
import math
import json
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit,studio_smooth_clock as clock,studio_smooth_speed as smooth,studio_editor_render as render,production_studio as studio
from lib.studio_smooth_audio import resample_file
from lib.studio_render_process import Control,Cancelled
from tests.backlot.test_studio_editor import project,command,add

MODE='continuous_resample_pitch_changes'
def points(end=10):return [{'source_seconds':0,'speed':.75},{'source_seconds':end/2,'speed':1.5},{'source_seconds':end,'speed':.75}]


def test_analytic_clock_inverse_accel_decel_and_vector_path(project):
    pid,key,_=project;clip=add(pid,key);r,_=smooth.propose(edit.state(pid)['edit_decisions'],clip,points(),MODE);m=r['map']
    times=np.linspace(-1,12,301);mapped=np.array([clock.forward(m,float(t)) for t in times]);restored=clock.inverse_array(m,mapped)
    assert np.max(np.abs(restored-times))<1e-10 and np.all(np.diff(mapped)>0)
    slopes=np.diff(mapped)/np.diff(times);assert slopes[25]>slopes[120] and slopes[230]>slopes[160]
    assert max(abs(clock.inverse(m,float(y))-x) for x,y in zip(times,mapped))<1e-10


def test_smooth_shared_history_persistence_words_and_annotations(project):
    from lib.studio_word_clock import inspect
    pid,key,_=project;clip=add(pid,key);command(pid,'subtitles',srt='1\n00:00:04,000 --> 00:00:06,000\nNo retires esto.\n')
    e=edit.state(pid)['edit_decisions'];e['candidate_sets']=[{'id':'w','source_id':key,'source_sha256':e['sources'][key]['sha256'],'transcript_sha256':'a'*64,'coverage':{'processed_ranges':[[0,10]]},'words':[{'index':0,'word':'No','start':4,'end':6}]}]
    studio.save_json(studio.project_path(pid)/edit.ARTIFACT,{**edit.state(pid),'edit_decisions':e});before=edit.state(pid)
    r=smooth.project_plan(pid,{'id':clip,'points':points(),'audio_mode':MODE})
    value=edit.command(pid,{'operation':'clip_smooth_speed','id':clip,'revision':before['revision'],'reviewed':True,'input_edl_sha256':r['input_edl_sha256'],'points':points(),'audio_mode':MODE},'agent')
    out=value['edit_decisions'];assert len(out['cuts'])==1 and len(inspect(out,'w')['words'])==1
    assert out['cues'][0]['start_seconds']==clock.forward(r['map'],4)
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
    command(pid,'redo');command(pid,'save');assert studio.read_json(studio.project_path(pid)/edit.ARTIFACT)['edit_decisions']==out
    with pytest.raises(edit.Conflict):command(pid,'split',id=clip,at=5)


@pytest.mark.parametrize('change',[{'audio_mode':'preserve_pitch'},{'reviewed':False},{'input_edl_sha256':'stale'},{'points':[{'source_seconds':0,'speed':1},{'source_seconds':5,'speed':2}]}])
def test_smooth_invalid_is_atomic(project,change):
    pid,key,_=project;clip=add(pid,key);before=edit.state(pid)
    data={'operation':'clip_smooth_speed','id':clip,'revision':before['revision'],'reviewed':True,'input_edl_sha256':before['edit_sha256'],'points':points(),'audio_mode':MODE,**change}
    with pytest.raises((ValueError,edit.Conflict)):edit.command(pid,data)
    assert edit.state(pid)==before


def test_smooth_static_layer_audio_share_clock_and_graph(project):
    pid,key,_=project;clip=add(pid,key);command(pid,'layer_add',source_id=key,in_seconds=0,out_seconds=7,start_seconds=1,x=0,y=0,width=.25,height=.25)
    e=edit.state(pid)['edit_decisions'];e['audio_tracks']=[{**deepcopy(e['cuts'][0]),'id':'aux','start_seconds':1,'out_seconds':7}]
    r,out=smooth.propose(e,clip,points(),MODE)
    assert out['layers'][0]['time_warp']['map']==out['audio_tracks'][0]['time_warp']['map']==out['cuts'][0]['time_warp']['map']
    for preview in [False,True]:
        args,filters,*_=render.plan(pid,out,preview);graph=';'.join(filters)
        assert 'log(' in graph and 'audio-warp-0.f32' in args and 'audio-warp-1.f32' in args
        assert '[3:a:0]' in graph and '[4:a:0]' in graph


def test_smooth_layer_animation_not_silently_removed(project):
    pid,key,_=project;clip=add(pid,key);command(pid,'layer_add',source_id=key,in_seconds=0,out_seconds=7,start_seconds=1,x=0,y=0,width=.25,height=.25)
    e=edit.state(pid)['edit_decisions'];e['layers'][0]['motion']={'duration_seconds':2,'dx':.1,'dy':0}
    with pytest.raises(ValueError,match='animada'):smooth.propose(e,clip,points(),MODE)


def test_continuous_audio_impulses_follow_analytic_map_and_cancel(tmp_path):
    m={'contract':clock.CONTRACT,'points':points(4),'old_start_seconds':0,'old_duration_seconds':4,'fps':25,'output_frames':92};clock.validate(m)
    samples=np.zeros((192000,2),dtype='<f4')
    for t in [.25,1.9,3.5]:samples[round(t*48000):round(t*48000)+48]=.5
    source=tmp_path/'in.f32';samples.tofile(source);w={'map':m,'old_start_seconds':0,'old_speed':1};out=tmp_path/'out.f32';control=Control('test')
    n=resample_file(source,out,w,92/25,control);a=np.fromfile(out,dtype='<f4').reshape(-1,2)
    assert n==176640 and a.shape==(n,2)
    for t in [.25,1.9,3.5]:
        at=round(clock.forward(m,t)*48000);assert np.max(a[max(0,at-2):at+100])>.49
    control.event.set()
    with pytest.raises(Cancelled):resample_file(source,tmp_path/'cancel.f32',w,92/25,control)


def test_smooth_api_is_read_only(project):
    pid,key,_=project;clip=add(pid,key);before=edit.state(pid);c=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    r=c.post(f'/api/studio/editor/{pid}/smooth-speed-plan',json={'id':clip,'points':points(),'audio_mode':MODE})
    assert r.status_code==200 and r.json()['map']['contract']==clock.CONTRACT
    assert edit.state(pid)==before


def test_smooth_agent_same_readonly_plan(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;clip=add(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    monkeypatch.setattr(bridge,'request',lambda path,data=None:client.post('/api/studio/editor/'+path,json=data).json())
    result=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'smooth_speed_plan','ramp':{'id':clip,'points':points(),'audio_mode':MODE}})
    assert result.success and result.data['map']['contract']==clock.CONTRACT


def test_map_endpoint_and_fps_drift_are_rejected(project):
    pid,key,_=project;clip=add(pid,key);_,e=smooth.propose(edit.state(pid)['edit_decisions'],clip,points(),MODE)
    e['output']['fps']=60
    with pytest.raises(ValueError,match='FPS'):edit._validate_edit(e)


def test_color_compare_uses_continuous_source_clock(project,monkeypatch):
    import io
    from PIL import Image
    from types import SimpleNamespace
    from lib import studio_color
    pid,key,_=project;clip=add(pid,key);r=smooth.project_plan(pid,{'id':clip,'points':points(),'audio_mode':MODE})
    command(pid,'clip_smooth_speed',id=clip,points=points(),audio_mode=MODE,reviewed=True,input_edl_sha256=r['input_edl_sha256'])
    png=io.BytesIO();Image.new('RGB',(4,2)).save(png,format='PNG')
    monkeypatch.setattr('lib.media_executables.require_media',lambda _:'ffmpeg-fixture')
    monkeypatch.setattr(studio_color.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout=png.getvalue(),stderr=b''))
    result=studio_color.compare(pid,clip,1)
    assert abs(result['requested_source_seconds']-clock.inverse(r['map'],1))<1e-12
