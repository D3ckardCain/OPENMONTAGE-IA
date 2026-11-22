"""Determine whether saved render evidence predates an editorial revision."""
from datetime import datetime


def _time(value):
    try:
        result=datetime.fromisoformat(value)
        return result if result.tzinfo is not None else None
    except (TypeError,ValueError):
        return None


def current(verification,reviews):
    if not isinstance(verification,dict) or verification.get('status')!='passed':return False
    verified=_time(verification.get('finished_at'))
    if not isinstance(reviews,list):return False
    for review in reviews:
        if not isinstance(review,dict) or review.get('decision')!='revision_requested':continue
        requested=_time(review.get('at'))
        if verified is None or requested is None or requested>verified:return False
    return True
