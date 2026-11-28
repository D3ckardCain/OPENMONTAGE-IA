"""Focal offline regressions #132, no real CLI/browser/media/models."""
import json
import subprocess
import pytest
from lib import hyperframes_runtime as runtime,hyperframes_staging as staging
from tools.video.hyperframes_compose import HyperFramesCompose


@pytest.fixture
def local(tmp_path,monkeypatch):
    runtime._DOCTOR.clear()
    root=tmp_path/'package';root.mkdir();(root/'bin').mkdir();(root/'bin/hf.mjs').write_text('// synthetic, never executed')
    (root/'package.json').write_text(json.dumps({'name':'hyperframes','version':'0.9.96','bin':{'hyperframes':'bin/hf.mjs'}}))
    browser=tmp_path/'chrome';browser.write_text('not executed')
    monkeypatch.setenv('HYPERFRAMES_PACKAGE_DIR',str(root));monkeypatch.setenv('HYPERFRAMES_BROWSER_PATH',str(browser))
    monkeypatch.setattr(runtime.shutil,'which',lambda name:'/prepared/node' if name=='node' else None)
    monkeypatch.setattr(runtime,'find_media',lambda name:'/prepared/'+name)
    calls=[]
    def run(cmd,**kwargs):
        calls.append(cmd);assert cmd==['/prepared/node','--version'];return subprocess.CompletedProcess(cmd,0,'v22.10.0\n','')
    monkeypatch.setattr(runtime.subprocess,'run',run)
    return root,browser,calls


def test_catalog_local_only_no_cli_network_or_disk_writes(local,monkeypatch):
    root,browser,calls=local;before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
    monkeypatch.setattr(HyperFramesCompose,'_probe_cli',classmethod(lambda cls:pytest.fail('Catalog executed CLI')))
    report=HyperFramesCompose().get_info()['hyperframes_runtime']
    assert report['local_requirements_met'] and not report['runtime_available'] and report['installed'] and not report['render_validated']
    assert report['cli_probe_status']=='not_run' and all(cmd[-1]=='--version' for cmd in calls)
    assert before=={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('failure',['missing','version','entry','escape','node','ffprobe','browser'])
def test_real_local_requirements_fail_closed(local,monkeypatch,failure):
    root,browser,calls=local
    if failure=='missing':(root/'package.json').unlink()
    if failure in ('version','entry','escape'):
        data=json.loads((root/'package.json').read_text())
        if failure=='version':data['version']='0.9.97'
        if failure=='entry':data['bin']['hyperframes']='missing.mjs'
        if failure=='escape':data['bin']['hyperframes']='../../outside.mjs'
        (root/'package.json').write_text(json.dumps(data))
    if failure=='node':monkeypatch.setattr(runtime.shutil,'which',lambda name:None)
    if failure=='ffprobe':monkeypatch.setattr(runtime,'find_media',lambda name:None if name=='ffprobe' else '/ffmpeg')
    if failure=='browser':browser.unlink()
    result=runtime.check();assert not result['runtime_available'] and result['reasons']


def test_no_stale_negative_cache_and_same_resolver_for_execution(local):
    root,browser,calls=local;p=root/'package.json';content=p.read_text();p.unlink()
    assert not runtime.check()['installed'];p.write_text(content)
    assert runtime.check()['local_requirements_met']
    assert runtime.command(['doctor','--json'])==['/prepared/node',str((root/'bin/hf.mjs').resolve()),'doctor','--json']


def test_doctor_cache_bound_to_current_install_and_expires(local,monkeypatch):
    root,browser,calls=local;now=runtime.check()
    runtime.remember(now,{'status':'ok','error':None})
    assert runtime.check()['runtime_available']
    (root/'bin/hf.mjs').write_text('// modified synthetic CLI')
    assert not runtime.check()['runtime_available']
    runtime.remember(runtime.check(),{'status':'ok','error':None})
    original=runtime.time.monotonic();monkeypatch.setattr(runtime.time,'monotonic',lambda:original+61)
    assert not runtime.check()['runtime_available']


def test_explicit_doctor_failure_invalidates_prior_healthy_receipt(local,monkeypatch):
    runtime.remember(runtime.check(),{'status':'ok','error':None})
    assert runtime.check()['runtime_available']
    monkeypatch.setattr(HyperFramesCompose,'_run_hf',lambda self,args,**kw:subprocess.CompletedProcess(args,1,'','synthetic failure'))
    assert not HyperFramesCompose().execute({'operation':'doctor'}).success
    assert not runtime.check()['runtime_available']


@pytest.mark.parametrize('failure',['FFprobe','Chrome','Memory',None,'malformed','missing'])
def test_doctor_exit_zero_uses_required_json_not_optional_checks(local,monkeypatch,failure):
    rows=[dict(name=n,ok=n!=failure) for n in runtime.REQUIRED_CHECKS]+[dict(name='Docker',ok=False),dict(name='TTS (Kokoro)',ok=False)]
    if failure=='missing':rows=rows[:-3]
    value={'ok':False,'checks':rows} if failure!='malformed' else {'ok':True}
    monkeypatch.setattr(HyperFramesCompose,'_run_hf',lambda self,args,**kw:subprocess.CompletedProcess(args,0,json.dumps(value),''))
    result=HyperFramesCompose().execute({'operation':'doctor'})
    assert result.success==(failure is None)
    if failure is None:assert len(result.data['cli_doctor']['optional'])==2


def test_staging_same_basename_size_and_reuse_only_unchanged_identity(tmp_path,monkeypatch):
    a=tmp_path/'a';b=tmp_path/'b';w=tmp_path/'workspace'
    for p in [a,b,w]:p.mkdir()
    first=a/'same.wav';second=b/'same.wav';first.write_bytes(b'AAAA');second.write_bytes(b'BBBB')
    t1=staging.stage(first,w);t2=staging.stage(second,w)
    assert t1!=t2 and t1.read_bytes()==b'AAAA' and t2.read_bytes()==b'BBBB'
    (w/'assets/same.wav').write_bytes(b'foreign')
    original=staging.digest;reads=[]
    monkeypatch.setattr(staging,'digest',lambda p:(reads.append(p),original(p))[1])
    assert staging.stage(first,w)==t1 and reads==[]
    first.write_bytes(b'CCCC');t3=staging.stage(first,w)
    assert t3!=t1 and t1.read_bytes()==b'AAAA' and (w/'assets/same.wav').read_bytes()==b'foreign'


def test_audio_video_same_name_route_through_one_content_stager(tmp_path):
    w=tmp_path/'w';w.mkdir();a=tmp_path/'a';b=tmp_path/'b';a.mkdir();b.mkdir()
    v=a/'same.mp4';m=b/'same.mp4';v.write_bytes(b'video');m.write_bytes(b'audio')
    tool=HyperFramesCompose();cuts,_=tool._resolve_and_stage_assets([{'source':'v'}],[{'id':'v','path':str(v)}],w)
    refs=tool._resolve_audio_refs({'music':{'asset_id':'m','volume':0}},[{'id':'m','path':str(m)}],w)
    assert cuts[0]['source']!=refs['music']['src'] and refs['music']['volume']==0


def test_zero_volume_reaches_generated_html():
    html=HyperFramesCompose()._generate_index_html([],{'music':{'src':'assets/music.wav','volume':0}},640,360,1,{},'Synthetic only')
    assert 'data-volume="0"' in html


def test_identical_contents_reuse_copy_and_foreign_hash_target_is_preserved(tmp_path):
    w=tmp_path/'w';w.mkdir();a=tmp_path/'a.wav';b=tmp_path/'b.wav';a.write_bytes(b'same');b.write_bytes(b'same')
    target=staging.stage(a,w);assert staging.stage(b,w)==target
    target.write_bytes(b'foreign modified')
    with pytest.raises(ValueError,match='se conserva'):staging.stage(a,w)
    assert target.read_bytes()==b'foreign modified' and a.read_bytes()==b'same'


@pytest.mark.parametrize('fade',['fade_in_seconds','fade_out_seconds'])
def test_unimplemented_music_fades_are_explicit_not_silently_dropped(tmp_path,fade):
    with pytest.raises(ValueError,match='no aplica fades'):
        HyperFramesCompose()._resolve_audio_refs({'music':{fade:1}},[],tmp_path)
