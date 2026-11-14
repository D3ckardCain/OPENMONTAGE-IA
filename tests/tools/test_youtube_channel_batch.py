import pytest
from tools.research.youtube_channel_batch import YouTubeChannelBatch
from tools.research.youtube_channels import ChannelSearch, YouTubeFailure
from tests.tools.test_youtube_channels import A,B,channel


def client_factory(monkeypatch,fail=None):
    calls=[]
    current={'query':None,'round':0}
    def api(resource,params):
        calls.append((resource,dict(params)))
        if resource=='search':
            current['query']=params['q'];current['round']+=1
            if fail and params['q']=='second':raise YouTubeFailure(fail)
            return {'items':[{'id':{'channelId':A,'kind':'youtube#channel'}},
                             {'id':{'channelId':B,'kind':'youtube#channel'}}]}
        if resource=='channels':
            # Later response lowers A's counter: keep that actual value, not max.
            return {'items':[channel(A,300 if current['round']==1 else 100,1000),channel(B,200,1)]}
        raise AssertionError(resource)
    monkeypatch.setattr('tools.research.youtube_channel_batch.ChannelSearch',lambda:ChannelSearch('fixture',api))
    return calls


def test_batch_deduplicates_and_keeps_latest_public_counters(monkeypatch):
    calls=client_factory(monkeypatch)
    result=YouTubeChannelBatch().execute({'queries':['first',' second ','first']})
    assert result.success and result.data['complete'] and not result.data['partial']
    assert result.data['queries']==['first','second']
    assert [row['id'] for row in result.data['results']]==[B,A]
    assert result.data['results'][1]['viewCount']==100
    assert result.data['results'][1]['matched_queries']==['first','second']
    assert len(calls)==4 and sum(result.data['requests'].values())==4

@pytest.mark.parametrize('failure',['QUOTA_EXCEEDED','INVALID_KEY','NETWORK_ERROR','RATE_LIMITED'])
def test_failure_stops_subsequent_topics_without_retry(monkeypatch,failure):
    calls=client_factory(monkeypatch,fail=failure)
    result=YouTubeChannelBatch().execute({'queries':['first','second','third']})
    assert not result.success and result.data['partial'] and not result.data['complete']
    assert result.data['failure']['code']==failure
    assert result.data['pending_queries']==['second','third']
    assert result.data['failed_query']=='second'
    assert [params['q'] for resource,params in calls if resource=='search']==['first','second']
    assert result.data['results'][0]['matched_queries']==['first']

@pytest.mark.parametrize('limit,complete,partial',[(1,0,False),(2,1,True),(3,1,True),(4,2,False)])
def test_request_budget_is_enforced_before_each_api_call(monkeypatch,limit,complete,partial):
    calls=client_factory(monkeypatch)
    result=YouTubeChannelBatch().execute({'queries':['first','second'],'max_requests':limit})
    assert len(calls)==limit
    assert len(result.data['completed_queries'])==complete
    assert result.data['partial']==partial
    assert result.success==(limit==4)
    if limit<4:assert result.data['failure']['code']=='REQUEST_BUDGET_EXCEEDED'


def test_validate_entire_batch_before_requesting(monkeypatch):
    def fail():raise AssertionError('No requests allowed')
    monkeypatch.setattr('tools.research.youtube_channel_batch.ChannelSearch',fail)
    result=YouTubeChannelBatch().execute({'queries':['valid','https://evil.invalid/@x']})
    assert not result.success and result.data=={}


def test_constructor_error_leaves_every_topic_pending(monkeypatch):
    def fail():raise YouTubeFailure('MISSING_KEY')
    monkeypatch.setattr('tools.research.youtube_channel_batch.ChannelSearch',fail)
    result=YouTubeChannelBatch().execute({'queries':['first','second']})
    assert not result.success and not result.data['partial']
    assert not result.data['results'] and result.data['pending_queries']==['first','second']


def test_agent_can_discover_batch_retrieval():
    from tools.tool_registry import ToolRegistry
    from tools.research import youtube_channel_batch
    assert 'youtube_channel_batch' in ToolRegistry().register_module(youtube_channel_batch)
