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
    from lib.project_channel_performance import verified as verified_performance
    verified_performance(path,request)
    from lib.packaging_options import read as read_packaging
    packaging=read_packaging(request['project_id'])
    receipt=studio.read_json(path/'render_verification.json',{})
    previous=receipt.get('channel_research') if isinstance(receipt,dict) else None
    if (isinstance(previous,dict) and previous.get('packaging_revision')
            and packaging['revision'] is None):
        raise ValueError('Selección editorial del render ausente')


def project_problem(path):
    """Preflight for queues; return a concrete problem without mutating the project."""
    request=studio.read_json(path/'production_request.json')
    saved=studio.read_json(path/'render_verification.json',{})
    previous=saved.get('channel_research') if isinstance(saved,dict) else None
    if (not request.get('research_idea') and not request.get('performance_import_id')
            and not (path/'artifacts/packaging_options.json').exists()
            and not (path/'artifacts/packaging_options.json').is_symlink()
            and not (isinstance(previous,dict) and previous.get('packaging_revision'))):return None
    try:
        require_valid(path,request)
        if request.get('research_idea'):
            from lib.project_video_observations import verified_rows
            verified_rows(path,request)
    except (ValueError,KeyError,TypeError,OverflowError,OSError) as exc:
        return 'Investigación del proyecto no válida: '+str(exc)[:300]
    return None


def restore_missing(pid):
    """Complete old project copies using the surviving local idea as an anchor."""
    from lib.channel_dossiers import read as read_dossier
    from lib.channel_ideas import read_draft
    from lib.project_video_observations import restore_missing as restore_observations
    path=studio.project_path(pid)
    with studio.LOCK:
        request=studio.read_json(path/'production_request.json')
        ref=request.get('research_idea')
        if not isinstance(ref,dict) or set(ref)!={'channel_id','snapshot_id','idea_id'}:
            raise ValueError('El proyecto no tiene una propuesta vinculada')
        snapshot_path=path/'artifacts/channel_research_snapshot.json'
        idea_path=path/'artifacts/channel_idea_source.json'
        if snapshot_path.is_file() and idea_path.is_file():
            verified(path,request)
            return {'restored':restore_observations(path,request),'status':'verified'}
        # A project with no surviving idea and no recorded digest has no trusted anchor.
        if not idea_path.is_file() and not request.get('research_idea_sha256'):
            raise ValueError('Falta la propuesta y su hash; no se puede recuperar con seguridad')
        dossier=read_dossier(ref['channel_id'],ref['snapshot_id'])
        idea=read_draft(ref['channel_id'],ref['idea_id'])
        if (idea['snapshot_id']!=dossier['id'] or idea['snapshot_sha256']!=dossier['report_sha256']
                or request.get('reference') not in [r['url'] for r in idea['references']]):
            raise ValueError('La investigación original no corresponde al proyecto')
        digest=_digest(idea)
        if request.get('research_idea_sha256') and request['research_idea_sha256']!=digest:
            raise ValueError('La propuesta original difiere del hash del proyecto')
        if snapshot_path.is_file() and studio.read_json(snapshot_path)!=dossier:
            raise ValueError('El expediente del proyecto fue alterado')
        if idea_path.is_file() and studio.read_json(idea_path)!=idea:
            raise ValueError('La propuesta del proyecto fue alterada')
        if not idea_path.is_file():studio.save_json(idea_path,idea)
        if not snapshot_path.is_file():studio.save_json(snapshot_path,dossier)
        if not request.get('research_idea_sha256'):
            request['research_idea_sha256']=digest
            studio.save_json(path/'production_request.json',request)
        verified(path,request)
        restore_observations(path,request)
        return {'restored':True,'status':'verified'}


def summary(path,request):
    if not request.get('research_idea'):return None
    if not (path/'artifacts/channel_research_snapshot.json').is_file() or not (path/'artifacts/channel_idea_source.json').is_file():
        return {'status':'missing','message':'Falta la copia de investigación. Recupera desde registros locales si siguen disponibles.'}
    if request.get('research_observations_sha256') is not None and not (path/'artifacts/video_observations_snapshot.json').is_file():
        return {'status':'missing','message':'Falta la copia histórica de vidIQ. Recupera desde el registro local si sigue disponible.'}
    try:
        snapshot,idea,report=verified(path,request)
        from lib.project_video_observations import verified_rows
        observations=verified_rows(path,request)
    except (ValueError,KeyError,TypeError,OverflowError):
        return {'status':'invalid','message':'Expediente, propuesta u observaciones ausentes o alteradas; revisa el proyecto antes de producir.'}
    return {'status':'verified','channel_id':report['channel_id'],'snapshot_id':snapshot['id'],
            'snapshot_sha256':snapshot['report_sha256'],'retrieved_at_utc':report['retrieved_at_utc'],
            'complete_period':report['complete_period'],'publication_total':len(report['publications']),
            'idea_title':idea['title'],'vidiq_observation_total':len(observations) if observations is not None else None,
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
