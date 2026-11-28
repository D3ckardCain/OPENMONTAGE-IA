"""Opt-in ripple regression on an isolated copy of an existing manual project.

Actual HTTP routes via TestClient, copied existing media, no server restart,
FFmpeg, inference or ComfyUI. This does not validate GUI/playback/listening.
"""
from copy import deepcopy
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-project', required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--phase', choices=['before', 'after'], required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    original = (repo/'projects'/args.source_project).resolve(strict=True)
    original.relative_to(repo/'projects')
    workspace = args.workspace.resolve()
    workspace.relative_to(repo/'.runtime/qa')
    workspace.mkdir(parents=True, exist_ok=args.phase == 'after')
    os.environ['OPENMONTAGE_PROJECTS_DIR'] = str(workspace/'projects')
    from lib import production_studio as studio, studio_editor as edit, studio_editor_render as render
    from backlot.server import create_app
    from fastapi.testclient import TestClient
    assert studio.PROJECTS_DIR == workspace/'projects'
    def sha(path):
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                h.update(block)
        return h.hexdigest()
    config_paths = [repo/'.backlot/studio/settings.json', repo/'.backlot/studio/applications.json']
    protected = {str(p.relative_to(repo)): sha(p) for p in config_paths + [original/edit.ARTIFACT]}
    pid = 'edit-ripple-7146510875'
    target = studio.PROJECTS_DIR/pid
    if args.phase == 'before':
        target.mkdir(parents=True, exist_ok=False)
        source_state = json.loads((original/edit.ARTIFACT).read_text(encoding='utf-8'))
        edl = deepcopy(source_state['edit_decisions'])
        video = next(k for k, v in edl['sources'].items() if v['kind'] == 'video' and v['duration'] >= 6)
        audio = next(k for k, v in edl['sources'].items() if v['kind'] == 'audio' and v['duration'] >= 1)
        for info in edl['sources'].values():
            source = edit.media_path(original, info['path'])
            destination = target/info['path']
            destination.resolve().relative_to(target.resolve())
            destination.parent.mkdir(parents=True, exist_ok=True)
            assert sha(source) == info['sha256'], 'Source changed before test copy'
            shutil.copy2(source, destination)
            assert sha(destination) == info['sha256']
        base = {'speed': 1, 'muted': False, 'gain': 1, 'fade_in': 0, 'fade_out': 0, 'start_seconds': 0}
        edl['cuts'] = [{**base, 'id': uuid.uuid4().hex, 'source_id': video, 'source': edl['sources'][video]['path'],
                        'in_seconds': i*2, 'out_seconds': i*2+2} for i in range(3)]
        edl['audio_tracks'] = [{**base, 'id': uuid.uuid4().hex, 'source_id': audio,
                                'source': edl['sources'][audio]['path'], 'in_seconds': 0, 'out_seconds': 1, 'start_seconds': 4}]
        edl['layers'] = [{'id': uuid.uuid4().hex, 'source_id': video, 'source': edl['sources'][video]['path'],
                          'in_seconds': 0, 'out_seconds': 1, 'start_seconds': 4, 'speed': 1,
                          'x': .65, 'y': .05, 'width': .3, 'height': .3, 'opacity': 1}]
        edl['titles'] = [{'id': uuid.uuid4().hex, 'text': 'QA ripple copy', 'start_seconds': 4,
                          'end_seconds': 5, 'size': 80, 'position': 'top'}]
        edl['cues'] = [{'text': 'Manual QA cue', 'start_seconds': 4, 'end_seconds': 5}]
        edl['markers'] = [{'id': uuid.uuid4().hex, 'label': 'QA following', 'seconds': 4.5}]
        edit._validate_edit(edl)
        studio.save_json(target/'production_request.json', {'title': 'Isolated ripple regression copy', 'manual_edit': True})
        studio.save_json(target/'project.json', {'project_id': pid, 'type': 'manual_edit'})
        studio.save_json(target/edit.ARTIFACT, {'revision': 0, 'edit_decisions': edl, 'undo': [], 'redo': [], 'events': []})
        studio.save_json(workspace/'setup.json', {'protected': protected, 'initial_edl': edl})
    setup = studio.read_json(workspace/'setup.json')
    assert protected == setup['protected'], 'Protected files changed between phases'
    report = {'phase': args.phase, 'scope': 'Actual isolated API on copied existing project media; no rendering or live Studio request',
              'source_project': args.source_project, 'copy_project': pid, 'protected_sha256': protected,
              'gui_observed': False, 'av_rendered': False, 'listening': False, 'server_restarted': False}
    try:
        with TestClient(create_app(), base_url='http://127.0.0.1:4750') as client:
            def state():
                response = client.get('/api/studio/editor/'+pid)
                response.raise_for_status()
                return response.json()
            def command(op, origin='user', **params):
                route = 'agent-command' if origin == 'agent' else 'command'
                return client.post('/api/studio/editor/'+pid+'/'+route,
                                   json={'operation': op, 'revision': state()['revision'], **params})
            before = state()
            assert before['edit_decisions'] == setup['initial_edl']
            response = command('ripple_delete', ids=[before['edit_decisions']['cuts'][1]['id']])
            report.update(http_status=response.status_code, response=response.json())
            if args.phase == 'before':
                assert response.status_code == 400 and 'capa' in response.json()['detail']
                report['rejected_atomically'] = state() == before
                assert report['rejected_atomically']
                report['status'] = 'reproduced'
            else:
                response.raise_for_status()
                after = response.json()
                edl = after['edit_decisions']
                assert edit.duration(edl) == 4
                assert edl['layers'][0]['start_seconds'] == edl['audio_tracks'][0]['start_seconds'] == 2
                assert [(t['start_seconds'], t['end_seconds']) for t in edl['titles']] == [(2, 3)]
                assert [(t['start_seconds'], t['end_seconds']) for t in edl['cues']] == [(2, 3)]
                assert edl['markers'][0]['seconds'] == 2.5
                assert edl['sources'] == before['edit_decisions']['sources']
                assert command('undo', origin='agent').json()['edit_decisions'] == before['edit_decisions']
                assert command('redo').json()['edit_decisions'] == edl
                assert command('save', origin='agent').status_code == 200
                _, filters, _, _ = render.plan(pid, edl)
                report['layer_filter'] = next(f for f in filters if '[layer0]' in f)
                report.update(status='passed', undo_redo_shared_api=True, expected_edl=edl)
        if args.phase == 'after':
            with TestClient(create_app(), base_url='http://127.0.0.1:4750') as reopened:
                result = reopened.get('/api/studio/editor/'+pid).json()
                assert result['edit_decisions'] == edl and result['render_sha256'] == after['render_sha256']
                report['reopened_new_app_from_disk'] = True
    finally:
        report['protected_files_unchanged'] = all(sha(repo/p) == value for p, value in protected.items())
        report['source_media_unchanged'] = all(sha(edit.media_path(original, info['path'])) == info['sha256']
                                               for info in setup['initial_edl']['sources'].values())
        assert report['protected_files_unchanged'] and report['source_media_unchanged']
        studio.save_json(workspace/(args.phase+'.json'), report)
        print(json.dumps({k: v for k, v in report.items() if k not in ('response', 'expected_edl', 'protected_sha256')}))


if __name__ == '__main__':
    main()
