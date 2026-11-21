from lib.football_comparisons import collect, select
from tools.football.ligamx import RANKINGS, ranking_urls, tournament_scope


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
    assert select(result, 0, ['goals', 'saves'])['metrics'] == ['goals', 'saves']
