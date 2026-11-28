"""Local numeric coordinates through the existing isolated Kloppy/MPLSoccer runtime."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from jsonschema import validate, ValidationError
from lib import production_studio as studio
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ToolStatus

RUNTIME = Path(__file__).resolve().parents[2] / '.runtime/sports-analysis/venv'
WORKER = Path(__file__).resolve().parents[2] / 'lib/sports_coordinates_worker.py'
INSTALL = 'Prepara .runtime/sports-analysis/venv con Kloppy 3.19.1 y MPLSoccer 1.8.1. Consulta docs/COORDENADAS_DEPORTIVAS_ES.md.'


def python_path():
    return RUNTIME / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def worker(raw=None):
    python = python_path()
    if not python.is_file():
        raise ValueError('SPORTS_RUNTIME_MISSING: ' + INSTALL)
    with tempfile.TemporaryDirectory(prefix='openmontage-sports-') as cache:
        env = dict(os.environ, MPLBACKEND='Agg', MPLCONFIGDIR=cache)
        try:
            process = subprocess.run([str(python), '-I', '-B', str(WORKER)] + ([] if raw is not None else ['doctor']),
                                     input=raw, capture_output=True, env=env, timeout=45, shell=False)
        except subprocess.TimeoutExpired as exc:
            raise ValueError('SPORTS_TIMEOUT: el entorno excedió 45 segundos') from exc
        if len(process.stdout) > 2_000_000:
            raise ValueError('SPORTS_OUTPUT_INVALID: respuesta demasiado grande')
        try:
            result = json.loads(process.stdout.decode('utf-8'))
        except (ValueError, UnicodeError) as exc:
            raise ValueError('SPORTS_OUTPUT_INVALID: respuesta ilegible del entorno aislado') from exc
        if not isinstance(result, dict):
            raise ValueError('SPORTS_OUTPUT_INVALID: respuesta no estructurada')
        if process.returncode or result.get('error'):
            raise ValueError(str(result.get('error', 'SPORTS_PROCESS_FAILED: ' + process.stderr.decode('utf-8', errors='replace')[-300:]))[:500])
        return result


def failure(exc):
    message = exc.message if isinstance(exc, ValidationError) else str(exc)
    return ToolResult(success=False, error=message if message.startswith('SPORTS_') else 'SPORTS_INPUT_INVALID: ' + message[:500], cost_usd=0)


class SportsCoordinatesDoctor(BaseTool):
    name = 'sports_coordinates_doctor'
    capability = 'sports_coordinate_analysis'
    provider = 'kloppy_mplsoccer'
    tier = ToolTier.CORE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    install_instructions = INSTALL
    input_schema = {'type': 'object', 'properties': {}, 'additionalProperties': False}

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            result = worker()
            result['worker_sha256'] = hashlib.sha256(WORKER.read_bytes()).hexdigest()
            return ToolResult(success=True, data=result, cost_usd=0)
        except (ValueError, OSError, ValidationError) as exc:
            return failure(exc)


class SportsCoordinates(BaseTool):
    name = 'sports_coordinates'
    capability = 'sports_coordinate_analysis'
    provider = 'kloppy_mplsoccer'
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    install_instructions = INSTALL
    input_schema = {'type': 'object', 'additionalProperties': False,
                    'required': ['project_id', 'input_path', 'output_path'],
                    'properties': {name: {'type': 'string', 'minLength': 1} for name in
                                   ('project_id', 'input_path', 'output_path')}}

    def get_status(self):
        return ToolStatus.AVAILABLE if python_path().is_file() and WORKER.is_file() else ToolStatus.UNAVAILABLE

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            root = studio.project_path(inputs['project_id']).resolve()
            source = Path(inputs['input_path'])
            source = (source if source.is_absolute() else root / source).resolve()
            relative = source.relative_to(root)
            if source.suffix.lower() != '.json' or not source.is_file():
                raise ValueError('SPORTS_INPUT_INVALID: se requiere un JSON local dentro del proyecto')
            with source.open('rb') as stream:
                raw = stream.read(500001)
            if not raw or len(raw) > 500000:
                raise ValueError('SPORTS_INPUT_INVALID: JSON vacío o mayor de 500000 bytes')
            output = Path(inputs['output_path'])
            output = (output if output.is_absolute() else root / output).resolve()
            destination = output.relative_to(root)
            if destination.parts[0] not in ('assets', 'artifacts', 'workspaces') or output.suffix.lower() != '.json':
                raise ValueError('SPORTS_OUTPUT_INVALID: guarda el JSON en assets/, artifacts/ o workspaces/')
            if output.exists():
                raise ValueError('SPORTS_OUTPUT_EXISTS: conserva el informe previo usando una ruta nueva')
            worker_hash = hashlib.sha256(WORKER.read_bytes()).hexdigest()
            result = worker(raw)
            if worker_hash != hashlib.sha256(WORKER.read_bytes()).hexdigest():
                raise ValueError('SPORTS_RUNTIME_CHANGED: el adaptador cambió durante la operación')
            provenance = {'project_id': inputs['project_id'], 'project_relative_path': relative.as_posix(),
                          'input_sha256': hashlib.sha256(raw).hexdigest(), 'input_bytes': len(raw),
                          'worker_sha256': worker_hash, 'versions': result['versions'],
                          'created_at_utc': datetime.now(timezone.utc).isoformat(), 'network_accessed': False,
                          'metadata_origin': 'declared_in_input_not_independently_verified'}
            report = {'schema_version': '1.0', **result, 'provenance': provenance}
            output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.sports-', dir=output.parent) as temporary:
                prepared = Path(temporary) / 'report.json'
                studio.save_json(prepared, report)
                try:
                    os.link(prepared, output)
                except FileExistsError as exc:
                    raise ValueError('SPORTS_OUTPUT_EXISTS: otro proceso publicó ese informe') from exc
            return ToolResult(success=True, cost_usd=0, artifacts=[str(output)], data={
                'output_path': str(output), 'report_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                'point_count': len(result['points']), 'points_preview': result['points'][:10],
                'roundtrip_max_error_m': result['roundtrip_max_error_m'], 'provenance': provenance,
                'figures_generated': False})
        except (ValueError, OSError, ValidationError) as exc:
            return failure(exc)
