"""Explicit private HyperFrames selection, shared by Studio and native tools."""
import json
import subprocess
from pathlib import Path

from lib import production_studio as studio
from lib.hyperframes_offline_profile import environment

FIELDS = ('node', 'browser', 'package_dir', 'scratch', 'gsap_package_dir')
_CHILD = None  # Only set by the one-tool transport process, never by Studio routes.


def use_child_profile(profile, network_log):
    global _CHILD
    _CHILD = (validate(profile), Path(network_log))


def read():
    path = studio.CONFIG_DIR / 'hyperframes_profile.json'
    if path.is_symlink() or path.is_file() and path.stat().st_size > 16000:
        raise ValueError('Perfil HyperFrames superior a16KB')
    value = studio.read_json(path, {'contract': 'hf-profile-v1', 'revision': 0, 'profile': None})
    if not isinstance(value, dict) or value.get('contract') != 'hf-profile-v1' or type(value.get('revision')) is not int:
        raise ValueError('Registro de selección HyperFrames inválido; se conserva')
    return value


def validate(profile):
    if not isinstance(profile, dict) or set(profile) != set(FIELDS):
        raise ValueError('Indica node, browser, package_dir, scratch y gsap_package_dir explícitos')
    for key, value in profile.items():
        if not isinstance(value, str) or not value or len(value) > 4000 or not Path(value).is_absolute():
            raise ValueError('Ruta absoluta requerida: ' + key)
    value = {key: str(Path(profile[key]).resolve()) for key in FIELDS}
    if not Path(value['scratch']).is_dir():
        raise ValueError('Scratch debe ser una carpeta existente; no se prepara implícitamente')
    environment(value, Path(value['scratch']) / 'network.jsonl')
    for key, name, version in [('package_dir', 'hyperframes', '0.9.96'), ('gsap_package_dir', 'gsap', '3.14.2')]:
        path = Path(value[key]) / 'package.json'
        if not path.is_file() or path.stat().st_size > 100000:
            raise ValueError('Manifest local ausente o fuera de presupuesto: ' + key)
        meta = json.loads(path.read_text(encoding='utf-8'))
        if meta.get('name') != name or meta.get('version') != version:
            raise ValueError('Paquete/versión no revisados: ' + key)
    if not (Path(value['gsap_package_dir']) / 'dist/gsap.min.js').is_file():
        raise ValueError('GSAP preparado incompleto')
    return value


def save(profile, revision):
    from lib.studio_editor import Conflict
    profile = validate(profile)
    with studio.LOCK:
        current = read()
        if current['profile'] == profile:
            return {**current, 'unchanged': True}
        if type(revision) is not int or revision != current['revision']:
            raise Conflict('Cambió el perfil; consulta el estado antes de reenviar')
        value = {'contract': 'hf-profile-v1', 'revision': revision + 1,
                 'profile': profile, 'updated_at': studio.now()}
        studio.save_json(studio.CONFIG_DIR / 'hyperframes_profile.json', value)
        return value


def selected_environment():
    value = read()
    if value['profile'] is None and _CHILD is None:
        return None
    profile = validate(value['profile']) if _CHILD is None else _CHILD[0]
    env = environment(profile, Path(profile['scratch']) / 'network.jsonl' if _CHILD is None else _CHILD[1])
    env['OPENMONTAGE_HF_NODE']=profile['node']
    env.pop('OPENMONTAGE_HF_PROFILE_REVISION',None)
    if profile == value['profile']:
        env['OPENMONTAGE_HF_PROFILE_REVISION']=str(value['revision'])
    return env


def probe_matches(key, revision):
    value = read()
    probe = value.get('execution_probe', {})
    if not isinstance(probe,dict):return False
    # JSON normalizes tuples; compare declared bounded file identities, no hashes.
    return (str(value['revision']) == revision and probe.get('identity_key') == json.loads(json.dumps(key))
            and probe.get('status') == 'ok')


def execute_probe():
    from lib import hyperframes_runtime as runtime
    from lib.studio_editor import Conflict
    before = read()
    if before['profile'] is None:
        raise ValueError('Selecciona un perfil antes de probar su ejecución')
    current = runtime.check()
    if not current['local_requirements_met']:
        raise ValueError('; '.join(current['reasons']))
    try:
        result = subprocess.run(runtime.command(['--version']), env=runtime.environment(),
                                capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('CLI no confirmó ejecución dentro del límite; consulta el perfil antes de repetir') from exc
    if result.returncode or result.stdout.strip() != runtime.REVIEWED_VERSION:
        raise ValueError('CLI seleccionado no confirmó la versión revisada: ' + result.stderr[-500:])
    with studio.LOCK:
        value = read()
        if value['revision'] != before['revision'] or runtime.check()['identity_key'] != current['identity_key']:
            raise Conflict('Perfil o recursos cambiaron durante la comprobación')
        value['execution_probe'] = {'status': 'ok', 'operation': '--version',
            'version': result.stdout.strip(), 'identity_key': current['identity_key'],
            'at': studio.now(), 'doctor_repeated': False, 'render_executed': False}
        studio.save_json(studio.CONFIG_DIR / 'hyperframes_profile.json', value)
    return {'selection': value, 'availability': runtime.check()}
