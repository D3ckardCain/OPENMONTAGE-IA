"""Local manual editing contract shared by Studio and the agent. No inference.

The authoritative revision, EDL, media provenance and undo journal are committed
atomically in one project artifact. Originals are never edited in place.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import uuid

from lib import production_studio as studio, production_agent as agent
from lib.media_executables import require_media
from lib.scene_subtitles import parse_srt

ARTIFACT = 'artifacts/manual_edit.json'
EXTENSIONS = {'.mp4', '.mov', '.mkv', '.webm', '.m4v', '.wav', '.mp3', '.flac', '.ogg', '.m4a'}
INPUT_OPTIONS = ['-protocol_whitelist', 'file,pipe', '-format_whitelist', 'mov,matroska,webm,wav,mp3,flac,ogg']
PRESETS = {'16:9': (1920, 1080), '9:16': (1080, 1920), '1:1': (1080, 1080), '4:5': (1080, 1350)}
EXPORTING: set[str] = set()
RENDER_CONTRACT = 'timeline-v3'


class Conflict(ValueError):
    """A stale revision or an active resource owner prevents a mutation."""


def number(value, low=0, high=86400):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('Número o intervalo fuera de límites')
    return float(value)


def media_path(project, relative):
    if not isinstance(relative, str) or '\\' in relative or not (
        relative.startswith('assets/') or relative.startswith('originales/')
    ):
        raise ValueError('El medio debe estar dentro de originales/ o assets/ del proyecto')
    path = project / relative
    path.resolve().relative_to(project.resolve())
    if any(p in ('.', '..') for p in Path(relative).parts) or path.is_symlink() or not path.is_file():
        raise ValueError('Medio ausente o ruta no permitida')
    return path


def identity(path):
    stat = path.stat()
    return {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}


def digest(path):
    h = hashlib.sha256()
    remaining = path.stat().st_size
    with path.open('rb') as stream:
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise Conflict('El archivo se truncó durante su verificación')
            remaining -= len(chunk)
            h.update(chunk)
        if stream.read(1):
            raise Conflict('El archivo creció durante su verificación')
    return h.hexdigest()


def probe(path):
    try:
        result = subprocess.run([require_media('ffprobe'), '-v', 'error', *INPUT_OPTIONS, '-show_streams', '-show_format',
                                 '-of', 'json', str(path)], capture_output=True, timeout=30, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('FFprobe excedió el límite de diagnóstico de 30 segundos') from exc
    if result.returncode:
        raise ValueError('FFprobe no pudo leer el medio: ' + result.stderr.decode('utf-8', 'replace')[-500:])
    data = json.loads(result.stdout)
    streams = data.get('streams', [])
    video = next((s for s in streams if s.get('codec_type') == 'video' and not s.get('disposition', {}).get('attached_pic')), None)
    audio = any(s.get('codec_type') == 'audio' for s in streams)
    if not video and not audio:
        raise ValueError('El archivo no contiene vídeo ni audio reproducible')
    duration = number(float(data.get('format', {}).get('duration', 0)), .001, 7200)
    return {'duration': duration, 'kind': 'video' if video else 'audio', 'audio': audio,
            'width': video.get('width') if video else None, 'height': video.get('height') if video else None}


def _empty():
    return {'version': '1.0', 'render_runtime': 'ffmpeg', 'cuts': [], 'audio_tracks': [], 'cues': [],
            'sources': {}, 'output': {'ratio': '16:9', 'fps': 24, 'fit': 'pad'},
            'subtitle_style': {'size': 32, 'position': 'bottom', 'mode': 'soft', 'language': 'und'}}


def create(title):
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
        raise ValueError('Indica un título de 1 a 120 caracteres')
    from lib.project_workspace import create_project_folder, describe as describe_workspace, initialize_layout
    pid, project = create_project_folder(studio.PROJECTS_DIR, title)
    initialize_layout(project)
    studio.save_json(project / 'production_request.json', {'title': title.strip(), 'manual_edit': True})
    studio.save_json(project / 'project.json', {'project_id': pid, 'title': title.strip(), 'type': 'manual_edit'})
    studio.save_json(project / ARTIFACT, {'revision': 0, 'edit_decisions': _empty(), 'undo': [], 'redo': [], 'events': []})
    return {'project_id': pid, 'project_path': str(project), 'workspace': describe_workspace(project), **state(pid)}


def state(pid):
    project = studio.project_path(pid)
    with studio.LOCK:
        value = studio.read_json(project / ARTIFACT)
    if value is None:
        raise ValueError('Este proyecto usa el flujo de producción. Crea un proyecto de edición manual; no se sustituye su montaje.')
    value['edit_sha256'] = edit_digest(value['edit_decisions'])
    value['render_sha256'] = render_digest(value['edit_decisions'])
    from lib.project_workspace import describe as describe_workspace
    value['workspace'] = describe_workspace(project)
    return value


def edit_digest(edl):
    """Content identity independent of save/log-only command revisions."""
    payload = json.dumps(edl, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def render_digest(edl, contract=RENDER_CONTRACT):
    """AV identity excludes markers, edit locks and unused-source provenance."""
    content = {key: deepcopy(edl[key]) for key in ('cuts', 'audio_tracks', 'cues', 'output', 'subtitle_style')}
    content['render_contract'] = contract
    if edl['cues'] and edl['subtitle_style'].get('mode')=='burn' and edl.get('subtitle_karaoke',{}).get('enabled'):
        from lib.studio_subtitle_karaoke import normalize as normalize_karaoke,CONTRACT as karaoke_contract
        settings=normalize_karaoke(edl['subtitle_karaoke']);content['subtitle_karaoke']=settings;content['subtitle_karaoke_contract']=karaoke_contract
        dataset=next((v for v in edl.get('candidate_sets',[]) if v.get('id')==settings['set_id']),{})
        content['subtitle_karaoke_basis_hash']=edit_digest({k:dataset.get(k) for k in ('words','coverage','source_sha256','transcript_sha256')})
    if edl['cues'] and edl['subtitle_style'].get('mode')=='burn' and 'subtitle_layout' in edl:
        content['subtitle_safe_area']=deepcopy(edl['subtitle_layout']['safe_area'])
        content['subtitle_layout_contract']='subtitle-reading-layout-v1'
    if any(c.get('transition', {}).get('type') == 'crossfade' for c in edl['cuts']):
        from lib.studio_crossfade import RENDER_CONTRACT as crossfade_contract
        content['crossfade_render_contract'] = crossfade_contract
    output = edl['output']
    width, height = (output['width'], output['height']) if output.get('ratio') == 'custom' else PRESETS[output['ratio']]
    content['output'] = {'width': width, 'height': height, 'fps': output['fps'], 'fit': output['fit']}
    if output.get('background'):content['output']['background']=output['background']
    if any(t.get('component_layout') for t in edl.get('titles',[])):
        from lib.studio_components import RENDER_CONTRACT as component_contract
        content['component_render_contract']=component_contract
    if edl.get('titles'):
        content['titles'] = deepcopy(edl['titles'])
    if edl.get('layers'):
        content['layers'] = deepcopy(edl['layers'])
    mix = edl.get('audio_mix', {})
    if mix.get('normalize') or mix.get('gain', 1) != 1:
        content['audio_mix'] = {'gain': mix.get('gain', 1), 'normalize': mix.get('normalize', False)}
        if mix.get('normalize'):
            content['audio_mix']['target_lufs'] = mix['target_lufs']
    for clip in content['cuts'] + content['audio_tracks']:
        from lib.studio_color import effective as effective_color,CONTRACT as color_contract
        from lib.studio_color_curves import effective as effective_color_curves
        curves=effective_color_curves(clip.get('color_curves'),clip.get('color',{}).get('bypass',False))
        if curves:
            clip['color_curves']=curves;content['color_curves_contract']='rgb-pchip-v1'
        else:clip.pop('color_curves',None)
        color=effective_color(clip.get('color'))
        if color:
            clip['color']=color;content['color_contract']=color_contract
        else:clip.pop('color',None)
        from lib.studio_audio_processing import effective, RENDER_CONTRACT as audio_contract
        processing=effective(clip.get('audio_processing'))
        if processing:
            clip['audio_processing']=processing
            content['audio_processing_contract']=audio_contract
        else:clip.pop('audio_processing',None)
        clip.pop('locked', None)
        if not clip.get('solo'):
            clip.pop('solo', None)
    from lib.studio_track_mixer import effective as effective_mixer
    mixer = effective_mixer(edl)
    if mixer:
        content['track_mixer'] = mixer
        content['track_mixer_contract'] = 'logical-lanes-v1'
    from lib.studio_ducking import effective as effective_ducking, RENDER_CONTRACT as ducking_contract
    from lib.studio_volume_automation import effective as effective_volume, RENDER_CONTRACT as volume_contract
    volumes={lane:effective_volume(edl,lane) for lane in ('video','audio')}
    if any(volumes.values()):
        content['volume_automation']={lane:p for lane,p in volumes.items() if p}
        content['volume_automation_contract']=volume_contract
    ducking = effective_ducking(edl)
    if ducking:
        content['audio_ducking'] = ducking
        content['ducking_contract'] = ducking_contract
        content['ducking_music_ids'] = [c['id'] for c in edl['audio_tracks'] if c.get('ducking_music')]
    for clip in content['audio_tracks']:
        clip.pop('ducking_music', None)
    used = {c['source_id'] for c in content['cuts'] + content['audio_tracks'] + content.get('layers', []) if c.get('kind') != 'gap'}
    content['sources'] = {key: {name: edl['sources'][key].get(name) for name in ('path', 'sha256', 'kind', 'audio')}
                          for key in sorted(used)}
    return edit_digest(content)


@contextmanager
def guard(pid, origin='user'):
    # Same lock ordering as the production entry points; no check/use race.
    with agent.ACTIVE_LOCK, studio.LOCK:
        if (pid in agent.ACTIVE and origin != 'agent') or pid in EXPORTING:
            raise Conflict('Proyecto ocupado: detén el agente y espera su finalización, o espera la exportación')
        yield


def _commit(pid, value, edl, origin, operation):
    value['undo'] = (value['undo'] + [value['edit_decisions']])[-50:]
    value['redo'] = []
    value['edit_decisions'] = edl
    return _write(pid, value, origin, operation)


def _write(pid, value, origin, operation):
    value['edit_sha256'] = edit_digest(value['edit_decisions'])
    value['render_sha256'] = render_digest(value['edit_decisions'])
    value['revision'] += 1
    value['events'] = (value['events'] + [{'revision': value['revision'], 'origin': origin,
                      'operation': operation, 'at': studio.now()}])[-500:]
    studio.save_json(studio.project_path(pid) / ARTIFACT, value)
    return value


def _revision(value, expected):
    if type(expected) is not int or expected != value['revision']:
        raise Conflict('El proyecto cambió. Reabre la revisión actual antes de editar')


def register(pid, relative, expected, origin='user', original_name=None):
    with guard(pid, origin):
        value = state(pid)
        _revision(value, expected)
        path = media_path(studio.project_path(pid), relative)
        if path.suffix.lower() not in EXTENSIONS:
            raise ValueError('Formato multimedia no admitido')
        edl = deepcopy(value['edit_decisions'])
        if len(edl['sources']) >= 200:
            raise ValueError('Límite local: 200 fuentes por proyecto')
        before = identity(path)
        if before['bytes'] > 2_000_000_000:
            raise ValueError('Límite de importación: 2 GB por archivo')
        info = probe(path)
        sha = digest(path)
        if before != identity(path):
            raise Conflict('El archivo cambió durante la importación')
        key = uuid.uuid4().hex
        edl['sources'][key] = {**info, **before, 'path': relative, 'sha256': sha,
                              'original_name': original_name or path.name, 'imported_at': studio.now(), 'origin': origin}
        return _commit(pid, value, edl, origin, 'import')


def _item(items, key):
    return next(item for item in items if item['id'] == key)


def import_subtitles(pid, blob, filename, expected):
    """Preserve the actual imported bytes, separately from subsequent cue edits."""
    if not isinstance(filename, str) or len(filename) > 240 or Path(filename).suffix.lower() != '.srt':
        raise ValueError('Indica un archivo SRT')
    if not isinstance(blob, bytes) or not 0 < len(blob) <= 500_000:
        raise ValueError('SRT vacío o superior a 500 KB')
    with guard(pid):
        value = state(pid)
        _revision(value, expected)
        edl = deepcopy(value['edit_decisions'])
        edl['cues'] = parse_srt(blob.decode('utf-8-sig'), duration(edl))
        relative = 'subtitulos/' + uuid.uuid4().hex + '.srt'
        target = studio.project_path(pid) / relative
        target.parent.resolve().relative_to(studio.project_path(pid).resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(blob)
        edl.setdefault('subtitle_sources', []).append({'path': relative, 'original_name': filename,
            'sha256': hashlib.sha256(blob).hexdigest(), 'bytes': len(blob), 'origin': 'user',
            'exact_original_bytes': True, 'imported_at': studio.now()})
        return _commit(pid, value, edl, 'user', 'import_subtitles')


def duration(edl):
    fps = edl['output']['fps']
    return sum(frames(c, fps) / fps for c in edl['cuts'])


def frames(clip, fps):
    if clip.get('time_warp',{}).get('role')=='primary':
        from lib.studio_smooth_clock import validate
        m=validate(clip['time_warp']['map'])
        if fps!=m['fps']:raise ValueError('No cambies FPS con rampa continua activa')
        return m['output_frames']
    # Match browser Math.round for nonnegative times, including half frames.
    return math.floor((clip['out_seconds'] - clip['in_seconds']) / clip['speed'] * fps + .5)


def command(pid, data, origin='user'):
    if origin not in ('user', 'agent'):
        raise ValueError('Procedencia desconocida')
    with guard(pid, origin):
        value = state(pid)
        _revision(value, data.get('revision'))
        op = data.get('operation')
        if op in ('undo', 'redo'):
            source, target = ('undo', 'redo') if op == 'undo' else ('redo', 'undo')
            if not value[source]:
                raise ValueError('No hay operaciones para ' + op)
            value[target].append(value['edit_decisions'])
            value['edit_decisions'] = value[source].pop()
            return _write(pid, value, origin, op)
        if op == 'save':
            return _write(pid, value, origin, op)
        edl = deepcopy(value['edit_decisions'])
        _apply_edit(edl, data)
        _validate_edit(edl)
        return _commit(pid, value, edl, origin, op)


def _apply_edit(edl, data):
    from lib.studio_timeline_ops import apply_timeline, assert_editable
    op = data.get('operation')
    if op == 'batch':
        operations = data.get('operations')
        if not isinstance(operations, list) or not 1 <= len(operations) <= 200:
            raise ValueError('Batch requiere de 1 a 200 operaciones')
        for item in operations:
            if not isinstance(item, dict) or item.get('operation') in ('batch', 'save', 'undo', 'redo'):
                raise ValueError('No se admiten comandos de historial ni batch anidados')
            _apply_edit(edl, item)
        return
    try:
        assert_editable(edl, data)
        if apply_timeline(edl, data):
            return
    except (KeyError, StopIteration, TypeError) as exc:
        raise ValueError('Clip o parámetro de operación no encontrado') from exc
    try:
        if op == 'add':
            source = edl['sources'][data['source_id']]
            item = {'id': uuid.uuid4().hex, 'source': source['path'], 'source_id': data['source_id'],
                    'in_seconds': 0, 'out_seconds': source['duration'], 'speed': 1, 'muted': False,
                    'gain': 1, 'fade_in': 0, 'fade_out': 0, 'start_seconds': 0}
            edl['cuts' if source['kind'] == 'video' else 'audio_tracks'].append(item)
        elif op in ('trim', 'split', 'remove', 'move', 'clip'):
            if data.get('track', 'video') not in ('video', 'audio'):
                raise ValueError('Pista desconocida')
            items = edl['audio_tracks'] if data.get('track') == 'audio' else edl['cuts']
            item = _item(items, data['id'])
            index = items.index(item)
            if op == 'remove':
                items.remove(item)
            elif op == 'move':
                position = data['index']
                if type(position) is not int or not 0 <= position < len(items):
                    raise ValueError('Posición fuera de la pista')
                items.insert(position, items.pop(index))
            elif op == 'split':
                at = number(data['at'], item['in_seconds'] + .001, item['out_seconds'] - .001)
                second = {**item, 'id': uuid.uuid4().hex, 'in_seconds': at}
                second.pop('transition', None)
                if data.get('track') == 'audio':
                    second['start_seconds'] += (at - item['in_seconds']) / item['speed']
                item['out_seconds'] = at
                items.insert(index + 1, second)
            elif op == 'trim':
                start = number(data['in_seconds'])
                end = number(data['out_seconds'], start + .001, item['gap_duration'] if item.get('kind') == 'gap' else edl['sources'][item['source_id']]['duration'])
                item.update(in_seconds=start, out_seconds=end)
            else:
                for key in ('speed', 'gain', 'fade_in', 'fade_out', 'start_seconds'):
                    if key in data:
                        item[key] = number(data[key], .25 if key == 'speed' else 0,
                                           4 if key in ('speed', 'gain') else 7200)
                for flag in ('muted', 'solo', 'locked'):
                    if flag in data:
                        if type(data[flag]) is not bool:
                            raise ValueError('Mute/solo/bloqueo requieren booleanos')
                        item[flag] = data[flag]
        elif op == 'output':
            if data['ratio'] not in PRESETS:
                raise ValueError('Formato no admitido')
            fps = data.get('fps', 24)
            if fps not in (24, 25, 30, 60):
                raise ValueError('FPS no admitidos')
            background=edl['output'].get('background')
            edl['output'] = {'ratio': data['ratio'], 'fps': fps, 'fit': 'pad'}
            if background:edl['output']['background']=background
        elif op == 'subtitle_from_words':
            from lib.studio_word_subtitles import apply
            apply(edl, data)
        elif op == 'silence_apply':
            from lib.studio_silence_proposal import apply
            apply(edl, data)
        elif op == 'qwen_tts_plan':
            from lib.qwen_tts_local import save_plan
            save_plan(edl, data)
        elif op == 'reference_plan':
            from lib.studio_reference_plan import apply
            apply(edl, data)
        elif op in ('component_add','component_remove'):
            from lib.studio_components import apply
            apply(edl,data)
        elif op == 'subtitles':
            edl['cues'] = parse_srt(data['srt'], duration(edl)) if data['srt'].strip() else []
        elif op in ('cue_update', 'cue_split', 'cue_merge', 'cue_offset'):
            cues = edl['cues']
            if op == 'cue_offset':
                offset = number(data['seconds'], -7200, 7200)
                for cue in cues:
                    cue['start_seconds'] += offset
                    cue['end_seconds'] += offset
            else:
                index = data['index']
                if type(index) is not int or not 0 <= index < len(cues):
                    raise ValueError('Subtítulo no encontrado')
                cue = cues[index]
                if op == 'cue_update':
                    cue.update(start_seconds=number(data['start_seconds']), end_seconds=number(data['end_seconds']), text=data['text'])
                elif op == 'cue_split':
                    at = number(data['at'], cue['start_seconds'] + .001, cue['end_seconds'] - .001)
                    text_index = data['text_index']
                    if type(text_index) is not int or not 0 < text_index < len(cue['text']):
                        raise ValueError('Indica dónde dividir el texto')
                    second = {**cue, 'start_seconds': at, 'text': cue['text'][text_index:].strip()}
                    cue.update(end_seconds=at, text=cue['text'][:text_index].strip())
                    cues.insert(index + 1, second)
                else:
                    if index + 1 >= len(cues):
                        raise ValueError('No hay subtítulo siguiente')
                    following = cues.pop(index + 1)
                    cue.update(end_seconds=following['end_seconds'], text=cue['text'] + '\n' + following['text'])
            edl['cues'] = parse_srt(srt(edl), duration(edl)) if cues else []
        elif op == 'subtitle_style':
            from lib.studio_subtitle_language import validate_language
            size = number(data['size'], 12, 96)
            if data['position'] not in ('bottom', 'center', 'top') or data.get('mode', 'soft') not in ('soft', 'burn'):
                raise ValueError('Posición no admitida')
            old = edl['subtitle_style']
            language = validate_language(data['language']) if 'language' in data else old.get('language')
            edl['subtitle_style'] = {'size': size, 'position': data['position'], 'mode': data.get('mode', 'soft')}
            if language is not None:
                edl['subtitle_style']['language'] = language
        else:
            raise ValueError('Operación aún no disponible')
    except (KeyError, StopIteration) as exc:
        raise ValueError('Fuente, clip o parámetro no encontrado') from exc


def _validate_edit(edl):
    from lib.studio_smooth_speed import validate as validate_smooth
    validate_smooth(edl)
    from lib.studio_color_curves import normalize as normalize_color_curves
    for clip in edl['cuts']:
        if 'color_curves' in clip:normalize_color_curves(clip['color_curves'])
    from lib.studio_color import normalize as normalize_color
    for clip in edl['cuts']:
        if 'color' in clip:normalize_color(clip['color'])
    if 'subtitle_karaoke' in edl:
        from lib.studio_subtitle_karaoke import normalize as normalize_karaoke
        normalize_karaoke(edl['subtitle_karaoke'])
    if 'subtitle_layout' in edl:
        from lib.studio_subtitle_layout import normalize as normalize_subtitle_layout
        normalize_subtitle_layout(edl['subtitle_layout'])
    from lib.studio_volume_automation import validate as validate_volume
    validate_volume(edl)
    from lib.studio_ducking import validate as validate_ducking
    validate_ducking(edl)
    from lib.studio_track_mixer import normalize as normalize_mixer
    normalize_mixer(edl.get('track_mixer', {}))
    from lib.studio_audio_processing import validate as validate_processing
    validate_processing(edl)
    from lib.studio_audio_balance import validate as validate_balance
    validate_balance(edl)
    from lib.studio_editor_layers import validate_composition
    validate_composition(edl)
    if len(edl['cuts']) + len(edl['audio_tracks']) > 200 or duration(edl) > 7200:
        raise ValueError('Límite local: 200 clips y dos horas')
    if any((c['out_seconds'] - c['in_seconds']) / c['speed'] < 1 / edl['output']['fps'] - 1e-9 for c in edl['cuts']):
        raise ValueError('Cada clip de vídeo debe durar al menos un fotograma de salida')
    if edl['cues'] and max(c['end_seconds'] for c in edl['cues']) > duration(edl) + .02:
        raise ValueError('El montaje dejaría subtítulos fuera de duración; ajusta sus tiempos primero')
    if any(t['end_seconds'] > duration(edl)+.001 for t in edl.get('titles', [])):
        raise ValueError('Ajusta los títulos que quedarían fuera de duración')


def srt(edl):
    def stamp(seconds):
        ms = round(seconds * 1000)
        return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'
    return '\n\n'.join(f"{i}\n{stamp(c['start_seconds'])} --> {stamp(c['end_seconds'])}\n{c['text']}"
                       for i, c in enumerate(edl['cues'], 1)) + ('\n' if edl['cues'] else '')


def source(pid, source_id):
    edl = state(pid)['edit_decisions']
    try:
        info = edl['sources'][source_id]
    except KeyError as exc:
        raise ValueError('Fuente no encontrada') from exc
    path = media_path(studio.project_path(pid), info['path'])
    if identity(path) != {key: info[key] for key in ('bytes', 'mtime_ns')}:
        raise Conflict('El medio cambió desde su importación; vuelve a importarlo')
    return path

