"""New volume envelopes only; do not rerun approved mixer/ducking/meter suites."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit,studio_editor_render as render,studio_volume_automation as curve
from tests.backlot.test_studio_editor import project,command,add

POINTS=[{'seconds':0,'gain':.2},{'seconds':2,'gain':1},{'seconds':4,'gain':.2}]


def test_points_history_bypass_save_reopen_and_neutral_identity(project):
    pid,key,_=project;add(pid,key);baseline=edit.state(pid)['render_sha256']
    value=command(pid,'track_volume_points',track='video',points=POINTS);active=value['render_sha256'];assert active!=baseline
    value=command(pid,'track_volume_points',track='video',points=POINTS,bypass=True)
    assert value['render_sha256']==baseline
    command(pid,'undo');assert edit.state(pid)['render_sha256']==active
    command(pid,'redo');command(pid,'save');assert edit.state(pid)['edit_decisions']['volume_automation']['video']['points']==POINTS
    value=command(pid,'track_volume_points',track='video',points=[])
    assert 'volume_automation' not in value['edit_decisions'] and value['render_sha256']==baseline
    value=command(pid,'track_volume_points',track='video',points=[{'seconds':2,'gain':1}]);assert value['render_sha256']==baseline


@pytest.mark.parametrize('change',[{'points':[{'seconds':1,'gain':True}]},{'points':[{'seconds':-1,'gain':1}]},
    {'points':[{'seconds':1,'gain':5}]},{'points':[{'seconds':0,'gain':1}]*2},{'points':POINTS[::-1]},
    {'points':[{'seconds':float('inf'),'gain':1}]},{'points':[{'seconds':1,'gain':1,'expression':'evil'}]},
    {'bypass':1},{'points':[{'seconds':i,'gain':1} for i in range(33)]},{'track':'unknown'}])
def test_invalid_points_never_mutate(project,change):
    pid,key,_=project;add(pid,key);before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'track_volume_points',**{'track':'audio','points':POINTS,**change})
    assert edit.state(pid)==before


def test_absolute_clock_after_clip_delay_and_video_concat_before_ducking(project):
    pid,key,_=project;add(pid,key);state=edit.state(pid);edl=deepcopy(state['edit_decisions'])
    clip=deepcopy(edl['cuts'][0]);clip.update(id='added',start_seconds=3);edl['audio_tracks']=[clip]
    edl['volume_automation']={lane:{'points':POINTS,'bypass':False} for lane in ('video','audio')}
    edl['audio_ducking']={'enabled':True};clip['ducking_music']=True
    graphs=[render.plan(pid,edl,preview)[1] for preview in (False,True)]
    assert graphs[0][1:]==graphs[1][1:]
    graph=';'.join(graphs[0]);assert 'adelay=3000:all=1,aeval=' in graph
    assert '[baseaudio]aeval=' in graph and '[baseaudio_automated]asplit=2' in graph
    assert graph.index('concat=')<graph.index('[baseaudio]aeval=')<graph.index('sidechaincompress=')
    assert 'val(0)' in graph and 'val(1)' in graph and 'volume=0.2' not in graph
    assert "c=stereo,aformat=sample_fmts=fltp:channel_layouts=stereo" in graph


def test_split_reorder_and_ripple_keep_absolute_points_and_preserve_muted_draft(project):
    pid,key,_=project;clip=add(pid,key)
    command(pid,'track_volume_points',track='video',points=POINTS)
    value=command(pid,'split',id=clip,at=5);second=value['edit_decisions']['cuts'][1]['id']
    value=command(pid,'move',id=second,index=0)
    assert value['edit_decisions']['volume_automation']['video']['points']==POINTS
    value=command(pid,'ripple_delete',track='video',ids=[second])
    assert value['edit_decisions']['volume_automation']['video']['points']==POINTS
    command(pid,'track_mixer',mixer={'video':{'muted':True}});baseline=edit.state(pid)['render_sha256']
    value=command(pid,'track_volume_points',track='video',points=[{'seconds':20,'gain':.5}])
    assert value['render_sha256']==baseline and curve.suffix(value['edit_decisions'],'video')==''


def test_agent_api_shares_points_and_no_arbitrary_expression(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;add(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def request(path,data=None):
        response=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert response.status_code==200,response.text
        return response.json()
    monkeypatch.setattr(bridge,'request',request)
    assert 'track_volume_points' in request('capabilities')['commands']
    result=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'command','command':{
        'operation':'track_volume_points','revision':edit.state(pid)['revision'],'track':'video','points':POINTS}})
    assert result.success and edit.state(pid)['events'][-1]['origin']=='agent'
    with pytest.raises(edit.Conflict):edit.command(pid,{'operation':'track_volume_points','revision':0,'track':'video','points':[]})


def test_missing_or_misspelled_points_cannot_clear_saved_curve(project):
    pid,key,_=project;add(pid,key);command(pid,'track_volume_points',track='video',points=POINTS)
    before=edit.state(pid)
    for payload in ({'track':'video'},{'track':'video','keyframes':[]},{'track':'video','points':[],'keyframes':[]}):
        with pytest.raises(ValueError):command(pid,'track_volume_points',**payload)
        assert edit.state(pid)==before
