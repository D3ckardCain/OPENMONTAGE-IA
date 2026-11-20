"""Upper bounds for request traffic; no API calls or channel metrics."""
from jsonschema import validate
from .channel_identity import parse_channel_query
from .youtube_channel_batch import YouTubeChannelBatch


def plan(inputs):
    validate(inputs,YouTubeChannelBatch.input_schema)
    from .youtube_channels import ChannelFilters
    filters=ChannelFilters(**inputs.get('filters',{}));filters.validate()
    queries=[];seen=set()
    for value in inputs['queries']:
        identity=parse_channel_query(value)
        if identity not in seen:seen.add(identity);queries.append(value.strip())
    pages=inputs.get('pages',1);search=0;channels=0;playlists=0;videos=0
    for query in queries:
        kind,_=parse_channel_query(query)
        if kind=='keywords':
            candidates=pages*50;search+=pages;channels+=pages
            if filters.discovery_mode=='recent_publications':videos+=pages
        else:candidates=1;channels+=1
        if filters.inspect_uploads:playlists+=candidates;videos+=candidates
    return {'source':'local_request_planner','api':'YouTube Data API v3','network_requests_started':0,
        'unique_queries':len(queries),'maximum_requests_before_budget':{'search':search,'channels':channels,'playlistItems':playlists,'videos':videos},
        'maximum_requests_total_before_budget':search+channels+playlists+videos,
        'batch_request_limit':inputs.get('max_requests',300) if len({q.strip() for q in inputs['queries']})>1 else None,'remaining_project_quota':None,
        'quota_model':{'search_bucket':'Search Queries','search_list_calls_upper_bound':search,
            'other_read_units_upper_bound':channels+playlists+videos,
            'official_reference':'https://developers.google.com/youtube/data/determine_quota_cost'},
        'notes':['Límite superior, no consumo real ni cuota restante del proyecto.',
                 'La paginación, los candidatos descartados y el límite del lote pueden reducir las solicitudes.',
                 'El límite de solicitudes del lote solo se aplica al endpoint de búsquedas por lote.',
                 'No se envía una consulta a YouTube al preparar este cálculo.']}
