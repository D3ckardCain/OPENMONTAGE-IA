"""Read verified local channel evidence in bounded parts for agents."""
from jsonschema import validate

from tools.base_tool import BaseTool,ToolResult,ToolTier,ToolRuntime,ToolStability


class SavedChannelEvidence(BaseTool):
    name='saved_channel_evidence'
    version='0.1.0'
    provider='openmontage_local'
    tier=ToolTier.SOURCE
    runtime=ToolRuntime.LOCAL
    stability=ToolStability.BETA
    capability='youtube_channel_research'
    capabilities=['youtube_channel_research','local_research_evidence']
    side_effects=[]
    install_instructions='Audita un canal en /channels y guarda una propuesta editorial si corresponde.'
    input_schema={'type':'object','additionalProperties':False,'required':['channel_id','snapshot_id'],
        'properties':{'channel_id':{'type':'string','pattern':'^UC[A-Za-z0-9_-]{22}$'},
            'snapshot_id':{'type':'string','pattern':'^[0-9a-f]{32}$'},
            'idea_id':{'type':'string','pattern':'^[0-9a-f]{32}$'},
            'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':50}}}

    def execute(self,inputs):
        from lib.channel_dossiers import read
        from lib.channel_ideas import read_draft
        try:
            validate(inputs,self.input_schema)
            source=read(inputs['channel_id'],inputs['snapshot_id'])
            report=source['report'];idea=None
            if inputs.get('idea_id'):
                idea=read_draft(inputs['channel_id'],inputs['idea_id'])
                if idea['snapshot_id']!=source['id'] or idea['snapshot_sha256']!=source['report_sha256']:
                    raise ValueError('La propuesta no corresponde a este expediente')
            offset=inputs.get('offset',0);limit=inputs.get('limit',20)
            rows=report['publications'];next_offset=offset+limit if offset+limit<len(rows) else None
            return ToolResult(success=True,cost_usd=0,data={
                'source':'YouTube Data API (expediente local, sin consulta nueva)',
                'channel_id':inputs['channel_id'],'snapshot_id':source['id'],
                'snapshot_sha256':source['report_sha256'],'retrieved_at_utc':report['retrieved_at_utc'],
                'since_utc':report['since_utc'],'cutoff_at_utc':report['cutoff_at_utc'],
                'complete_period':report['complete_period'],'analysis':report.get('analysis'),
                'publication_total':len(rows),'offset':offset,'publications':rows[offset:offset+limit],
                'next_offset':next_offset,'idea':idea,
                'limits':'Vistas acumuladas en la fecha de consulta. El borrador no aprueba hechos, derechos ni publicación.'})
        except (ValueError,KeyError,TypeError,FileNotFoundError):
            return ToolResult(success=False,error='SAVED_CHANNEL_EVIDENCE_INVALID: revisa IDs, expediente e integridad',cost_usd=0)
