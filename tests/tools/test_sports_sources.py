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
    assert all(x['connector'] is None for x in result['sources'] if x['region']=='arab')


def test_copy_and_validation():
    import pytest
    first=catalog(); first['sources'][0]['name']='changed'
    assert catalog()['sources'][0]['name']!='changed'
    with pytest.raises(ValueError):catalog('basketball')
    with pytest.raises(ValueError):catalog(region='unknown')
