"""Bounded #132 pilot using the existing HyperFrames adapter, never a fallback."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import wave
from tools.base_tool import BaseTool,ToolResult,ToolStatus,ToolRuntime
from tools.video.hyperframes_compose import HyperFramesCompose
from lib import checkpoint,hyperframes_runtime
from lib.hyperframes_pilot_process import OwnedHyperFrames

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class HyperFramesOfflinePilot(BaseTool):
    name='hyperframes_offline_pilot'
    version='1.1.0'
    capability='video_post'
    provider='hyperframes'
    runtime=ToolRuntime.LOCAL
    description='Bounded own-resource HyperFrames offline QA; separate project only.'
    agent_skills=['hyperframes','hyperframes-core','hyperframes-cli','ffmpeg']
    input_schema={'type':'object','required':['project_id','phase'],'properties':{'project_id':{'enum':['qa132-hyperframes-offline','qa186-gsap-offline']},'phase':{'enum':['build','render','cancel']}}}

    def get_status(self):
        return ToolStatus.AVAILABLE if hyperframes_runtime.check()['local_requirements_met'] else ToolStatus.UNAVAILABLE

    def execute(self,inputs):
        try:
            if inputs['project_id'] not in ('qa132-hyperframes-offline','qa186-gsap-offline'):raise ValueError('Only explicit separate QA projects are supported')
            root=checkpoint.PROJECTS_DIR/inputs['project_id'];marker=json.loads((root/'project.json').read_text())
            if marker.get('pipeline_type')!='hyperframes-offline-pilot':raise ValueError('Wrong pipeline')
            phase=inputs['phase']
            if inputs['project_id']=='qa186-gsap-offline' and phase not in ('build','render'):raise ValueError('GSAP title scope is build/render only; do not repeat cancellation')
            if phase=='build':return self.build(root)
            workspace=root/'hyperframes';entry=workspace/'index.html';receipt=json.loads((root/'artifacts/pilot-build.json').read_text())
            if sha(entry)!=receipt['html_sha256']:raise ValueError('Authored workspace changed; inspect before reuse')
            adapter=OwnedHyperFrames(root,phase=='cancel')
            if phase=='render':
                target=root/'renders/hyperframes-offline.mp4'
                if target.exists():raise ValueError('Completed output exists; do not render again')
                if inputs['project_id']=='qa132-hyperframes-offline':
                    doctor=HyperFramesCompose().execute({'operation':'doctor'})
                    if not doctor.success:return doctor
                result=adapter.execute({'operation':'render_existing','workspace_path':str(workspace),'output_path':str(target),'fps':24,'quality':'draft'})
                data={'success':result.success,'error':result.error,'data':result.data,'processes':adapter.processes,'html_unchanged':sha(entry)==receipt['html_sha256']}
                (root/'artifacts/pilot-render.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
                return ToolResult(success=result.success,data=data,error=result.error)
            if phase=='cancel':
                render=json.loads((root/'artifacts/pilot-render.json').read_text())
                if not render.get('success'):raise ValueError('Finish and inspect the first render before cancellation test')
                target=root/'renders/cancelled.partial.mp4'
                if target.exists() or (root/'artifacts/pilot-cancel.json').exists() or (root/'artifacts/cancel.request').exists():raise ValueError('Existing cancellation evidence; inspect it instead of repeating')
                result=adapter._run_hf(['render','--output',str(target),'--fps','24','--quality','draft'],cwd=workspace,timeout=120,check=False)
                data={'exit_code':result.returncode,'processes':adapter.processes,'partial_exists':target.exists(),'promoted':False}
                (root/'artifacts/pilot-cancel.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
                return ToolResult(success=result.returncode==130,data=data,error=None if result.returncode==130 else 'No active cancellation demonstrated')
            raise ValueError('Unknown phase')
        except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:return ToolResult(success=False,error=str(exc))

    def build(self,root):
        if root.name=='qa186-gsap-offline':return self.build_gsap_title(root)
        workspace=root/'hyperframes'
        if workspace.exists():raise ValueError('Existing workspace; reuse its checkpoint, do not overwrite')
        workspace.mkdir();assets=workspace/'assets';assets.mkdir()
        audio=ROOT/'projects/edit-635e36b5107a/assets/audio/piper-6336d4f8cfa94f96aa713233b3a5b9a2.wav'
        js=ROOT/'.runtime/hyperframes-0.9.96/node_modules/gsap/dist/gsap.min.js'
        shutil.copy2(audio,assets/'voice.wav');shutil.copy2(audio.with_suffix('.wav.json'),assets/'voice.provenance.json');shutil.copy2(js,assets/'gsap.min.js')
        shutil.copy2(js.parent.parent/'package.json',assets/'gsap.package.json')
        with wave.open(str(audio),'rb') as wav:seconds=wav.getnframes()/wav.getframerate()
        if not 0<seconds<=3.75:raise ValueError('Audio does not fit the bounded4s pilot')
        html=(ROOT/'tools/video/templates/hyperframes-offline-pilot.html').read_text(encoding='utf-8').replace('__AUDIO_DURATION__',str(seconds))
        (workspace/'index.html').write_text(html,encoding='utf-8')
        data={'html_sha256':sha(workspace/'index.html'),'audio_sha256':sha(audio),'audio_copy_sha256':sha(assets/'voice.wav'),'gsap_sha256':sha(js),'audio_seconds':seconds,'audio_offset_seconds':.25,'duration_seconds':4,'fps':24,'width':640,'height':360,'audio_origin':str(audio.relative_to(ROOT)),'audio_attribution':'Sharvard CC BY3.0; HiFiTTS Cori Samuel reader92 CC BY4.0; existing Piper1.8.0 QA output, no new synthesis','gsap_license':'GSAP standard no-charge license; package metadata and header retained','cost_usd':0}
        (root/'artifacts/pilot-build.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        return ToolResult(success=True,data=data)

    def build_gsap_title(self,root):
        from lib.hyperframes_profile_store import read,validate
        selected=read();profile=validate(selected['profile']);workspace=root/'hyperframes'
        if workspace.exists():raise ValueError('Existing title workspace; recover its receipt')
        workspace.mkdir();assets=workspace/'assets';assets.mkdir()
        js=Path(profile['gsap_package_dir'])/'dist/gsap.min.js'
        old=ROOT/'projects/qa132-hyperframes-offline/artifacts/pilot-build.json'
        identity=list(hyperframes_runtime._identity(js))
        reuse=old.is_file() and identity in selected.get('execution_probe',{}).get('identity_key',[]) and js.resolve()==(ROOT/'.runtime/hyperframes-0.9.96/node_modules/gsap/dist/gsap.min.js').resolve()
        gsap_hash=json.loads(old.read_text(encoding='utf-8'))['gsap_sha256'] if reuse else sha(js)
        shutil.copy2(js,assets/'gsap.min.js')
        shutil.copy2(js.parent.parent/'package.json',assets/'gsap.package.json')
        html=(ROOT/'tools/video/templates/hyperframes-gsap-title.html').read_text(encoding='utf-8')
        (workspace/'index.html').write_text(html,encoding='utf-8')
        data={'html_sha256':sha(workspace/'index.html'),'gsap_sha256':gsap_hash,'gsap_hash_reused':reuse,
              'gsap_version':'3.14.2','runtime_profile_revision':selected['revision'],'duration_seconds':3,'fps':24,
              'width':640,'height':360,'audio':False,'cost_usd':0,'scope':'New own GSAP186 title only; no previous132 render repeated'}
        (root/'artifacts/pilot-build.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        return ToolResult(success=True,data=data)
