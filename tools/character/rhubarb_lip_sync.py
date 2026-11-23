"""Local Rhubarb diagnostics and validated mouth cues for project audio."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from jsonschema import validate, ValidationError

from lib import external_applications as applications
from lib import production_studio as studio
from tools.analysis.audio_probe import AudioProbe
from tools.base_tool import BaseTool, ResourceProfile, ToolResult, ToolRuntime, ToolStability, ToolStatus, ToolTier


INSTALL = 'Configura rhubarb.exe en Aplicaciones de Studio y FFprobe en las herramientas de medios. Conserva res/sphinx junto al ejecutable.'


def find_rhubarb():
    configured = applications.configuration().get('rhubarb', {}).get('executable')
    if configured:
        path = Path(configured)
        allowed = applications.CATALOG['rhubarb']['executables']
        if path.is_absolute() and path.name.casefold() in {name.casefold() for name in allowed} and path.is_file():
            return path.resolve()
        return None
    found = shutil.which('rhubarb')
    return Path(found).resolve() if found else None


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def resource_files(executable):
    root = executable.parent / 'res' / 'sphinx'
    required = ('cmudict-en-us.dict', 'en-us-phone.lm.bin', 'en-us.lm.bin',
                'acoustic-model/mdef', 'acoustic-model/means', 'acoustic-model/variances')
    missing = [name for name in required if not (root / name).is_file()]
    if missing:
        raise ValueError('RHUBARB_RESOURCES_MISSING: ' + ', '.join(missing))
    return {path.relative_to(root).as_posix(): path for path in sorted(root.rglob('*')) if path.is_file()}


def diagnose():
    executable = find_rhubarb()
    if executable is None:
        raise ValueError('RHUBARB_NOT_CONFIGURED: ' + INSTALL)
    resources = resource_files(executable)
    try:
        process = subprocess.run([str(executable), '--version'], capture_output=True,
                                 text=True, encoding='utf-8', errors='replace', timeout=30, shell=False)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('RHUBARB_DOCTOR_TIMEOUT: --version excedió 30 segundos') from exc
    match = re.search(r'Rhubarb Lip Sync version\s+(\d+\.\d+\.\d+)', process.stdout + process.stderr)
    if process.returncode or not match:
        raise ValueError('RHUBARB_VERSION_FAILED: ' + (process.stderr or process.stdout)[-500:])
    return {
        'executable': str(executable), 'version': match[1], 'executable_sha256': sha256(executable),
        'resource_sha256': {name: sha256(path) for name, path in resources.items()},
        'ffprobe_available': AudioProbe().get_status() == ToolStatus.AVAILABLE,
        'audio_analyzed': False, 'animation_generated': False,
    }


def failure(message):
    return ToolResult(success=False, error=message, cost_usd=0)


class RhubarbDoctor(BaseTool):
    name = 'rhubarb_doctor'
    provider = 'rhubarb'
    tier = ToolTier.CORE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'character_animation'
    capabilities = ['rhubarb_diagnostics']
    install_instructions = INSTALL
    input_schema = {'type': 'object', 'additionalProperties': False, 'properties': {}}
    output_schema = {'type': 'object', 'required': ['version', 'executable_sha256', 'resource_sha256',
                                                 'ffprobe_available', 'audio_analyzed', 'animation_generated']}

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            return ToolResult(success=True, data=diagnose(), cost_usd=0)
        except ValidationError as exc:
            return failure('RHUBARB_INPUT_INVALID: ' + exc.message)
        except ValueError as exc:
            return failure(str(exc))
        except OSError as exc:
            return failure('RHUBARB_IO_ERROR: ' + str(exc))


def project_file(root, value):
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    path.relative_to(root)
    if not path.is_file():
        raise ValueError('Archivo de entrada ausente')
    return path


def snapshot(source, destination, root, maximum):
    digest = hashlib.sha256()
    count = 0
    with source.open('rb') as stream, destination.open('xb') as output:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            count += len(block)
            if count > maximum:
                raise ValueError('Archivo de entrada demasiado grande')
            output.write(block)
            digest.update(block)
    if not count:
        raise ValueError('Archivo de entrada vacío')
    return {'project_relative_path': source.relative_to(root).as_posix(),
            'sha256': digest.hexdigest(), 'bytes': count, 'snapshot_used': True}


def finite_number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def validate_native(data, audio_snapshot, duration):
    if not isinstance(data, dict) or not isinstance(data.get('metadata'), dict):
        raise ValueError('RHUBARB_OUTPUT_INVALID: falta metadata')
    metadata = data['metadata']
    native_duration = metadata.get('duration')
    if not finite_number(native_duration) or native_duration < 0 or abs(native_duration - duration) > 0.021:
        raise ValueError('RHUBARB_OUTPUT_INVALID: duración incompatible con FFprobe')
    try:
        same_audio = isinstance(metadata.get('soundFile'), str) and Path(metadata['soundFile']).resolve() == audio_snapshot
    except (ValueError, OSError):
        same_audio = False
    if not same_audio:
        raise ValueError('RHUBARB_OUTPUT_INVALID: la salida corresponde a otro audio')
    cues = data.get('mouthCues')
    if not isinstance(cues, list) or len(cues) > 100_000:
        raise ValueError('RHUBARB_OUTPUT_INVALID: mouthCues inválido o demasiado grande')
    previous = 0
    for cue in cues:
        if not isinstance(cue, dict) or set(cue) != {'start', 'end', 'value'}:
            raise ValueError('RHUBARB_OUTPUT_INVALID: estructura de clave inválida')
        start, end = cue['start'], cue['end']
        if (not finite_number(start) or not finite_number(end) or start < previous
                or end <= start or end > native_duration + 0.001
                or cue['value'] not in tuple('ABCDEFGHX')):
            raise ValueError('RHUBARB_OUTPUT_INVALID: tiempos o forma de boca inválidos')
        previous = end
    return cues


class RhubarbLipSync(BaseTool):
    name = 'rhubarb_lip_sync'
    provider = 'rhubarb'
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = 'character_animation'
    capabilities = ['mouth_cues', 'local_audio_alignment']
    resource_profile = ResourceProfile(cpu_cores=2, ram_mb=1024, disk_mb=1024, network_required=False)
    side_effects = ['writes a new project JSON report with mouth cues']
    install_instructions = INSTALL
    input_schema = {
        'type': 'object', 'additionalProperties': False,
        'required': ['project_id', 'audio_path', 'language', 'output_path'],
        'properties': {
            'project_id': {'type': 'string'}, 'audio_path': {'type': 'string'},
            'output_path': {'type': 'string'}, 'dialog_path': {'type': 'string'},
            'language': {'type': 'string', 'pattern': '^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$'},
            'recognizer': {'enum': ['pocketSphinx', 'phonetic']},
            'timeout_seconds': {'type': 'integer', 'minimum': 1, 'maximum': 3600},
        },
    }
    output_schema = {'type': 'object', 'required': ['output_path', 'report_sha256', 'cue_count',
                                                 'mouth_cues_preview', 'provenance', 'animation_generated']}

    def get_status(self):
        try:
            executable = find_rhubarb()
            if executable and resource_files(executable) and AudioProbe().get_status() == ToolStatus.AVAILABLE:
                return ToolStatus.AVAILABLE
        except (ValueError, OSError):
            pass
        return ToolStatus.UNAVAILABLE

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            root = studio.project_path(inputs['project_id']).resolve()
            audio = project_file(root, inputs['audio_path'])
            if audio.suffix.lower() not in ('.wav', '.ogg'):
                raise ValueError('Rhubarb admite archivos WAV y Ogg Vorbis')
            english = inputs['language'].split('-')[0].lower() in ('en', 'eng')
            recognizer = inputs.get('recognizer', 'pocketSphinx' if english else 'phonetic')
            if recognizer == 'pocketSphinx' and not english:
                raise ValueError('PocketSphinx admite diálogo inglés; usa phonetic para otros idiomas')
            dialog = project_file(root, inputs['dialog_path']) if inputs.get('dialog_path') else None
            output = Path(inputs['output_path'])
            if not output.is_absolute():
                output = root / output
            output = output.resolve()
            relative = output.relative_to(root)
            if not relative.parts or relative.parts[0] not in ('assets', 'artifacts', 'workspaces') or output.suffix.lower() != '.json':
                raise ValueError('Guarda el informe JSON en assets/, artifacts/ o workspaces/ del proyecto')
            if output.exists():
                return failure('RHUBARB_OUTPUT_EXISTS: elige una ruta nueva para conservar el informe previo')
            if output in (audio, dialog):
                raise ValueError('El informe debe tener una ruta distinta de las entradas')
            doctor = diagnose()
            if not doctor['ffprobe_available']:
                return failure('RHUBARB_FFPROBE_MISSING: configura FFprobe en Studio')
            executable = Path(doctor['executable'])
            output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.rhubarb-', dir=output.parent) as temporary:
                temporary = Path(temporary)
                copied_audio = temporary / ('source' + audio.suffix.lower())
                audio_source = snapshot(audio, copied_audio, root, 512 * 1024 * 1024)
                probe = AudioProbe().execute({'input_path': str(copied_audio)})
                if not probe.success or not probe.data.get('audio'):
                    return failure('RHUBARB_AUDIO_INVALID: ' + str(probe.error or 'falta una pista de audio'))
                duration = probe.data.get('duration_seconds')
                if not finite_number(duration) or duration <= 0:
                    return failure('RHUBARB_AUDIO_INVALID: duración ausente o inválida')
                formats = str(probe.data.get('format_name', '')).split(',')
                if audio.suffix.lower() == '.wav' and 'wav' not in formats:
                    return failure('RHUBARB_AUDIO_INVALID: el archivo no contiene audio WAVE')
                if audio.suffix.lower() == '.ogg' and ('ogg' not in formats or probe.data['audio'].get('codec') != 'vorbis'):
                    return failure('RHUBARB_AUDIO_INVALID: Ogg requiere codec Vorbis')
                dialog_source = None
                raw_output = temporary / 'native.json'
                command = [str(executable), '--exportFormat', 'json', '--recognizer', recognizer,
                           '--extendedShapes', 'GHX', '--machineReadable', '--threads', '2',
                           '--output', str(raw_output)]
                if dialog:
                    copied_dialog = temporary / 'dialog.txt'
                    dialog_source = snapshot(dialog, copied_dialog, root, 1_000_000)
                    copied_dialog.read_text(encoding='utf-8-sig')
                    command.extend(['--dialogFile', str(copied_dialog)])
                command.append(str(copied_audio))
                log_path = temporary / 'native.log'
                with log_path.open('wb') as log:
                    process = subprocess.run(command, cwd=executable.parent, stdout=subprocess.DEVNULL,
                                             stderr=log, timeout=inputs.get('timeout_seconds', 300), shell=False)
                if process.returncode:
                    with log_path.open('rb') as log:
                        log.seek(max(0, log_path.stat().st_size - 2000))
                        detail = log.read().decode('utf-8', errors='replace')
                    return failure('RHUBARB_PROCESS_FAILED: ' + detail)
                if not raw_output.is_file() or raw_output.stat().st_size > 20_000_000:
                    raise ValueError('RHUBARB_OUTPUT_INVALID: salida ausente o demasiado grande')
                try:
                    native = json.loads(raw_output.read_text(encoding='utf-8'))
                except (ValueError, UnicodeError) as exc:
                    raise ValueError('RHUBARB_OUTPUT_INVALID: JSON ilegible') from exc
                cues = validate_native(native, copied_audio, duration)
                if (sha256(executable) != doctor['executable_sha256'] or
                        {name: sha256(path) for name, path in resource_files(executable).items()} != doctor['resource_sha256']):
                    raise ValueError('RHUBARB_RUNTIME_CHANGED: ejecutable o recursos cambiaron durante el análisis')
                report = {
                    'version': '1.0', 'generator': 'rhubarb', 'generator_version': doctor['version'],
                    'metadata': {'soundFile': audio_source['project_relative_path'], 'duration': native['metadata']['duration']},
                    'mouthCues': cues, 'animation_generated': False,
                    'provenance': {
                        'project_id': inputs['project_id'], 'audio': audio_source, 'dialog': dialog_source,
                        'language': inputs['language'], 'recognizer': recognizer,
                        'executable_sha256': doctor['executable_sha256'], 'resource_sha256': doctor['resource_sha256'],
                        'native_json_sha256': sha256(raw_output), 'probed_duration_seconds': duration,
                        'created_at_utc': datetime.now(timezone.utc).isoformat(), 'network_required': False,
                    },
                }
                prepared = temporary / 'report.json'
                studio.save_json(prepared, report)
                try:
                    os.link(prepared, output)
                except FileExistsError:
                    return failure('RHUBARB_OUTPUT_EXISTS: otro proceso ya publicó ese informe')
                return ToolResult(success=True, artifacts=[str(output)], cost_usd=0, data={
                    'output_path': str(output), 'report_sha256': sha256(output),
                    'duration_seconds': native['metadata']['duration'], 'cue_count': len(cues),
                    'mouth_cues_preview': cues[:10], 'provenance': report['provenance'],
                    'animation_generated': False,
                })
        except subprocess.TimeoutExpired:
            return failure('RHUBARB_TIMEOUT: el proceso excedió el tiempo configurado')
        except (ValueError, ValidationError) as exc:
            message = str(exc)
            return failure(message if message.startswith('RHUBARB_') else 'RHUBARB_INPUT_INVALID: ' + message[:500])
        except OSError as exc:
            return failure('RHUBARB_IO_ERROR: ' + str(exc))
