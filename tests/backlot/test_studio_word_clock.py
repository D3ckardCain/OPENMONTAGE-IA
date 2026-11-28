"""New E04 clock fixtures only: no ASR, voices, decoding, media or live server."""
from copy import deepcopy
from fractions import Fraction
import json
import pytest
from lib import studio_word_clock as clock,studio_editor as edit,production_studio as studio


@pytest.fixture
def edl():
    result=edit._empty();result['output']['fps']=10
    result['sources']={'s1':dict(kind='video',duration=6,sha256='a'*64,path='assets/s1.mp4'),
                       'other':dict(kind='video',duration=2,sha256='b'*64,path='assets/other.mp4')}
    result['cuts']=[dict(id='other-clip',source_id='other',in_seconds=0,out_seconds=1,speed=1),
                    dict(id='a',source_id='s1',in_seconds=1,out_seconds=3,speed=1),
                    dict(id='gap',kind='gap',gap_duration=1,in_seconds=0,out_seconds=1,speed=1),
                    dict(id='b',source_id='s1',in_seconds=1,out_seconds=3,speed=2)]
    result['candidate_sets']=[dict(id='set',source_id='s1',source_sha256='a'*64,transcript_sha256='c'*64,
        provenance=dict(language='es',time_offset=.5,model_size='synthetic_no_model'),coverage=dict(processed_ranges=[[0,6]]),
        words=[dict(index=i,word=text,start=start,end=end,**extra) for i,(text,start,end,extra) in enumerate([
            ('Antes.',.5,.9,{}),('No',1,1.5,dict(speaker='speaker0',timing_status='estimated')),
            ('retires',1.5,2,{}),('protección.',2,2.5,{}),('cero',2.7,2.7,{})])])]
    return result


def test_clock_reorder_gap_speed_and_duplicate_occurrences_preserve_metadata(edl):
    before=deepcopy(edl);report=clock.inspect(edl,'set')
    assert edl==before and edl['cues']==[]
    assert report['duration_seconds']==5 and len(report['words'])==6
    first,second=report['words'][0],report['words'][3]
    assert first['text']==second['text']=='No' and first['word_index']==1
    assert first['occurrence_id']!=second['occurrence_id']
    assert (first['timeline']['start_seconds'],first['timeline']['end_seconds'])==(1,1.5)
    assert (second['timeline']['start_seconds'],second['timeline']['end_seconds'])==(4,4.25)
    assert first['source']['start_seconds']==1  # Offset was applied at import, never again.
    assert report['asr_provenance']['time_offset']==.5 and report['asr_provenance']['model_size']=='synthetic_no_model'
    assert first['speaker']=='speaker0' and first['language']=='es'
    assert first['timing_status']=='estimated' and report['words'][1]['timing_status']=='unknown'
    assert report['source_file_rehashed'] is False and report['source_sha256']=='a'*64
    assert report['transcript_sha256']=='c'*64 and report['input_edl_sha256']==edit.edit_digest(edl)


def test_fractional_speed_retains_exact_rational_word_clock(edl):
    edl['cuts']=[edl['cuts'][1]];edl['cuts'][0]['speed']=1.5
    word=clock.inspect(edl,'set')['words'][0]
    assert word['timeline']['end_rational']==[1,3]
    assert word['timeline']['end_seconds']==pytest.approx(float(Fraction(1,3)))


def test_partial_negation_is_reported_never_rewritten(edl):
    edl['cuts']=[edl['cuts'][1]];edl['cuts'][0]['in_seconds']=1.2
    report=clock.inspect(edl,'set');clip=report['clips'][0]
    assert 'No' not in [w['text'] for w in report['words']]
    no=next(w for w in clip['excluded_words'] if w['text']=='No')
    assert no['reason']=='partial_source_word' and no['source']['start_seconds']==1
    assert clip['boundary_review_required']
    assert report['words'][0]['timeline']['start_rational']==[3,10]


def test_zero_duration_never_gets_invented_alignment(edl):
    report=clock.inspect(edl,'set')
    assert all(w['text']!='cero' for w in report['words'])
    assert report['excluded_word_occurrences']==2
    assert all(c['excluded_words'][0]['reason']=='zero_duration' for c in report['clips'] if c['source_inspected'])


def test_frame_shortening_never_clamps_whole_word_silently(edl):
    edl['cuts']=[edl['cuts'][1]];edl['cuts'][0]['out_seconds']=1.24
    edl['candidate_sets'][0]['words']=[dict(index=0,word='No',start=1,end=1.23)]
    report=clock.inspect(edl,'set')
    assert report['words']==[] and report['clips'][0]['frames']==2
    assert report['clips'][0]['excluded_words'][0]['reason']=='partial_frame_quantization'


def test_half_frame_matches_existing_editor_rounding(edl):
    edl['cuts']=[edl['cuts'][1]];edl['cuts'][0]['out_seconds']=1.25
    edl['candidate_sets'][0]['words']=[dict(index=0,word='No',start=1,end=1.25)]
    report=clock.inspect(edl,'set')
    assert report['clips'][0]['frames']==3 and report['duration_seconds']==.3
    assert report['words'][0]['timeline']['end_rational']==[1,4]


def test_partial_coverage_is_explicit_not_silence(edl):
    dataset=edl['candidate_sets'][0];dataset['coverage']['processed_ranges']=[[0,2]]
    dataset['words']=dataset['words'][:3]
    report=clock.inspect(edl,'set')
    assert all(not c['coverage_complete_declared'] for c in report['clips'] if c['source_inspected'])
    assert any('silencio' in warning for warning in report['warnings'])


def test_overlap_remains_word_overlap_not_fake_cue_repair(edl):
    edl['candidate_sets'][0]['words'][1]['end']=1.7
    report=clock.inspect(edl,'set')
    assert report['words'][0]['timeline']['end_seconds']>report['words'][1]['timeline']['start_seconds']


@pytest.mark.parametrize('case',['missing_set','stale_source','missing_transcript_hash','bad_index','nan','infinity','boolean',
                                'reverse_word','word_order','coverage_missing','coverage_overlap','outside_coverage','duplicate_clip','fps_ratio','bad_speed','too_many_words'])
def test_invalid_metadata_is_explicit_and_not_mutated(edl,case):
    dataset=edl['candidate_sets'][0];set_id='set'
    if case=='missing_set':set_id='missing'
    if case=='stale_source':edl['sources']['s1']['sha256']='f'*64
    if case=='missing_transcript_hash':dataset.pop('transcript_sha256')
    if case=='bad_index':dataset['words'][0]['index']=99
    if case=='nan':dataset['words'][0]['start']=float('nan')
    if case=='infinity':dataset['words'][0]['end']=float('inf')
    if case=='boolean':dataset['words'][0]['start']=True
    if case=='reverse_word':dataset['words'][0]['end']=-1
    if case=='word_order':dataset['words'][2]['start']=.1
    if case=='coverage_missing':dataset.pop('coverage')
    if case=='coverage_overlap':dataset['coverage']['processed_ranges']=[[0,3],[2,6]]
    if case=='outside_coverage':dataset['coverage']['processed_ranges']=[[0,1]]
    if case=='duplicate_clip':edl['cuts'][1]['id']=edl['cuts'][0]['id']
    if case=='fps_ratio':edl['output']['fps']='30000/1001'
    if case=='bad_speed':edl['cuts'][1]['speed']=0
    if case=='too_many_words':dataset['words']*=1100
    before=json.dumps(edl,sort_keys=True)
    with pytest.raises((ValueError,KeyError)):clock.inspect(edl,set_id)
    assert json.dumps(edl,sort_keys=True)==before


def test_api_and_agent_share_read_only_report_without_media_reads(edl,monkeypatch,tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backlot.editor_routes import create_editor_router
    from tools.video import studio_project_edit as agent
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path)
    value=edit.create('Synthetic clock inspection')
    pid=value['project_id'];path=tmp_path/pid/edit.ARTIFACT
    value['edit_decisions']=edl;studio.save_json(path,value);before=path.read_bytes()
    async def body(request,*args):return await request.json()
    app=FastAPI();app.include_router(create_editor_router(body));client=TestClient(app)
    response=client.get(f'/api/studio/editor/{pid}/subtitle-words?set_id=set')
    assert response.status_code==200 and len(response.json()['words'])==6
    def request(route,data=None,**kwargs):
        assert data is None
        result=client.get('/api/studio/editor/'+route);assert result.status_code==200
        return result.json()
    monkeypatch.setattr(agent,'request',request)
    result=agent.StudioProjectEdit().execute(dict(project_id=pid,action='subtitle_words',set_id='set'))
    assert result.success and result.data['words']==response.json()['words']
    assert path.read_bytes()==before
    assert not (tmp_path/pid/'assets/s1.mp4').exists()  # Only registered synthetic metadata is used.
