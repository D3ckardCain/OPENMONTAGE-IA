import pytest

from lib.sports_sources import catalog
from tools.football import official_jleague as jleague
from tools.graphics.sports_card import render
from tools.tool_registry import ToolRegistry


@pytest.fixture
def official_page(monkeypatch):
    url = jleague.goals_url(2025)
    page = f'''
    <link rel="canonical" href="{url}">
    <title>2025 Season - Top scorers | J1 League Player Stats | Official Website of J.LEAGUE</title>
    '''
    for name, player, goals in [('Example One', '100', 21), ('Example Two', '200', 18), ('Unlinked', None, 18)]:
        row = f'''<div class="{jleague.ROW_CLASS}" name="{name}" score="{goals}">
        <p class="{jleague.ROW_CLASS}__points">{goals}</p></div>'''
        page += f'<a class="{jleague.ROW_CLASS}__link" href="/en/player/{player}/">{row}</a>' if player else row

    def fetch(requested):
        assert requested == url
        return page, {'url': url, 'retrieved_at': '2026-11-20T00:00:00Z'}

    monkeypatch.setattr(jleague, 'fetch', fetch)
    return page


def test_source_discovery_and_comparison(official_page):
    entry = next(row for row in catalog('football', 'asia')['sources'] if row['id'] == 'jleague')
    assert entry['connector'] in ToolRegistry().register_module(jleague)
    result = jleague.OfficialJLeague().execute(
        {'action': 'compare_players', 'season': 2025, 'names': ['Exámple One', 'Example Two']})
    assert result.success and result.data['ready_for_script']
    assert result.cost_usd == 0 and not result.from_cache
    assert [row['statistics']['goals'] for row in result.data['records']] == [21, 18]
    assert 'J1 League · 2025' in render(result.data)
    result.data['records'][0]['statistics_source']['url'] = jleague.goals_url(2024)
    with pytest.raises(ValueError, match='fuente'):
        render(result.data)


@pytest.mark.parametrize(('name', 'reason'), [('Unlinked', 'official_id_missing'), ('Missing', 'not_in_visible_ranking')])
def test_unverified_identity_blocks_rendering(official_page, name, reason):
    result = jleague.OfficialJLeague().execute({'action': 'collectible_card', 'season': 2025, 'names': [name]})
    assert result.success and not result.data['ready_for_script']
    assert result.data['records'] == []
    assert result.data['unresolved'] == [{'name': name, 'reason': reason}]
    with pytest.raises(ValueError):
        render(result.data)


def test_rejects_wrong_season_and_inconsistent_visible_score(official_page):
    with pytest.raises(ValueError, match='temporada'):
        jleague.parse_goals(official_page, 2024)
    with pytest.raises(ValueError, match='Fila'):
        jleague.parse_goals(official_page.replace('>21</p>', '>20</p>'), 2025)
