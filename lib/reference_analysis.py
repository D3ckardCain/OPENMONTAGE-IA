"""Project reference analysis using local executables and offline model adapters."""
import json
import math
import shutil
import subprocess
import threading
import uuid
from pathlib import Path
from lib import production_studio as studio

LOCK=threading.RLock()
ACTIVE=set()


def executable(name):
    configured=studio.settings().get(name+'_path','')
    value=configured or shutil.which(name)
    if not value or not Path(value).is_file():raise ValueError('Configura la ruta de '+name+' en el Estudio')
    return str(value)


def read(project_id):
    path=studio.project_path(project_id)
    report=studio.read_json(path/'reference_analysis.json',{'status':'not_started'})
    with LOCK:
        if report.get('status') in ('running','queued') and project_id not in ACTIVE:
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
            except Exception as exc:report['gaps'].append('Transcripción: '+str(exc)[:500])
        if options['summary']:
            try:
                evidence=json.dumps({'media':report['media'],'frames':report['frames'],'transcript':report.get('transcript')},ensure_ascii=False)
                report['analysis']=model('qwen3',{'text':'Analiza esta evidencia de un video. Separa observaciones de inferencias. Resume tema, estructura narrativa, gancho, recursos y posibles mejoras originales. Enumera afirmaciones que requieren investigación externa; no las presentes como verificadas. No propongas ocultar copias. No supongas cortes o movimientos entre fotogramas muestreados. Evidencia: '+evidence[:60000],'max_new_tokens':2048,'output_dir':str(output/'summary')})
            except Exception as exc:report['gaps'].append('Síntesis: '+str(exc)[:500])
        report['gaps']=list(dict.fromkeys(report['gaps']))
        report['status']='partial' if report['gaps'] else 'completed'
    except Exception as exc:report.update(status='failed',error=str(exc)[:1800])
    report['finished_at']=studio.now();save()
    return report


def start(project_id,data):
    if set(data)-{'frames','vision','transcribe','summary','vision_model'}:raise ValueError('Opciones desconocidas')
    options={'frames':4,'vision':True,'transcribe':True,'summary':True,'vision_model':'smolvlm',**data}
    if type(options['frames']) is not int or not 1<=options['frames']<=12:raise ValueError('Usa entre 1 y 12 fotogramas')
    if any(type(options[k]) is not bool for k in ('vision','transcribe','summary')):raise ValueError('Opciones inválidas')
    if options['vision_model'] not in ('smolvlm','qwen-vl'):raise ValueError('Modelo de visión no permitido')
    path=studio.project_path(project_id);source=path/'reference_video.mp4'
    if not source.is_file():raise ValueError('Carga primero el video de referencia del proyecto')
    from lib import production_agent
    with production_agent.ACTIVE_LOCK,LOCK:
        if ACTIVE or production_agent.ACTIVE:raise ValueError('Hay una tarea local activa; espera antes de iniciar el análisis')
        output=path/'reference_analysis'/('run-'+uuid.uuid4().hex[:12]);output.mkdir(parents=True)
        ACTIVE.add(project_id)
        studio.save_json(path/'reference_analysis.json',{'status':'queued','options':options})
    def worker():
        try:analyze(project_id,source,options,output)
        finally:
            with LOCK:ACTIVE.discard(project_id)
    threading.Thread(target=worker,daemon=True).start()
    return {'started':True,'device':'cpu','cost_usd':0}
