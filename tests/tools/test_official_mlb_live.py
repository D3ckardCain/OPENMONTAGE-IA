from copy import deepcopy
import pytest
from tools.base_tool import _is_cacheable
from tools.baseball.official_mlb import MLB,OfficialMLB,Transport
from tools.tool_registry import ToolRegistry


class Feed:
    def __init__(self):self.calls=[];self.bad=None
    def get(self,path,params):
        self.calls.append((path,params))
        if path=='people/search':
            pid=1 if params['names']=='One' else 2
            rows=[{'id':pid,'fullName':params['names'],'lastName':params['names']}]
            if self.bad=='ambiguous':rows.append({'id':3,'fullName':params['names']})
            data={'people':rows}
        else:
            pid=int(path.split('/')[1]);name='One' if pid==1 else 'Two'
            split={'season':str(params['season']),'gameType':'R','sport':{'id':1},'player':{'id':pid,'fullName':name},'stat':{'homeRuns':0,'avg':'.310','inningsPitched':'4.1'}}
            if self.bad=='scope':split['season']='2023'
            if self.bad=='nan':split['stat']['homeRuns']=float('nan')
            if self.bad=='bool':split['stat']['homeRuns']=True
            splits=[] if self.bad=='empty' else [split,deepcopy(split)] if self.bad=='multi' else [split]
            data={'stats':[{'type':{'displayName':'season'},'group':{'displayName':params['group']},'splits':splits}]}
        return deepcopy(data),{'url':'https://statsapi.mlb.com/api/v1/'+path,'retrieved_at':'2026-11-20T00:00:00Z'}


def test_discovery_network_and_no_cache():
    from tools.baseball import official_mlb
    assert 'official_mlb_live' in ToolRegistry().register_module(official_mlb)
    t=OfficialMLB();assert not _is_cacheable(t,{'output_path':'x'})
    assert t.estimate_cost({})==0 and t.resource_profile.network_required


def test_name_comparison_preserves_zero_string_rates_and_missing():
    f=Feed();r=MLB(f).compare_players(['One','Two'],2024,'hitting',['homeRuns','avg','rbi'])
    assert not r['ready_for_script']
    a=r['records'][0]
    assert a['statistics']=={'homeRuns':0,'avg':'.310','rbi':None}
    assert a['missing_metrics']==['rbi']
    assert len(r['queries'])==4
    assert all(params.get('gameType')=='R' for p,params in f.calls if p.endswith('/stats'))


def test_pitching_innings_remain_original_string_and_queries_are_fresh():
    f=Feed();c=MLB(f)
    for _ in range(2):
        assert c.player_statistics('1',2024,'pitching',['inningsPitched'])['records'][0]['statistics']['inningsPitched']=='4.1'
    assert len(f.calls)==2


@pytest.mark.parametrize('bad',['scope','nan','bool','empty','multi'])
def test_invalid_or_multiteam_statistics_not_silently_summed(bad):
    f=Feed();f.bad=bad
    with pytest.raises(ValueError):MLB(f).player_statistics('1',2024,'hitting',['homeRuns'])


def test_ambiguity_blocks_stats():
    f=Feed();f.bad='ambiguous'
    r=MLB(f).compare_players(['One','Two'],2024,'hitting',['homeRuns'])
    assert r['type']=='comparison_blocked' and not r['ready_for_script']
    assert all(p=='people/search' for p,params in f.calls)


def test_validation_and_failures_have_no_old_data():
    t=OfficialMLB();t.client=MLB(Feed())
    r=t.execute({'action':'resolve_player','name':'One','season':2024})
    assert not r.success and not r.data['stale_fallback']
    assert not t.execute({'action':'resolve_player','name':'One','output_path':'x.json'}).success
    with pytest.raises(ValueError):Transport().get('../evil',{})
