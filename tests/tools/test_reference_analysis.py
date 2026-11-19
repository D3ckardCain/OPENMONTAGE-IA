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


@pytest.mark.parametrize('url',[
    'https://youtu.be/M2oOPhZtTdU?feature=share',
    'https://www.youtube.com/shorts/M2oOPhZtTdU?feature=share',
    'https://www.youtube.com/watch?v=M2oOPhZtTdU&list=ignored'])
def test_youtube_reference_url_is_normalized(url):
    assert analysis.youtube_url(url)=='https://www.youtube.com/watch?v=M2oOPhZtTdU'


def test_portable_tools_are_detected_without_running_or_downloading(project,monkeypatch):
    root=project/'portable'
    for relative in ('HERRAMIENTAS/yt-dlp/yt-dlp.exe','HERRAMIENTAS/yt-dlp/deno.exe',
                     'HERRAMIENTAS/FFmpeg/version/bin/ffmpeg.exe','HERRAMIENTAS/FFmpeg/version/bin/ffprobe.exe'):
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'not executed fixture')
    monkeypatch.setattr(analysis,'portable_roots',lambda:[root])
    monkeypatch.setattr(analysis.shutil,'which',lambda name:None)
    report=analysis.runtime()
    assert all(tool['found'] for tool in report['tools'].values())
    assert report['inference_tested'] is False


def test_transcript_exports_timed_subtitles_without_rewriting_text():
    content=analysis.transcript_srt([{'start':0.25,'end':2.5,'text':' Hola mundo. '},
        {'start':62,'end':64.125,'text':'Segunda frase.'}])
    assert '00:00:00,250 --> 00:00:02,500\nHola mundo.' in content
    assert '00:01:02,000 --> 00:01:04,125\nSegunda frase.' in content
    with pytest.raises(ValueError):analysis.transcript_srt([{'start':3,'end':2,'text':'bad'}])


def test_selected_source_reuses_download_and_stays_inside_project(project):
    downloaded=project/'reference_analysis/run/download.mp4'
    downloaded.parent.mkdir(parents=True);downloaded.write_bytes(b'fixture')
    studio.save_json(project/'reference_source.json',{'path':'reference_analysis/run/download.mp4'})
    assert analysis.selected_source('one')==downloaded.resolve()
    studio.save_json(project/'reference_source.json',{'path':'../../outside.mp4'})
    with pytest.raises(ValueError):analysis.selected_source('one')


@pytest.mark.parametrize('url',['http://youtube.com/watch?v=M2oOPhZtTdU',
    'https://localhost/watch?v=M2oOPhZtTdU','https://youtube.com.evil.invalid/watch?v=M2oOPhZtTdU',
    'https://youtube.com/playlist?list=test','https://user:password@youtube.com/watch?v=M2oOPhZtTdU'])
def test_other_urls_are_rejected(url):
    with pytest.raises(ValueError):analysis.youtube_url(url)


def test_download_uses_explicit_local_tools_and_does_not_submit_generation(project,monkeypatch):
    seen=[];out=project/'download';out.mkdir()
    monkeypatch.setattr(analysis,'executable',lambda name:'/local/'+name)
    def fake_run(args,**kwargs):
        seen.append(args);(out/'reference.mp4').write_bytes(b'fixture')
        return SimpleNamespace(returncode=0,stdout='done',stderr='')
    monkeypatch.setattr(analysis.subprocess,'run',fake_run)
    source=analysis.download_reference('one','https://youtu.be/M2oOPhZtTdU',out)
    assert source==out/'reference.mp4'
    assert '--ignore-config' in seen[0] and '--no-playlist' in seen[0]
    assert 'deno:/local/deno' in seen[0]
    assert seen[0][-1]=='https://www.youtube.com/watch?v=M2oOPhZtTdU'
    assert (out/'download.log').is_file()


def test_shot_detection_finds_synthetic_hard_cut(project):
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:pytest.skip('FFmpeg required')
    source=project/'cut.mp4'
    subprocess.run([ffmpeg,'-nostdin','-v','error','-y','-f','lavfi','-i','color=black:s=64x64:d=1',
        '-f','lavfi','-i','color=white:s=64x64:d=1','-filter_complex','[0:v][1:v]concat=n=2:v=1:a=0',
        '-c:v','mpeg4',str(source)],check=True,timeout=30)
    result=analysis.detect_shots(ffmpeg,source,2)
    assert len(result['shots'])==2
    assert result['shots'][0]['end_seconds']==pytest.approx(1,abs=0.05)
    assert result['verified_by_human'] is False
