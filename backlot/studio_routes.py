"""Local production control surface; publishing is deliberately separate."""
import asyncio
import json
import hmac
import secrets
from tempfile import TemporaryDirectory
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse,FileResponse
from starlette.background import BackgroundTask
from lib import production_studio as studio
from lib import production_agent as agent


def create_studio_router():
    router=APIRouter()
    round_export_key = secrets.token_bytes(32)

    def round_signature(report):
        payload = json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False)
        return hmac.digest(round_export_key, payload.encode('utf-8'), 'sha256').hex()

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
    @router.get('/api/studio/queue')
    def production_queue_state():
        from lib.production_queue import read
        return invoke(read)
    @router.get('/api/studio/queue/inspect')
    def production_queue_inspection():
        from lib.production_queue import inspect
        return invoke(inspect)
    @router.get('/api/studio/production-metrics')
    def production_metrics():
        from lib.production_metrics import snapshot
        return invoke(snapshot)
    @router.post('/api/studio/queue/{action}')
    async def production_queue_action(action:str,request:Request):
        from lib import production_queue
        data=await body(request)
        if action=='freeze-pilot':
            if data:raise HTTPException(400,'Esta acción no admite parámetros')
            return invoke(production_queue.freeze_pilot)
        if action in ('start','pause'):
            if data:raise HTTPException(400,'Esta acción no admite parámetros')
            return invoke(getattr(production_queue,action))
        if action=='enqueue-batch' and set(data)=={'project_ids'}:return invoke(production_queue.enqueue_many,data['project_ids'])
        if action=='enqueue' and set(data)=={'project_id'} and isinstance(data['project_id'],str):return invoke(production_queue.enqueue,data['project_id'])
        if action=='retry' and set(data)=={'id'} and isinstance(data['id'],str):return invoke(production_queue.retry,data['id'])
        if action=='remove' and set(data)=={'id'} and isinstance(data['id'],str):return invoke(production_queue.edit,data['id'])
        if action=='move' and set(data)=={'id','direction'} and isinstance(data['id'],str) and isinstance(data['direction'],str):return invoke(production_queue.edit,data['id'],data['direction'])
        raise HTTPException(400,'Acción de cola inválida')
    @router.get('/api/studio/finals')
    def final_outputs_catalog():
        from lib.final_catalog import catalog
        return invoke(catalog)
    @router.get('/api/studio/finals/{pid}/integrity')
    def final_integrity(pid:str):
        from lib.final_integrity import inspect
        return invoke(inspect,pid)
    @router.get('/api/studio/finals/{pid}/sources')
    def final_sources(pid:str):
        from lib.final_source_trace import inspect
        return invoke(inspect,pid)
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
    @router.get('/api/studio/translation/{pid}')
    def project_translation_state(pid:str):
        from lib.project_translation import read
        return invoke(read,pid)
    @router.post('/api/studio/translation/{pid}')
    async def project_translation_start(pid:str,request:Request):
        from lib.project_translation import start
        return invoke(start,pid,await body(request,250000))
    @router.post('/api/studio/reference-reuse/{pid}')
    async def reuse_reference_analysis(pid:str,request:Request):
        from lib.reference_reuse import reuse
        data=await body(request)
        if set(data)!={'project_ids'}:raise HTTPException(400,'Indica solo project_ids')
        return invoke(reuse,pid,data['project_ids'])
    @router.get('/api/studio/reference-language/{pid}')
    def reference_language_state(pid:str):
        from lib.reference_language import read
        return invoke(read,pid)
    @router.post('/api/studio/reference-language/{pid}')
    async def reference_language_confirm(pid:str,request:Request):
        from lib.reference_language import confirm
        from lib import reference_analysis
        data=await body(request)
        if set(data)!={'language'}:raise HTTPException(400,'Indica solo language')
        with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
            if agent.ACTIVE or reference_analysis.ACTIVE:raise HTTPException(409,'Espera a que termine la tarea local')
            return invoke(confirm,pid,data['language'])
    @router.get('/api/studio/language-requirements/{pid}')
    def language_requirements(pid:str):
        from lib.language_versions import local_requirements
        return invoke(local_requirements,pid)
    @router.get('/api/studio/language-versions/{pid}')
    def language_versions_list(pid:str):
        from lib.language_versions import list_versions
        return invoke(list_versions,pid)
    @router.post('/api/studio/language-versions/{pid}')
    async def language_versions(pid:str,request:Request):
        from lib.language_versions import create_versions
        data=await body(request)
        if set(data)!={'languages'}:raise HTTPException(400,'Indica solo languages')
        return invoke(create_versions,pid,data['languages'])
    @router.get('/api/studio/scene-batch-plan/{pid}')
    def scene_batch_plan(pid:str):
        from lib.scene_batch import approved_plan
        return invoke(approved_plan,pid)
    @router.get('/api/studio/scene-batch/{pid}')
    def scene_batch_read(pid:str):
        from lib.scene_batch import read
        return invoke(read,pid)
    @router.post('/api/studio/scene-batch/{pid}')
    async def scene_batch_prepare(pid:str,request:Request):
        from lib.scene_batch import prepare
        return invoke(prepare,pid,await body(request,250000))
    @router.post('/api/studio/scene-batch-media/{pid}')
    async def scene_batch_media(pid:str,request:Request):
        from lib.scene_batch import record_media
        return invoke(record_media,pid,await body(request))
    @router.post('/api/studio/scene-batch-approve/{pid}')
    async def scene_batch_approve(pid:str,request:Request):
        from lib.scene_batch import approve_take
        return invoke(approve_take,pid,await body(request))
    @router.post('/api/studio/scene-batch-preview/{pid}')
    async def scene_batch_preview(pid:str,request:Request):
        from lib.scene_batch import start_preview
        data=await body(request)
        if set(data)!={'scene_id'}:raise HTTPException(400,'Indica la escena')
        return invoke(start_preview,pid,data['scene_id'])
    @router.get('/api/studio/scene-edit-readiness/{pid}')
    def scene_edit_readiness(pid:str):
        from lib.scene_edit import readiness
        return invoke(readiness,pid)
    @router.get('/api/studio/scene-edit-preview/{pid}')
    def scene_edit_preview_state(pid:str):
        from lib.scene_preview import state
        return invoke(state,pid)
    @router.post('/api/studio/scene-edit-preview/{pid}')
    async def scene_edit_preview_start(pid:str,request:Request):
        from lib.scene_preview import start
        data=await body(request)
        if set(data)!={'fit_policy'}:raise HTTPException(400,'Indica la política de duración')
        return invoke(start,pid,data['fit_policy'])
    @router.get('/api/studio/scene-audio-preview/{pid}')
    def scene_audio_preview_state(pid:str):
        from lib.scene_audio_preview import state
        return invoke(state,pid)
    @router.post('/api/studio/scene-audio-preview/{pid}')
    async def scene_audio_preview_start(pid:str,request:Request):
        from lib.scene_audio_preview import start
        return invoke(start,pid,await body(request))
    @router.post('/api/studio/scene-subtitles-inspect/{pid}')
    async def scene_subtitles_inspect(pid:str,request:Request):
        from lib.scene_subtitles import inspect
        data=await body(request)
        if set(data)!={'srt_path'}:raise HTTPException(400,'Indica el archivo SRT')
        return invoke(inspect,pid,data['srt_path'])
    @router.get('/api/studio/scene-subtitles/{pid}')
    def scene_subtitles_state(pid:str):
        from lib.scene_subtitles import state
        return invoke(state,pid)
    @router.post('/api/studio/scene-subtitles/{pid}')
    async def scene_subtitles_start(pid:str,request:Request):
        from lib.scene_subtitles import start
        return invoke(start,pid,await body(request))
    @router.get('/api/studio/scene-burned-subtitles/{pid}')
    def scene_burned_subtitles_state(pid:str):
        from lib.scene_burned_subtitles import state
        return invoke(state,pid)
    @router.post('/api/studio/scene-burned-subtitles/{pid}')
    def scene_burned_subtitles_start(pid:str):
        from lib.scene_burned_subtitles import start
        return invoke(start,pid)
    @router.get('/api/studio/projects/{pid}')
    def project(pid:str):
        state=invoke(studio.production_state,pid)
        with agent.ACTIVE_LOCK:active=pid in agent.ACTIVE
        state['active']=active
        if state['job'].get('status')=='running' and not active:
            state['job'].update(status='interrupted',message='El proceso anterior terminó. Puedes reanudar desde los artefactos guardados.')
        return state
    @router.get('/api/studio/script-diagnostic/{pid}')
    def script_diagnostic(pid:str,words_per_minute:int=Query(150,ge=80,le=220)):
        from lib.script_diagnostic import inspect
        return invoke(inspect,pid,words_per_minute)
    @router.get('/api/studio/script-outline/{pid}')
    def script_outline_read(pid:str):
        from lib.script_outline import read
        return invoke(read,pid)
    @router.post('/api/studio/script-outline/{pid}')
    async def script_outline_save(pid:str,request:Request):
        from lib.script_outline import save
        return invoke(save,pid,await body(request,35000))
    @router.get('/api/studio/packaging-options/{pid}')
    def packaging_options_read(pid:str):
        from lib.packaging_options import read
        return invoke(read,pid)
    @router.post('/api/studio/packaging-options/{pid}')
    async def packaging_options_save(pid:str,request:Request):
        from lib.packaging_options import save
        return invoke(save,pid,await body(request,12000))
    @router.get('/api/studio/project-thumbnail/{pid}')
    def project_thumbnail_read(pid:str):
        from lib.project_thumbnail import current
        return invoke(current,pid)
    @router.post('/api/studio/project-thumbnail/{pid}')
    async def project_thumbnail_stage(pid:str,request:Request):
        from lib.project_thumbnail import stage
        data=await body(request,11000000)
        with agent.ACTIVE_LOCK:
            if pid in agent.ACTIVE:raise HTTPException(409,'Detén los agentes antes de cambiar la miniatura')
            return invoke(stage,pid,data)
    @router.get('/api/studio/asset-sources/{pid}')
    def asset_sources_read(pid:str):
        from lib.project_asset_sources import read
        return invoke(read,pid)
    @router.post('/api/studio/asset-sources/{pid}')
    async def asset_sources_save(pid:str,request:Request):
        from lib.project_asset_sources import save
        return invoke(save,pid,await body(request,6000))
    @router.get('/api/studio/asset-coverage/{pid}')
    def asset_coverage(pid:str,offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50)):
        from lib.project_asset_sources import coverage
        return invoke(coverage,pid,offset,limit)
    @router.get('/api/studio/asset-usage/{pid}')
    def asset_usage(pid:str,offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50)):
        from lib.project_asset_sources import usage
        return invoke(usage,pid,offset,limit)
    @router.get('/api/studio/channel-research/{pid}')
    def channel_research_page(pid:str,offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50)):
        from lib.project_channel_evidence import page
        path=invoke(studio.project_path,pid)
        return invoke(page,path,studio.read_json(path/'production_request.json'),offset,limit)
    @router.get('/api/studio/vidiq-observations/{pid}')
    def vidiq_observations_page(pid:str,offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50)):
        from lib.project_video_observations import page
        path=invoke(studio.project_path,pid)
        return invoke(page,path,studio.read_json(path/'production_request.json'),offset,limit)
    @router.get('/api/studio/channel-performance/{pid}')
    def channel_performance_page(pid:str,offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50)):
        from lib.project_channel_performance import page
        path=invoke(studio.project_path,pid)
        return invoke(page,path,studio.read_json(path/'production_request.json'),offset,limit)
    @router.post('/api/studio/projects/{pid}/restore-channel-research')
    async def restore_channel_research(pid:str,request:Request):
        if await body(request):raise HTTPException(400,'Esta acción no admite parámetros')
        from lib.project_channel_evidence import restore_missing
        return invoke(restore_missing,pid)
    @router.post('/api/studio/projects/{pid}/{action}')
    async def action(pid:str,action:str,request:Request):
        await body(request)
        fn={'start':agent.start,'resume':agent.start,'stop':agent.stop,'approve':agent.approve}.get(action)
        if fn is None:raise HTTPException(404,'Acción desconocida')
        return invoke(fn,pid)
    @router.post('/api/studio/revision/{pid}')
    async def revision(pid:str,request:Request):
        data=await body(request)
        if set(data)!={'reason'}:raise HTTPException(400,'Indica solo reason')
        return invoke(agent.request_revision,pid,data['reason'])
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
    @router.get('/api/studio/download-plan')
    def pending_download_plan():
        from lib.download_plan import plan
        return invoke(plan)
    @router.get('/api/studio/football/schema')
    def football_schema():
        from lib.football_research import schema
        return invoke(schema)
    @router.post('/api/studio/football/query')
    async def football_query(request:Request):
        from lib.football_research import query
        data=await body(request)
        return await asyncio.to_thread(lambda:invoke(query,data))
    @router.get('/api/studio/football/desk-editions')
    def football_desk_editions():
        from lib.world_cup_edition_desk import DEFAULT_EDITION, edition_options
        return {'default': DEFAULT_EDITION, 'editions': edition_options()}

    @router.post('/api/studio/football/round-goals')
    async def football_round_goals(request: Request):
        from jsonschema import ValidationError, validate
        from lib.world_cup_rounds import PROPERTIES
        from lib.world_cup_open_goals import compare
        from tools.graphics.sports_card import render
        from lib.world_cup_edition_desk import DEFAULT_EDITION, EDITIONS, compare_edition, can_export_selection

        data = await body(request)
        try:
            properties = {**PROPERTIES, 'round': {'enum': ['edition', *PROPERTIES['round']['enum']]},
                          'edition': {'enum': list(EDITIONS)}}
            edition = data.get('edition', DEFAULT_EDITION)
            if data.get('round') == 'edition' and edition != DEFAULT_EDITION:
                players = PROPERTIES['players']
                properties['players'] = {**players, 'items': {**players['items'], 'required': ['name']}}
            validate(data, {'type': 'object', 'properties': properties,
                            'required': ['round', 'players'], 'additionalProperties': False})
        except ValidationError as exc:
            raise HTTPException(400, exc.message) from exc
        if data['round'] == 'edition':
            call = lambda: invoke(compare_edition, data['players'], edition)
            result = await asyncio.to_thread(call)
            report = result['report']
            return {**result, 'export_token': round_signature(report)
                    if can_export_selection(report, result['display_metrics'], result.get('errors', [])) else None}

        if edition != DEFAULT_EDITION:
            raise HTTPException(400, 'El desglose por ronda está disponible para Qatar 2022')
        try:
            report = await asyncio.to_thread(lambda: invoke(lambda: compare(data['round'], data['players'])))
        except OSError as exc:
            raise HTTPException(502, 'No se pudo consultar OpenFootball') from exc
        preview = invoke(render, report, ['goals']) if report['ready_for_script'] else None
        return {'report': report, 'preview_svg': preview,
                'display_metrics': ['goals'] if preview else [],
                'export_token': round_signature(report) if preview else None}

    async def verified_round_selection(request):
        from jsonschema import ValidationError, validate
        from tools.graphics.sports_card import METRIC_SELECTION

        data = await body(request, limit=256000)
        report, token = data.get('report'), data.get('export_token')
        metrics = data.get('metrics', ['goals'])
        if (set(data) - {'report', 'export_token', 'metrics'} or not isinstance(report, dict)
                or not isinstance(token, str) or len(token) != 64 or not token.isascii()):
            raise HTTPException(400, 'Se requiere una comparativa verificada')
        signature = invoke(round_signature, report)
        if not hmac.compare_digest(token, signature):
            raise HTTPException(400, 'La comparativa cambió o la sesión se reinició. Vuelve a consultarla.')
        try:
            validate(metrics, METRIC_SELECTION)
        except ValidationError as exc:
            raise HTTPException(400, exc.message) from exc
        return report, metrics

    def round_filename(report, extension):
        scope = report['scope']
        if report.get('source') == 'FIFA':
            return f"fifa-{scope['competition_id']}-{scope['season_id']}.{extension}"
        competition = scope.get('competition', report.get('competition', 'uefa'))
        season = scope.get('season', scope.get('seasonYear'))
        return f"{competition}-{season}-{scope.get('round', scope['phase'])}.{extension}"

    @router.post('/api/studio/football/round-goals/preview')
    async def football_round_preview(request: Request):
        from tools.graphics.sports_card import render

        report, metrics = await verified_round_selection(request)
        return {'preview_svg': invoke(render, report, metrics)}

    @router.post('/api/studio/football/round-goals/dossier')
    async def football_round_dossier(request: Request):
        from lib.football_comparison_dossier import build

        report, metrics = await verified_round_selection(request)
        return invoke(build, report, metrics)

    @router.post('/api/studio/football/round-goals/projects/{pid}')
    async def football_round_save_project(pid: str, request: Request):
        from lib.football_comparison_dossier import save_to_project

        report, metrics = await verified_round_selection(request)
        return invoke(save_to_project, pid, report, metrics)

    @router.post('/api/studio/football/round-goals/video')
    async def football_round_video(request: Request):
        from tools.graphics.sports_card_video import SportsCardVideo

        report, metrics = await verified_round_selection(request)
        folder = TemporaryDirectory(prefix='openmontage-round-')
        output = Path(folder.name) / 'round.mp4'
        try:
            result = await asyncio.to_thread(SportsCardVideo().execute, {
                'report': report, 'metrics': metrics, 'output_path': str(output), 'duration_seconds': 6,
            })
            if not result.success:
                raise HTTPException(422, result.error)
            return FileResponse(output, media_type='video/mp4',
                                filename=round_filename(report, 'mp4'),
                                background=BackgroundTask(folder.cleanup))
        except Exception:
            folder.cleanup()
            raise

    @router.get('/api/studio/resources')
    def resources():return studio.resource_catalog()
    @router.get('/api/studio/updates')
    def update_targets(offset:int=0,limit:int=10):
        from lib.update_center import targets
        return invoke(targets,offset,limit)
    @router.get('/api/studio/updates/check')
    def update_check(kind:str,identifier:str):
        from lib.update_center import check
        return invoke(check,kind,identifier)
    @router.get('/api/studio/updates/discover')
    def update_discover(kind:str,query:str):
        from lib.update_center import discover
        return invoke(discover,kind,query)
    @router.get('/api/studio/updates/files')
    def update_files(identifier:str,offset:int=0,limit:int=10):
        from lib.update_center import files
        return invoke(files,identifier,offset,limit)
    @router.get('/api/studio/updates/local-check')
    def update_local_check(identifier:str,index:int):
        from lib.update_center import check_local
        return invoke(check_local,identifier,index)
    @router.get('/api/studio/integration-coverage')
    def integration_coverage():
        from lib.integration_coverage import coverage
        return coverage()
    @router.get('/api/studio/applications')
    def applications():
        from lib.external_applications import catalog
        return {'applications':catalog()}
    @router.post('/api/studio/applications/{identifier}')
    async def application_configure(identifier:str,request:Request):
        from lib.external_applications import configure
        from lib import reference_analysis
        data=await body(request)
        with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
            if agent.ACTIVE or reference_analysis.ACTIVE:raise HTTPException(409,'Espera a que terminen las tareas antes de cambiar herramientas')
            return invoke(configure,identifier,data)
    @router.post('/api/studio/applications/{identifier}/launch')
    async def application_launch(identifier:str,request:Request):
        from lib.external_applications import launch
        data=await body(request)
        if set(data)-{'project_id','file'} or not isinstance(data.get('project_id'),str) or ('file' in data and not isinstance(data['file'],str)):raise HTTPException(400,'Indica proyecto y archivo opcional')
        return invoke(launch,identifier,data['project_id'],data.get('file'))
    @router.get('/api/studio/storage')
    def storage():
        from lib.storage_layout import describe
        return invoke(describe,studio.REPO_ROOT,studio.PROJECTS_DIR)
    @router.post('/api/studio/final-delivery/{pid}/retry')
    async def retry_final_delivery(pid:str,request:Request):
        from lib.final_delivery import retry_verified_delivery
        from lib import reference_analysis
        import threading
        if await body(request):raise HTTPException(400,'La recuperación no admite rutas ni parámetros')
        invoke(studio.project_path,pid)
        token=threading.Event()
        # Reserve the producer task slot, but do not start an AI agent. Locks
        # protect only the reservation, never a potentially long disk copy.
        with agent.ACTIVE_LOCK,reference_analysis.LOCK:
            if agent.ACTIVE or reference_analysis.ACTIVE:raise HTTPException(409,'Espera a que terminen las tareas antes de recuperar la entrega')
            agent.ACTIVE[pid]=(None,token)
        try:
            return await asyncio.to_thread(lambda:invoke(retry_verified_delivery,pid))
        finally:
            with agent.ACTIVE_LOCK:
                if agent.ACTIVE.get(pid,(None,None))[1] is token:agent.ACTIVE.pop(pid,None)
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
    @router.get('/api/studio/setup')
    def setup_report():
        from lib.setup_center import report
        return invoke(report)
    @router.post('/api/studio/setup/report')
    async def save_setup_report(request:Request):
        from lib.setup_center import save_report
        if await body(request):raise HTTPException(400,'El informe no necesita argumentos')
        return await asyncio.to_thread(save_report)
    @router.post('/api/studio/setup/discover')
    async def discover_setup(request:Request):
        from lib.setup_center import discover
        data=await body(request)
        return await asyncio.to_thread(lambda:invoke(discover,data))
    @router.get('/api/studio/setup/runtime/{family}')
    def runtime_settings(family:str):
        from lib.setup_center import read_runtime_settings
        return invoke(read_runtime_settings,family)
    @router.post('/api/studio/setup/runtime/{family}')
    async def configure_runtime_settings(family:str,request:Request):
        from lib.setup_center import save_runtime_settings
        from lib import reference_analysis
        data=await body(request)
        with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
            if agent.ACTIVE or reference_analysis.ACTIVE:raise HTTPException(409,'Espera a que terminen las tareas antes de cambiar el motor')
            return invoke(save_runtime_settings,family,data)
    @router.post('/api/studio/adapters/{family}')
    async def bind_adapter(family:str,request:Request):
        from lib.model_adapters import configure
        data=await body(request)
        with agent.ACTIVE_LOCK:
            if agent.ACTIVE:raise HTTPException(409,'Detén la producción antes de cambiar adaptadores')
            return invoke(configure,family,data)
    @router.get('/api/studio/workflow-recipes')
    def workflow_recipes():
        from lib.workflow_preparation import recipes
        return recipes()
    @router.post('/api/studio/adapters/{family}/prepare')
    async def prepare_adapter_workflow(family:str,request:Request):
        from lib.workflow_preparation import prepare
        data=await body(request)
        from lib import reference_analysis
        with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
            if agent.ACTIVE or reference_analysis.ACTIVE:raise HTTPException(409,'Espera a que terminen las tareas locales antes de preparar workflows')
            return invoke(prepare,family,data)
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
