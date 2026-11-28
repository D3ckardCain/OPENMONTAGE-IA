import pytest

from lib.football_statistics import add_standard_statistics
from lib.sports_sources import catalog
from tools.football import official_mls as mls
from tools.graphics.sports_card import render
from tools.tool_registry import ToolRegistry


def page():
    return f"""
    <link rel="canonical" href="{mls.SOURCE_URL}">
    <h1>Estos son los máximos goleadores de cada equipo de MLS en 2025</h1>
    <div class="oc-c-article__body">
      <div class="body-part">Jugadores de la temporada regular de MLS 2025.</div>
      <div class="body-part"><a href="/jugadores/player-one/">Player One</a><a href="/clubes/team-one/">Team One</a></div>
      <div class="body-part">ESTADÍSTICAS: 11 goles, 4 asistencias en 30 partidos - 1.807 minutos</div>
      <div class="body-part"><a href="/jugadores/player-two/">Player Two</a><a href="/clubes/team-two/">Team Two</a></div>
      <div class="body-part">ESTADÍSTICAS: 7 goles, 1 asistencia en 30 partidos - 2.198 minutos</div>
    </div>
    """


def test_mls_official_report_is_discoverable_and_renders_common_fields(monkeypatch):
    entry = next(row for row in catalog('football', 'americas')['sources'] if row['id'] == 'mls')
    assert entry['connector'] in ToolRegistry().register_module(mls)
    monkeypatch.setattr(mls, 'fetch', lambda: (page(), {'url': mls.SOURCE_URL, 'retrieved_at': '2026-11-20'}))
    tool = mls.OfficialMLS()
    result = tool.execute({'action': 'compare_players', 'season': 2025, 'names': ['Player One', 'Player Two']})
    assert result.success and result.data['ready_for_script']
    stats = add_standard_statistics(result.data)['records'][0]['standard_statistics']
    assert len(stats) == 54 and stats['minutes_played']['value'] == 1807 and stats['shots'] is None
    assert 'Temporada regular' in render(result.data)
    blocked = tool.execute({'action': 'collectible_card', 'season': 2025, 'names': ['Unknown']})
    assert blocked.success and not blocked.data['ready_for_script']
    assert blocked.data['records'] == []


def test_mls_rejects_a_source_with_the_wrong_season():
    with pytest.raises(ValueError, match='temporada'):
        mls.parse(page().replace('temporada regular de MLS 2025', 'postemporada de MLS 2025'))
