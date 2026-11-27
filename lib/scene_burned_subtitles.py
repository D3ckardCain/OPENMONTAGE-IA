"""Render a review MP4 with visible captions from a verified SRT."""
import json
import math
import subprocess
import tempfile
import threading
import uuid
from pathlib import Path

from lib import production_studio as studio
from lib import scene_audio_preview as audio, scene_subtitles as subs
from lib.media_executables import require_media


def state(project_id):
    return studio.read_json(studio.project_path(project_id)/'artifacts/scene_burned_subtitles.json',{'status':'not_started'})


def _source(project_id):
    project=studio.project_path(project_id)
    record=subs.state(project_id)
    source=audio.state(project_id)
    if record.get('status')!='completed' or not record.get('output') or source.get('status')!='completed':
        raise ValueError('Crea primero el video con pista de subtítulos editable')
    if record.get('source_attempt')!=source.get('attempt') or record.get('source')!=source.get('output') or not subs._current(project_id,source):
        raise ValueError('El montaje o las escenas cambiaron; revisa los subtítulos otra vez')
    video=project/record['output']['path']
    srt=subs._file(project,record['srt_path'])
    if video.is_symlink() or not video.is_file() or audio._hash(video)!=record['output']['sha256'] or audio._hash(srt)!=record['srt_sha256']:
        raise ValueError('Cambió el MP4 o el SRT aprobado')
    cues=subs.parse_srt(srt.read_text(encoding='utf-8-sig'),record['output']['duration_seconds'])
    return record,cues


def _timestamp(seconds):
    centis=round(seconds*100)
    return f'{centis//360000}:{centis//6000%60:02d}:{centis//100%60:02d}.{centis%100:02d}'


def _ass(cues,width,height,subtitle_style=None,safe_area=None):
    vertical=height>width
    fontsize=max(24,round(width*(.052 if vertical else .038)))
    margin=max(24,round(height*(.12 if vertical else .09)))
    alignment=2
    if subtitle_style:
        fontsize=round(subtitle_style['size']*height/1080)
        alignment={'bottom':2,'center':5,'top':8}[subtitle_style['position']]
    style=f'Style: Main,Arial,{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,{max(24,width//18)},{max(24,width//18)},{margin},1'
    if subtitle_style:
        parts=style.split(',');parts[2]=str(fontsize);parts[18]=str(alignment);style=','.join(parts)
    anchor=''
    if safe_area is not None:
        parts=style.split(',');parts[19]=str(round(width*safe_area['left']));parts[20]=str(round(width*safe_area['right']));style=','.join(parts)
        x=width*(safe_area['left']+(1-safe_area['left']-safe_area['right'])/2)
        y=height*(safe_area['top'] if alignment==8 else 1-safe_area['bottom'] if alignment==2 else safe_area['top']+(1-safe_area['top']-safe_area['bottom'])/2)
        anchor=f'{{\\pos({x:.3f},{y:.3f})\\an{alignment}}}'
    header=('[Script Info]\nScriptType: v4.00+\nWrapStyle: 0\nScaledBorderAndShadow: yes\n'
            f'PlayResX: {width}\nPlayResY: {height}\n\n[V4+ Styles]\n'
            'Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n'
            +style+'\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n')
    lines=[]
    for cue in cues:
        safe=cue['text'].replace('\\','\\\\').replace('{','\\{').replace('}','\\}').replace('\r','').replace('\n','\\N')
        lines.append(f"Dialogue: 0,{_timestamp(cue['start_seconds'])},{_timestamp(cue['end_seconds'])},Main,,0,0,0,,{anchor}{safe}")
    return header+'\n'.join(lines)+'\n'


def start(project_id):
    from lib import production_agent as agent, reference_analysis
    project=studio.project_path(project_id)
    with agent.ACTIVE_LOCK,reference_analysis.LOCK,studio.LOCK:
        if agent.ACTIVE or reference_analysis.ACTIVE:raise ValueError('Hay una tarea local activa')
        source,cues=_source(project_id)
        record={'status':'running','attempt':uuid.uuid4().hex,'started_at':studio.now(),
                'source_attempt':source['attempt'],'source_sha256':source['output']['sha256'],
                'srt_sha256':source['srt_sha256'],'cue_count':len(cues),'output':None}
        studio.save_json(project/'artifacts/scene_burned_subtitles.json',record)
        token=threading.Event()
        thread=threading.Thread(target=_worker,args=(project_id,record,token),daemon=True,name='scene-burn-'+project_id)
        agent.ACTIVE[project_id]=(thread,token)
        thread.start()
    return {'started':True,'attempt':record['attempt'],'cue_count':len(cues)}


def _worker(project_id,record,token):
    from lib import production_agent as agent
    project=studio.project_path(project_id);output=None
    try:
        source,cues=_source(project_id)
        if source['attempt']!=record['source_attempt'] or source['output']['sha256']!=record['source_sha256'] or source['srt_sha256']!=record['srt_sha256']:
            raise ValueError('Cambió la fuente aprobada')
        video=project/source['output']['path']
        probe=subprocess.run([require_media('ffprobe'),'-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','json',str(video)],capture_output=True,text=True,timeout=30)
        if probe.returncode:raise ValueError('No se pudo inspeccionar el video de origen')
        streams=json.loads(probe.stdout).get('streams',[])
        if not streams:raise ValueError('Video de origen sin imagen')
        width,height=streams[0]['width'],streams[0]['height']
        if width<128 or height<128:raise ValueError('Resolución insuficiente para subtítulos visibles')
        output=project/'renders'/('scene-burned-preview-'+record['attempt']+'.mp4')
        with tempfile.TemporaryDirectory(prefix='scene-captions-') as tmp:
            Path(tmp,'captions.ass').write_text(_ass(cues,width,height),encoding='utf-8')
            result=subprocess.run([require_media('ffmpeg'),'-nostdin','-v','error','-xerror','-y',
                '-i',str(video),'-map','0:v:0','-map','0:a:0','-vf','ass=captions.ass',
                '-c:v','libx264','-crf','20','-preset','medium','-c:a','copy','-movflags','+faststart',str(output)],
                cwd=tmp,capture_output=True,text=True,timeout=3600)
        if result.returncode or not output.is_file() or not output.stat().st_size:
            raise ValueError('Error al dibujar subtítulos: '+result.stderr[-500:])
        check=subprocess.run([require_media('ffprobe'),'-v','error','-show_entries','stream=codec_type:format=duration','-of','json',str(output)],capture_output=True,text=True,timeout=30)
        if check.returncode:raise ValueError('No se pudo comprobar el video exportado')
        info=json.loads(check.stdout);duration=float(info.get('format',{}).get('duration',0))
        kinds={s.get('codec_type') for s in info.get('streams',[])}
        if not {'video','audio'}<=kinds or not math.isfinite(duration) or abs(duration-source['output']['duration_seconds'])>max(.5,duration*.01):
            raise ValueError('Video, audio o duración inválidos en la copia visible')
        fresh,_=_source(project_id)
        if fresh['attempt']!=record['source_attempt'] or fresh['output']['sha256']!=record['source_sha256'] or fresh['srt_sha256']!=record['srt_sha256']:
            raise ValueError('Cambió la fuente durante la exportación')
        relative=output.relative_to(project).as_posix()
        record.update(status='completed',completed_at=studio.now(),resolution=[width,height],
                      output={'path':relative,'url':'/media/'+project_id+'/'+relative,'sha256':audio._hash(output),
                              'bytes':output.stat().st_size,'duration_seconds':duration})
    except Exception as exc:
        if output is not None:output.unlink(missing_ok=True)
        record.update(status='failed',completed_at=studio.now(),error=str(exc)[:1800])
    finally:
        with studio.LOCK:
            if state(project_id).get('attempt')==record['attempt']:
                studio.save_json(project/'artifacts/scene_burned_subtitles.json',record)
        with agent.ACTIVE_LOCK:
            if agent.ACTIVE.get(project_id,(None,None))[1] is token:agent.ACTIVE.pop(project_id,None)
