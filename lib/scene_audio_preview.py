"""Mix explicit local narration and optional music into a scene review copy."""
import hashlib
import json
import math
import subprocess
import threading
import uuid
from pathlib import Path

from lib import production_studio as studio
from lib import scene_batch,scene_edit,scene_preview
from lib.media_executables import require_media


def _hash(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def _track(project,relative):
    if not isinstance(relative,str) or not 1<=len(relative)<=500 or '\\' in relative:
        raise ValueError('Indica una ruta relativa de audio dentro del proyecto')
    path=Path(relative)
    if path.is_absolute() or any(p in ('.','..') for p in path.parts) or path.suffix.lower() not in ('.wav','.mp3','.m4a','.flac','.ogg'):
        raise ValueError('Ruta o formato de audio no admitido')
    target=project.joinpath(*path.parts)
    target.resolve().relative_to(project.resolve())
    if any(project.joinpath(*path.parts[:n]).is_symlink() for n in range(1,len(path.parts)+1)):
        raise ValueError('No se admiten enlaces simbólicos')
    if not target.is_file() or not 0<target.stat().st_size<1_000_000_000:
        raise ValueError('Audio ausente, vacío o mayor de 1 GB')
    result=subprocess.run([require_media('ffprobe'),'-v','error','-show_entries','stream=codec_type:format=duration',
                           '-of','json',str(target)],capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError('Audio no reconocido por ffprobe')
    info=json.loads(result.stdout);duration=float(info.get('format',{}).get('duration',0))
    if not any(s.get('codec_type')=='audio' for s in info.get('streams',[])) or not math.isfinite(duration) or not 0<duration<=10800:
        raise ValueError('La pista de audio no tiene duración válida')
    return {'path':relative,'sha256':_hash(target),'bytes':target.stat().st_size,'duration_seconds':duration}


def state(project_id):
    return studio.read_json(studio.project_path(project_id)/'artifacts/scene_audio_preview.json',{'status':'not_started'})


def start(project_id,data):
    from lib import production_agent as agent,reference_analysis
    if not isinstance(data,dict) or set(data)!={'narration_path','music_path','narration_db','music_db'}:
        raise ValueError('Indica narración, música opcional y niveles de mezcla')
    voice_db,music_db=data['narration_db'],data['music_db']
    if (type(voice_db) not in (int,float) or type(music_db) not in (int,float) or
            not math.isfinite(voice_db) or not math.isfinite(music_db) or
            not -12<=voice_db<=12 or not -40<=music_db<=-6):
        raise ValueError('Niveles fuera de rango')
    project=studio.project_path(project_id)
    with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
        if agent.ACTIVE or reference_analysis.ACTIVE:raise ValueError('Hay una tarea local activa')
        preview=scene_preview.state(project_id)
        if preview.get('status')!='completed' or not preview.get('output'):
            raise ValueError('Crea primero un montaje de revisión completo')
        if not scene_edit.readiness(project_id,preview['fit_policy'])['ready']:
            raise ValueError('Cambió el plan o alguna toma aprobada')
        current=scene_batch.read(project_id)
        choices=[{'scene_id':s['scene_id'],'path':next((t['path'] for t in s['takes'] if t['sha256']==s['approved_take_id']),None),
                  'sha256':s['approved_take_id'],'seconds':s['end_seconds']-s['start_seconds']} for s in current['scenes']]
        if choices!=preview['choices'] or current['scene_plan_sha256']!=preview['scene_plan_sha256']:
            raise ValueError('El montaje corresponde a una selección anterior')
        video=project/preview['output']['path']
        video.resolve().relative_to(project.resolve())
        if video.is_symlink() or not video.is_file() or _hash(video)!=preview['output']['sha256']:
            raise ValueError('El montaje de revisión cambió en disco')
        narration=_track(project,data['narration_path'])
        if narration['duration_seconds']>preview['output']['duration_seconds']+.5:
            raise ValueError('La narración supera la duración del video; revisa tiempos antes de mezclar')
        music=_track(project,data['music_path']) if data['music_path'] else None
        attempt=uuid.uuid4().hex
        record={'status':'running','attempt':attempt,'started_at':studio.now(),'video':preview['output'],
                'video_attempt':preview['attempt'],'narration':narration,'music':music,
                'narration_db':voice_db,'music_db':music_db,'output':None}
        studio.save_json(project/'artifacts/scene_audio_preview.json',record)
        token=threading.Event()
        thread=threading.Thread(target=_worker,args=(project_id,record,token),daemon=True,name='scene-audio-'+project_id)
        agent.ACTIVE[project_id]=(thread,token)
        thread.start()
    return {'started':True,'attempt':attempt}


def _worker(project_id,record,token):
    from lib import production_agent as agent
    project=studio.project_path(project_id)
    output=None
    try:
        current=scene_preview.state(project_id)
        if current.get('attempt')!=record['video_attempt'] or current.get('output')!=record['video']:
            raise ValueError('Cambió el montaje de video')
        sources=[record['narration']]+([record['music']] if record['music'] else [])
        if _hash(project/record['video']['path'])!=record['video']['sha256'] or any(
                _track(project,item['path'])['sha256']!=item['sha256'] for item in sources):
            raise ValueError('Cambió un archivo de entrada')
        duration=record['video']['duration_seconds']
        cmd=[require_media('ffmpeg'),'-nostdin','-v','error','-xerror','-y','-i',str(project/record['video']['path']),
             '-i',str(project/record['narration']['path'])]
        if record['music']:cmd+=['-stream_loop','-1','-i',str(project/record['music']['path'])]
        voice=f'[1:a]volume={record["narration_db"]}dB,aresample=48000,apad,atrim=duration={duration:.3f},asetpts=PTS-STARTPTS[v]'
        if record['music']:
            music=f'[2:a]volume={record["music_db"]}dB,aresample=48000,atrim=duration={duration:.3f},asetpts=PTS-STARTPTS[m]'
            filters=voice+';'+music+';[v][m]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]'
        else:filters=voice+';[v]alimiter=limit=0.95[a]'
        output=project/'renders'/('scene-audio-preview-'+record['attempt']+'.mp4')
        cmd+=['-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k',
              '-t',f'{duration:.3f}','-movflags','+faststart',str(output)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=min(3600,max(120,math.ceil(duration*5))))
        if result.returncode or not output.is_file() or not output.stat().st_size:
            raise ValueError('Error al mezclar audio: '+result.stderr[-500:])
        probe=subprocess.run([require_media('ffprobe'),'-v','error','-show_entries','stream=codec_type:format=duration',
                              '-of','json',str(output)],capture_output=True,text=True,timeout=30)
        if probe.returncode:raise ValueError('No se pudo comprobar el resultado con audio')
        info=json.loads(probe.stdout);actual=float(info.get('format',{}).get('duration',0))
        kinds={stream.get('codec_type') for stream in info.get('streams',[])}
        if not {'video','audio'}<=kinds or not math.isfinite(actual) or abs(actual-duration)>max(.5,duration*.01):
            raise ValueError('El resultado no contiene audio y video con la duración prevista')
        if (scene_preview.state(project_id).get('attempt')!=record['video_attempt'] or
                _hash(project/record['video']['path'])!=record['video']['sha256'] or
                any(_track(project,item['path'])['sha256']!=item['sha256'] for item in sources)):
            raise ValueError('Cambió una fuente durante la mezcla')
        video_record=scene_preview.state(project_id)
        manifest=scene_batch.read(project_id)
        current_choices=[{'scene_id':s['scene_id'],'path':next((t['path'] for t in s['takes'] if t['sha256']==s['approved_take_id']),None),
                          'sha256':s['approved_take_id'],'seconds':s['end_seconds']-s['start_seconds']} for s in manifest['scenes']]
        if (manifest['scene_plan_sha256']!=video_record['scene_plan_sha256'] or current_choices!=video_record['choices'] or
                not scene_edit.readiness(project_id,video_record['fit_policy'])['ready']):
            raise ValueError('Cambió una escena aprobada durante la mezcla')
        relative=output.relative_to(project).as_posix()
        record.update(status='completed',completed_at=studio.now(),output={'path':relative,
                      'url':'/media/'+project_id+'/'+relative,'sha256':_hash(output),
                      'bytes':output.stat().st_size,'duration_seconds':actual})
    except Exception as exc:
        if output is not None:output.unlink(missing_ok=True)
        record.update(status='failed',completed_at=studio.now(),error=str(exc)[:1800])
    finally:
        with studio.LOCK:
            if state(project_id).get('attempt')==record['attempt']:
                studio.save_json(project/'artifacts/scene_audio_preview.json',record)
        with agent.ACTIVE_LOCK:
            if agent.ACTIVE.get(project_id,(None,None))[1] is token:agent.ACTIVE.pop(project_id,None)
