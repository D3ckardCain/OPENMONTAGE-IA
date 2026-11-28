"""Project scoped, manually recorded vidIQ observations kept apart from YouTube audits."""
from lib import production_studio as studio
from lib.channel_dossiers import _digest
from lib.project_channel_evidence import verified


def verified_rows(path,request):
    if not request.get('research_idea'):
        raise ValueError('El proyecto no tiene investigación de canal vinculada')
    _,idea,_=verified(path,request)
    digest=request.get('research_observations_sha256')
    if digest is None:
        return None  # Projects predating the observation copy.
    rows=studio.read_json(path/'artifacts/video_observations_snapshot.json',None)
    selected={item['id'] for item in idea['references']}
    if (not isinstance(rows,list) or _digest(rows)!=digest
            or any(not isinstance(row,dict) or row.get('video_id') not in selected
                   or row.get('source')!='vidIQ Edge (transcripción manual)' for row in rows)):
        raise ValueError('Observaciones del proyecto ausentes o alteradas')
    return rows


def restore_missing(path,request):
    """Recover an absent historical prefix, never replacing an existing file."""
    from lib.video_observations import read
    _,idea,_=verified(path,request)
    digest=request.get('research_observations_sha256')
    if digest is None:return False
    target=path/'artifacts/video_observations_snapshot.json'
    if target.is_file():
        verified_rows(path,request)
        return False
    selected={item['id'] for item in idea['references']}
    candidates=[row for row in read() if row.get('video_id') in selected]
    # The global log is append-only. A later observation cannot enter this old copy.
    for count in range(len(candidates)+1):
        prefix=candidates[:count]
        if _digest(prefix)==digest:
            studio.save_json(target,prefix)
            verified_rows(path,request)
            return True
    raise ValueError('No se encontró la copia histórica de observaciones con el hash original')


def page(path,request,offset=0,limit=20):
    rows=verified_rows(path,request)
    if rows is None:
        return {'status':'not_copied','observations':[],
                'message':'Este proyecto se creó antes de conservar observaciones de vidIQ.'}
    return {'status':'verified','source':'vidIQ Edge (transcripción manual)',
            'observation_total':len(rows),'offset':offset,'observations':rows[offset:offset+limit],
            'next_offset':offset+limit if offset+limit<len(rows) else None,
            'limits':'Observaciones introducidas manualmente, fechadas y calculadas por vidIQ. No son cifras oficiales ni actuales de YouTube.'}
