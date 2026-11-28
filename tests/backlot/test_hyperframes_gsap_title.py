import json
from pathlib import Path
import pytest
from tools.video import hyperframes_offline_pilot as pilot
from lib import hyperframes_profile_store as profiles


def test_new_title_build_selected_profile_and_reuse(tmp_path,monkeypatch):
    root=tmp_path/'qa186-gsap-offline';(root/'artifacts').mkdir(parents=True)
    package=tmp_path/'.runtime/hyperframes-0.9.96/node_modules/gsap'
    (package/'dist').mkdir(parents=True);js=package/'dist/gsap.min.js';js.write_text('/* own test stub */')
    (package/'package.json').write_text('{"name":"gsap","version":"3.14.2"}')
    old=tmp_path/'projects/qa132-hyperframes-offline/artifacts/pilot-build.json';old.parent.mkdir(parents=True)
    old.write_text(json.dumps({'gsap_sha256':pilot.sha(js)}))
    template=Path(pilot.ROOT/'tools/video/templates/hyperframes-gsap-title.html').read_text(encoding='utf-8')
    dest=tmp_path/'tools/video/templates';dest.mkdir(parents=True);(dest/'hyperframes-gsap-title.html').write_text(template,encoding='utf-8')
    identity=list(pilot.hyperframes_runtime._identity(js))
    monkeypatch.setattr(pilot,'ROOT',tmp_path)
    monkeypatch.setattr(profiles,'read',lambda:{'profile':{'gsap_package_dir':str(package)},'revision':7,'execution_probe':{'identity_key':[identity]}})
    monkeypatch.setattr(profiles,'validate',lambda p:p)
    before=js.stat();result=pilot.HyperFramesOfflinePilot().build(root)
    assert result.success and result.data['gsap_hash_reused'] and result.data['runtime_profile_revision']==7
    assert result.data['audio'] is False and result.data['duration_seconds']==3
    assert js.stat().st_mtime_ns==before.st_mtime_ns and js.stat().st_ino==before.st_ino
    with pytest.raises(ValueError,match='Existing title workspace'):pilot.HyperFramesOfflinePilot().build(root)


def test_title_template_paused_local_explicit_timeline():
    html=(pilot.ROOT/'tools/video/templates/hyperframes-gsap-title.html').read_text(encoding='utf-8')
    assert 'data-composition-id="qa186"' in html and 'window.__timelines.qa186=tl' in html
    assert 'paused:true' in html and 'immediateRender:false' in html
    assert 'src="assets/gsap.min.js"' in html
    assert not any(x in html for x in ['https://','autoAlpha','Math.random','Date.now','.play('])
