"""Explicit project translation task; shares the existing single-workload slot."""
import threading
from lib import production_studio as studio,production_agent as agent,reference_analysis


def read(project_id):
    path=studio.project_path(project_id)
    report=studio.read_json(path/'translation_task.json',{'status':'not_started'})
    with agent.ACTIVE_LOCK:
        active=agent.ACTIVE.get(project_id)
        translation_active=bool(active and active[0] is not None and getattr(active[0],'name','')=='project-translation')
        if report.get('status')=='running' and not translation_active:
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


def summary(project_id):
    report=read(project_id)
    return {'status':report['status'],'language':report.get('language'),
        'segments_count':len(report.get('segments',[])),'saved_translation_available':report['status']=='completed',
        'quality_review_required':True,'message':report.get('message','')}


def read_for_agent(project_id,offset=0,limit=10):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=20:raise ValueError('Usa offset no negativo y limit de 1 a 20')
    report=read(project_id);result=summary(project_id)
    if report['status']!='completed':return {**result,'segments':[],'next_offset':None}
    segments=report.get('segments') or ([{'index':0,'translation':report.get('text','')}] if report.get('text') else [])
    selected=[];used=0;end=offset
    for item in segments[offset:offset+limit]:
        size=len(str(item.get('translation','')))+len(str(item.get('text','')))
        if used+size>24000:
            if not selected:raise ValueError('Fragmento demasiado grande para esta consulta; revísalo desde el panel')
            break
        selected.append(item);used+=size;end+=1
    return {**result,'segments_count':len(segments),'segments':selected,
        'offset':offset,'next_offset':end if end<len(segments) else None,
        'note':'Traducción guardada, pendiente de revisión lingüística y cultural. No sustituye un guion aprobado ni inicia trabajo.'}
