"""Primary channel discovery capability for research agents and the local panel."""
from jsonschema import validate
from tools.base_tool import ToolResult
from .youtube_research import YouTubeResearch
from .youtube_channels import ChannelSearch, ChannelFilters, Unavailable
from .channel_identity import parse_channel_query, InvalidChannelQuery

FILTER_SCHEMA = {'type':'object','additionalProperties':False,'properties':{
    **{key:{'type':'integer','minimum':0} for key in ('min_views','max_views','min_subscribers',
       'max_subscribers','min_minutes','max_minutes','min_publication_views')},
    'language':{'type':'string'},'country':{'type':'string'},
    'sample_size':{'type':'integer','minimum':1,'maximum':20},
    'content_type':{'enum':['any','short_candidate','over_3m','medium','long']},
    'published_within':{'enum':['any','hour','day','week','month','year']}}}

class YouTubeChannelSearch(YouTubeResearch):
    name = 'youtube_channel_search'
    version = '0.3.0'
    capability = 'youtube_channel_research'
    capabilities = ['youtube_channel_research']
    input_schema = {'type':'object','additionalProperties':False,'required':['query'],
        'properties':{'query':{'type':'string','minLength':1,'maxLength':200},
                      'pages':{'type':'integer','minimum':1,'maximum':3},'filters':FILTER_SCHEMA}}

    def execute(self, inputs):
        try:
            validate(inputs,self.input_schema)
            filters = ChannelFilters(**inputs.get('filters',{}))
            filters.validate()
            parse_channel_query(inputs['query'])
        except InvalidChannelQuery as exc:
            return ToolResult(success=False,error='CHANNEL_INPUT_INVALID: '+str(exc))
        except Exception:
            return ToolResult(success=False,error='CHANNEL_FILTERS_INVALID: revisa los rangos y filtros')
        try:
            client = ChannelSearch()
            data = client.search_channels(inputs['query'],filters,inputs.get('pages',1))
            return ToolResult(success=True,data=data,artifacts=[],cost_usd=0)
        except Unavailable:
            return ToolResult(success=False,error='CHANNEL_SEARCH_UNAVAILABLE: comprueba clave, cuota, conexión o reduce páginas',data={'stale_fallback':False})
        except Exception:
            return ToolResult(success=False,error='CHANNEL_SEARCH_FAILED: no se devuelven resultados anteriores',data={'stale_fallback':False})
