import shutil
import subprocess
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from backlot.server import create_app
from lib import production_studio as studio
from lib import reference_analysis as analysis
from tools.base_tool import ToolStatus,ToolResult


@pytest.fixture
def project(tmp_path,monkeypatch):
    from lib import production_agent
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(production_agent,'ACTIVE',{})
    monkeypatch.setattr(analysis,'ACTIVE',set())
    path=studio.PROJECTS_DIR/'one';studio.save_json(path/'production_request.json',{})
    return path


def test_upload_does_not_analyze_and_reports_are_project_scoped(project):
    with TestClient(create_app(),base_url='http://127.0.0.1:4750') as client:
        base='/api/studio/reference-video/one'
        assert client.post(base+'/upload',content=b'uploaded-test-bytes').json()['analysis_started'] is False
        assert (project/'reference_video.mp4').read_bytes()==b'uploaded-test-bytes'
        assert client.get(base).json()['status']=='not_started'
        assert client.get('/api/studio/reference-video/absent').status_code==404
        assert client.post(base+'/upload',content=b'').status_code==400
        assert client.post(base+'/upload',content=b'x',headers={'origin':'https://other.invalid'}).status_code==403


def test_active_analysis_blocks_source_replacement(project):
    analysis.ACTIVE.add('one')
    with TestClient(create_app(),base_url='http://127.0.0.1:4750') as client:
        assert client.post('/api/studio/reference-video/one/upload',content=b'x').status_code==409
    assert not (project/'reference_video.mp4').exists()


def test_analysis_options_fail_before_starting_work(project):
    for data in ({'frames':0},{'frames':True},{'device':'cuda'},{'vision_model':'paid'},{'vision':'yes'}):
        with pytest.raises(ValueError):analysis.start('one',data)


def test_synthetic_video_runs_through_local_extraction_and_model_contracts(project,monkeypatch):
    ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:pytest.skip('FFmpeg required for integration fixture')
    studio.configure({'ffmpeg_path':ffmpeg,'ffprobe_path':ffprobe})
    source=project/'reference_video.mp4'
    subprocess.run([ffmpeg,'-nostdin','-v','error','-y','-f','lavfi','-i','color=blue:s=64x64:d=1',
        '-f','lavfi','-i','sine=frequency=440:duration=1','-c:v','mpeg4','-c:a','aac','-shortest',str(source)],check=True,timeout=30)
    from tools import tool_registry
    seen=[]
    class Registry:
        def discover(self,*args):pass
        def get(self,name):
            def execute(inputs):
                seen.append((name,inputs))
                return ToolResult(success=True,data={'result':{'text':'synthetic fixture analysis'}})
            return SimpleNamespace(get_status=lambda:ToolStatus.AVAILABLE,execute=execute)
    monkeypatch.setattr(tool_registry,'ToolRegistry',Registry)
    out=project/'reference_analysis/run-test';out.mkdir(parents=True)
    report=analysis.analyze('one',source,{'frames':2,'vision':True,'vision_model':'smolvlm','transcribe':True,'summary':True},out)
    assert report['status']=='completed',report
    assert report['media']['width']==64 and len(report['frames'])==2
    assert all(inputs['device']=='cpu' for _,inputs in seen)
    assert {name for name,_ in seen}=={'model_smolvlm','model_faster_whisper','model_qwen3'}
    assert report['external_fact_check']=='not_performed'
    assert (out/'audio.wav').is_file() and (out/'report.json').is_file()


def test_missing_executables_create_explicit_failure(project,monkeypatch):
    monkeypatch.setattr(analysis,'executable',lambda name:(_ for _ in ()).throw(ValueError('Missing '+name)))
    out=project/'test';out.mkdir()
    report=analysis.analyze('one',project/'source.mp4',{},out)
    assert report['status']=='failed' and 'Missing ffmpeg' in report['error']
