"""Atomic metadata operations for the shared manual timeline. No I/O or inference."""
from copy import deepcopy
import uuid

CAPABILITIES = ['batch', 'duplicate', 'markers', 'flags', 'audio_trim_position', 'delete_keep_gap', 'ripple_delete',
                'transform', 'titles', 'output_custom', 'audio_mix', 'transition', 'layers']


def assert_editable(edl, data):
    from lib import studio_editor as edit
    op = data.get('operation')
    if op in ('trim', 'split', 'remove', 'move', 'clip', 'audio_trim_position'):
        items = edl['audio_tracks'] if data.get('track') == 'audio' or op == 'audio_trim_position' else edl['cuts']
        item = edit._item(items, data.get('id'))
        if item.get('locked') and not (op == 'clip' and data.get('locked') is False):
            raise edit.Conflict('Clip bloqueado; desbloquéalo antes de editar')
        if items is edl['cuts']:
            index = items.index(item)
            changes_length = op == 'remove'
            if op in ('trim', 'clip'):
                proposed = {**item, **{k: data[k] for k in ('in_seconds', 'out_seconds', 'speed') if k in data}}
                if all(isinstance(proposed[k], (int, float)) and not isinstance(proposed[k], bool) for k in ('in_seconds', 'out_seconds', 'speed')) and proposed['speed'] > 0:
                    changes_length = edit.frames(proposed, edl['output']['fps']) != edit.frames(item, edl['output']['fps'])
            if changes_length and any(c.get('locked') for c in items[index+1:]):
                raise edit.Conflict('La operación movería clips posteriores bloqueados')
            if op == 'move' and type(data.get('index')) is int:
                first, last = sorted((index, data['index']))
                if any(c.get('locked') for c in items[max(0, first):last+1]):
                    raise edit.Conflict('La reordenación afectaría clips bloqueados')


def _selection(edl, data):
    from lib import studio_editor as edit
    if data.get('track', 'video') not in ('video', 'audio'):
        raise ValueError('Pista desconocida')
    items = edl['audio_tracks'] if data.get('track') == 'audio' else edl['cuts']
    ids = data.get('ids')
    if not isinstance(ids, list) or not ids or len(set(ids)) != len(ids) or any(not isinstance(k, str) for k in ids):
        raise ValueError('Selecciona IDs de clip distintos')
    selected = [c for c in items if c['id'] in ids]
    if len(selected) != len(ids):
        raise ValueError('La selección contiene clips ausentes')
    if any(c.get('locked') for c in selected):
        raise edit.Conflict('La selección contiene clips bloqueados')
    return items, selected


def _segments(start, end, removed):
    pieces = [(start, end)]
    for a, b in removed:
        next_pieces = []
        for x, y in pieces:
            if x < a:
                next_pieces.append((x, min(y, a)))
            if y > b:
                next_pieces.append((max(x, b), y))
        pieces = [(x, y) for x, y in next_pieces if y - x >= .001-1e-9]
    return pieces


def _ripple_time(time, removed):
    return time - sum(max(0, min(time, b) - a) for a, b in removed)


def apply_timeline(edl, data):
    from lib import studio_editor as edit
    from lib.studio_editor_effects import apply_effect
    from lib.studio_editor_layers import apply_composition
    if apply_composition(edl, data):
        return True
    if apply_effect(edl, data):
        return True
    op = data.get('operation')
    if op == 'duplicate':
        items, selected = _selection(edl, data)
        copies = []
        for item in selected:
            copy = {**deepcopy(item), 'id': uuid.uuid4().hex}
            if data.get('track') == 'audio':
                copy['start_seconds'] += (copy['out_seconds'] - copy['in_seconds']) / copy['speed']
            copies.append(copy)
        index = max(items.index(c) for c in selected) + 1
        if data.get('track') != 'audio' and any(c.get('locked') for c in items[index:]):
            raise edit.Conflict('Duplicar movería clips posteriores bloqueados')
        items[index:index] = copies
    elif op == 'flags':
        items = edl['audio_tracks'] if data.get('track') == 'audio' else edl['cuts']
        if data.get('track', 'video') not in ('video', 'audio'):
            raise ValueError('Pista desconocida')
        item = edit._item(items, data['id'])
        if not any(k in data for k in ('muted', 'solo', 'locked')):
            raise ValueError('Indica mute, solo o bloqueo')
        for key in ('muted', 'solo', 'locked'):
            if key in data:
                if type(data[key]) is not bool:
                    raise ValueError('Mute/solo/bloqueo requieren booleanos')
                item[key] = data[key]
    elif op == 'audio_trim_position':
        if data.get('track') not in (None, 'audio'):
            raise ValueError('Esta operación requiere audio')
        item = edit._item(edl['audio_tracks'], data['id'])
        start = edit.number(data['in_seconds'])
        end = edit.number(data['out_seconds'], start + .001, edl['sources'][item['source_id']]['duration'])
        item.update(in_seconds=start, out_seconds=end, start_seconds=edit.number(data['start_seconds']))
    elif op in ('delete_keep_gap', 'ripple_delete'):
        items, selected = _selection(edl, data)
        if data.get('track') == 'audio':
            items[:] = [c for c in items if c not in selected]
            return True
        removed = []
        time = 0
        for item in items:
            duration = edit.frames(item, edl['output']['fps']) / edl['output']['fps']
            if item in selected:
                removed.append((time, time + duration))
            time += duration
        if op == 'delete_keep_gap':
            for item, (start, end) in zip(selected, removed):
                seconds = end - start
                items[items.index(item)] = {'id': uuid.uuid4().hex, 'kind': 'gap', 'source': None,
                    'source_id': None, 'in_seconds': 0, 'out_seconds': seconds, 'gap_duration': seconds,
                    'speed': 1, 'muted': True, 'gain': 0, 'fade_in': 0, 'fade_out': 0, 'start_seconds': 0}
        else:
            time = 0
            for clip in items:
                time += edit.frames(clip, edl['output']['fps']) / edl['output']['fps']
                if clip.get('locked') and time > removed[0][0]:
                    raise edit.Conflict('Ripple movería vídeo bloqueado; desbloquéalo antes')
            if any(c.get('locked') and c['start_seconds'] + (c['out_seconds']-c['in_seconds'])/c['speed'] > removed[0][0]
                   for c in edl['audio_tracks']):
                raise edit.Conflict('Ripple afectaría audio bloqueado; desbloquéalo antes')
            items[:] = [c for c in items if c not in selected]
            audio = []
            for clip in edl['audio_tracks']:
                start = clip['start_seconds']
                end = start + (clip['out_seconds']-clip['in_seconds'])/clip['speed']
                for index, (a, b) in enumerate(_segments(start, end, removed)):
                    piece = {**clip, 'id': clip['id'] if index == 0 else uuid.uuid4().hex,
                             'in_seconds': clip['in_seconds']+(a-start)*clip['speed'],
                             'out_seconds': clip['in_seconds']+(b-start)*clip['speed'],
                             'start_seconds': _ripple_time(a, removed),
                             'fade_in': max(0, clip['fade_in']-(a-start)),
                             'fade_out': max(0, clip['fade_out']-(end-b))}
                    audio.append(piece)
            edl['audio_tracks'] = audio
            edl['cues'] = [{**cue, 'start_seconds': _ripple_time(a, removed), 'end_seconds': _ripple_time(b, removed)}
                           for cue in edl['cues'] for a, b in _segments(cue['start_seconds'], cue['end_seconds'], removed)]
            edl['markers'] = [{**m, 'seconds': _ripple_time(m['seconds'], removed)} for m in edl.get('markers', [])
                              if not any(a <= m['seconds'] < b for a, b in removed)]
    elif op in ('marker_add', 'marker_update', 'marker_remove'):
        markers = edl.setdefault('markers', [])
        if op == 'marker_remove':
            markers.remove(edit._item(markers, data['id']))
        else:
            label = data.get('label', edit._item(markers, data['id']).get('label', '') if op == 'marker_update' else '')
            if not isinstance(label, str) or len(label) > 120:
                raise ValueError('Marcador: texto de hasta 120 caracteres')
            end = max(edit.duration(edl), 0, *(c['start_seconds']+(c['out_seconds']-c['in_seconds'])/c['speed'] for c in edl['audio_tracks']))
            seconds = edit.number(data['seconds'], 0, max(end, .001))
            if op == 'marker_add':
                if len(markers) >= 500:
                    raise ValueError('Límite: 500 marcadores')
                markers.append({'id': uuid.uuid4().hex, 'seconds': seconds, 'label': label})
            else:
                edit._item(markers, data['id']).update(seconds=seconds, label=label)
            markers.sort(key=lambda m: m['seconds'])
    else:
        return False
    return True
