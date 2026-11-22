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


def page(path,request,offset=0,limit=20):
    rows=verified_rows(path,request)
    if rows is None:
        return {'status':'not_copied','observations':[],
                'message':'Este proyecto se creó antes de conservar observaciones de vidIQ.'}
    return {'status':'verified','source':'vidIQ Edge (transcripción manual)',
            'observation_total':len(rows),'offset':offset,'observations':rows[offset:offset+limit],
            'next_offset':offset+limit if offset+limit<len(rows) else None,
            'limits':'Observaciones introducidas manualmente, fechadas y calculadas por vidIQ. No son cifras oficiales ni actuales de YouTube.'}
