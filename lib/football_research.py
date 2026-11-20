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


def query(data):
    if not LOCK.acquire(blocking=False):raise ValueError('Hay otra consulta UEFA activa; espera antes de repetir')
    try:
        tool=OfficialUEFA()
        result=tool.execute(data)
        return {'success':result.success,'data':result.data if result.success else None,
            'error':result.error,'cost_usd':0,'from_cache':False,'persistent_statistics':False,
            'stale_fallback':False,'note':'Consulta bajo demanda. Conserva el alcance, las advertencias y las fechas de las fuentes; no equivale a toda la carrera de una persona.'}
    finally:LOCK.release()
