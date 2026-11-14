"""Channel discovery ordered by public lifetime views, then subscribers.
Content filters inspect recent uploads, not the complete channel history.
No derived viral/earnings score, media download or persistent cache.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
import re
import time

from .youtube_client import YouTube, Unavailable, count, duration_seconds


@dataclass
class ChannelFilters:
    min_views: int = 0
    max_views: int | None = None
    min_subscribers: int | None = None
    max_subscribers: int | None = None
    language: str | None = None
    country: str | None = None
    min_minutes: int = 0
    max_minutes: int | None = None
    content_type: str = 'any'
    published_within: str = 'any'
    min_publication_views: int = 0
    sample_size: int = 10

    @property
    def inspect_uploads(self):
        return bool(self.language or self.min_minutes or self.max_minutes is not None
                    or self.content_type != 'any' or self.published_within != 'any'
                    or self.min_publication_views)

    def validate(self):
        for low, high in ((self.min_views,self.max_views),
                          (self.min_subscribers,self.max_subscribers),
                          (self.min_minutes,self.max_minutes)):
            if any(v is not None and (type(v) is not int or v < 0) for v in (low,high)):
                raise Unavailable('Los límites deben ser enteros no negativos')
            if low is not None and high is not None and low > high:
                raise Unavailable('Rango invertido')
        if type(self.min_publication_views) is not int or self.min_publication_views < 0:
            raise Unavailable('Vistas de publicación inválidas')
        if type(self.sample_size) is not int or not 1 <= self.sample_size <= 20:
            raise Unavailable('Revisa entre 1 y 20 publicaciones por canal')
        if self.language and not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*', self.language):
            raise Unavailable('Idioma inválido')
        if self.country and not re.fullmatch('[A-Z]{2}', self.country):
            raise Unavailable('País ISO de dos letras mayúsculas')
        if self.content_type not in {'any','short_candidate','over_3m','medium','long'}:
            raise Unavailable('Tipo de contenido inválido')
        if self.published_within not in {'any','hour','day','week','month','year'}:
            raise Unavailable('Periodo inválido')


class ChannelSearch(YouTube):
    def get(self, resource, **params):
        if time.monotonic() > self._deadline:
            raise Unavailable('Consulta demasiado amplia; reduce páginas o filtros')
        return super().get(resource, **params)

    def search_channels(self, query, filters=None, pages=1):
        filters = filters or ChannelFilters()
        filters.validate()
        if not isinstance(query,str) or not query.strip() or len(query) > 200:
            raise Unavailable('Escribe un tema de hasta 200 caracteres')
        if type(pages) is not int or not 1 <= pages <= 3:
            raise Unavailable('Usa entre 1 y 3 páginas')
        self._deadline = time.monotonic() + 120
        self.calls = {}
        now = datetime.now(timezone.utc)
        params = dict(part='snippet',type='channel',q=query.strip(),maxResults=50,
                      order='viewCount',safeSearch='moderate')
        if filters.language:
            params['relevanceLanguage'] = filters.language
        items, exhausted = self.pages('search', pages, **params)
        # The documented search index may mix resource types for some orders.
        ids = list(dict.fromkeys(item['id']['channelId'] for item in items
                   if isinstance(item.get('id'),dict) and item['id'].get('channelId')
                   and item['id'].get('kind','youtube#channel') == 'youtube#channel'))
        channels = self.batches('channels', ids, 'snippet,statistics,contentDetails')
        by_id = {ch.get('id'):ch for ch in channels}
        rows = []
        excluded = {}
        def reject(reason):
            excluded[reason] = excluded.get(reason,0) + 1
        for channel_id in ids:
            ch = by_id.get(channel_id)
            if not ch:
                reject('channel_unavailable'); continue
            sn, stats = ch.get('snippet',{}), ch.get('statistics',{})
            views = count(stats.get('viewCount'))
            subs = None if stats.get('hiddenSubscriberCount') else count(stats.get('subscriberCount'))
            if views is None:
                reject('views_unknown'); continue
            if views < filters.min_views or (filters.max_views is not None and views > filters.max_views):
                reject('channel_views'); continue
            if filters.min_subscribers is not None or filters.max_subscribers is not None:
                if subs is None:
                    reject('subscribers_unknown'); continue
                if ((filters.min_subscribers is not None and subs < filters.min_subscribers)
                    or (filters.max_subscribers is not None and subs > filters.max_subscribers)):
                    reject('subscribers'); continue
            if filters.country and sn.get('country') != filters.country:
                reject('country_unknown_or_other'); continue
            rows.append(dict(id=channel_id,url='https://www.youtube.com/channel/'+channel_id,
                title=sn.get('title'),description=sn.get('description'),
                viewCount=views,subscriberCount_public_rounded=subs,
                videoCount=count(stats.get('videoCount')),country_declared=sn.get('country'),
                created_at=sn.get('publishedAt'),text_language_declared=sn.get('defaultLanguage'),
                uploads_playlist=ch.get('contentDetails',{}).get('relatedPlaylists',{}).get('uploads'),
                content_review=None,viral_now=None,monetized=None,rpm=None))
        rows.sort(key=lambda ch: (-ch['viewCount'],
                    -(ch['subscriberCount_public_rounded'] if ch['subscriberCount_public_rounded'] is not None else -1), ch['id']))
        if filters.inspect_uploads:
            reviewed = []
            for row in rows:
                playlist = row.pop('uploads_playlist')
                if not playlist:
                    reject('uploads_unavailable'); continue
                reply = self.get('playlistItems', part='contentDetails',playlistId=playlist,
                                 maxResults=filters.sample_size)
                video_ids = list(dict.fromkeys(x.get('contentDetails',{}).get('videoId')
                                 for x in reply['items'] if x.get('contentDetails',{}).get('videoId')))
                videos = self.batches('videos',video_ids,'snippet,statistics,contentDetails,liveStreamingDetails')
                matches = [v for v in videos if self._matches(v,row['id'],filters,now)]
                if not matches:
                    reject('no_match_in_recent_sample'); continue
                dates = [v['snippet']['publishedAt'] for v in matches if v['snippet'].get('publishedAt')]
                row['content_review'] = dict(sample_requested=filters.sample_size,
                    inspected=len(videos),matched=len(matches),
                    latest_matching_publication=max(dates) if dates else None,
                    complete_history=False,shorts_confirmed=None)
                reviewed.append(row)
            rows = reviewed
        else:
            for row in rows:
                row.pop('uploads_playlist',None)
        return dict(source='YouTube Data API',retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            result_type='channels',order=['viewCount_desc','subscriberCount_public_rounded_desc'],
            scope=dict(query=query.strip(),pages_requested=pages,search_pages_exhausted=exhausted,
                       candidate_channels=len(ids),global_coverage=False,
                       content_filter_scope='recent_upload_sample' if filters.inspect_uploads else 'not_requested'),
            filters=asdict(filters),results=rows,excluded=excluded,requests=dict(self.calls),
            notes=['Orden por vistas acumuladas del canal; suscriptores como segundo criterio.',
                   'La muestra no certifica viralidad actual, crecimiento, monetización ni RPM.',
                   'Suscriptores públicos redondeados; desconocido no equivale a cero.',
                   'Los filtros de contenido exigen una misma publicación coincidente en la muestra reciente.',
                   'Idioma: audio declarado de publicaciones; no verificación acústica ni idioma de todo el canal.',
                   'Hasta 3 minutos solo indica candidato a Short; más de 3 minutos es un filtro de duración.',
                   'Periodos móviles: día 24h, semana 7d, mes 30d, año 365d.'])

    @staticmethod
    def _matches(video, channel_id, filters, now):
        sn = video.get('snippet',{})
        if sn.get('channelId') != channel_id or video.get('liveStreamingDetails') is not None:
            return False
        if filters.language:
            lang = sn.get('defaultAudioLanguage')
            if not lang or lang.lower().split('-')[0] != filters.language.lower().split('-')[0]:
                return False
        if filters.published_within != 'any':
            try:
                date = datetime.fromisoformat(sn.get('publishedAt','').replace('Z','+00:00'))
                hours = {'hour':1,'day':24,'week':168,'month':720,'year':8760}[filters.published_within]
                if date.utcoffset() is None or not now-timedelta(hours=hours) <= date <= now:
                    return False
            except (ValueError,TypeError):
                return False
        if filters.min_publication_views:
            views = count(video.get('statistics',{}).get('viewCount'))
            if views is None or views < filters.min_publication_views:
                return False
        if filters.min_minutes or filters.max_minutes is not None or filters.content_type != 'any':
            try:
                seconds = duration_seconds(video.get('contentDetails',{}).get('duration'))
            except Unavailable:
                return False
            if seconds < filters.min_minutes*60 or (filters.max_minutes is not None and seconds > filters.max_minutes*60):
                return False
            if filters.content_type == 'short_candidate' and not 0 < seconds <= 180:
                return False
            if filters.content_type == 'over_3m' and seconds <= 180:
                return False
            if filters.content_type == 'medium' and not 240 <= seconds <= 1200:
                return False
            if filters.content_type == 'long' and seconds <= 1200:
                return False
        return True
