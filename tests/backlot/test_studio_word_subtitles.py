"""New word-to-cue contracts; synthetic metadata only, no ASR/media/server restart."""
from copy import deepcopy
import pytest
from lib import studio_editor as edit, studio_word_subtitles as subtitles, production_studio as studio


@pytest.fixture
def edl():
    value=edit._empty()
    value['sources']={'s':dict(kind='video',duration=6,sha256='a'*64,path='assets/test.mp4')}
    value['cuts']=[dict(id='c',source_id='s',in_seconds=0,out_seconds=6,speed=1)]
    value['candidate_sets']=[dict(id='set',source_id='s',source_sha256='a'*64,transcript_sha256='b'*64,
        coverage=dict(processed_ranges=[[0,6]]),provenance=dict(language='es',binding='synthetic_no_model'),
        words=[dict(index=i,word=text,start=i*.5,end=i*.5+.4,timing_status='estimated')
               for i,text in enumerate(['No','retires','la','protección.','¿Sí?','Ñandú','🙂'])])]
    return value


def params(value):
    d=subtitles.draft(value,'set')
    return dict(operation='subtitle_from_words',set_id='set',reviewed=True,
                input_edl_sha256=d['input_edl_sha256'],word_data_sha256=d['word_data_sha256'])


def test_draft_pure_keeps_negation_unicode_and_every_occurrence(edl):
    before=deepcopy(edl);d=subtitles.draft(edl,'set')
    assert d['ready'] and edl==before and len(d['cues'])==2
    assert d['cues'][0]['text']=='No retires la protección. ¿Sí? Ñandú'
    assert d['cues'][1]['text']=='🙂'
    assert [w['word_index'] for group in d['word_groups'] for w in group]==list(range(7))
    assert d['word_groups'][0][0]['timeline']['end_rational']==[2,5]
    assert d['source_file_rehashed'] is False and d['transcript_sha256']=='b'*64


def test_reordered_repeated_sped_clips_get_distinct_groups(edl):
    edl['cuts']=[dict(id='fast',source_id='s',in_seconds=0,out_seconds=6,speed=2),edl['cuts'][0]]
    d=subtitles.draft(edl,'set');assert d['ready']
    assert len({w['occurrence_id'] for g in d['word_groups'] for w in g})==14
    assert d['cues'][0]['end_seconds']==1.45
    assert d['cues'][2]['start_seconds']==3


@pytest.mark.parametrize('case',['partial','zero','coverage','other_source','overlap','submillisecond','invalid_text','empty'])
def test_incomplete_or_unrepresentable_draft_is_blocked_without_mutation(edl,case):
    words=edl['candidate_sets'][0]['words']
    if case=='partial':edl['cuts'][0]['in_seconds']=.1
    if case=='zero':words[0]['end']=0
    if case=='coverage':edl['candidate_sets'][0]['coverage']['processed_ranges']=[[0,4]]
    if case=='other_source':
        edl['sources']['x']={**edl['sources']['s'],'sha256':'f'*64};edl['cuts'].append(dict(id='x',source_id='x',in_seconds=0,out_seconds=1,speed=1))
    if case=='overlap':words[0]['end']=.7
    if case=='submillisecond':words[0]['end']=.0001
    if case=='invalid_text':words[0]['word']='No\nretires'
    if case=='empty':edl['cuts'][0].update(in_seconds=4,out_seconds=6)
    before=deepcopy(edl);d=subtitles.draft(edl,'set')
    assert not d['ready'] and d['blockers'] and not d['cues'] and not d['word_groups'] and edl==before
    with pytest.raises(ValueError,match='bloqueado'):subtitles.apply(edl,params(edl))
    assert edl==before


@pytest.mark.parametrize('changed',['edl','words'])
def test_stale_basis_rejected_even_if_revision_was_omitted(edl,changed):
    data=params(edl)
    if changed=='edl':edl['cuts'][0]['speed']=2
    else:edl['candidate_sets'][0]['words'][0]['word']='Nunca'
    before=deepcopy(edl)
    with pytest.raises(edit.Conflict,match='obsoleto'):subtitles.apply(edl,data)
    assert edl==before


def test_bounded_derivation_does_not_duplicate_unlimited_word_receipts(edl):
    edl['sources']['s']['duration']=3000;edl['cuts'][0]['out_seconds']=3000
    dataset=edl['candidate_sets'][0];dataset['coverage']['processed_ranges']=[[0,3000]]
    dataset['words']=[dict(index=i,word='palabra',start=i,end=i+.5) for i in range(2001)]
    result=subtitles.draft(edl,'set')
    assert not result['ready'] and not result['word_groups'] and any('2000' in b for b in result['blockers'])


def test_review_and_explicit_replace_required(edl):
    data=params(edl);data['reviewed']=False
    with pytest.raises(ValueError,match='Revisa'):subtitles.apply(edl,data)
    edl['cues']=[dict(start_seconds=0,end_seconds=1,text='Original')];data=params(edl)
    with pytest.raises(ValueError,match='reemplazar'):subtitles.apply(edl,data)
    assert edl['cues'][0]['text']=='Original'
    data['replace_existing']=True;subtitles.apply(edl,data)
    assert edl['subtitle_word_origin']['scope']=='snapshot_at_apply_not_live_alignment'


def test_api_agent_apply_undo_redo_reopen_share_single_revision(edl,monkeypatch,tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backlot.editor_routes import create_editor_router
    from tools.video import studio_project_edit as agent
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    initial=edit.create('Synthetic subtitle draft');pid=initial['project_id']
    path=tmp_path/pid/edit.ARTIFACT;initial['edit_decisions']=edl;studio.save_json(path,initial)
    before=path.read_bytes()
    async def body(request,*args):return await request.json()
    app=FastAPI();app.include_router(create_editor_router(body));client=TestClient(app)
    base='/api/studio/editor/'
    def request(route,data=None,**kw):
        r=client.get(base+route) if data is None else client.post(base+route,json=data)
        if r.status_code!=200:return {'_error':r.json()['detail'],'_conflict':r.status_code==409}
        return r.json()
    monkeypatch.setattr(agent,'request',request)
    result=agent.StudioProjectEdit().execute(dict(project_id=pid,action='subtitle_draft',set_id='set'))
    assert result.success and result.data['ready'] and path.read_bytes()==before
    assert 'subtitle_from_words' in client.get(base+'capabilities').json()['commands']
    data={**params(edl),'revision':0}
    applied=agent.StudioProjectEdit().execute(dict(project_id=pid,action='command',command=data))
    assert applied.success and applied.data['revision']==1
    state=client.get(base+pid).json();assert state['edit_decisions']['cues'][0]['text'].startswith('No ')
    assert state['events'][-1]['origin']=='agent'
    assert client.post(base+pid+'/command',json=data).status_code==409
    for revision,op in [(1,'undo'),(2,'redo'),(3,'save')]:
        assert client.post(base+pid+'/command',json=dict(revision=revision,operation=op)).status_code==200
        if op=='undo':assert client.get(base+pid).json()['edit_decisions']['cues']==[]
    reopened=client.get(base+pid).json()['edit_decisions']
    assert reopened['subtitle_word_origin']['applied_cues_sha256']==edit.edit_digest(reopened['cues'])
    assert reopened['candidate_sets']==edl['candidate_sets']
    assert not (tmp_path/pid/'assets/test.mp4').exists()
