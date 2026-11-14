"""Public YouTube research, read-only, on demand. Python 3.11+, no dependencies.
No earnings inference, derived viral score, scraping, media download or disk cache.
"""
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json, os, re
import urllib.request, urllib.error
from urllib.parse import urlencode

class Unavailable(ValueError): pass

def duration_seconds(value):
    m=re.fullmatch(r'P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?',value or '')
    if not m or not any(m.groups()):raise Unavailable('Duración desconocida')
    return sum(int(v or 0)*factor for v,factor in zip(m.groups(),(86400,3600,60,1)))

def count(value):
    return int(value) if isinstance(value,(str,int)) and not isinstance(value,bool) and re.fullmatch(r'\d+',str(value)) else None

@dataclass
class Filters:
    language:str|None=None
    strict_language:bool=False
    min_seconds:int=0
    max_seconds:int|None=None
    min_views:int=0
    max_views:int|None=None
    min_subscribers:int|None=None
    max_subscribers:int|None=None
    format:str='any' # duration only: not an assertion of Shorts classification
    def validate(self):
        for low,high in ((self.min_seconds,self.max_seconds),(self.min_views,self.max_views),(self.min_subscribers,self.max_subscribers)):
            if any(v is not None and (type(v) is not int or v<0) for v in (low,high)):raise Unavailable('Límites deben ser enteros positivos o cero')
            if low is not None and high is not None and low>high:raise Unavailable('Rango invertido')
        if self.format not in ('any','short_candidate','over_3m'):raise Unavailable('Formato desconocido')
        if self.strict_language and not self.language:raise Unavailable('Especifica idioma para el filtro estricto')
        if self.language and not re.fullmatch(r'[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*',self.language):raise Unavailable('Idioma inválido')

class YouTube:
    def __init__(self,key=None,transport=None):
        self.key=key or os.environ.get('YOUTUBE_API_KEY')
        if not self.key:raise Unavailable('Falta YOUTUBE_API_KEY; no se usa scraping como sustituto')
        self.transport=transport;self.calls={}
    def get(self,resource,**params):
        self.calls[resource]=self.calls.get(resource,0)+1
        if self.transport:result=self.transport(resource,params)
        else:
            url='https://www.googleapis.com/youtube/v3/'+resource+'?'+urlencode({**params,'key':self.key})
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'Cache-Control':'no-cache'}),timeout=30) as r:
                    if r.geturl()!=url:raise Unavailable('Redirección inesperada')
                    raw=r.read(8_000_001)
                    if len(raw)>8_000_000:raise Unavailable('Respuesta excesiva')
                    result=json.loads(raw)
            except urllib.error.HTTPError as e:raise Unavailable('YouTube HTTP '+str(e.code)+'; comprueba clave, API y cuota. No se devuelven datos anteriores.') from None
            except (urllib.error.URLError,TimeoutError):raise Unavailable('No se pudo consultar YouTube') from None
        if not isinstance(result,dict) or not isinstance(result.get('items'),list) or 'error' in result:raise Unavailable('Respuesta API no válida')
        return result
    def pages(self,resource,max_pages,**params):
        if type(max_pages) is not int or not 1<=max_pages<=20:raise Unavailable('Usa 1..20 páginas por consulta')
        rows=[];token=None;seen=set()
        for _ in range(max_pages):
            reply=self.get(resource,**params,**({'pageToken':token} if token else {}))
            rows.extend(reply['items']);token=reply.get('nextPageToken')
            if not token:return rows,True
            if token in seen:raise Unavailable('Paginación repetida')
            seen.add(token)
        return rows,False
    def batches(self,resource,ids,part):
        ids=list(dict.fromkeys(ids));rows=[]
        for pos in range(0,len(ids),50):rows.extend(self.get(resource,part=part,id=','.join(ids[pos:pos+50]))['items'])
        return rows
    def search(self,query,filters=None,region=None,after=None,before=None,pages=1,order='viewCount'):
        filters=filters or Filters();filters.validate()
        if not query.strip():raise Unavailable('Falta tema de búsqueda')
        if order not in ('viewCount','date','relevance'):raise Unavailable('Orden no admitido')
        params=dict(part='snippet',type='video',q=query,maxResults=50,order=order,safeSearch='moderate')
        if region:
            if not re.fullmatch('[A-Z]{2}',region):raise Unavailable('Región ISO de dos letras mayúsculas')
            params['regionCode']=region
        if filters.language:params['relevanceLanguage']=filters.language
        for key,value in [('publishedAfter',after),('publishedBefore',before)]:
            if value:
                try:
                    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
                    if parsed.utcoffset() is None:raise ValueError
                except ValueError:raise Unavailable('Fecha RFC3339 con zona requerida') from None
                params[key]=value
        if after and before and datetime.fromisoformat(after.replace('Z','+00:00'))>=datetime.fromisoformat(before.replace('Z','+00:00')):raise Unavailable('Fechas invertidas')
        items,exhausted=self.pages('search',pages,**params)
        ids=[x['id']['videoId'] for x in items if isinstance(x.get('id'),dict) and x['id'].get('videoId')]
        return self.enrich(ids,filters,{'query':query,'region_available_in':region,'after':after,'before':before,'search_pages_exhausted':exhausted,'global_coverage':False})
    def channel(self,channel_id,filters=None,pages=1):
        filters=filters or Filters();filters.validate()
        if not re.fullmatch(r'UC[A-Za-z0-9_-]{22}',channel_id):raise Unavailable('Usa el ID oficial UC... del canal')
        result=self.get('channels',part='contentDetails',id=channel_id)['items']
        if len(result)!=1 or result[0].get('id')!=channel_id:raise Unavailable('Canal no disponible')
        uploads=result[0].get('contentDetails',{}).get('relatedPlaylists',{}).get('uploads')
        if not uploads:raise Unavailable('Canal sin lista pública de subidas')
        items,exhausted=self.pages('playlistItems',pages,part='contentDetails',playlistId=uploads,maxResults=50)
        ids=[x.get('contentDetails',{}).get('videoId') for x in items];ids=[x for x in ids if x]
        return self.enrich(ids,filters,{'channel_id':channel_id,'uploads_pages_exhausted':exhausted,'global_coverage':False})
    def enrich(self,ids,filters,scope):
        videos=self.batches('videos',ids,'snippet,contentDetails,statistics,status,liveStreamingDetails')
        channels=self.batches('channels',[x['snippet']['channelId'] for x in videos],'snippet,statistics')
        channels={x['id']:x for x in channels};out=[];excluded={}
        def reject(reason):excluded[reason]=excluded.get(reason,0)+1
        for v in videos:
            sn=v.get('snippet',{});stats=v.get('statistics',{});ch=channels.get(sn.get('channelId'))
            if not ch:reject('channel_unavailable');continue
            if v.get('liveStreamingDetails') is not None:reject('live_or_archive_excluded');continue
            try:seconds=duration_seconds(v.get('contentDetails',{}).get('duration'))
            except Unavailable:reject('duration_unknown');continue
            views=count(stats.get('viewCount'));cs=ch.get('statistics',{})
            subscribers=None if cs.get('hiddenSubscriberCount') else count(cs.get('subscriberCount'))
            language=sn.get('defaultAudioLanguage');declared_text=sn.get('defaultLanguage')
            if views is None:reject('views_unknown');continue
            if not filters.min_seconds<=seconds or (filters.max_seconds is not None and seconds>filters.max_seconds):reject('duration');continue
            if views<filters.min_views or (filters.max_views is not None and views>filters.max_views):reject('views');continue
            if filters.format=='short_candidate' and not 0<seconds<=180:reject('duration_format');continue
            if filters.format=='over_3m' and seconds<=180:reject('duration_format');continue
            if filters.strict_language and (not language or language.lower().split('-')[0]!=filters.language.lower().split('-')[0]):reject('audio_language_unknown_or_other');continue
            if filters.min_subscribers is not None or filters.max_subscribers is not None:
                if subscribers is None:reject('subscribers_unknown');continue
                if (filters.min_subscribers is not None and subscribers<filters.min_subscribers) or (filters.max_subscribers is not None and subscribers>filters.max_subscribers):reject('subscribers');continue
            out.append({'id':v['id'],'url':'https://www.youtube.com/watch?v='+v['id'],'title':sn.get('title'),'publishedAt':sn.get('publishedAt'),'duration_seconds':seconds,'audio_language_declared':language,'text_language_declared':declared_text,'shorts_confirmed':None,'viewCount':views,'likeCount':count(stats.get('likeCount')),'commentCount':count(stats.get('commentCount')),'channel_id':ch['id'],'channel_title':ch.get('snippet',{}).get('title'),'channel_country_declared':ch.get('snippet',{}).get('country'),'subscriberCount_public_rounded':subscribers,'thumbnail_references':sn.get('thumbnails',{}),'license':v.get('status',{}).get('license'),'monetized':None,'revenue':None,'rpm':None})
        out.sort(key=lambda x:x['viewCount'],reverse=True)
        return {'source':'YouTube Data API','retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'scope':scope,'filters':asdict(filters),'results':out,'excluded':excluded,'unavailable_video_ids':sorted(set(ids)-{v['id'] for v in videos}),'requests':dict(self.calls),'notes':['Muestra de búsqueda/subidas, no todos los canales de YouTube.','Idioma declarado no es verificación acústica; región de búsqueda no es país del público.','Duración <=180s no confirma Short: faltan orientación y contexto.','No se certifica viralidad, monetización ni ingresos de terceros.','Sin métricas derivadas ni puntuaciones de viralidad; revisar permisos específicos antes de implementarlas.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['search','channel']);p.add_argument('query');p.add_argument('--language');p.add_argument('--strict-language',action='store_true');p.add_argument('--region');p.add_argument('--after');p.add_argument('--before');p.add_argument('--pages',type=int,default=1);p.add_argument('--min-seconds',type=int,default=0);p.add_argument('--max-seconds',type=int);p.add_argument('--min-views',type=int,default=0);p.add_argument('--max-views',type=int);p.add_argument('--min-subscribers',type=int);p.add_argument('--max-subscribers',type=int);p.add_argument('--format',choices=['any','short_candidate','over_3m'],default='any');a=p.parse_args()
    f=Filters(**{k:getattr(a,k) for k in Filters.__dataclass_fields__})
    try:
        c=YouTube();r=c.channel(a.query,f,a.pages) if a.mode=='channel' else c.search(a.query,f,a.region,a.after,a.before,a.pages)
        print(json.dumps(r,ensure_ascii=False,indent=2))
    except (Unavailable,ValueError,KeyError,TypeError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
