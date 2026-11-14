import pytest
from tools.research.channel_identity import parse_channel_query, InvalidChannelQuery
from tools.research.youtube_channels import ChannelSearch, ChannelFilters
from tools.research.youtube_channel_search import YouTubeChannelSearch
from tests.tools.test_youtube_channels import A, channel, video

@pytest.mark.parametrize('value,expected',[
    ('animales bonitos',('keywords','animales bonitos')),
    ('  @example  ',('handle','example')),('@한국어채널',('handle','한국어채널')),
    (A,('id',A)),('https://www.youtube.com/@example/videos?view=0',('handle','example')),
    ('youtube.com/@example',('handle','example')),('https://m.youtube.com/@example/shorts',('handle','example')),
    ('https://youtube.com/channel/'+A+'/about',('id',A)),
    ('https://youtube.com/user/LegacyName/videos',('username','LegacyName')),
    ('https://youtube.com/@%ED%95%9C%EA%B5%AD',('handle','한국')),
])
def test_accepted_identities(value,expected):
    assert parse_channel_query(value)==expected

@pytest.mark.parametrize('value',['','   ','@','@bad name','https://evil.invalid/@name',
    'https://youtube.com.evil.invalid/@name','https://youtube.com@evil.invalid/@name',
    'https://evil@youtube.com/@name','https://youtube.com:443/@name',
    'https://youtube.com/watch?v=abc','https://youtu.be/video',
    'https://youtube.com/c/custom','https://youtube.com/@bad%2Fname',
    'https://youtube.com/@bad%ZZ','file:///tmp/private','//youtube.com/@name',
    'https://youtube.com/channel/invalid','@bad\x00name'])
def test_bad_identities_rejected(value):
    with pytest.raises(InvalidChannelQuery):parse_channel_query(value)

@pytest.mark.parametrize('query,key,value',[
    ('@example','forHandle','example'),(A,'id',A),
    ('https://youtube.com/user/Legacy','forUsername','Legacy')])
def test_exact_lookup_skips_search_bucket(query,key,value):
    calls=[]
    def api(resource,params):
        calls.append((resource,params))
        assert resource=='channels' and params[key]==value
        return {'items':[channel(A,100)]}
    result=ChannelSearch('fixture',api).search_channels(query)
    assert len(calls)==1 and result['results'][0]['id']==A
    assert not result['scope']['pages_applicable']

def test_filters_still_apply_to_exact_lookup():
    def api(resource,params):return {'items':[channel(A,100)]}
    result=ChannelSearch('fixture',api).search_channels('@example',ChannelFilters(min_views=101))
    assert result['results']==[] and result['excluded']=={'channel_views':1}

def test_missing_handle_does_not_fall_back_to_similar_channel():
    def api(resource,params):
        assert resource=='channels'
        return {'items':[]}
    assert ChannelSearch('fixture',api).search_channels('@missing')['results']==[]

def test_invalid_url_validated_before_key_or_network(monkeypatch):
    def fail():raise AssertionError('should not construct a client')
    monkeypatch.setattr('tools.research.youtube_channel_search.ChannelSearch',fail)
    result=YouTubeChannelSearch().execute({'query':'https://evil.invalid/@x'})
    assert not result.success and result.error.startswith('CHANNEL_INPUT_INVALID:')
