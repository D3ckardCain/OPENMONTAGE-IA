"""New reversible application regressions; numeric projects only, no render/ASR."""
from copy import deepcopy
from unittest.mock import patch

import pytest

from lib import production_studio as studio, studio_editor as editor
from lib import studio_silence_proposal as silence


@pytest.fixture
def copy_project(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, 'PROJECTS_DIR', tmp_path)
    value = editor.create('QA reversible silence copy'); pid = value['project_id']
    edl = value['edit_decisions']; edl['output']['fps'] = 25
    edl['sources'] = {'s': dict(kind='video', sha256='a'*64, duration=6, audio=True, path='assets/not-read.mp4')}
    clip = dict(id='video', source_id='s', source='assets/not-read.mp4', in_seconds=0,
                out_seconds=6, speed=1, start_seconds=0, gain=1, muted=False, fade_in=.2, fade_out=.2)
    edl['cuts'] = [clip]
    edl['audio_tracks'] = [{**clip, 'id': 'audio'}]
    edl['layers'] = [{**clip, 'id': 'layer', 'x': .6, 'y': 0, 'width': .4, 'height': .4, 'opacity': 1}]
    edl['titles'] = [dict(id='title', start_seconds=0, end_seconds=6, text='Título conservado')]
    edl['cues'] = [dict(start_seconds=.9, end_seconds=1.1, text='No'),
                   dict(start_seconds=3, end_seconds=3.4, text='borres.')]
    edl['markers'] = [dict(id=str(i), seconds=t, label='marca') for i,t in enumerate([.5,.7,2.4,5])]
    edl['candidate_sets'] = [dict(id='words', source_id='s', source_sha256='a'*64,
        transcript_sha256='b'*64, coverage=dict(processed_ranges=[[0,6]]),
        provenance=dict(language='es', binding='synthetic_not_measured'),
        words=[dict(index=0, word='No', start=.9, end=1.1), dict(index=1, word='borres.', start=3, end=3.4)])]
    path = tmp_path / pid / editor.ARTIFACT
    studio.save_json(path, value)
    return pid, path


def command(edl, revision=0):
    proposal = dict(set_id='words', input_edl_sha256=editor.edit_digest(edl),
        word_data_sha256=editor.edit_digest(edl['candidate_sets'][0]['words']),
        analysis=dict(source_id='s', source_sha256='a'*64, clock='source_seconds',
            method='synthetic_fixture', threshold_db=-35, min_silence_seconds=.3,
            processed_ranges=[[0,6]], intervals=[[.5,2.5]]))
    report = silence.draft(edl, proposal)
    return dict(operation='silence_apply', revision=revision, proposal=proposal,
                proposal_sha256=report['proposal_sha256'], reviewed=True,
                selected_ids=[c['id'] for c in report['candidates']])


def test_all_tracks_source_mapping_words_and_history_survive_reopen(copy_project):
    pid,path = copy_project; before = editor.state(pid); original = deepcopy(before['edit_decisions'])
    with patch('subprocess.Popen') as spawn, patch.object(editor, 'digest') as hash_file:
        result = editor.command(pid, command(original), 'agent')
    edl = result['edit_decisions']
    assert result['revision'] == 1 and result['events'][-1]['origin'] == 'agent'
    assert editor.duration(edl) == pytest.approx(4.6)
    assert [(c['in_seconds'],c['out_seconds']) for c in edl['cuts']] == [(0,.6),(.8,1.2),(2.4,6)]
    for key in ('audio_tracks','layers'):
        assert [c['start_seconds'] for c in edl[key]] == pytest.approx([0,.6,1])
        assert [c['in_seconds'] for c in edl[key]] == pytest.approx([0,.8,2.4])
        assert [c['out_seconds'] for c in edl[key]] == pytest.approx([.6,1.2,6])
    assert [t['start_seconds'] for t in edl['titles']] == pytest.approx([0,.6,1])
    assert [t['end_seconds'] for t in edl['titles']] == pytest.approx([.6,1,4.6])
    assert all(t['text']=='Título conservado' for t in edl['titles'])
    assert [c['text'] for c in edl['cues']] == ['No','borres.']
    assert [c['start_seconds'] for c in edl['cues']] == pytest.approx([.7,1.6])
    assert [m['seconds'] for m in edl['markers']] == pytest.approx([.5,1,3.6])
    assert edl['candidate_sets']==original['candidate_sets'] and edl['sources']==original['sources']
    assert edl['cuts'][1]['fade_in']==0 and edl['cuts'][0]['fade_out']==0
    assert edl['silence_origin']['removed_frames']==[[15,20],[30,60]]
    assert editor.state(pid)['edit_decisions']==edl
    assert editor.command(pid,dict(operation='undo',revision=1))['edit_decisions']==original
    assert editor.command(pid,dict(operation='redo',revision=2))['edit_decisions']==edl
    editor.command(pid,dict(operation='save',revision=3))
    assert studio.read_json(path)['edit_decisions']==edl and len(editor.state(pid)['undo'])==1
    spawn.assert_not_called(); hash_file.assert_not_called()


@pytest.mark.parametrize('key',['cuts','audio_tracks','layers','titles'])
def test_locks_reject_whole_transaction_without_partial_splits(copy_project,key):
    pid,path=copy_project; value=editor.state(pid);value['edit_decisions'][key][0]['locked']=True
    studio.save_json(path,value);before=path.read_bytes()
    with pytest.raises(editor.Conflict,match='bloquead'):
        editor.command(pid,command(value['edit_decisions']))
    assert path.read_bytes()==before


@pytest.mark.parametrize('case',['review','hash','unknown','duplicate','stale','analysis'])
def test_review_selection_and_exact_basis_required(copy_project,case):
    pid,path=copy_project;value=editor.state(pid);data=command(value['edit_decisions']);before=path.read_bytes()
    if case=='review':data['reviewed']=False
    if case=='hash':data['proposal_sha256']='0'*64
    if case=='unknown':data['selected_ids']=['unknown']
    if case=='duplicate':data['selected_ids']*=2
    if case=='stale':data['revision']=1
    if case=='analysis':data['proposal']['analysis']['intervals']=[[.5,2]]
    with pytest.raises(ValueError):editor.command(pid,data)
    assert path.read_bytes()==before


def test_layer_limit_rolls_back_all_tracks_instead_of_dropping_pieces(copy_project):
    pid,path=copy_project;value=editor.state(pid);edl=value['edit_decisions']
    edl['layers']=[{**edl['layers'][0],'id':str(i)} for i in range(4)]
    studio.save_json(path,value);before=path.read_bytes()
    with pytest.raises(ValueError,match='4 capas'):editor.command(pid,command(edl))
    assert path.read_bytes()==before


def test_subset_does_not_apply_unselected_candidate(copy_project):
    pid,_=copy_project;edl=editor.state(pid)['edit_decisions'];data=command(edl)
    data['selected_ids']=data['selected_ids'][:1]
    result=editor.command(pid,data)['edit_decisions']
    assert editor.duration(result)==pytest.approx(5.8)
    assert result['silence_origin']['removed_frames']==[[15,20]]


@pytest.mark.parametrize('fps',[24,30,60])
def test_frame_count_exact_with_speed_and_no_frame_loss(copy_project,fps):
    pid,path=copy_project;value=editor.state(pid);edl=value['edit_decisions']
    edl['output']['fps']=fps;edl['cuts'][0]['speed']=2
    edl.update(audio_tracks=[],layers=[],titles=[],cues=[],markers=[])
    studio.save_json(path,value);data=command(edl)
    report=silence.draft(edl,data['proposal']);removed=sum(c['frames'][1]-c['frames'][0] for c in report['candidates'])
    result=editor.command(pid,data)['edit_decisions']
    assert sum(editor.frames(c,fps) for c in result['cuts'])==3*fps-removed
    for c in result['cuts']:
        assert not(c['in_seconds']<1.1 and .9<c['out_seconds']) or c['in_seconds']<=.9 and c['out_seconds']>=1.1


def test_audio_words_on_independent_placement_cannot_be_removed(copy_project):
    pid,path=copy_project;value=editor.state(pid);edl=value['edit_decisions']
    edl['audio_tracks'][0]['start_seconds']=.3
    studio.save_json(path,value);before=path.read_bytes()
    with pytest.raises(editor.Conflict,match='palabra guardada de audio'):
        editor.command(pid,command(edl))
    assert path.read_bytes()==before


def test_audio_without_transcript_requires_explicit_track_review(copy_project):
    pid,path=copy_project;value=editor.state(pid);edl=value['edit_decisions']
    edl['sources']['a']={**edl['sources']['s'],'kind':'audio','sha256':'c'*64}
    edl['audio_tracks'][0]['source_id']='a'
    studio.save_json(path,value);before=path.read_bytes();data=command(edl)
    with pytest.raises(ValueError,match='revisa explícitamente la pista audio'):
        editor.command(pid,data)
    assert path.read_bytes()==before
    data['reviewed_audio_ids']=['audio']
    assert editor.command(pid,data)['revision']==1


def test_api_agent_apply_undo_redo_reopen_single_commit(copy_project,monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backlot.editor_routes import create_editor_router
    from tools.video import studio_project_edit as agent
    pid,path=copy_project;original=editor.state(pid)['edit_decisions']
    async def body(request,*args):return await request.json()
    app=FastAPI();app.include_router(create_editor_router(body));client=TestClient(app)
    base='/api/studio/editor/'
    def request(route,data=None,**kw):
        response=client.get(base+route) if data is None else client.post(base+route,json=data)
        return response.json() if response.status_code==200 else {'_error':response.json()['detail'],'_conflict':response.status_code==409}
    monkeypatch.setattr(agent,'request',request)
    result=agent.StudioProjectEdit().execute(dict(project_id=pid,action='command',command=command(original)))
    assert result.success and result.data['revision']==1
    applied=result.data['edit_decisions']
    assert client.post(base+pid+'/agent-command',json=command(original)).status_code==409
    for rev,operation in [(1,'undo'),(2,'redo'),(3,'save')]:
        assert client.post(base+pid+'/command',json=dict(revision=rev,operation=operation)).status_code==200
        if operation=='undo':assert client.get(base+pid).json()['edit_decisions']==original
    assert studio.read_json(path)['edit_decisions']==applied
    assert client.get(base+'capabilities').json()['silence_proposal']['apply_command']=='silence_apply'


def test_partial_audio_transcript_requires_review_of_uncovered_ranges(copy_project):
    pid,path=copy_project;value=editor.state(pid);edl=value['edit_decisions']
    edl['sources']['a']={**edl['sources']['s'],'kind':'audio','sha256':'c'*64}
    edl['audio_tracks'][0]['source_id']='a'
    edl['candidate_sets'].append(dict(id='audio-words',source_id='a',source_sha256='c'*64,
        coverage=dict(processed_ranges=[[0,.5]]),words=[dict(index=0,word='audio',start=.1,end=.2)]))
    studio.save_json(path,value);before=path.read_bytes();data=command(edl)
    with pytest.raises(ValueError,match='Cobertura ASR parcial de audio'):
        editor.command(pid,data)
    assert path.read_bytes()==before
    data['reviewed_audio_ids']=['audio']
    result=editor.command(pid,data)['edit_decisions']
    assert result['silence_origin']['reviewed_audio_ids']==['audio']


def test_malformed_nested_proposal_is_clear_error_without_writes(copy_project):
    pid,path=copy_project;data=command(editor.state(pid)['edit_decisions']);before=path.read_bytes()
    data['proposal']=[]
    with pytest.raises(ValueError,match='objeto de propuesta original'):
        editor.command(pid,data)
    assert path.read_bytes()==before
