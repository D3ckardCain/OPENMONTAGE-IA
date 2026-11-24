"""Bounded numeric GIS operations in the registered OSGeo4W Python runtime."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from jsonschema import validate, ValidationError
from lib import production_studio as studio
from lib.external_applications import configuration
from lib.qgis_runtime import environment
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ToolStatus

WORKER = Path(__file__).resolve().parents[2] / 'lib/qgis_coordinates_worker.py'


def runtime():
    executable = configuration().get('qgis', {}).get('executable', '')
    if not executable:
        raise ValueError('QGIS_RUNTIME_MISSING: registra el QGIS ya preparado en Studio')
    env = environment(executable)
    python = Path(env['PYTHONEXECUTABLE'])
    if not python.is_file():
        raise ValueError('QGIS_RUNTIME_MISSING: falta Python de OSGeo4W')
    return python, env


class QgisCoordinates(BaseTool):
    name = 'qgis_coordinates'
    capability = 'geographic_coordinate_analysis'
    provider = 'pyqgis'
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    install_instructions = 'Reutiliza el QGIS OSGeo4W registrado. Consulta docs/COORDENADAS_QGIS_ES.md.'
    input_schema = {'type': 'object', 'additionalProperties': False,
                    'required': ['project_id', 'source_crs', 'target_crs', 'points'], 'properties': {
                        'project_id': {'type': 'string', 'minLength': 1},
                        'source_crs': {'enum': ['EPSG:4326', 'EPSG:3857']},
                        'target_crs': {'enum': ['EPSG:4326', 'EPSG:3857']},
                        'points': {'type': 'array', 'minItems': 1, 'maxItems': 1000,
                                   'items': {'type': 'array', 'minItems': 2, 'maxItems': 2,
                                             'items': {'type': 'number'}}}}}

    def get_status(self):
        try:
            runtime()
            return ToolStatus.AVAILABLE if WORKER.is_file() else ToolStatus.UNAVAILABLE
        except (ValueError, OSError):
            return ToolStatus.UNAVAILABLE

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            studio.project_path(inputs['project_id'])
            payload = {key: inputs[key] for key in ('source_crs', 'target_crs', 'points')}
            from lib.qgis_coordinates_worker import validate_payload
            validate_payload(payload)
            raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            if len(raw) > 65536:
                raise ValueError('QGIS_INPUT_INVALID: entrada demasiado grande')
            python, env = runtime()
            worker_hash = hashlib.sha256(WORKER.read_bytes()).hexdigest()
            with tempfile.TemporaryDirectory(prefix='openmontage-qgis-') as temporary:
                env.update({'QT_QPA_PLATFORM': 'offscreen', 'OPENMONTAGE_QGIS_PROFILE': temporary,
                            'QGIS_CUSTOM_CONFIG_PATH': temporary, 'QGIS_AUTH_DB_DIR_PATH': temporary,
                            'XDG_CACHE_HOME': temporary, 'XDG_CONFIG_HOME': temporary})
                env.pop('PYQGIS_STARTUP', None)
                process = subprocess.run([str(python), '-s', '-B', str(WORKER)], input=raw,
                                         env=env, cwd=temporary, capture_output=True, timeout=60,
                                         shell=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if len(process.stdout) > 250000:
                raise ValueError('QGIS_OUTPUT_INVALID: respuesta demasiado grande')
            try:
                result = json.loads(process.stdout.decode('utf-8'))
            except (ValueError, UnicodeError) as exc:
                raise ValueError('QGIS_OUTPUT_INVALID: no se recibió JSON; código ' + str(process.returncode) + '; ' + process.stderr.decode('utf-8', errors='replace')[-300:]) from exc
            if not isinstance(result, dict) or process.returncode or result.get('error'):
                raise ValueError('QGIS_PROCESS_FAILED: ' + str(result.get('error', 'error de proceso') if isinstance(result, dict) else 'respuesta inválida'))
            if worker_hash != hashlib.sha256(WORKER.read_bytes()).hexdigest():
                raise ValueError('QGIS_RUNTIME_CHANGED: worker cambió durante la operación')
            result['provenance'] = {'project_id': inputs['project_id'], 'input_sha256': hashlib.sha256(raw).hexdigest(),
                                    'worker_sha256': worker_hash, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                                    'metadata_origin': 'user_declared_crs_and_points',
                                    'operation': 'qgis_coordinate_transform', 'network_accessed': False}
            return ToolResult(success=True, data=result, cost_usd=0)
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error='QGIS_TIMEOUT: operación excedió 60 segundos', cost_usd=0)
        except (ValueError, OSError, ValidationError) as exc:
            return ToolResult(success=False, error='QGIS_INPUT_OR_RUNTIME_ERROR: ' + str(exc)[:500], cost_usd=0)
