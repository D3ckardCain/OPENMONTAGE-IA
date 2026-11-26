"""Attenuating stereo balance on the shared clip, without channel mixing."""


def apply(edl, data):
    if data.get('operation') != 'audio_balance':
        return False
    from lib import studio_editor as edit
    track = data.get('track', 'video')
    if track not in ('video', 'audio'):
        raise ValueError('Pista desconocida')
    item = edit._item(edl['audio_tracks'] if track == 'audio' else edl['cuts'], data['id'])
    if item.get('locked'):
        raise edit.Conflict('Clip bloqueado; desbloquéalo antes de editar')
    if item.get('kind') == 'gap' or not edl['sources'][item['source_id']].get('audio'):
        raise ValueError('El clip no contiene audio para ajustar su balance')
    value = edit.number(data['balance'], -1, 1)
    if value == 0:
        item.pop('stereo_balance', None)
    else:
        item['stereo_balance'] = value
    return True


def filter_suffix(clip):
    """After stereo conversion: centre is bit-neutral; extremes mute one side."""
    from lib.studio_editor import number
    value = number(clip.get('stereo_balance', 0), -1, 1)
    if value == 0:
        return ''
    left, right = 1 - max(0, value), 1 + min(0, value)
    return f',pan=stereo|c0={left:.12g}*c0|c1={right:.12g}*c1'


def validate(edl):
    from lib.studio_editor import number
    for item in edl['cuts'] + edl['audio_tracks']:
        if 'stereo_balance' in item:
            number(item['stereo_balance'], -1, 1)
