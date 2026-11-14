"""UEFA live overview connector. No persistence, no inferred career totals."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import json, re, urllib.request
from urllib.parse import urljoin, urlsplit, parse_qs

COMPETITIONS = {
 'champions': 'uefachampionsleague',
 'europa': 'uefaeuropaleague',
 'conference': 'uefaconferenceleague',
 'euro': 'uefaeuro',
 'nations': 'uefanationsleague',
 'supercup': 'uefasupercup',
 'finalissima': 'finalissima',
 'qualifiers': 'european-qualifiers',
}
class Unavailable(ValueError): pass
@dataclass
class Node:
 tag: str
 attrs: dict = field(default_factory=dict)
 children: list = field(default_factory=list)
 def text(self):
  return ' '.join(' '.join(c.text() if isinstance(c,Node) else c for c in self.children).split())
 def walk(self,tag=None,**attrs):
  for c in self.children:
   if isinstance(c,Node):
    if (tag is None or c.tag==tag) and all(c.attrs.get(k)==v for k,v in attrs.items()): yield c
    yield from c.walk(tag,**attrs)
 def first(self,tag=None,**attrs): return next(self.walk(tag,**attrs),None)
class DOM(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 def __init__(self):
  super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root]
 def handle_starttag(self,tag,attrs):
  n=Node(tag,dict(attrs));self.stack[-1].children.append(n)
  if tag not in self.VOID:self.stack.append(n)
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in self.VOID:self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:del self.stack[i:];break
 def handle_data(self,data):self.stack[-1].children.append(data)

def numeric(raw):
 if not re.fullmatch(r'\d+(?:\.\d+)?',raw):raise Unavailable('Formato numerico inesperado: '+raw)
 try:value=Decimal(raw)
 except InvalidOperation:raise Unavailable('Numero invalido')
 return int(value) if value==value.to_integral_value() else str(value)

def parse_overview(html,competition,expected_season):
 if competition not in COMPETITIONS:raise Unavailable('Competicion no soportada')
 dom=DOM();dom.feed(html);root=dom.root
 heading=root.first('h1')
 if not heading:raise Unavailable('Falta cabecera estadistica; posible bloqueo o cambio de pagina')
 match=re.fullmatch(r'Tournament stats (\d{4}(?:/\d{2,4})?)',heading.text())
 history_match=re.fullmatch(r'(\d{4}) Stats',heading.text())
 if match:season=match[1]
 elif history_match:season=history_match[1]
 elif heading.text()=='Tournament stats':
  editions=set(re.findall(r'window\.currentSeason\s*=\s*(\d{4})\s*;',html))
  if len(editions)!=1:raise Unavailable('UEFA no identifica una edicion unica')
  season=editions.pop()
 else:raise Unavailable('Cabecera UEFA no reconocida: '+heading.text())
 if not re.fullmatch(r'\d{4}(?:/\d{2,4})?',expected_season):raise Unavailable('Edicion invalida')
 if season!=expected_season:raise Unavailable('Edicion solicitada '+expected_season+'; la pagina identifica '+season)
 folders=set(re.findall(r"window\.competitionFolder\s*=\s*['\"]([^'\"]+)['\"]",html))
 if folders and not folders.issubset({COMPETITIONS[competition],{'champions':'ucl','europa':'uel','conference':'uecl','supercup':'scup','qualifiers':'eq'}.get(competition,COMPETITIONS[competition])}):raise Unavailable('La pagina corresponde a otra competicion')
 base=source_url(competition,expected_season)
 rankings=[];keys=set()
 for card in root.walk('pk-data-card'):
  cta=card.first('pk-button',slot='cta')
  if not cta:continue
  path=cta.attrs.get('link-href','');parts=path.split('?',1)[0].strip('/').split('/')
  if not parts or parts[0] not in ('clubs','players','teams'):continue
  entity_type=parts[0]
  query_args=parse_qs(urlsplit(path).query)
  if len(query_args.get('sortBy',[]))!=1:raise Unavailable('Metrica sin sortBy unico')
  metric=query_args['sortBy'][0]
  header=card.first(slot='header')
  # Header contains the first-ranked row as well as its metric label.
  metric_label=next((n.text() for n in header.children if isinstance(n,Node) and n.tag=='div'),metric) if header else metric
  rows=[];ids=set()
  for row in card.walk('pk-list-item'):
   value=row.first(slot='suffix-card');name=row.first(slot='primary');rank=row.first(slot='prefix-card')
   if not value or not name:continue
   link=next((n for n in row.walk('a') if re.search(r'/(?:players|clubs|teams)/\d+',n.attrs.get('href',''))),None)
   if not link:
    avatar=row.first('pk-avatar')
    image=avatar.attrs.get('src','') if avatar else ''
    image_id=re.fullmatch(r'https://img\.uefa\.com/imgml/TP/players/\d+/\d{4}/\d+x\d+/(\d+)\.jpg',image)
    if entity_type!='players' or not image_id:raise Unavailable('Fila con cifra sin identificador de entidad')
    href=None;actual='players';entity_id=image_id[1];id_source=image
   else:
    href=link.attrs['href'];id_match=re.search(r'/(players|clubs|teams)/(\d+)',href)
    actual=id_match[1];entity_id=id_match[2];id_source=urljoin(base,href)
   if (entity_type=='players')!=(actual=='players'):raise Unavailable('Entidad incompatible con ranking')
   if entity_id in ids:raise Unavailable('Entidad duplicada en ranking')
   ids.add(entity_id)
   secondary=row.first(slot='secondary')
   r=int(rank.text()) if rank and rank.text().isdigit() else None
   rows.append(dict(id=entity_id,nombre=name.text(),contexto=secondary.text() if secondary else None,posicion=r,valor=numeric(value.text()),valor_original=value.text(),perfil=urljoin(base,href) if href else None,fuente_identificador=id_source))
  if rows:
   key=(entity_type,metric)
   if key in keys:
    previous=next(x for x in rankings if (x['entidad'],x['metrica'])==key)
    if previous['filas']!=rows:raise Unavailable('Rankings duplicados con cifras distintas')
    continue
   keys.add(key)
   rankings.append(dict(entidad=entity_type,metrica=metric,etiqueta=metric_label,filas=rows,ranking_completo=False,url_ranking=urljoin(base,path)))
 if not rankings:raise Unavailable('No se encontraron rankings verificables en el HTML')
 return dict(competicion=competition,temporada=season,fuente=base,alcance='lideres_visibles_del_resumen_UEFA; no es historial ni ranking completo',rankings=rankings)

def source_url(competition,edition):
 if competition=='euro':
  if not re.fullmatch(r'\d{4}',edition):raise Unavailable('EURO requiere anio de edicion de cuatro cifras')
  return 'https://www.uefa.com/uefaeuro/history/seasons/'+edition+'/statistics/'
 return 'https://www.uefa.com/'+COMPETITIONS[competition]+'/statistics/'

def query(competition,expected_season,fetch=None):
 if competition not in COMPETITIONS:raise Unavailable('Competicion no soportada')
 url=source_url(competition,expected_season)
 if fetch is None:fetch=fetch_http
 html,metadata=fetch(url)
 result=parse_overview(html,competition,expected_season)
 result.update(metadata);result['consultado_utc']=datetime.now(timezone.utc).isoformat()
 result['estado']='extraido_de_fuente_oficial; pendiente_contraste_para_publicacion'
 return result

def fetch_http(url):
 request=urllib.request.Request(url,headers={'User-Agent':'OpenMontageFootball/0.3','Cache-Control':'no-cache','Pragma':'no-cache','Accept-Language':'en'})
 with urllib.request.urlopen(request,timeout=25) as response:
  final=response.url
  if urlsplit(final).hostname!='www.uefa.com':raise Unavailable('Redireccion fuera de UEFA')
  if 'html' not in response.headers.get('Content-Type',''):raise Unavailable('Respuesta no HTML')
  body=response.read(4_000_001)
  if len(body)>4_000_000:raise Unavailable('Respuesta excede limite')
  return body.decode(response.headers.get_content_charset() or 'utf-8'),dict(url_consultada=final,fecha_http=response.headers.get('Date'),edad_cache_servidor=response.headers.get('Age'),actualizado_por_organizador=None)

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('competicion',choices=COMPETITIONS);parser.add_argument('--temporada',required=True);args=parser.parse_args()
 try:print(json.dumps(query(args.competicion,args.temporada),ensure_ascii=False,indent=2))
 except Exception as exc:parser.exit(1,'No disponible: '+str(exc)+'\nNo se usan estadisticas guardadas.\n')
