"""Opt-in real-media QA for a new timeline model in an isolated projects root.

Never starts/restarts Studio or writes its active projects. Existing media only.
No inference, downloads or installation. Does not certify browser playback/listening.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import os
import re
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-project', required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--recheck', action='store_true')
    parser.add_argument('--effects', action='store_true')
    args = parser.parse_args()
    if args.effects and not args.recheck:
        parser.error('--effects requires --recheck to reuse the prepared QA workspace')
    repo = Path(__file__).resolve().parents[1]
    original = (repo / 'projects' / args.source_project).resolve(strict=True)
    original.relative_to(repo / 'projects')
    workspace = args.workspace.resolve()
    workspace.relative_to(repo / 'projects')
    workspace.mkdir(parents=True, exist_ok=args.recheck)
    os.environ['OPENMONTAGE_PROJECTS_DIR'] = str(workspace / 'projects')
    from lib import studio_editor as edit, studio_editor_render as render, production_studio as studio
    assert studio.PROJECTS_DIR == workspace / 'projects'
    source_artifact = original / edit.ARTIFACT
    before = hashlib.sha256(source_artifact.read_bytes()).hexdigest()
    settings = studio.settings()
    ffmpeg, ffprobe = settings['ffmpeg_path'], settings['ffprobe_path']
    report = {'scope': 'New model loaded in separate Python process and isolated root; NOT active Studio API/UI',
              'workspace': workspace.relative_to(repo).as_posix(), 'source_project': args.source_project,
              'server_restart': False, 'live_backend_activated': False, 'renders': []}
    destination = workspace / 'report.json'
    source = json.loads(source_artifact.read_text(encoding='utf-8'))['edit_decisions']['sources']
    previous = json.loads(destination.read_text(encoding='utf-8')) if args.recheck else None
    if previous:
        report['prior_runs'] = previous.get('prior_runs', []) + [previous['renders']]
        pid = previous['project_id']
    else:
        pid = edit.create('QA atomic timeline - existing authorized media')['project_id']
    work = studio.project_path(pid)
    report['project_id'] = pid

    def command(operation, **params):
        return edit.command(pid, {'operation': operation, 'revision': edit.state(pid)['revision'], **params})

    def pcm_rms(path, seconds):
        result = subprocess.run([ffmpeg, '-v', 'error', '-ss', str(seconds), '-i', str(path), '-t', '0.5',
                                 '-vn', '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'],
                                capture_output=True, check=True, timeout=20)
        samples = array.array('f', result.stdout)
        return math.sqrt(sum(v*v for v in samples)/len(samples))

    def output(label):
        value = edit.state(pid)
        render.start(pid, value['revision'], True)
        deadline = time.monotonic() + 90
        while True:
            job = render.status(pid)
            if job['status'] != 'running':
                break
            if time.monotonic() > deadline:
                raise RuntimeError('Bounded QA wait expired; no retry')
            time.sleep(.25)
        if job['status'] != 'completed':
            raise RuntimeError(job)
        path = work / job['path']
        check = subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'],
                               capture_output=True, timeout=30)
        assert check.returncode == 0, check.stderr.decode('utf-8', 'replace')
        metadata = json.loads(subprocess.run([ffprobe, '-v', 'error', '-show_format', '-show_streams',
                                              '-of', 'json', str(path)], capture_output=True, check=True, timeout=10).stdout)
        entry = {'case': label, 'duration': job['duration'], 'sha256': job['sha256'],
                 'render_sha256': job['render_sha256'], 'full_decode': True,
                 'streams': [s['codec_type'] for s in metadata['streams']],
                 'path': path.relative_to(repo).as_posix()}
        entry['video'] = [{k: s.get(k) for k in ('width', 'height', 'avg_frame_rate')}
                          for s in metadata['streams'] if s['codec_type'] == 'video']
        report['renders'].append(entry)
        destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
        return path, entry

    def effects_cases():
        edl = edit.state(pid)['edit_decisions']
        video_key = next(k for k, v in edl['sources'].items() if v['kind'] == 'video')
        audio_key = next(k for k, v in edl['sources'].items() if v['kind'] == 'audio')
        operations = [{'operation': 'title_remove', 'id': t['id']} for t in edl.get('titles', [])]
        operations += [{'operation': 'marker_remove', 'id': m['id']} for m in edl.get('markers', [])]
        operations += [{'operation': 'remove', 'track': 'audio', 'id': c['id']} for c in edl['audio_tracks']]
        operations += [{'operation': 'remove', 'id': c['id']} for c in edl['cuts']]
        operations += [{'operation': 'add', 'source_id': video_key}]
        value = command('batch', operations=operations)
        clip = value['edit_decisions']['cuts'][0]
        command('trim', id=clip['id'], in_seconds=0, out_seconds=2)
        command('output_custom', width=640, height=360, fps=24, platform='youtube', preset_name='QA editable')
        command('audio_mix', normalize=False, gain=1)
        command('transform', id=clip['id'], fit='crop', zoom=1.25, focus_x=1, focus_y=0, flip_h=True)
        command('title_add', text='QA #92 manual', start_seconds=0, end_seconds=1.75, size=80, position='center')
        path, entry = output('crop-flip-title-custom-output')
        assert entry['video'][0]['width'] == 640 and entry['video'][0]['height'] == 360
        frame = path.parent / 'title-frame.png'
        subprocess.run([ffmpeg, '-v', 'error', '-n', '-ss', '1', '-i', str(path), '-frames:v', '1', str(frame)],
                       capture_output=True, check=True, timeout=10)
        entry['frame'] = frame.relative_to(repo).as_posix()
        value = command('add', source_id=audio_key)
        audio = value['edit_decisions']['audio_tracks'][0]
        command('trim', track='audio', id=audio['id'], in_seconds=0, out_seconds=2)
        command('flags', track='audio', id=audio['id'], solo=True)
        command('audio_mix', normalize=True, target_lufs=-18, gain=1)
        path, entry = output('explicit-normalization-reuses-audio-mixer')
        measured = subprocess.run([ffmpeg, '-v', 'info', '-i', str(path), '-vn', '-af',
                                   'loudnorm=I=-18:print_format=json', '-f', 'null', '-'],
                                  capture_output=True, check=True, timeout=20)
        match = re.search(r'\{\s*"input_i".*?\}', measured.stderr.decode('utf-8', 'replace'), re.S)
        assert match, 'No loudness measurement returned'
        entry['loudnorm_measurement'] = json.loads(match.group())
        assert abs(float(entry['loudnorm_measurement']['input_i'])+18) < 1.5
        return True

    try:
        if args.effects:
            effects_cases()
            report['status'] = 'passed'
            return 0
        if args.recheck:
            value = edit.state(pid)
            keys = {kind: next(k for k, v in value['edit_decisions']['sources'].items() if v['kind'] == kind) for kind in ('video', 'audio')}
            ids = [c['id'] for c in value['edit_decisions']['cuts']]
            audio = value['edit_decisions']['audio_tracks'][0]
            command('flags', id=audio['id'], track='audio', muted=True, solo=False)
        else:
            keys = {}
            for kind in ('video', 'audio'):
                info = next(v for v in source.values() if v['kind'] == kind)
                relative = 'assets/source' + Path(info['path']).suffix
                target = work / relative
                target.parent.mkdir(exist_ok=True)
                os.link(original / info['path'], target)
                value = edit.register(pid, relative, edit.state(pid)['revision'])
                keys[kind] = next(k for k, v in value['edit_decisions']['sources'].items() if v['path'] == relative)
                assert value['edit_decisions']['sources'][keys[kind]]['sha256'] == info['sha256']
            ids = []
            for start in (0, 10, 20):
                value = command('add', source_id=keys['video'])
                clip = value['edit_decisions']['cuts'][-1]
                ids.append(clip['id'])
                command('trim', id=clip['id'], in_seconds=start, out_seconds=start+2)
            before_edit = edit.state(pid)['edit_sha256']
            command('duplicate', ids=[ids[0], ids[2]])
            assert len(edit.state(pid)['edit_decisions']['cuts']) == 5
            command('undo')
            assert edit.state(pid)['edit_sha256'] == before_edit
            command('delete_keep_gap', ids=[ids[1]])
        path, entry = output('preserve-gap')
        assert abs(entry['duration']-6) < .02
        raw = subprocess.run([ffmpeg, '-v', 'error', '-ss', '3', '-i', str(path), '-frames:v', '1',
                              '-vf', 'scale=64:36', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, check=True, timeout=10).stdout
        entry['gap_rgb_mean'] = sum(raw)/len(raw)
        entry['gap_audio_rms'] = pcm_rms(path, 2.5)
        assert entry['gap_rgb_mean'] < 1 and entry['gap_audio_rms'] < .00001
        command('marker_add', seconds=3, label='Shared marker')
        command('flags', id=ids[0], locked=True)
        assert render.status(pid)['current'], 'Metadata must not invalidate AV'
        command('flags', id=ids[0], locked=False)
        if not args.recheck:
            value = command('add', source_id=keys['audio'])
            audio = value['edit_decisions']['audio_tracks'][0]
        command('clip', id=audio['id'], track='audio', gain=.25)
        command('flags', id=audio['id'], track='audio', solo=True, muted=False)
        path, entry = output('solo-independent-audio')
        input_path = edit.source(pid, keys['audio'])
        entry['source_window_rms'] = pcm_rms(input_path, .5)
        entry['output_window_rms'] = pcm_rms(path, .5)
        entry['gain_ratio'] = entry['output_window_rms']/entry['source_window_rms']
        entry['after_solo_clip_rms'] = pcm_rms(path, 5)
        assert abs(entry['gain_ratio']-.25) < .005
        assert entry['after_solo_clip_rms'] < .00001
        report['status'] = 'passed'
    except Exception as exc:
        report.update(status='failed', error=str(exc))
        raise
    finally:
        report.update(source_project_unchanged=hashlib.sha256(source_artifact.read_bytes()).hexdigest() == before,
                      browser_observation=False, listening=False)
        destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
        if args.effects:
            print(json.dumps(report), flush=True)
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
