from copy import deepcopy
import pytest
from tools.football.official_uefa import OfficialUEFA
from tools.football.uefa_names import resolve,compare


class Client:
    def __init__(self):
        self.calls=[]
        self.rows=[{'id':'1','team_id':'10','nombre':'Kylian Mbappé','estadisticas':{'goals':0},'metricas_no_disponibles':[]},
                   {'id':'2','team_id':'20','nombre':'Erling Haaland','estadisticas':{'goals':3},'metricas_no_disponibles':[]}]
    def ranking(self,*args):
        self.calls.append(args)
        return {'fuente':'UEFA','registros':deepcopy(self.rows),'paginacion_agotada':True,
                'alcance':{'competitionId':'1','seasonYear':2024,'phase':'TOURNAMENT'},
                'consultas':[{'url':'https://compstats.uefa.com/fixture','consultado_utc':'2026-11-20'}]}


def test_resolves_accents_preserves_zero_and_queries_once_per_comparison():
    c=Client();r=compare(c,'champions',2024,['Mbappe','Haaland'],['goals'])
    assert r['ready_for_script'] and len(c.calls)==1
    assert r['registros'][0]['estadisticas']['goals']==0
    assert r['consultas'] and r['alcance']['seasonYear']==2024


def test_ambiguous_surnames_and_team_splits_are_not_added():
    c=Client();c.rows.append(dict(c.rows[0],team_id='99'))
    r=compare(c,'champions',2024,['Mbappe','Haaland'],['goals'])
    assert not r['ready_for_script'] and r['tipo']=='comparativa_bloqueada'
    assert r['registros'][0]['estado']=='ambiguous'


def test_absent_name_is_not_claimed_absent_from_tournament():
    r=resolve(Client(),'champions',2024,['Missing'],['goals'])
    assert r['registros'][0]['estado']=='not_found_in_ranking'
    assert r['poblacion_consultada']=='ranking_de_las_metricas_solicitadas'


def test_missing_metric_blocks_script_and_same_player_rejected():
    c=Client();c.rows[0]['estadisticas']['goals']=None
    assert not compare(c,'champions',2024,['Mbappe','Haaland'],['goals'])['ready_for_script']
    with pytest.raises(ValueError):compare(Client(),'champions',2024,['Mbappe','Kylian Mbappe'],['goals'])


def test_tool_dispatch_validation_and_failure_without_cache():
    t=OfficialUEFA();t.client=Client()
    args={'action':'compare_players','competition':'champions','edition':2024,'names':['Mbappe','Haaland'],'metrics':['goals']}
    assert t.execute(args).success
    assert not t.execute(dict(args,player_id='1')).success
    assert not t.execute(dict(args,names=['Mbappe'])).success
