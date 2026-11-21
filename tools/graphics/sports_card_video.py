"""Optional narrated local video segment from a sourced sports card; no GPU or publishing."""
import json
import hashlib
import math
import os
from pathlib import Path
import subprocess
import tempfile
from fractions import Fraction
from tools.base_tool import DependencyError, BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ResourceProfile
from tools.graphics.sports_card import render, rasterize, METRIC_SELECTION
from lib.media_executables import require_media


def file_digest(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def inspect_streams(metadata,duration,narration_duration=None):
    streams=metadata.get('streams',[])
    videos=[s for s in streams if s.get('codec_type')=='video']
    audios=[s for s in streams if s.get('codec_type')=='audio']
    if len(videos)!=1 or len(audios)!=(1 if narration_duration is not None else 0):
        raise ValueError('Cantidad de pistas distinta de la solicitada')
    video=videos[0]
    actual=float(metadata.get('format',{}).get('duration',0))
    if not math.isfinite(actual) or abs(actual-duration)>.1 or (video.get('width'),video.get('height'))!=(720,1280):
        raise ValueError('Resolución o duración del clip incorrecta')
    if video.get('codec_name')!='h264' or video.get('pix_fmt')!='yuv420p' or Fraction(video.get('avg_frame_rate','0/1'))!=24:
        raise ValueError('El clip no cumple H.264, yuv420p y 24 fps')
    if audios:
        audio=audios[0];length=float(audio.get('duration',0))
        if audio.get('codec_name')!='aac' or not math.isfinite(length) or length<narration_duration-.06 or length>actual+.1:
            raise ValueError('La narración exportada está incompleta o su formato no coincide')
    return actual,bool(audios)


class SportsCardVideo(BaseTool):
    name='sports_card_video'
    version='0.3.0'
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
        'metrics':METRIC_SELECTION,
        'audio_path':{'type':'string','minLength':1},
        'duration_seconds':{'type':'number','minimum':1,'maximum':30}}}

    def check_dependencies(self):
        from lib.sports_export_requirements import video_requirements
        report=video_requirements()
        if not report['available']:raise DependencyError('; '.join(report['missing']))

    def get_info(self):
        from lib.sports_export_requirements import video_requirements
        info=super().get_info()
        info['export_readiness']=video_requirements()
        return info

    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            svg=render(inputs['report'], inputs.get('metrics'))
            duration=inputs.get('duration_seconds',6)
            ffmpeg=require_media('ffmpeg');ffprobe=require_media('ffprobe')
            audio=None;audio_evidence=None
            if inputs.get('audio_path'):
                audio=Path(inputs['audio_path']).resolve()
                if audio.suffix.lower() not in ('.wav','.flac','.mp3','.m4a','.ogg') or not audio.is_file():
                    raise ValueError('La narración debe ser un archivo de audio local existente')
                before=audio.stat()
                checksum=file_digest(audio)
                probe_audio=subprocess.run([ffprobe,'-v','error','-protocol_whitelist','file,pipe',
                    '-show_streams','-show_format','-of','json',str(audio)],capture_output=True,text=True,timeout=30)
                if probe_audio.returncode:raise ValueError('No se pudo inspeccionar la narración')
                am=json.loads(probe_audio.stdout)
                if not any(s.get('codec_type')=='audio' for s in am.get('streams',[])):
                    raise ValueError('La narración no contiene pista de audio')
                length=float(am.get('format',{}).get('duration',0))
                if not math.isfinite(length) or not 1<=length<=30:raise ValueError('Narración fuera del intervalo 1–30 segundos; dividirla en segmentos')
                if 'duration_seconds' in inputs and duration<length:raise ValueError('La duración recortaría la narración')
                if 'duration_seconds' not in inputs:duration=min(30,math.ceil(length*24)/24)
                audio_evidence={'path':str(audio),'sha256':checksum,'duration_seconds':length}
            if not math.isfinite(duration):raise ValueError('Duración inválida')
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
                         *(['-protocol_whitelist','file,pipe','-i',str(audio)] if audio else []),
                         '-vf',filters,'-t',str(duration),
                         *(['-map','0:v:0','-map','1:a:0','-af','apad','-c:a','aac','-b:a','128k'] if audio else ['-an']),
                         '-c:v','libx264','-threads','2',
                         '-preset','veryfast','-pix_fmt','yuv420p','-movflags','+faststart','-n',str(video)]
                result=subprocess.run(command,capture_output=True,text=True,timeout=180)
                if result.returncode:raise ValueError('FFmpeg: '+result.stderr[-1000:])
                probe=subprocess.run([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,text=True,timeout=30)
                if probe.returncode:raise ValueError('No se pudo inspeccionar el clip')
                metadata=json.loads(probe.stdout)
                actual,has_audio=inspect_streams(metadata,duration,audio_evidence['duration_seconds'] if audio_evidence else None)
                decoded=subprocess.run([ffmpeg,'-nostdin','-v','error','-xerror','-i',str(video),'-f','null','-'],capture_output=True,text=True,timeout=60)
                if decoded.returncode:raise ValueError('El clip no pasó la decodificación completa')
                if audio:
                    after=audio.stat()
                    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or file_digest(audio)!=checksum:
                        raise ValueError('La narración cambió durante el render')
                record={'report_sha256':hashlib.sha256(json.dumps(inputs['report'],sort_keys=True,ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest(),'report':inputs['report'],'narration':audio_evidence,'media':{'path':str(output),'duration_seconds':actual,
                         'resolution':'720x1280','audio':has_audio,'full_decode_passed':True,
                         'fps':24,'video_codec':'h264','pixel_format':'yuv420p',
                         'sha256':file_digest(video),'file_size_bytes':video.stat().st_size},
                        'role':'composition_segment','final_video_verified':False}
                if 'metrics' in inputs:
                    record['displayed_metrics'] = inputs['metrics']
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
