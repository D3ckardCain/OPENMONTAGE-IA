import json
import shutil
import runpy
from pathlib import Path
import pytest
from tools.graphics.sports_card_video import SportsCardVideo


def example():
    return runpy.run_path(str(Path(__file__).with_name('test_sports_card_svg.py')))['report']()


def test_rejects_invalid_report_before_media_or_output(tmp_path,monkeypatch):
    monkeypatch.setattr('tools.graphics.sports_card_video.require_media',lambda name:pytest.fail('No media calls for invalid report'))
    r=example();r['ready_for_script']=False
    out=tmp_path/'clip.mp4'
    assert not SportsCardVideo().execute({'report':r,'output_path':str(out)}).success
    assert not out.exists()


def test_actual_synthetic_clip_and_evidence(tmp_path,monkeypatch):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):pytest.skip('FFmpeg not installed')
    monkeypatch.setattr('tools.graphics.sports_card_video.require_media',shutil.which)
    out=tmp_path/'clip.mp4';tool=SportsCardVideo()
    r=tool.execute({'report':example(),'output_path':str(out),'duration_seconds':1})
    assert r.success,r.error
    assert out.stat().st_size>0
    assert r.data['full_decode_passed'] and not r.data['audio']
    evidence=json.loads(out.with_suffix('.evidence.json').read_text())
    assert evidence['report']['records'][0]['facts'][0]['value']==0
    before=out.read_bytes()
    assert not tool.execute({'report':example(),'output_path':str(out),'duration_seconds':1}).success
    assert out.read_bytes()==before
