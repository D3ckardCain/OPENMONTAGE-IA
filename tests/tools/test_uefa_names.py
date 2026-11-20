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


def test_real_ranking_normalization_feeds_name_resolver(monkeypatch):
    from types import SimpleNamespace
    from tools.football.uefa_live import UEFA,Reply
    client=UEFA(pause=0)
    ctx=SimpleNamespace(competition='champions',competition_id='1',current_edition=2026,stats_url='https://compstats.uefa.com/',key='test')
    monkeypatch.setattr(client,'context',lambda competition:ctx)
    monkeypatch.setattr(client,'api',lambda *args:Reply([{'name':'goals','actors':['PLAYER']}],'https://compstats.uefa.com/definitions','2026-11-20'))
    raw=[{'playerId':pid,'teamId':team,'player':{'id':pid,'internationalName':name},'statistics':[{'name':'goals','value':value}]}
         for pid,team,name,value in [('1','10','Kylian Mbappé','8'),('2','20','Erling Haaland','6')]]
    monkeypatch.setattr(client,'paginate',lambda *args:(raw,[{'url':'https://compstats.uefa.com/ranking','consultado_utc':'2026-11-20'}]))
    result=client.compare_players('champions',2024,['Mbappe','Haaland'],['goals'])
    assert result['ready_for_script']
    assert [row['estadisticas']['goals'] for row in result['registros']]==['8','6']


def test_shared_surname_needs_first_name_not_ranking_position():
    c=Client();c.rows.append({'id':'3','team_id':'10','nombre':'Ethan Mbappé','estadisticas':{'goals':0},'metricas_no_disponibles':[]})
    ambiguous=compare(c,'champions',2024,['Mbappe','Haaland'],['goals'])
    assert ambiguous['tipo']=='comparativa_bloqueada'
    assert ambiguous['registros'][0]['nombres_oficiales_para_aclarar']==['Kylian Mbappé','Ethan Mbappé']
    assert ambiguous['diagnostico_identidad']['filas_consultadas']==3
    exact=compare(c,'champions',2024,['Kylian Mbappe','Erling Haaland'],['goals'])
    assert exact['ready_for_script']
    assert exact['registros'][0]['id']=='1'


def test_pagination_attaches_correct_page_to_each_ranking_row(monkeypatch):
    from tools.football.uefa_live import UEFA,Reply
    client=UEFA(page_size=1,pause=0)
    data=[[{'id':'first'}],[{'id':'second'}],[]]
    def api(ctx,base,path,params):
        offset=params['offset']
        return Reply(data[offset],f'https://compstats.uefa.com/ranking?offset={offset}',f'2026-11-20T00:00:0{offset}Z')
    monkeypatch.setattr(client,'api',api)
    rows,queries=client.paginate(None,'https://compstats.uefa.com/','ranking',{},lambda x:x['id'],True)
    assert rows[0]['_openmontage_source']['url'].endswith('offset=0')
    assert rows[1]['_openmontage_source']['url'].endswith('offset=1')
    assert '_openmontage_source' not in data[0][0]
    assert len(queries)==3
    plain,_=client.paginate(None,'https://compstats.uefa.com/','ranking',{},lambda x:x['id'])
    assert '_openmontage_source' not in plain[0]


def test_collectible_card_resolves_one_name_without_inventing_portrait_or_titles():
    from tools.football.uefa_names import collectible_card
    r=collectible_card(Client(),'champions',2024,['Kylian Mbappe'],['goals'])
    assert r['tipo']=='postal_jugador' and r['ready_for_script']
    assert r['registros'][0]['estadisticas']['goals']==0
    assert r['retrato'] is None and r['palmares'] is None and r['puntuacion_habilidad'] is None
    assert not r['rendered']
    r=collectible_card(Client(),'champions',2024,['Unknown'],['goals'])
    assert r['tipo']=='postal_bloqueada' and not r['ready_for_script']
    with pytest.raises(ValueError):collectible_card(Client(),'champions',2024,['Mbappe','Haaland'],['goals'])


def test_registered_uefa_card_action():
    t=OfficialUEFA();t.client=Client()
    r=t.execute({'action':'collectible_card','competition':'champions','edition':2024,'names':['Kylian Mbappe'],'metrics':['goals']})
    assert r.success and r.data['ready_for_script']
