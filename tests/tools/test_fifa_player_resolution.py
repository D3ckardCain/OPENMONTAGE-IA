from copy import deepcopy
import pytest
from tools.football.fifa_live import FIFA
from tools.football.official_fifa import OfficialFIFA


def player(pid, name, team='1', fdh=None):
    return {'IdPlayer':pid,'IdTeam':team,'IdSeason':'22',
            'PlayerName':[{'Description':name}],'ShortName':[],
            'Properties':{'IdIFES':fdh or pid}}


class Feed:
    def __init__(self):
        self.calls=[]
        self.players={'1':[player('10','Lionel MESSI',fdh='100')],
                      '2':[player('20','Kylian MBAPPÉ',team='2',fdh='200')]}
        self.stats={'100':[['Goals',0,True]],'200':[['Goals',2,True]]}
    def get(self,url):
        self.calls.append(url)
        if '/seasons/' in url:
            data={'IdSeason':'22','IdCompetition':'17','Properties':{'IdIFES':'99'}}
        elif '/competitions/teams/' in url:
            data={'Results':[{'IdTeam':k,'Name':[{'Description':n}],'Abbreviation':a} for k,n,a in [('1','Argentina','ARG'),('2','France','FRA')]]}
        elif '/squad?' in url:
            tid=url.split('/teams/')[1].split('/')[0]
            data={'IdCompetition':'17','IdSeason':'22','IdTeam':tid,'TeamName':[], 'Players':self.players[tid]}
        elif '/players.json' in url: data=self.stats
        else:raise AssertionError(url)
        return deepcopy(data),{'url':url,'retrieved_at':'2026-11-20T00:00:00Z'}


def test_comparison_resolves_names_and_official_namespace_mapping():
    feed=Feed();r=FIFA(feed).compare_players('17','22',[{'name':'Messi'},{'name':'Mbappe'}],['Goals'])
    assert r['type']=='player_comparison' and r['ready_for_script']
    assert [x['entity_id'] for x in r['records']]==['100','200']
    assert r['records'][0]['name']=='Lionel MESSI'
    assert r['records'][0]['statistics']['Goals']['value']==0
    assert all('idCompetition=17&idSeason=22' in u for u in feed.calls if '/squad?' in u)
    assert len([u for u in feed.calls if '/squad?' in u])==2


def test_team_hint_limits_requests_and_does_not_need_team_id():
    feed=Feed();r=FIFA(feed).resolve_players('17','22',[{'name':'messi','team_name':'ARG'}])
    assert r['records'][0]['status']=='resolved'
    assert len([u for u in feed.calls if '/squad?' in u])==1


def test_ambiguous_surname_blocks_without_stats_request():
    feed=Feed();feed.players['2']=[player('21','Other MESSI',team='2')]
    r=FIFA(feed).compare_players('17','22',[{'name':'messi'},{'name':'Other MESSI'}],['Goals'])
    assert not r['ready_for_script']
    assert r['records'][0]['status']=='ambiguous'
    assert not any('/players.json' in u for u in feed.calls)


def test_missing_name_does_not_fuzzy_match():
    r=FIFA(Feed()).resolve_players('17','22',[{'name':'Mess'}])
    assert r['records'][0]['status']=='not_found'


def test_duplicate_subject_and_missing_fdh_link_block():
    f=Feed()
    with pytest.raises(ValueError):FIFA(f).compare_players('17','22',[{'name':'messi'},{'name':'messi'}],['Goals'])
    f.players['1'][0]['Properties']={}
    with pytest.raises(ValueError):FIFA(f).compare_players('17','22',[{'name':'messi'},{'name':'mbappe'}],['Goals'])


def test_wrong_squad_scope_or_duplicate_player_fails():
    f=Feed();f.players['1'][0]['IdSeason']='23'
    with pytest.raises(ValueError):FIFA(f).squad('17','22','1')
    f=Feed();f.players['1'].append(deepcopy(f.players['1'][0]))
    with pytest.raises(ValueError):FIFA(f).squad('17','22','1')


def test_missing_metric_not_ready_and_tool_dispatch():
    tool=OfficialFIFA();tool.client=FIFA(Feed())
    r=tool.execute({'action':'compare_players','competition_id':'17','season_id':'22',
                    'subjects':[{'name':'messi'},{'name':'mbappe'}],'metrics':['Goals','Assists']})
    assert r.success and not r.data['ready_for_script']
    assert r.data['records'][0]['statistics']['Assists']['value'] is None


def test_one_unavailable_squad_does_not_become_not_found():
    f=Feed();f.players['2']=None
    with pytest.raises(ValueError):FIFA(f).resolve_players('17','22',[{'name':'messi'}])
