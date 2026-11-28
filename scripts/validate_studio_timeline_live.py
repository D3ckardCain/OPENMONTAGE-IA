"""Opt-in QA of the live editor using existing authorized project media.

Creates one separate QA project; preserves the source project, original media,
settings and server. No inference, downloads, installations or browser claims.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

from scripts.validate_studio_editor_media import LiveClient
from tools.video.studio_project_edit import StudioProjectEdit


def inspect_render(repo, work, job, report):
    output = work / job['path']
    settings = json.loads((repo / '.backlot/studio/settings.json').read_text(encoding='utf-8'))
    ffmpeg, ffprobe = settings['ffmpeg_path'], settings['ffprobe_path']
    checked = subprocess.run([ffprobe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json',
                              str(output)], capture_output=True, timeout=20, check=True)
    metadata = json.loads(checked.stdout)
    decoded = subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(output), '-f', 'null', '-'],
                             capture_output=True, timeout=90)
    assert decoded.returncode == 0, decoded.stderr.decode('utf-8', 'replace')
    raw = subprocess.run([ffmpeg, '-v', 'error', '-ss', '2.5', '-i', str(output), '-t', '0.5',
                          '-vn', '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'],
                         capture_output=True, timeout=20, check=True).stdout
    samples = array.array('f', raw)
    report.update(status='passed', render={k: job[k] for k in ['revision', 'edit_sha256', 'sha256', 'duration', 'path']},
                  full_decode_passed=True, streams=[{k: s[k] for k in ['codec_type', 'codec_name', 'width', 'height'] if k in s}
                                                   for s in metadata['streams']],
                  audio_window_rms=math.sqrt(sum(x*x for x in samples)/len(samples)),
                  browser_playback='not observed', listening='not performed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-project')
    parser.add_argument('--inspect-project')
    parser.add_argument('--node', type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    if args.inspect_project:
        work = (repo / 'projects' / args.inspect_project).resolve(strict=True)
        work.relative_to(repo / 'projects')
        destination = work / 'artifacts/timeline_live_validation.json'
        report = json.loads(destination.read_text(encoding='utf-8'))
        response = LiveClient('http://127.0.0.1:4750').get('/api/studio/editor/' + args.inspect_project + '/render')
        response.raise_for_status()
        job = response.json()
        if job['status'] != 'completed' or not job['current']:
            raise RuntimeError('No current completed QA render; inspection does not render automatically')
        inspect_render(repo, work, job, report)
        destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report), flush=True)
        return 0
    if not args.source_project or not args.node:
        parser.error('--source-project and --node are required unless --inspect-project is used')
    source_root = (repo / 'projects' / args.source_project).resolve(strict=True)
    source_root.relative_to(repo / 'projects')
    artifact = source_root / 'artifacts/manual_edit.json'
    before = hashlib.sha256(artifact.read_bytes()).hexdigest()
    client = LiveClient('http://127.0.0.1:4750')
    report = {'scope': 'Live HTTP and actual Node UI time arithmetic; NOT browser interaction or listening',
              'source_project': args.source_project, 'events': [], 'restart': False}

    def request(method, path, data=None):
        response = client.request(method, '/api/studio/editor/' + path,
                                  **({'json': data} if data is not None else {}))
        response.raise_for_status()
        return response.json()

    original = request('GET', args.source_project)
    value = request('POST', 'projects', {'title': 'QA #92 timeline 60s - existing authorized media'})
    pid = value['project_id']
    work = repo / 'projects' / pid
    report.update(project_id=pid)
    destination = work / 'artifacts/timeline_live_validation.json'

    def record(operation, value):
        report['events'].append({'operation': operation, 'revision': value['revision'],
                                 'edit_sha256': value['edit_sha256'],
                                 'origin': value['events'][-1]['origin'] if value['events'] else None})
        destination.write_text(json.dumps(report, indent=2), encoding='utf-8')

    def command(operation, agent=False, **params):
        nonlocal value
        data = {'operation': operation, 'revision': value['revision'], **params}
        if agent:
            result = StudioProjectEdit().execute({'project_id': pid, 'action': 'command', 'command': data})
            if not result.success:
                raise RuntimeError(result.error)
            value = request('GET', pid)
        else:
            value = request('POST', pid + '/command', data)
        record(operation, value)
        return value

    def ui_params(function, clip, **params):
        code = ("import fs from 'node:fs';import {splitAtCursor,trimByDelta} from './backlot/ui/editor-time.js';"
                "const p=JSON.parse(fs.readFileSync(0,'utf8'));"
                "console.log(JSON.stringify(p.function==='split'?splitAtCursor(p.edl,p.clip,'video',p.cursor):"
                "trimByDelta(p.edl,p.clip,p.track,p.edge,p.delta)));")
        data = {'function': function, 'edl': value['edit_decisions'], 'clip': clip, **params}
        result = subprocess.run([str(args.node), '--input-type=module', '-e', code],
                                input=json.dumps(data).encode(), cwd=repo, capture_output=True, timeout=10)
        if result.returncode:
            raise RuntimeError(result.stderr.decode('utf-8', 'replace'))
        return json.loads(result.stdout)

    try:
        keys = {}
        for kind in ('video', 'audio'):
            source = next(v for v in original['edit_decisions']['sources'].values() if v['kind'] == kind)
            relative = 'assets/existing-source' + Path(source['path']).suffix
            target = work / relative
            target.parent.mkdir(exist_ok=True)
            os.link(source_root / source['path'], target)
            value = request('POST', pid + '/register', {'relative_path': relative, 'revision': value['revision']})
            keys[kind] = next(k for k, s in value['edit_decisions']['sources'].items() if s['path'] == relative)
            assert value['edit_decisions']['sources'][keys[kind]]['sha256'] == source['sha256']
        command('add', source_id=keys['video'])
        clip = value['edit_decisions']['cuts'][0]
        command('trim', id=clip['id'], track='video', in_seconds=10, out_seconds=70)
        checkpoint = value['edit_sha256']
        clip = value['edit_decisions']['cuts'][0]
        params = ui_params('split', clip, cursor=20)
        command('split', agent=True, **params)
        assert len(value['edit_decisions']['cuts']) == 2
        assert value['edit_decisions']['cuts'][1]['in_seconds'] == 30
        command('undo')
        assert value['edit_sha256'] == checkpoint
        params = ui_params('trim', value['edit_decisions']['cuts'][0], track='video', edge='out', delta=-.25)
        command('trim', **params)
        assert value['edit_decisions']['cuts'][0]['out_seconds'] == 69.75
        command('undo', agent=True)
        assert value['edit_sha256'] == checkpoint
        command('add', source_id=keys['audio'])
        audio = value['edit_decisions']['audio_tracks'][0]
        checkpoint = value['edit_sha256']
        params = ui_params('trim', audio, track='audio', edge='out', delta=-.25)
        command('trim', **params)
        command('undo')
        assert value['edit_sha256'] == checkpoint
        command('clip', id=audio['id'], track='audio', start_seconds=2, gain=.25, fade_in=.25, fade_out=.25)
        params = ui_params('split', value['edit_decisions']['cuts'][0], cursor=20)
        command('split', **params)
        srt = client.get('/api/studio/editor/' + args.source_project + '/subtitles')
        srt.raise_for_status()
        command('subtitles', srt=srt.content.decode('utf-8'))
        checkpoint = value['edit_sha256']
        command('save')
        assert request('GET', pid)['edit_sha256'] == checkpoint
        report['persistence_and_undo'] = 'passed; user/agent share one revisioned EDL'
        print(json.dumps({'project_id': pid, 'commands': 'passed', 'render': 'starting 60s preview'}), flush=True)
        request('POST', pid + '/render', {'revision': value['revision'], 'preview': True})
        deadline = time.monotonic() + 180
        while True:
            job = request('GET', pid + '/render')
            if job['status'] != 'running':
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Bounded render wait expired; no automatic retry')
            time.sleep(1)
        assert job['status'] == 'completed', job
        assert job['current'] and abs(job['duration'] - 60) < .02
        inspect_render(repo, work, job, report)
    finally:
        report['source_project_unchanged'] = hashlib.sha256(artifact.read_bytes()).hexdigest() == before
        destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'report': destination.relative_to(repo).as_posix(), **report}), flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
