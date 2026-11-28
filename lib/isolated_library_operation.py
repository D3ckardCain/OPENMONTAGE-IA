"""Shared functional transport for prepared, allowlisted isolated libraries."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from jsonschema import validate, ValidationError
from lib import production_studio as studio
from tools.base_tool import BaseTool, ToolResult, ToolStatus, ToolTier, ToolRuntime, ToolStability

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / '.runtime'
WORKER = ROOT / 'lib/prepared_library_worker.py'


class IsolatedLibraryOperation(BaseTool):
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    install_instructions = 'Reutiliza el entorno aislado preparado; docs/OPERACIONES_BIBLIOTECAS_ES.md.'

    def python(self):
        return RUNTIME_ROOT / self.library / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

    def get_status(self):
        return ToolStatus.AVAILABLE if self.python().is_file() and WORKER.is_file() else ToolStatus.UNAVAILABLE

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            studio.project_path(inputs['project_id'])
            data = {k: v for k, v in inputs.items() if k != 'project_id'}
            raw = json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            if len(raw) > 500000:
                raise ValueError('LIBRARY_INPUT_INVALID: máximo 500000 bytes')
            if not self.python().is_file():
                raise ValueError('LIBRARY_RUNTIME_MISSING: falta entorno aislado ' + self.library)
            worker_hash = hashlib.sha256(WORKER.read_bytes()).hexdigest()
            with tempfile.TemporaryDirectory(prefix='openmontage-library-operation-') as cache:
                env = dict(os.environ, MPLBACKEND='Agg', MPLCONFIGDIR=cache, HF_HOME=cache,
                           HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TORCH_HOME=cache,
                           TF_CPP_MIN_LOG_LEVEL='3', CUDA_VISIBLE_DEVICES='')
                process = subprocess.run([str(self.python()), '-I', '-B', str(WORKER), self.library, '--operate'],
                                         input=raw, env=env, cwd=cache, capture_output=True, timeout=60, shell=False,
                                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if len(process.stdout) > 250000:
                raise ValueError('LIBRARY_OUTPUT_INVALID: respuesta demasiado grande')
            try:
                result = json.loads(process.stdout.decode('utf-8'))
            except (ValueError, UnicodeError) as exc:
                raise ValueError('LIBRARY_OUTPUT_INVALID: no se recibió JSON') from exc
            if not isinstance(result, dict) or process.returncode or result.get('error'):
                raise ValueError(str(result.get('error', 'LIBRARY_PROCESS_FAILED')) if isinstance(result, dict) else 'LIBRARY_OUTPUT_INVALID')
            if worker_hash != hashlib.sha256(WORKER.read_bytes()).hexdigest():
                raise ValueError('LIBRARY_RUNTIME_CHANGED: worker cambió durante la operación')
            provenance = {'project_id': inputs['project_id'], 'input_sha256': hashlib.sha256(raw).hexdigest(),
                          'worker_sha256': worker_hash, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                          'metadata_origin': 'user_declared_not_independently_verified', 'network_accessed': False,
                          'installed_files_rehashed': False}
            receipt = RUNTIME_ROOT / self.library / 'source-provenance.json'
            if receipt.is_file():
                receipt_raw = receipt.read_bytes()
                recorded = json.loads(receipt_raw)
                provenance.update(source_receipt_sha256=hashlib.sha256(receipt_raw).hexdigest(),
                                  prepared_commit=recorded.get('commit'), prepared_archive_sha256=recorded.get('archive_sha256'))
            result['provenance'] = provenance
            return ToolResult(success=result.get('valid', True), data=result, cost_usd=0,
                              error=None if result.get('valid', True) else 'LIBRARY_VALIDATION_FAILED: consulta issues del informe')
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error='LIBRARY_TIMEOUT: operación excedió 60 segundos', cost_usd=0)
        except (OSError, ValueError, ValidationError) as exc:
            return ToolResult(success=False, error='LIBRARY_INPUT_OR_RUNTIME_ERROR: ' + str(exc)[:500], cost_usd=0)
