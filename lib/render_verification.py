"""Technical media verification before final delivery; no inference or publishing."""
import json
import math
import re
from fractions import Fraction
import hashlib
import subprocess
from pathlib import Path
from lib import production_studio as studio
from lib.reference_analysis import executable
from lib.final_delivery import digest


def declarations_digest(outputs):
    return hashlib.sha256(json.dumps(outputs,sort_keys=True,allow_nan=False).encode()).hexdigest()


def football_selection(project_id):
    from lib.football_comparison_dossier import latest_for_agent
    selected = latest_for_agent(project_id)
    if not selected['available']:
        return None
    return {key: selected[key] for key in ('selection_id', 'sha256', 'dossier_path',
                                          'selected_metrics', 'scope', 'source', 'status')}


def _rate(value):
    if not isinstance(value,str) or len(value)>40:return None
    try:
        rate=Fraction(value)
        result=float(rate)
        return result if math.isfinite(result) and result>0 else None
    except (ValueError,ZeroDivisionError,OverflowError):
        return None


def _aspect(video,width,height):
    display=video.get('display_aspect_ratio')
    match=re.fullmatch(r'(\d+)[:/](\d+)',display) if isinstance(display,str) else None
    if match and int(match[2])>0:return int(match[1])/int(match[2])
    sample=video.get('sample_aspect_ratio')
    match=re.fullmatch(r'(\d+)[:/](\d+)',sample) if isinstance(sample,str) else None
    if match and int(match[1])>0 and int(match[2])>0:
        return (width*int(match[1]))/(height*int(match[2]))
    return width/height


def _expected_aspect(value):
    if isinstance(value,(int,float)) and type(value) is not bool and math.isfinite(value) and value>0:
        return float(value)
    if isinstance(value,str):
        match=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*[:/]\s*(\d+(?:\.\d+)?)\s*',value)
        if match and float(match[2])>0:return float(match[1])/float(match[2])
    raise ValueError('Aspect ratio esperado inválido')

def verify(project_id,outputs):
    project=studio.project_path(project_id);report={'status':'running','started_at':studio.now(),
        'outputs':[],'visual_quality_verified':False,'content_accuracy_verified':False,'cost_usd':0}
    report_path=project/'render_verification.json'
    try:
        if not isinstance(outputs,list) or not outputs:raise ValueError('No hay render_report con salidas')
        if len(outputs)>16:raise ValueError('Se admiten hasta 16 salidas por verificación y entrega')
        selected = football_selection(project_id)
        from lib.editorial_freshness import research_index
        research=research_index(project)
        if isinstance(research,dict) and research.get('invalid'):
            raise ValueError('La investigación del proyecto está ausente o alterada')
        report['declared_outputs_sha256']=declarations_digest(outputs)
        probe=executable('ffprobe');decoder=executable('ffmpeg');verified=[];seen=set()
        for item in outputs:
            path=Path(item['path'])
            if not path.is_absolute():path=project/path
            path=path.resolve();path.relative_to((project/'renders').resolve())
            if path in seen:raise ValueError('Render repetido en el informe')
            seen.add(path)
            if not path.is_file() or path.stat().st_size==0:raise ValueError('El render declarado no existe o está vacío')
            before=path.stat()
            result=subprocess.run([probe,'-v','error','-show_format','-show_streams','-of','json',str(path)],
                capture_output=True,text=True,timeout=30)
            if result.returncode:raise ValueError('Render no reconocible por ffprobe')
            metadata=json.loads(result.stdout);streams=metadata.get('streams',[])
            video=next((s for s in streams if s.get('codec_type')=='video'),None)
            duration=float(metadata.get('format',{}).get('duration',0))
            if not video or not math.isfinite(duration) or duration<=0:raise ValueError('La salida no contiene un video de duración positiva y finita')
            width=video.get('width');height=video.get('height')
            if type(width) is not int or type(height) is not int or min(width,height)<=0:raise ValueError('Dimensiones de video inválidas')
            fps=_rate(video.get('avg_frame_rate')) or _rate(video.get('r_frame_rate'))
            aspect=_aspect(video,width,height)
            declared_fps=item.get('fps')
            if declared_fps is not None:
                if type(declared_fps) not in (int,float) or not math.isfinite(declared_fps) or declared_fps<=0:
                    raise ValueError('FPS esperado inválido')
                if fps is None or abs(fps-declared_fps)>max(0.01,declared_fps*0.001):
                    raise ValueError('El FPS real no coincide con render_report')
            declared_aspect=item.get('aspect_ratio')
            if declared_aspect is not None:
                expected_aspect=_expected_aspect(declared_aspect)
                if abs(aspect-expected_aspect)>0.01:
                    raise ValueError('La relación de aspecto real no coincide con render_report')
            declared=item.get('duration_seconds')
            if declared is not None:
                if type(declared) not in (int,float) or not math.isfinite(declared) or declared<=0 or abs(duration-declared)>max(0.25,duration*0.02):raise ValueError('La duración real no coincide con render_report')
            resolution=item.get('resolution','');match=re.fullmatch(r'(\d+)[xX×](\d+)',resolution)
            if match and (int(match[1]),int(match[2]))!=(width,height):raise ValueError('La resolución real no coincide con render_report')
            if item.get('file_size_bytes') is not None and item['file_size_bytes']!=before.st_size:raise ValueError('El tamaño real no coincide con render_report')
            audio=[s for s in streams if s.get('codec_type')=='audio']
            if item.get('audio_codec') and not audio:raise ValueError('Se declaró audio pero el archivo no contiene una pista de audio')
            decode_args=[decoder,'-nostdin','-nostats','-v','info' if audio else 'error',
                '-xerror','-threads','1','-i',str(path),'-map','0:v:0','-map','0:a?']
            if audio:
                decode_args.extend(['-filter:a:0',
                    'aresample=48000,ebur128=peak=true,'
                    'astats=metadata=0:reset=0:measure_perchannel=none:'
                    'measure_overall=Peak_level+RMS_level+Number_of_samples'])
            decode_args.extend(['-threads','1','-f','null','-'])
            decoded=subprocess.run(decode_args,capture_output=True,text=True,
                timeout=min(3600,max(60,math.ceil(duration*3))))
            if decoded.returncode:raise ValueError('El video o audio no superó la decodificación completa: '+decoded.stderr[-600:])
            audio_check={'status':'not_present','stream_count':0}
            if audio:
                from lib.studio_mix_meter import parse as parse_audio_metrics
                try:
                    metrics=parse_audio_metrics(decoded.stderr)
                except ValueError:
                    audio_check={'status':'unavailable','stream_count':len(audio),
                                 'scope':'first_audio_stream','warning':'No se obtuvieron métricas legibles durante el decode.'}
                else:
                    coverage_seconds=metrics['samples_per_channel']/48000
                    warnings=[]
                    if metrics['loudness_below_gate']:
                        warnings.append('loudness_below_gate; no demuestra por sí sola un archivo vacío')
                    if metrics['sample_peak_at_or_above_full_scale']:
                        warnings.append('sample_peak_at_or_above_full_scale')
                    if metrics['true_peak_above_full_scale']:
                        warnings.append('true_peak_above_full_scale')
                    if abs(coverage_seconds-duration)>max(.05,duration*.01):
                        warnings.append('audio_coverage_differs_from_video_duration')
                    audio_check={
                        'status':'warning' if warnings else 'measured',
                        'scope':'first_audio_stream',
                        'stream_count':len(audio),
                        'coverage_seconds':coverage_seconds,
                        'video_duration_seconds':duration,
                        'metrics':metrics,
                        'warnings':warnings,
                    }
            checksum=digest(path);after=path.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('El render cambió durante la verificación')
            record={'path':str(path),'duration_seconds':duration,'width':width,'height':height,
                'video_codec':video.get('codec_name'),'fps':fps,'display_aspect_ratio':aspect,'audio_streams':len(audio),
                'audio_signal_check':audio_check,
                'bytes':after.st_size,'sha256':checksum,'full_decode_passed':True}
            report['outputs'].append(record);verified.append({**item,'path':str(path),'verified_sha256':checksum})
        with studio.LOCK:
            if football_selection(project_id) != selected:
                raise ValueError('La selección de fútbol cambió durante la verificación del render')
            if research_index(project)!=research:
                raise ValueError('La investigación cambió durante la verificación del render')
            report['football_selection'] = selected
            report['channel_research'] = research
            report['status']='passed';report['finished_at']=studio.now();studio.save_json(report_path,report)
        return verified
    except Exception as exc:
        report.update(status='failed',error=str(exc)[:1800],finished_at=studio.now());studio.save_json(report_path,report)
        raise
