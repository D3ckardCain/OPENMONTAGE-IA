"""Producer dispatch to real local sports tools, with a simulated official site.
No local LLM, model weights, paid service, public network or GPU is used.
"""
import json
import runpy
from pathlib import Path
import pytest
from lib import production_studio as studio,production_agent as agent
from tools.boxing import official_wba as wba
from tools.graphics.sports_card import SportsCard
from tools.tool_registry import ToolRegistry


@pytest.fixture
def producer(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    pid=studio.create_production({'title':'Postal de boxeo','brief':'Crear una postal del ranking WBA por nombre',
        'pipeline':'animated-explainer','language':'es','automatic':False})['project_id']
    registry=ToolRegistry();registry.register(wba.OfficialWBA());registry.register(SportsCard())
    worker=agent.LocalAgent(pid,registry=registry)
    return worker,studio.project_path(pid)


def test_producer_discovers_queries_and_designs_without_ids_or_retyping_stats(producer,monkeypatch):
    worker,path=producer
    source=worker.dispatch('sports_sources',{'sport':'boxing'})
    assert next(row for row in source['sources'] if row['id']=='wba')['connector']=='official_wba_live'
    available=worker.dispatch('list_tools',{'capability':'boxing_rankings'})
    assert [row['name'] for row in available]==['official_wba_live']
    page=runpy.run_path(str(Path(__file__).with_name('test_official_wba_live.py')))['page']()
    calls=[]
    def fetch():calls.append(1);return page,{'url':wba.URL,'retrieved_at':'2026-11-20T00:00:00Z'}
    monkeypatch.setattr(wba,'fetch',fetch)
    request={'name':'official_wba_live','inputs':{'action':'collectible_card','name':'Boxer 1'}}
    with pytest.raises(ValueError,match='skill'):worker.dispatch('execute_tool',request)
    assert not calls
    worker.instruction('skills/'+worker.manifest['stages'][0]['skill']+'.md')
    researched=worker.dispatch('execute_tool',request)
    assert researched['success'] and researched['artifacts']==[] and researched['cost_usd']==0
    report=researched['data']
    worker.dispatch('write_project_file',{'path':'assets/sports_report.json','content':json.dumps(report)})
    rendered=worker.dispatch('execute_tool',{'name':'sports_card_svg','inputs':{'report':report,'output_path':'assets/wba.png'}})
    assert rendered['success'],rendered['error']
    assert rendered['artifacts']==[str(path/'assets/wba.png')]
    assert (path/'assets/wba.png').is_file()
    from PIL import Image
    with Image.open(path/'assets/wba.png') as image:
        saved=json.loads(image.info['openmontage_evidence'])
        assert saved==report
    assert len(calls)==1


def test_producer_preserves_output_boundary_and_no_cached_source_fallback(producer,monkeypatch,tmp_path):
    worker,path=producer
    worker.instruction('skills/'+worker.manifest['stages'][0]['skill']+'.md')
    def fail():raise OSError('Fixture offline')
    monkeypatch.setattr(wba,'fetch',fail)
    result=worker.dispatch('execute_tool',{'name':'official_wba_live','inputs':{'action':'collectible_card','name':'Boxer 1'}})
    assert not result['success'] and not result['data']['stale_fallback']
    assert result['artifacts']==[]
    outside=tmp_path/'outside.png'
    with pytest.raises(ValueError):worker.dispatch('execute_tool',{'name':'sports_card_svg','inputs':{'report':{},'output_path':str(outside)}})
    assert not outside.exists()


def test_player_reports_use_the_same_54_fields_with_provider_evidence():
    from lib.football_statistics import add_standard_statistics
    from lib.sports_sources import FOOTBALL_STANDARD_METRICS

    fifa_source = {'url': 'https://fdh-api.fifa.com/fixture', 'retrieved_at': '2026-11-20'}
    fifa = {'source': 'FIFA', 'type': 'player_comparison', 'queries': [fifa_source],
            'records': [{'statistics': {'Goals': {'value': 0}, 'TimePlayed': {'value': 90}}}]}
    uefa_source = {'url': 'https://compstats.uefa.com/fixture', 'consultado_utc': '2026-11-20'}
    uefa = {'fuente': 'UEFA', 'tipo': 'comparativa_jugadores',
            'registros': [{'estadisticas': {'attempts_on_target': '3', 'matches_appearance': '12',
                                           'penalty_scored': '2', 'clearance_completed': '8'},
                           'fuente_estadisticas': uefa_source}]}
    jleague_url = 'https://www.jleague.jp/en/j1/stats/player/2025/score/search-list/'
    jleague = {'source': 'J.League', 'type': 'collectible_card', 'records': [{
        'statistics': {'goals': 7, 'assists': None},
        'facts': [{'metric': 'goals', 'value': 7, 'unit': 'goals', 'source_url': jleague_url,
                   'retrieved_at': '2026-11-20'}]}]}

    rows = [add_standard_statistics(report)[key][0]['standard_statistics']
            for report, key in [(fifa, 'records'), (uefa, 'registros'), (jleague, 'records')]]
    assert all(tuple(row) == FOOTBALL_STANDARD_METRICS and len(row) == 54 for row in rows)
    assert rows[0]['goals']['value'] == 0
    assert rows[0]['minutes_played'] is None
    assert rows[1]['shots_on_target']['source_metric'] == 'attempts_on_target'
    assert rows[1]['shots_on_target']['source_url'] == uefa_source['url']
    assert rows[1]['matches_played']['value'] == '12'
    assert rows[1]['penalty_goals']['source_metric'] == 'penalty_scored'
    assert rows[1]['clearances']['value'] == '8'
    assert rows[2]['goals']['source_url'] == jleague_url
    assert rows[2]['assists'] is None
