"""Local production control surface; publishing is deliberately separate."""
import asyncio
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
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
    @router.post('/api/studio/inventories')
    async def inventory(request:Request):return invoke(studio.import_inventory,await body(request,32000000))
    @router.get('/api/studio/tools')
    async def tools():
        def discover():
            from tools.tool_registry import registry
            registry.ensure_discovered()
            return [{'name':t.name,'capability':t.capability,'runtime':t.runtime.value,'status':t.get_status().value,
                     'install_instructions':t.install_instructions} for t in registry._tools.values() if agent.LocalAgent.permitted(t)]
        return await asyncio.to_thread(discover)
    return router
