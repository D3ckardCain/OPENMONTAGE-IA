"""Allowlisted dependency diagnostics and synthetic checks, never media production."""
import importlib.metadata as metadata
import json
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
    else:
        raise ValueError('LIBRARY_UNKNOWN: runtime no admitido')
    return {'runtime': name, 'versions': {name: metadata.version(name) for name in packages},
            'synthetic_checks': checks, 'network_accessed': False, 'real_input_read': False,
            'geometry_generated': False, 'figures_generated': False, 'model_inference_performed': False}


if __name__ == '__main__':
    sys.addaudithook(offline)
    try:
        report = check(sys.argv[1])
        sys.stdout.buffer.write(json.dumps(report, allow_nan=False).encode('utf-8'))
    except Exception as exc:
        sys.stdout.buffer.write(json.dumps({'error': 'LIBRARY_DIAGNOSTIC_FAILED: ' + str(exc)[:400]}).encode('utf-8'))
        sys.exit(1)
