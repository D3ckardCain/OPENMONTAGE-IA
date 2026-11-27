from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import studio_editor as edit,production_studio as studio,studio_subtitle_karaoke as karaoke
from tests.backlot.test_studio_editor import project,command,add


def seed(pid,key):
    add(pid,key);value=edit.state(pid)
    value['edit_decisions']['candidate_sets']=[{'id':'words','source_id':key,'source_sha256':value['edit_decisions']['sources'][key]['sha256'],
      'transcript_sha256':'a'*64,'coverage':{'processed_ranges':[[0,10]]},'provenance':{'binding':'synthetic_offline','language':'es'},
      'words':[{'index':i,'word':text,'start':a,'end':b,'timing_status':'estimated'} for i,(text,a,b) in enumerate([('No',0,.5),('retires',.5,1),('esto.',1.25,2)])]}]
    studio.save_json(studio.project_path(pid)/edit.ARTIFACT,value)
    command(pid,'subtitles',srt='1\n00:00:00,000 --> 00:00:02,000\nNo retires esto.\n')


def activate(pid,**extra):
    result=karaoke.project_report(pid,'words')
    return command(pid,'subtitle_karaoke',enabled=True,set_id='words',reviewed=True,
                   input_edl_sha256=result['input_edl_sha256'],word_data_sha256=result['word_data_sha256'],**extra)


def test_real_stored_spans_gap_events_and_safe_escaping(project):
    pid,key,_=project;seed(pid,key);result=karaoke.project_report(pid,'words')
    assert result['ready'] and [w['span'] for w in result['cues'][0]['words']]==[[0,2],[3,10],[11,16]]
    activate(pid);e=edit.state(pid)['edit_decisions'];text=karaoke.ass(e,640,360)
    assert '\\1c&H4DD2FF&}No' in text
    assert '0:00:01.00,0:00:01.25' in text  # Actual gap, no fabricated word.
    assert len([x for x in text.splitlines() if x.startswith('Dialogue:')])==4
    assert result['source_file_rehashed'] is False and result['asr_provenance']['binding']=='synthetic_offline'


def test_history_soft_burn_identity_and_stale_words(project):
    pid,key,_=project;seed(pid,key);original=edit.state(pid)['render_sha256'];activate(pid)
    assert edit.state(pid)['render_sha256']==original  # mov_text does not gain fake colors.
    command(pid,'subtitle_style',size=32,position='bottom',mode='burn');active=edit.state(pid)['render_sha256']
    command(pid,'subtitle_karaoke',enabled=False);assert edit.state(pid)['render_sha256']!=active
    command(pid,'undo');command(pid,'redo');command(pid,'undo');command(pid,'save')
    assert edit.state(pid)['edit_decisions']['subtitle_karaoke']['enabled']
    value=edit.state(pid);value['edit_decisions']['candidate_sets'][0]['words'][0]['end']=.4
    assert edit.render_digest(value['edit_decisions'])!=active
    with pytest.raises(ValueError):karaoke.validate_render(value['edit_decisions'])


@pytest.mark.parametrize('change',['missing_negation','changed_time','partial_word'])
def test_incompatible_cues_never_invent_alignment(project,change):
    pid,key,_=project;seed(pid,key);e=deepcopy(edit.state(pid)['edit_decisions'])
    if change=='missing_negation':e['cues'][0]['text']='retires esto.'
    if change=='changed_time':e['cues'][0]['end_seconds']=1.5
    if change=='partial_word':e['cues'][0]['start_seconds']=.25
    assert not karaoke.report(e,'words')['ready']


def test_review_and_hash_required_and_color_injection_rejected(project):
    pid,key,_=project;seed(pid,key);before=edit.state(pid)
    for data in ({'enabled':True,'set_id':'words'},{'enabled':True,'set_id':'words','reviewed':True,'input_edl_sha256':'old'},
                 {'enabled':False,'highlight_color':'#FF0000\\pos(0,0)'}):
        with pytest.raises((ValueError,edit.Conflict)):command(pid,'subtitle_karaoke',**data)
        assert edit.state(pid)==before


def test_reflow_whitespace_keeps_word_mapping(project):
    pid,key,_=project;seed(pid,key);e=deepcopy(edit.state(pid)['edit_decisions']);e['cues'][0]['text']='No\nretires esto.'
    result=karaoke.report(e,'words');assert result['ready'] and result['cues'][0]['words'][1]['span']==[3,10]


def test_agent_inspection_and_ass_endpoint(project,monkeypatch):
    from tools.video import studio_project_edit as bridge
    pid,key,_=project;seed(pid,key);activate(pid);client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    def request(path,data=None):
        r=client.get('/api/studio/editor/'+path) if data is None else client.post('/api/studio/editor/'+path,json=data)
        assert r.status_code==200,r.text
        return r.json()
    monkeypatch.setattr(bridge,'request',request)
    result=bridge.StudioProjectEdit().execute({'project_id':pid,'action':'subtitle_karaoke','set_id':'words'})
    assert result.success and result.data['ready']
    assert '\\1c&H4DD2FF&}' in client.get('/api/studio/editor/'+pid+'/subtitles.ass').text


def test_declared_partial_coverage_cannot_validate_unprocessed_words(project):
    pid,key,_=project;seed(pid,key);activate(pid);e=deepcopy(edit.state(pid)['edit_decisions']);e['subtitle_style']['mode']='burn'
    before=edit.render_digest(e);e['candidate_sets'][0]['coverage']['processed_ranges']=[[0,1]]
    with pytest.raises(ValueError,match='cobertura'):karaoke.report(e,'words')
    assert edit.render_digest(e)!=before
