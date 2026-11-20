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


def read():
    with LOCK:
        value=_load()
        if WORKER is None and value['status'] in ('running','pausing'):
            value['status']='paused';value['message']='La app se cerró o el controlador se interrumpió. Revisa los trabajos antes de reanudar.'
            for item in value['items']:
                if item['status'] in ('starting','running'):item['status']='interrupted'
            _save(value)
        return {**value,'projects_root':str(studio.PROJECTS_DIR.resolve()),'worker_active':WORKER is not None,'automatic_restart':False}


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
