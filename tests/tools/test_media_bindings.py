from types import SimpleNamespace
import pytest
from lib import production_studio as studio
from lib.media_executables import find_media,require_media
from tools.analysis import audio_probe
from tools.video.video_compose import VideoCompose

@pytest.fixture
def bound(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    executable=tmp_path/'ffmpeg.exe';executable.write_bytes(b'fixture')
    probe=tmp_path/'ffprobe.exe';probe.write_bytes(b'fixture')
    studio.configure({'ffmpeg_path':str(executable),'ffprobe_path':str(probe)})
    return executable,probe


def test_configured_media_binary_is_available_without_path(bound,monkeypatch):
    from lib import reference_analysis
    monkeypatch.setattr(reference_analysis.shutil,'which',lambda name:None)
    assert find_media('ffmpeg')==str(bound[0])
    assert VideoCompose()._ffmpeg_available() is True


def test_audio_probe_runs_configured_binary_with_simulated_process(bound,monkeypatch,tmp_path):
    source=tmp_path/'audio.wav';source.write_bytes(b'fixture')
    calls=[]
    def run(command,**kwargs):
        calls.append(command);return SimpleNamespace(returncode=0,stdout='{"format":{"duration":"3.5"}}')
    monkeypatch.setattr(audio_probe.subprocess,'run',run)
    assert audio_probe.probe_duration(source)==3.5
    assert calls[0][0]==str(bound[1])


def test_missing_explicit_path_does_not_fallback(bound,monkeypatch):
    from lib import reference_analysis
    monkeypatch.setattr(reference_analysis.shutil,'which',lambda name:str(bound[1]))
    bound[0].unlink()
    assert find_media('ffmpeg') is None
    with pytest.raises(ValueError):require_media('ffmpeg')


def test_child_environment_contains_configured_media_without_mutating_path(bound,monkeypatch):
    import os
    from lib.media_executables import media_environment
    monkeypatch.setenv('PATH','fixture-original')
    result=media_environment()
    assert result['PATH'].split(os.pathsep)[0]==str(bound[0].parent)
    assert os.environ['PATH']=='fixture-original'


def test_video_compose_passes_private_media_environment_to_node(bound,monkeypatch):
    from tools import base_tool
    calls=[]
    def run(command,**kwargs):
        calls.append((command,kwargs));return SimpleNamespace(returncode=0,stdout='',stderr='')
    monkeypatch.setattr(base_tool.subprocess,'run',run)
    VideoCompose().run_command(['node','fixture.js'])
    assert str(bound[0].parent) in calls[0][1]['env']['PATH']
