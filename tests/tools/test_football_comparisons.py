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
