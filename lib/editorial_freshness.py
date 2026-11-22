"""Determine whether saved render evidence predates an editorial revision."""
from datetime import datetime
import re


def _time(value):
    try:
        result=datetime.fromisoformat(value)
        return result if result.tzinfo is not None else None
    except (TypeError,ValueError):
        return None


def selection_index(project):
    """Read the selected dossier identity; malformed indices fail closed."""
    from lib import production_studio as studio
    path=project/'artifacts/football_comparison_selection.json'
    if not path.exists() and not path.is_symlink():return None
    if path.is_symlink():return {'invalid':True}
    try:
        value=studio.read_json(path)
        return value if isinstance(value,dict) else {'invalid':True}
    except (OSError,ValueError,TypeError):
        return {'invalid':True}


def current(verification,reviews,selection_index=None):
    if not isinstance(verification,dict) or verification.get('status')!='passed':return False
    selected=verification.get('football_selection')
    if selected is not None or selection_index is not None:
        if not isinstance(selected,dict) or not isinstance(selection_index,dict):return False
        if any(selected.get(key)!=selection_index.get(key) or not isinstance(selected.get(key),str)
               for key in ('selection_id','sha256')):return False
    verified=_time(verification.get('finished_at'))
    if not isinstance(reviews,list):return False
    for review in reviews:
        if not isinstance(review,dict) or review.get('decision')!='revision_requested':continue
        requested=_time(review.get('at'))
        if verified is None or requested is None or requested>verified:return False
    return True


def delivery_current(verification,delivery,reviews,selection_index=None):
    """Match saved delivery receipt to the latest verified source hashes."""
    if not current(verification,reviews,selection_index) or not isinstance(delivery,dict) or delivery.get('copied') is not True:
        return False
    verified_at=_time(verification.get('finished_at'))
    delivered_at=_time(delivery.get('delivered_at'))
    if verified_at is None or delivered_at is None or delivered_at<verified_at:return False
    verified=verification.get('outputs')
    copied=delivery.get('outputs')
    if not isinstance(verified,list) or not verified or not isinstance(copied,list) or len(verified)!=len(copied):return False
    def pairs(records,path_key):
        result={}
        for record in records:
            if not isinstance(record,dict):return None
            path,sha=record.get(path_key),record.get('sha256')
            if not isinstance(path,str) or not path or not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):return None
            if path in result:return None
            result[path]=sha
        return result
    sources=pairs(verified,'path')
    return sources is not None and sources==pairs(copied,'source')
