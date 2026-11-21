import pytest
from tools.football import official_spl_status as spl
from tools.tool_registry import ToolRegistry
from tools.base_tool import _is_cacheable


def page(extra=''):
    return '<h2>Stats Hub</h2><h2>PLAYER STATISTICS</h2>'+extra


def test_explicit_unavailability_is_not_zero_or_global_no_data():
    r=spl.inspect(page('<p>Player statistics are currently unavailable for the selected season.</p>'),{'url':spl.URL,'retrieved_at':'2026-11-20'})
    assert r['statistics_status']=='explicitly_unavailable_for_selected_season'
    assert r['statistics'] is None and not r['ready_for_script']


def test_script_translation_is_not_mistaken_for_visible_failure():
    r=spl.inspect(page('<script>Player statistics are currently unavailable for the selected season.</script>'),{'url':spl.URL})
    assert r['statistics_status']=='extraction_not_implemented'


def test_season_references_do_not_claim_year_or_statistics_coverage():
    r=spl.inspect(page('<script>spl::Football_Season::'+'a'*32+'</script>'),{'url':spl.URL})
    assert len(r['season_ids_referenced'])==1
    assert not r['season_year_mapping_verified'] and r['statistics'] is None
    with pytest.raises(ValueError):spl.inspect('<h1>Access denied</h1>',{})


def test_discovery_validation_and_no_stale_fallback(monkeypatch):
    assert 'official_spl_source_status' in ToolRegistry().register_module(spl)
    calls=[]
    def fetch():calls.append(1);return page(),{'url':spl.URL}
    monkeypatch.setattr(spl,'fetch',fetch)
    t=spl.OfficialSPLStatus()
    assert not _is_cacheable(t,{'output_path':'x'})
    assert t.execute({}).success and t.execute({}).success and len(calls)==2
    assert not t.execute({'season':2026}).success
    def fail():raise OSError('offline')
    monkeypatch.setattr(spl,'fetch',fail)
    r=t.execute({});assert not r.success and not r.data['stale_fallback']
