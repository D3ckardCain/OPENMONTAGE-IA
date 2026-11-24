"""Native FreeCAD unit conversions through an isolated bundled Python process."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from jsonschema import validate, ValidationError
from lib import production_studio as studio
from lib.freecad_runtime import python_environment
from lib.freecad_units_worker import UNITS, validate_payload
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ToolStatus

WORKER = Path(__file__).resolve().parents[2] / 'lib/freecad_units_worker.py'
UNIT_NAMES = [unit for units in UNITS.values() for unit in units]


class FreecadUnits(BaseTool):
    name = 'freecad_units'
    capability = 'cad_parameter_analysis'
    provider = 'freecad'
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    install_instructions = 'Reutiliza FreeCAD y su Python incluidos; docs/UNIDADES_FREECAD_ES.md.'
    input_schema = {'type': 'object', 'additionalProperties': False,
                    'required': ['project_id', 'source_unit', 'target_unit', 'values'], 'properties': {
                        'project_id': {'type': 'string', 'minLength': 1},
                        'source_unit': {'enum': UNIT_NAMES}, 'target_unit': {'enum': UNIT_NAMES},
                        'values': {'type': 'array', 'minItems': 1, 'maxItems': 1000, 'items': {'type': 'number'}}}}

    def get_status(self):
        try:
            python_environment()
            return ToolStatus.AVAILABLE if WORKER.is_file() else ToolStatus.UNAVAILABLE
        except (ValueError, OSError):
            return ToolStatus.UNAVAILABLE

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            studio.project_path(inputs['project_id'])
            payload = {key: inputs[key] for key in ('source_unit', 'target_unit', 'values')}
            validate_payload(payload)
            raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            if len(raw) > 65536:
                raise ValueError('FREECAD_INPUT_INVALID: entrada demasiado grande')
            python, env = python_environment()
            worker_hash = hashlib.sha256(WORKER.read_bytes()).hexdigest()
            with tempfile.TemporaryDirectory(prefix='openmontage-freecad-') as temporary:
                env['FREECAD_USER_HOME'] = temporary
                for variable, folder in (('FREECAD_USER_DATA', 'data'), ('FREECAD_USER_TEMP', 'temp')):
                    path = Path(temporary) / folder
                    path.mkdir()
                    env[variable] = str(path)
                process = subprocess.run([str(python), '-I', '-B', str(WORKER)], input=raw,
                                         env=env, cwd=temporary, capture_output=True, timeout=45,
                                         shell=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if len(process.stdout) > 150000:
                raise ValueError('FREECAD_OUTPUT_INVALID: respuesta demasiado grande')
            try:
                result = json.loads(process.stdout.decode('utf-8'))
            except (ValueError, UnicodeError) as exc:
                raise ValueError('FREECAD_OUTPUT_INVALID: no se recibió JSON; código ' + str(process.returncode) + '; ' + process.stderr.decode('utf-8', errors='replace')[-300:]) from exc
            if not isinstance(result, dict) or process.returncode or result.get('error'):
                raise ValueError('FREECAD_PROCESS_FAILED: ' + str(result.get('error', 'proceso falló') if isinstance(result, dict) else 'respuesta inválida'))
            if worker_hash != hashlib.sha256(WORKER.read_bytes()).hexdigest():
                raise ValueError('FREECAD_RUNTIME_CHANGED: worker cambió durante la operación')
            result['provenance'] = {'project_id': inputs['project_id'], 'input_sha256': hashlib.sha256(raw).hexdigest(),
                                    'worker_sha256': worker_hash, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                                    'metadata_origin': 'user_declared_values_and_units', 'network_accessed': False}
            return ToolResult(success=True, data=result, cost_usd=0)
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error='FREECAD_TIMEOUT: operación excedió 45 segundos', cost_usd=0)
        except (ValueError, OSError, ValidationError) as exc:
            return ToolResult(success=False, error='FREECAD_INPUT_OR_RUNTIME_ERROR: ' + str(exc)[:500], cost_usd=0)
