"""Official UEFA website services, fetched on demand; no persistent data cache.
Undocumented services may change: unexpected schemas fail closed.
"""
from dataclasses import dataclass
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from html import unescape
import argparse,json,re,time,urllib.request,urllib.error
from urllib.parse import urlencode,urljoin,urlsplit
try:
 from .uefa import COMPETITIONS,Unavailable,DOM,numeric
except ImportError:
 from uefa import COMPETITIONS,Unavailable,DOM,numeric

@dataclass
class Reply:
 data:object
 url:str
 retrieved_at:str
 http_date:str|None=None
 age:str|None=None

class Transport:
 def get(self,url,key=None):
  host=urlsplit(url).hostname
  if urlsplit(url).scheme!='https':raise Unavailable('HTTPS obligatorio')
  if host not in {'www.uefa.com','compstats.uefa.com','comp.uefa.com','match.uefa.com','matchstats.uefa.com','standings.uefa.com'}:raise Unavailable('Host ajeno a los servicios UEFA permitidos')
  headers={'User-Agent':'OpenMontageFootball/0.4','Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'en'}
  if key:headers['x-api-key']=key
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=25) as r:
    if urlsplit(r.url).hostname!=host:raise Unavailable('Redireccion inesperada')
    raw=r.read(12_000_001)
    if len(raw)>12_000_000:raise Unavailable('Respuesta excesiva')
    kind=r.headers.get('Content-Type','')
    text=raw.decode(r.headers.get_content_charset() or 'utf-8')
    data=json.loads(text) if 'json' in kind else text
    return Reply(data,r.url,datetime.now(timezone.utc).isoformat(),r.headers.get('Date'),r.headers.get('Age'))
  except urllib.error.HTTPError as e:
   raise Unavailable('Servicio UEFA devolvio HTTP '+str(e.code)+'; sin respaldo antiguo') from None

@dataclass
class Context:
 competition:str
 competition_id:str
 current_edition:int
 key:str
 page:str
 stats_url:str
 comp_url:str
 match_url:str

class UEFA:
 def __init__(self,transport=None,page_size=50,max_pages=200,pause=.15):
  if not 1<=page_size<=50:raise ValueError('page_size debe ser 1..50')
  if not 1<=max_pages<=1000:raise ValueError('max_pages debe ser 1..1000')
  self.transport=transport or Transport();self.page_size=page_size;self.max_pages=max_pages;self.pause=pause
 def context(self,competition):
  if competition not in COMPETITIONS:raise Unavailable('Competicion no soportada')
  page='https://www.uefa.com/'+COMPETITIONS[competition]+'/history/'
  try:reply=self.transport.get(page)
  except Unavailable as exc:
   if 'HTTP 404' not in str(exc):raise
   page='https://www.uefa.com/'+COMPETITIONS[competition]+'/'
   reply=self.transport.get(page)
  if not isinstance(reply.data,str):raise Unavailable('Configuracion UEFA no HTML')
  def one(name,numeric=False):
   pattern=r'window\.'+re.escape(name)+(r'\s*=\s*(\d+)\s*;' if numeric else r'''\s*=\s*['"]([^'"]+)['"]''')
   values=set(re.findall(pattern,reply.data))
   if len(values)!=1:raise Unavailable('Configuracion UEFA ausente o ambigua: '+name)
   return values.pop()
  folder=one('competitionFolder')
  allowed={COMPETITIONS[competition],{'champions':'ucl','europa':'uel','conference':'uecl','supercup':'scup','qualifiers':'eq'}.get(competition,COMPETITIONS[competition])}
  if folder not in allowed:raise Unavailable('Configuracion pertenece a otra competicion')
  cid=one('competitionId');edition=int(one('currentSeason',True));key=one('apiKey')
  if not cid.isdigit():raise Unavailable('ID de competicion invalido')
  services=[one(n) for n in ('compStatsApiUrl','compApiUrl','matchApiUrl')]
  for url,host in zip(services,['compstats.uefa.com','comp.uefa.com','match.uefa.com']):
   if urlsplit(url).scheme!='https' or urlsplit(url).hostname!=host:raise Unavailable('Servicio UEFA inesperado')
  return Context(competition,cid,edition,key,page,*services)
 def api(self,ctx,base,path,params):
  values={k:v for k,v in params.items() if v is not None}
  url=urljoin(base,path)+'?'+urlencode(values)
  r=self.transport.get(url,ctx.key)
  if isinstance(r.data,str):raise Unavailable('Servicio devolvio HTML en lugar de JSON')
  return r
 def paginate(self,ctx,base,path,params,identity):
  rows=[];seen=set();requests=[]
  for page in range(self.max_pages):
   r=self.api(ctx,base,path,{**params,'limit':self.page_size,'offset':page*self.page_size})
   if not isinstance(r.data,list):raise Unavailable('Paginacion: se esperaba lista')
   requests.append({'url':r.url,'consultado_utc':r.retrieved_at,'fecha_http':r.http_date,'edad_cache_servidor':r.age})
   if not r.data:return rows,requests
   if len(r.data)>self.page_size:raise Unavailable('Servicio ignoro el limite de pagina')
   for item in r.data:
    if not isinstance(item,dict):raise Unavailable('Registro no estructurado')
    key=identity(item)
    if key in seen:raise Unavailable('Paginacion duplicada o datos cambiantes; repetir la consulta')
    seen.add(key);rows.append(item)
   if self.pause:time.sleep(self.pause)
  raise Unavailable('Limite de paginas alcanzado; no se publica una lista parcial como completa')
 @staticmethod
 def scope(ctx,edition,phase):
  if type(edition) is not int or not 1955<=edition<=ctx.current_edition:raise Unavailable('Edicion fuera del rango admitido; usar anio final UEFA')
  if phase not in ('TOURNAMENT','QUALIFYING','ALL'):raise Unavailable('Fase debe ser TOURNAMENT, QUALIFYING o ALL')
  return {'competitionId':ctx.competition_id,'seasonYear':edition,'phase':None if phase=='ALL' else phase}
 @staticmethod
 def pack(ctx,scope,rows,requests,kind):
  return dict(fuente='UEFA',competicion=ctx.competition,tipo=kind,alcance=scope,registros=rows,consultas=requests,fase_solicitada=scope.get('phase'),fase_omitida_no_acredita_union=scope.get('phase') is None,paginacion_agotada=True,cobertura_historica_no_garantizada=True,advertencia='La consulta es nueva; no garantiza actualizacion instantanea ni cobertura de otras competiciones. Validar antes de publicar.')
 def ranking(self,competition,edition,entity,metrics,phase='TOURNAMENT',team_id=None,order='DESC'):
  if entity not in ('player','team'):raise Unavailable('Entidad debe ser player o team')
  if order not in ('ASC','DESC'):raise Unavailable('Orden invalido')
  if not metrics or any(not re.fullmatch('[a-z][a-z0-9_]*',m) for m in metrics):raise Unavailable('Metricas invalidas')
  if len(set(metrics))!=len(metrics):raise Unavailable('Metrica duplicada')
  ctx=self.context(competition);scope=self.scope(ctx,edition,phase)
  defs=self.api(ctx,ctx.stats_url,'v2/definitions',{}).data
  if not isinstance(defs,list):raise Unavailable('Definiciones no estructuradas')
  supported={d.get('name') for d in defs if isinstance(d,dict) and entity.upper() in d.get('actors',[])}
  if any(m not in supported for m in metrics):raise Unavailable('Metrica no definida por UEFA para '+entity+': '+','.join(m for m in metrics if m not in supported))
  if team_id is not None and not str(team_id).isdigit():raise Unavailable('team_id invalido')
  params={**scope,'stats':','.join(metrics),'order':order,'teamId':team_id,'optionalFields':'PLAYER,TEAM'}
  def ident(item):
   pid=item.get('playerId') if entity=='player' else item.get('teamId')
   if not pid:raise Unavailable('Falta ID de entidad')
   return str(pid),str(item.get('teamId',''))
  raw,requests=self.paginate(ctx,ctx.stats_url,'v2/'+entity+'-ranking',params,ident)
  rows=[]
  for item in raw:
   stats=item.get('statistics')
   if not isinstance(stats,list):raise Unavailable('Estadisticas no estructuradas')
   values={}
   for s in stats:
    if not isinstance(s,dict) or 'name' not in s or 'value' not in s or s['name'] in values:raise Unavailable('Estadistica mal formada o duplicada')
    value=s['value']
    if value is not None:
     try:
      d=Decimal(str(value))
      if not d.is_finite():raise InvalidOperation
     except (InvalidOperation,ValueError):raise Unavailable('Valor estadistico no numerico')
    values[s['name']]=value
   missing=[m for m in metrics if m not in values or values[m] is None]
   profile=item.get(entity,{})
   if team_id is not None and str(item.get('teamId'))!=str(team_id):raise Unavailable('El servicio ignoro el filtro de equipo')
   if not isinstance(profile,dict):raise Unavailable('Perfil mal formado')
   if profile.get('id') and str(profile['id'])!=str(item.get('playerId') if entity=='player' else item.get('teamId')):raise Unavailable('ID de perfil incompatible')
   rows.append({'id':str(item.get('playerId') if entity=='player' else item.get('teamId')),'team_id':str(item['teamId']) if item.get('teamId') else None,'nombre':profile.get('internationalName'),'estadisticas':{m:values.get(m) for m in metrics},'metricas_no_disponibles':missing,'posicion':item.get('rank')})
  return self.pack(ctx,{**scope,'entidad':entity,'metricas':metrics,'orden':order,'teamId':team_id},rows,requests,'ranking')
 def matches(self,competition,edition,phase='ALL',team_id=None):
  if phase=='ALL':
   reports=[self.matches(competition,edition,p,team_id) for p in ('TOURNAMENT','QUALIFYING')]
   rows=[];seen=set()
   for report in reports:
    for row in report['registros']:
     mid=str(row['id'])
     if mid in seen:raise Unavailable('Partido repetido entre fases; filtro no fiable')
     seen.add(mid);rows.append(row)
   return dict(fuente='UEFA',competicion=competition,tipo='partidos_por_union_de_fases',alcance={'seasonYear':edition,'phase':'ALL','teamId':team_id},registros=rows,consultas=[q for r in reports for q in r['consultas']],paginacion_agotada=True,fases_consultadas=['TOURNAMENT','QUALIFYING'],advertencia='Union de las dos fases solicitadas; cobertura limitada a lo devuelto por UEFA.')
  if team_id is not None and not str(team_id).isdigit():raise Unavailable('ID de equipo invalido')
  ctx=self.context(competition);scope=self.scope(ctx,edition,phase)
  params={**scope,'teamId':team_id,'order':'ASC'}
  def ident(x):
   if not x.get('id'):raise Unavailable('Partido sin ID')
   if str(x.get('competition',{}).get('id'))!=ctx.competition_id:raise Unavailable('Partido de otra competicion')
   if str(x.get('seasonYear'))!=str(edition):raise Unavailable('Partido de otra edicion')
   actual_phase=x.get('round',{}).get('phase')
   if actual_phase is not None and actual_phase!=phase:raise Unavailable('Partido de otra fase; filtro no fiable')
   if team_id is not None and str(team_id) not in {str(x.get(k,{}).get('id')) for k in ('homeTeam','awayTeam')}:raise Unavailable('El servicio ignoro el filtro de equipo')
   return str(x['id'])
  rows,requests=self.paginate(ctx,ctx.match_url,'v5/matches',params,ident)
  return self.pack(ctx,{**scope,'teamId':team_id},rows,requests,'partidos_oficiales_sin_recalcular_marcadores')
 def match(self,competition,match_id,lineups=False):
  if not str(match_id).isdigit():raise Unavailable('ID de partido invalido')
  ctx=self.context(competition)
  detail=self.api(ctx,ctx.match_url,'v5/matches/'+str(match_id),{})
  if not isinstance(detail.data,dict) or str(detail.data.get('id'))!=str(match_id):raise Unavailable('Partido no coincide')
  if str(detail.data.get('competition',{}).get('id'))!=ctx.competition_id:raise Unavailable('Partido de otra competicion')
  data={'partido':detail.data};requests=[{'url':detail.url,'consultado_utc':detail.retrieved_at}]
  if lineups:
   r=self.api(ctx,ctx.match_url,'v5/matches/'+str(match_id)+'/lineups',{})
   if not isinstance(r.data,dict) or str(r.data.get('matchId'))!=str(match_id):raise Unavailable('Alineacion invalida o de otro partido')
   data['alineaciones']=r.data;requests.append({'url':r.url,'consultado_utc':r.retrieved_at})
  return dict(fuente='UEFA',competicion=competition,datos=data,consultas=requests,estado=detail.data.get('status'),advertencia='Mantener separados score, penaltis y prorroga; no inferir marcador final de campos ausentes.')
 def player(self,competition,edition,player_id,metrics,phase='TOURNAMENT'):
  if not str(player_id).isdigit():raise Unavailable('ID de jugador invalido')
  if not metrics or any(not re.fullmatch('[a-z][a-z0-9_]*',m) for m in metrics):raise Unavailable('Metricas invalidas')
  ctx=self.context(competition);scope=self.scope(ctx,edition,phase)
  r=self.api(ctx,ctx.stats_url,'v2/player-statistics',{**scope,'playerId':player_id,'stats':','.join(metrics),'optionalFields':'PLAYER,TEAM'})
  if not isinstance(r.data,list):raise Unavailable('Respuesta individual no es lista')
  for item in r.data:
   if not isinstance(item,dict) or str(item.get('playerId'))!=str(player_id):raise Unavailable('Jugador devuelto no coincide')
   if not isinstance(item.get('statistics'),list):raise Unavailable('Estadisticas individuales incompletas')
  result=self.pack(ctx,{**scope,'playerId':str(player_id),'metricas':metrics},r.data,[{'url':r.url,'consultado_utc':r.retrieved_at}],'estadisticas_jugador_por_equipo_sin_sumar')
  result['paginacion_agotada']=None
  return result
 def historical(self,competition,entity,metric):
  if entity not in ('players','teams'):raise Unavailable('Entidad historica invalida')
  ctx=self.context(competition)
  root='https://www.uefa.com/'+COMPETITIONS[competition]+'/history/rankings/'
  menu=self.transport.get(root);dom=DOM()
  if not isinstance(menu.data,str):raise Unavailable('Indice historico no HTML')
  dom.feed(menu.data)
  links={urljoin(root,n.attrs['link-href']) for n in dom.root.walk('pk-button') if n.attrs.get('link-href')}
  url=root+entity+'/'+metric+'/'
  if url not in links:raise Unavailable('UEFA no publica ese ranking en el indice de esta competicion')
  records=[];seen=set();requests=[];label=None
  for page in range(self.max_pages):
   r=self.transport.get(url+(str(page) if page else ''))
   if not isinstance(r.data,str):raise Unavailable('Ranking historico no HTML')
   doc=DOM();doc.feed(r.data)
   if page==0:
    title=doc.root.first('h1');label=title.text() if title else None
    if not label:raise Unavailable('Falta titulo historico')
   requests.append({'url':r.url,'consultado_utc':r.retrieved_at})
   candidates=[n for n in doc.root.walk('pk-list-item') if 'stats-data-item' in n.attrs.get('class','').split()]
   if not candidates:
    if page==0:raise Unavailable('Ranking historico vacio, no equivale a cero')
    if '<html' in r.data.lower() or '<!doctype' in r.data.lower():raise Unavailable('Pagina completa inesperada al paginar, posible bloqueo')
    return self.pack(ctx,{'periodo':'historico_segun_UEFA','entidad':entity,'metrica':metric,'titulo':label,'incluye_previas':None,'criterio':'no inferir fases o inicio de cobertura sin definicion UEFA'},records,requests,'ranking_historico')
   for row in candidates:
    name=row.first(slot='primary');value=row.first(slot='suffix-card');rank=row.first(slot='prefix-card')
    if not name or not value or not rank:raise Unavailable('Fila historica incompleta')
    image=row.first('pk-avatar') if entity=='players' else row.first('pk-badge')
    src=image.attrs.get('src','') if image else ''
    pattern=r'https://img\.uefa\.com/imgml/TP/players/\d+/history/(\d+)\.jpg' if entity=='players' else r'https://img\.uefa\.com/imgml/TP/teams/logos/\d+x\d+/(\d+)\.png'
    found=re.fullmatch(pattern,src)
    if not found:raise Unavailable('ID historico ausente o formato cambiado')
    eid=found[1]
    identity=(eid,rank.text()) if metric=='season_goals_scored' else eid
    if identity in seen:raise Unavailable('Entidad historica repetida; paginacion no fiable')
    seen.add(identity)
    records.append({'id':eid,'nombre':name.text(),'posicion':None if metric=='season_goals_scored' else numeric(rank.text()),'temporada':rank.text() if metric=='season_goals_scored' else None,'valor':numeric(value.text()),'fuente_id':src})
   if self.pause:time.sleep(self.pause)
  raise Unavailable('Ranking historico excede limite; no se entrega parcial como completo')
 def coaches(self,competition,edition,team_id=None,coach_id=None,phase='ALL'):
  if coach_id is not None and not str(coach_id).isdigit():raise Unavailable('ID de entrenador invalido')
  matches=self.matches(competition,edition,phase,team_id)
  records=[];missing=[];requests=list(matches['consultas'])
  for match in matches['registros']:
   if match.get('status')!='FINISHED':continue
   result=self.match(competition,match['id'],True);requests.extend(result['consultas'])
   lineup=result['datos']['alineaciones']
   if not isinstance(lineup,dict) or str(lineup.get('matchId'))!=str(match['id']):raise Unavailable('Alineacion no coincide con partido')
   for side in ('homeTeam','awayTeam'):
    team=lineup.get(side,{})
    tid=str(team.get('team',{}).get('id',''))
    expected=str(result['datos']['partido'].get(side,{}).get('id',''))
    if not tid or tid!=expected:raise Unavailable('Equipo de alineacion no coincide con partido')
    if team_id and tid!=str(team_id):continue
    staff=team.get('coaches')
    if not isinstance(staff,list) or not any(isinstance(x,dict) and x.get('role')=='COACH' for x in staff):missing.append({'matchId':str(match['id']),'teamId':tid});continue
    for entry in staff:
     person=entry.get('person',{});pid=str(person.get('id',''));role=entry.get('role')
     if not pid or not role:raise Unavailable('Entrenador sin ID o funcion')
     if coach_id and pid!=str(coach_id):continue
     records.append({'matchId':str(match['id']),'teamId':tid,'coachId':pid,'nombre':person.get('translations',{}).get('name',{}).get('EN'),'funcion':role,'lado':side,'score_oficial':result['datos']['partido'].get('score'),'estado':'FINISHED'})
  return dict(fuente='UEFA',competicion=competition,edicion=edition,fase=phase,registros=records,alineaciones_sin_entrenador=missing,cobertura_completa_en_el_alcance=not missing,consultas=requests,advertencia='Funciones segun acta; no equiparar asistentes con entrenador principal. No equivale a toda la carrera ni acredita titulos personales.')
 def coach_balance(self,competition,edition,coach_id,team_id=None,phase='ALL'):
  report=self.coaches(competition,edition,team_id,coach_id,phase)
  return summarize_coach(report,coach_id)
 def player_history(self,competition,player_id,metrics):
  if not str(player_id).isdigit():raise Unavailable('ID de jugador invalido')
  if not metrics or any(not re.fullmatch('[a-z][a-z0-9_]*',m) for m in metrics):raise Unavailable('Metricas invalidas')
  ctx=self.context(competition)
  r=self.api(ctx,ctx.stats_url,'v2/player-statistics/all-time',{'playerId':player_id,'stats':','.join(metrics)})
  if not isinstance(r.data,dict) or str(r.data.get('playerId'))!=str(player_id):raise Unavailable('Historico no corresponde al jugador')
  raw=r.data.get('competitionSeasonStatistics')
  if not isinstance(raw,list):raise Unavailable('Historico sin desglose por competicion y edicion')
  # This service returns multiple competitions even when competitionId is requested.
  rows=[];seen=set()
  for row in raw:
   if not isinstance(row,dict):raise Unavailable('Fila historica mal formada')
   if str(row.get('competitionId'))!=ctx.competition_id:continue
   ident=(str(row.get('seasonYear')),str(row.get('teamId')))
   if ident in seen:raise Unavailable('Historico de jugador duplicado')
   seen.add(ident);rows.append(row)
  return dict(fuente='UEFA',competicion=competition,playerId=str(player_id),desglose_por_temporada_equipo=rows,url=r.url,consultado_utc=r.retrieved_at,cobertura_completa_de_carrera=False,incluye_previas=None,advertencia='Servicio por edicion sin fase verificada. No sumar como total de carrera ni interpretar filas ausentes como cero.')
 def teams(self,competition,edition,phase='ALL'):
  ctx=self.context(competition);scope=self.scope(ctx,edition,phase)
  def identity(row):
   if not row.get('id'):raise Unavailable('Equipo sin ID')
   return str(row['id'])
  rows,requests=self.paginate(ctx,ctx.comp_url,'v2/teams',scope,identity)
  return self.pack(ctx,scope,rows,requests,'equipos')
 def team(self,competition,team_id):
  if not str(team_id).isdigit():raise Unavailable('ID de equipo invalido')
  ctx=self.context(competition);r=self.api(ctx,ctx.comp_url,'v2/teams',{'teamIds':team_id})
  if not isinstance(r.data,list) or len(r.data)!=1 or str(r.data[0].get('id'))!=str(team_id):raise Unavailable('Perfil de equipo no coincide')
  return dict(fuente='UEFA',perfil=r.data[0],url=r.url,consultado_utc=r.retrieved_at,advertencia='Perfil actual, no plantilla historica')
 def head_to_head(self,competition,team1,team2):
  if any(not str(x).isdigit() for x in (team1,team2)) or str(team1)==str(team2):raise Unavailable('Equipos distintos con IDs numericos requeridos')
  ctx=self.context(competition);r=self.api(ctx,ctx.stats_url,'v2/team-statistics/head2head',{'teamId':str(team1)+','+str(team2),'competitionId':ctx.competition_id})
  if not isinstance(r.data,list) or len(r.data)!=2 or {str(x.get('teamId')) for x in r.data if isinstance(x,dict)}!={str(team1),str(team2)}:raise Unavailable('Enfrentamiento no corresponde a los dos equipos')
  for row in r.data:
   stats=row.get('statistics')
   if not isinstance(stats,list):raise Unavailable('Estadisticas H2H ausentes')
   values={}
   for item in stats:
    if item.get('name') in values:raise Unavailable('Metrica H2H duplicada')
    values[item.get('name')]=numeric(str(item.get('value')))
   required={'matches_win','matches_loss','matches_draw','matches_appearance'}
   if not required.issubset(values) or sum(values[k] for k in ('matches_win','matches_loss','matches_draw'))!=values['matches_appearance']:raise Unavailable('Balance H2H inconsistente')
  return dict(fuente='UEFA',competicion=competition,equipos=[str(team1),str(team2)],datos_oficiales=r.data,url=r.url,consultado_utc=r.retrieved_at,estado='identidades_y_balance_validados',incluye_previas=None,advertencia='Alcance historico del servicio UEFA; no extrapolar a otras competiciones ni asumir fases sin comprobar.')
 def squad(self,competition,edition,team_id):
  if not str(team_id).isdigit():raise Unavailable('ID de equipo invalido')
  ctx=self.context(competition);scope=self.scope(ctx,edition,'ALL')
  r=self.api(ctx,ctx.comp_url,'v2/team-players',{**scope,'teamId':team_id})
  if not isinstance(r.data,list):raise Unavailable('Plantilla no estructurada')
  seen=set()
  for row in r.data:
   if not isinstance(row,dict) or not row.get('playerId') or str(row.get('teamId'))!=str(team_id):raise Unavailable('Jugador de plantilla sin ID o de otro equipo')
   if str(row['playerId']) in seen:raise Unavailable('Plantilla duplicada')
   seen.add(str(row['playerId']))
  return dict(fuente='UEFA',competicion=competition,edicion=edition,teamId=str(team_id),inscripciones=r.data,url=r.url,consultado_utc=r.retrieved_at,advertencia='Inscripciones de UEFA en esta edicion, no toda la plantilla contractual del club.')
 def standings(self,competition,edition,phase='TOURNAMENT'):
  ctx=self.context(competition);scope=self.scope(ctx,edition,phase)
  r=self.api(ctx,'https://standings.uefa.com/','v1/standings',scope)
  if not isinstance(r.data,list):raise Unavailable('Clasificacion no estructurada')
  for group in r.data:
   if not isinstance(group,dict) or not isinstance(group.get('group'),dict) or not isinstance(group.get('items'),list):raise Unavailable('Grupo de clasificacion mal formado')
   meta=group['group']
   if str(meta.get('competitionId'))!=ctx.competition_id or str(meta.get('seasonYear'))!=str(edition):raise Unavailable('Clasificacion de otra competicion o edicion')
   if phase!='ALL' and meta.get('phase')!=phase:raise Unavailable('Clasificacion de otra fase')
  return dict(fuente='UEFA',competicion=competition,alcance=scope,grupos=r.data,url=r.url,consultado_utc=r.retrieved_at,advertencia='Clasificacion oficial por grupos/fases; no recalcular puntos sin reglas y sanciones. Una lista vacia no implica cero puntos.')
 def definitions(self,competition):
  ctx=self.context(competition);r=self.api(ctx,ctx.stats_url,'v2/definitions',{})
  return dict(fuente='UEFA',definiciones=r.data,url=r.url,consultado_utc=r.retrieved_at)

def summarize_coach(report,coach_id):
 if not str(coach_id).isdigit():raise Unavailable('ID de entrenador invalido')
 if not report.get('cobertura_completa_en_el_alcance'):raise Unavailable('Faltan entrenadores en actas; no se calcula un total')
 totals=dict(partidos=0,victorias=0,empates=0,derrotas=0,goles_favor=0,goles_contra=0,tandas_ganadas=0,tandas_perdidas=0)
 seen=set()
 for row in report.get('registros',[]):
  if str(row.get('coachId'))!=str(coach_id) or row.get('funcion')!='COACH':continue
  mid=str(row.get('matchId'))
  if mid in seen:raise Unavailable('Entrenador repetido en el mismo partido')
  seen.add(mid)
  if row.get('estado')!='FINISHED' or row.get('lado') not in ('homeTeam','awayTeam'):raise Unavailable('Partido o lado no verificable')
  score=row.get('score_oficial')
  if not isinstance(score,dict) or not isinstance(score.get('total'),dict):raise Unavailable('Falta marcador final, no equivale a cero')
  home,away=score['total'].get('home'),score['total'].get('away')
  if any(type(x) is not int or x<0 for x in (home,away)):raise Unavailable('Marcador final invalido')
  own,other=(home,away) if row['lado']=='homeTeam' else (away,home)
  totals['partidos']+=1;totals['goles_favor']+=own;totals['goles_contra']+=other
  totals['victorias' if own>other else 'derrotas' if own<other else 'empates']+=1
  if 'penalty' in score:
   p=score['penalty']
   if not isinstance(p,dict) or any(type(p.get(k)) is not int or p[k]<0 for k in ('home','away')):raise Unavailable('Tanda invalida')
   if home!=away or p['home']==p['away']:raise Unavailable('Tanda incompatible con el marcador')
   a,b=(p['home'],p['away']) if row['lado']=='homeTeam' else (p['away'],p['home'])
   totals['tandas_ganadas' if a>b else 'tandas_perdidas']+=1
 return {**report,'balance':totals,'criterio_balance':'Solo rol COACH en acta; marcador total tras prorroga y sin sumar tanda. Tandas separadas. Sin atribuir titulos ni totalidad de carrera.'}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('competition',choices=COMPETITIONS)
 sub=parser.add_subparsers(dest='command',required=True)
 a=sub.add_parser('ranking');a.add_argument('--edition',type=int,required=True);a.add_argument('--entity',choices=['player','team'],required=True);a.add_argument('--metrics',required=True);a.add_argument('--phase',default='TOURNAMENT');a.add_argument('--team-id')
 a=sub.add_parser('matches');a.add_argument('--edition',type=int,required=True);a.add_argument('--phase',default='ALL');a.add_argument('--team-id')
 a=sub.add_parser('match');a.add_argument('id');a.add_argument('--lineups',action='store_true')
 a=sub.add_parser('player');a.add_argument('id');a.add_argument('--edition',type=int,required=True);a.add_argument('--metrics',required=True);a.add_argument('--phase',default='TOURNAMENT')
 a=sub.add_parser('player-history');a.add_argument('id');a.add_argument('--metrics',required=True)
 a=sub.add_parser('historical');a.add_argument('--entity',choices=['players','teams'],required=True);a.add_argument('--metric',required=True)
 a=sub.add_parser('coaches');a.add_argument('--edition',type=int,required=True);a.add_argument('--team-id');a.add_argument('--coach-id');a.add_argument('--phase',default='ALL')
 a=sub.add_parser('coach-balance');a.add_argument('id');a.add_argument('--edition',type=int,required=True);a.add_argument('--team-id');a.add_argument('--phase',default='ALL')
 a=sub.add_parser('teams');a.add_argument('--edition',type=int,required=True);a.add_argument('--phase',default='ALL')
 a=sub.add_parser('team');a.add_argument('id')
 a=sub.add_parser('head-to-head');a.add_argument('team1');a.add_argument('team2')
 a=sub.add_parser('squad');a.add_argument('id');a.add_argument('--edition',type=int,required=True)
 a=sub.add_parser('standings');a.add_argument('--edition',type=int,required=True);a.add_argument('--phase',default='TOURNAMENT')
 sub.add_parser('definitions');args=parser.parse_args();client=UEFA()
 try:
  if args.command=='ranking':result=client.ranking(args.competition,args.edition,args.entity,args.metrics.split(','),args.phase,args.team_id)
  elif args.command=='matches':result=client.matches(args.competition,args.edition,args.phase,args.team_id)
  elif args.command=='match':result=client.match(args.competition,args.id,args.lineups)
  elif args.command=='player':result=client.player(args.competition,args.edition,args.id,args.metrics.split(','),args.phase)
  elif args.command=='player-history':result=client.player_history(args.competition,args.id,args.metrics.split(','))
  elif args.command=='historical':result=client.historical(args.competition,args.entity,args.metric)
  elif args.command=='coaches':result=client.coaches(args.competition,args.edition,args.team_id,args.coach_id,args.phase)
  elif args.command=='coach-balance':result=client.coach_balance(args.competition,args.edition,args.id,args.team_id,args.phase)
  elif args.command=='teams':result=client.teams(args.competition,args.edition,args.phase)
  elif args.command=='team':result=client.team(args.competition,args.id)
  elif args.command=='head-to-head':result=client.head_to_head(args.competition,args.team1,args.team2)
  elif args.command=='squad':result=client.squad(args.competition,args.edition,args.id)
  elif args.command=='standings':result=client.standings(args.competition,args.edition,args.phase)
  else:result=client.definitions(args.competition)
  print(json.dumps(result,ensure_ascii=False,indent=2))
 except Exception as e:parser.exit(1,'Consulta rechazada: '+str(e)+'\nNo se devuelve informacion antigua ni cobertura supuesta.\n')
