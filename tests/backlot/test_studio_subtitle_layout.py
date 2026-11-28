from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio,studio_editor as edit,studio_subtitle_layout as layout
from lib.scene_burned_subtitles import _ass
from tests.backlot.test_studio_editor import project,command,add


def seed(pid,key):
    add(pid,key);command(pid,'subtitles',srt='1\n00:00:01,000 --> 00:00:02,000\nNo debemos eliminar ninguna negación del texto.\n')


def test_limits_reflow_history_and_safe_burn_identity(project):
    pid,key,_=project;seed(pid,key);baseline=edit.state(pid)
    policy={**deepcopy(layout.DEFAULT),'max_chars_per_line':12,'max_cps':10}
    value=command(pid,'subtitle_layout',layout=policy);assert value['render_sha256']==baseline['render_sha256']
    report=layout.project_report(pid);assert report['warning_cues']==1 and report['cues'][0]['cps']>10
    value=command(pid,'subtitle_reflow',reviewed=True,input_edl_sha256=report['input_edl_sha256'])
    cue=value['edit_decisions']['cues'][0];assert cue['text'].split()==baseline['edit_decisions']['cues'][0]['text'].split()
    assert cue['start_seconds']==1 and cue['end_seconds']==2
    command(pid,'undo');command(pid,'redo');command(pid,'save');assert edit.state(pid)['edit_decisions']['cues'][0]==cue
    command(pid,'subtitle_style',size=32,position='bottom',mode='burn');before=edit.state(pid)['render_sha256']
    policy['safe_area']['bottom']=.3;value=command(pid,'subtitle_layout',layout=policy);assert value['render_sha256']!=before


@pytest.mark.parametrize('change',[{'max_lines':True},{'max_cps':float('nan')},{'max_chars_per_line':9},{'safe_area':{'left':.1}},{'unknown':1}])
def test_invalid_policy_is_atomic(project,change):
    pid,key,_=project;seed(pid,key);before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'subtitle_layout',layout=change)
    assert edit.state(pid)==before


def test_reflow_requires_review_and_current_hash(project):
    pid,key,_=project;seed(pid,key);before=edit.state(pid)
    with pytest.raises(ValueError):command(pid,'subtitle_reflow',reviewed=False)
    with pytest.raises(edit.Conflict):command(pid,'subtitle_reflow',reviewed=True,input_edl_sha256='old')
    assert edit.state(pid)==before


def test_ass_uses_safe_rectangle_and_does_not_inject_text():
    cues=[{'text':'No {\\pos(0,0)} borrar','start_seconds':0,'end_seconds':1}]
    text=_ass(cues,640,360,{'size':48,'position':'bottom'}, {'left':.1,'right':.2,'top':.1,'bottom':.25})
    assert '\\pos(288.000,270.000)' in text and '\\{\\\\pos(0,0)\\}' in text
    assert ',64,128,' in text


def test_agent_quality_and_shared_edit_command(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;seed(pid,key);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def request(path,data=None):
        r=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert r.status_code==200,r.text
        return r.json()
    monkeypatch.setattr(bridge,'request',request)
    result=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'subtitle_quality'})
    assert result.success and len(result.data['cues'])==1


def test_timing_report_finds_overlap_and_out_of_range_and_manual_copy_repair(project):
    pid,key,_=project
    add(pid,key)
    source=edit.state(pid)['edit_decisions']
    corrupted=deepcopy(source)
    corrupted['cues']=[
        {'start_seconds':1.,'end_seconds':2.,'text':'No borrar negaciones.'},
        {'start_seconds':1.8,'end_seconds':10.5,'text':'Segundo cue.'},
    ]
    source_before=deepcopy(source)
    audit=layout.report(corrupted)
    assert audit['timing']['out_of_range_cues']==[1]
    assert len(audit['timing']['overlaps'])==1
    overlap=audit['timing']['overlaps'][0]
    assert (overlap['earlier_index'],overlap['later_index'])==(0,1)
    assert overlap['overlap_seconds']==pytest.approx(.2)
    assert 'Se solapa con subtítulo #1' in audit['cues'][1]['warnings']
    assert 'Fuera de duración del montaje' in audit['cues'][1]['warnings']
    assert source==source_before  # QA did not mutate the saved project.

    corrected=deepcopy(corrupted)
    corrected['cues'][1].update(start_seconds=2.,end_seconds=3.)
    repaired=layout.report(corrected)
    assert repaired['timing']['overlaps']==[]
    assert repaired['timing']['out_of_range_cues']==[]
    assert repaired['timing_warning_cues']==0
    assert source==source_before


def test_nonfinite_timing_is_reported_and_blocks_reflow(project):
    pid,key,_=project
    add(pid,key)
    corrupted=deepcopy(edit.state(pid)['edit_decisions'])
    corrupted['cues']=[{'start_seconds':1.,'end_seconds':float('nan'),'text':'Texto'}]
    report=layout.report(corrupted)
    assert report['input_edl_sha256'] is None
    assert report['timing']['invalid_interval_cues']==[0]
    assert report['cues'][0]['cps_available'] is False
    with pytest.raises(ValueError,match='intervalos inválidos'):
        layout.apply(corrupted,{'operation':'subtitle_reflow','reviewed':True,'input_edl_sha256':None})


def test_out_of_range_cue_repair_is_selective_shared_and_reversible(project):
    pid,key,source_path=project
    seed(pid,key)
    original_media=source_path.read_bytes()
    artifact=studio.project_path(pid)/edit.ARTIFACT
    corrupted=edit.state(pid)
    corrupted['edit_decisions']['cues'][0]['end_seconds']=12.
    # Inject a defect only into this disposable synthetic test project.
    corrupted['undo']=[];corrupted['redo']=[]
    studio.save_json(artifact,corrupted)

    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    url=f'/api/studio/editor/{pid}'
    audit=client.get(url+'/subtitles/quality')
    assert audit.status_code==200
    assert audit.json()['timing']['out_of_range_cues']==[0]
    before=edit.state(pid)
    before_edl=deepcopy(before['edit_decisions'])

    def agent_command(operation,**params):
        current=edit.state(pid)
        response=client.post(url+'/agent-command',json={
            'operation':operation,'revision':current['revision'],**params})
        assert response.status_code==200,response.text
        return response.json()

    agent_command('cue_update',index=0,start_seconds=1.,end_seconds=2.,
                  text=before_edl['cues'][0]['text'])
    fixed=edit.state(pid)
    fixed_edl=fixed['edit_decisions']
    assert fixed_edl['cues'][0]['end_seconds']==2.
    assert fixed_edl['cuts']==before_edl['cuts']
    assert fixed_edl['audio_tracks']==before_edl['audio_tracks']
    assert fixed_edl['sources']==before_edl['sources']
    assert fixed_edl['output']==before_edl['output']
    assert fixed['events'][-1]['origin']=='agent'
    assert layout.project_report(pid)['timing']['out_of_range_cues']==[]

    agent_command('undo')
    assert layout.project_report(pid)['timing']['out_of_range_cues']==[0]
    agent_command('redo')
    assert layout.project_report(pid)['timing']['out_of_range_cues']==[]
    agent_command('save')
    reopened=studio.read_json(artifact)
    assert reopened['edit_decisions']==edit.state(pid)['edit_decisions']
    assert reopened['edit_decisions']['cues'][0]['end_seconds']==2.
    assert source_path.read_bytes()==original_media
