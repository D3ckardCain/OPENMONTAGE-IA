"""Render an explicitly requested silent review copy from approved scene takes."""
import hashlib
import json
import math
import subprocess
import threading
import uuid
from pathlib import Path

from lib import production_studio as studio
from lib import scene_batch,scene_edit
from lib.media_executables import require_media


def state(project_id):
    project=studio.project_path(project_id)
    return studio.read_json(project/'artifacts/scene_edit_preview.json',{'status':'not_started'})


def start(project_id,fit_policy):
    from lib import production_agent as agent,reference_analysis
    if fit_policy not in ('exact','trim_or_hold'):raise ValueError('Política de duración desconocida')
    project=studio.project_path(project_id)
    with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
        if agent.ACTIVE or reference_analysis.ACTIVE:raise ValueError('Hay una tarea local activa')
        check=scene_edit.readiness(project_id,fit_policy)
        if not check['ready']:raise ValueError('Montaje pendiente: '+ '; '.join(check['problems']+[s['scene_id']+': '+', '.join(s['problems']) for s in check['scenes'] if s['problems']])[:1000])
        manifest=scene_batch.read(project_id)
        if manifest['duration_seconds']>1800:raise ValueError('La vista previa admite hasta 30 minutos')
        # Freeze the verified source selection; the worker checks it again before rendering.
        choices=[{'scene_id':s['scene_id'],'path':next(t['path'] for t in s['takes'] if t['sha256']==s['approved_take_id']),
                  'sha256':s['approved_take_id'],'seconds':s['end_seconds']-s['start_seconds']} for s in manifest['scenes']]
        attempt=uuid.uuid4().hex
        record={'status':'running','attempt':attempt,'fit_policy':fit_policy,'started_at':studio.now(),
                'scene_plan_sha256':manifest['scene_plan_sha256'],'choices':choices,'output':None}
        studio.save_json(project/'artifacts/scene_edit_preview.json',record)
        token=threading.Event()
        thread=threading.Thread(target=_worker,args=(project_id,record,token),daemon=True,name='scene-edit-'+project_id)
        agent.ACTIVE[project_id]=(thread,token)
        thread.start()
    return {'started':True,'attempt':attempt}


def _worker(project_id,record,token):
    from lib import production_agent as agent
    project=studio.project_path(project_id)
    work=project/'assets/video/scene-edits'/record['attempt']
    output=None
    try:
        check=scene_edit.readiness(project_id,record['fit_policy'])
        if not check['ready']:raise ValueError('Cambió una toma antes de empezar el montaje')
        ffmpeg=require_media('ffmpeg')
        manifest=scene_batch.read(project_id)
        width,height=(720,1280) if manifest['aspect_ratio']=='9:16' else (1280,720)
        work.mkdir(parents=True,exist_ok=False)
        segments=[]
        for index,choice in enumerate(record['choices']):
            verified=scene_batch._media(project,choice['path'],'video')
            if verified['sha256']!=choice['sha256']:raise ValueError('Cambió la toma de '+choice['scene_id'])
            seconds=choice['seconds'];frames=round(seconds*24)
            if frames<1 or not math.isfinite(seconds):raise ValueError('Duración inválida')
            dest=work/f'{index:04d}.mp4'
            filters=f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24'
            filters+=f',tpad=stop_mode=clone:stop_duration={seconds:.3f}'
            filters+=f',trim=duration={seconds:.3f},setpts=PTS-STARTPTS'
            cmd=[ffmpeg,'-nostdin','-v','error','-xerror','-y','-i',str(project/choice['path']),'-an','-vf',filters,
                 '-frames:v',str(frames),'-c:v','libx264','-pix_fmt','yuv420p','-r','24',str(dest)]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=max(120,math.ceil(seconds*8)))
            if result.returncode or not dest.is_file() or not dest.stat().st_size:
                raise ValueError('Error en escena '+choice['scene_id']+': '+result.stderr[-500:])
            segments.append(dest)
            if scene_batch._media(project,choice['path'],'video')['sha256']!=choice['sha256']:
                raise ValueError('La toma cambió durante el montaje: '+choice['scene_id'])
        listing=work/'clips.txt'
        listing.write_text(''.join("file '"+str(path.resolve()).replace('\\','/').replace("'","'\\''")+"'\n" for path in segments),encoding='utf-8')
        output=project/'renders'/('scene-preview-'+record['attempt']+'.mp4')
        output.parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run([ffmpeg,'-nostdin','-v','error','-xerror','-y','-f','concat','-safe','0','-i',str(listing),
                               '-c','copy','-movflags','+faststart',str(output)],capture_output=True,text=True,timeout=600)
        if result.returncode or not output.is_file() or not output.stat().st_size:
            raise ValueError('Error al unir las escenas: '+result.stderr[-500:])
        probe=subprocess.run([require_media('ffprobe'),'-v','error','-show_entries','stream=codec_type,width,height:format=duration',
                              '-of','json',str(output)],capture_output=True,text=True,timeout=30)
        if probe.returncode:raise ValueError('No se pudo verificar el montaje')
        metadata=json.loads(probe.stdout);streams=[s for s in metadata.get('streams',[]) if s.get('codec_type')=='video']
        duration=float(metadata.get('format',{}).get('duration',0))
        expected_duration=sum(choice['seconds'] for choice in record['choices'])
        if (not streams or streams[0].get('width')!=width or streams[0].get('height')!=height or
                not math.isfinite(duration) or abs(duration-expected_duration)>max(.5,expected_duration*.01)):
            raise ValueError('El montaje no coincide con la duración o el formato esperado')
        current=scene_batch.read(project_id)
        selected_now=[{'scene_id':s['scene_id'],'path':next((t['path'] for t in s['takes'] if t['sha256']==s['approved_take_id']),None),
                       'sha256':s['approved_take_id'],'seconds':s['end_seconds']-s['start_seconds']} for s in current['scenes']]
        if selected_now!=record['choices'] or current['scene_plan_sha256']!=record['scene_plan_sha256'] or not scene_edit.readiness(project_id,record['fit_policy'])['ready']:
            raise ValueError('El plan o las tomas aprobadas cambiaron durante el montaje')
        digest=hashlib.sha256()
        with output.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
        record.update(status='completed',completed_at=studio.now(),output={'path':output.relative_to(project).as_posix(),
                      'url':'/media/'+project_id+'/'+output.relative_to(project).as_posix(),
                      'sha256':digest.hexdigest(),'bytes':output.stat().st_size,
                      'duration_seconds':duration},audio_included=False)
    except Exception as exc:
        if output is not None:output.unlink(missing_ok=True)
        record.update(status='failed',completed_at=studio.now(),error=str(exc)[:1800])
    finally:
        with studio.LOCK:
            if state(project_id).get('attempt')==record['attempt']:
                studio.save_json(project/'artifacts/scene_edit_preview.json',record)
        with agent.ACTIVE_LOCK:
            if agent.ACTIVE.get(project_id,(None,None))[1] is token:agent.ACTIVE.pop(project_id,None)
