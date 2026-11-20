import pytest

from lib.sports_sources import catalog
from tools.football import official_jleague as jleague
from tools.graphics.sports_card import render
from tools.tool_registry import ToolRegistry


@pytest.fixture
def official_page(monkeypatch):
    url = jleague.ranking_url(2025, 'goals')
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
    result.data['records'][0]['facts'][0]['source_url'] = jleague.ranking_url(2024, 'goals')
    with pytest.raises(ValueError, match='fuente'):
        render(result.data)


@pytest.mark.parametrize(('name', 'reason'), [('Unlinked', 'official_id_missing'), ('Missing', 'not_in_visible_ranking')])
def test_unverified_identity_blocks_rendering(official_page, name, reason):
    result = jleague.OfficialJLeague().execute({'action': 'collectible_card', 'season': 2025, 'names': [name]})
    assert result.success and not result.data['ready_for_script']
    assert result.data['records'] == []
    assert result.data['unresolved'] == [{'name': name, 'reason': reason, 'metric': 'goals', 'value': None}]
    with pytest.raises(ValueError):
        render(result.data)


def test_rejects_wrong_season_and_inconsistent_visible_score(official_page):
    with pytest.raises(ValueError, match='temporada'):
        jleague.parse_ranking(official_page, 2024, 'goals')
    with pytest.raises(ValueError, match='Fila'):
        jleague.parse_ranking(official_page.replace('>21</p>', '>20</p>'), 2025, 'goals')


def test_combined_metrics_keep_separate_sources_and_block_missing(official_page, monkeypatch):
    goals_url = jleague.ranking_url(2025, 'goals')
    assists_url = jleague.ranking_url(2025, 'assists')
    assists = official_page.replace(goals_url, assists_url).replace('Top scorers', 'Assists')
    assists = assists.replace('score="21"', 'score="15"').replace('>21</p>', '>15</p>')
    assists = assists.replace('Example Two', 'Other Player')

    def fetch(url):
        if url not in (goals_url, assists_url):
            raise OSError('Profile unavailable')
        return (official_page if url == goals_url else assists), {'url': url, 'retrieved_at': '2026-11-20'}

    monkeypatch.setattr(jleague, 'fetch', fetch)
    tool = jleague.OfficialJLeague()
    args = {'season': 2025, 'metrics': ['goals', 'assists']}
    card = tool.execute(dict(args, action='collectible_card', names=['Example One']))
    assert card.success and card.data['ready_for_script']
    facts = card.data['records'][0]['facts']
    assert [(f['metric'], f['value'], f['source_url']) for f in facts] == [
        ('goals', 21, goals_url), ('assists', 15, assists_url)]
    assert 'Asistencias' in render(card.data)
    facts[1]['source_url'] = goals_url
    with pytest.raises(ValueError, match='fuente'):
        render(card.data)

    comparison = tool.execute(dict(args, action='compare_players', names=['Example One', 'Example Two']))
    assert comparison.success and not comparison.data['ready_for_script']
    assert comparison.data['records'][1]['statistics'] == {'goals': 18, 'assists': None}
    with pytest.raises(ValueError):
        render(comparison.data)

def test_goals_recovered_from_the_same_official_player_profile(official_page, monkeypatch):
    goals_url = jleague.ranking_url(2025, 'goals')
    assists_url = jleague.ranking_url(2025, 'assists')
    player_url = jleague.profile_url('100')
    profile = f"""
    <link rel="canonical" href="{player_url}">
    <title>One Example | Club | Official Website of J.LEAGUE</title>
    <table><tr><th>Season</th><th>Club</th><th>League</th><th>League Cup</th><th>U-21</th></tr>
    <tr><th>App.</th><th>Goals</th><th>App.</th><th>Goals</th><th>App.</th><th>Goals</th></tr>
    <tr><td>2025</td><td><p>Club</p><span>J1</span></td><td>32</td><td>7</td>
    <td>4</td><td>1</td><td>-</td><td>-</td></tr>
    <tr><td>2025</td><td><p>Other Club</p><span>J2</span></td><td>2</td><td>3</td>
    <td>0</td><td>0</td><td>-</td><td>-</td></tr></table>
    """
    pages = {
        goals_url: official_page.replace('Example One', 'Other Player'),
        assists_url: official_page.replace(goals_url, assists_url).replace('Top scorers', 'Assists'),
        player_url: profile,
    }

    def fetch(url):
        return pages[url], {'url': url, 'retrieved_at': '2026-11-20'}

    monkeypatch.setattr(jleague, 'fetch', fetch)
    inputs = {'action': 'collectible_card', 'season': 2025, 'names': ['Example One'],
              'metrics': ['goals', 'assists']}
    result = jleague.OfficialJLeague().execute(inputs)
    assert result.success and result.data['ready_for_script']
    goals = result.data['records'][0]['facts'][0]
    assert (goals['value'], goals['source_url']) == (7, player_url)
    assert 'Goles' in render(result.data)

    pages[player_url] = profile.replace('One Example', 'Wrong Player')
    result = jleague.OfficialJLeague().execute(inputs)
    assert result.success and not result.data['ready_for_script']
    assert result.data['records'][0]['statistics']['goals'] is None
