"""Project reference analysis using local executables and offline model adapters."""
import json
import math
import os
import re
import shutil
import subprocess
import threading
import uuid
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from lib import production_studio as studio

LOCK=threading.RLock()
ACTIVE=set()


def executable(name):
    configured=studio.settings().get(name.replace('-','_')+'_path','')
    value=configured or shutil.which(name)
    if not value:
        for root in portable_roots():
            patterns=[f'HERRAMIENTAS/yt-dlp/{name}.exe'] if name in ('yt-dlp','deno') else [f'HERRAMIENTAS/FFmpeg/bin/{name}.exe',f'HERRAMIENTAS/FFmpeg/*/bin/{name}.exe']
            found=next((path for pattern in patterns for path in sorted(root.glob(pattern)) if path.is_file()),None)
            if found:value=str(found);break
    if not value or not Path(value).is_file():raise ValueError('Configura la ruta de '+name+' en el Estudio')
    return str(value)


def portable_roots():
    roots=[studio.REPO_ROOT,*map(Path,studio.settings().get('resource_roots',[]))]
    if os.name=='nt':roots.extend([Path('C:/OPENMONTAJE-IA'),Path('D:/OPENMONTAJE-IA')])
    return roots


def runtime():
    tools={}
    for name in ('ffmpeg','ffprobe','yt-dlp','deno'):
        try:tools[name]={'found':True,'path':executable(name)}
        except ValueError as exc:tools[name]={'found':False,'problem':str(exc)}
    return {'tools':tools,'inference_tested':False,'cost_usd':0}


def selected_source(project_id):
    root=studio.project_path(project_id).resolve()
    record=studio.read_json(root/'reference_source.json',{'path':'reference_video.mp4'})
    source=(root/record['path']).resolve();source.relative_to(root)
    return source


def youtube_url(value):
    if not isinstance(value,str) or len(value)>2000:raise ValueError('Enlace inválido')
    parsed=urlsplit(value)
    if parsed.scheme!='https' or parsed.username or parsed.password or parsed.port not in (None,443):raise ValueError('Usa un enlace HTTPS de YouTube')
    host=(parsed.hostname or '').lower();identifier=None
    if host=='youtu.be':identifier=parsed.path.lstrip('/')
    elif host in ('youtube.com','www.youtube.com','m.youtube.com'):
        if parsed.path=='/watch':identifier=parse_qs(parsed.query).get('v',[''])[0]
        elif parsed.path.startswith('/shorts/'):identifier=parsed.path.split('/')[2]
    if not identifier or not re.fullmatch(r'[A-Za-z0-9_-]{11}',identifier):raise ValueError('Se requiere el enlace de un video, no una lista ni un canal')
    return 'https://www.youtube.com/watch?v='+identifier


def download_reference(project_id,url,output):
    """Called by the background task, never by page refresh or metadata reads."""
    ffmpeg=executable('ffmpeg');downloader=executable('yt-dlp');deno=executable('deno')
    args=[downloader,'--ignore-config','--no-playlist','--no-cache-dir',
          '--ffmpeg-location',str(Path(ffmpeg).parent),'--js-runtimes','deno:'+deno,
          '--max-filesize','500M','--match-filter','duration <= 1800',
          '-f','bv*[height<=1080]+ba/b[height<=1080]','--merge-output-format','mp4',
          '--remux-video','mp4','--write-info-json','-o',str(output/'reference.%(ext)s'),youtube_url(url)]
    result=subprocess.run(args,capture_output=True,text=True,timeout=1800)
    # Preserve diagnostics locally, not in an unbounded UI report.
    (output/'download.log').write_text((result.stdout+'\n'+result.stderr)[-100000:],encoding='utf-8')
    if result.returncode:raise ValueError('No se pudo descargar la referencia; consulta download.log. '+result.stderr[-800:])
    source=output/'reference.mp4'
    if not source.is_file() or not 0<source.stat().st_size<=500000000:raise ValueError('La descarga no produjo un MP4 de hasta 500 MB')
    return source


def detect_shots(ffmpeg,source,duration):
    result=subprocess.run([ffmpeg,'-nostdin','-hide_banner','-loglevel','info','-threads','1','-i',str(source),
        '-an','-vf',"scale=320:-2,select='gt(scene,0.3)',showinfo",'-filter_threads','1','-fps_mode','vfr','-f','null','-'],
        capture_output=True,text=True,timeout=600,check=True)
    cuts=sorted({float(value) for value in re.findall(r'pts_time:([0-9.eE+\-]+)',result.stderr)})
    boundaries=[0.0]+[cut for cut in cuts if 0<cut<duration]+[duration]
    return {'method':'ffmpeg_scene_threshold','threshold':0.3,'verified_by_human':False,
            'shots':[{'start_seconds':a,'end_seconds':b,'duration_seconds':b-a} for a,b in zip(boundaries,boundaries[1:])]}


def transcript_srt(segments):
    def stamp(seconds):
        milliseconds=round(seconds*1000);hours,remainder=divmod(milliseconds,3600000)
        minutes,remainder=divmod(remainder,60000);seconds,ms=divmod(remainder,1000)
        return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'
    blocks=[]
    for segment in segments:
        start=segment.get('start');end=segment.get('end');text=segment.get('text')
        if not isinstance(start,(int,float)) or not isinstance(end,(int,float)) or not math.isfinite(start) or not math.isfinite(end) or not 0<=start<end or not isinstance(text,str):raise ValueError('Segmento de transcripción inválido')
        text=' '.join(text.split())
        if text:blocks.append(f'{len(blocks)+1}\n{stamp(start)} --> {stamp(end)}\n{text}\n')
    return '\n'.join(blocks)


def read(project_id):
    path=studio.project_path(project_id)
    report=studio.read_json(path/'reference_analysis.json',{'status':'not_started'})
    with LOCK:
        if report.get('status') in ('running','queued','downloading') and project_id not in ACTIVE:
            return {**report,'status':'interrupted','message':'El proceso anterior terminó; los resultados parciales se conservan'}
    return report


def analyze(project_id,source,options,output):
    """CPU-only; missing models produce explicit gaps, never cloud fallbacks."""
    report={'status':'running','source':str(source),'started_at':studio.now(),
            'cost_usd':0,'device':'cpu','frames':[],'gaps':[],
            'scope':'sampled_frames_and_transcript','external_fact_check':'not_performed'}
    def save():
        studio.save_json(studio.project_path(project_id)/'reference_analysis.json',report)
        studio.save_json(output/'report.json',report)
    save()
    try:
        ffmpeg=executable('ffmpeg');ffprobe=executable('ffprobe')
        probe=subprocess.run([ffprobe,'-v','error','-show_format','-show_streams','-of','json',str(source)],capture_output=True,text=True,timeout=30,check=True)
        metadata=json.loads(probe.stdout)
        streams=metadata.get('streams',[])
        video=next((s for s in streams if s.get('codec_type')=='video'),None)
        duration=float(metadata.get('format',{}).get('duration',0))
        if not video or not math.isfinite(duration) or not 0<duration<=1800:raise ValueError('Se requiere video de hasta 30 minutos y duración verificable')
        report['media']={'duration_seconds':duration,'width':video.get('width'),'height':video.get('height'),'has_audio':any(s.get('codec_type')=='audio' for s in streams)}
        try:report['shot_detection']=detect_shots(ffmpeg,source,duration)
        except Exception as exc:report['gaps'].append('Cambios de plano: '+str(exc)[:500])
        save()
        from tools.tool_registry import ToolRegistry
        registry=ToolRegistry();registry.discover('tools.models')
        def model(name,inputs):
            from tools.base_tool import ToolStatus
            tool=registry.get('model_'+name.replace('-','_'))
            if tool is None or tool.get_status()!=ToolStatus.AVAILABLE:raise ValueError('Adaptador no preparado: '+name)
            result=tool.execute({**inputs,'device':'cpu','timeout':3600})
            if not result.success:raise ValueError(result.error)
            return result.data.get('result',{})
        for i in range(options['frames']):
            timestamp=(i+0.5)*duration/options['frames'];frame=output/f'frame-{i:02d}.jpg'
            subprocess.run([ffmpeg,'-nostdin','-v','error','-y','-ss',str(timestamp),'-i',str(source),'-frames:v','1','-vf','scale=640:-2','-threads','1',str(frame)],capture_output=True,text=True,timeout=60,check=True)
            relative=frame.relative_to(studio.project_path(project_id)).as_posix()
            record={'timestamp_seconds':timestamp,'url':f'/media/{project_id}/{relative}','visual_analysis':'not_requested'}
            if options['vision']:
                try:record['observation']=model(options['vision_model'],{'input_path':str(frame),'text':'Describe únicamente lo visible: objetos, textos legibles, encuadre y composición. No inventes movimiento, audio, especificaciones ni hechos externos.','max_new_tokens':512,'output_dir':str(output/f'vision-{i:02d}')});record['visual_analysis']='completed'
                except Exception as exc:record['visual_analysis']='unavailable';report['gaps'].append(str(exc)[:500])
            report['frames'].append(record);save()
        if options['transcribe'] and report['media']['has_audio']:
            try:
                audio=output/'audio.wav'
                subprocess.run([ffmpeg,'-nostdin','-v','error','-y','-i',str(source),'-vn','-ac','1','-ar','16000','-threads','1',str(audio)],capture_output=True,text=True,timeout=180,check=True)
                report['transcript']=model('faster-whisper',{'input_path':str(audio),'output_dir':str(output/'transcript')})
                if report['transcript'].get('segments'):
                    subtitles=output/'transcript.srt';subtitles.write_text(transcript_srt(report['transcript']['segments']),encoding='utf-8')
                    report['transcript_srt_url']=f'/media/{project_id}/'+subtitles.relative_to(studio.project_path(project_id)).as_posix()
            except Exception as exc:report['gaps'].append('Transcripción: '+str(exc)[:500])
        if options['summary']:
            try:
                evidence=json.dumps({'media':report['media'],'frames':report['frames'],'shot_detection':report.get('shot_detection'),'transcript':report.get('transcript')},ensure_ascii=False)
                report['analysis']=model('qwen3',{'text':'Analiza esta evidencia de un video. Separa observaciones de inferencias. Resume tema, estructura narrativa, gancho, recursos y posibles mejoras originales. Enumera afirmaciones que requieren investigación externa; no las presentes como verificadas. No propongas ocultar copias. No supongas cortes o movimientos entre fotogramas muestreados. Evidencia: '+evidence[:60000],'max_new_tokens':2048,'output_dir':str(output/'summary')})
            except Exception as exc:report['gaps'].append('Síntesis: '+str(exc)[:500])
        report['gaps']=list(dict.fromkeys(report['gaps']))
        report['status']='partial' if report['gaps'] else 'completed'
    except Exception as exc:report.update(status='failed',error=str(exc)[:1800])
    report['finished_at']=studio.now();save()
    return report


def prepare_request(project_id,data):
    if set(data)-{'frames','vision','transcribe','summary','vision_model','url'}:raise ValueError('Opciones desconocidas')
    data=dict(data);url=data.pop('url',None)
    if url is not None:url=youtube_url(url)
    options={'frames':4,'vision':True,'transcribe':True,'summary':True,'vision_model':'smolvlm',**data}
    if type(options['frames']) is not int or not 1<=options['frames']<=12:raise ValueError('Usa entre 1 y 12 fotogramas')
    if any(type(options[k]) is not bool for k in ('vision','transcribe','summary')):raise ValueError('Opciones inválidas')
    if options['vision_model'] not in ('smolvlm','qwen-vl'):raise ValueError('Modelo de visión no permitido')
    path=studio.project_path(project_id);source=selected_source(project_id)
    # Reference analysis does not deliver finals, so check only its working root.
    if not path.is_dir():raise ValueError('El disco de trabajo no está disponible')
    if shutil.disk_usage(path).free==0:raise ValueError('El disco de trabajo no tiene espacio libre')
    if not url and not source.is_file():raise ValueError('Carga el video de referencia o indica su enlace de YouTube')
    if url:
        for name in ('ffmpeg','ffprobe','yt-dlp','deno'):executable(name)
    return path,source,url,options


def execute_reference(project_id,path,source,url,options,output):
    try:
        selected=source
        if url:
            studio.save_json(path/'reference_analysis.json',{'status':'downloading','source_url':url,'device':'cpu','cost_usd':0})
            selected=download_reference(project_id,url,output)
            studio.save_json(output/'source.json',{'url':url,'downloaded_at':studio.now()})
            studio.save_json(path/'reference_source.json',{'path':selected.relative_to(path).as_posix(),'url':url})
        return analyze(project_id,selected,options,output)
    except Exception as exc:
        report={'status':'failed','error':str(exc)[:1800],'source_url':url,'cost_usd':0}
        studio.save_json(path/'reference_analysis.json',report);studio.save_json(output/'report.json',report)
        return report


def start(project_id,data):
    path,source,url,options=prepare_request(project_id,data)
    from lib import production_agent
    with production_agent.ACTIVE_LOCK,LOCK:
        if ACTIVE or production_agent.ACTIVE:raise ValueError('Hay una tarea local activa; espera antes de iniciar el análisis')
        output=path/'reference_analysis'/('run-'+uuid.uuid4().hex[:12]);output.mkdir(parents=True)
        ACTIVE.add(project_id)
        studio.save_json(path/'reference_analysis.json',{'status':'queued','options':options})
    def worker():
        try:execute_reference(project_id,path,source,url,options,output)
        finally:
            with LOCK:ACTIVE.discard(project_id)
    threading.Thread(target=worker,daemon=True).start()
    return {'started':True,'device':'cpu','cost_usd':0}


def run_for_producer(project_id,data,cancel):
    """Synchronous action of the sole registered producer, not a second worker."""
    if 'url' in data:raise ValueError('Usa la referencia elegida del proyecto, no una URL nueva')
    from lib import production_agent
    path=studio.project_path(project_id);source=selected_source(project_id)
    options=dict(data)
    if not source.is_file():
        request=studio.read_json(path/'production_request.json')
        try:options['url']=youtube_url(request.get('reference',''))
        except ValueError:raise ValueError('Elige una publicación de referencia o carga su video; un canal no identifica un video concreto') from None
    path,source,url,options=prepare_request(project_id,options)
    with production_agent.ACTIVE_LOCK,LOCK:
        owner=production_agent.ACTIVE.get(project_id)
        if not owner or owner[1] is not cancel or len(production_agent.ACTIVE)!=1:raise ValueError('El análisis requiere el productor activo de este proyecto')
        if ACTIVE:raise ValueError('Ya hay un análisis de referencia activo')
        if cancel.is_set():raise ValueError('El productor recibió una solicitud de parada')
        output=path/'reference_analysis'/('run-'+uuid.uuid4().hex[:12]);output.mkdir(parents=True)
        ACTIVE.add(project_id)
        studio.save_json(path/'reference_analysis.json',{'status':'queued','owner':'producer','options':options})
    try:
        if cancel.is_set():raise ValueError('Detenido antes de analizar la referencia')
        return execute_reference(project_id,path,source,url,options,output)
    finally:
        with LOCK:ACTIVE.discard(project_id)
