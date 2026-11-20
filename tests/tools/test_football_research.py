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
