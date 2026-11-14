"""Local channel-search surface. Fresh read-only queries; no result persistence."""
import asyncio
import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from tools.research.youtube_channel_search import YouTubeChannelSearch
from tools.research.youtube_channel_batch import YouTubeChannelBatch


def create_channel_router():
    router = APIRouter()
    busy = asyncio.Semaphore(2)

    @router.get('/channels')
    async def channel_page():
        return FileResponse(Path(__file__).parent/'ui'/'channels.html',headers={'Cache-Control':'no-cache'})

    @router.get('/api/research/channels/status')
    async def channel_status():
        return JSONResponse({'configured':bool(os.environ.get('YOUTUBE_API_KEY'))},headers={'Cache-Control':'no-store'})

    async def run_query(request: Request, tool_class):
        if request.headers.get('origin') not in (None,str(request.base_url).rstrip('/')):
            raise HTTPException(403,'Origen no permitido')
        if request.headers.get('content-type','').split(';')[0] != 'application/json':
            raise HTTPException(415,'Usa JSON')
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body)>16384:
                raise HTTPException(413,'Consulta demasiado grande')
        try:
            inputs=json.loads(body)
        except (ValueError,UnicodeDecodeError):
            raise HTTPException(400,'JSON inválido')
        from jsonschema import validate, ValidationError
        try:
            validate(inputs,tool_class.input_schema)
        except ValidationError:
            raise HTTPException(422,'Consulta o filtros inválidos')
        if busy.locked():
            raise HTTPException(429,'Ya hay dos búsquedas en curso')
        async with busy:
            result=await asyncio.to_thread(tool_class().execute,inputs)
        if not result.success:
            failure=result.data.get('failure')
            if failure:
                status={'QUOTA_EXCEEDED':429,'RATE_LIMITED':429,'TIMEOUT':504,
                        'RESOURCE_UNAVAILABLE':404,'INVALID_RESPONSE':502,'UPSTREAM_ERROR':502}.get(failure['code'],503)
                payload={'error':failure['message'],'error_code':failure['code'],'retryable':failure['retryable']}
                if result.data.get('result_type')=='channels':
                    payload.update(result.data)
                return JSONResponse(payload,status_code=status,headers={'Cache-Control':'no-store'})
            status=422 if result.error.startswith(('CHANNEL_FILTERS_INVALID','CHANNEL_INPUT_INVALID')) else 503
            return JSONResponse({'error':result.error},status_code=status,headers={'Cache-Control':'no-store'})
        return JSONResponse(result.data,headers={'Cache-Control':'no-store'})

    @router.post('/api/research/channels')
    async def channel_query(request: Request):
        return await run_query(request,YouTubeChannelSearch)

    @router.post('/api/research/channels/batch')
    async def channel_batch(request: Request):
        return await run_query(request,YouTubeChannelBatch)

    return router
