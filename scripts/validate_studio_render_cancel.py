"""Opt-in real FFmpeg cancellation; prepared isolated QA root, no live server writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    args=parser.parse_args();repo=Path(__file__).resolve().parents[1]
    workspace=args.workspace.resolve(strict=True);workspace.relative_to(repo/'projects')
    previous=json.loads((workspace/'report.json').read_text(encoding='utf-8'));pid=previous['project_id']
    os.environ['OPENMONTAGE_PROJECTS_DIR']=str(workspace/'projects')
    from lib import production_studio as studio, studio_editor as edit, studio_editor_render as render
    from lib.studio_render_process import CONTROLS
    from fastapi.testclient import TestClient
    from backlot.server import create_app
    assert studio.PROJECTS_DIR==workspace/'projects'
    source=repo/'projects'/previous['source_project']/edit.ARTIFACT
    source_before=hashlib.sha256(source.read_bytes()).hexdigest()
    value=edit.state(pid);before=edit.edit_digest(value);original=render.execute
    def paced(command,work,control,timeout):
        # QA only: pace the first EXISTING input so cancellation has a stable window.
        command=list(command);command.insert(command.index('-i'),'-re')
        return original(command,work,control,timeout)
    def wait(predicate):
        deadline=time.monotonic()+30
        while not predicate():
            if time.monotonic()>deadline:raise RuntimeError('Bounded QA wait expired; no retry')
            time.sleep(.025)
    render.execute=paced
    job=render.start(pid,value['revision'],True)
    wait(lambda:CONTROLS.get(pid) is not None and CONTROLS[pid].process is not None)
    process=CONTROLS[pid].process;time.sleep(.25)
    with TestClient(create_app(),base_url='http://127.0.0.1:4750') as client:
        response=client.post(f'/api/studio/editor/{pid}/render/cancel',json={'attempt':job['attempt']})
        response.raise_for_status();requested=response.json()
        assert requested['status']=='cancelling'
    wait(lambda:pid not in edit.EXPORTING)
    cancelled=render.status(pid)
    assert cancelled['status']=='cancelled' and cancelled['process_stopped'] and process.poll() is not None
    assert 'url' not in cancelled and edit.edit_digest(edit.state(pid))==before
    render.execute=original
    retry=render.start(pid,value['revision'],True);wait(lambda:pid not in edit.EXPORTING)
    completed=render.status(pid)
    assert completed['status']=='completed' and retry['attempt']!=job['attempt']
    path=studio.project_path(pid)/completed['path']
    subprocess.run([studio.settings()['ffmpeg_path'],'-v','error','-xerror','-i',str(path),'-f','null','-'],
                   capture_output=True,check=True,timeout=30)
    assert edit.edit_digest(edit.state(pid))==before
    assert hashlib.sha256(source.read_bytes()).hexdigest()==source_before
    report={'scope':'Real isolated FFmpeg child; in-process actual HTTP API; NOT active4750 or Windows panel',
            'project_id':pid,'cancel_request':requested,'cancelled':cancelled,
            'encoder_exit_code':process.returncode,'retry':completed,'full_decode':True,
            'same_edit_revision':edit.state(pid)['revision']==value['revision'],
            'edit_state_unchanged':True,'source_project_unchanged':True,
            'server_restarted':False,'listening':False,'browser_observation':False,
            'qa_input_pacing':'-re only for cancelled attempt, existing source; no synthetic AV generated'}
    target=workspace/'cancel-report.json'
    if target.exists():raise RuntimeError('QA report already exists; preserve it and inspect before another run')
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(target),'cancelled':True,'process_exited':True,'retry_sha256':completed['sha256']}))


if __name__=='__main__':main()
