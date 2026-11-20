"""Silent local video segment from a sourced sports card; no GPU or publishing."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ResourceProfile
from tools.graphics.sports_card import render, rasterize
from lib.media_executables import require_media


class SportsCardVideo(BaseTool):
    name='sports_card_video'
    version='0.1.0'
    provider='local'
    tier=ToolTier.CORE
    runtime=ToolRuntime.LOCAL
    stability=ToolStability.EXPERIMENTAL
    capability='sports_card_video'
    capabilities=['sports_card_video']
    dependencies=[]
    install_instructions='FFmpeg y ffprobe configurados en el centro de mando; Pillow y fuente Arial o DejaVu Sans. Sin GPU, red ni API de pago.'
    resource_profile=ResourceProfile(cpu_cores=2,ram_mb=512,vram_mb=0,disk_mb=64,network_required=False)
    input_schema={'type':'object','required':['report','output_path'],'additionalProperties':False,'properties':{
        'report':{'type':'object'},'output_path':{'type':'string','minLength':1},
        'duration_seconds':{'type':'number','minimum':1,'maximum':30}}}

    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            svg=render(inputs['report'])
            duration=inputs.get('duration_seconds',6)
            ffmpeg=require_media('ffmpeg');ffprobe=require_media('ffprobe')
            output=Path(inputs['output_path']).absolute()
            if output.suffix.lower()!='.mp4':raise ValueError('La salida debe ser MP4')
            evidence=output.with_suffix('.evidence.json')
            if output.exists() or evidence.exists():raise ValueError('La salida ya existe; usa otro nombre para conservar el trabajo anterior')
            output.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='sports-card-',dir=output.parent) as folder:
                folder=Path(folder);png=folder/'card.png';video=folder/'segment.mp4'
                rasterize(svg,png)
                filters='scale=720:900,pad=720:1280:0:190:color=0x0d1117,fade=t=in:st=0:d=0.25,fade=t=out:st='+str(duration-.25)+':d=0.25'
                command=[ffmpeg,'-nostdin','-v','error','-loop','1','-framerate','24','-i',str(png),
                         '-vf',filters,'-t',str(duration),'-an','-c:v','libx264','-threads','2',
                         '-preset','veryfast','-pix_fmt','yuv420p','-movflags','+faststart','-n',str(video)]
                result=subprocess.run(command,capture_output=True,text=True,timeout=180)
                if result.returncode:raise ValueError('FFmpeg: '+result.stderr[-1000:])
                probe=subprocess.run([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,text=True,timeout=30)
                if probe.returncode:raise ValueError('No se pudo inspeccionar el clip')
                metadata=json.loads(probe.stdout)
                streams=metadata.get('streams',[])
                v=next((s for s in streams if s.get('codec_type')=='video'),{})
                actual=float(metadata.get('format',{}).get('duration',0))
                if (v.get('width'),v.get('height'))!=(720,1280) or abs(actual-duration)>.1:
                    raise ValueError('Resolución o duración del clip incorrecta')
                decoded=subprocess.run([ffmpeg,'-nostdin','-v','error','-xerror','-i',str(video),'-f','null','-'],capture_output=True,text=True,timeout=60)
                if decoded.returncode:raise ValueError('El clip no pasó la decodificación completa')
                record={'report':inputs['report'],'media':{'path':str(output),'duration_seconds':actual,
                         'resolution':'720x1280','audio':False,'full_decode_passed':True},
                        'role':'composition_segment','final_video_verified':False}
                saved=folder/'evidence.json';saved.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
                # Never replace a previous render. The final production still goes through its normal gates.
                if output.exists() or evidence.exists():raise ValueError('La salida apareció durante la exportación')
                os.rename(video,output)
                try:os.rename(saved,evidence)
                except Exception:
                    output.unlink();raise
            return ToolResult(success=True,data=record['media']|{'role':'composition_segment','final_video_verified':False,
                'evidence_path':str(evidence)},artifacts=[str(output),str(evidence)],cost_usd=0)
        except Exception as exc:return ToolResult(success=False,error='SPORTS_VIDEO_REJECTED: '+str(exc),cost_usd=0)
