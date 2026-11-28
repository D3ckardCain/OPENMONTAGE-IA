"""Bounded own-resource pilot, using registered Blender and FFmpeg bindings."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from tools.base_tool import BaseTool,ToolResult,ToolRuntime,ToolTier,ToolStatus,ResourceProfile
from lib import blender_profiles,production_studio as studio


SCRIPT=Path(__file__).with_name('templates')/'blender-skills-pilot.py'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()


class BlenderSkillsPilot(BaseTool):
    name='blender_skills_pilot'
    version='1.0.0'
    capability='local_blender_validation'
    provider='blender'
    runtime=ToolRuntime.LOCAL_GPU
    tier=ToolTier.GENERATE
    resource_profile=ResourceProfile(network_required=False,ram_mb=2048,vram_mb=2048)
    agent_skills=['ffmpeg']
    side_effects=['writes a separate own-resource QA blend, PNG sequence and MP4 inside an initialized project']
    input_schema={'type':'object','required':['project_id','phase'],'additionalProperties':False,'properties':{
        'project_id':{'type':'string','pattern':'^[a-z0-9-]{1,80}$'},'phase':{'enum':['build','render','inspect','skills_qa']}}}

    def get_status(self):
        try:return ToolStatus.AVAILABLE if Path(blender_profiles.resolve('blender-5.3')['executable']).is_file() else ToolStatus.UNAVAILABLE
        except (ValueError,TypeError):return ToolStatus.UNAVAILABLE

    def estimate_cost(self,inputs):return 0.0

    def execute(self,inputs):
        try:
            from jsonschema import validate
            validate(inputs,self.input_schema)
            pid=inputs['project_id'];phase=inputs['phase']
            if not re.fullmatch('[a-z0-9-]{1,80}',pid):raise ValueError('Invalid project ID')
            root=(studio.PROJECTS_DIR/pid).resolve();root.relative_to(studio.PROJECTS_DIR.resolve())
            if not (root/'project.json').is_file():raise ValueError('Initialize the pipeline project first')
            marker=json.loads((root/'project.json').read_text(encoding='utf-8'))
            if marker.get('pipeline_type')!='blender-skills-pilot' or marker.get('project_id')!=pid:raise ValueError('This tool requires its own pilot project')
            for folder in ('assets/scene','assets/video/frames','artifacts','renders'):(root/folder).resolve().relative_to(root)
            profile=blender_profiles.resolve('blender-5.3')
            if profile['version']!='5.3.0' or not profile['user_resources']:raise ValueError('Pilot requires isolated registered Blender5.3.0')
            blend=root/'assets/scene/pilot.blend';receipt=root/'artifacts/pilot-build.json'
            if phase=='build' and (blend.exists() or receipt.exists()):raise ValueError('Existing pilot: inspect/resume, never overwrite the original')
            if phase!='build':
                report=json.loads(receipt.read_text(encoding='utf-8'))
                if report.get('contract')!='blender-skills-pilot-v1' or report.get('blend_sha256')!=digest(blend):raise ValueError('Pilot blend changed; do not render an unreviewed revision')
            before=digest(blend) if blend.exists() else None
            if phase=='render' and (root/'renders/blender-skills-pilot.mp4').exists():
                raise ValueError('Completed render already exists; inspect it without rerendering')
            command=[profile['executable'],'--background','--offline-mode','--disable-autoexec','--python-exit-code','1']
            if phase=='build':command.append('--factory-startup')
            else:command.append(str(blend))
            command+=['--python',str(SCRIPT),'--','--phase',phase,'--project',str(root)]
            process=subprocess.run(command,env=blender_profiles.environment(profile),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
            (root/'artifacts'/('pilot-'+phase+'.log')).write_text(process.stdout+'\n'+process.stderr,encoding='utf-8')
            if process.returncode:raise ValueError('Blender pilot failed: '+(process.stderr or process.stdout)[-1800:])
            report=json.loads((root/'artifacts'/('pilot-'+phase+'.json')).read_text(encoding='utf-8'))
            if phase=='build':
                report['blend_sha256']=digest(blend);receipt.write_text(json.dumps(report,indent=2),encoding='utf-8')
            elif before!=digest(blend):raise ValueError('Pilot blend unexpectedly modified')
            if phase=='render':report.update(self._package(root))
            return ToolResult(success=True,data=report,artifacts=[str(blend)],model='blender-5.3.0-eevee-pilot')
        except Exception as exc:return ToolResult(success=False,error=str(exc)[:2000])

    def _package(self,root):
        settings=studio.settings();ffmpeg=Path(settings.get('ffmpeg_path',''));ffprobe=Path(settings.get('ffprobe_path',''))
        if not ffmpeg.is_file() or not ffprobe.is_file():raise ValueError('Configured FFmpeg/FFprobe unavailable; no download/fallback')
        frames=root/'assets/video/frames'
        if any(not (frames/f'frame_{n:04d}.png').is_file() for n in range(1,73)):raise ValueError('Incomplete72frame sequence')
        output=root/'renders/blender-skills-pilot.mp4'
        if output.exists():raise ValueError('MP4 already exists; verify it instead of overwriting')
        args=[str(ffmpeg),'-v','error','-n','-framerate','24','-start_number','1','-i',str(frames/'frame_%04d.png'),'-frames:v','72','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(output)]
        result=subprocess.run(args,capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError('FFmpeg packaging failed: '+result.stderr[-1000:])
        result=subprocess.run([str(ffprobe),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(output)],capture_output=True,text=True,timeout=30)
        if result.returncode:raise ValueError('FFprobe failed: '+result.stderr[-1000:])
        probe=json.loads(result.stdout);video=next(s for s in probe['streams'] if s['codec_type']=='video')
        if (video['width'],video['height'],video.get('nb_read_frames'),video['r_frame_rate'])!=(640,360,'72','24/1'):raise ValueError('Unexpected output format/cadence/frame count')
        if abs(float(probe['format']['duration'])-3)>0.001 or any(s['codec_type']=='audio' for s in probe['streams']):raise ValueError('Unexpected duration/audio')
        check=subprocess.run([str(ffmpeg),'-v','error','-i',str(output),'-f','null','-'],capture_output=True,text=True,timeout=30)
        if check.returncode or check.stderr:raise ValueError('Decode validation failed: '+check.stderr[-1000:])
        report={'output':str(output),'sha256':digest(output),'bytes':output.stat().st_size,'probe':probe,'decode_errors':check.stderr}
        (root/'artifacts/pilot-media.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        return report
