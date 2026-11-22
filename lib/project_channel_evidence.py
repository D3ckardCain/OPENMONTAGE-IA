"""Verify research copies held inside one production project."""
from lib import production_studio as studio
from lib.channel_dossiers import _digest


def verified(path, request):
    ref=request.get('research_idea')
    snapshot=studio.read_json(path/'artifacts/channel_research_snapshot.json',{})
    idea=studio.read_json(path/'artifacts/channel_idea_source.json',{})
    report=snapshot.get('report') if isinstance(snapshot,dict) else None
    if (not isinstance(ref,dict) or not isinstance(report,dict) or not isinstance(idea,dict)
            or snapshot.get('id')!=ref.get('snapshot_id')
            or report.get('channel_id')!=ref.get('channel_id')
            or snapshot.get('report_sha256')!=_digest(report)
            or idea.get('id')!=ref.get('idea_id')
            or idea.get('channel_id')!=ref.get('channel_id')
            or idea.get('snapshot_id')!=snapshot['id']
            or idea.get('snapshot_sha256')!=snapshot['report_sha256']
            or _digest(idea)!=request.get('research_idea_sha256')
            or not isinstance(report.get('publications'),list)):
        raise ValueError('Expediente del proyecto ausente o alterado')
    return snapshot,idea,report


def require_valid(path,request):
    if request.get('research_idea') is not None:
        verified(path,request)


def summary(path,request):
    if not request.get('research_idea'):return None
    try:snapshot,idea,report=verified(path,request)
    except (ValueError,KeyError,TypeError,OverflowError):
        return {'status':'invalid','message':'Expediente o propuesta ausente o alterada; revisa el proyecto antes de producir.'}
    return {'status':'verified','channel_id':report['channel_id'],'snapshot_id':snapshot['id'],
            'snapshot_sha256':snapshot['report_sha256'],'retrieved_at_utc':report['retrieved_at_utc'],
            'complete_period':report['complete_period'],'publication_total':len(report['publications']),
            'idea_title':idea['title'],
            'message':'Captura histórica: comprueba vigencia, hechos y derechos antes de publicar.'}


def page(path,request,offset=0,limit=20):
    snapshot,idea,report=verified(path,request)
    rows=report['publications']
    return {'source':'YouTube Data API (copia local del proyecto)',
            'channel_id':report['channel_id'],'snapshot_id':snapshot['id'],
            'snapshot_sha256':snapshot['report_sha256'],
            'retrieved_at_utc':report['retrieved_at_utc'],
            'since_utc':report['since_utc'],'cutoff_at_utc':report['cutoff_at_utc'],
            'complete_period':report['complete_period'],'analysis':report.get('analysis'),
            'publication_total':len(rows),'offset':offset,'publications':rows[offset:offset+limit],
            'next_offset':offset+limit if offset+limit<len(rows) else None,'idea':idea,
            'limits':'Vistas acumuladas en la fecha de consulta. Revisa hechos y derechos antes de publicar.'}
