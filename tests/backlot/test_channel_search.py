import pytest
from fastapi.testclient import TestClient
from tools.base_tool import ToolResult
from backlot.server import create_app

@pytest.fixture
def client():
    return TestClient(create_app(),base_url='http://127.0.0.1:4750')

def test_channel_screen_and_library_link(client):
    assert 'Buscador de canales' in client.get('/channels').text
    assert 'href="/channels"' in client.get('/').text
    assert client.get('/ui/channels.js').status_code==200

def test_status_does_not_disclose_key(client,monkeypatch):
    monkeypatch.setenv('YOUTUBE_API_KEY','private-fixture')
    response=client.get('/api/research/channels/status')
    assert response.json()=={'configured':True}
    assert response.headers['cache-control']=='no-store'
    assert 'private-fixture' not in response.text

def test_live_results_not_cached(client,monkeypatch):
    seen=[]
    def query(self,inputs):
        seen.append(inputs)
        return ToolResult(success=True,data={'results':[],'request':len(seen)})
    monkeypatch.setattr('backlot.channel_routes.YouTubeChannelSearch.execute',query)
    a=client.post('/api/research/channels',json={'query':'animals'})
    b=client.post('/api/research/channels',json={'query':'animals'})
    assert a.json()['request']!=b.json()['request']
    assert a.headers['cache-control']=='no-store'

@pytest.mark.parametrize('payload',[{'query':'animals','output_path':'a.json'},{'query':'a','pages':4},{'query':'a','filters':{'rpm':10}}])
def test_invalid_input_never_calls_tool(client,monkeypatch,payload):
    def fail(*args):raise AssertionError('not reached')
    monkeypatch.setattr('backlot.channel_routes.YouTubeChannelSearch.execute',fail)
    assert client.post('/api/research/channels',json=payload).status_code==422

def test_foreign_origin_rejected(client):
    assert client.post('/api/research/channels',json={'query':'a'},headers={'Origin':'https://evil.invalid'}).status_code==403

def test_failure_is_reported_without_stale_results(client,monkeypatch):
    monkeypatch.setattr('backlot.channel_routes.YouTubeChannelSearch.execute',lambda *args:ToolResult(success=False,error='CHANNEL_SEARCH_UNAVAILABLE'))
    response=client.post('/api/research/channels',json={'query':'a'})
    assert response.status_code==503

def test_query_body_limit(client):
    assert client.post('/api/research/channels',content='x'*16385,headers={'Content-Type':'application/json'}).status_code==413


def test_bad_channel_link_reports_input_error(client,monkeypatch):
    def fail():raise AssertionError('No client may be constructed')
    monkeypatch.setattr('tools.research.youtube_channel_search.ChannelSearch',fail)
    response=client.post('/api/research/channels',json={'query':'https://youtube.com/watch?v=abc'})
    assert response.status_code==422
    assert response.json()['error'].startswith('CHANNEL_INPUT_INVALID:')
