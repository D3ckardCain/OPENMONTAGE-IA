"""Strict variant/resource checks and editable request plans; never load weights."""
import json
from copy import deepcopy
from pathlib import Path
from lib.hyperframes_staging import identity
from lib import studio_editor as editor
from lib.model_languages import binding, QWEN

ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = Path('C:/OPENMONTAJE-IA/DESCARGAS_MODELOS')
HASH_CACHE = ROOT / '.runtime/qwen-tts/verified-models.json'
PROFILES = {
    'voice-design': dict(folder='Qwen--Qwen3-TTS-12Hz-1.7B-VoiceDesign', model_type='voice_design',
                         function='voice_design', main_bytes=3833402552,
                         main_sha256='391e8db219f292c515297cdceeb43e4eae67cdde35fa57e79a6a8a532fca0522'),
    'qwen-tts-17b-base': dict(folder='Qwen--Qwen3-TTS-12Hz-1.7B-Base', model_type='base',
                            function='authorized_voice_clone', main_bytes=3857413744,
                            main_sha256='38fc7fc51c5e776e840414b6fd443962e9411b9654888fd7913e4da643cb857c'),
}
TOKEN_SHA = '836b7b357f5ea43e889936a3709af68dfe3751881acefe4ecf0dbd30ba571258'
TOKEN_BYTES = 682293092


def resources(family, folder):
    profile = PROFILES[family]; folder = Path(folder)
    problems = []; checked = []
    try:
        cache = json.loads(HASH_CACHE.read_text()) if HASH_CACHE.is_file() else {}
        if not isinstance(cache,dict):raise ValueError('cache must be object')
    except (OSError,ValueError):
        cache = {}; problems.append('Cache de verificacion ilegible; no acredita pesos')
    for relative, size, expected in [('model.safetensors', profile['main_bytes'], profile['main_sha256']),
                                    ('speech_tokenizer/model.safetensors', TOKEN_BYTES, TOKEN_SHA)]:
        path = folder / relative
        if not path.is_file():
            problems.append(relative + ': final ausente o es directorio; no promover .fdmdownload')
            checked.append(dict(path=relative, status='final_missing_or_directory')); continue
        observed = identity(path); row = cache.get(str(path.resolve()), {})
        if path.stat().st_size != size:
            status = 'size_differs'
        elif row.get('identity') != observed or not row.get('sha256'):
            status = 'checksum_not_verified_for_current_identity'
        elif row['sha256'] != expected:
            status = 'different_variant_or_content_not_corruption_claim'
        else:
            status = 'verified_cached'
        if status != 'verified_cached':problems.append(relative + ': ' + status)
        checked.append(dict(path=relative, status=status, expected_sha256=expected, bytes=observed[2]))
    config = folder / 'config.json'
    if config.is_file() and config.stat().st_size <= 100000:
        try:
            value = json.loads(config.read_text(encoding='utf-8'))
            if not isinstance(value,dict):raise ValueError('config must be object')
        except (OSError,ValueError):
            value = {}; problems.append('config.json ilegible o invalido')
        if value.get('tts_model_type') != profile['model_type'] or value.get('tts_model_size') != '1b7':
            problems.append('Config de variante incorrecta; se requiere ' + profile['model_type'] + '/1b7')
    else:problems.append('config.json de modelo ausente; configuration.json no lo sustituye')
    for relative in ['generation_config.json','preprocessor_config.json','tokenizer_config.json','vocab.json','merges.txt',
                     'speech_tokenizer/config.json','speech_tokenizer/configuration.json','speech_tokenizer/preprocessor_config.json']:
        if not (folder / relative).is_file():problems.append('Auxiliar ausente o directorio: ' + relative)
    return dict(profile=family, function=profile['function'], resources_verified=not problems,
                checked_weights=checked, problems=problems, weights_read=False, automatic_download=False)


def catalog():
    from lib.model_adapters import diagnostics
    rows = []
    for family, spec in PROFILES.items():
        diagnostic = diagnostics(family)
        rows.append(dict(id=family, title=spec['folder'], function=spec['function'],
            native_tool='model_' + family.replace('-', '_'), languages=list(QWEN),
            diagnostic=diagnostic, inference_verified=False,
            preview_available=False, preview_limit='Preescucha/cancelación real pendientes de recursos y runtime completos; no se habilita botón ficticio.',
            license='Apache-2.0 model card; rights to reference voice separate'))
    return dict(contract='qwen-local-profiles-v1', profiles=rows, model_loaded=False,
        note='RAM/VRAM deben evaluarse antes de cargar; tamaño en disco no acredita compatibilidad8GB.')


def save_plan(edl, data):
    family = data['profile']
    if family not in PROFILES:raise ValueError('Selecciona VoiceDesign1.7B o Base1.7B explícitos')
    language = binding('qwen-tts', data['language'])
    text = data['text']
    if not isinstance(text, str) or not text.strip() or len(text) > 1000:raise ValueError('Texto requerido1–1000caracteres')
    value = dict(profile=family, function=PROFILES[family]['function'], language=language, text=text,
                 synthesized=False, contract='qwen-request-plan-v1')
    if family == 'voice-design':
        instruction = data.get('instruction')
        if not isinstance(instruction, str) or not instruction.strip() or len(instruction) > 2000:
            raise ValueError('VoiceDesign requiere descripción de voz1–2000caracteres')
        value['instruction'] = instruction
    else:
        if data.get('reference_authorized') is not True:raise ValueError('Confirma autorización de la voz de referencia')
        source = edl['sources'][data['reference_source_id']]
        if source['kind'] != 'audio' or Path(source['path']).suffix.lower() not in ('.wav','.flac'):
            raise ValueError('Referencia: audio WAV/FLAC registrado; no se extrae otra voz automáticamente')
        ref = data.get('reference_text')
        if not isinstance(ref, str) or not ref.strip() or len(ref) > 2000:raise ValueError('Se requiere transcripción de referencia')
        value.update(reference_source_id=data['reference_source_id'], reference_sha256=source['sha256'],
                     reference_authorized=True, reference_text=ref)
    edl['qwen_tts_plan'] = deepcopy(value)


def cpu_memory_preflight(folder, available_bytes=None):
    """Conservative FP32 weight floor, not a VRAM fit promise; no tensor reads."""
    if available_bytes is None:
        import ctypes
        import os
        if os.name == 'nt':
            class Memory(ctypes.Structure):
                _fields_ = [('length',ctypes.c_ulong),('load',ctypes.c_ulong)] + [(key,ctypes.c_ulonglong) for key in ['total','available','total_page','available_page','total_virtual','available_virtual','extended']]
            value=Memory();value.length=ctypes.sizeof(value)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):raise OSError('No se pudo consultar RAM libre')
            available_bytes=value.available
        else:
            available_bytes=os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')
    # Current worker explicitly selects FP32 on CPU. BF16 safetensors can double.
    paths=[Path(folder)/name for name in ['model.safetensors','speech_tokenizer/model.safetensors']]
    floor=sum(p.stat().st_size for p in paths if p.is_file())*2
    required=floor+1024**3
    return dict(device='cpu',available_bytes=available_bytes,estimated_fp32_weight_floor_bytes=floor,
                required_with_minimum_headroom_bytes=required,allowed=available_bytes>=required,
                estimate_not_peak_measurement=True,model_loaded=False)
