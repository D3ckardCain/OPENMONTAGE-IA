from lib.sports_sources import catalog


def test_regions_and_sports_are_explicit():
    rows=catalog()['sources']
    assert {x['sport'] for x in rows} == {'football','boxing','baseball'}
    assert {'asia','africa','arab','americas','europe'} <= {x['region'] for x in rows}
    assert len({x['id'] for x in rows}) == len(rows)
    assert all(x['url'].startswith('https://') for x in rows)


def test_pending_sources_do_not_claim_statistics_or_coverage():
    result=catalog('football','arab')
    assert 'saudi' in {x['id'] for x in result['sources']}
    assert all(not x['coverage_verified'] for x in result['sources'])
    assert not result['statistics_included']
    assert not result['complete_global_coverage']
    assert all(x['connector'] is None for x in result['sources'] if x['region']=='arab' and x['id']!='saudi')
    assert next(x for x in result['sources'] if x['id']=='saudi')['status']=='implemented_requires_live_check'


def test_every_listed_football_competition_has_the_same_metric_contract_and_honest_adapter_capability():
    from lib.sports_sources import FOOTBALL_STANDARD_METRICS
    result = catalog('football')
    assert result['football_standard']['metrics'] == list(FOOTBALL_STANDARD_METRICS)
    rows = {row['id']: row for row in result['sources']}
    assert all(row['metric_capability']['scope'] == 'configured_adapter_fields_not_verified_player_values'
               and not row['coverage_verified'] for row in rows.values())
    assert rows['uae']['metric_capability']['standard_metrics'] == []
    assert rows['kleague']['status'] == 'source_inspection_only'
    assert rows['kleague']['connector'] is None and not rows['kleague']['coverage_verified']
    assert 'authKey' in rows['kleague']['integration_note']
    assert rows['ofc_nations_cup']['metric_capability']['standard_metrics'] == ['goals']
    assert rows['fifa']['metric_capability']['dynamic_metric_discovery']
    assert rows['uefa']['metric_capability']['dynamic_metric_discovery']
    assert {'goals', 'assists', 'saves'} <= set(rows['premier']['metric_capability']['standard_metrics'])
    assert 'expected_goals_excl_pk' in rows['jleague']['metric_capability']['additional_configured_metrics']


def test_copy_and_validation():
    import pytest
    first=catalog(); first['sources'][0]['name']='changed'
    assert catalog()['sources'][0]['name']!='changed'
    with pytest.raises(ValueError):catalog('basketball')
    with pytest.raises(ValueError):catalog(region='unknown')
