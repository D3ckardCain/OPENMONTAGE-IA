"""Isolated PyQGIS numeric worker. No layers, projects, plugins or rendering."""
import json
import math
import os
from pathlib import Path
import sys


def validate_payload(data):
    if not isinstance(data, dict):
        raise ValueError('QGIS_INPUT_INVALID: se requiere un objeto')
    if set(data) != {'source_crs', 'target_crs', 'points'}:
        raise ValueError('QGIS_INPUT_INVALID: campos desconocidos')
    source, target, points = data['source_crs'], data['target_crs'], data['points']
    if {source, target} != {'EPSG:4326', 'EPSG:3857'}:
        raise ValueError('QGIS_CRS_INVALID: solo WGS84 y Web Mercator en sentidos opuestos')
    if not isinstance(points, list) or not 1 <= len(points) <= 1000:
        raise ValueError('QGIS_INPUT_INVALID: indica entre 1 y 1000 puntos XY')
    bounds = (180, 85.0511287798066) if source == 'EPSG:4326' else (20037508.342789244,) * 2
    for point in points:
        if not isinstance(point, list) or len(point) != 2 or any(
                type(v) not in (int, float) or not math.isfinite(v) or abs(v) > bounds[i]
                for i, v in enumerate(point)):
            raise ValueError('QGIS_POINT_INVALID: XY finito dentro del dominio Web Mercator')
    return source, target, points


def main():
    raw = sys.stdin.buffer.read(65537)
    if not raw or len(raw) > 65536:
        raise ValueError('QGIS_INPUT_INVALID: entrada vacía o demasiado grande')
    source, target, points = validate_payload(json.loads(raw))
    from qgis.core import (QgsApplication, Qgis, QgsCoordinateReferenceSystem,
                           QgsCoordinateTransform, QgsCoordinateTransformContext, QgsPointXY,
                           QgsNetworkAccessManager)
    from qgis.PyQt.QtNetwork import QNetworkAccessManager
    profile = os.environ['OPENMONTAGE_QGIS_PROFILE']
    QgsApplication.setPrefixPath(os.environ['QGIS_PREFIX_PATH'], True)
    app = QgsApplication([], False, profile)
    QgsApplication.setAuthDatabaseDirPath(profile)
    QgsNetworkAccessManager.instance().setNetworkAccessible(QNetworkAccessManager.NotAccessible)
    app.initQgis()
    try:
        src, dst = QgsCoordinateReferenceSystem(source), QgsCoordinateReferenceSystem(target)
        context = QgsCoordinateTransformContext()
        forward = QgsCoordinateTransform(src, dst, context)
        reverse = QgsCoordinateTransform(dst, src, context)
        for transform in (forward, reverse):
            transform.setBallparkTransformsAreAppropriate(False)
            transform.setAllowFallbackTransforms(False)
            if not transform.isValid():
                raise ValueError('QGIS_TRANSFORM_INVALID: CRS u operación no disponible')
        transformed, errors = [], []
        for x, y in points:
            result = forward.transform(QgsPointXY(x, y))
            back = reverse.transform(result)
            values = [result.x(), result.y(), back.x(), back.y()]
            if not all(math.isfinite(v) for v in values):
                raise ValueError('QGIS_TRANSFORM_INVALID: resultado no finito')
            if forward.fallbackOperationOccurred() or reverse.fallbackOperationOccurred():
                raise ValueError('QGIS_TRANSFORM_INVALID: se rechazó una operación aproximada')
            transformed.append(values[:2])
            errors.append(max(abs(back.x() - x), abs(back.y() - y)))
        return {'qgis_version': Qgis.QGIS_VERSION, 'source_crs': source, 'target_crs': target,
                'axis_order': 'xy_longitude_latitude_for_epsg4326', 'points': transformed,
                'target_units': 'metres' if target == 'EPSG:3857' else 'degrees',
                'roundtrip_max_error': max(errors),
                'roundtrip_error_units': 'degrees' if source == 'EPSG:4326' else 'metres',
                'approximate_fallback_allowed': False, 'proj_network_enabled': False,
                'layers_loaded': False, 'maps_generated': False, 'model_inference': False}
    finally:
        app.exitQgis()


if __name__ == '__main__':
    try:
        print(json.dumps(main(), allow_nan=False))
    except Exception as exc:
        print(json.dumps({'error': str(exc)[:500]}))
        sys.exit(1)
