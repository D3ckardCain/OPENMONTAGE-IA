"""Opt-in real-media QA. No mocks, inference, downloads or server restart.

Uses the real application through in-process HTTP and an isolated project root.
It does NOT certify the running Studio server, browser playback or listening.
Run with an existing authorized source; originals are only read.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--phase', choices=['video', 'audio', 'subtitles', 'save-preview'], default='video')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    source = args.source.resolve(strict=True)
    workspace = args.workspace.resolve()
    workspace.relative_to(repo / 'projects')
    if args.phase != 'video':
        return resume_phase(args, repo, source, workspace)
    workspace.mkdir(parents=True, exist_ok=False)
    os.environ['OPENMONTAGE_PROJECTS_DIR'] = str(workspace / 'projects')
    sys.path.insert(0, str(repo))
    # Import after the supported process-only projects-root override.
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    from lib import studio_editor as editor, production_studio as studio
    from lib.media_executables import require_media

    report = {'transport': 'in_process_TestClient_NOT_running_Studio',
              'media_engine': 'real_ffmpeg_and_ffprobe', 'mocks': False,
              'browser_playback_verified': False, 'listening_verified': False,
              'source': {'path': str(source), **editor.identity(source)},
              'started_at': studio.now(), 'requests': [], 'renders': {}, 'status': 'running'}
    try:
        report['source']['sha256'] = editor.digest(source)
        report['source']['probe'] = editor.probe(source)
        if report['source']['probe']['duration'] < 43:
            raise ValueError('This bounded protocol requires an existing source of at least 43 seconds')
        client = TestClient(create_app(), base_url='http://127.0.0.1:4750')

        def request(method, route, **kwargs):
            response = client.request(method, '/api/studio/editor/' + route, **kwargs)
            report['requests'].append({'method': method, 'route': route, 'status': response.status_code})
            response.raise_for_status()
            return response.json()

        value = request('POST', 'projects', json={'title': 'QA #92 · medio existente · API aislada'})
        pid = value['project_id']
        report['project_id'] = pid
        project = studio.project_path(pid)
        report['project_path'] = str(project)

        def chunks():
            with source.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    yield chunk

        value = request('POST', pid + '/upload', params={'filename': source.name, 'revision': value['revision']},
                        content=chunks(), headers={'Content-Type': 'application/octet-stream'})
        key = next(iter(value['edit_decisions']['sources']))
        assert value['edit_decisions']['sources'][key]['sha256'] == report['source']['sha256']

        def command(operation, **params):
            nonlocal value
            value = request('POST', pid + '/command', json={'operation': operation, 'revision': value['revision'], **params})
            return value

        def render(label):
            request('POST', pid + '/render', json={'revision': value['revision'], 'preview': True})
            deadline = time.monotonic() + 150
            while time.monotonic() < deadline:
                state = request('GET', pid + '/render')
                if state['status'] != 'running':
                    report['renders'][label] = state
                    if state['status'] != 'completed':
                        raise RuntimeError(label + ': ' + state.get('error', state['status']))
                    assert state['current'] and state['revision'] == value['revision']
                    response = client.get(state['url'], headers={'Range': 'bytes=0-31'})
                    assert response.status_code == 206 and len(response.content) == 32
                    output = project / state['path']
                    decoded = subprocess.run([require_media('ffmpeg'), '-nostdin', '-v', 'error',
                        '-xerror', '-i', str(output), '-f', 'null', '-'], capture_output=True, timeout=60)
                    if decoded.returncode:
                        raise RuntimeError(decoded.stderr.decode('utf-8', 'replace'))
                    state['full_decode_passed'] = True
                    return output
                time.sleep(.25)
            raise TimeoutError('Bounded QA render polling expired; worker state retained')

        command('add', source_id=key)
        first = value['edit_decisions']['cuts'][0]['id']
        command('trim', id=first, in_seconds=10, out_seconds=14)
        original = render('video_before')
        command('split', id=first, at=12)
        second = value['edit_decisions']['cuts'][1]['id']
        command('trim', id=second, in_seconds=40, out_seconds=42)
        command('move', id=second, index=0)
        command('trim', id=first, in_seconds=10.5, out_seconds=12)
        command('save')
        reloaded = request('GET', pid)
        assert reloaded == value
        assert [(c['in_seconds'], c['out_seconds']) for c in reloaded['edit_decisions']['cuts']] == [(40, 42), (10.5, 12)]
        edited = render('video_after')
        assert abs(report['renders']['video_before']['duration'] - 4) < .15
        assert abs(report['renders']['video_after']['duration'] - 3.5) < .15
        frames = project / 'assets/qa-evidence'
        frames.mkdir(parents=True, exist_ok=False)
        ffmpeg = require_media('ffmpeg')
        for name, path, at in [('before-0.5', original, .5), ('after-0.5', edited, .5),
                               ('after-2.5', edited, 2.5), ('source-10.5', source, 10.5),
                               ('source-40.5', source, 40.5), ('source-11', source, 11)]:
            result = subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-n', '-ss', str(at), '-i', str(path),
                '-frames:v', '1', '-vf', 'scale=960:540', str(frames / (name + '.png'))], capture_output=True, timeout=60)
            if result.returncode:
                raise RuntimeError(result.stderr.decode('utf-8', 'replace'))
        report['video_persistence_verified'] = True
        report['frame_evidence_path'] = str(frames)
        report['source_unchanged'] = (editor.identity(source) == {k: report['source'][k] for k in ('bytes', 'mtime_ns')}
                                      and editor.digest(source) == report['source']['sha256'])
        assert report['source_unchanged']
        report['status'] = 'video_backend_completed_pending_visual_review_and_live_UI'
    except Exception as exc:
        report.update(status='failed', error=str(exc))
    finally:
        report['finished_at'] = studio.now()
        (workspace / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'error': report.get('error'), 'report': str(workspace / 'report.json')}, ensure_ascii=True))
    return 1 if report['status'] == 'failed' else 0


def resume_phase(args, repo, source, workspace):
    """Continue the existing real-media project, without reimporting/retesting video."""
    import array
    import math
    os.environ['OPENMONTAGE_PROJECTS_DIR'] = str(workspace / 'projects')
    sys.path.insert(0, str(repo))
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    from lib import studio_editor as editor, production_studio as studio
    from lib.media_executables import require_media
    report_path = workspace / 'report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if str(source) != report['source']['path'] or not report.get('video_persistence_verified'):
        raise ValueError('Resume requires the matching completed video project')
    if editor.identity(source) != {k: report['source'][k] for k in ('bytes', 'mtime_ns')}:
        raise ValueError('Original metadata changed; cached source hash not reused')
    previous = report.get(args.phase)
    if previous:
        if previous.get('status') == 'real_backend_passed_live_UI_and_listening_unverified':
            print(json.dumps({'phase':args.phase,'reused_completed_phase':True,'report':str(report_path)}))
            return 0
        raise ValueError('Phase already has a receipt; preserve it and use a new workspace for another attempt')
    phase = {'started_at': studio.now(), 'status': 'running'}
    report[args.phase] = phase
    pid = report['project_id']
    project = studio.project_path(pid)
    client = TestClient(create_app(), base_url='http://127.0.0.1:4750')
    ffmpeg = require_media('ffmpeg')

    def run(command):
        result = subprocess.run(command, capture_output=True, timeout=90)
        if result.returncode:
            raise RuntimeError(result.stderr.decode('utf-8', 'replace')[-1500:])
        return result.stdout

    def request(method, route, **kwargs):
        response = client.request(method, '/api/studio/editor/' + route, **kwargs)
        report['requests'].append({'method': method, 'route': route, 'status': response.status_code})
        response.raise_for_status()
        return response.json()

    value = request('GET', pid)

    def command(operation, **params):
        nonlocal value
        value = request('POST', pid + '/command', json={'operation': operation, 'revision': value['revision'], **params})

    def render(label):
        request('POST', pid + '/render', json={'revision': value['revision'], 'preview': True})
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            state = request('GET', pid + '/render')
            if state['status'] != 'running':
                report['renders'][label] = state
                if state['status'] != 'completed':
                    raise RuntimeError(state.get('error', state['status']))
                assert state['revision'] == value['revision'] and state['current']
                output = project / state['path']
                run([ffmpeg, '-nostdin', '-v', 'error', '-xerror', '-i', str(output), '-f', 'null', '-'])
                state['full_decode_passed'] = True
                return output
            time.sleep(.25)
        raise TimeoutError('Bounded render polling expired')

    def audio_metrics(path):
        pcm = run([ffmpeg, '-nostdin', '-v', 'error', '-i', str(path), '-t', '4', '-vn',
                   '-ac', '1', '-ar', '48000', '-f', 's16le', '-'])
        values = array.array('h', pcm)
        if sys.byteorder != 'little': values.byteswap()
        return {'samples': len(values), 'rms': math.sqrt(sum(x*x for x in values) / max(1,len(values))) / 32768,
                'peak': max((abs(x) for x in values), default=0) / 32768}

    try:
        evidence = project / 'assets/qa-evidence'
        if args.phase == 'audio':
            audio = evidence / 'existing-source-audio.wav'
            original_key = value['edit_decisions']['cuts'][0]['source_id']
            run([ffmpeg, '-nostdin', '-v', 'error', '-n', '-ss', '10', '-i', str(editor.source(pid,original_key)),
                 '-t', '4', '-map', '0:a:0', '-vn', '-c:a', 'pcm_s16le', str(audio)])
            phase['source_pcm'] = audio_metrics(audio)
            if phase['source_pcm']['rms'] <= .00001:
                raise ValueError('Existing audio is silent; cannot certify gain against it')
            value = request('POST', pid + '/register', json={'relative_path':audio.relative_to(project).as_posix(), 'revision':value['revision']})
            audio_key = next(k for k,v in value['edit_decisions']['sources'].items() if v['path'] == audio.relative_to(project).as_posix())
            for cut in list(value['edit_decisions']['cuts']): command('clip', id=cut['id'], muted=True)
            command('add', source_id=audio_key)
            track = value['edit_decisions']['audio_tracks'][-1]['id']
            command('trim', track='audio', id=track, in_seconds=0, out_seconds=3.5)
            base = render('audio_unity')
            phase['unity_pcm'] = audio_metrics(base)
            command('clip', track='audio', id=track, gain=.25, fade_in=.25, fade_out=.25, start_seconds=0)
            reduced = render('audio_gain_fades')
            phase['gain_fades_pcm'] = audio_metrics(reduced)
            ratio = phase['gain_fades_pcm']['rms'] / phase['unity_pcm']['rms']
            phase['rms_ratio'] = ratio
            assert .05 < ratio < .35
            command('clip', track='audio', id=track, muted=True)
            silent = render('audio_muted')
            phase['muted_pcm'] = audio_metrics(silent)
            assert phase['muted_pcm']['peak'] == 0
            command('clip', track='audio', id=track, muted=False)
        elif args.phase == 'subtitles':
            # Deliberately manual QA text, never represented as a transcription.
            blob = b'\xef\xbb\xbf1\r\n00:00:00,500 --> 00:00:01,500\r\nQA #92: TEXTO MANUAL DE PRUEBA\r\n'
            value = request('POST', pid + '/subtitles/import', params={'filename':'qa-manual.srt', 'revision':value['revision']},
                            content=blob, headers={'Content-Type':'application/octet-stream'})
            command('cue_offset', seconds=.25)
            command('cue_split', index=0, at=1.25, text_index=7)
            command('cue_merge', index=0)
            soft = render('subtitles_soft')
            extracted = run([ffmpeg,'-nostdin','-v','error','-i',str(soft),'-map','0:s:0','-f','srt','-']).decode('utf-8')
            assert 'TEXTO MANUAL DE PRUEBA' in extracted and '00:00:00,750' in extracted
            phase['soft_srt_extracted'] = extracted
            command('subtitle_style', mode='burn', size=40, position='bottom')
            burned = render('subtitles_burned')
            for name,path in [('subtitle-soft',soft),('subtitle-burned',burned)]:
                run([ffmpeg,'-nostdin','-v','error','-n','-ss','1','-i',str(path),'-frames:v','1',str(evidence/(name+'.png'))])
            from PIL import Image, ImageChops, ImageStat
            a = Image.open(evidence/'subtitle-soft.png').convert('RGB')
            b = Image.open(evidence/'subtitle-burned.png').convert('RGB')
            difference = ImageChops.difference(a,b)
            phase['burn_bottom_mean_pixel_change'] = sum(ImageStat.Stat(difference.crop((0,360,960,540))).mean)/3
            assert phase['burn_bottom_mean_pixel_change'] > .05
            record = value['edit_decisions']['subtitle_sources'][-1]
            assert (project/record['path']).read_bytes() == blob
            phase['original_srt_bytes_preserved'] = True
            phase['manual_QA_text_not_transcription'] = True
        else:
            before = render('save_preview_identity')
            before_status = request('GET',pid+'/render')
            before_edit = value['edit_decisions']
            before_revision = value['revision']
            command('save')
            assert request('GET',pid) == value
            after_status = request('GET',pid+'/render')
            assert value['revision'] == before_revision + 1
            assert value['edit_decisions'] == before_edit
            assert after_status['current']
            assert after_status['path'] == before_status['path'] and after_status['sha256'] == before_status['sha256']
            phase.update(preview_reused_after_save=True,edit_sha256=value['edit_sha256'],output=str(before),
                         before_revision=before_revision,after_save_revision=value['revision'])
        command('save')
        assert request('GET',pid) == value
        if args.phase == 'save-preview':
            assert request('GET',pid+'/render')['current']
        phase.update(status='real_backend_passed_live_UI_and_listening_unverified', revision=value['revision'])
        report['status'] = args.phase + '_backend_completed_pending_live_UI'
    except Exception as exc:
        phase.update(status='failed',error=str(exc))
        report.update(status='failed',error=str(exc))
    finally:
        phase['finished_at'] = studio.now()
        report['finished_at'] = phase['finished_at']
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'phase':args.phase,**phase,'report':str(report_path)},ensure_ascii=True))
    return 1 if phase['status'] == 'failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
