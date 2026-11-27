"""Explicit music clips ducked by the existing video-audio lane, locally."""
from copy import deepcopy

DEFAULT = {'enabled': True, 'bypass': False, 'threshold_db': -30.,
           'ratio': 6., 'attack_ms': 20., 'release_ms': 250.}
RENDER_CONTRACT = 'video-key-music-sidechain-v1'


def normalize(value):
    from lib.studio_editor import number
    if not isinstance(value, dict) or set(value)-set(DEFAULT):
        raise ValueError('Parámetros de ducking desconocidos')
    result = {**DEFAULT, **value}
    for key in ('enabled', 'bypass'):
        if type(result[key]) is not bool:
            raise ValueError('Ducking enabled/bypass requiere booleanos')
    for key, low, high in [('threshold_db', -50, -6), ('ratio', 1, 20),
                           ('attack_ms', 2, 200), ('release_ms', 20, 2000)]:
        result[key] = number(result[key], low, high)
    return result


def validate(edl):
    if 'audio_ducking' in edl:
        normalize(edl['audio_ducking'])
    for clip in edl['audio_tracks']:
        if 'ducking_music' in clip and type(clip['ducking_music']) is not bool:
            raise ValueError('Marca de música requiere booleano')


def apply(edl, data):
    if data.get('operation') != 'audio_ducking':
        return False
    from lib import studio_editor as edit
    settings = data['settings']
    ids = data.get('music_ids', [])
    if not isinstance(ids, list) or any(not isinstance(k, str) for k in ids) or len(set(ids)) != len(ids):
        raise ValueError('Selecciona clips de música distintos')
    if set(ids)-{c['id'] for c in edl['audio_tracks']}:
        raise ValueError('Clip de música ausente: solo clips de audio añadidos')
    value = normalize(settings) if settings is not None else None
    if value and value['enabled'] and not ids:
        raise ValueError('Selecciona al menos un clip de música')
    for clip in edl['audio_tracks']:
        marked = value is not None and clip['id'] in ids
        if bool(clip.get('ducking_music')) != marked and clip.get('locked'):
            raise edit.Conflict('Desbloquea el clip antes de cambiar su función de música')
    for clip in edl['audio_tracks']:
        if value is not None and clip['id'] in ids:
            if not edl['sources'][clip['source_id']].get('audio'):
                raise ValueError('El clip de música no contiene audio')
            clip['ducking_music'] = True
        else:
            clip.pop('ducking_music', None)
    if value is None:
        edl.pop('audio_ducking', None)
    else:
        edl['audio_ducking'] = deepcopy(value)
    return True


def effective(edl):
    value = normalize(edl['audio_ducking']) if 'audio_ducking' in edl else None
    if not value or not value['enabled'] or value['bypass'] or value['ratio'] == 1:
        return None
    if not any(c.get('ducking_music') for c in edl['audio_tracks']):
        return None
    return {k: v for k, v in value.items() if k not in ('enabled', 'bypass')}


def mix_inputs(edl, filters,voice_label='[baseaudio]'):
    """Same asplit/sidechaincompress pattern as AudioMixer, no fixed attenuation."""
    labels = [(clip, f'[a{i+len(edl["cuts"])}]') for i, clip in enumerate(edl['audio_tracks'])]
    value = effective(edl)
    if value is None:
        return voice_label+''.join(label for _, label in labels), len(labels)+1
    from lib.studio_editor import duration
    music = [label for c, label in labels if c.get('ducking_music')]
    other = [label for c, label in labels if not c.get('ducking_music')]
    filters.append(voice_label+'asplit=2[duck_voice_out][duck_voice_key]')
    filters.append(''.join(music)+f'amix=inputs={len(music)}:duration=longest:normalize=0,'
                   f'apad,atrim=duration={duration(edl)}[duck_music]')
    threshold = 10**(value['threshold_db']/20)
    filters.append('[duck_music][duck_voice_key]sidechaincompress='
                   f"threshold={threshold:.12g}:ratio={value['ratio']:.12g}:"
                   f"attack={value['attack_ms']:.12g}:release={value['release_ms']:.12g}:"
                   'makeup=1:mix=1:detection=rms:link=maximum[duck_music_out]')
    return '[duck_voice_out][duck_music_out]'+''.join(other), len(other)+2
