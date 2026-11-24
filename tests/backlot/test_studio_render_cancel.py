"""Owned subprocess cancellation and persistent shared render state, offline."""
from copy import deepcopy
import sys
import threading
import time

import pytest
from fastapi.testclient import TestClient

from backlot.server import create_app
from lib import studio_editor as edit, studio_editor_render as render
from lib.studio_render_process import CONTROLS, Control, Cancelled, execute
from tests.backlot.test_studio_editor import project, command, add


def wait_for(predicate, timeout=5):
    deadline=time.monotonic()+timeout
    while not predicate():
        assert time.monotonic()<deadline, 'Bounded test deadline exceeded'
        time.sleep(.01)


def test_owned_child_exits_on_cancel_and_timeout(tmp_path):
    control=Control('cancel-test');errors=[]
    def run():
        try:execute([sys.executable,'-c','import time;time.sleep(30)'],tmp_path,control)
        except Cancelled as exc:errors.append(str(exc))
    worker=threading.Thread(target=run);worker.start()
    wait_for(lambda:control.process is not None)
    control.event.set();worker.join(5)
    assert not worker.is_alive() and errors and control.stopped
    assert control.process.poll() is not None
    import subprocess
    timeout=Control('timeout-test')
    with pytest.raises(subprocess.TimeoutExpired):
        execute([sys.executable,'-c','import time;time.sleep(30)'],tmp_path,timeout,timeout=.1)
    assert timeout.stopped and timeout.process.poll() is not None


def test_cancel_api_retains_ownership_until_exit_and_retries_without_edit_replay(project,monkeypatch):
    pid,key,_=project;add(pid,key);before=deepcopy(edit.state(pid));real_execute=execute
    def controlled(command,work,control,timeout):
        return real_execute([sys.executable,'-c','import time;time.sleep(30)'],work,control,timeout)
    monkeypatch.setattr(render,'execute',controlled)
    monkeypatch.setattr(render,'require_media',lambda _:sys.executable)
    job=render.start(pid,before['revision'],True);attempt=job['attempt']
    wait_for(lambda:CONTROLS.get(pid) is not None and CONTROLS[pid].process is not None)
    process=CONTROLS[pid].process
    with TestClient(create_app(),base_url='http://127.0.0.1:4750') as client:
        stale=client.post(f'/api/studio/editor/{pid}/render/cancel',json={'attempt':'older-attempt'})
        assert stale.status_code==409 and process.poll() is None
        result=client.post(f'/api/studio/editor/{pid}/agent-render/cancel',json={'attempt':attempt})
        assert result.status_code==200 and result.json()['status']=='cancelling'
    wait_for(lambda:pid not in edit.EXPORTING)
    saved=render.status(pid)
    assert saved['status']=='cancelled' and saved['process_stopped'] and saved['cancel_origin']=='agent'
    assert process.poll() is not None and 'url' not in saved and 'path' not in saved
    assert edit.state(pid)==before and pid not in CONTROLS
    assert render.cancel(pid,attempt)['status']=='cancelled'
    second=render.start(pid,before['revision'],True)
    assert second['attempt']!=attempt
    render.cancel(pid,second['attempt'])
    wait_for(lambda:pid not in edit.EXPORTING)
    assert render.status(pid)['status']=='cancelled' and edit.state(pid)==before


def test_cancel_before_spawn_does_not_start_encoder(project,monkeypatch):
    pid,key,_=project;add(pid,key)
    value=edit.state(pid);args,filters,width,height=render.plan(pid,value['edit_decisions'])
    control=Control('before-spawn');control.event.set();CONTROLS[pid]=control;edit.EXPORTING.add(pid)
    monkeypatch.setattr(render,'require_media',lambda _:pytest.fail('Must not spawn encoder'))
    job={'status':'running','attempt':control.attempt,'revision':value['revision'],'width':width,'height':height}
    render._worker(pid,value['edit_decisions'],job,args,filters)
    assert render.status(pid)['status']=='cancelled' and not render.status(pid)['encoder_started']
    assert edit.state(pid)==value and pid not in CONTROLS and pid not in edit.EXPORTING
