import json
from types import SimpleNamespace
import pytest
from tools.video import hyperframes_offline_pilot as pilot


@pytest.fixture
def project(tmp_path,monkeypatch):
    root=tmp_path/'qa186-gsap-offline';(root/'artifacts').mkdir(parents=True);(root/'hyperframes').mkdir()
    entry=root/'hyperframes/index.html';entry.write_text('own title')
    (root/'artifacts/pilot-build.json').write_text(json.dumps({'html_sha256':pilot.sha(entry)}))
    calls=[]
    class Owned:
        def __init__(self,root,trace=False):self.processes=[];self.trace=trace
        def _run_hf(self,args,**kw):calls.append((args,kw,self.trace));return SimpleNamespace(returncode=0)
    monkeypatch.setattr(pilot,'OwnedHyperFrames',Owned)
    monkeypatch.setattr('lib.media_executables.require_media',lambda _: 'ffprobe-fixture')
    return root,calls


def test_one_frame_gate_preserves_receipt_and_refuses_repeat(project,monkeypatch):
    root,calls=project
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=json.dumps({'streams':[{'nb_read_frames':'1'}]})))
    tool=pilot.HyperFramesOfflinePilot();assert tool.diagnostic186(root,'frame186').success
    assert calls[0][0][-4:]==['--start','1','--end',str(1+1/24)] and not calls[0][2]
    with pytest.raises(ValueError,match='Existing diagnostic receipt'):tool.diagnostic186(root,'frame186')
    assert len(calls)==1


def test_full_trace_requires_actual_gate_and_checks_72(project,monkeypatch):
    root,calls=project;tool=pilot.HyperFramesOfflinePilot()
    (root/'artifacts/frame186.json').write_text('{"success":false}')
    with pytest.raises(ValueError,match='must pass first'):tool.diagnostic186(root,'trace186')
    assert not calls
    (root/'artifacts/frame186.json').write_text('{"success":true}')
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=json.dumps({'streams':[{'nb_read_frames':'71'}]})))
    result=tool.diagnostic186(root,'trace186');assert not result.success and '71' in result.error
    assert calls[0][2] and calls[0][1]['timeout']==45
    assert (root/'artifacts/trace186.json').is_file()


def test_changed_authored_title_is_not_rendered(project):
    root,calls=project;(root/'hyperframes/index.html').write_text('changed')
    with pytest.raises(ValueError,match='Title changed'):pilot.HyperFramesOfflinePilot().diagnostic186(root,'frame186')
    assert not calls
