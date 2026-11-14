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

@pytest.mark.parametrize('age,expected',[(10,True),(89,True),(91,False),(365*5,False)])
def test_many_views_with_maximum_channel_age(age,expected):
    ch=channel(A,1000000)
    ch['snippet']['publishedAt']=(datetime.now(timezone.utc)-timedelta(days=age)).isoformat()
    result=search(API([ch]),min_views=1000000,max_channel_age_days=90)
    assert bool(result['results'])==expected
    if not expected:assert result['excluded']=={'channel_too_old':1}

@pytest.mark.parametrize('date',[None,'invalid','2026-01-01T00:00:00',
    (datetime.now(timezone.utc)+timedelta(days=1)).isoformat()])
def test_unknown_or_invalid_creation_does_not_pass_age_filter(date):
    ch=channel(A,1000000);ch['snippet']['publishedAt']=date
    result=search(API([ch]),max_channel_age_days=90)
    assert not result['results']
    assert result['excluded']=={'channel_creation_unknown_or_invalid':1}

def test_channel_age_does_not_require_video_requests():
    api=API([channel(A,1000000)])
    api.channels[0]['snippet']['publishedAt']=datetime.now(timezone.utc).isoformat()
    assert search(api,max_channel_age_days=90)['results']
    assert [resource for resource,params in api.calls]==['search','channels']

@pytest.mark.parametrize('age',[0,-1,True,36501])
def test_invalid_age_limits_rejected_before_requests(age):
    api=API([])
    with pytest.raises(Unavailable):search(api,max_channel_age_days=age)
    assert not api.calls


def test_age_filter_also_limits_candidate_discovery():
    api=API([])
    search(api,max_channel_age_days=90)
    resource,params=api.calls[0]
    assert resource=='search' and params['type']=='channel'
    start=datetime.fromisoformat(params['publishedAfter'])
    end=datetime.fromisoformat(params['publishedBefore'])
    assert end-start==timedelta(days=90)


def test_repeated_recent_success_requires_distinct_matching_publications():
    publications=[video('aaaaaaaaaaa',views=120000),video('bbbbbbbbbbb',views=200000),
                  video('ccccccccccc',views=90000),video('ddddddddddd',age=40,views=900000)]
    api=API([channel(A,2000000)],{A:publications})
    result=search(api,min_publication_views=100000,published_within='month',min_matching_publications=2)
    review=result['results'][0]['content_review']
    assert review['matched']==2 and review['minimum_required']==2
    assert [v['id'] for v in review['matching_publications']]==['aaaaaaaaaaa','bbbbbbbbbbb']
    assert review['matching_publications'][0]['viewCount']==120000
    assert review['complete_history'] is False
    rejected=search(api,min_publication_views=100000,published_within='month',min_matching_publications=3)
    assert rejected['results']==[]
    assert rejected['excluded']=={'insufficient_matching_publications':1}


def test_repeated_response_records_cannot_satisfy_minimum():
    api=API([channel(A,100)],{A:[video('aaaaaaaaaaa'),video('aaaaaaaaaaa')]})
    result=search(api,min_matching_publications=2)
    assert not result['results']
    assert result['excluded']=={'insufficient_matching_publications':1}


@pytest.mark.parametrize('minimum,sample',[(0,10),(True,10),(21,20),(6,5)])
def test_invalid_matching_minimum_never_queries(minimum,sample):
    api=API([])
    with pytest.raises(Unavailable):search(api,min_matching_publications=minimum,sample_size=sample)
    assert not api.calls


def test_matching_minimum_validated_by_both_agent_tools_before_client(monkeypatch):
    from tools.research.youtube_channel_batch import YouTubeChannelBatch
    def fail():raise AssertionError('client must not be created')
    monkeypatch.setattr('tools.research.youtube_channel_search.ChannelSearch',fail)
    monkeypatch.setattr('tools.research.youtube_channel_batch.ChannelSearch',fail)
    filters={'min_matching_publications':6,'sample_size':5}
    assert not YouTubeChannelSearch().execute({'query':'animals','filters':filters}).success
    assert not YouTubeChannelBatch().execute({'queries':['animals'],'filters':filters}).success


def test_recent_matching_views_can_out_rank_lifetime_channel_views():
    api=API([channel(A,90000000,9000),channel(B,1000000,10)],{
        A:[video('aaaaaaaaaaa',cid=A,views=10000),video('ccccccccccc',cid=A,age=60,views=80000000)],
        B:[video('bbbbbbbbbbb',cid=B,views=400000)]})
    result=search(api,published_within='month',sort_by='matching_publication_views')
    assert [r['id'] for r in result['results']]==[B,A]
    assert result['results'][0]['content_review']['matching_publication_views_sum']==400000
    assert result['order']==['matching_publication_views_sum_desc','subscriberCount_public_rounded_desc']


def test_unknown_matching_views_do_not_become_zero_or_partial_sum():
    missing=video('aaaaaaaaaaa');missing['statistics']={}
    api=API([channel(A,1000,999),channel(B,100,1)],{
        A:[missing,video('ccccccccccc',views=90000)],B:[video('bbbbbbbbbbb',cid=B,views=0)]})
    result=search(api,published_within='month',sort_by='matching_publication_views')
    assert [r['id'] for r in result['results']]==[B,A]
    assert result['results'][1]['content_review']['matching_publication_views_sum'] is None


@pytest.mark.parametrize('filters',[{'sort_by':'rpm'},{'sort_by':'matching_publication_views'}])
def test_invalid_or_undated_recent_order_rejected_before_network(filters):
    api=API([])
    with pytest.raises(Unavailable):search(api,**filters)
    assert not api.calls
