"""On-demand official football queries; no persistent statistics or stale fallback."""
import inspect
import threading
from tools.football.official_uefa import OfficialUEFA,ACTIONS
from tools.football.uefa import COMPETITIONS
from tools.football.uefa_live import UEFA

LOCK=threading.Lock()


def schema():
    actions=[]
    for name,fields in ACTIONS.items():
        signature=inspect.signature(getattr(UEFA,name))
        required=[key for key,param in signature.parameters.items() if key!='self' and param.default is inspect.Parameter.empty]
        actions.append({'name':name,'fields':list(fields),'required':required,
            'defaults':{key:param.default for key,param in signature.parameters.items() if key!='self' and param.default is not inspect.Parameter.empty},
            'choices':{'entity':['player','team']} if name=='ranking' else {'entity':['players','teams']} if name=='historical' else {}})
    return {'provider':'UEFA','competitions':list(COMPETITIONS),'actions':actions,'parameters':OfficialUEFA.input_schema['properties'],
        'persistent_statistics':False,'coverage_note':'Solo competiciones cubiertas por este conector UEFA; no todas las ligas ni FIFA o CONMEBOL.'}


def followups(data):
    """Prepare explicit official-ID lookups, never infer an identity from names."""
    if not isinstance(data,dict) or data.get('fuente')!='UEFA' or data.get('competicion') not in COMPETITIONS:return []
    rows=data.get('registros');scope=data.get('alcance',{});kind=data.get('tipo');result=[]
    if not isinstance(rows,list) or not isinstance(scope,dict):return []
    def numeric(value):return isinstance(value,(str,int)) and not isinstance(value,bool) and str(value).isascii() and str(value).isdigit()
    for index,row in enumerate(rows[:100]):
        if not isinstance(row,dict) or not numeric(row.get('id')):continue
        identifier=str(row['id']);params={'competition':data['competicion']};label=None
        if kind=='equipos' or kind=='ranking' and scope.get('entidad')=='team':
            params.update(action='team',team_id=identifier);label='Preparar ficha actual del equipo'
        elif kind=='ranking' and scope.get('entidad')=='player':
            metrics=scope.get('metricas');edition=scope.get('seasonYear')
            if type(edition) is not int or not isinstance(metrics,list) or not metrics:continue
            params.update(action='player',player_id=identifier,edition=edition,metrics=metrics,phase=scope.get('phase') or 'ALL');label='Preparar consulta del jugador en esta edición'
        elif kind in ('partidos_oficiales_sin_recalcular_marcadores','partidos_por_union_de_fases'):
            params.update(action='match',match_id=identifier);label='Preparar ficha del partido'
        if label:
            from jsonschema import validate,ValidationError
            try:validate(params,OfficialUEFA.input_schema)
            except ValidationError:continue
            result.append({'row_index':index,'label':label,'query':params})
    return result


def query(data):
    if not LOCK.acquire(blocking=False):raise ValueError('Hay otra consulta UEFA activa; espera antes de repetir')
    try:
        tool=OfficialUEFA()
        result=tool.execute(data)
        return {'success':result.success,'data':result.data if result.success else None,
            'followups':followups(result.data) if result.success else [],
            'error':result.error,'cost_usd':0,'from_cache':False,'persistent_statistics':False,
            'stale_fallback':False,'note':'Consulta bajo demanda. Conserva el alcance, las advertencias y las fechas de las fuentes; no equivale a toda la carrera de una persona.'}
    finally:LOCK.release()
