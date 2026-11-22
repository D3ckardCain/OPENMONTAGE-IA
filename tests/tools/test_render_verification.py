"""Technical export verification; simulated probes and small synthetic media."""
import json
import shutil
import subprocess
from types import SimpleNamespace
from pathlib import Path
import pytest
from lib import production_studio as studio,render_verification as checks
from lib import final_delivery,storage_layout


@pytest.fixture
def render(tmp_path,monkeypatch):
    monkeypatch.setattr(studio,'CONFIG_DIR',tmp_path/'config')
    monkeypatch.setattr(studio,'PROJECTS_DIR',tmp_path/'projects')
    monkeypatch.setattr(studio,'REPO_ROOT',tmp_path/'app')
    project=studio.PROJECTS_DIR/'one';studio.save_json(project/'production_request.json',{})
    path=project/'renders/video.mp4';path.parent.mkdir();path.write_bytes(b'fixture bytes')
    return project,path


def transport(monkeypatch,metadata,decode_error=False):
    calls=[]
    monkeypatch.setattr(checks,'executable',lambda name:'/configured/'+name+'.exe')
    def run(args,**kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1 if len(calls)==2 and decode_error else 0,
            stdout=json.dumps(metadata),stderr='broken media' if decode_error else '')
    monkeypatch.setattr(checks.subprocess,'run',run)
    return calls


def metadata(duration='1'):
    return {'format':{'duration':duration},'streams':[{'codec_type':'video','codec_name':'h264','width':64,'height':64}]}


def test_configured_tools_full_decode_and_integrity_receipt(render,monkeypatch):
    project,path=render;calls=transport(monkeypatch,metadata())
    result=checks.verify('one',[{'path':str(path),'duration_seconds':1,'resolution':'64x64'}])
    assert calls[0][0]=='/configured/ffprobe.exe' and calls[1][0]=='/configured/ffmpeg.exe'
    assert '-xerror' in calls[1] and calls[1][-2:]==['null','-']
    assert result[0]['verified_sha256']==final_delivery.digest(path)
    report=studio.read_json(project/'render_verification.json')
    assert report['status']=='passed' and report['outputs'][0]['full_decode_passed']
    assert report['visual_quality_verified'] is False and report['content_accuracy_verified'] is False
    assert report['football_selection'] is None


def test_render_receipt_freezes_saved_football_selection(render, monkeypatch):
    project,path=render;transport(monkeypatch,metadata())
    selected = {'available': True, 'selection_id': 'a'*64, 'sha256': 'b'*64,
                'dossier_path': 'artifacts/football_comparisons/'+'a'*64+'.json',
                'selected_metrics': ['goals'], 'scope': {'competition': 'j1'},
                'source': 'J.League', 'status': 'selection_previewed'}
    monkeypatch.setattr('lib.football_comparison_dossier.latest_for_agent',
                        lambda pid: selected)
    checks.verify('one',[{'path':str(path)}])
    receipt=studio.read_json(project/'render_verification.json')
    assert receipt['football_selection']['selection_id'] == 'a'*64
    assert receipt['football_selection']['selected_metrics'] == ['goals']
    assert receipt['content_accuracy_verified'] is False


def test_changed_football_selection_blocks_render_receipt(render, monkeypatch):
    project,path=render;transport(monkeypatch,metadata())
    calls=iter([{'available': False}, {'available': True, 'selection_id': 'a'*64,
                'sha256': 'b'*64, 'dossier_path': 'artifacts/football_comparisons/'+'a'*64+'.json',
                'selected_metrics': ['goals'], 'scope': {}, 'source': 'J.League',
                'status': 'selection_previewed'}])
    monkeypatch.setattr('lib.football_comparison_dossier.latest_for_agent',
                        lambda pid: next(calls))
    with pytest.raises(ValueError,match='selección de fútbol cambió'):
        checks.verify('one',[{'path':str(path)}])
    assert studio.read_json(project/'render_verification.json')['status']=='failed'


@pytest.mark.parametrize('duration',['NaN','Infinity','0','-1'])
def test_invalid_durations_cannot_mark_export_as_finished(render,monkeypatch,duration):
    project,path=render;calls=transport(monkeypatch,metadata(duration))
    with pytest.raises(ValueError,match='duración'):checks.verify('one',[{'path':str(path)}])
    assert len(calls)==1 and studio.read_json(project/'render_verification.json')['status']=='failed'


@pytest.mark.parametrize('declaration',[{'duration_seconds':60},{'duration_seconds':0},{'resolution':'1920x1080'},{'file_size_bytes':99999},{'audio_codec':'aac'}])
def test_declared_metadata_must_match_real_export(render,monkeypatch,declaration):
    project,path=render;transport(monkeypatch,metadata())
    with pytest.raises(ValueError):checks.verify('one',[{'path':str(path),**declaration}])
    assert path.exists() and studio.read_json(project/'render_verification.json')['status']=='failed'


def test_decode_failure_preserves_render_and_failure_evidence(render,monkeypatch):
    project,path=render;transport(monkeypatch,metadata(),decode_error=True)
    with pytest.raises(ValueError,match='decodificación'):checks.verify('one',[{'path':str(path)}])
    assert path.read_bytes()==b'fixture bytes'
    assert studio.read_json(project/'render_verification.json')['status']=='failed'


def test_changed_render_cannot_be_copied_as_the_verified_version(render,monkeypatch,tmp_path):
    project,path=render;transport(monkeypatch,metadata())
    verified=checks.verify('one',[{'path':str(path)}]);path.write_bytes(b'changed after verification')
    finals=tmp_path/'finals';finals.mkdir()
    storage_layout.configure(studio.REPO_ROOT,{'volumes':[{'name':'Work','projects_dir':str(studio.PROJECTS_DIR)}],
        'active_projects_dir':str(studio.PROJECTS_DIR),'final_outputs_dir':str(finals)},studio.save_json)
    with pytest.raises(ValueError,match='cambió'):final_delivery.deliver('one',verified)
    assert not list(finals.rglob('*.mp4'))


def test_real_synthetic_video_passes_full_decode(render,monkeypatch):
    ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:pytest.skip('FFmpeg required')
    project,path=render
    studio.configure({'ffmpeg_path':ffmpeg,'ffprobe_path':ffprobe})
    monkeypatch.setattr(shutil,'which',lambda name:None)
    subprocess.run([ffmpeg,'-nostdin','-v','error','-y','-f','lavfi','-i','color=blue:s=64x64:d=0.2','-c:v','mpeg4',str(path)],check=True,timeout=20)
    checks.verify('one',[{'path':str(path),'duration_seconds':0.2,'resolution':'64x64'}])
    assert studio.read_json(project/'render_verification.json')['status']=='passed'
