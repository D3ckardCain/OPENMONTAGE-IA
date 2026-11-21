import pytest
from lib.football_comparisons import collect, select
from tools.football.ligamx import RANKINGS, ranking_urls, tournament_scope
from tools.football.official_jleague import METRICS as JLEAGUE_METRICS


def test_premier_desk_preserves_matchweek_and_source(monkeypatch):
    from lib.world_cup_edition_desk import compare_edition
    from tools.football.official_premier import OfficialPremier, URL

    monkeypatch.setattr(OfficialPremier, 'read_rankings', lambda self: ({
        'goals': {'a': ('A', 'AAA', 4), 'b': ('B', 'BBB', 3)},
        'assists': {'a': ('A', 'AAA', 2), 'b': ('B', 'BBB', 1)},
    }, []))
    result = compare_edition([{'name': 'A', 'team': ''}, {'name': 'B', 'team': ''}],
                             'premier:2024-2025:regular_season')
    assert result['report']['scope']['through_matchweek'] == 29
    assert result['report']['queries'][0]['url'] == URL
    assert {'goals', 'assists'} <= set(result['display_metrics'])
    assert result['report']['ready_for_script']


@pytest.mark.parametrize('competition,season', [('euro', 2024), ('champions', 2025),
                                               ('europa', 2025), ('conference', 2025),
                                               ('women_champions', 2025)])
def test_uefa_desk_uses_tournament_phase_and_source_batches(monkeypatch, competition, season):
    from lib.world_cup_edition_desk import compare_edition
    from tools.football.official_uefa import OfficialUEFA
    from tools.base_tool import ToolResult

    origin = {'url': 'https://compstats.uefa.com/example', 'consultado_utc': '2026-11-21'}
    scope = {'competitionId': '3', 'seasonYear': season, 'phase': 'TOURNAMENT'}

    def execute(self, args):
        assert args['competition'] == competition
        assert args['edition'] == season and args['phase'] == 'TOURNAMENT'
        assert args['metrics'] == 'all'
        rows = [{'id': str(i), 'nombre': name, 'estadisticas': {'goals': i},
                 'fuente_estadisticas': origin, 'fuente_por_metrica': {'goals': origin}}
                for i, name in enumerate(args['names'], 1)]
        report = {'fuente': 'UEFA', 'tipo': 'comparativa_jugadores', 'alcance': scope,
                  'consultas': [origin], 'registros': rows, 'ready_for_script': True}
        return ToolResult(success=True, data=report, cost_usd=0, from_cache=False)

    monkeypatch.setattr(OfficialUEFA, 'execute', execute)
    result = compare_edition([{'name': 'A'}, {'name': 'B'}],
                             f'{competition}:{season}:TOURNAMENT')
    assert result['report']['scope'] == scope
    assert result['report']['queries'][0]['url'] == origin['url']
    assert result['display_metrics'] == ['goals']


def test_euro_desk_handles_unresolved_names_without_server_error(monkeypatch):
    from lib.world_cup_edition_desk import compare_edition
    from tools.football.official_uefa import OfficialUEFA
    from tools.base_tool import ToolResult

    monkeypatch.setattr(OfficialUEFA, 'execute', lambda self, args: ToolResult(
        success=True, data={'fuente': 'UEFA', 'tipo': 'comparativa_bloqueada',
                            'registros': [], 'ready_for_script': False}, cost_usd=0, from_cache=False))
    result = compare_edition([{'name': 'No identificado'}, {'name': 'B'}], 'euro:2024:TOURNAMENT')
    assert result['report'] is None
    assert result['errors']


def test_fifa_desk_requests_verified_qatar_edition_without_phase_claim(monkeypatch):
    from lib.world_cup_edition_desk import compare_edition
    from tools.football.official_fifa import OfficialFIFA
    from tools.base_tool import ToolResult

    def execute(self, args):
        assert args['competition_id'] == '17' and args['season_id'] == '255711'
        assert args['subjects'] == [{'name': 'A', 'team_name': 'Argentina'}, {'name': 'B'}]
        scope = {'competition_id': '17', 'season_id': '255711',
                 'phase': 'season_aggregate_as_published'}
        source = {'url': 'https://fdh-api.fifa.com/v1/stats/season/99/players.json',
                  'retrieved_at': '2026-11-21'}
        records = [dict(entity_id=str(i), identity={'fdh_player_id': str(i), 'name': name},
                        statistics={'Goals': {'value': i, 'source_flag': True, 'unit': None}},
                        missing_metrics=[]) for i, name in enumerate(('A', 'B'), 1)]
        return ToolResult(success=True, data=dict(source='FIFA', type='player_comparison',
                         scope=scope, queries=[source], records=records, ready_for_script=True),
                          cost_usd=0, from_cache=False)

    monkeypatch.setattr(OfficialFIFA, 'execute', execute)
    result = compare_edition([{'name': 'A', 'team': 'Argentina'}, {'name': 'B'}],
                             'fifa_world_cup:2022:season_aggregate_as_published')
    assert result['display_metrics'] == ['Goals']
    assert result['phase_note']
    assert result['report']['scope']['phase'] == 'season_aggregate_as_published'
    from tools.graphics.sports_card import render
    assert '<svg' in render(result['report'], ['Goals'])


def test_partial_metric_selection_requires_resolved_identities_and_no_failed_batches():
    from lib.world_cup_edition_desk import can_export_selection
    records = [{'entity_id': 'a', 'missing_metrics': ['Assists']},
               {'entity_id': 'b', 'missing_metrics': ['Assists']}]
    fifa = {'source': 'FIFA', 'type': 'player_comparison', 'records': records,
            'ready_for_script': False}
    assert can_export_selection(fifa, ['Goals'])
    assert not can_export_selection(fifa, ['Goals'], ['timeout'])
    assert not can_export_selection({**fifa, 'records': records[:1]}, ['Goals'])
    assert not can_export_selection({**fifa, 'failed_metrics': {'Assists': 'timeout'}}, ['Goals'])
    uefa = {**fifa, 'source': 'UEFA', 'original_report': {'tipo': 'comparativa_jugadores',
            'standard_query': {'failed_batches': []}}}
    assert can_export_selection(uefa, ['goals'])
    uefa['original_report']['standard_query']['failed_batches'].append({'metrics': ['assists']})
    assert not can_export_selection(uefa, ['goals'])
    jleague = {**fifa, 'source': 'J.League', 'unresolved': [
        {'name': 'B', 'metric': 'assists', 'reason': 'not_in_visible_ranking'}]}
    assert can_export_selection(jleague, ['goals'])
    assert not can_export_selection({**jleague, 'unresolved': [{'name': 'B', 'reason': 'ambiguous'}]}, ['goals'])


def test_jleague_merges_metric_batches_with_source_evidence():
    calls = []
    scope = {'competition': 'j1', 'season': 2025, 'phase': 'regular_season'}

    def execute(connector, args):
        metrics = args['metrics']
        assert 1 <= len(metrics) <= 6
        calls.append(metrics)
        queries = [{'url': f'https://example.org/{metric}', 'retrieved_at': '2026-11-21'}
                   for metric in metrics]
        records = [dict(entity_id=player, identity={'entity_id': player, 'name': player},
                        facts=[dict(metric=metric, value=1, entity_id=player, scope=scope,
                                    source_url=query['url'], retrieved_at=query['retrieved_at'])
                               for metric, query in zip(metrics, queries)],
                        statistics=dict.fromkeys(metrics, 1)) for player in ('a', 'b')]
        return {'success': True, 'data': dict(source='J.League', scope=scope, queries=queries,
                                              records=records, failed_metrics={}, unresolved=[],
                                              visible_rows_by_metric={metric: 10 for metric in metrics})}

    result = collect('competition', [{'connector': 'official_jleague_live',
                                      'inputs': {'season': 2025, 'names': ['a', 'b']}}], execute)
    section = result['sections'][0]
    assert len(calls) > 1
    assert set().union(*map(set, calls)) == set(JLEAGUE_METRICS)
    assert set(section['display_metrics']) == set(JLEAGUE_METRICS)
    assert len(section['report']['queries']) == len(JLEAGUE_METRICS)
    assert set(section['report']['visible_rows_by_metric']) == set(JLEAGUE_METRICS)
    assert section['report']['records'][0]['facts'][0]['source_url'] == 'https://example.org/goals'


def test_jleague_does_not_mix_different_players_between_batches():
    from lib.football_comparisons import merge_batches
    scope = {'competition': 'j1', 'season': 2025}
    def batch(players):
        return {'source': 'J.League', 'scope': scope, 'queries': [], 'failed_metrics': {},
                'unresolved': [], 'records': [{'entity_id': name, 'facts': [], 'statistics': {}}
                                            for name in players]}
    import pytest
    with pytest.raises(ValueError, match='jugadores distintos'):
        merge_batches([batch(['a', 'b']), batch(['a', 'c'])])


def test_jleague_partial_batch_failure_is_not_verified():
    def execute(connector, args):
        if args['metrics'][0] != 'goals':
            return {'success': False, 'error': 'El ranking no respondió'}
        return {'success': True, 'data': {'source': 'J.League', 'scope': {'competition': 'j1'},
                'queries': [], 'failed_metrics': {}, 'unresolved': [],
                'records': [{'entity_id': name, 'facts': [], 'statistics': {'goals': 1}}
                            for name in ('a', 'b')]}}
    section = collect('competition', [{'connector': 'official_jleague_live',
              'inputs': {'season': 2025, 'names': ['a', 'b']}}], execute)['sections'][0]
    assert section['errors']
    assert section['report']['ready_for_script'] is False


def test_jleague_merges_two_identified_players_when_secondary_ranking_lacks_one():
    from lib.football_comparisons import merge_batches
    scope = {'competition': 'j1', 'season': 2025, 'phase': 'league'}
    def batch(metric, missing):
        return {'source': 'J.League', 'scope': scope, 'queries': [],
                'failed_metrics': {}, 'unresolved': ([{'name': 'B', 'metric': metric,
                   'reason': 'not_in_visible_ranking'}] if missing else []),
                'records': [{'entity_id': name, 'facts': [],
                             'statistics': {metric: 1 if name == 'A' or not missing else None}}
                            for name in ('A', 'B')]}
    merged = merge_batches([batch('goals', False), batch('assists', True)])
    assert merged['records'][0]['statistics'] == {'goals': 1, 'assists': 1}
    assert merged['records'][1]['statistics']['goals'] == 1
    assert merged['unresolved'][0]['metric'] == 'assists'
    assert merged['ready_for_script'] is False


def test_competition_and_player_use_distinct_phases():
    calls = []

    def execute(connector, args):
        calls.append(args)
        return {'success': False, 'error': 'Sin datos en la prueba'}

    source = {'connector': 'official_uefa_live',
              'inputs': {'competition': 'euro', 'edition': 2024, 'names': ['A', 'B'], 'phase': 'ALL'}}
    collect('competition', [source], execute)
    assert [args['phase'] for args in calls] == ['TOURNAMENT']
    calls.clear()
    result = collect('player', [source], execute)
    assert [args['phase'] for args in calls] == ['TOURNAMENT', 'QUALIFYING']
    assert [entry['qualification'] for entry in result['sections']] == [False, True]
    assert all(args['metrics'] == 'all' for args in calls)


def test_as_merges_batches_before_selection():
    tournament = ('ligamx', 2025, 'apertura')
    scope, urls = tournament_scope(tournament), ranking_urls(tournament)

    def execute(connector, args):
        metrics = args['metrics']
        assert len(metrics) <= 6
        queries = [{'url': urls[metric], 'retrieved_at': '2026-11-21'} for metric in metrics]
        rows = []
        for entity in ('a', 'b'):
            facts = [dict(metric=metric, value=1, entity_id=entity, scope=scope,
                          source_url=query['url'], retrieved_at=query['retrieved_at'])
                     for metric, query in zip(metrics, queries)]
            rows.append(dict(entity_id=entity, identity={'entity_id': entity, 'name': entity},
                             facts=facts, statistics=dict.fromkeys(metrics, 1)))
        return {'success': True, 'data': dict(source='AS', type='player_comparison', scope=scope,
                                              queries=queries, records=rows, failed_metrics={}, unresolved=[])}

    source = {'connector': 'ligamx_player_stats', 'inputs': {'season': 2025, 'names': ['a', 'b']}}
    result = collect('competition', [source], execute)
    assert len(result['standard_metrics']) == 54
    assert set(result['sections'][0]['display_metrics']) == set(RANKINGS)
    matrix = {row['metric']: row for row in result['sections'][0]['metric_matrix']}
    assert len(matrix) == 54
    assert matrix['goals']['display_metric'] == 'goals'
    assert matrix['goals']['values'][0]['source_url'] == urls['goals']
    assert matrix['expected_goals']['values'] == [None, None]
    assert matrix['expected_goals']['display_metric'] is None
    assert select(result, 0, ['goals', 'saves'])['metrics'] == ['goals', 'saves']
