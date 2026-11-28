from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit,studio_speed_ramp as ramp,production_studio as studio
from tests.backlot.test_studio_editor import project,command,add


def knots():return [{'source_seconds':0,'speed':.5},{'source_seconds':5,'speed':2}]


def seed(pid,key):
    clip=add(pid,key);command(pid,'subtitles',srt='1\n00:00:01,000 --> 00:00:06,000\nNo retires esto.\n')
    command(pid,'title_add',text='QA',start_seconds=1,end_seconds=6)
    command(pid,'marker_add',seconds=6,label='fin')
    e=edit.state(pid)['edit_decisions'];e['audio_tracks']=[{**deepcopy(e['cuts'][0]),'id':'audio','start_seconds':1,'in_seconds':0,'out_seconds':8}]
    studio.save_json(studio.project_path(pid)/edit.ARTIFACT,{**edit.state(pid),'edit_decisions':e})
    return clip


def test_reviewed_ramp_shared_sync_history_reopen(project):
    pid,key,_=project;clip=seed(pid,key);before=edit.state(pid);report=ramp.project_plan(pid,{'id':clip,'points':knots()})
    assert report['duration_before']==10 and report['duration_after']==12.5
    result=edit.command(pid,{'operation':'clip_speed_ramp','revision':before['revision'],'id':clip,'points':knots(),'reviewed':True,'input_edl_sha256':report['input_edl_sha256']},'agent')
    e=result['edit_decisions'];assert [c['speed'] for c in e['cuts']]==[.5,2]
    assert e['cues'][0]['start_seconds']==2 and e['cues'][0]['end_seconds']==10.5
    assert e['titles'][0]['end_seconds']==10.5 and e['markers'][0]['seconds']==10.5
    assert len(e['audio_tracks'])==2 and e['audio_tracks'][1]['start_seconds']==10
    assert sum((c['out_seconds']-c['in_seconds'])/c['speed'] for c in e['audio_tracks'])==10
    command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
    command(pid,'redo');command(pid,'save');assert studio.read_json(studio.project_path(pid)/edit.ARTIFACT)['edit_decisions']==e


@pytest.mark.parametrize('extra',[{'reviewed':False},{'input_edl_sha256':'stale'},{'points':[{'source_seconds':0,'speed':0},{'source_seconds':5,'speed':2}]}])
def test_bad_or_stale_ramp_atomic(project,extra):
    pid,key,_=project;clip=add(pid,key);before=edit.state(pid);data={'operation':'clip_speed_ramp','revision':before['revision'],'id':clip,'points':knots(),'reviewed':True,'input_edl_sha256':before['edit_sha256'],**extra}
    with pytest.raises((ValueError,edit.Conflict)):edit.command(pid,data)
    assert edit.state(pid)==before


def test_word_boundary_protection_and_no_new_asr(project):
    pid,key,_=project;clip=add(pid,key);e=edit.state(pid)['edit_decisions']
    e['candidate_sets']=[{'id':'words','source_id':key,'source_sha256':e['sources'][key]['sha256'],'transcript_sha256':'a'*64,'coverage':{'processed_ranges':[[0,10]]},'words':[{'index':0,'word':'No','start':4,'end':6}]}]
    with pytest.raises(ValueError,match='No'):ramp.propose(e,clip,knots())
    points=[{'source_seconds':0,'speed':.5},{'source_seconds':6,'speed':2}]
    report,after=ramp.propose(e,clip,points);assert report['protected_word_sets']==['words'] and after['candidate_sets']==e['candidate_sets']


def test_volume_absolute_default_and_explicit_follow_inserts_knots(project):
    pid,key,_=project;clip=add(pid,key);e=edit.state(pid)['edit_decisions'];e['volume_automation']={'video':{'points':[{'seconds':0,'gain':1},{'seconds':10,'gain':0}],'bypass':True}}
    _,absolute=ramp.propose(e,clip,knots());assert absolute['volume_automation']==e['volume_automation']
    _,follow=ramp.propose(e,clip,knots(),True);assert follow['volume_automation']['video']['points']==[{'seconds':0,'gain':1},{'seconds':10,'gain':.5},{'seconds':12.5,'gain':0}]


def test_speed_plan_is_read_only_http(project):
    pid,key,_=project;clip=add(pid,key);before=edit.state(pid);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    r=client.post(f'/api/studio/editor/{pid}/speed-plan',json={'id':clip,'points':knots()});assert r.status_code==200 and r.json()['duration_after']==12.5
    assert edit.state(pid)==before


def test_layer_split_source_clock_and_lock_rejection(project):
    pid,key,_=project;clip=add(pid,key);command(pid,'layer_add',source_id=key,in_seconds=0,out_seconds=8,start_seconds=1,x=0,y=0,width=.25,height=.25)
    e=edit.state(pid)['edit_decisions'];_,out=ramp.propose(e,clip,knots())
    assert len(out['layers'])==2 and out['layers'][0]['start_seconds']==2
    assert out['layers'][1]['start_seconds']==10 and out['layers'][1]['in_seconds']==4
    e['layers'][0]['locked']=True
    with pytest.raises(ValueError,match='bloqueado'):ramp.propose(e,clip,knots())


def test_speed_agent_plan_is_same_readonly_contract(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;clip=add(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    monkeypatch.setattr(bridge,'request',lambda path,data=None:client.post('/api/studio/editor/'+path,json=data).json())
    value=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'speed_plan','ramp':{'id':clip,'points':knots()}})
    assert value.success and value.data['contract']==ramp.CONTRACT


def test_decimal_rate_keeps_word_exactly_at_source_boundary(project):
    from lib.studio_word_clock import inspect
    pid,key,_=project;clip=add(pid,key);e=edit.state(pid)['edit_decisions'];e['output']['fps']=25
    e['cuts'][0]['out_seconds']=4
    e['candidate_sets']=[{'id':'words','source_id':key,'source_sha256':e['sources'][key]['sha256'],'transcript_sha256':'a'*64,'coverage':{'processed_ranges':[[0,4]]},'words':[{'index':0,'word':'quando','start':1.82,'end':1.94}]}]
    report,after=ramp.propose(e,clip,[{'source_seconds':0,'speed':.75},{'source_seconds':1.94,'speed':1.5}])
    words=inspect(after,'words');assert len(words['words'])==1 and not words['excluded_word_occurrences']
    assert words['words'][0]['timeline']['end_seconds']<=2.6
    assert report['segments'][0]['output_frames']==65
