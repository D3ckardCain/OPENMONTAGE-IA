"""Reference plan contracts only; no generated media or orchestration agents."""
from copy import deepcopy
import pytest
from lib import studio_editor as edit,studio_reference_plan as reference,production_studio as studio


def fixture():
    edl=edit._empty();edl['sources']={'s':dict(sha256='a'*64,duration=10,kind='video',path='assets/ref.mp4')}
    edl['markers']=[dict(id='note',seconds=1,label='Revisar cifra y fuente')]
    plan=dict(version='1.0',scenes=[dict(id=k,type='text_card',description='Plan propuesto, no plano observado',start_seconds=i,end_seconds=i+1) for i,k in enumerate(['one','two'])],metadata=dict(reference_contract='studio-reference-plan-v1',
        evidence=[dict(source_id='s',source_sha256='a'*64,receipt_sha256='b'*64,requested_range=[0,2],coverage='partial_sampled_images_only',frames=[dict(pts_seconds=1,sha256='c'*64)])],
        scene_refs={'one':['b'*64],'two':['b'*64]},scene_notes={'one':['note']},comparisons=[]))
    return edl,plan


def apply(edl,plan):reference.apply(edl,dict(input_edl_sha256=edit.edit_digest(edl),plan=plan))


def test_changed_scene_only_is_reviewed_and_markers_reused():
    edl,plan=fixture();apply(edl,plan)
    assert edl['reference_plan_origin']['changed_ids']==['one','two']
    changed=deepcopy(plan);changed['scenes'][0]['description']='Cambiar solo esta tarjeta';apply(edl,changed)
    assert edl['reference_plan_origin']['changed_ids']==['one']
    assert edl['reference_plan_origin']['unchanged_ids']==['two']
    assert not edl['reference_plan_origin']['generation_performed']
    assert edl['markers'][0]['label']=='Revisar cifra y fuente'


def test_note_change_invalidates_associated_scene_not_all():
    edl,plan=fixture();apply(edl,plan);edl['markers'][0]['label']='Corregir cifra'
    apply(edl,plan);assert edl['reference_plan_origin']['changed_ids']==['one']


@pytest.mark.parametrize('case',['hash','schema','coverage','timestamp','missing_before','note'])
def test_invalid_evidence_or_comparison_not_silently_accepted(case):
    edl,plan=fixture()
    if case=='hash':plan['metadata']['evidence'][0]['source_sha256']='f'*64
    if case=='schema':plan['scenes'][0]['type']='unknown_generator'
    if case=='coverage':plan['metadata']['evidence'][0]['coverage']='complete_video_seen'
    if case=='note':plan['metadata']['scene_notes']['one']=['missing']
    if case in ('timestamp','missing_before'):
        before=dict(source_sha256='a'*64,frame_sha256='c'*64,pts_seconds=1)
        after={**before,'frame_sha256':'d'*64,'pts_seconds':2 if case=='timestamp' else 1}
        if case=='missing_before':before['frame_sha256']='e'*64
        plan['metadata']['comparisons']=[dict(scene_id='one',clock='reference_source_pts',before=before,after=after)]
    with pytest.raises(ValueError):apply(edl,plan)
    assert 'reference_plan' not in edl


def test_shared_editor_undo_redo_reopen_no_media_processing(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path);value=edit.create('Plan QA');pid=value['project_id'];edl,plan=fixture()
    value['edit_decisions']=edl;studio.save_json(tmp_path/pid/edit.ARTIFACT,value)
    data=dict(operation='reference_plan',revision=0,input_edl_sha256=edit.edit_digest(edl),plan=plan)
    applied=edit.command(pid,data)['edit_decisions'];assert applied['reference_plan']==plan
    with pytest.raises(edit.Conflict):edit.command(pid,data)
    assert edit.command(pid,dict(operation='undo',revision=1))['edit_decisions']==edl
    assert edit.command(pid,dict(operation='redo',revision=2))['edit_decisions']==applied
    assert edit.state(pid)['edit_decisions']==applied
