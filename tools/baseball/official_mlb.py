"""Read public MLB StatsAPI on demand; no saved-statistics fallback."""
import json
import math
import re
import unicodedata
import urllib.request
from datetime import datetime,timezone
from urllib.parse import urlencode
from tools.base_tool import BaseTool,ToolResult,ToolTier,ToolRuntime,ToolStability,ResourceProfile


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Redirección MLB no admitida')


class Transport:
    def get(self,path,params):
        if not re.fullmatch(r'(people/search|people/[0-9]+/stats)',path):raise ValueError('Ruta MLB no admitida')
        url='https://statsapi.mlb.com/api/v1/'+path+'?'+urlencode(params)
        request=urllib.request.Request(url,headers={'User-Agent':'OpenMontageSports/0.1','Accept':'application/json','Cache-Control':'no-cache','Pragma':'no-cache'})
        with urllib.request.build_opener(_NoRedirect()).open(request,timeout=25) as response:
            raw=response.read(4_000_001)
            if len(raw)>4_000_000:raise ValueError('Respuesta MLB excesiva')
            data=json.loads(raw)
            return data,{'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),
                         'http_date':response.headers.get('Date'),'http_age':response.headers.get('Age')}


def normalized(value):
    if not isinstance(value,str) or not 1<=len(value.strip())<=150:raise ValueError('Nombre requerido')
    text=''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c))
    result=' '.join(re.findall(r'[^\W_]+',text,re.UNICODE))
    if not result:raise ValueError('Nombre vacío')
    return result


class MLB:
    def __init__(self,transport=None):self.transport=transport or Transport()

    @staticmethod
    def pack(kind,scope,records,queries):
        return {'source':'MLB','sport':'baseball','type':kind,'scope':scope,'records':records,'queries':queries,
                'persistent_cache':False,'global_coverage':False,
                'warning':'Consulta nueva a MLB, no garantiza actualización instantánea. Solo MLB y temporada regular; sin NPB, KBO ni historial completo. No convertir innings a fracciones decimales ni sumar tasas.'}

    def resolve_player(self,name):
        target=normalized(name)
        data,query=self.transport.get('people/search',{'names':name,'sportIds':1})
        if not isinstance(data,dict) or not isinstance(data.get('people'),list) or len(data['people'])>100:
            raise ValueError('Respuesta de jugadores incompleta o formato inesperado')
        candidates=[];seen=set()
        for row in data['people']:
            if not isinstance(row,dict) or type(row.get('id')) is not int or row['id']<=0:
                raise ValueError('Jugador MLB sin ID válido')
            if row['id'] in seen:raise ValueError('Jugador duplicado')
            seen.add(row['id'])
            aliases=[row[k] for k in ('fullName','firstLastName','nameFirstLast','lastName','useLastName') if isinstance(row.get(k),str) and row[k].strip()]
            if not isinstance(row.get('fullName'),str) or not row['fullName'].strip():raise ValueError('Jugador sin nombre')
            if target not in {normalized(a) for a in aliases}:continue
            candidates.append({'entity_id':str(row['id']),'name':row['fullName'],'birth_date':row.get('birthDate'),
                               'birth_country':row.get('birthCountry'),'position':row.get('primaryPosition'),
                               'identity_source':query})
        return self.pack('player_resolution',{'sport_id':1},[{'requested_name':name,
            'status':'resolved' if len(candidates)==1 else 'ambiguous' if candidates else 'not_found',
            'candidates':candidates}],[query])

    def player_statistics(self,player_id,season,group,metrics):
        if not isinstance(player_id,str) or not re.fullmatch('[0-9]{1,12}',player_id):raise ValueError('ID MLB inválido')
        if type(season) is not int or not 1876<=season<=datetime.now(timezone.utc).year:raise ValueError('Temporada fuera del rango admitido')
        if group not in ('hitting','pitching'):raise ValueError('Elegir hitting o pitching')
        if not isinstance(metrics,list) or not 1<=len(metrics)<=30 or len(set(metrics))!=len(metrics) or any(not isinstance(m,str) or not re.fullmatch('[a-zA-Z][a-zA-Z0-9]{0,80}',m) for m in metrics):
            raise ValueError('Métricas inválidas')
        data,query=self.transport.get('people/'+player_id+'/stats',{'stats':'season','group':group,'season':season,'gameType':'R','sportIds':1})
        if not isinstance(data,dict) or not isinstance(data.get('stats'),list):raise ValueError('Estadísticas MLB no estructuradas')
        splits=[]
        for block in data['stats']:
            if not isinstance(block,dict) or block.get('type',{}).get('displayName')!='season' or block.get('group',{}).get('displayName')!=group or not isinstance(block.get('splits'),list):
                raise ValueError('Grupo o tipo estadístico no coincide')
            splits.extend(block['splits'])
        if not splits:raise ValueError('No hay estadísticas para ese jugador, temporada y grupo; no sustituir por cero')
        for split in splits:
            if not isinstance(split,dict) or split.get('season')!=str(season) or str(split.get('player',{}).get('id'))!=player_id or split.get('sport',{}).get('id')!=1 or split.get('gameType')!='R':
                raise ValueError('MLB devolvió otro jugador, temporada, deporte o fase')
        if len(splits)!=1:raise ValueError('Desglose múltiple por equipos: falta validar el total oficial; no sumar tasas ni innings')
        split=splits[0];stats=split.get('stat')
        if not isinstance(stats,dict):raise ValueError('Métricas no estructuradas')
        selected={}
        for metric in metrics:
            value=stats.get(metric)
            if value is not None and not (type(value) in (int,float) and math.isfinite(value) or isinstance(value,str) and re.fullmatch(r'-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)',value)):
                raise ValueError('Valor estadístico inesperado: '+metric)
            selected[metric]=value
        scope={'sport_id':1,'season':season,'group':group,'game_type':'R'}
        return self.pack('player_statistics',scope,[{'entity_id':player_id,'name':split.get('player',{}).get('fullName'),
            'statistics_source':dict(query),'team':split.get('team'),'statistics':selected,'missing_metrics':[m for m in metrics if selected[m] is None]}],[query])

    def compare_players(self,names,season,group,metrics):
        if not isinstance(names,list) or len(names)!=2:raise ValueError('Indicar dos nombres')
        resolved=[self.resolve_player(name) for name in names]
        queries=[q for r in resolved for q in r['queries']]
        if any(r['records'][0]['status']!='resolved' for r in resolved):
            return self.pack('comparison_blocked',{'season':season,'group':group,'game_type':'R'},[r['records'][0] for r in resolved],queries)|{'ready_for_script':False}
        identities=[r['records'][0]['candidates'][0] for r in resolved]
        if identities[0]['entity_id']==identities[1]['entity_id']:raise ValueError('La comparativa requiere dos jugadores distintos')
        rows, failures = [], []
        scope = {'sport_id': 1, 'season': season, 'group': group, 'game_type': 'R'}
        for identity in identities:
            player_id = identity['entity_id']
            try:
                report = self.player_statistics(player_id, season, group, metrics)
            except OSError as exc:
                failures.append({'player_id': player_id, 'reason': str(exc)})
                rows.append({'entity_id': player_id, 'name': identity['name'], 'identity': identity,
                             'statistics': dict.fromkeys(metrics), 'missing_metrics': list(metrics)})
                continue
            row = report['records'][0]
            if row['name'] != identity['name']:
                raise ValueError('Nombre estadístico distinto del resuelto')
            rows.append(row | {'identity': identity})
            queries.extend(report['queries'])
        if len(failures) == len(identities):
            raise ValueError('No se pudieron consultar las estadísticas de ninguno de los jugadores MLB')
        return self.pack('player_comparison', scope, rows, queries) | {
            'ready_for_script': not any(row['missing_metrics'] for row in rows), 'failed_players': failures}


    def collectible_card(self,name,season,group,metrics):
        resolution=self.resolve_player(name)
        result=resolution['records'][0]
        if result['status']!='resolved':
            return resolution|{'type':'card_blocked','ready_for_script':False}
        identity=result['candidates'][0]
        statistics=self.player_statistics(identity['entity_id'],season,group,metrics)
        row=statistics['records'][0]
        if row['name']!=identity['name']:raise ValueError('Identidad estadística inconsistente')
        source=statistics['queries'][0]
        facts=[{'metric':metric,'value':value,'entity_id':identity['entity_id'],
                'scope':statistics['scope'].copy(),'source_url':source['url'],'retrieved_at':source['retrieved_at']}
               for metric,value in row['statistics'].items()]
        return self.pack('collectible_card',statistics['scope'],[{'identity':identity,'team':row['team'],
            'facts':facts,'missing_metrics':row['missing_metrics'],'image':None,'image_rights':'not_provided'}],
            resolution['queries']+statistics['queries'])|{'ready_for_script':not row['missing_metrics'],'rendered':False}


class OfficialMLB(BaseTool):
    name='official_mlb_live'
    version='0.3.0'
    provider='mlb_official'
    tier=ToolTier.SOURCE
    runtime=ToolRuntime.LOCAL
    stability=ToolStability.EXPERIMENTAL
    capability='baseball_statistics'
    capabilities=['baseball_statistics','official_live_data']
    dependencies=[]
    idempotency_key_fields=[]
    side_effects=['read_public_mlb_web_services']
    fallback=None
    fallback_tools=[]
    supports={'persistent_cache':False,'offline':False,'name_resolution':True,'regular_season_only':True}
    install_instructions='Python y HTTPS a MLB StatsAPI; sin claves ni API de pago. Cobertura inicial: MLB, temporada regular.'
    resource_profile=ResourceProfile(cpu_cores=1,ram_mb=256,vram_mb=0,disk_mb=0,network_required=True)
    input_schema={'type':'object','additionalProperties':False,'required':['action'],'properties':{
        'action':{'enum':['resolve_player','player_statistics','compare_players','collectible_card']},
        'name':{'type':'string','minLength':1,'maxLength':150},
        'names':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'string','minLength':1,'maxLength':150}},
        'player_id':{'type':'string','pattern':'^[0-9]{1,12}$'},'season':{'type':'integer','minimum':1876},
        'group':{'enum':['hitting','pitching']},'metrics':{'type':'array','minItems':1,'maxItems':30,'uniqueItems':True,
            'items':{'type':'string','pattern':'^[A-Za-z][A-Za-z0-9]{0,80}$'}}}}
    def __init__(self):self.client=MLB()
    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            action=inputs['action']
            allowed={'resolve_player':{'name'},'collectible_card':{'name','season','group','metrics'},'player_statistics':{'player_id','season','group','metrics'},'compare_players':{'names','season','group','metrics'}}[action]
            if set(inputs)-allowed-{'action'}:raise ValueError('Parámetros no aplicables')
            data=getattr(self.client,action)(**{k:v for k,v in inputs.items() if k!='action'})
            return ToolResult(success=True,data=data,artifacts=[],cost_usd=0,from_cache=False)
        except Exception as exc:return ToolResult(success=False,error='MLB_QUERY_REJECTED: '+str(exc),data={'fresh_query_failed':True,'stale_fallback':False},cost_usd=0,from_cache=False)
