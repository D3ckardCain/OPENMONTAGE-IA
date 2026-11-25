"""Manual editing HTTP surface. All mutations use the agent's shared contract."""
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from lib import production_studio as studio, studio_editor as editor, studio_editor_render as render
from backlot.studio_identity import capabilities as editor_capabilities


def create_editor_router(body):
    router = APIRouter(prefix='/api/studio/editor')

    def invoke(fn, *args):
        try:
            return fn(*args)
        except editor.Conflict as exc:
            raise HTTPException(409, str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.get('/capabilities')
    def capabilities():
        return editor_capabilities()

    @router.get('/piper/voices')
    def piper_voices():
        from lib.studio_piper import catalog
        return invoke(catalog)

    @router.post('/{pid}/piper/preview')
    async def piper_preview(pid: str, request: Request):
        from starlette.concurrency import run_in_threadpool
        from lib.studio_piper import preview
        data = await body(request, 8000)
        return await run_in_threadpool(invoke, preview, pid, data)

    @router.get('/{pid}/piper/audio/{filename}')
    def piper_audio(pid: str, filename: str):
        if not filename.startswith('piper-') or Path(filename).name != filename or not filename.endswith('.wav'):
            raise HTTPException(400, 'Invalid preview')
        return FileResponse(invoke(studio.project_path, pid) / 'assets' / 'audio' / filename, media_type='audio/wav')

    @router.get('/projects')
    def projects():
        return [{'project_id': p.parent.name, 'title': studio.read_json(p).get('title', p.parent.name)}
                for p in studio.PROJECTS_DIR.glob('*/production_request.json')
                if studio.read_json(p).get('manual_edit')]

    @router.post('/projects')
    async def create(request: Request):
        data = await body(request)
        return invoke(editor.create, data.get('title'))

    @router.get('/{pid}')
    def state(pid: str):
        return invoke(editor.state, pid)

    @router.post('/{pid}/command')
    async def command(pid: str, request: Request):
        return invoke(editor.command, pid, await body(request, 600_000))

    @router.post('/{pid}/register')
    async def register(pid: str, request: Request):
        data = await body(request)
        return invoke(editor.register, pid, data.get('relative_path'), data.get('revision'))

    @router.post('/{pid}/agent-command')
    async def agent_command(pid: str, request: Request):
        data = await body(request, 600_000)
        return invoke(editor.command, pid, data, 'agent')

    @router.post('/{pid}/agent-register')
    async def agent_register(pid: str, request: Request):
        data = await body(request)
        return invoke(editor.register, pid, data.get('relative_path'), data.get('revision'), 'agent')

    @router.post('/{pid}/upload')
    async def upload(pid: str, request: Request, filename: str, revision: int):
        origin = request.headers.get('origin')
        if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            raise HTTPException(403, 'Origen no autorizado')
        suffix = Path(filename).suffix.lower()
        if suffix not in editor.EXTENSIONS or len(filename) > 240:
            raise HTTPException(400, 'Extensión no admitida o nombre demasiado largo')
        project = invoke(studio.project_path, pid)
        invoke(editor._revision, invoke(editor.state, pid), revision)
        relative = 'assets/imports/' + uuid.uuid4().hex + suffix
        target = project / relative
        try:
            target.parent.resolve().relative_to(project.resolve())
        except ValueError as exc:
            raise HTTPException(400, 'La carpeta de importación sale del proyecto') from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        try:
            with target.open('xb') as stream:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 2_000_000_000:
                        raise HTTPException(413, 'Límite de importación: 2 GB por archivo')
                    stream.write(chunk)
            if not size:
                raise HTTPException(400, 'Archivo vacío')
            return invoke(editor.register, pid, relative, revision, 'user', filename)
        except Exception:
            target.unlink(missing_ok=True)
            raise

    @router.get('/{pid}/source/{key}')
    def source(pid: str, key: str):
        return FileResponse(invoke(editor.source, pid, key))

    @router.get('/{pid}/subtitles', response_class=PlainTextResponse)
    def subtitles(pid: str):
        value = invoke(editor.state, pid)
        return PlainTextResponse(editor.srt(value['edit_decisions']), media_type='application/x-subrip',
                                 headers={'Content-Disposition': 'attachment; filename="subtitles.srt"'})

    @router.post('/{pid}/subtitles/import')
    async def import_subtitles(pid: str, request: Request, filename: str, revision: int):
        origin = request.headers.get('origin')
        if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            raise HTTPException(403, 'Origen no autorizado')
        chunks = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 500_000:
                raise HTTPException(413, 'SRT superior a 500 KB')
            chunks.append(chunk)
        return invoke(editor.import_subtitles, pid, b''.join(chunks), filename, revision)

    @router.get('/{pid}/render')
    def render_status(pid: str):
        return invoke(render.status, pid)

    @router.get('/{pid}/subtitles.ass', response_class=PlainTextResponse)
    def ass_subtitles(pid: str):
        value = invoke(editor.state, pid)['edit_decisions']
        output = value['output']
        width, height = (output['width'], output['height']) if output['ratio'] == 'custom' else editor.PRESETS[output['ratio']]
        from lib.scene_burned_subtitles import _ass
        return PlainTextResponse(_ass(value['cues'], width, height, value['subtitle_style']),
                                 headers={'Content-Disposition': 'attachment; filename="subtitles.ass"'})

    @router.post('/{pid}/render/cancel')
    async def cancel_render(pid: str, request: Request):
        data = await body(request)
        return invoke(render.cancel, pid, data.get('attempt'))

    @router.post('/{pid}/agent-render/cancel')
    async def cancel_agent_render(pid: str, request: Request):
        data = await body(request)
        return invoke(render.cancel, pid, data.get('attempt'), 'agent')

    @router.post('/{pid}/render')
    async def start_render(pid: str, request: Request):
        data = await body(request)
        if type(data.get('preview', False)) is not bool:
            raise HTTPException(400, 'preview requiere un booleano')
        return invoke(render.start, pid, data.get('revision'), data.get('preview', False))

    @router.post('/{pid}/agent-render')
    async def start_agent_render(pid: str, request: Request):
        data = await body(request)
        if type(data.get('preview', False)) is not bool:
            raise HTTPException(400, 'preview requiere un booleano')
        return invoke(render.start, pid, data.get('revision'), data.get('preview', False), 'agent')

    return router
