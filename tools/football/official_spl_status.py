"""Inspect the official SPL source. This is not a statistics extractor."""
import re
import urllib.request
from datetime import datetime,timezone
from tools.football.uefa import DOM
from tools.base_tool import BaseTool,ToolResult,ToolTier,ToolRuntime,ToolStability,ResourceProfile

URL='https://www.spl.com.sa/en/stats/players'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Redirección SPL no admitida')


def fetch():
    request=urllib.request.Request(URL,headers={'User-Agent':'OpenMontageSports/0.1','Cache-Control':'no-cache','Pragma':'no-cache'})
    with urllib.request.build_opener(NoRedirect()).open(request,timeout=25) as response:
        raw=response.read(4_000_001)
        if len(raw)>4_000_000:raise ValueError('Página SPL excesiva')
        return raw.decode('utf-8'),{'url':URL,'retrieved_at':datetime.now(timezone.utc).isoformat(),'http_date':response.headers.get('Date')}


def visible(node):
    if isinstance(node,str):return node
    if node.tag in ('script','style','noscript'):return ''
    return ' '.join(visible(child) for child in node.children)


def inspect(html,query):
    dom=DOM();dom.feed(html)
    text=' '.join(visible(dom.root).split())
    if 'Stats Hub' not in text or 'PLAYER STATISTICS' not in text:
        raise ValueError('Página SPL no reconocida; posible cambio de formato o bloqueo')
    unavailable='Player statistics are currently unavailable for the selected season.' in text
    refs=list(dict.fromkeys(re.findall(r'spl::Football_Season::[0-9a-f]{32}',html)))
    return {'source':'SPL','type':'source_status','statistics_status':'explicitly_unavailable_for_selected_season' if unavailable else 'extraction_not_implemented',
            'queries':[query],'season_ids_referenced':refs,'season_year_mapping_verified':False,
            'statistics':None,'ready_for_script':False,'persistent_cache':False,
            'reason':'La web oficial declara indisponibilidad para la selección por defecto.' if unavailable else 'La página respondió; todavía no hay extractor estadístico validado.',
            'limits':'Los IDs referenciados no acreditan cifras disponibles ni identifican por sí solos un año. No extrapolar la indisponibilidad de esta selección a todas las temporadas. No rellenar con ceros, datos antiguos ni conocimiento del modelo.'}


class OfficialSPLStatus(BaseTool):
    name='official_spl_source_status'
    version='0.1.0'
    provider='spl_official'
    tier=ToolTier.SOURCE
    runtime=ToolRuntime.LOCAL
    stability=ToolStability.EXPERIMENTAL
    capability='football_source_status'
    capabilities=['football_source_status']
    dependencies=[]
    idempotency_key_fields=[]
    side_effects=['read_public_spl_statistics_page']
    fallback=None
    fallback_tools=[]
    supports={'statistics_extraction':False,'persistent_cache':False,'offline':False}
    resource_profile=ResourceProfile(cpu_cores=1,ram_mb=256,vram_mb=0,disk_mb=0,network_required=True)
    install_instructions='Consulta HTTPS a SPL sin clave ni pago. Solo diagnóstico de la fuente; no devuelve estadísticas.'
    input_schema={'type':'object','additionalProperties':False,'properties':{}}
    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            html,query=fetch()
            return ToolResult(success=True,data=inspect(html,query),artifacts=[],cost_usd=0,from_cache=False)
        except Exception as exc:return ToolResult(success=False,error='SPL_SOURCE_REJECTED: '+str(exc),data={'fresh_query_failed':True,'stale_fallback':False,'statistics':None},cost_usd=0,from_cache=False)
