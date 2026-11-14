from datetime import datetime, timezone, timedelta
import pytest
from tools.research.youtube_channels import ChannelSearch, ChannelFilters, Unavailable
from tools.research.youtube_channel_search import YouTubeChannelSearch

A,B,C=['UC'+letter*22 for letter in 'abc']
def channel(cid,views,subs=100):
    return {'id':cid,'snippet':{'title':cid,'country':'MX'},'statistics':{
        'viewCount':str(views),'subscriberCount':str(subs),'videoCount':'30'},
        'contentDetails':{'relatedPlaylists':{'uploads':cid+'-uploads'}}}

def video(vid,cid=A,lang='es',seconds='PT10M',age=1,views=1000):
    return {'id':vid,'snippet':{'channelId':cid,'defaultAudioLanguage':lang,
        'publishedAt':(datetime.now(timezone.utc)-timedelta(days=age)).isoformat()},
        'contentDetails':{'duration':seconds},'statistics':{'viewCount':str(views)}}

class API:
    def __init__(self,channels,publications=None):
        self.channels=channels;self.publications=publications or {};self.calls=[]
    def __call__(self,resource,params):
        self.calls.append((resource,params))
        if resource=='search':
            assert params['type']=='channel'
            return {'items':[{'id':{'channelId':ch['id'],'kind':'youtube#channel'}} for ch in self.channels]
                    +[{'id':{'videoId':'ignored','kind':'youtube#video'}}]}
        if resource=='channels':return {'items':self.channels}
        if resource=='playlistItems':
            cid=params['playlistId'].split('-uploads')[0]
            return {'items':[{'contentDetails':{'videoId':v['id']}} for v in self.publications.get(cid,[])]}
        if resource=='videos':
            ids=params['id'].split(',')
            return {'items':[v for group in self.publications.values() for v in group if v['id'] in ids]}
        raise AssertionError(resource)

def search(api,**filters):
    return ChannelSearch('fixture',api).search_channels('animales',ChannelFilters(**filters))

def test_views_first_subscribers_only_break_ties():
    result=search(API([channel(A,100,999),channel(B,200,1),channel(C,100,1000)]))
    assert [c['id'] for c in result['results']]==[B,C,A]
    assert result['result_type']=='channels'
    assert result['scope']['candidate_channels']==3
    assert all(c['viral_now'] is None and c['rpm'] is None for c in result['results'])

def test_no_upload_queries_unless_content_filters_are_set():
    api=API([channel(A,0,0)])
    result=search(api)
    assert result['results'][0]['viewCount']==0
    assert [call[0] for call in api.calls]==['search','channels']

def test_hidden_subscribers_are_unknown_not_zero():
    ch=channel(A,100);ch['statistics']['hiddenSubscriberCount']=True
    assert search(API([ch]))['results'][0]['subscriberCount_public_rounded'] is None
    assert search(API([ch]),min_subscribers=0)['results']==[]

def test_missing_views_are_not_sorted_as_zero():
    ch=channel(A,1);del ch['statistics']['viewCount']
    assert search(API([ch]))['excluded']=={'views_unknown':1}

@pytest.mark.parametrize('filters',[{'min_views':101},{'max_views':99},{'min_subscribers':101},
    {'max_subscribers':99},{'country':'US'}])
def test_channel_stat_filters(filters):
    assert search(API([channel(A,100,100)]),**filters)['results']==[]

def test_all_content_filters_must_match_one_publication():
    api=API([channel(A,100)],{A:[video('v1',lang='en'),video('v2',lang='es',seconds='PT30M')]})
    assert search(api,language='es',content_type='medium')['results']==[]

@pytest.mark.parametrize('filters',[{'language':'es'},{'min_minutes':4,'max_minutes':20},
    {'content_type':'medium'},{'published_within':'week'},{'min_publication_views':1000}])
def test_recent_sample_filters_return_channels(filters):
    api=API([channel(A,100)],{A:[video('v1')]})
    row=search(api,**filters)['results'][0]
    assert row['id']==A and row['content_review']['matched']==1
    assert 'videos' not in row and not row['content_review']['complete_history']

def test_language_unknown_and_old_content_rejected():
    assert not search(API([channel(A,100)],{A:[video('v1',lang=None)]}),language='es')['results']
    assert not search(API([channel(A,100)],{A:[video('v1',age=8)]}),published_within='week')['results']

@pytest.mark.parametrize('kind,seconds,expected',[
    ('short_candidate','PT3M',True),('short_candidate','PT3M1S',False),
    ('over_3m','PT3M',False),('medium','PT4M',True),('medium','PT20M',True),
    ('long','PT20M',False),('long','PT20M1S',True)])
def test_duration_boundaries(kind,seconds,expected):
    result=search(API([channel(A,100)],{A:[video('v1',seconds=seconds)]}),content_type=kind)
    assert bool(result['results'])==expected
    if expected:assert result['results'][0]['content_review']['shorts_confirmed'] is None

@pytest.mark.parametrize('filters',[{'min_views':True},{'min_views':2,'max_views':1},
    {'sample_size':21},{'language':'??'},{'country':'MEX'},{'published_within':'future'},
    {'min_minutes':-1}])
def test_bad_filters_fail_before_network(filters):
    api=API([])
    with pytest.raises(Unavailable):search(api,**filters)
    assert not api.calls

def test_duplicate_channels_deduplicated():
    result=search(API([channel(A,100),channel(A,100)]))
    assert len(result['results'])==1

def test_api_failure_no_stale_results(monkeypatch):
    def fail(*args,**kwargs):raise RuntimeError('secret-fixture')
    monkeypatch.setattr('tools.research.youtube_channel_search.ChannelSearch',fail)
    result=YouTubeChannelSearch().execute({'query':'animals'})
    assert not result.success and result.data['stale_fallback'] is False
    assert 'secret-fixture' not in result.error

def test_agent_adapter_is_discoverable():
    from tools.tool_registry import ToolRegistry
    from tools.research import youtube_channel_search
    assert 'youtube_channel_search' in ToolRegistry().register_module(youtube_channel_search)
