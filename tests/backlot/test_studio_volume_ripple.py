"""Only opt-in ripple remapping of envelopes; no approved audio/render suites."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit,studio_volume_automation as volume
from tests.backlot.test_studio_editor import project,command,add

POINTS=[{'seconds':0,'gain':1},{'seconds':6,'gain':1},{'seconds':8,'gain':.2},{'seconds':10,'gain':.2}]


def setup(pid,key):
    first=add(pid,key);command(pid,'split',id=first,at=2)
    for lane in ('video','audio'):command(pid,'track_volume_points',track=lane,points=POINTS,bypass=lane=='audio')
    return first


def test_default_absolute_and_explicit_ripple_follow_material_history(project):
    pid,key,_=project;first=setup(pid,key);before=edit.state(pid)
    absolute=command(pid,'ripple_delete',ids=[first]);assert absolute['edit_decisions']['volume_automation']==before['edit_decisions']['volume_automation']
    command(pid,'undo');shifted=command(pid,'ripple_delete',ids=[first],move_volume_points=True)
    lanes=shifted['edit_decisions']['volume_automation'];assert lanes['audio']['bypass']
    assert lanes['audio']['points']==lanes['video']['points']
    assert {'seconds':4.,'gain':1.} in lanes['video']['points']
    assert {'seconds':6.,'gain':.2} in lanes['video']['points']
    for t in (2.1,5,7.5,10):assert volume.value_at(lanes['video']['points'],t-2)==pytest.approx(volume.value_at(POINTS,t))
    expected=deepcopy(lanes);command(pid,'undo');assert edit.state(pid)['edit_decisions']==before['edit_decisions']
    command(pid,'redo');command(pid,'save');assert edit.state(pid)['edit_decisions']['volume_automation']==expected


def test_half_open_boundaries_right_wins_and_one_sample_glue():
    points=[{'seconds':0,'gain':1},{'seconds':1,'gain':.8},{'seconds':1.5,'gain':.2},{'seconds':2,'gain':.6},{'seconds':3,'gain':.4}]
    edl={'volume_automation':{'video':{'points':points,'bypass':False}}};volume.ripple(edl,[(1,2)])
    result=edl['volume_automation']['video']['points'];volume.normalize({'points':result})
    assert next(p['gain'] for p in result if p['seconds']==1)==.6
    assert not any(p['gain']==.2 for p in result)
    assert volume.value_at(result,1-1/48000)==pytest.approx(volume.value_at(points,1-1/48000))
    assert volume.value_at(result,.5)==pytest.approx(volume.value_at(points,.5))
    assert volume.value_at(result,1.5)==pytest.approx(volume.value_at(points,2.5))


def test_adjacent_intervals_merge_and_multiple_removals_map_once():
    edl={'volume_automation':{'video':{'points':POINTS,'bypass':True}}}
    other=deepcopy(edl);volume.ripple(edl,[(0,1),(1,2),(3,4)]);volume.ripple(other,[(0,2),(3,4)])
    assert edl==other
    points=edl['volume_automation']['video']['points'];assert next(p['seconds'] for p in points if p['gain']==.2)==5
    assert edl['volume_automation']['video']['bypass']


@pytest.mark.parametrize('bad',[True,1,'yes'])
def test_invalid_option_or_audio_only_delete_is_atomic(project,bad):
    pid,key,_=project;first=setup(pid,key);before=edit.state(pid)
    params={'track':'audio' if bad is True else 'video','ids':[first],'move_volume_points':bad}
    with pytest.raises(ValueError):command(pid,'ripple_delete',**params)
    assert edit.state(pid)==before


def test_capacity_and_lock_conflict_roll_back_entire_ripple(project):
    pid,key,_=project;first=setup(pid,key)
    points=[{'seconds':i/4,'gain':1 if i%2 else .5} for i in range(32)]
    command(pid,'track_volume_points',track='video',points=points)
    # Middle interval adds boundary anchors, no existing point to replace there.
    value=command(pid,'split',id=first,at=.1);piece=value['edit_decisions']['cuts'][1]['id'];command(pid,'split',id=piece,at=.2)
    before=edit.state(pid)
    with pytest.raises(ValueError,match='32 puntos'):command(pid,'ripple_delete',ids=[piece],move_volume_points=True)
    assert edit.state(pid)==before
    last=before['edit_decisions']['cuts'][-1]['id'];command(pid,'flags',id=last,locked=True);before=edit.state(pid)
    with pytest.raises(edit.Conflict):command(pid,'ripple_delete',ids=[piece],move_volume_points=True)
    assert edit.state(pid)==before


def test_agent_same_opt_in_command(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;first=setup(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def request(path,data=None):
        r=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert r.status_code==200,r.text
        return r.json()
    monkeypatch.setattr(bridge,'request',request)
    assert 'ripple_volume_points' in request('capabilities')['commands']
    result=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'command','command':{
        'operation':'ripple_delete','revision':edit.state(pid)['revision'],'ids':[first],'move_volume_points':True}})
    assert result.success and edit.state(pid)['events'][-1]['origin']=='agent'
    assert {'seconds':6.,'gain':.2} in edit.state(pid)['edit_decisions']['volume_automation']['video']['points']


def test_silence_apply_forwards_explicit_option_without_retesting_asr(project,monkeypatch):
    from lib import studio_silence_proposal as silence,studio_timeline_ops as timeline
    pid,key,_=project;first=setup(pid,key);before=edit.state(pid);seen=[]
    report={'proposal_sha256':'test-proposal','ready_for_review':True,'blockers':[],
            'candidates':[{'id':'selected','clip_id':first,'frames':[0,48]}],
            'parameters':{'word_padding_seconds':0}}
    monkeypatch.setattr(silence,'draft',lambda *a:report)
    monkeypatch.setattr(silence,'_protect_audio_words',lambda *a:None)
    original=timeline.apply_timeline
    class Observed(RuntimeError):pass
    def capture(edl,data):
        if data.get('operation')=='ripple_delete':seen.append(data);raise Observed()
        return original(edl,data)
    monkeypatch.setattr(timeline,'apply_timeline',capture)
    with pytest.raises(Observed):command(pid,'silence_apply',proposal={},proposal_sha256='test-proposal',
        reviewed=True,selected_ids=['selected'],move_volume_points=True)
    assert seen[0]['move_volume_points'] is True and edit.state(pid)==before
