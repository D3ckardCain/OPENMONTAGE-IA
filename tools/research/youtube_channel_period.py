"""Bounded, on-demand audit of uploads from one channel within a UTC window."""
from datetime import datetime, timedelta, timezone
import re

from .youtube_client import YouTube, Unavailable, count
from .youtube_channels import sample_analysis


def _date(value):
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.utcoffset() is not None else None
    except (ValueError,TypeError,AttributeError):
        return None


def audit_channel(channel_id,days=30,max_pages=10,client=None,now=None):
    if not isinstance(channel_id,str) or not re.fullmatch(r'UC[A-Za-z0-9_-]{22}',channel_id):
        raise Unavailable('Indica el ID oficial UC... del canal')
    if type(days) is not int or not 1<=days<=365 or type(max_pages) is not int or not 1<=max_pages<=20:
        raise Unavailable('Periodo o límite de páginas inválido')
    client=client or YouTube()
    now=now or datetime.now(timezone.utc)
    if now.utcoffset() is None:raise Unavailable('Fecha de corte sin zona horaria')
    now=now.astimezone(timezone.utc);since=now-timedelta(days=days)
    channels=client.get('channels',part='snippet,contentDetails',id=channel_id)['items']
    if len(channels)!=1 or channels[0].get('id')!=channel_id:raise Unavailable('Canal no disponible')
    playlist=channels[0].get('contentDetails',{}).get('relatedPlaylists',{}).get('uploads')
    if not playlist:raise Unavailable('Canal sin lista pública de subidas')
    ids=[];seen_tokens=set();token=None;boundary=False;exhausted=False;pages=0;missing_dates=0
    for _ in range(max_pages):
        reply=client.get('playlistItems',part='snippet,contentDetails',playlistId=playlist,maxResults=50,
                         **({'pageToken':token} if token else {}))
        pages+=1
        for item in reply['items']:
            date=_date(item.get('contentDetails',{}).get('videoPublishedAt') or item.get('snippet',{}).get('publishedAt'))
            if date is None:missing_dates+=1;continue
            if date<since:boundary=True;continue
            if date<=now:
                vid=item.get('contentDetails',{}).get('videoId')
                if isinstance(vid,str) and re.fullmatch(r'[A-Za-z0-9_-]{11}',vid):ids.append(vid)
        token=reply.get('nextPageToken')
        if not token:exhausted=True;break
        if token in seen_tokens:raise Unavailable('Paginación repetida')
        seen_tokens.add(token)
        # A playlist is reverse chronological, but stop only when every dated
        # item on the page is older. A single old item does not prove coverage.
        dates=[_date(x.get('contentDetails',{}).get('videoPublishedAt') or x.get('snippet',{}).get('publishedAt')) for x in reply['items']]
        if dates and all(d is not None and d<since for d in dates):break
    ids=list(dict.fromkeys(ids))
    found={v.get('id'):v for v in client.batches('videos',ids,'snippet,statistics,contentDetails')}
    videos=[found[vid] for vid in ids if vid in found and found[vid].get('snippet',{}).get('channelId')==channel_id]
    records=[{'id':v['id'],'url':'https://www.youtube.com/watch?v='+v['id'],
              'title':v.get('snippet',{}).get('title'),
              'published_at':v.get('snippet',{}).get('publishedAt'),
              'viewCount':count(v.get('statistics',{}).get('viewCount'))} for v in videos]
    complete=bool(exhausted or (boundary and not token)) and missing_dates==0 and len(videos)==len(ids)
    # A page full of older items proves that later pages are outside the window.
    if boundary and not exhausted and token and dates and all(d is not None and d<since for d in dates):
        complete=missing_dates==0 and len(videos)==len(ids)
    return {'source':'YouTube Data API','channel_id':channel_id,'channel_title':channels[0].get('snippet',{}).get('title'),
            'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'cutoff_at_utc':now.isoformat(),
            'since_utc':since.isoformat(),'pages_read':pages,'max_pages':max_pages,
            'complete_period':complete,'missing_playlist_dates':missing_dates,
            'unavailable_video_count':len(ids)-len(videos),'analysis':sample_analysis(videos,len(ids)),
            'publications':records,'requests':dict(client.calls),
            'note':'Vistas acumuladas al consultar; no vistas ganadas en el periodo. La cobertura depende de la lista pública de subidas.'}
