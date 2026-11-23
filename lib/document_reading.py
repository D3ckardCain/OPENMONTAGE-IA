"""Project document parsing through the separately provisioned Python runtime."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit


MAX_BYTES = 500_000
RUNTIME = Path(__file__).resolve().parents[1] / '.runtime' / 'document-reading' / 'venv'
WORKER = Path(__file__).with_name('document_reading_worker.py')


def read_document(path, project_root, document_format, source_url='', offset=0, limit=None):
    root = Path(project_root).resolve()
    source = Path(path)
    if not source.is_absolute():
        source = root / source
    source = source.resolve()
    relative = source.relative_to(root)
    if document_format not in ('feed', 'html'):
        raise ValueError('Formato documental inválido')
    if limit is None:
        limit = 20 if document_format == 'feed' else 20_000
    maximum = 100 if document_format == 'feed' else 50_000
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= maximum:
        raise ValueError('Paginación documental inválida')
    if not isinstance(source_url, str) or len(source_url) > 2000:
        raise ValueError('URL de procedencia inválida')
    if source_url:
        url = urlsplit(source_url)
        if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password:
            raise ValueError('La procedencia debe ser una URL HTTP(S) sin credenciales')
        _ = url.port
    if not source.is_file() or source.stat().st_size > MAX_BYTES:
        raise ValueError('Archivo ausente o demasiado grande')
    with source.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('Documento vacío o demasiado grande')
    python = RUNTIME / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        raise ValueError('Falta el entorno aislado .runtime/document-reading/venv')
    try:
        process = subprocess.run(
            [str(python), '-I', '-B', str(WORKER), document_format, source_url,
             str(offset), str(limit)],
            input=raw, capture_output=True, timeout=45, shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError('El lector documental excedió 45 segundos') from exc
    except OSError as exc:
        raise ValueError('No se pudo iniciar el entorno documental aislado') from exc
    if len(process.stdout) > 2_000_000:
        raise ValueError('La respuesta documental excede el límite')
    try:
        result = json.loads(process.stdout.decode('utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise ValueError('El entorno documental devolvió una respuesta inválida') from exc
    if process.returncode or not isinstance(result, dict) or result.get('error'):
        error = result.get('error', 'Error del lector documental') if isinstance(result, dict) else 'Respuesta inválida'
        raise ValueError(str(error)[:300])
    result.update({
        'path': str(source),
        'content_role': 'untrusted_source_document',
        'provenance': {
            'project_relative_path': relative.as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw),
            'parsed_at_utc': datetime.now(timezone.utc).isoformat(),
            'supplied_source_url': source_url or None,
            'source_url_verified': False,
            'network_accessed': False,
        },
    })
    if len(json.dumps(result, ensure_ascii=False)) > 95_000:
        raise ValueError('La página documental excede el límite de transporte del agente')
    return result
