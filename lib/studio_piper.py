"""Explicit local Piper resources shared by Studio and the agent; no downloads."""
import json
import subprocess
import uuid
from pathlib import Path
from lib import production_studio as studio


VCTK_RETRAINED_REVISION = '5ec43b186ef915a195d3ddbcfd9916e76c503c3f'
VCTK_RETRAINED_SHA256 = 'fc3d92d266b1a6c03af2a38215e0eee430ca7fb360f641d7c3dcb17c7670c0f3'


def vctk_blocked(reference, config, card):
    """Enable only the pinned retrain; presence and speaker count are insufficient."""
    return not (
        reference.get('revision') == VCTK_RETRAINED_REVISION
        and any(f.get('sha256') == VCTK_RETRAINED_SHA256 for f in reference.get('files', [])
                if f.get('name') == 'en_GB-vctk-medium.onnx')
        and config.get('piper_version') == '1.5.0'
        and config.get('num_speakers') == 109
        and len(config.get('speaker_id_map', {})) == 109
        and set(config.get('speaker_id_map', {}).values()) == set(range(109))
        and 'hifi_tts_92' in card and 'Cori Samuel' in card and 'lessac' not in card.lower()
    )


def configuration():
    return studio.read_json(studio.CONFIG_DIR / 'piper.json', {})


def catalog():
    cfg = configuration()
    result = []
    for item in json.loads(Path(__file__).with_name('piper_voices.json').read_text(encoding='utf-8')):
        voice = dict(item)
        folder = Path(cfg.get('voices_root', '')) / voice['id']
        config = studio.read_json(folder / (voice['id'] + '.onnx.json'), {})
        voice['speakers'] = config.get('speaker_id_map') or {'default': 0}
        voice['sample_rate'] = config.get('audio', {}).get('sample_rate')
        voice['available'] = bool(cfg.get('python') and Path(cfg['python']).is_file() and
                                  all((folder / f['name']).is_file() for f in voice['files']))
        voice['blocked'] = False
        if voice['id'] == 'en_GB-vctk-medium':
            card_path = folder / 'MODEL_CARD'
            card = card_path.read_text(encoding='utf-8') if card_path.is_file() else ''
            voice['blocked'] = vctk_blocked(voice, config, card)
        voice['tested'] = False  # Presence never proves synthesis or perceptual quality.
        result.append(voice)
    return result


def synthesize(text, voice_id, speaker_id, output):
    voice = next((v for v in catalog() if v['id'] == voice_id), None)
    if not voice or not voice['available']:
        raise ValueError('Piper: paquete o entorno aislado no disponible')
    if voice['blocked']:
        raise ValueError('VCTK antiguo: base Lessac; uso bloqueado hasta resolver licencia/pesos')
    if type(speaker_id) is not int or speaker_id not in voice['speakers'].values():
        raise ValueError('Hablante no pertenece a esta voz')
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:
        raise ValueError('Texto requerido: 1 a 1000 caracteres')
    cfg = configuration()
    folder = Path(cfg['voices_root']) / voice_id
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError('El destino ya existe; no se sobrescribe')
    payload = dict(text=text, model=str(folder / (voice_id + '.onnx')),
                   speaker_id=speaker_id, output=str(output), references=voice)
    proc = subprocess.run([cfg['python'], '-B', '-m', 'lib.piper_worker'],
                          input=json.dumps(payload), text=True, encoding='utf-8',
                          capture_output=True, timeout=90, cwd=studio.REPO_ROOT)
    if proc.returncode:
        raise ValueError('Piper: ' + proc.stderr[-2000:])
    return json.loads(proc.stdout)


def preview(pid, data):
    project = studio.project_path(pid)
    relative = 'assets/audio/piper-' + uuid.uuid4().hex + '.wav'
    result = synthesize(data.get('text'), data.get('voice'), data.get('speaker_id', 0), project / relative)
    result['relative_path'] = relative
    return result
