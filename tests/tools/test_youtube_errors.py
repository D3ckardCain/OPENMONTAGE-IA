import io
import json
import urllib.error
from unittest.mock import patch
import pytest
from tools.research.youtube_client import YouTube, YouTubeFailure
from tools.research.youtube_errors import classify_http_error, read_http_error
from tools.research.youtube_channel_search import YouTubeChannelSearch

@pytest.mark.parametrize('status,reason,expected',[
    (403,'quotaExceeded','QUOTA_EXCEEDED'),(403,'dailyLimitExceeded','QUOTA_EXCEEDED'),
    (403,'userRateLimitExceeded','RATE_LIMITED'),(429,'other','RATE_LIMITED'),
    (400,'keyInvalid','INVALID_KEY'),(400,'API_KEY_INVALID','INVALID_KEY'),
    (403,'accessNotConfigured','API_DISABLED'),(403,'SERVICE_DISABLED','API_DISABLED'),
    (403,'forbidden','ACCESS_DENIED'),(401,'other','ACCESS_DENIED'),
    (404,'channelNotFound','RESOURCE_UNAVAILABLE'),(503,'other','UPSTREAM_ERROR'),
    (400,'invalidFilters','UPSTREAM_REQUEST_INVALID')])
def test_known_reasons(status,reason,expected):
    assert classify_http_error(status,{'error':{'errors':[{'reason':reason}],'message':'secret'}})==expected

@pytest.mark.parametrize('status,payload,expected',[
    (400,{'error':{'details':[{'reason':'API_KEY_INVALID'}]}},'INVALID_KEY'),
    (403,{'error':{'message':'quotaExceeded secret'}},'ACCESS_DENIED'),
    (403,{'error':{'errors':'quotaExceeded'}},'ACCESS_DENIED'),
    (500,[], 'UPSTREAM_ERROR')])
def test_malformed_and_unknown_messages_not_guessed(status,payload,expected):
    assert classify_http_error(status,payload)==expected

def test_real_http_error_is_sanitized_and_closed():
    body=io.BytesIO(json.dumps({'error':{'errors':[{'reason':'quotaExceeded'}],
        'message':'secret-fixture'}}).encode())
    error=urllib.error.HTTPError('https://google.invalid?key=secret-fixture',403,'secret-fixture',{},body)
    with patch('urllib.request.urlopen',side_effect=error):
        with pytest.raises(YouTubeFailure) as exc:YouTube('secret-fixture').get('search')
    assert exc.value.code=='QUOTA_EXCEEDED' and not exc.value.retryable
    assert 'secret-fixture' not in str(exc.value)
    assert body.closed

@pytest.mark.parametrize('body',[b'not json',b'x'*65537])
def test_unparseable_error_body_uses_status(body):
    error=urllib.error.HTTPError('https://google.invalid',403,'secret',{},io.BytesIO(body))
    assert read_http_error(error)=='ACCESS_DENIED'

@pytest.mark.parametrize('error,expected',[(urllib.error.URLError('secret'),'NETWORK_ERROR'),
    (urllib.error.URLError(TimeoutError()),'TIMEOUT'),(TimeoutError('secret'),'TIMEOUT'),
    (ConnectionResetError('secret'),'NETWORK_ERROR')])
def test_network_errors_do_not_leak_urls(error,expected):
    with patch('urllib.request.urlopen',side_effect=error):
        with pytest.raises(YouTubeFailure) as exc:YouTube('secret').get('search')
    assert exc.value.code==expected and 'secret' not in str(exc.value)

def test_missing_key_is_not_misreported_as_no_results(monkeypatch):
    monkeypatch.delenv('YOUTUBE_API_KEY',raising=False)
    result=YouTubeChannelSearch().execute({'query':'animals'})
    assert not result.success and result.data['failure']['code']=='MISSING_KEY'
    assert 'results' not in result.data

def test_malformed_success_payload():
    class Reply:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def geturl(self):return 'https://www.googleapis.com/youtube/v3/search?key=fixture'
        def read(self,n):return b'not-json'
    with patch('urllib.request.urlopen',return_value=Reply()):
        with pytest.raises(YouTubeFailure) as exc:YouTube('fixture').get('search')
    assert exc.value.code=='INVALID_RESPONSE'
