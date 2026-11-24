"""FreeCAD Units API with allowlisted units and no documents or geometry."""
import json
import math
import os
from pathlib import Path
import sys

UNITS = {
    'length': ('mm', 'cm', 'm', 'in', 'ft'),
    'area': ('mm^2', 'cm^2', 'm^2', 'in^2'),
    'volume': ('mm^3', 'cm^3', 'm^3', 'in^3'),
    'angle': ('deg', 'rad'),
    'mass': ('g', 'kg'),
    'time': ('s', 'min', 'h'),
    'force': ('N', 'kN'),
    'pressure': ('Pa', 'kPa', 'MPa'),
}


def validate_payload(data):
    if not isinstance(data, dict) or set(data) != {'source_unit', 'target_unit', 'values'}:
        raise ValueError('FREECAD_INPUT_INVALID: campos desconocidos')
    source, target, values = data['source_unit'], data['target_unit'], data['values']
    dimension = next((kind for kind, units in UNITS.items() if source in units and target in units), None)
    if dimension is None:
        raise ValueError('FREECAD_UNIT_INVALID: unidades no admitidas o dimensiones incompatibles')
    if not isinstance(values, list) or not 1 <= len(values) <= 1000 or any(
            type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1e12 for v in values):
        raise ValueError('FREECAD_VALUE_INVALID: 1–1000 números finitos con magnitud máxima 1e12')
    return source, target, values, dimension


def main():
    raw = sys.stdin.buffer.read(65537)
    if not raw or len(raw) > 65536:
        raise ValueError('FREECAD_INPUT_INVALID: entrada vacía o demasiado grande')
    source, target, values, dimension = validate_payload(json.loads(raw))
    def network_guard(event, args):
        if event.startswith('socket.'):
            raise RuntimeError('FREECAD_NETWORK_DISABLED')
    sys.addaudithook(network_guard)
    import FreeCAD
    if Path(FreeCAD.ConfigGet('UserAppData')).resolve() != Path(os.environ['FREECAD_USER_DATA']).resolve():
        raise ValueError('FREECAD_PROFILE_INVALID: perfil temporal no confirmado')
    if FreeCAD.GuiUp or FreeCAD.listDocuments():
        raise ValueError('FREECAD_PROCESS_INVALID: se requiere contexto sin GUI ni documentos')
    converted, errors = [], []
    for value in values:
        quantity = FreeCAD.Units.Quantity(format(value, '.17g') + ' ' + source)
        result = quantity.getValueAs(target).Value
        back = FreeCAD.Units.Quantity(format(result, '.17g') + ' ' + target).getValueAs(source).Value
        if not math.isfinite(result) or not math.isfinite(back):
            raise ValueError('FREECAD_RESULT_INVALID: conversión no finita')
        converted.append(result)
        errors.append(abs(back - value))
    if FreeCAD.listDocuments():
        raise ValueError('FREECAD_PROCESS_INVALID: se creó un documento inesperado')
    return {'freecad_version': '.'.join(FreeCAD.Version()[:3]), 'dimension': dimension,
            'source_unit': source, 'target_unit': target, 'values': converted,
            'roundtrip_max_error': max(errors), 'roundtrip_error_unit': source,
            'gui_loaded': False, 'documents_created': False, 'geometry_created': False, 'temporary_profile_verified': True,
            'model_inference': False}


if __name__ == '__main__':
    try:
        print(json.dumps(main(), allow_nan=False))
    except Exception as exc:
        print(json.dumps({'error': str(exc)[:500]}))
        sys.exit(1)
