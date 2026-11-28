"""Summarize saved producer timing events within one queue attempt."""
from datetime import datetime


def _stamp(value):
    try:
        parsed=datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else None
    except (TypeError,ValueError):
        return None


def summarize(events,start=None,end=None):
    lower=_stamp(start);upper=_stamp(end)
    if not isinstance(events,list):return {}
    stages={}
    for event in events:
        if not isinstance(event,dict) or event.get('kind')!='stage_timing':continue
        if lower is not None:
            at=_stamp(event.get('at'))
            if at is None or at<lower or (upper is not None and at>upper):continue
        stage,elapsed=event.get('stage'),event.get('elapsed_seconds')
        if not isinstance(stage,str) or not stage or type(elapsed) not in (int,float) or not 0<=elapsed<=86400:continue
        stages[stage]=round(stages.get(stage,0)+elapsed,3)
    return stages
