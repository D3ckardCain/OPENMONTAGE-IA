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

    assert jleague.profile_goals(profile, '100', 'Example One', 2025, 'j2') == 3
    pages[player_url] = profile.replace('One Example', 'Wrong Player')
    result = jleague.OfficialJLeague().execute(inputs)
    assert result.success and not result.data['ready_for_script']
    assert result.data['records'][0]['statistics']['goals'] is None


@pytest.mark.parametrize('division', ['j2', 'j3'])
def test_division_uses_its_own_rankings_and_rejects_j1_evidence(official_page, monkeypatch, division):
    j1_url = jleague.ranking_url(2025, 'goals')
    division_url = jleague.ranking_url(2025, 'goals', division)
    division_page = official_page.replace(j1_url, division_url).replace('J1 League', f'{division.upper()} League')

    def fetch(url):
        assert url == division_url
        return division_page, {'url': url, 'retrieved_at': '2026-11-20'}

    monkeypatch.setattr(jleague, 'fetch', fetch)
    result = jleague.OfficialJLeague().execute(
        {'action': 'collectible_card', 'season': 2025, 'competition': division, 'names': ['Example One']})
    assert result.success and result.data['ready_for_script']
    assert f'{division.upper()} League · 2025' in render(result.data)
    result.data['records'][0]['facts'][0]['source_url'] = j1_url
    with pytest.raises(ValueError, match='fuente'):
        render(result.data)
    with pytest.raises(ValueError, match='división'):
        jleague.parse_ranking(official_page, 2025, 'goals', division)


def test_levain_cup_keeps_cup_scope_and_skips_league_profile(official_page, monkeypatch):
    goals_url = jleague.ranking_url(2025, 'goals', 'leaguecup')
    assists_url = jleague.ranking_url(2025, 'assists', 'leaguecup')
    cup_goals = official_page.replace(jleague.ranking_url(2025, 'goals'), goals_url).replace('J1 League', 'Levain Cup')
    cup_assists = cup_goals.replace(goals_url, assists_url).replace('Top scorers', 'Assists')

    def fetch(url):
        page = {goals_url: cup_goals.replace('Example Two', 'Other Player'), assists_url: cup_assists}[url]
        return page, {'url': url, 'retrieved_at': '2026-11-20'}

    monkeypatch.setattr(jleague, 'fetch', fetch)
    inputs = {'action': 'collectible_card', 'season': 2025, 'competition': 'leaguecup',
              'metrics': ['goals', 'assists']}
    tool = jleague.OfficialJLeague()
    card = tool.execute(dict(inputs, names=['Example One']))
    assert card.success and card.data['ready_for_script']
    assert card.data['scope']['phase'] == 'cup'
    assert 'Levain Cup · 2025' in render(card.data)
    card.data['scope']['phase'] = 'league'
    with pytest.raises(ValueError, match='Alcance'):
        render(card.data)

    missing = tool.execute(dict(inputs, names=['Example Two']))
    assert missing.success and not missing.data['ready_for_script']
    assert missing.data['records'][0]['statistics']['goals'] is None


@pytest.mark.parametrize(('metric', 'title', 'label'), [
    ('duels_won', 'Duels won', 'Duelos ganados'),
    ('aerial_duels_won', 'Aerial duels won', 'Duelos aéreos ganados'),
    ('shots', 'Shots', 'Tiros'),
    ('shots_on_target', 'Shots on target', 'Tiros a puerta'),
    ('matches_played', 'Appearances', 'Partidos jugados'),
    ('minutes_played', 'Minutes played', 'Minutos jugados'),
    ('passes_attempted', 'Passes', 'Pases intentados'),
    ('crosses_attempted', 'Crosses', 'Centros intentados'),
    ('chances_created', 'Chances created', 'Ocasiones creadas'),
    ('distance_covered', 'Distance', 'Distancia recorrida'),
    ('sprints', 'Sprints', 'Sprints'),
    ('pass_accuracy', 'Pass accuracy', 'Precisión de pase'),
    ('saves', 'Saves', 'Paradas'),
    ('penalty_goals', 'Goals (penalty)', 'Penaltis marcados'),
    ('fouls_committed', 'Fouls committed', 'Faltas cometidas'),
    ('fouls_suffered', 'Fouls won', 'Faltas recibidas'),
    ('clearances', 'Clearances', 'Despejes'),
    ('blocks', 'Blocks', 'Bloqueos'),
    ('tackles', 'Tackles', 'Entradas'),
    ('long_balls_completed', 'Long passes', 'Pases largos completados'),
    ('dribbles_attempted', 'Dribbles', 'Regates intentados'),
    ('touches', 'Ball touches', 'Toques de balón'),
    ('recoveries', 'Ball recoveries', 'Recuperaciones'),
    ('expected_goals', 'Expected Goals', 'Goles esperados (xG)'),
    ('top_speed', 'Top Speed', 'Velocidad máxima'),
    ('save_percentage', 'Save success rate', 'Porcentaje de paradas'),
    ('clean_sheets', 'Clean sheets', 'Porterías a cero'),
    ('yellow_cards', 'Yellow cards', 'Tarjetas amarillas'),
    ('red_cards', 'Red cards', 'Tarjetas rojas'),
])
def test_added_metric_uses_its_own_ranking_and_label(official_page, monkeypatch, metric, title, label):
    url = jleague.ranking_url(2025, metric)
    page = official_page.replace(jleague.ranking_url(2025, 'goals'), url).replace('Top scorers', title)
    suffix = jleague.DISPLAY_SUFFIXES.get(metric, '')
    for score in (21, 18):
        page = page.replace(f'>{score}</p>', f'>{score}{suffix}</p>')
    if jleague.METRIC_UNITS.get(metric) in jleague.DECIMAL_UNITS:
        page = page.replace('score="21"', 'score="21.5"').replace(
            f'>21{suffix}</p>', f'>21.5{suffix}</p>')


    def fetch(requested):
        assert requested == url
        return page, {'url': url, 'retrieved_at': '2026-11-20'}

    monkeypatch.setattr(jleague, 'fetch', fetch)
    result = jleague.OfficialJLeague().execute(
        {'action': 'compare_players', 'season': 2025, 'names': ['Example One', 'Example Two'],
         'metrics': [metric]})
    assert result.success and result.data['ready_for_script']
    assert result.data['records'][0]['statistics'] == {metric: 21.5 if jleague.METRIC_UNITS.get(metric) in jleague.DECIMAL_UNITS else 21}
    if jleague.METRIC_UNITS.get(metric) == '%':
        assert result.data['records'][0]['facts'][0]['unit'] == '%'
        assert '21.5%' in render(result.data)
        with pytest.raises(ValueError):
            jleague.parse_ranking(page.replace('21.5', '121.5'), 2025, metric)
    assert label in render(result.data)
    if metric == 'distance_covered':
        assert result.data['records'][0]['facts'][0]['unit'] == 'km'
        assert '21.5 km' in render(result.data)
    if metric == 'top_speed':
        assert result.data['records'][0]['facts'][0]['unit'] == 'km/h'
        assert '21.5 km/h' in render(result.data)
    if metric == 'sprints':
        assert '25 km/h' in result.data['records'][0]['facts'][0]['provider_definition']
    if metric in jleague.METRIC_DEFINITIONS:
        from lib.football_statistics import add_standard_statistics
        stats = add_standard_statistics(result.data)['records'][0]['standard_statistics']
        fact = result.data['records'][0]['facts'][0]
        assert fact['provider_definition'] == jleague.METRIC_DEFINITIONS[metric]
        if metric == 'tackles':
            assert stats['tackles_attempted'] is None and stats['tackles_won'] is None
        else:
            assert stats[metric]['provider_definition'] == fact['provider_definition']


@pytest.mark.parametrize('selection', ['all', ['goals', 'red_cards', 'interceptions']])
def test_multi_metric_queries_retain_results_after_one_source_failure(official_page, monkeypatch, selection):
    goals_url = jleague.ranking_url(2025, 'goals')
    pages = {
        jleague.ranking_url(2025, metric):
        official_page.replace(goals_url, jleague.ranking_url(2025, metric)).replace('Top scorers', title)
        for metric, (_, title) in jleague.METRICS.items()
    }
    for metric, suffix in jleague.DISPLAY_SUFFIXES.items():
        url = jleague.ranking_url(2025, metric)
        for score in (21, 18):
            pages[url] = pages[url].replace(f'>{score}</p>', f'>{score}{suffix}</p>')
    failed_url = jleague.ranking_url(2025, 'red_cards')

    def fetch(url):
        if url == failed_url:
            raise OSError('Ranking unavailable')
        return pages[url], {'url': url, 'retrieved_at': '2026-11-20'}

    monkeypatch.setattr(jleague, 'fetch', fetch)
    result = jleague.OfficialJLeague().execute({
        'action': 'collectible_card', 'season': 2025, 'names': ['Example One'], 'metrics': selection,
    })
    assert result.success and not result.data['ready_for_script']
    assert set(result.data['failed_metrics']) == {'red_cards'}
    record = result.data['records'][0]
    assert list(record['statistics']) == (list(jleague.METRICS) if selection == 'all' else selection)
    assert record['statistics']['red_cards'] is None
    assert record['statistics']['interceptions'] == 21
    assert all(fact['source_url'] != failed_url for fact in record['facts'])


def test_split_season_is_distinct_from_the_jleague_special_edition(official_page, monkeypatch):
    old_url = jleague.ranking_url(2025, 'goals')
    url = jleague.ranking_url('2026-27', 'goals')
    page = official_page.replace(old_url, url).replace('2025 Season', '2026/27 Season').replace('Example One', 'One Example')

    def fetch(requested):
        assert requested == url
        return page, {'url': url, 'retrieved_at': '2026-11-20'}

    monkeypatch.setattr(jleague, 'fetch', fetch)
    inputs = {'action': 'collectible_card', 'season': '2026/27', 'names': ['Example One']}
    result = jleague.OfficialJLeague().execute(inputs)
    assert result.success and result.data['ready_for_script']
    assert result.data['scope']['season'] == '2026-27'
    assert result.data['records'][0]['identity']['name'] == 'One Example'
    assert 'J1 League · 2026/27' in render(result.data)
    with pytest.raises(ValueError, match='Temporada'):
        jleague.season_key('2026/28', 'j1')
    with pytest.raises(ValueError, match='Copa Levain'):
        jleague.season_key(2026, 'leaguecup')

    special_url = jleague.ranking_url(2026, 'goals')
    special = official_page.replace(old_url, special_url).replace('2025 Season', '2026 Special Season')
    assert jleague.parse_ranking(special, 2026, 'goals')[0][2] == 21
    with pytest.raises(ValueError, match='temporada'):
        jleague.parse_ranking(special.replace('2026 Special Season', '2026/27 Season'), 2026, 'goals')
