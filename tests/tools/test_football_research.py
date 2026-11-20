from types import SimpleNamespace
import pytest
from lib import football_research as football


def test_schema_does_not_access_network(monkeypatch):
    monkeypatch.setattr(football.OfficialUEFA,'__init__',lambda self:pytest.fail('Schema must not query'))
    report=football.schema()
    assert 'champions' in report['competitions']
    assert next(item for item in report['actions'] if item['name']=='definitions')['required']==['competition']
    assert report['persistent_statistics'] is False


def test_fresh_results_and_failures_do_not_reuse_data(monkeypatch):
    calls=[]
    class Tool:
        def execute(self,data):
            calls.append(data)
            return SimpleNamespace(success=len(calls)==1,data={'fixture':'new data'},error=None if len(calls)==1 else 'UEFA unavailable')
    monkeypatch.setattr(football,'OfficialUEFA',Tool)
    assert football.query({'action':'definitions','competition':'champions'})['data']=={'fixture':'new data'}
    failed=football.query({'action':'definitions','competition':'champions'})
    assert failed['success'] is False and failed['data'] is None and failed['stale_fallback'] is False
    assert len(calls)==2


def test_busy_query_does_not_start_another_request(monkeypatch):
    with football.LOCK:
        with pytest.raises(ValueError,match='activa'):football.query({})


def test_football_routes_use_existing_schema_validation(monkeypatch):
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    client=TestClient(create_app(),base_url='http://127.0.0.1:4750')
    assert client.get('/api/studio/football/schema').status_code==200
    reply=client.post('/api/studio/football/query',json={'action':'definitions','competition':'champions','output_path':'stats.json'})
    assert reply.status_code==200 and reply.json()['success'] is False
    assert reply.json()['data'] is None


def test_entity_choices_preserve_different_official_action_contracts():
    actions={item['name']:item for item in football.schema()['actions']}
    assert actions['ranking']['choices']['entity']==['player','team']
    assert actions['historical']['choices']['entity']==['players','teams']


def test_followups_use_explicit_ids_and_preserve_player_scope():
    data={'fuente':'UEFA','competicion':'champions','tipo':'ranking','alcance':{'entidad':'player','seasonYear':2027,'metricas':['goals'],'phase':'TOURNAMENT'},'registros':[{'id':'123','nombre':'Name is not used'}]}
    prepared=football.followups(data)
    assert prepared[0]['query']=={'action':'player','competition':'champions','player_id':'123','edition':2027,'metrics':['goals'],'phase':'TOURNAMENT'}
    assert football.followups({**data,'registros':[{'nombre':'No official ID'}]})==[]
    assert football.followups({**data,'tipo':'unknown'})==[]


def test_team_and_match_followups_do_not_claim_historical_team_profile():
    team={'fuente':'UEFA','competicion':'champions','tipo':'equipos','registros':[{'id':456}]}
    result=football.followups(team)
    assert result[0]['query']=={'action':'team','competition':'champions','team_id':'456'}
    assert 'actual' in result[0]['label']
    match={**team,'tipo':'partidos_por_union_de_fases'}
    assert football.followups(match)[0]['query']['match_id']=='456'
    assert football.followups({**team,'competicion':'unsupported'})==[]
