"""Source-clock position curves for existing editable layers; no new timeline."""
import math

INTERPOLATIONS = ('linear', 'hold', 'smooth', 'bezier')


def validate(value, layer, source_duration):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {'clock', 'points'} or value['clock'] != 'source_seconds':
        raise ValueError('Keyframes: reloj source_seconds y points requeridos')
    points = value['points']
    if not isinstance(points, list) or not 2 <= len(points) <= 32:
        raise ValueError('Keyframes: entre 2 y 32 puntos')
    result = []
    for point in points:
        if not isinstance(point, dict) or set(point)-{'seconds','x','y','interpolation','control_points'} or not {'seconds','x','y','interpolation'} <= set(point):
            raise ValueError('Keyframe requiere seconds, x, y e interpolation')
        numbers = [point[k] for k in ('seconds', 'x', 'y')]
        if any(type(n) not in (int, float) or not math.isfinite(n) for n in numbers):
            raise ValueError('Keyframes requieren números finitos')
        seconds, x, y = numbers
        if not 0 <= seconds <= source_duration or (result and seconds <= result[-1]['seconds']):
            raise ValueError('Tiempos de fuente crecientes y dentro del medio')
        if not 0 <= x <= 1-layer['width']+1e-9 or not 0 <= y <= 1-layer['height']+1e-9:
            raise ValueError('Los keyframes sacarían la capa del lienzo')
        if point['interpolation'] not in INTERPOLATIONS:
            raise ValueError('Interpolación: linear, hold o smooth')
        from lib.studio_transform_keyframes import controls
        controls(point)
        result.append(dict(point))
    return {'clock': 'source_seconds', 'points': result}


def expression(points, axis, clock):
    """FFmpeg expression; finite validated numbers only, no user expressions."""
    expression = repr(float(points[-1][axis]))
    for left, right in reversed(list(zip(points, points[1:]))):
        a, b = left['seconds'], right['seconds']
        progress = f'clip((({clock})-{a})/{b-a},0,1)'
        if left['interpolation'] == 'hold':
            segment = repr(float(left[axis]))
        else:
            if left['interpolation'] == 'smooth':
                progress = f'({progress})*({progress})*(3-2*({progress}))'
            segment = f"({left[axis]}+({right[axis]-left[axis]})*({progress}))"
        expression = f'if(lt(({clock}),{b}),{segment},{expression})'
    return f"if(lt(({clock}),{points[0]['seconds']}),{points[0][axis]},{expression})"


def overlay_position(layer, width, height):
    points = layer['position_keyframes']['points']
    clock = f"{layer['in_seconds']}+(t-{layer['start_seconds']})*{layer['speed']}"
    return tuple(f"'{size}*({expression(points, axis, clock)})'" for size, axis in ((width, 'x'), (height, 'y')))
