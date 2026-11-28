"""Reversible effects/presets contracts. Actual AV QA is explicitly opt-in."""
import pytest

from lib import studio_editor as edit, studio_editor_render as render
from tests.backlot.test_studio_editor import project, command, add


def test_transform_validates_and_maps_to_compositor(project):
    pid, key, _ = project
    clip = add(pid, key)
    before = edit.state(pid)
    value = command(pid, 'transform', id=clip, fit='crop', rotation=90, zoom=1.5, focus_x=0, focus_y=1, flip_h=True)
    _, filters, _, _ = render.plan(pid, value['edit_decisions'], True)
    video = next(f for f in filters if '[0:v:0]' in f)
    assert 'transpose=clock' in video and 'hflip' in video and 'crop=960:540' in video
    assert value['render_sha256'] != before['render_sha256']
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions'] == before['edit_decisions']
    for params in [{'rotation': 45}, {'zoom': 0}, {'fit': 'pad', 'focus_x': 1}, {'flip_h': 1}]:
        checkpoint = edit.state(pid)
        with pytest.raises(ValueError):
            command(pid, 'transform', id=clip, **params)
        assert edit.state(pid) == checkpoint


def test_title_times_style_and_undo_are_shared_data(project):
    pid, key, _ = project
    add(pid, key)
    before = edit.state(pid)
    value = command(pid, 'title_add', text='Manual {title}\nSecond line', start_seconds=1, end_seconds=4, size=64)
    title = value['edit_decisions']['titles'][0]
    command(pid, 'title_update', id=title['id'], text='Edited', start_seconds=2, end_seconds=5, size=80, position='top')
    command(pid, 'undo')
    assert edit.state(pid)['edit_decisions']['titles'][0] == title
    command(pid, 'title_remove', id=title['id'])
    assert edit.state(pid)['render_sha256'] == before['render_sha256']
    with pytest.raises(ValueError):
        command(pid, 'title_add', text='Outside', start_seconds=9, end_seconds=11)


def test_output_custom_is_even_bounded_and_platform_is_not_av_identity(project):
    pid, key, _ = project
    add(pid, key)
    value = command(pid, 'output_custom', width=1080, height=1920, fps=30, platform='tiktok', preset_name='Editable vertical')
    _, _, w, h = render.plan(pid, value['edit_decisions'], True)
    assert (w, h) == (540, 960)
    digest = value['render_sha256']
    value = command(pid, 'output_custom', width=1080, height=1920, fps=30, platform='instagram', preset_name='Other label')
    assert value['render_sha256'] == digest
    for params in [{'width': 1079}, {'height': 0}, {'fps': True}, {'width': 3840, 'height': 3840}]:
        with pytest.raises(ValueError):
            command(pid, 'output_custom', **{'width':1080,'height':1920,'fps':30,**params})


def test_mix_reuses_loudnorm_and_does_not_normalize_silently(project):
    pid, key, _ = project
    add(pid, key)
    before = edit.state(pid)
    value = command(pid, 'audio_mix', normalize=False, target_lufs=-14, gain=1)
    assert value['render_sha256'] == before['render_sha256']
    _, filters, _, _ = render.plan(pid, value['edit_decisions'], True)
    assert not any('loudnorm' in f for f in filters)
    value = command(pid, 'audio_mix', normalize=True, target_lufs=-18, gain=.5)
    _, filters, _, _ = render.plan(pid, value['edit_decisions'], True)
    assert any('loudnorm=I=-18.0' in f and 'aresample=48000' in f for f in filters)
    assert any('level=0' in f for f in filters)
