"""Offline numeric interoperability, running only in the isolated sports Python."""
import importlib.metadata
import json
import math
import sys


def offline(event, args):
    if event.startswith('socket.'):
        raise PermissionError('SPORTS_NETWORK_DISABLED: operación exclusivamente offline')


def number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def coordinate_system(metadata):
    from kloppy.domain import CustomCoordinateSystem, Dimension, MetricPitchDimensions
    from kloppy.domain import NormalizedPitchDimensions, Origin, VerticalOrientation, Unit
    keys = {'pitch_length_m', 'pitch_width_m', 'unit', 'origin', 'y_axis'}
    if not isinstance(metadata, dict) or set(metadata) != keys:
        raise ValueError('SPORTS_METADATA_INVALID: indica longitud, anchura, unidad, origen y eje Y')
    length, width = metadata['pitch_length_m'], metadata['pitch_width_m']
    if not number(length) or not 70 <= length <= 130 or not number(width) or not 40 <= width <= 100 or length <= width:
        raise ValueError('SPORTS_DIMENSIONS_INVALID: dimensiones físicas no compatibles con fútbol de campo')
    unit, origin, y_axis = metadata['unit'], metadata['origin'], metadata['y_axis']
    if unit not in ('m', 'cm', 'normalized') or origin not in ('center', 'top_left', 'bottom_left') or y_axis not in ('up', 'down'):
        raise ValueError('SPORTS_METADATA_INVALID: unidad, origen o eje Y desconocido')
    if (origin == 'top_left' and y_axis != 'down') or (origin == 'bottom_left' and y_axis != 'up'):
        raise ValueError('SPORTS_ORIENTATION_INVALID: origen y dirección del eje Y incompatibles')
    xmax, ymax = (1, 1) if unit == 'normalized' else (length, width)
    if unit == 'cm':
        xmax, ymax = xmax * 100, ymax * 100
    x = Dimension(-xmax / 2, xmax / 2) if origin == 'center' else Dimension(0, xmax)
    y = Dimension(-ymax / 2, ymax / 2) if origin == 'center' else Dimension(0, ymax)
    if unit == 'normalized':
        dimensions = NormalizedPitchDimensions(x_dim=x, y_dim=y, pitch_length=length, pitch_width=width)
    else:
        dimensions = MetricPitchDimensions(x_dim=x, y_dim=y, pitch_length=length,
                                           pitch_width=width, standardized=False)
        if unit == 'cm':
            dimensions = dimensions.convert(Unit.CENTIMETERS)
            # convert also scales bounds; the declared bounds are already centimeters.
            dimensions.x_dim, dimensions.y_dim = x, y
    return CustomCoordinateSystem(
        origin={'center': Origin.CENTER, 'top_left': Origin.TOP_LEFT, 'bottom_left': Origin.BOTTOM_LEFT}[origin],
        vertical_orientation=VerticalOrientation.TOP_TO_BOTTOM if y_axis == 'down' else VerticalOrientation.BOTTOM_TO_TOP,
        pitch_dimensions=dimensions)


def transform(data):
    from kloppy.domain import Point, VerticalOrientation
    from mplsoccer import Standardizer
    if not isinstance(data, dict) or set(data) != {'source', 'target', 'points'}:
        raise ValueError('SPORTS_INPUT_INVALID: se requieren source, target y points')
    source, target = coordinate_system(data['source']), coordinate_system(data['target'])
    for name in ('pitch_length_m', 'pitch_width_m'):
        if data['source'][name] != data['target'][name]:
            raise ValueError('SPORTS_DIMENSIONS_MISMATCH: no se infiere un cambio de campo físico')
    points = data['points']
    if not isinstance(points, list) or not 1 <= len(points) <= 1000:
        raise ValueError('SPORTS_POINTS_INVALID: indica entre 1 y 1000 puntos')
    length, width = source.pitch_length, source.pitch_width
    def to_metric(point, system):
        dims = system.pitch_dimensions
        bx, by = dims.x_dim.to_base(point[0]), dims.y_dim.to_base(point[1])
        if not 0 <= bx <= 1 or not 0 <= by <= 1:
            raise ValueError('SPORTS_POINT_OUTSIDE: coordenada fuera del campo; no se recorta silenciosamente')
        if system.vertical_orientation == VerticalOrientation.TOP_TO_BOTTOM:
            by = 1 - by
        return bx * length, by * width
    def from_metric(point, system):
        bx, by = point[0] / length, point[1] / width
        if system.vertical_orientation == VerticalOrientation.TOP_TO_BOTTOM:
            by = 1 - by
        dims = system.pitch_dimensions
        return [dims.x_dim.from_base(bx), dims.y_dim.from_base(by)]
    for point in points:
        if not isinstance(point, list) or len(point) != 2 or not all(number(v) for v in point):
            raise ValueError('SPORTS_POINTS_INVALID: coordenadas XY finitas requeridas')
    metric = [to_metric(point, source) for point in points]
    # The public Standardizer replaces the broken experimental to_mplsoccer bridge.
    standard = Standardizer(pitch_from='custom', pitch_to='statsbomb', length_from=length, width_from=width)
    sx, sy = standard.transform([p[0] for p in metric], [p[1] for p in metric])
    rx, ry = standard.transform(sx, sy, reverse=True)
    error = max(max(abs(a - x), abs(b - y)) for (a, b), x, y in zip(metric, rx, ry))
    if error > 1e-8:
        raise ValueError('SPORTS_ROUNDTRIP_FAILED: conversión MPLSoccer no reversible dentro de tolerancia')
    converted = [from_metric(point, target) for point in metric]
    back = [from_metric(to_metric(point, target), source) for point in converted]
    source_error = max(abs(a - b) for expected, actual in zip(points, back) for a, b in zip(expected, actual))
    if source_error > 1e-7:
        raise ValueError('SPORTS_ROUNDTRIP_FAILED: conversión de unidades/orientación no reversible')
    return {'source': data['source'], 'target': data['target'], 'points': converted,
            'mplsoccer_statsbomb': {'unit': 'provider_grid', 'origin': 'top_left', 'y_axis': 'down',
                                   'x_range': [0, 120], 'y_range': [0, 80],
                                   'points': [[float(x), float(y)] for x, y in zip(sx, sy)]},
            'consecutive_distances_m': [Point(*a).distance_to(Point(*b)) for a, b in zip(metric, metric[1:])],
            'roundtrip_max_error_m': error, 'roundtrip_max_error_source_units': source_error,
            'bridge': 'kloppy.Dimension -> metric -> mplsoccer.Standardizer', 'figures_generated': False}


def main():
    sys.addaudithook(offline)
    try:
        versions = {name: importlib.metadata.version(name) for name in ('kloppy', 'mplsoccer')}
        if versions != {'kloppy': '3.19.1', 'mplsoccer': '1.8.1'}:
            raise ValueError('SPORTS_RUNTIME_VERSION: versiones no validadas: ' + str(versions))
        from kloppy.domain import Point
        from mplsoccer import Standardizer
        if sys.argv[1:] == ['doctor']:
            result = {'versions': versions, 'python': sys.version.split()[0], 'network_accessed': False,
                      'legacy_bridge_used': False, 'figures_generated': False}
        else:
            raw = sys.stdin.buffer.read(500001)
            if not raw or len(raw) > 500000:
                raise ValueError('SPORTS_INPUT_INVALID: JSON vacío o demasiado grande')
            result = transform(json.loads(raw))
            result.update({'versions': versions, 'network_accessed': False})
        sys.stdout.buffer.write(json.dumps(result, allow_nan=False).encode('utf-8'))
        return 0
    except Exception as exc:
        message = str(exc)
        if not message.startswith('SPORTS_'):
            message = 'SPORTS_WORKER_ERROR: ' + message
        sys.stdout.buffer.write(json.dumps({'error': message[:500]}).encode('utf-8'))
        return 1


if __name__ == '__main__':
    sys.exit(main())
