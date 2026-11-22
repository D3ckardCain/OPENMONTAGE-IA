"""Validate an SRT and mux an editable subtitle track into a review MP4."""
import json
import math
import re
import subprocess
import threading
import uuid
from pathlib import Path

from lib import production_studio as studio
from lib import scene_audio_preview as audio
from lib import scene_batch,scene_edit,scene_preview
from lib.media_executables import require_media

TIMECODE=re.compile(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})$')


def _seconds(values):
    hour,minute,second,millis=map(int,values)
    if minute>=60 or second>=60:return -1
    return hour*3600+minute*60+second+millis/1000


def parse_srt(content,duration):
    if not isinstance(content,str) or not 0<len(content.encode('utf-8'))<=500_000:
        raise ValueError('SRT vacío o superior a 500 KB')
    blocks=re.split(r'\n\s*\n',content.lstrip('\ufeff').replace('\r\n','\n').strip())
    if len(blocks)>10000:raise ValueError('Demasiados subtítulos')
    cues=[];previous=0
    for index,block in enumerate(blocks,1):
        lines=block.split('\n')
        if len(lines)<3 or lines[0].strip()!=str(index):raise ValueError('Numeración SRT inválida en '+str(index))
        match=TIMECODE.fullmatch(lines[1].strip())
        if not match:raise ValueError('Tiempo SRT inválido en '+str(index))
        start=_seconds(match.groups()[:4]);end=_seconds(match.groups()[4:])
        text='\n'.join(lines[2:]).strip()
        if start<previous or end<=start or end>duration+.1 or not text or len(text)>400 or '\x00' in text:
            raise ValueError('Texto o intervalo SRT inválido en '+str(index))
        cues.append({'start_seconds':start,'end_seconds':end,'text':text})
        previous=end
    return cues


def _file(project,relative):
    if not isinstance(relative,str) or not 1<=len(relative)<=500 or '\\' in relative:
        raise ValueError('Indica una ruta relativa para el SRT')
    path=Path(relative)
    if path.is_absolute() or path.suffix.lower()!='.srt' or any(p in ('.','..') for p in path.parts):
        raise ValueError('Ruta SRT inválida')
    target=project.joinpath(*path.parts)
    target.resolve().relative_to(project.resolve())
    if any(project.joinpath(*path.parts[:n]).is_symlink() for n in range(1,len(path.parts)+1)):
        raise ValueError('No se admiten enlaces simbólicos')
    if not target.is_file() or not 0<target.stat().st_size<=500_000:raise ValueError('SRT ausente o demasiado grande')
    return target


def state(project_id):
    return studio.read_json(studio.project_path(project_id)/'artifacts/scene_subtitles.json',{'status':'not_started'})


def _current(project_id,source):
    project=studio.project_path(project_id)
    video=scene_preview.state(project_id)
    manifest=scene_batch.read(project_id)
    if (video.get('status')!='completed' or video.get('attempt')!=source.get('video_attempt') or
            video.get('output')!=source.get('video') or not manifest.get('scenes') or
            manifest['scene_plan_sha256']!=video['scene_plan_sha256']):
        return False
    choices=[{'scene_id':s['scene_id'],'path':next((t['path'] for t in s['takes'] if t['sha256']==s['approved_take_id']),None),
              'sha256':s['approved_take_id'],'seconds':s['end_seconds']-s['start_seconds']} for s in manifest['scenes']]
    if choices!=video['choices'] or not scene_edit.readiness(project_id,video['fit_policy'])['ready']:
        return False
    sources=[source['narration']]+([source['music']] if source.get('music') else [])
    return (audio._hash(project/video['output']['path'])==video['output']['sha256'] and
            all(audio._track(project,item['path'])['sha256']==item['sha256'] for item in sources))


def inspect(project_id,relative):
    project=studio.project_path(project_id)
    source=audio.state(project_id)
    if source.get('status')!='completed' or not source.get('output'):
        raise ValueError('Crea primero el montaje de revisión con audio')
    if not _current(project_id,source):raise ValueError('El montaje con audio corresponde a escenas o pistas anteriores')
    target=_file(project,relative)
    cues=parse_srt(target.read_text(encoding='utf-8-sig'),source['output']['duration_seconds'])
    return {'path':relative,'sha256':audio._hash(target),'cue_count':len(cues),'cues':cues[:100],
            'partial':len(cues)>100,'video_duration_seconds':source['output']['duration_seconds']}


def start(project_id,data):
    from lib import production_agent as agent,reference_analysis
    if not isinstance(data,dict) or set(data)!={'srt_path','language'} or data['language'] not in ('spa','eng'):
        raise ValueError('Indica ruta SRT e idioma spa o eng')
    project=studio.project_path(project_id)
    with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
        if agent.ACTIVE or reference_analysis.ACTIVE:raise ValueError('Hay una tarea local activa')
        report=inspect(project_id,data['srt_path'])
        source=audio.state(project_id)
        video=project/source['output']['path']
        video.resolve().relative_to(project.resolve())
        if video.is_symlink() or not video.is_file() or audio._hash(video)!=source['output']['sha256']:
            raise ValueError('Cambió el montaje con audio')
        attempt=uuid.uuid4().hex
        record={'status':'running','attempt':attempt,'started_at':studio.now(),'source':source['output'],
                'source_attempt':source['attempt'],'srt_path':data['srt_path'],'srt_sha256':report['sha256'],
                'cue_count':report['cue_count'],'language':data['language'],'output':None}
        studio.save_json(project/'artifacts/scene_subtitles.json',record)
        token=threading.Event()
        thread=threading.Thread(target=_worker,args=(project_id,record,token),daemon=True,name='scene-subs-'+project_id)
        agent.ACTIVE[project_id]=(thread,token)
        thread.start()
    return {'started':True,'attempt':attempt,'cue_count':report['cue_count']}


def _worker(project_id,record,token):
    from lib import production_agent as agent
    project=studio.project_path(project_id);output=None
    try:
        source=audio.state(project_id)
        if source.get('attempt')!=record['source_attempt'] or source.get('output')!=record['source'] or not _current(project_id,source):
            raise ValueError('Cambió el montaje de audio')
        video=project/record['source']['path'];srt=_file(project,record['srt_path'])
        if audio._hash(video)!=record['source']['sha256'] or audio._hash(srt)!=record['srt_sha256']:
            raise ValueError('Cambió un archivo de entrada')
        output=project/'renders'/('scene-subs-preview-'+record['attempt']+'.mp4')
        result=subprocess.run([require_media('ffmpeg'),'-nostdin','-v','error','-xerror','-y',
                '-i',str(video),'-i',str(srt),'-map','0:v:0','-map','0:a:0','-map','1:s:0',
                '-c:v','copy','-c:a','copy','-c:s','mov_text','-metadata:s:s:0','language='+record['language'],
                '-movflags','+faststart',str(output)],capture_output=True,text=True,timeout=900)
        if result.returncode or not output.is_file() or not output.stat().st_size:
            raise ValueError('Error al incorporar subtítulos: '+result.stderr[-500:])
        probe=subprocess.run([require_media('ffprobe'),'-v','error','-show_entries','stream=codec_type:format=duration',
                              '-of','json',str(output)],capture_output=True,text=True,timeout=30)
        if probe.returncode:raise ValueError('No se pudo comprobar el video con subtítulos')
        info=json.loads(probe.stdout);duration=float(info.get('format',{}).get('duration',0))
        kinds={stream.get('codec_type') for stream in info.get('streams',[])}
        if not {'video','audio','subtitle'}<=kinds or not math.isfinite(duration) or abs(duration-record['source']['duration_seconds'])>max(.5,duration*.01):
            raise ValueError('Falta video, audio o subtítulos, o la duración cambió')
        if (audio.state(project_id).get('attempt')!=record['source_attempt'] or not _current(project_id,audio.state(project_id)) or
                audio._hash(video)!=record['source']['sha256'] or audio._hash(srt)!=record['srt_sha256']):
            raise ValueError('Cambió una fuente durante el montaje')
        relative=output.relative_to(project).as_posix()
        record.update(status='completed',completed_at=studio.now(),output={'path':relative,
                     'url':'/media/'+project_id+'/'+relative,'sha256':audio._hash(output),
                     'bytes':output.stat().st_size,'duration_seconds':duration},
                     srt_url='/media/'+project_id+'/'+record['srt_path'])
    except Exception as exc:
        if output is not None:output.unlink(missing_ok=True)
        record.update(status='failed',completed_at=studio.now(),error=str(exc)[:1800])
    finally:
        with studio.LOCK:
            if state(project_id).get('attempt')==record['attempt']:
                studio.save_json(project/'artifacts/scene_subtitles.json',record)
        with agent.ACTIVE_LOCK:
            if agent.ACTIVE.get(project_id,(None,None))[1] is token:agent.ACTIVE.pop(project_id,None)
