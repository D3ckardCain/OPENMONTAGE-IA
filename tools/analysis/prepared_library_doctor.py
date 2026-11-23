"""Studio/agent entry point for allowlisted isolated library diagnostics."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from jsonschema import validate, ValidationError
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = ROOT / '.runtime'
WORKER = ROOT / 'lib/prepared_library_worker.py'
NAMES = ['socceraction', 'cq_warehouse', 'soccervision']


class PreparedLibraryDoctor(BaseTool):
    name = 'prepared_library_doctor'
    capability = 'local_library_diagnostics'
    provider = 'isolated_python'
    tier = ToolTier.CORE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    install_instructions = 'Consulta docs/BIBLIOTECAS_AISLADAS_ES.md y prepara el entorno individual bajo .runtime/.'
    input_schema = {'type': 'object', 'required': ['library'], 'additionalProperties': False,
                    'properties': {'library': {'enum': NAMES}}}

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            name = inputs['library']
            python = RUNTIME_ROOT / name / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            if not python.is_file():
                raise ValueError('LIBRARY_RUNTIME_MISSING: falta el entorno aislado de ' + name)
            worker_hash = hashlib.sha256(WORKER.read_bytes()).hexdigest()
            with tempfile.TemporaryDirectory(prefix='openmontage-library-') as cache:
                env = dict(os.environ, MPLBACKEND='Agg', MPLCONFIGDIR=cache)
                try:
                    process = subprocess.run([str(python), '-I', '-B', str(WORKER), name], env=env,
                                             capture_output=True, timeout=60, shell=False)
                except subprocess.TimeoutExpired as exc:
                    raise ValueError('LIBRARY_TIMEOUT: diagnóstico excedió 60 segundos') from exc
            if len(process.stdout) > 100_000:
                raise ValueError('LIBRARY_OUTPUT_INVALID: respuesta demasiado grande')
            try:
                result = json.loads(process.stdout.decode('utf-8'))
            except (ValueError, UnicodeError) as exc:
                raise ValueError('LIBRARY_OUTPUT_INVALID: respuesta ilegible') from exc
            if not isinstance(result, dict) or process.returncode or result.get('error'):
                raise ValueError(str(result.get('error', 'LIBRARY_PROCESS_FAILED')) if isinstance(result, dict) else 'LIBRARY_OUTPUT_INVALID')
            if worker_hash != hashlib.sha256(WORKER.read_bytes()).hexdigest():
                raise ValueError('LIBRARY_RUNTIME_CHANGED: worker cambió durante el diagnóstico')
            result['provenance'] = {'worker_sha256': worker_hash, 'source_receipt_available': False}
            receipt = RUNTIME_ROOT / name / 'source-provenance.json'
            if receipt.is_file():
                raw = receipt.read_bytes()
                value = json.loads(raw)
                result['provenance'].update({'source_receipt_available': True,
                    'source_receipt_sha256': hashlib.sha256(raw).hexdigest(),
                    'prepared_commit': value.get('commit'), 'prepared_archive_sha256': value.get('archive_sha256'),
                    'verified_archive_files': value.get('verified_files'), 'installed_files_rehashed': False})
            return ToolResult(success=True, data=result, cost_usd=0)
        except (ValueError, OSError, ValidationError) as exc:
            message = exc.message if isinstance(exc, ValidationError) else str(exc)
            return ToolResult(success=False, error=message if message.startswith('LIBRARY_') else 'LIBRARY_INPUT_INVALID: ' + message[:500], cost_usd=0)
