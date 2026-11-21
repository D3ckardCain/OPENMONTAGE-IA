"""On-demand men's WBA rankings. No inferred fight records or champion status."""
import calendar
import re
import urllib.request
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qs
from tools.football.uefa import DOM
from tools.baseball.official_mlb import normalized
from tools.base_tool import BaseTool,ToolResult,ToolTier,ToolRuntime,ToolStability,ResourceProfile

URL='https://www.wbaboxing.com/wba-ranking'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Redirección WBA no admitida')


def fetch():
    request=urllib.request.Request(URL,headers={'User-Agent':'OpenMontageSports/0.1','Cache-Control':'no-cache','Pragma':'no-cache'})
    with urllib.request.build_opener(NoRedirect()).open(request,timeout=25) as response:
        raw=response.read(4_000_001)
        if len(raw)>4_000_000:raise ValueError('Página WBA excesiva')
        return raw.decode('utf-8'),{'url':URL,'retrieved_at':datetime.now(timezone.utc).isoformat(),'http_date':response.headers.get('Date')}


def parse(html,query):
    dom=DOM();dom.feed(html);root=dom.root
    dates=set()
    for heading in root.walk('h2'):
        match=re.fullmatch(r'World Boxing Association Ranking as of ([A-Z]+) (\d{4})',heading.text(),re.I)
        if match:dates.add((match[1].upper(),int(match[2])))
    if len(dates)!=1:raise ValueError('Falta un mes de referencia WBA inequívoco')
    month,year=dates.pop()
    months={calendar.month_name[n].upper():n for n in range(1,13)}
    if month not in months or not 1900<=year<=datetime.now(timezone.utc).year:raise ValueError('Fecha WBA inválida')
    headings={}
    for link in root.walk('a'):
        target=link.attrs.get('href','')
        if re.fullmatch(r'#division[0-9]+',target):headings.setdefault(target[1:],set()).add(link.text())
    records=[];divisions=set()
    for division in root.walk('div'):
        ident=division.attrs.get('id','')
        if not re.fullmatch(r'division[0-9]+',ident):continue
        labels=headings.get(ident,set())
        if len(labels)!=1 or ident in divisions:raise ValueError('División ausente, duplicada o ambigua')
        label=next(iter(labels));divisions.add(ident);ranks=set()
        for row in division.walk('tr'):
            cells=list(row.walk('td'))
            if not cells or not re.fullmatch(r'[0-9]+',cells[0].text()):continue
            rank=int(cells[0].text())
            if not 1<=rank<=15 or rank in ranks:raise ValueError('Puesto WBA duplicado o fuera de rango')
            ranks.add(rank)
            links=[a for a in row.walk('a') if '/wba-boxer-profile/' in a.attrs.get('href','')]
            if not links:
                if 'NOT RATED' not in row.text().upper():raise ValueError('Puesto sin perfil o marca de vacante reconocida')
                records.append({'division':label,'rank':rank,'name':None,'entity_id':None,'status':'not_rated','source':dict(query)})
                continue
            if len(cells)!=4 or len(links)!=1:raise ValueError('Fila WBA cambió de formato')
            link=links[0];profile=link.attrs['href'];url=urlsplit(profile)
            params=parse_qs(url.query)
            ids=params.get('id',[])
            if url.scheme!='https' or url.hostname not in ('www.wbaboxing.com','wbaboxing.com') or url.path!='/wba-boxer-profile/' or len(ids)!=1 or not re.fullmatch('[0-9]+',ids[0]):raise ValueError('Perfil WBA inválido')
            name=link.text()
            if not name:raise ValueError('Boxeador sin nombre')
            records.append({'division':label,'rank':rank,'name':name,'entity_id':ids[0],'profile_url':profile,
                            'country':cells[3].text(),'regional_label_as_published':cells[2].text(),
                            'status':'ranked','source':dict(query)})
        if ranks!=set(range(1,16)):raise ValueError('División incompleta; no presentar un ranking parcial como completo')
    if not divisions:raise ValueError('No hay divisiones reconocidas')
    return {'source':'WBA','sport':'boxing','type':'rankings','scope':{'category':'men','as_of_month':f'{year:04d}-{months[month]:02d}'},
            'records':records,'queries':[query],'champions_included':False,'fight_record_included':False,
            'persistent_cache':False,'global_coverage':False,
            'warning':'Solo puestos 1–15 del ranking masculino WBA publicado para ese mes. No incluye campeones fuera de los puestos, récord de combates, nocauts ni rankings WBC/IBF/WBO. Fecha de consulta y mes de publicación son distintos.'}


class OfficialWBA(BaseTool):
    name='official_wba_live'
    version='0.2.0'
    provider='wba_official'
    tier=ToolTier.SOURCE
    runtime=ToolRuntime.LOCAL
    stability=ToolStability.EXPERIMENTAL
    capability='boxing_rankings'
    capabilities=['boxing_rankings','official_live_data']
    dependencies=[]
    idempotency_key_fields=[]
    side_effects=['read_public_wba_rankings']
    fallback=None
    fallback_tools=[]
    supports={'persistent_cache':False,'offline':False,'mens_rankings_only':True,'fight_records':False}
    resource_profile=ResourceProfile(cpu_cores=1,ram_mb=256,vram_mb=0,disk_mb=0,network_required=True)
    install_instructions='HTTPS a la web oficial WBA; sin clave, modelos ni API de pago. Solo ranking masculino, no récord de combates.'
    input_schema={'type':'object','required':['action'],'additionalProperties':False,'properties':{
        'action':{'enum':['rankings','resolve_boxer','collectible_card']},'name':{'type':'string','minLength':1,'maxLength':150}}}
    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            if inputs['action']=='rankings' and 'name' in inputs:raise ValueError('Nombre no aplicable al listado completo')
            target=normalized(inputs['name']) if inputs['action'] in ('resolve_boxer','collectible_card') else None
            html,query=fetch();report=parse(html,query)
            if target:
                candidates=[r for r in report['records'] if r['name'] and (target==normalized(r['name']) or (' '+target+' ') in (' '+normalized(r['name'])+' '))]
                report.update(type='boxer_resolution',records=[{'requested_name':inputs['name'],'status':'resolved' if len(candidates)==1 else 'ambiguous' if candidates else 'not_found_in_ranking','candidates':candidates}])
                if inputs['action']=='collectible_card':
                    if len(candidates)!=1:
                        report.update(type='card_blocked',ready_for_script=False)
                    else:
                        row=candidates[0];scope=report['scope']|{'division':row['division']}
                        fact={'metric':'rank','value':row['rank'],'entity_id':row['entity_id'],
                              'scope':scope,'source_url':query['url'],'retrieved_at':query['retrieved_at']}
                        report.update(type='collectible_card',scope=scope,ready_for_script=True,rendered=False,
                            records=[{'identity':{'name':row['name'],'entity_id':row['entity_id'],
                                'team_name':[{'Description':row['division']}],'country':row['country'],
                                'profile_url':row['profile_url']},'facts':[fact],
                                'image':None,'fight_record':None,'knockouts':None,'skill_rating':None}])
            return ToolResult(success=True,data=report,artifacts=[],cost_usd=0,from_cache=False)
        except Exception as exc:return ToolResult(success=False,error='WBA_QUERY_REJECTED: '+str(exc),data={'fresh_query_failed':True,'stale_fallback':False},cost_usd=0,from_cache=False)
