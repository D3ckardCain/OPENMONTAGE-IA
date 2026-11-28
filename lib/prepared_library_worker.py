"""Allowlisted offline diagnostics and numeric operations, never media production."""
import importlib.metadata as metadata
import json
import math
import re
from pathlib import Path
import sys


def offline(event, args):
    if event.startswith('socket.'):
        raise PermissionError('LIBRARY_NETWORK_DISABLED: diagnóstico offline')


def check(name):
    if name == 'socceraction':
        import pandas as pd
        from socceraction.spadl import play_left_to_right
        from socceraction.spadl.schema import SPADLSchema
        row = {'game_id': 0, 'original_event_id': None, 'action_id': 0, 'period_id': 1,
               'time_seconds': 0., 'team_id': 2, 'player_id': 0, 'start_x': 10., 'start_y': 20.,
               'end_x': 30., 'end_y': 40., 'bodypart_id': 0, 'type_id': 0, 'result_id': 1}
        data = SPADLSchema.validate(pd.DataFrame([row]))
        flipped = play_left_to_right(data, home_team_id=1)
        assert flipped.start_x.iloc[0] == 95 and flipped.start_y.iloc[0] == 48
        assert flipped.end_x.iloc[0] == 75 and flipped.end_y.iloc[0] == 28
        restored = play_left_to_right(flipped, home_team_id=1)
        pd.testing.assert_frame_equal(data, restored)
        invalid = pd.DataFrame([{**row, 'start_x': 106.}])
        try:
            SPADLSchema.validate(invalid)
        except Exception:
            pass
        else:
            raise ValueError('SPADL accepted a point outside its fixed 105x68 field')
        packages = ['socceraction', 'pandera', 'multimethod', 'numpy', 'pandas']
        checks = ['SPADL schema', 'away team 105x68 orientation and inverse', 'invalid coordinates rejected']
    elif name == 'cq_warehouse':
        import cadquery
        import cq_warehouse.bearing
        import cq_warehouse.extensions
        from cq_warehouse.fastener import polygon_diagonal, decode_imperial_size, read_fastener_parameters_from_csv
        assert abs(polygon_diagonal(10, 6) - 11.547005383792515) < 1e-12
        diameter, pitch = decode_imperial_size('#8-32')
        assert abs(diameter - 4.1656) < 1e-10 and abs(pitch - 0.79375) < 1e-10
        assert len(read_fastener_parameters_from_csv('hex_head_parameters.csv')) > 0
        packages = ['cq_warehouse', 'cadquery', 'cadquery-ocp', 'numpy']
        checks = ['CadQuery/OCP and warehouse module imports', 'fastener numeric dimensions', 'bundled CSV table read']
    elif name == 'soccervision':
        import numpy as np
        from soccervision.calib.homography import apply_homography
        matrix = np.array([[2., 0., 10.], [0., 3., 20.], [0., 0., 1.]])
        points = np.array([[0., 0.], [3., 4.], [-2., 8.]])
        transformed = apply_homography(matrix, points)
        assert np.allclose(transformed, [[10, 20], [16, 32], [6, 44]])
        assert np.allclose(apply_homography(np.linalg.inv(matrix), transformed), points)
        packages = ['soccervision', 'opencv-python', 'supervision', 'numpy']
        checks = ['CPU homography module import', 'synthetic homography and inverse']
    elif name == 'musetalk':
        source = Path(__file__).resolve().parents[1] / '.runtime/musetalk/sources/0a89dec45a01'
        if not source.is_dir():
            raise ValueError('LIBRARY_SOURCE_MISSING: prepara las fuentes verificadas de MuseTalk')
        sys.path.insert(0, str(source))
        import torch
        import musetalk.models.unet
        import musetalk.models.vae
        import mmcv.ops
        from mmpose.apis import init_model
        # Do not import preprocessing: upstream constructs models on import.
        from musetalk.utils.utils import get_file_type
        assert get_file_type('synthetic.wav') == 'unsupported'
        assert get_file_type('synthetic.mp4') == 'video'
        packages = ['torch', 'torchvision', 'diffusers', 'transformers', 'mmcv', 'mmengine', 'mmdet', 'mmpose', 'numpy']
        checks = ['CPU model class imports without construction or weights', 'MMLab API/native operators import',
                  'synthetic filename classification, no file opened']
    elif name == 'tvcalib':
        source = Path(__file__).resolve().parents[1] / '.runtime/tvcalib/sources/1222c5230af2'
        if not source.is_dir():
            raise ValueError('LIBRARY_SOURCE_MISSING: prepara las fuentes verificadas de TVCalib')
        sys.path.insert(0, str(source))
        import torch
        import tvcalib.cam_modules
        import tvcalib.module
        from tvcalib.utils.data_distr import FeatureScalerZScore
        scale = FeatureScalerZScore(10., 2.)
        points = torch.tensor([-1., 0., 1.])
        assert torch.allclose(scale.denormalize(points), torch.tensor([8., 10., 12.]))
        assert torch.allclose(scale.normalize(scale.denormalize(points)), points)
        packages = ['torch', 'torchvision', 'kornia', 'pytorch-lightning', 'numpy', 'scipy']
        checks = ['CPU camera/calibration class imports without construction', 'synthetic feature scaling and inverse']
    else:
        raise ValueError('LIBRARY_UNKNOWN: runtime no admitido')
    return {'runtime': name, 'versions': {name: metadata.version(name) for name in packages},
            'python': sys.version.split()[0],
            'synthetic_checks': checks, 'network_accessed': False, 'real_input_read': False,
            'geometry_generated': False, 'figures_generated': False, 'model_inference_performed': False,
            'weights_loaded': False, 'cuda_validated': False}


def operate(name, data):
    """Functional operations use the same isolated runtimes and offline guard."""
    if name != 'socceraction':
        return operate_component(name, data)
    import pandas as pd
    from socceraction.spadl.schema import SPADLSchema
    from socceraction.spadl import config
    if data.get('coordinate_system') != 'spadl_105x68_bottom_left_home_to_right':
        raise ValueError('SPADL_COORDINATES_REQUIRED: declara el marco SPADL 105x68, metros, origen inferior izquierdo y local hacia la derecha')
    rows = data.get('actions')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError('SPADL_INPUT_INVALID: indica 1–1000 acciones')
    required = {'game_id', 'original_event_id', 'action_id', 'period_id', 'time_seconds', 'team_id', 'player_id',
                'start_x', 'start_y', 'end_x', 'end_y', 'bodypart_id', 'type_id', 'result_id'}
    optional = {'bodypart_name', 'type_name', 'result_name'}
    issues, seen = [], set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) - required - optional or required - set(row):
            issues.append({'row': i, 'field': 'columns', 'reason': 'missing_or_unknown_columns'})
            continue
        for field in ('action_id', 'period_id', 'bodypart_id', 'type_id', 'result_id'):
            if type(row[field]) is not int or row[field] < 0:
                issues.append({'row': i, 'field': field, 'reason': 'integer_required_no_lossy_coercion'})
        for field in ('game_id', 'team_id', 'player_id', 'original_event_id'):
            value = row[field]
            if field == 'original_event_id' and value is None:
                continue
            if type(value) not in (str, int) or (isinstance(value, str) and not 1 <= len(value) <= 200):
                issues.append({'row': i, 'field': field, 'reason': 'identifier_required'})
        for field in ('time_seconds', 'start_x', 'start_y', 'end_x', 'end_y'):
            if type(row[field]) not in (int, float) or not math.isfinite(row[field]):
                issues.append({'row': i, 'field': field, 'reason': 'finite_number_required'})
        key = (str(type(row['game_id'])), str(row['game_id']), str(row['action_id']))
        if key in seen:
            issues.append({'row': i, 'field': 'action_id', 'reason': 'duplicate_action_in_game'})
        seen.add(key)
        for field, values in (('bodypart', config.bodyparts), ('type', config.actiontypes), ('result', config.results)):
            index = row[field + '_id']
            if field + '_name' in row and (type(index) is not int or not 0 <= index < len(values) or row[field + '_name'] != values[index]):
                issues.append({'row': i, 'field': field + '_name', 'reason': 'name_id_mismatch'})
    native_checked = not issues
    native_issue_count = 0
    if native_checked:
        try:
            # Native schema checks enum IDs, periods, bounds and strict columns.
            SPADLSchema.validate(pd.DataFrame(rows), lazy=True)
        except Exception as exc:
            failures = getattr(exc, 'failure_cases', None)
            if failures is None:
                raise
            native_issue_count = len(failures)
            issues = [{'row': str(r.get('index')), 'field': str(r.get('column')),
                       'reason': str(r.get('check'))[:160]} for r in failures.to_dict('records')[:20]]
            if not issues:
                issues = [{'row': None, 'field': 'schema', 'reason': 'native_validation_failed'}]
    return {'valid': not issues, 'issues': issues[:20], 'issues_truncated': max(native_issue_count, len(issues)) > 20,
            'action_count': len(rows), 'coordinate_system': data['coordinate_system'],
            'versions': {key: metadata.version(key) for key in ('socceraction', 'pandera', 'multimethod', 'pandas', 'numpy')},
            'native_schema': 'socceraction.spadl.schema.SPADLSchema',
            'native_schema_checked': native_checked,
            'coordinates_transformed': False, 'provider_events_converted': False,
            'models_trained': False, 'geometry_generated': False, 'figures_generated': False,
            'weights_loaded': False, 'model_inference_performed': False}


def operate_component(name, data):
    if name == 'tvcalib':
        loc, scale, values, mode = (data.get(k) for k in ('loc', 'scale', 'values', 'mode'))
        if type(loc) not in (int, float) or not math.isfinite(loc) or abs(loc) > 1e9 or type(scale) not in (int, float) or not math.isfinite(scale) or not 1e-9 <= scale <= 1e9:
            raise ValueError('TVCALIB_SCALE_INVALID: loc finito<=1e9 y escala positiva1e-9–1e9')
        if mode not in ('normalize', 'denormalize') or not isinstance(values, list) or not 1 <= len(values) <= 1000 or any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1e9 for v in values):
            raise ValueError('TVCALIB_INPUT_INVALID: modo y valores finitos explícitos')
        source = Path(__file__).resolve().parents[1] / '.runtime/tvcalib/sources/1222c5230af2'
        if not source.is_dir():
            raise ValueError('LIBRARY_SOURCE_MISSING: fuentes TVCalib preparadas ausentes')
        sys.path.insert(0, str(source))
        import torch
        from tvcalib.utils.data_distr import FeatureScalerZScore
        with torch.no_grad():
            scaler = FeatureScalerZScore(float(loc), float(scale))
            tensor = torch.tensor(values, dtype=torch.float64, device='cpu')
            transformed = scaler.normalize(tensor) if mode == 'normalize' else scaler.denormalize(tensor)
            restored = scaler.denormalize(transformed) if mode == 'normalize' else scaler.normalize(transformed)
            if not torch.isfinite(transformed).all() or not torch.isfinite(restored).all():
                raise ValueError('TVCALIB_OUTPUT_INVALID: resultado no finito')
            error = float(torch.max(torch.abs(restored - tensor)).item())
        return {'values': transformed.tolist(), 'mode': mode, 'feature_name': data['feature_name'],
                'declared_feature_unit': data['feature_unit'],
                'output_unit': 'dimensionless_z_score' if mode == 'normalize' else data['feature_unit'],
                'roundtrip_max_error_in_input_units': error, 'dtype': 'float64',
                'versions': {p: metadata.version(p) for p in ('torch', 'numpy')}, 'component_source': 'tvcalib.utils.data_distr.FeatureScalerZScore',
                'camera_calibration_performed': False, 'geometry_generated': False, 'figures_generated': False,
                'weights_loaded': False, 'model_inference_performed': False}
    if name == 'musetalk':
        chunks, frames, batch, delay = (data.get(k) for k in ('audio_chunk_count', 'latent_frame_count', 'batch_size', 'delay_frame'))
        if any(type(v) is not int for v in (chunks, frames, batch, delay)) or not 1 <= chunks <= 32 or not 1 <= frames <= 32 or not 1 <= batch <= 16 or not 0 <= delay <= 1000:
            raise ValueError('MUSETALK_PLAN_INVALID: chunks/frames1–32, batch1–16, delay0–1000')
        source = Path(__file__).resolve().parents[1] / '.runtime/musetalk/sources/0a89dec45a01'
        if not source.is_dir():
            raise ValueError('LIBRARY_SOURCE_MISSING: fuentes MuseTalk preparadas ausentes')
        sys.path.insert(0, str(source))
        import torch
        from musetalk.utils.utils import datagen
        with torch.no_grad():
            conditioning = [torch.full((2, 384), float(i), device='cpu') for i in range(chunks)]
            latents = [torch.full((1, 4, 2, 2), float(i), device='cpu') for i in range(frames)]
            batches = []
            for audio, latent in datagen(conditioning, latents, batch_size=batch, delay_frame=delay, device='cpu'):
                batches.append({'chunk_indices': [int(v) for v in audio[:, 0, 0].tolist()],
                                'latent_indices': [int(v) for v in latent[:, 0, 0, 0].tolist()],
                                'conditioning_shape': list(audio.shape), 'latent_shape': list(latent.shape)})
        if [i for b in batches for i in b['chunk_indices']] != list(range(chunks)):
            raise ValueError('MUSETALK_PLAN_INVALID: se perdieron chunks')
        return {'batches': batches, 'batch_count': len(batches), 'placeholder_tensors_only': True,
                'versions': {p: metadata.version(p) for p in ('torch', 'diffusers', 'transformers')},
                'geometry_generated': False, 'figures_generated': False, 'weights_loaded': False,
                'model_inference_performed': False, 'audio_decoded': False, 'avatar_generated': False}
    if name == 'soccervision':
        import numpy as np
        from soccervision.calib.homography import apply_homography
        h = np.asarray(data['matrix'], dtype=np.float64)
        points = np.asarray(data['points'], dtype=np.float64)
        if h.shape != (3, 3) or points.ndim != 2 or points.shape[1] != 2 or not 1 <= len(points) <= 1000:
            raise ValueError('HOMOGRAPHY_INPUT_INVALID: matriz3x3 y1–1000puntosXY')
        if not np.isfinite(h).all() or not np.isfinite(points).all() or np.max(np.abs(h)) == 0 or np.max(np.abs(points)) > 1e12:
            raise ValueError('HOMOGRAPHY_INPUT_INVALID: valores no finitos o magnitud inválida')
        h = h / np.max(np.abs(h))
        condition = float(np.linalg.cond(h))
        if not math.isfinite(condition) or condition > 1e10:
            raise ValueError('HOMOGRAPHY_SINGULAR: matriz singular o mal condicionada')
        inverse = np.linalg.inv(h)
        def project(matrix, coordinates):
            denominators = (np.column_stack((coordinates, np.ones(len(coordinates)))) @ matrix.T)[:, 2]
            if np.any(np.abs(denominators) <= 1e-12):
                raise ValueError('HOMOGRAPHY_HORIZON: punto sobre el horizonte proyectivo')
            result = apply_homography(matrix, coordinates)
            if not np.isfinite(result).all():
                raise ValueError('HOMOGRAPHY_OUTPUT_INVALID: resultado no finito')
            return result
        transformed = project(h, points)
        restored = project(inverse, transformed)
        error = float(np.max(np.abs(restored - points)))
        if error > 1e-6 * (1 + float(np.max(np.abs(points)))):
            raise ValueError('HOMOGRAPHY_UNSTABLE: retorno numérico no fiable')
        return {'points': transformed.tolist(), 'source_units': data['source_units'], 'target_units': data['target_units'],
                'condition_number': condition, 'roundtrip_max_error_in_source_units': error,
                'versions': {p: metadata.version(p) for p in ('soccervision', 'opencv-python', 'numpy')},
                'matrix_estimated_from_images': False, 'calibration_verified': False,
                'geometry_generated': False, 'figures_generated': False, 'weights_loaded': False,
                'model_inference_performed': False}
    if name != 'cq_warehouse':
        raise ValueError('LIBRARY_OPERATION_UNSUPPORTED')
    size, width, sides = data.get('size'), data.get('across_flats_mm'), data.get('sides')
    pattern = r'(?:#(?:0000|000|00|0|1|2|3|4|5|6|8|10|12)|[0-9]{1,2}(?:/[1-9][0-9]?)?)-[1-9][0-9]{0,2}'
    if not isinstance(size, str) or not re.fullmatch(pattern, size):
        raise ValueError('WAREHOUSE_SIZE_INVALID: usa tamaño imperial numerado o fracción y TPI explícito')
    if type(width) not in (int, float) or not math.isfinite(width) or not 0 < width <= 10000 or type(sides) is not int or not 3 <= sides <= 24:
        raise ValueError('WAREHOUSE_DIMENSIONS_INVALID: ancho positivo <=10000mm, polígono de3–24lados')
    from cq_warehouse.fastener import decode_imperial_size, polygon_diagonal
    diameter, pitch = decode_imperial_size(size)
    if diameter <= 0 or pitch <= 0:
        raise ValueError('WAREHOUSE_SIZE_INVALID: diámetro y paso deben ser positivos')
    return {'size_declared': size, 'major_diameter_mm': diameter, 'pitch_mm': pitch,
            'across_flats_mm': width, 'polygon_sides': sides, 'polygon_diagonal_mm': polygon_diagonal(width, sides),
            'versions': {p: metadata.version(p) for p in ('cq_warehouse', 'cadquery', 'cadquery-ocp')},
            'units': 'mm', 'geometry_generated': False, 'figures_generated': False,
            'manufacturing_fit_verified': False, 'weights_loaded': False, 'model_inference_performed': False}


if __name__ == '__main__':
    sys.addaudithook(offline)
    try:
        if len(sys.argv) == 3 and sys.argv[2] == '--operate':
            raw = sys.stdin.buffer.read(500001)
            if not raw or len(raw) > 500000:
                raise ValueError('LIBRARY_INPUT_INVALID: máximo 500000 bytes')
            report = operate(sys.argv[1], json.loads(raw))
        else:
            report = check(sys.argv[1])
        sys.stdout.buffer.write(json.dumps(report, allow_nan=False).encode('utf-8'))
    except Exception as exc:
        prefix = 'LIBRARY_OPERATION_FAILED: ' if '--operate' in sys.argv else 'LIBRARY_DIAGNOSTIC_FAILED: '
        sys.stdout.buffer.write(json.dumps({'error': prefix + str(exc)[:400]}).encode('utf-8'))
        sys.exit(1)
