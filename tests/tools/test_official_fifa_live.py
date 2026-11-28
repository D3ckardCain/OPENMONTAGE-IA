from copy import deepcopy
import pytest
from tools.football.fifa_live import FIFA, Transport
from tools.football.official_fifa import OfficialFIFA
from tools.tool_registry import ToolRegistry
from tools.base_tool import _is_cacheable


class Fake:
    def __init__(self):
        self.calls=[]
        self.season={'IdSeason':'22','IdCompetition':'17','Properties':{'IdIFES':'99'}}
        self.stats={'10':[['Goals',0,True],['Assists',2,False]],'20':[['Goals',1,True]]}
        self.editions={'Results':[deepcopy(self.season)],'ContinuationToken':None}
    def get(self,url):
        self.calls.append(url)
        data=self.editions if '/seasons?' in url else self.season if '/seasons/' in url else self.stats
        return deepcopy(data),{'url':url,'retrieved_at':'2026-11-20T00:00:00Z'}


def test_registry_and_no_persistent_cache():
    from tools.football import official_fifa
    assert 'official_fifa_live' in ToolRegistry().register_module(official_fifa)
    tool=OfficialFIFA()
    assert not _is_cacheable(tool,{'output_path':'x.json'})
    assert tool.estimate_cost({})==0
    assert tool.resource_profile.network_required


def test_uses_verified_season_mapping_and_preserves_zero_missing_and_flag():
    fake=Fake(); client=FIFA(fake)
    report=client.player_statistics('17','22',['10','20'],['Goals','Assists'])
    assert '/season/99/players.json' in fake.calls[-1]
    a,b=report['records']
    assert a['statistics']['Goals']['value']==0
    assert a['statistics']['Assists']['source_flag'] is False
    assert b['statistics']['Assists']['value'] is None
    assert b['missing_metrics']==['Assists']
    assert a['name'] is None
    assert len(report['queries'])==2
    assert report['scope']['season_id']=='22'


def test_each_call_is_fresh():
    fake=Fake(); client=FIFA(fake)
    client.player_statistics('17','22',['10']);fake.stats['10'][0][1]=3
    assert client.player_statistics('17','22',['10'])['records'][0]['statistics']['Goals']['value']==3
    assert len(fake.calls)==4


@pytest.mark.parametrize('mutation',[
    lambda f:f.season.update(IdCompetition='18'),
    lambda f:f.season.update(Properties={}),
    lambda f:f.stats.update({'10':[['Goals',1,True],['Goals',2,True]]}),
    lambda f:f.stats.update({'10':[['Goals',float('nan'),True]]}),
    lambda f:f.stats.update({'10':[['Goals',True,True]]}),
    lambda f:f.stats.update({'10':[['Goals',1,'true']]}),
])
def test_schema_drift_and_scope_mismatch_fail_closed(mutation):
    fake=Fake();mutation(fake)
    with pytest.raises(ValueError): FIFA(fake).player_statistics('17','22',['10'])


def test_missing_player_never_becomes_zero():
    with pytest.raises(ValueError): FIFA(Fake()).player_statistics('17','22',['999'])


def test_seasons_reject_incomplete_and_wrong_competition():
    fake=Fake();fake.editions['ContinuationToken']='next'
    with pytest.raises(ValueError): FIFA(fake).seasons('17')
    fake.editions['ContinuationToken']=None
    fake.editions['Results'][0]['IdCompetition']='18'
    with pytest.raises(ValueError): FIFA(fake).seasons('17')


def test_tool_rejects_extra_paths_and_inapplicable_fields_before_network():
    tool=OfficialFIFA();fake=Fake();tool.client=FIFA(fake)
    for extra in ({'output_path':'stats.json'},{'season_id':'22'},{'metrics':['Goals']}):
        assert not tool.execute({'action':'seasons','competition_id':'17',**extra}).success
    assert not fake.calls


def test_failure_has_no_stale_fallback():
    tool=OfficialFIFA()
    class Broken:
        def seasons(self,**kwargs):raise OSError('network down')
    tool.client=Broken();r=tool.execute({'action':'seasons','competition_id':'17'})
    assert not r.success
    assert r.data=={'fresh_query_failed':True,'stale_fallback':False}


@pytest.mark.parametrize('url',['http://api.fifa.com/x','https://evil.test/x','https://api.fifa.com:443/x','https://user@api.fifa.com/x'])
def test_transport_rejects_unexpected_urls_before_network(url):
    with pytest.raises(ValueError):Transport().get(url)
