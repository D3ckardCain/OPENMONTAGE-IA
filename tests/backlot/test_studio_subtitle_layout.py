from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit,studio_subtitle_layout as layout
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
