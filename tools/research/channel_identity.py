"""Parse channel identifiers without fetching or following user-provided URLs."""
import re
import unicodedata
from urllib.parse import urlsplit, unquote
from .youtube_client import Unavailable


class InvalidChannelQuery(Unavailable):
    pass


def parse_channel_query(value):
    if not isinstance(value,str) or not value.strip() or len(value)>200:
        raise InvalidChannelQuery('Escribe un tema, @usuario o enlace de canal de hasta 200 caracteres')
    value=value.strip()
    channel_id=re.compile(r'UC[A-Za-z0-9_-]{22}')
    def handle(text):
        if not text or len(text)>100 or any(ch.isspace() or unicodedata.category(ch).startswith('C')
                or ch in '/\\?&#:%@' for ch in text):
            raise InvalidChannelQuery('Usuario inválido; copia el @usuario del canal')
        return ('handle',text)
    if value.startswith('@'):
        return handle(value[1:])
    if channel_id.fullmatch(value):
        return ('id',value)
    bare=bool(re.match(r'^(?:www\.|m\.)?youtube\.com/',value,re.I))
    if bare or '://' in value or value.startswith('//'):
        try:
            url=urlsplit('https://'+value if bare else value)
            if (url.scheme not in {'http','https'} or url.hostname not in {'youtube.com','www.youtube.com','m.youtube.com'}
                    or url.username is not None or url.password is not None or url.port is not None):
                raise ValueError
            path=unquote(url.path,errors='strict').strip('/')
        except (ValueError,UnicodeDecodeError):
            raise InvalidChannelQuery('Usa un enlace de canal de youtube.com') from None
        parts=path.split('/')
        tabs={'videos','shorts','streams','featured','about','playlists','community','podcasts'}
        if parts[0].startswith('@') and (len(parts)==1 or len(parts)==2 and parts[1] in tabs):
            return handle(parts[0][1:])
        if parts[0] in {'channel','user'} and (len(parts)==2 or len(parts)==3 and parts[2] in tabs):
            identifier=parts[1]
            if parts[0]=='channel' and channel_id.fullmatch(identifier):
                return ('id',identifier)
            if parts[0]=='user' and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',identifier):
                return ('username',identifier)
        raise InvalidChannelQuery('Ese enlace no identifica un canal admitido; usa su @usuario o /channel/UC…')
    return ('keywords',value)
