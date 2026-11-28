"""Credential and request-planner contracts, without live YouTube traffic."""
import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from tools.research import youtube_credentials as credentials
from tools.research.youtube_client import YouTube
from tools.research.youtube_query_plan import plan
from tools.research.youtube_research import YouTubeResearch
from tools.base_tool import ToolStatus


@pytest.fixture
def isolated(monkeypatch):
    monkeypatch.setattr(credentials,'SESSION_KEY',None)
    monkeypatch.delenv('YOUTUBE_API_KEY',raising=False)
    return TestClient(create_app(),base_url='http://127.0.0.1:4750')


def test_session_key_is_used_by_client_and_agent_but_never_returned(isolated):
    key='fixture_private_api_key_123456789'
    response=isolated.post('/api/research/channels/configuration',json={'api_key':key})
    assert response.status_code==200 and key not in response.text
    assert response.json()['session_key_persisted'] is False
    assert YouTube().key==key and YouTubeResearch().get_status()==ToolStatus.AVAILABLE
    assert isolated.get('/api/research/channels/status').json()=={'configured':True}
    status=isolated.get('/api/research/channels/configuration')
    assert key not in status.text and status.headers['cache-control']=='no-store'
    assert status.json()['key_verified'] is False


def test_clearing_session_keeps_environment_configuration(isolated,monkeypatch):
    monkeypatch.setenv('YOUTUBE_API_KEY','environment-key')
    credentials.configure({'api_key':'session_private_key_123456789'})
    result=credentials.configure({'api_key':''})
    assert result['source']=='environment' and YouTube().key=='environment-key'
    monkeypatch.delenv('YOUTUBE_API_KEY')
    assert not credentials.status()['configured']


@pytest.mark.parametrize('body',[{'api_key':'bad secret'},{'api_key':123},{'api_key':'x'*300},{'other':'never echo me'}])
def test_invalid_keys_are_rejected_without_echoing_values(isolated,body):
    response=isolated.post('/api/research/channels/configuration',json=body)
    assert response.status_code==400 and response.json()['detail']=='Formato de clave inválido'
    assert credentials.SESSION_KEY is None


def test_configuration_rejects_cross_origin_and_large_body(isolated):
    assert isolated.post('/api/research/channels/configuration',json={'api_key':''},headers={'Origin':'https://external.invalid'}).status_code==403
    assert isolated.post('/api/research/channels/configuration',content='x'*2049,headers={'Content-Type':'application/json'}).status_code==413


def test_planner_does_not_need_key_or_network_and_deduplicates_identity(isolated,monkeypatch):
    def forbidden(*a,**k):raise AssertionError('No API requests in planning')
    monkeypatch.setattr(YouTube,'get',forbidden)
    value=plan({'queries':['@example','https://www.youtube.com/@example','animals'],'pages':2,
        'filters':{'published_within':'month','discovery_mode':'recent_publications'}})
    assert value['unique_queries']==2
    assert value['maximum_requests_before_budget']=={'search':2,'channels':3,'playlistItems':101,'videos':103}
    assert value['remaining_project_quota'] is None and value['network_requests_started']==0
    assert isolated.post('/api/research/channels/plan',json={'queries':['@example']}).status_code==200
    assert isolated.post('/api/research/channels/plan',json={'queries':['https://youtube.com/watch?v=abcdefghijk']}).status_code==422


def test_default_channel_screen_uses_recent_publications(isolated):
    html=isolated.get('/channels').text
    assert '<option value="recent_publications" selected>' in html
    assert '<option value="matching_publication_views" selected>' in html
    assert '<option value="month" selected>' in html
    assert 'type="password"' in html
