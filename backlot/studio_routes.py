"""Local production control surface; publishing is deliberately separate."""
import asyncio
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse,FileResponse
from lib import production_studio as studio
from lib import production_agent as agent


def create_studio_router():
    router=APIRouter()
    async def body(request,limit=20000):
        origin=request.headers.get('origin')
        if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):
            raise HTTPException(403,'Origen no autorizado')
        chunks=[];size=0
        async for chunk in request.stream():
            size+=len(chunk)
            if size>limit:raise HTTPException(413,'Solicitud demasiado grande')
            chunks.append(chunk)
        try:
            value=json.loads(b''.join(chunks))
            if not isinstance(value,dict):raise ValueError()
            return value
        except (ValueError,UnicodeError):raise HTTPException(400,'Se requiere un objeto JSON')
    def invoke(fn,*args):
        try:return fn(*args)
        except FileNotFoundError as exc:raise HTTPException(404,str(exc))
        except (ValueError,KeyError,TypeError) as exc:raise HTTPException(400,str(exc))
    @router.get('/studio',response_class=HTMLResponse)
    def page():return (Path(__file__).parent/'ui'/'studio.html').read_text()
    @router.get('/api/studio/bootstrap')
    def bootstrap():
        projects=[]
        for f in studio.PROJECTS_DIR.glob('*/production_request.json'):
            r=studio.read_json(f);projects.append({'project_id':r['project_id'],'title':r['title']})
        return {'settings':studio.settings(),'pipelines':studio.pipelines(),'projects':projects}
    @router.get('/api/studio/runtime')
    async def runtime():return await asyncio.to_thread(studio.runtime_status)
    @router.post('/api/studio/settings')
    async def settings(request:Request):
        data=await body(request)
        with agent.ACTIVE_LOCK:
            if agent.ACTIVE:raise HTTPException(409,'Detén la producción antes de cambiar el runtime')
            return invoke(studio.configure,data)
    @router.post('/api/studio/projects')
    async def create(request:Request):return invoke(studio.create_production,await body(request))
    @router.get('/api/studio/projects/{pid}')
    def project(pid:str):
        state=invoke(studio.production_state,pid)
        with agent.ACTIVE_LOCK:active=pid in agent.ACTIVE
        state['active']=active
        if state['job'].get('status')=='running' and not active:
            state['job'].update(status='interrupted',message='El proceso anterior terminó. Puedes reanudar desde los artefactos guardados.')
        return state
    @router.post('/api/studio/projects/{pid}/{action}')
    async def action(pid:str,action:str,request:Request):
        await body(request)
        fn={'start':agent.start,'resume':agent.start,'stop':agent.stop,'approve':agent.approve}.get(action)
        if fn is None:raise HTTPException(404,'Acción desconocida')
        return invoke(fn,pid)
    @router.post('/api/studio/clarifications/{pid}')
    async def clarify(pid:str,request:Request):
        data=await body(request)
        text=data.get('message')
        if not isinstance(text,str) or not 1<=len(text.strip())<=12000:raise HTTPException(400,'Escribe la aclaración')
        p=invoke(studio.project_path,pid)
        with agent.ACTIVE_LOCK:
            if pid in agent.ACTIVE:raise HTTPException(409,'Detén los agentes antes de añadir instrucciones')
            values=studio.read_json(p/'user_clarifications.json',[])
            values.append({'at':studio.now(),'message':text})
            studio.save_json(p/'user_clarifications.json',values[-30:])
        return {'saved':True}
    @router.get('/api/studio/resources')
    def resources():return studio.resource_catalog()
    @router.get('/api/studio/storage')
    def storage():
        from lib.storage_layout import describe
        return invoke(describe,studio.REPO_ROOT,studio.PROJECTS_DIR)
    @router.get('/api/studio/storage/readiness')
    def storage_readiness():
        from lib.storage_layout import readiness
        return invoke(readiness,studio.REPO_ROOT,studio.PROJECTS_DIR)
    @router.post('/api/studio/storage')
    async def storage_configure(request:Request):
        from lib.storage_layout import configure
        from lib import reference_analysis
        data=await body(request)
        with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
            if agent.ACTIVE or reference_analysis.ACTIVE:raise HTTPException(409,'Espera a que terminen las tareas antes de cambiar el almacenamiento')
            return invoke(configure,studio.REPO_ROOT,data,studio.save_json)
    @router.post('/api/studio/inventories')
    async def inventory(request:Request):return invoke(studio.import_inventory,await body(request,32000000))
    @router.get('/api/studio/wan-presets')
    def wan_presets():
        from lib.wan_presets import catalog
        from lib.model_adapters import configuration
        return {'presets':catalog(),'current':configuration('wan')}
    @router.post('/api/studio/comfy-history/report')
    async def comfy_history_report(request:Request):
        from lib.comfy_history_report import summarize_history
        history=await body(request,8000000)
        return {'jobs':invoke(summarize_history,history),'source':'uploaded_history','persisted':False}
    @router.get('/api/studio/comfy-history/projects/{pid}')
    def comfy_saved_reports(pid:str):
        from lib.comfy_history_report import saved_reports
        return {'reports':invoke(saved_reports,pid)}
    @router.post('/api/studio/comfy-history/projects/{pid}')
    async def comfy_save_report(pid:str,request:Request):
        from lib.comfy_history_report import save_report
        return invoke(save_report,pid,await body(request,8000000))
    @router.post('/api/studio/comfy-history/projects/{pid}/{report_id}/context')
    async def comfy_report_context(pid:str,report_id:str,request:Request):
        from lib.comfy_history_report import annotate_report
        return invoke(annotate_report,pid,report_id,await body(request))
    @router.post('/api/studio/source-images/{pid}')
    async def source_image(pid:str,request:Request):
        from lib.production_input_image import stage_image
        data=await body(request,11000000)
        with agent.ACTIVE_LOCK:
            if pid in agent.ACTIVE:raise HTTPException(409,'Detén los agentes del proyecto antes de cambiar su imagen de entrada')
            return invoke(stage_image,pid,data)
    @router.get('/api/studio/source-images/{pid}')
    def source_image_current(pid:str):
        from lib.production_input_image import current_image
        return {'image':invoke(current_image,pid)}
    @router.get('/api/studio/comfy-jobs/{pid}')
    def comfy_project_jobs(pid:str):
        from lib.comfy_job_records import project_jobs
        return invoke(project_jobs,pid)
    @router.get('/api/studio/reference-runtime')
    def reference_runtime():
        from lib.reference_analysis import runtime
        return runtime()
    @router.post('/api/studio/reference-video/{pid}/upload')
    async def reference_video_upload(pid:str,request:Request):
        import uuid
        from lib import reference_analysis as analysis
        origin=request.headers.get('origin')
        if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):raise HTTPException(403,'Origen no autorizado')
        folder=invoke(studio.project_path,pid)
        temp=folder/('reference-upload-'+uuid.uuid4().hex+'.tmp');size=0
        try:
            with temp.open('xb') as stream:
                async for chunk in request.stream():
                    size+=len(chunk)
                    if size>500000000:raise HTTPException(413,'Video demasiado grande: máximo 500 MB')
                    stream.write(chunk)
            if not size:raise HTTPException(400,'Video vacío')
            with agent.ACTIVE_LOCK,analysis.LOCK:
                if agent.ACTIVE or analysis.ACTIVE:raise HTTPException(409,'Hay una tarea local activa; no se reemplazó el video')
                temp.replace(folder/'reference_video.mp4')
                studio.save_json(folder/'reference_source.json',{'path':'reference_video.mp4'})
                studio.save_json(folder/'reference_analysis.json',{'status':'not_started','message':'Video cargado, análisis pendiente','bytes':size})
            return {'uploaded':True,'bytes':size,'analysis_started':False}
        finally:temp.unlink(missing_ok=True)
    @router.post('/api/studio/reference-video/{pid}/analyze')
    async def reference_video_analyze(pid:str,request:Request):
        from lib.reference_analysis import start
        return invoke(start,pid,await body(request))
    @router.get('/api/studio/reference-video/{pid}')
    def reference_video_report(pid:str):
        from lib.reference_analysis import read
        return invoke(read,pid)
    @router.get('/api/studio/adapters')
    async def adapters():
        from lib.model_adapters import CATALOG,diagnostics,dependency_probe
        dependency_probe.cache_clear()
        return await asyncio.to_thread(lambda:[diagnostics(family) for family in CATALOG])
    @router.post('/api/studio/adapters/{family}')
    async def bind_adapter(family:str,request:Request):
        from lib.model_adapters import configure
        data=await body(request)
        with agent.ACTIVE_LOCK:
            if agent.ACTIVE:raise HTTPException(409,'Detén la producción antes de cambiar adaptadores')
            return invoke(configure,family,data)
    @router.get('/api/studio/validations')
    def validations():
        from lib import model_validation as checks
        paths=sorted(checks.root().glob('check-*/report.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]
        return [invoke(checks.read,p.parent.name) for p in paths]
    @router.post('/api/studio/validations')
    async def start_validation(request:Request):
        from lib import model_validation as checks
        return invoke(checks.start,await body(request))
    @router.get('/api/studio/validations/{identifier}')
    def validation(identifier:str):
        from lib import model_validation as checks
        return invoke(checks.read,identifier)
    @router.get('/api/studio/validations/{identifier}/audio')
    def validation_audio(identifier:str):
        from lib import model_validation as checks
        path=invoke(checks.folder,identifier)/'voice/voice.wav'
        if not path.is_file():raise HTTPException(404,'Audio no disponible')
        return FileResponse(path,media_type='audio/wav')
    @router.post('/api/studio/validations/{identifier}/review')
    async def validation_review(identifier:str,request:Request):
        from lib import model_validation as checks
        return invoke(checks.review,identifier,await body(request))
    @router.get('/api/studio/tools')
    async def tools():
        def discover():
            from tools.tool_registry import registry
            registry.ensure_discovered()
            return [{'name':t.name,'capability':t.capability,'runtime':t.runtime.value,'status':t.get_status().value,
                     'install_instructions':t.install_instructions} for t in registry._tools.values() if agent.LocalAgent.permitted(t)]
        return await asyncio.to_thread(discover)
    return router
