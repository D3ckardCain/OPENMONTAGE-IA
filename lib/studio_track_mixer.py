"""Two logical lane strips; no new timeline or playback-only state."""
from copy import deepcopy

DEFAULT = {'gain': 1., 'muted': False, 'solo': False}


def normalize(value):
    from lib.studio_editor import number
    if not isinstance(value, dict) or set(value) - {'video', 'audio'}:
        raise ValueError('Mezclador: pistas video/audio exclusivamente')
    result = {}
    for lane in ('video', 'audio'):
        settings = value.get(lane, {})
        if not isinstance(settings, dict) or set(settings) - set(DEFAULT):
            raise ValueError('Control de pista desconocido')
        strip = {**DEFAULT, **settings}
        strip['gain'] = number(strip['gain'], 0, 4)
        if any(type(strip[k]) is not bool for k in ('muted', 'solo')):
            raise ValueError('Silencio y solo requieren booleanos')
        result[lane] = strip
    return result


def apply(edl, data):
    if data.get('operation') != 'track_mixer':
        return False
    value = normalize(data['mixer'])
    if all(strip == DEFAULT for strip in value.values()):
        edl.pop('track_mixer', None)
    else:
        edl['track_mixer'] = deepcopy(value)
    return True


def gain(edl, lane):
    strips = normalize(edl.get('track_mixer', {}))
    strip = strips[lane]
    if strip['muted'] or (any(s['solo'] for s in strips.values()) and not strip['solo']):
        return 0.
    return strip['gain']


def effective(edl):
    values = {lane: gain(edl, lane) for lane in ('video', 'audio')}
    return values if any(v != 1 for v in values.values()) else None
