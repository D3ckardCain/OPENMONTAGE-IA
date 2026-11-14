"""Free public UEFA data adapter. No output artifacts or reusable data cache."""
from tools.base_tool import BaseTool,ToolResult,ToolTier,ToolRuntime,ToolStability,ResourceProfile
from tools.football.uefa_live import UEFA
from tools.football.uefa import COMPETITIONS

ACTIONS={
 'ranking':('competition','edition','entity','metrics','phase','team_id','order'),
 'matches':('competition','edition','phase','team_id'),
 'match':('competition','match_id','lineups'),
 'player':('competition','edition','player_id','metrics','phase'),
 'player_history':('competition','player_id','metrics'),
 'historical':('competition','entity','metric'),
 'coaches':('competition','edition','team_id','coach_id','phase'),
 'coach_balance':('competition','edition','coach_id','team_id','phase'),
 'teams':('competition','edition','phase'),
 'team':('competition','team_id'),
 'squad':('competition','edition','team_id'),
 'standings':('competition','edition','phase'),
 'head_to_head':('competition','team1','team2'),
 'definitions':('competition',),
}
class OfficialUEFA(BaseTool):
 name='official_uefa_live'
 version='0.4.0'
 provider='uefa_official'
 tier=ToolTier.SOURCE
 runtime=ToolRuntime.LOCAL
 stability=ToolStability.BETA
 capability='football_statistics'
 capabilities=['football_statistics','official_live_data']
 idempotency_key_fields=[]
 side_effects=['read_public_uefa_web_services']
 fallback=None
 fallback_tools=[]
 resource_profile=ResourceProfile(cpu_cores=1,ram_mb=512,vram_mb=0,disk_mb=0,network_required=True)
 dependencies=[]
 install_instructions='Adaptador Python local con acceso HTTPS a UEFA. Sin cuenta, API de pago ni modelos adicionales.'
 supports={'offline':False,'persistent_cache':False,'official_sources':True}
 input_schema={'type':'object','required':['action','competition'],'additionalProperties':False,'properties':{
  'action':{'type':'string','enum':list(ACTIONS)},
  'competition':{'type':'string','enum':list(COMPETITIONS)},
  'edition':{'type':'integer','minimum':1955},'entity':{'type':'string'},
  'metrics':{'type':'array','minItems':1,'uniqueItems':True,'items':{'type':'string','pattern':'^[a-z][a-z0-9_]*$'}},
  'metric':{'type':'string','pattern':'^[a-z][a-z0-9_]*$'},
  'phase':{'type':'string','enum':['TOURNAMENT','QUALIFYING','ALL']},
  'team_id':{'type':'string','pattern':'^[0-9]+$'},'player_id':{'type':'string','pattern':'^[0-9]+$'},
  'match_id':{'type':'string','pattern':'^[0-9]+$'},'coach_id':{'type':'string','pattern':'^[0-9]+$'},
  'team1':{'type':'string','pattern':'^[0-9]+$'},'team2':{'type':'string','pattern':'^[0-9]+$'},
  'order':{'type':'string','enum':['ASC','DESC']},'lineups':{'type':'boolean'}
 }}
 def __init__(self):self.client=UEFA()
 def execute(self,inputs):
  from jsonschema import validate
  try:
   validate(inputs,self.input_schema)
   action=inputs['action'];allowed=ACTIONS[action]
   extra=set(inputs)-set(allowed)-{'action'}
   if extra:raise ValueError('Parametros no aplicables: '+','.join(sorted(extra)))
   kwargs={k:inputs[k] for k in allowed if k in inputs}
   data=getattr(self.client,action)(**kwargs)
   return ToolResult(success=True,data=data,artifacts=[],cost_usd=0,from_cache=False)
  except Exception as exc:
   return ToolResult(success=False,error='UEFA_QUERY_REJECTED: '+str(exc),data={'fresh_query_failed':True,'stale_fallback':False},cost_usd=0,from_cache=False)
