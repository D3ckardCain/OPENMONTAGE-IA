import pytest

from lib import studio_color as color
from tests.backlot.test_studio_editor import add, command, project
from lib import studio_editor as edit, studio_editor_render as render, production_studio as studio


def test_temperature_tint_are_bounded_and_share_preview_export_filter():
    warm = color.normalize({'temperature': 0.5, 'tint': 0.25})
    assert warm['temperature'] == 0.5 and warm['tint'] == 0.25
    graph = color.suffix(warm)
    assert 'colorbalance=' in graph and 'rs=0.075' in graph and 'gs=-0.03' in graph
    assert 'rh=0.075' in graph and 'bh=-0.045' in graph
    cool = color.suffix({'temperature': -0.5, 'tint': -0.25})
    assert 'rs=-0.075' in cool and 'gs=0.03' in cool and 'bh=0.045' in cool
    assert color.suffix({'temperature': 0, 'tint': 0}) == ''


@pytest.mark.parametrize('key,value', [('temperature', 1.01), ('temperature', float('nan')),
                                       ('tint', -1.01), ('tint', True)])
def test_invalid_temperature_tint_fail_atomically(project, key, value):
    pid, api_key, _ = project
    clip = add(pid, api_key)
    before = edit.state(pid)
    with pytest.raises(ValueError):
        command(pid, 'clip_color', id=clip, color={key: value})
    assert edit.state(pid) == before


def test_temperature_tint_share_agent_history_persistence_and_bypass(project):
    pid, api_key, _ = project
    clip = add(pid, api_key)
    original = edit.state(pid)
    active = command(pid, 'clip_color', id=clip,
                     color={'temperature': 0.4, 'tint': -0.2})
    assert active['render_sha256'] != original['render_sha256']
    for preview in (True, False):
        graph = ';'.join(render.plan(pid, active['edit_decisions'], preview)[1])
        assert 'colorbalance=' in graph and 'rs=0.036' in graph
    edit.command(pid, {'operation': 'clip_color', 'revision': active['revision'], 'id': clip,
                       'color': {**active['edit_decisions']['cuts'][0]['color'], 'bypass': True}}, 'agent')
    bypass = edit.state(pid)
    assert bypass['render_sha256'] == original['render_sha256']
    command(pid, 'save')
    saved = studio.read_json(studio.project_path(pid) / edit.ARTIFACT)['edit_decisions']
    assert saved == bypass['edit_decisions']
