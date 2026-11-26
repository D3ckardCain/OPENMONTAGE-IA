"""Centred source-handle crossfades, preserving the existing timeline clock."""
import math

RENDER_CONTRACT = 'crossfade-centered-source-handles-sample-v1'


def cross_seconds(clip):
    value = clip.get('transition', {})
    return value.get('duration_seconds', 0) if value.get('type') == 'crossfade' else 0


def handles(edl, index):
    cuts = edl['cuts']
    return cross_seconds(cuts[index]) / 2, cross_seconds(cuts[index + 1]) / 2 if index + 1 < len(cuts) else 0


def footprint(clip):
    transition = clip.get('transition', {})
    duration = transition.get('duration_seconds', 0)
    return duration / 2 if transition.get('type') == 'crossfade' else duration


def set_transition(edl, item, seconds):
    from lib import studio_editor as edit
    fps = edl['output']['fps']
    value = edit.number(seconds, 2 / fps, 2)
    count = 2 * math.floor(value * fps / 2 + .5)
    item['transition'] = {'type': 'crossfade', 'duration_seconds': count / fps,
                          'alignment': 'center_source_handles', 'audio_curve': 'linear'}


def validate(edl):
    from lib import studio_editor as edit
    fps = edl['output']['fps']
    for index, item in enumerate(edl['cuts']):
        transition = item.get('transition', {})
        if transition.get('type') == 'crossfade':
            seconds = edit.number(transition['duration_seconds'], 2 / fps, 2)
            count = seconds * fps
            if index == 0 or abs(count - round(count)) > 1e-7 or round(count) % 2:
                raise ValueError('Fundido cruzado requiere un corte anterior y duración par en fotogramas')
            if 48000 % fps:
                raise ValueError('Fundido cruzado: usa FPS divisor de 48000 para alinear fotogramas y muestras')
            if transition.get('alignment') != 'center_source_handles' or transition.get('audio_curve') != 'linear':
                raise ValueError('Semántica de fundido cruzado no admitida')
        before, after = handles(edl, index)
        if not before and not after:
            continue
        if item.get('kind') == 'gap':
            raise ValueError('El fundido cruzado requiere vídeo real a ambos lados del corte')
        info = edl['sources'][item['source_id']]
        if item['in_seconds'] - before * item['speed'] < -1e-8:
            raise ValueError('Falta margen de fuente antes del clip entrante; recorta su entrada primero')
        if item['out_seconds'] + after * item['speed'] > info['duration'] + 1e-8:
            raise ValueError('Falta margen de fuente después del clip anterior; recorta su salida primero')
        if item.get('fade_in') or item.get('fade_out'):
            raise ValueError('Quita los fades individuales de los clips antes de usar el fundido cruzado')


def join(edl, filters, target):
    from lib import studio_editor as edit
    fps = edl['output']['fps']
    cuts = edl['cuts']
    lengths = [edit.frames(clip, fps) / fps + sum(handles(edl, i)) for i, clip in enumerate(cuts)]
    current = lengths[0]
    video, audio = 'v0', 'a0'
    for index in range(1, len(cuts)):
        seconds = cross_seconds(cuts[index])
        next_video, next_audio = f'joinedv{index}', f'joineda{index}'
        if seconds:
            filters.append(f'[{video}][v{index}]xfade=transition=fade:duration={seconds:.12g}:'
                           f'offset={current-seconds:.12g},settb=1/{fps},setpts=N[{next_video}]')
            filters.append(f'[{audio}][a{index}]acrossfade=d={seconds:.12g}:o=1:c1=tri:c2=tri,'
                           f'asettb=1/48000,asetpts=N/SR/TB[{next_audio}]')
        else:
            temporary = f'concatv{index}'
            temporary_audio = f'concata{index}'
            filters.append(f'[{video}][{audio}][v{index}][a{index}]concat=n=2:v=1:a=1[{temporary}][{temporary_audio}]')
            filters.append(f'[{temporary}]settb=1/{fps},setpts=N[{next_video}]')
            filters.append(f'[{temporary_audio}]asettb=1/48000,asetpts=N/SR/TB[{next_audio}]')
        current += lengths[index] - seconds
        video, audio = next_video, next_audio
    filters.append(f'[{video}]trim=end_frame={round(edit.duration(edl)*fps)},format=yuv420p[{target}]')
    filters.append(f'[{audio}]asettb=1/48000,asetpts=N/SR/TB,atrim=end_sample={round(edit.duration(edl)*48000)}[baseaudio]')
