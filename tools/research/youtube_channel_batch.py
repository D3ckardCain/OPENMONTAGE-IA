"""Bounded batch retrieval of agent-specified topics, not an agent orchestrator.
The agent chooses the topics and filters. This tool only queries, deduplicates,
and sorts public channel records. It neither invents topics nor produces videos.
"""
from datetime import datetime, timezone
import time
from jsonschema import validate
from tools.base_tool import ToolResult
from .youtube_channel_search import YouTubeChannelSearch, FILTER_SCHEMA
from .youtube_channels import ChannelSearch, ChannelFilters, YouTubeFailure
from .channel_identity import parse_channel_query


class YouTubeChannelBatch(YouTubeChannelSearch):
    name = 'youtube_channel_batch'
    version = '0.1.0'
    capability = 'youtube_channel_batch_research'
    capabilities = ['youtube_channel_batch_research']
    input_schema = {'type':'object','additionalProperties':False,'required':['queries'],
        'properties':{'queries':{'type':'array','minItems':1,'maxItems':5,
            'items':{'type':'string','minLength':1,'maxLength':200}},
            'pages':{'type':'integer','minimum':1,'maximum':3},'filters':FILTER_SCHEMA,
            'max_requests':{'type':'integer','minimum':1,'maximum':500}}}

    def execute(self, inputs):
        try:
            validate(inputs,self.input_schema)
            filters=ChannelFilters(**inputs.get('filters',{}));filters.validate()
            queries=[];seen=set()
            for value in inputs['queries']:
                identity=parse_channel_query(value)
                if identity not in seen:
                    seen.add(identity);queries.append(value.strip())
        except Exception:
            return ToolResult(success=False,error='CHANNEL_INPUT_INVALID: revisa los temas y filtros del lote')
        started=datetime.now(timezone.utc).isoformat()
        completed=[];rows={};requests={};failure=None;failed_query=None
        limit=inputs.get('max_requests',300)
        try:
            client=ChannelSearch()
            client.batch_deadline=time.monotonic()+180
            for query in queries:
                remaining=limit-sum(requests.values())
                if remaining<=0:
                    failed_query=query;raise YouTubeFailure('REQUEST_BUDGET_EXCEEDED')
                client.request_limit=remaining
                try:
                    data=client.search_channels(query,filters,inputs.get('pages',1))
                except Exception:
                    for resource,n in client.calls.items():requests[resource]=requests.get(resource,0)+n
                    failed_query=query
                    raise
                for resource,n in data['requests'].items():requests[resource]=requests.get(resource,0)+n
                for row in data['results']:
                    previous=rows.get(row['id'])
                    topics=list(previous['matched_queries']) if previous else []
                    topics.append(query)
                    # Prefer the latest response, never a fabricated maximum counter.
                    rows[row['id']]={**row,'matched_queries':topics,'retrieved_at_utc':data['retrieved_at_utc']}
                completed.append({'query':query,'scope':data['scope'],'excluded':data['excluded']})
        except YouTubeFailure as exc:
            failure={'code':exc.code,'message':str(exc),'retryable':exc.retryable}
        except Exception:
            failure={'code':'UNKNOWN_ERROR','message':'El lote se detuvo por un fallo de consulta. No se reintenta automáticamente.','retryable':False}
        result=list(rows.values())
        result.sort(key=lambda row:(-row['viewCount'],
            -(row['subscriberCount_public_rounded'] if row['subscriberCount_public_rounded'] is not None else -1),row['id']))
        pending=queries[len(completed):]
        data={'result_type':'channels','source':'YouTube Data API',
            'started_at_utc':started,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
            'results':result,'order':['viewCount_desc','subscriberCount_public_rounded_desc'],
            'queries':queries,'completed_queries':completed,'pending_queries':pending,
            'failed_query':failed_query,'complete':failure is None,'partial':bool(completed) and failure is not None,
            'stale_fallback':False,'requests':requests,'max_requests':limit,
            'scope':{'global_coverage':False,'lookup_mode':'batch',
                'candidate_channels':sum(item['scope']['candidate_channels'] for item in completed),
                'content_filter_scope':'recent_upload_sample' if filters.inspect_uploads else 'not_requested'},
            'excluded':{},'notes':['Sin duplicados por ID. Se conserva la última respuesta de cada canal.',
                'Las coincidencias y vistas son muestras actuales, no una certificación de viralidad.',
                'La ejecución se detiene ante cualquier fallo; no hay reintentos automáticos.']}
        if failure:
            data['failure']=failure
            return ToolResult(success=False,error=failure['code']+': '+failure['message'],data=data,artifacts=[])
        return ToolResult(success=True,data=data,artifacts=[],cost_usd=0)
