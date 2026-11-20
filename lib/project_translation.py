"""Explicit project translation task; shares the existing single-workload slot."""
import threading
from lib import production_studio as studio,production_agent as agent,reference_analysis


def read(project_id):
    path=studio.project_path(project_id)
    report=studio.read_json(path/'translation_task.json',{'status':'not_started'})
    with agent.ACTIVE_LOCK:
        if report.get('status')=='running' and project_id not in agent.ACTIVE:
            return {**report,'status':'interrupted','message':'La tarea se interrumpió; reenvía el mismo texto para recuperar fragmentos guardados'}
    return report


def start(project_id,data):
    if set(data)!={'text'} or not isinstance(data['text'],str) or not data['text'].strip() or len(data['text'])>50000:raise ValueError('Indica un texto de entre 1 y 50000 caracteres')
    path=studio.project_path(project_id)
    language=studio.read_json(path/'production_request.json')['language']
    output=path/'translations'/'madlad'
    cancel=threading.Event()
    def work():
        try:
            from tools.models.local_adapters import model_madlad
            result=model_madlad().execute({'text':data['text'],'language':language,'output_dir':str(output),'device':'cpu','max_new_tokens':2048,'timeout':3600})
            if not result.success:raise ValueError(result.error)
            translated=(result.data or {}).get('result',{})
            if not isinstance(translated.get('text'),str) or not translated['text'].strip():raise ValueError('El motor no devolvió texto traducido')
            studio.save_json(path/'translation_task.json',{'status':'completed','language':language,'finished_at':studio.now(),
                'text':translated.get('text',''),'segments':translated.get('segments',[]),'resumed_segments':translated.get('resumed_segments',0),
                'quality_review_required':True,'production_started':False})
        except Exception as exc:
            studio.save_json(path/'translation_task.json',{'status':'failed','language':language,'finished_at':studio.now(),'message':str(exc)[:1800],'production_started':False})
        finally:
            with agent.ACTIVE_LOCK:
                if agent.ACTIVE.get(project_id,(None,None))[1] is cancel:agent.ACTIVE.pop(project_id,None)
    thread=threading.Thread(target=work,daemon=True,name='project-translation')
    with agent.ACTIVE_LOCK,reference_analysis.LOCK:
        if agent.ACTIVE or reference_analysis.ACTIVE:raise ValueError('Espera a que termine la tarea local activa')
        studio.save_json(path/'translation_task.json',{'status':'running','language':language,'started_at':studio.now(),'production_started':False})
        agent.ACTIVE[project_id]=(thread,cancel)
        try:thread.start()
        except Exception:
            agent.ACTIVE.pop(project_id,None);raise
    return {'started':True,'language':language,'device':'cpu','production_started':False}
