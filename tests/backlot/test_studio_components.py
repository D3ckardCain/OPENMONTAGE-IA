"""Own presets on shared EDL. No old renderer suite or approved render repeated."""
from copy import deepcopy
import pytest
from lib import studio_editor as edit,production_studio as studio,studio_components as components
from lib import studio_timeline_ops as timeline


def params(kind,**kw):
    return dict(operation='component_add',kind=kind,start_seconds=0,end_seconds=4,platform='tiktok',
                source_label='QA propia',source_url='',rights='own',text='Muestra técnica',
                left_text='Antes: 1',right_text='Después: 2',source_ids=['s'],**kw)


def edl():
    e=edit._empty();e['sources']={'s':dict(kind='video',duration=3,path='assets/own.mp4',audio=False,sha256='a'*64)}
    return e


@pytest.mark.parametrize('kind',['evidence_card','comparison','collage'])
def test_presets_are_real_editable_titles_layers_with_provenance(kind):
    e=edl();edit._apply_edit(e,params(kind));edit._validate_edit(e)
    assert edit.duration(e)==4 and e['output']['background']=='#0d1117'
    assert e['titles'] and all(t['component_origin']['source_label']=='QA propia' for t in e['titles'])
    if kind=='collage':
        assert e['layers'][0]['fit']=='crop' and e['layers'][0]['motion']['duration_seconds']==4
        before=e['layers'][0]['x'];edit._apply_edit(e,dict(operation='layer_update',id=e['layers'][0]['id'],x=before+.01))
        assert e['layers'][0]['x']==pytest.approx(before+.01)


def test_component_title_render_wrap_box_and_normalized_position_all_ratios():
    e=edl();edit._apply_edit(e,params('comparison'))
    for width,height in [(1920,1080),(1080,1920),(1080,1080),(1080,1350)]:
        t=e['titles'][0];ass=components.title_ass(t,width,height)
        style=next(l for l in ass.splitlines() if l.startswith('Style:')).split(',')
        assert style[15]=='3' and style[18]=='5' and style[17]=='0'
        assert '\\pos('+str(round(width*t['component_layout']['anchor_x']))+','+str(round(height*.5))+')' in ass


def test_silence_ripple_keeps_absolute_motion_phase():
    e=edl();edit._apply_edit(e,params('collage'));layer=e['layers'][0]
    pieces=timeline._ripple_sources([layer],[(.5,1)],minimum=0)
    assert pieces[0]['motion']['phase_seconds']==0
    assert pieces[1]['motion']['phase_seconds']==1
    assert pieces[1]['start_seconds']==pytest.approx(.5)


@pytest.mark.parametrize('case',['outside','unknown','dirty_background','long_text'])
def test_invalid_presets_rollback_transaction(tmp_path,monkeypatch,case):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path);value=edit.create('Component QA');pid=value['project_id'];e=edl()
    value['edit_decisions']=e;path=tmp_path/pid/edit.ARTIFACT;studio.save_json(path,value)
    data=params('collage');data['revision']=0
    if case=='outside':data['start_seconds']=1
    if case=='unknown':data['kind']='remote_component'
    if case=='long_text':data['text']='x'*49
    if case=='dirty_background':
        e['cuts']=[dict(id='v',source_id='s',source='assets/own.mp4',in_seconds=0,out_seconds=3,speed=1)]
        studio.save_json(path,value);data['end_seconds']=3
    before=path.read_bytes()
    with pytest.raises(ValueError):edit.command(pid,data)
    assert path.read_bytes()==before


def test_edit_remove_undo_redo_reopen_preserves_shared_project(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path);v=edit.create('Components shared');pid=v['project_id'];v['edit_decisions']=edl();studio.save_json(tmp_path/pid/edit.ARTIFACT,v)
    applied=edit.command(pid,dict(revision=0,**params('evidence_card')))['edit_decisions']
    title=applied['titles'][0];text='Cambio manual'
    updated=edit.command(pid,dict(revision=1,operation='title_update',id=title['id'],text=text,start_seconds=0,end_seconds=3,size=48,position='bottom',anchor_x=.4))['edit_decisions']
    assert updated['titles'][0]['component_layout']['anchor_x']==.4
    removed=edit.command(pid,dict(revision=2,operation='component_remove',id=title['component_id']))['edit_decisions']
    assert not removed['titles']
    assert edit.command(pid,dict(revision=3,operation='undo'))['edit_decisions']==updated
    assert edit.command(pid,dict(revision=4,operation='redo'))['edit_decisions']==removed
    assert edit.state(pid)['edit_decisions']==removed


def test_bad_motion_never_moves_layer_outside_canvas():
    e=edl();edit._apply_edit(e,params('collage'))
    with pytest.raises(ValueError,match='sacaría'):
        edit._apply_edit(e,dict(operation='layer_update',id=e['layers'][0]['id'],motion=dict(dx=1,dy=0,duration_seconds=1)))


def test_vertical_component_text_uses_bounded_mobile_font():
    e=edl();edit._apply_edit(e,params("comparison"))
    ass=components.title_ass(e["titles"][0],360,640)
    fields=next(line for line in ass.splitlines() if line.startswith("Style:")).split(",")
    assert 14<=int(fields[2])<=22


def test_component_renderer_revision_invalidates_only_its_cached_renders(monkeypatch):
    plain=edl();old_plain=edit.render_digest(plain)
    preset=edl();edit._apply_edit(preset,params("evidence_card"));old=edit.render_digest(preset)
    monkeypatch.setattr(components,"RENDER_CONTRACT","next-render-revision")
    assert edit.render_digest(preset)!=old
    assert edit.render_digest(plain)==old_plain
