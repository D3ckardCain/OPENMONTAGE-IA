"""Bounded FFmpeg rendering of the shared manual EDL (no AI or downloads)."""
from copy import deepcopy
import json
import subprocess
import threading
import uuid

from lib import production_studio as studio, studio_editor as editor
from lib.media_executables import require_media
from tools.video.video_trimmer import VideoTrimmer
from lib.scene_burned_subtitles import _ass
from lib.studio_editor_effects import transform_filter
from tools.audio.audio_mixer import AudioMixer


def plan(pid, edl, preview=False):
    """One graph for both preview and export, preserving audio and letterboxing."""
    if not edl['cuts']:
        raise ValueError('Añade al menos un clip de vídeo')
    width, height = (edl['output']['width'], edl['output']['height']) if edl['output'].get('ratio') == 'custom' else editor.PRESETS[edl['output']['ratio']]
    if preview:
        if edl['output']['ratio'] != 'custom':
            width, height = {'16:9': (960, 540), '9:16': (540, 960), '1:1': (540, 540), '4:5': (432, 540)}[edl['output']['ratio']]
        else:
            scale = min(1, 960/max(width, height))
            width, height = max(2, round(width*scale/2)*2), max(2, round(height*scale/2)*2)
    fps = edl['output']['fps']
    args = []
    filters = []
    labels = []
    tracks = edl['cuts'] + edl['audio_tracks']
    solo = any(c.get('solo') for c in tracks)
    for i, clip in enumerate(tracks):
        gap = clip.get('kind') == 'gap'
        info = {'audio': False} if gap else edl['sources'][clip['source_id']]
        if gap:
            args += ['-f', 'lavfi', '-i', f"color=c=black:s={width}x{height}:r={fps}:d={clip['gap_duration']}"]
        else:
            path = editor.source(pid, clip['source_id'])
            args += [*editor.INPUT_OPTIONS, '-i', str(path)]
        start, end, speed = clip['in_seconds'], clip['out_seconds'], clip['speed']
        seconds = (end - start) / speed
        is_video = i < len(edl['cuts'])
        if is_video:
            seconds = editor.frames(clip, fps) / fps
            filters.append(f'[{i}:v:0]trim=start={start}:end={end},setpts=(PTS-STARTPTS)/{speed},'
                           + transform_filter(width, height, clip.get('transform')) + f',setsar=1,fps={fps},'
                           f'tpad=stop_mode=clone:stop_duration={seconds},trim=duration={seconds},format=yuv420p[v{i}]')
        gain = 0 if clip['muted'] or (solo and not clip.get('solo')) else clip['gain']
        if info['audio']:
            af = (f'[{i}:a:0]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,'
                  + VideoTrimmer._build_atempo_chain(speed) + f',aresample=48000,'
                  f'aformat=sample_fmts=fltp:channel_layouts=stereo,volume={gain}')
            if clip['fade_in']:
                af += f",afade=t=in:st=0:d={min(seconds, clip['fade_in'])}"
            if clip['fade_out']:
                fade = min(seconds, clip['fade_out'])
                af += f',afade=t=out:st={seconds-fade}:d={fade}'
            af += f',apad,atrim=duration={seconds}'
        else:
            af = f'anullsrc=r=48000:cl=stereo,atrim=duration={seconds}'
        if not is_video:
            af += f",adelay={round(clip['start_seconds'] * 1000)}:all=1"
        filters.append(af + f'[a{i}]')
        if is_video:
            labels.append(f'[v{i}][a{i}]')
    filters.append(''.join(labels) + f"concat=n={len(edl['cuts'])}:v=1:a=1[montage][baseaudio]")
    audio = '[baseaudio]' + ''.join(f'[a{i}]' for i in range(len(edl['cuts']), len(tracks)))
    mix = edl.get('audio_mix', {})
    filters.append(audio + f'amix=inputs={len(edl["audio_tracks"])+1}:duration=first:normalize=0,volume={mix.get("gain", 1)}[premix]')
    label = 'premix'
    if mix.get('normalize'):
        filters.append(AudioMixer._loudnorm_filter({'loudnorm_target': mix['target_lufs']}, label, 'normalized'))
        label = 'normalized'
    filters.append(f'[{label}]alimiter=limit=0.95:level=0:latency=1,atrim=duration={editor.duration(edl)}[mix]')
    return args, filters, width, height


def status(pid):
    with studio.LOCK:
        value = studio.read_json(studio.project_path(pid) / 'artifacts/manual_render.json', {'status': 'idle'})
    if value['status'] == 'running' and pid not in editor.EXPORTING:
        return {**value, 'status': 'interrupted', 'error': 'Servidor reiniciado; vuelve a solicitar el render'}
    value = deepcopy(value)
    current = editor.state(pid)
    if not value.get('render_sha256') and value.get('path'):
        try:
            project = studio.project_path(pid)
            snapshot = (project / value['path']).parent / 'edit_decisions.json'
            snapshot.resolve().relative_to(project.resolve())
            saved = studio.read_json(snapshot)
            if saved:
                value['render_sha256'] = editor.render_digest(saved, value.get('render_contract', 'legacy'))
                if not value.get('render_contract'):
                    value['render_identity_note'] = 'Render anterior al contrato actual; prepara una copia nueva, el original se conserva'
        except (ValueError, OSError, KeyError, TypeError):
            value['render_identity_note'] = 'No se pudo comparar el snapshot; se exige hash EDL exacto'
    value['current'] = (value['render_sha256'] == current['render_sha256'] if value.get('render_sha256') else
                        value['edit_sha256'] == current['edit_sha256'] if value.get('edit_sha256')
                        else value.get('revision') == current['revision'])
    return value


def start(pid, revision, preview=False, origin='user'):
    with editor.guard(pid, origin):
        value = editor.state(pid)
        editor._revision(value, revision)
        edl = deepcopy(value['edit_decisions'])
        args, filters, width, height = plan(pid, edl, preview)
        job = {'status': 'running', 'attempt': uuid.uuid4().hex, 'revision': revision, 'origin': origin,
               'edit_sha256': value['edit_sha256'],
               'render_sha256': value['render_sha256'],
               'render_contract': editor.RENDER_CONTRACT,
               'preview': preview, 'started_at': studio.now(), 'width': width, 'height': height}
        studio.save_json(studio.project_path(pid) / 'artifacts/manual_render.json', job)
        editor.EXPORTING.add(pid)
        try:
            threading.Thread(target=_worker, args=(pid, edl, job, args, filters), daemon=True).start()
        except RuntimeError as exc:
            editor.EXPORTING.discard(pid)
            job.update(status='failed', error=str(exc), completed_at=studio.now())
            studio.save_json(studio.project_path(pid) / 'artifacts/manual_render.json', job)
            raise ValueError('No se pudo iniciar el render local') from exc
        return job


def _worker(pid, edl, job, args, filters):
    project = studio.project_path(pid)
    work = project / 'assets' / 'editor-renders' / job['attempt']
    output = work / 'montage.mp4'
    try:
        work.resolve().relative_to(project.resolve())
        work.mkdir(parents=True, exist_ok=False)
        used = {clip['source_id'] for clip in edl['cuts'] + edl['audio_tracks'] if clip.get('kind') != 'gap'}
        for key in used:
            info = edl['sources'][key]
            if editor.digest(editor.source(pid, key)) != info['sha256']:
                raise ValueError('Cambió la identidad de un medio; importa su nueva versión')
        video_label = '[montage]'
        for index, title in enumerate(edl.get('titles', [])):
            name = f'title-{index}.ass'
            (work / name).write_text(_ass([title], job['width'], job['height'], title), encoding='utf-8')
            next_label = f'[title{index}]'
            filters.append(f'{video_label}ass={name}{next_label}')
            video_label = next_label
        burn = edl.get('subtitle_style', {}).get('mode') == 'burn'
        if edl['cues']:
            captions = work / 'captions.srt'
            captions.write_text(editor.srt(edl), encoding='utf-8')
            if burn:
                (work / 'captions.ass').write_text(_ass(edl['cues'], job['width'], job['height'], edl['subtitle_style']), encoding='utf-8')
                filters.append(video_label+'ass=captions.ass[captioned]')
                video_label = '[captioned]'
            else:
                args += ['-i', str(captions)]
        command = [require_media('ffmpeg'), '-nostdin', '-v', 'error', '-xerror', '-n', *args,
                   '-filter_complex', ';'.join(filters), '-map', video_label, '-map', '[mix]']
        if edl['cues'] and not burn:
            command += ['-map', f"{len(edl['cuts'])+len(edl['audio_tracks'])}:s:0", '-c:s', 'mov_text',
                        '-metadata:s:s:0', 'language=spa']
        command += ['-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-c:a', 'aac', '-b:a', '192k',
                    '-t', str(editor.duration(edl)), '-movflags', '+faststart', str(output)]
        result = subprocess.run(command, cwd=work, capture_output=True, timeout=600, check=False)
        if result.returncode or not output.is_file() or not output.stat().st_size:
            raise ValueError('FFmpeg: ' + result.stderr.decode('utf-8', 'replace')[-1500:])
        checked = editor.probe(output)
        if checked['kind'] != 'video' or not checked['audio'] or abs(checked['duration'] - editor.duration(edl)) > .15:
            raise ValueError('El resultado no conserva duración, vídeo y audio esperados')
        for key in used:
            if editor.digest(editor.source(pid, key)) != edl['sources'][key]['sha256']:
                raise ValueError('Cambió una fuente durante el render; el resultado no se acredita')
        relative = output.relative_to(project).as_posix()
        job.update(status='completed', completed_at=studio.now(), path=relative,
                   url=f'/media/{pid}/{relative}', sha256=editor.digest(output), bytes=output.stat().st_size,
                   duration=checked['duration'], subtitle_mode=('burn' if burn else 'mov_text') if edl['cues'] else 'none',
                   source_sha256={key: edl['sources'][key]['sha256'] for key in used})
        (work / 'edit_decisions.json').write_text(json.dumps(edl, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as exc:
        job.update(status='failed', completed_at=studio.now(), error=str(exc))
    finally:
        with studio.LOCK:
            try:
                studio.save_json(project / 'artifacts/manual_render.json', job)
            finally:
                editor.EXPORTING.discard(pid)
