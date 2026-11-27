"""Validated non-generative effects on the shared manual EDL."""
import uuid

TRANSFORM_DEFAULT = {'fit': 'pad', 'rotation': 0, 'flip_h': False, 'flip_v': False,
                     'zoom': 1., 'focus_x': .5, 'focus_y': .5}


def apply_effect(edl, data):
    from lib import studio_editor as edit
    op = data.get('operation')
    if op == 'transform':
        item = edit._item(edl['cuts'], data['id'])
        if item.get('locked'):
            raise edit.Conflict('Clip bloqueado')
        if item.get('kind') == 'gap':
            raise ValueError('Un intervalo vacío no tiene encuadre de fuente')
        values = {**TRANSFORM_DEFAULT, **{k: data[k] for k in TRANSFORM_DEFAULT if k in data}}
        if values['fit'] not in ('pad', 'crop') or type(values['rotation']) is not int or values['rotation'] not in (0, 90, 180, 270):
            raise ValueError('Encaje o giro no admitido')
        if any(type(values[k]) is not bool for k in ('flip_h', 'flip_v')):
            raise ValueError('Reflejos requieren booleanos')
        values['zoom'] = edit.number(values['zoom'], 1, 4)
        for key in ('focus_x', 'focus_y'):
            values[key] = edit.number(values[key], 0, 1)
        if values['fit'] == 'pad' and (values['zoom'] != 1 or values['focus_x'] != .5 or values['focus_y'] != .5):
            raise ValueError('Zoom y foco requieren recorte explícito para llenar')
        if values == TRANSFORM_DEFAULT:
            item.pop('transform', None)
        else:
            item['transform'] = values
    elif op in ('title_add', 'title_update', 'title_remove'):
        titles = edl.setdefault('titles', [])
        if op == 'title_remove':
            titles.remove(edit._item(titles, data['id']))
        else:
            text = data.get('text')
            if not isinstance(text, str) or not text.strip() or len(text) > 1000:
                raise ValueError('Título: texto de 1 a 1000 caracteres')
            start = edit.number(data['start_seconds'])
            end = edit.number(data['end_seconds'], start+.001, edit.duration(edl))
            position = data.get('position', 'center')
            if position not in ('bottom', 'center', 'top'):
                raise ValueError('Posición de título desconocida')
            value = {'text': text, 'start_seconds': start, 'end_seconds': end,
                     'size': edit.number(data.get('size', 64), 12, 200), 'position': position}
            if op == 'title_add':
                if len(titles) >= 20:
                    raise ValueError('Límite de esta entrega: 20 títulos')
                titles.append({'id': uuid.uuid4().hex, **value})
            else:
                item=edit._item(titles, data['id']);item.update(value)
                if 'anchor_x' in data:
                    if not item.get('component_layout'):raise ValueError('Ancla horizontal disponible en componentes')
                    item['component_layout']['anchor_x']=edit.number(data['anchor_x'],0,1)
    elif op == 'output_custom':
        width, height, fps = data.get('width'), data.get('height'), data.get('fps')
        if any(type(v) is not int for v in (width, height, fps)) or not 64 <= width <= 3840 or not 64 <= height <= 3840 or width % 2 or height % 2 or width*height > 3840*2160 or not 1 <= fps <= 60:
            raise ValueError('Salida: dimensiones pares64–3840, máximo4K y FPS entero1–60')
        platform = data.get('platform', 'local')
        if platform not in ('local', 'youtube', 'tiktok', 'facebook', 'instagram'):
            raise ValueError('Destino no admitido')
        name = data.get('preset_name', '')
        if not isinstance(name, str) or len(name) > 120:
            raise ValueError('Nombre de preset demasiado largo')
        background=edl['output'].get('background')
        edl['output'] = {'ratio': 'custom', 'width': width, 'height': height, 'fps': fps,
                         'fit': 'pad', 'platform': platform, 'preset_name': name}
        if background:edl['output']['background']=background
    elif op == 'audio_mix':
        previous = edl.get('audio_mix', {})
        if not isinstance(previous, dict):
            raise ValueError('La mezcla guardada no es válida')
        normalize = data.get('normalize', previous.get('normalize', False))
        if type(normalize) is not bool:
            raise ValueError('Normalización requiere booleano')
        edl['audio_mix'] = {
            'normalize': normalize,
            'target_lufs': edit.number(data.get('target_lufs', previous.get('target_lufs', -16)), -40, -5),
            'gain': edit.number(data.get('gain', previous.get('gain', 1)), 0, 4),
        }
    else:
        return False
    return True


def transform_filter(width, height, transform):
    values = {**TRANSFORM_DEFAULT, **(transform or {})}
    filters = []
    if values['rotation'] == 90:
        filters.append('transpose=clock')
    elif values['rotation'] == 270:
        filters.append('transpose=cclock')
    elif values['rotation'] == 180:
        filters.extend(['hflip', 'vflip'])
    for key, name in [('flip_h', 'hflip'), ('flip_v', 'vflip')]:
        if values[key]:
            filters.append(name)
    if values['fit'] == 'crop':
        w, h = max(width, round(width*values['zoom']/2)*2), max(height, round(height*values['zoom']/2)*2)
        filters.extend([f'scale={w}:{h}:force_original_aspect_ratio=increase',
                        f"crop={width}:{height}:(iw-ow)*{values['focus_x']}:(ih-oh)*{values['focus_y']}"])
    else:
        filters.extend([f'scale={width}:{height}:force_original_aspect_ratio=decrease',
                        f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2'])
    return ','.join(filters)
