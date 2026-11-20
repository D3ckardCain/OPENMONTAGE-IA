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
    import hashlib
    assert r.data['sha256']==hashlib.sha256(out.read_bytes()).hexdigest()
    assert r.data['file_size_bytes']==out.stat().st_size
    assert r.data['fps']==24
    assert r.data['full_decode_passed'] and not r.data['audio']
    evidence=json.loads(out.with_suffix('.evidence.json').read_text())
    assert evidence['report']['records'][0]['facts'][0]['value']==0
    before=out.read_bytes()
    assert not tool.execute({'report':example(),'output_path':str(out),'duration_seconds':1}).success
    assert out.read_bytes()==before


def tone(path,seconds=1.25):
    import wave,struct,math
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(b''.join(struct.pack('<h',int(3000*math.sin(2*math.pi*440*n/16000))) for n in range(int(16000*seconds))))


def test_local_narration_sets_duration_and_retains_evidence(tmp_path,monkeypatch):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):pytest.skip('FFmpeg not installed')
    monkeypatch.setattr('tools.graphics.sports_card_video.require_media',shutil.which)
    voice=tmp_path/'voice.wav';tone(voice)
    out=tmp_path/'narrated.mp4'
    result=SportsCardVideo().execute({'report':example(),'output_path':str(out),'audio_path':str(voice)})
    assert result.success,result.error
    assert result.data['audio'] and abs(result.data['duration_seconds']-1.25)<.1
    record=json.loads(out.with_suffix('.evidence.json').read_text())
    assert record['narration']['path']==str(voice)
    assert len(record['narration']['sha256'])==64
    blocked=tmp_path/'truncated.mp4'
    result=SportsCardVideo().execute({'report':example(),'output_path':str(blocked),'audio_path':str(voice),'duration_seconds':1})
    assert not result.success and not blocked.exists()


def test_missing_or_remote_audio_never_creates_output(tmp_path,monkeypatch):
    monkeypatch.setattr('tools.graphics.sports_card_video.require_media',lambda name:name)
    for path in ('https://example.com/audio.wav',str(tmp_path/'missing.wav')):
        out=tmp_path/'bad.mp4'
        result=SportsCardVideo().execute({'report':example(),'output_path':str(out),'audio_path':path})
        assert not result.success and not out.exists()


def test_export_stream_contract_rejects_incorrect_fps_and_truncated_voice():
    from copy import deepcopy
    from tools.graphics.sports_card_video import inspect_streams
    metadata={'format':{'duration':'2'},'streams':[
        {'codec_type':'video','width':720,'height':1280,'codec_name':'h264','pix_fmt':'yuv420p','avg_frame_rate':'24/1'},
        {'codec_type':'audio','codec_name':'aac','duration':'2'}]}
    assert inspect_streams(metadata,2,2)==(2,True)
    for field,value in [('avg_frame_rate','30/1'),('pix_fmt','yuv444p'),('codec_name','hevc')]:
        broken=deepcopy(metadata);broken['streams'][0][field]=value
        with pytest.raises(ValueError):inspect_streams(broken,2,2)
    broken=deepcopy(metadata);broken['streams'][1]['duration']='1'
    with pytest.raises(ValueError):inspect_streams(broken,2,2)
    with pytest.raises(ValueError):inspect_streams(metadata,2,None)
