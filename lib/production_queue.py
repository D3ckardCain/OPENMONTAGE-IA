"""Persistent sequential job transport; creative decisions stay in the producer."""
import threading
import uuid
from pathlib import Path
from lib import production_studio as studio
from lib import production_agent as agent

LOCK=threading.RLock()
WORKER=None
PAUSE=threading.Event()


def _path():return studio.CONFIG_DIR/'production_queue.json'
def _load():return studio.read_json(_path(),{'status':'paused','items':[]})
def _save(value):value['updated_at']=studio.now();studio.save_json(_path(),value)


def freeze_pilot():
    """Save a fixed ten-project cohort from the current queue without starting work."""
    with LOCK:
        if WORKER is not None:raise ValueError('Pausa la cola antes de fijar el piloto')
        state=read();items=state['items'][:10]
        root=str(studio.PROJECTS_DIR.resolve())
        if len(items)!=10 or len({item['project_id'] for item in items})!=10:
            raise ValueError('Necesitas diez proyectos distintos en los primeros diez lugares de la cola')
        if any(item['projects_root']!=root for item in items):
            raise ValueError('Conecta la raíz original de los diez proyectos')
        path=studio.CONFIG_DIR/'production_pilots.json'
        pilots=studio.read_json(path,[])
        if not isinstance(pilots,list):raise ValueError('El registro de pilotos no es válido')
        ids=[item['project_id'] for item in items]
        if pilots and pilots[-1].get('project_ids')==ids and pilots[-1].get('projects_root')==root:
            raise ValueError('Estos mismos diez proyectos ya están fijados como piloto actual')
        pilot={'id':uuid.uuid4().hex,'created_at':studio.now(),'projects_root':root,'project_ids':ids}
        pilots.append(pilot)
        studio.save_json(path,pilots[-20:])
    return {'pilot':pilot,'generation_started':False}


def _progress(item):
    """Expose saved producer evidence; never infer percentage or ETA."""
    if Path(item['projects_root']).resolve()!=studio.PROJECTS_DIR.resolve():
        return {'available':False,'message':'Conecta y selecciona la raíz original del proyecto'}
    try:
        path=studio.project_path(item['project_id'])
        request=studio.read_json(path/'production_request.json')
        job=studio.read_json(path/'job.json',{})
        stages=[]
        if request.get('pipeline'):
            manifest=studio.load_pipeline_readonly(request['pipeline'])
            for stage in manifest['stages']:
                if stage['name']=='publish':continue
                checkpoint=studio.read_json(path/('checkpoint_'+stage['name']+'.json'),{})
                stages.append({'name':stage['name'],'status':checkpoint.get('status','pending')})
        return {'available':True,'status':job.get('status','unknown'),'message':job.get('message',''),
            'updated_at':job.get('updated_at'),'stages':stages,
            'completed_stages':sum(stage['status']=='completed' for stage in stages),'total_stages':len(stages)}
    except (ValueError,OSError,KeyError) as exc:
        return {'available':False,'message':'No se pudo leer el progreso: '+str(exc)[:600]}


def read():
    with LOCK:
        value=_load()
        if WORKER is None and value['status'] in ('running','pausing'):
            value['status']='paused';value['message']='La app se cerró o el controlador se interrumpió. Revisa los trabajos antes de reanudar.'
            for item in value['items']:
                if item['status'] in ('starting','running'):item['status']='interrupted'
            _save(value)
        snapshot={**value,'items':[dict(item) for item in value['items']],'projects_root':str(studio.PROJECTS_DIR.resolve()),'worker_active':WORKER is not None,'automatic_restart':False}
    for item in snapshot['items']:item['progress']=_progress(item)
    return snapshot


def enqueue(project_id):
    path=studio.project_path(project_id)
    with LOCK:
        value=_load()
        if any(item['project_id']==project_id and item['projects_root']==str(studio.PROJECTS_DIR.resolve()) for item in value['items']):raise ValueError('El proyecto ya está en la cola; utiliza reintentar si quedó bloqueado')
        if len(value['items'])>=100:raise ValueError('La cola admite hasta 100 registros')
        request=studio.read_json(path/'production_request.json')
        value['items'].append({'id':uuid.uuid4().hex,'project_id':project_id,'title':request['title'],
            'projects_root':str(studio.PROJECTS_DIR.resolve()),'status':'pending','added_at':studio.now()})
        _save(value)
    return {'queued':True,'generation_started':False}


def retry(identifier):
    with LOCK:
        if WORKER is not None:raise ValueError('Pausa y espera al trabajo activo antes de reordenar la cola')
        value=read();value.pop('worker_active',None);value.pop('automatic_restart',None);value.pop('projects_root',None)
        item=next((item for item in value['items'] if item['id']==identifier),None)
        if item is None or item['status'] not in ('blocked','stopped','interrupted','awaiting_input','awaiting_human'):raise ValueError('Este registro no admite reintento')
        for record in value['items']:record.pop('progress',None)
        history=item.get('retry_history',[])
        if not isinstance(history,list):history=[]
        attempt={'status':item['status'],'message':item.get('message',''),
                 'started_at':item.get('started_at'),'finished_at':item.get('finished_at'),
                 'retried_at':studio.now()}
        if Path(item['projects_root']).resolve()==studio.PROJECTS_DIR.resolve():
            project=studio.project_path(item['project_id'])
            usage=studio.read_json(project/'resource_usage.json')
            if isinstance(usage,dict) and ((not history and not usage.get('recorded_at')) or
                    (isinstance(item.get('started_at'),str) and isinstance(usage.get('recorded_at'),str)
                     and usage['recorded_at']>=item['started_at'])):
                attempt['resource_usage']=usage
            if isinstance(item.get('started_at'),str):
                from lib.stage_timing import summarize
                job=studio.read_json(project/'job.json',{})
                attempt['stage_active_seconds']=summarize(job.get('events',[]),item['started_at'],
                                                          item.get('finished_at') or attempt['retried_at'])
        history.append(attempt)
        item['retry_history']=history[-20:]
        item.pop('started_at',None);item.pop('finished_at',None)
        item.update(status='pending',message='Reintento solicitado; se conservarán los checkpoints')
        value['status']='paused';_save(value)
    return {'queued':True,'generation_started':False}


def edit(identifier, direction=None):
    """Remove a queue record or move it one slot; never touch project files."""
    with LOCK:
        if WORKER is not None:raise ValueError('Pausa y espera al trabajo activo antes de modificar la cola')
        read()
        value=_load()
        index=next((i for i,item in enumerate(value['items']) if item['id']==identifier),None)
        if index is None:raise ValueError('Registro de cola inexistente')
        if direction is None:
            value['items'].pop(index)
        else:
            if direction not in ('up','down'):raise ValueError('Dirección inválida')
            if value['items'][index]['status']!='pending':raise ValueError('Solo se pueden mover trabajos pendientes')
            target=index+(-1 if direction=='up' else 1)
            if not 0<=target<len(value['items']):raise ValueError('El trabajo ya está en el extremo de la cola')
            value['items'][index],value['items'][target]=value['items'][target],value['items'][index]
        value['status']='paused';value['message']='Cola actualizada; no se inició generación';_save(value)
    return {'updated':True,'generation_started':False,'project_files_deleted':False}


def pause():
    PAUSE.set()
    with LOCK:
        value=_load();value['status']='pausing' if WORKER is not None else 'paused'
        value['message']='No se iniciará otro proyecto; el trabajo actual puede terminar.';_save(value)
    return {'requested':True,'current_task_cancelled':False}


def _update(identifier,**changes):
    with LOCK:
        value=_load();item=next(item for item in value['items'] if item['id']==identifier)
        item.update(**changes);_save(value)


def _run():
    global WORKER
    try:
        while not PAUSE.is_set():
            with LOCK:
                value=_load();item=next((dict(item) for item in value['items'] if item['status']!='completed'),None)
            if item is None:break
            if item['status']!='pending':break
            try:
                if Path(item['projects_root']).resolve()!=studio.PROJECTS_DIR.resolve():raise ValueError('Selecciona el disco de trabajo original y reinicia antes de ejecutar este proyecto')
                path=studio.project_path(item['project_id'])
                state=studio.read_json(path/'job.json',{})
                if state.get('status')=='awaiting_human':
                    _update(item['id'],status='awaiting_human',message='Aprueba la etapa desde el proyecto antes de reanudar');break
                if state.get('status')=='rendered':
                    _update(item['id'],status='completed',message='El productor ya había terminado; no se repitió');continue
                # Persist intent before launch. A restart requires explicit review
                # rather than risking an accidental second inference submission.
                _update(item['id'],status='starting',started_at=studio.now())
                if PAUSE.is_set():_update(item['id'],status='pending');break
                agent.start(item['project_id'])
                _update(item['id'],status='running')
                with agent.ACTIVE_LOCK:active=agent.ACTIVE.get(item['project_id'])
                if active and active[0] is not None:active[0].join()
                state=studio.read_json(path/'job.json',{});status=state.get('status','interrupted')
                _update(item['id'],status='completed' if status=='rendered' else status if status in ('awaiting_human','awaiting_input','stopped','blocked') else 'interrupted',
                    message=state.get('message','El productor no confirmó la finalización'),finished_at=studio.now())
                if status!='rendered':break
            except Exception as exc:
                _update(item['id'],status='blocked',message=str(exc)[:1200]);break
    finally:
        with LOCK:
            value=_load();value['status']='completed' if all(item['status']=='completed' for item in value['items']) else 'paused'
            value['message']='Cola terminada' if value['status']=='completed' else 'Cola pausada; revisa el primer trabajo pendiente'
            _save(value);WORKER=None


def start():
    global WORKER
    from lib import reference_analysis
    with LOCK:
        if WORKER is not None:raise ValueError('La cola ya está activa')
        read()
        value=_load()
        if not value['items'] or all(item['status']=='completed' for item in value['items']):raise ValueError('No hay proyectos pendientes')
        with agent.ACTIVE_LOCK,reference_analysis.LOCK:
            if agent.ACTIVE or reference_analysis.ACTIVE:raise ValueError('Espera a que termine la tarea local activa')
        value['status']='running';_save(value);PAUSE.clear()
        WORKER=threading.Thread(target=_run,daemon=True,name='production-queue');WORKER.start()
    return {'started':True,'publication_authorized':False}


def inspect():
    """Read-only snapshot, not a model compatibility or generation guarantee."""
    from lib.storage_layout import readiness
    with LOCK:
        value=_load()
        active=WORKER is not None
        items=[dict(item) for item in value['items']]
    from lib import reference_analysis
    with agent.ACTIVE_LOCK,reference_analysis.LOCK:
        local_task_active=bool(agent.ACTIVE or reference_analysis.ACTIVE)
    storage=readiness(studio.REPO_ROOT,studio.PROJECTS_DIR)
    queue_problems=[]
    if local_task_active:queue_problems.append('Espera a que termine la producción, análisis o entrega local activa')
    if active:queue_problems.append('La cola ya está activa')
    reports=[]
    for item in items:
        problems=[];job_status=None
        if Path(item['projects_root']).resolve()!=studio.PROJECTS_DIR.resolve():
            problems.append('El proyecto pertenece a otra raíz de trabajo; selecciona el disco original y reinicia')
        else:
            try:
                path=studio.project_path(item['project_id'])
                job_status=studio.read_json(path/'job.json',{}).get('status')
                if job_status=='awaiting_human':problems.append('La etapa requiere aprobación desde el proyecto')
            except (ValueError,OSError) as exc:problems.append(str(exc))
        if item['status'] not in ('pending','completed'):
            problems.append('Revisa el registro y vuelve a ponerlo pendiente antes de continuar')
        reports.append({'id':item['id'],'title':item['title'],'status':item['status'],
            'job_status':job_status,'problems':problems,'ready':not problems})
    pending=[item for item in reports if item['status']!='completed']
    return {'ready':bool(pending) and storage['ready'] and not active and not local_task_active and all(item['ready'] for item in pending),
        'worker_active':active,'local_task_active':local_task_active,'problems':queue_problems,'storage':storage,'items':reports,'generation_started':False,
        'scope':'queue_and_storage_only','note':'Comprobación puntual; no ejecuta modelos, no comprueba su compatibilidad ni garantiza espacio suficiente para el render.'}


def enqueue_many(project_ids):
    """Validate a small batch before saving it once; existing records are retained."""
    if not isinstance(project_ids,list) or not 1<=len(project_ids)<=10 or any(not isinstance(pid,str) for pid in project_ids):
        raise ValueError('Selecciona entre 1 y 10 proyectos')
    if len(set(project_ids))!=len(project_ids):raise ValueError('No repitas proyectos en el lote')
    with LOCK:
        value=_load();root=str(studio.PROJECTS_DIR.resolve());added=[];existing=[];records=[]
        for pid in project_ids:
            path=studio.project_path(pid)
            if any(item['project_id']==pid and item['projects_root']==root for item in value['items']):existing.append(pid);continue
            request=studio.read_json(path/'production_request.json')
            records.append({'id':uuid.uuid4().hex,'project_id':pid,'title':request['title'],'projects_root':root,'status':'pending','added_at':studio.now()})
            added.append(pid)
        if len(value['items'])+len(records)>100:raise ValueError('El lote supera el límite de 100 registros de cola')
        if records:value['items'].extend(records);_save(value)
    return {'added':added,'existing':existing,'generation_started':False}
