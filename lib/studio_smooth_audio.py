"""Bounded streamed audio resampling against the canonical inverse clock."""
from pathlib import Path
from lib import studio_smooth_clock as clock

RATE=48000


def tracks(edl):
    return [(i,c) for i,c in enumerate(edl['cuts']+edl['audio_tracks']) if c.get('time_warp') and edl['sources'][c['source_id']].get('audio')]


def resample_file(source,target,w,seconds,control):
    control.check()
    import numpy as np
    source=Path(source);target=Path(target);count=source.stat().st_size//8
    if not count or source.stat().st_size%8:raise ValueError('PCM de origen incompleto o vacío')
    audio=np.memmap(source,dtype='<f4',mode='r',shape=(count,2))
    output_start=clock.forward(w['map'],w['old_start_seconds']);total=round(seconds*RATE)
    try:
        with target.open('xb') as stream:
            for begin in range(0,total,8192):
                control.check();n=min(8192,total-begin)
                times=output_start+(begin+np.arange(n,dtype='float64'))/RATE
                positions=np.clip((clock.inverse_array(w['map'],times)-w['old_start_seconds'])*RATE,0,count-1)
                left=positions.astype('int64');right=np.minimum(left+1,count-1);fraction=(positions-left)[:,None]
                values=np.asarray(audio[left],dtype='float64')*(1-fraction)+np.asarray(audio[right],dtype='float64')*fraction
                if not np.isfinite(values).all():raise ValueError('Remuestreo produjo muestras no finitas')
                stream.write(values.astype('<f4').tobytes())
        control.check()
    finally:audio._mmap.close()
    return total


def prepare(pid,edl,work,control):
    from lib import studio_editor as edit
    from lib.media_executables import require_media
    from lib.studio_render_process import execute
    from tools.video.video_trimmer import VideoTrimmer
    receipts=[]
    for i,c in tracks(edl):
        control.check();w=c['time_warp'];raw=work/f'decode-warp-{i}.f32';target=work/f'audio-warp-{i}.f32'
        old_seconds=(c['out_seconds']-c['in_seconds'])/w['old_speed']
        if old_seconds>60:raise ValueError('Audio continuo superior al presupuesto60s')
        m=w['map'];root_rate=(m['points'][-1]['source_seconds']-m['points'][0]['source_seconds'])/m['old_duration_seconds']
        max_ratio=max(p['speed'] for p in m['points'])/clock.scale(m)/root_rate
        cutoff=min(22000,22000/max(1,max_ratio))
        af=(f"atrim=start={c['in_seconds']}:end={c['out_seconds']},asetpts=PTS-STARTPTS,"
            +VideoTrimmer._build_atempo_chain(w['old_speed'])+f',aresample={RATE},aformat=channel_layouts=stereo,lowpass=f={cutoff:.12g},apad,atrim=duration={old_seconds}')
        command=[str(require_media('ffmpeg')),'-nostdin','-v','error','-xerror','-n',*edit.INPUT_OPTIONS,'-i',str(edit.source(pid,c['source_id'])),
                 '-map','0:a:0','-vn','-sn','-af',af,'-ar',str(RATE),'-ac','2','-f','f32le',str(raw)]
        result=execute(command,work,control,timeout=60)
        if result.returncode:raise ValueError('No se pudo preparar audio continuo: '+result.stderr.decode('utf-8','replace')[-500:])
        samples=resample_file(raw,target,w,clock.item_seconds(c),control)
        receipts.append({'clip_id':c['id'],'source_id':c['source_id'],'source_sha256':edl['sources'][c['source_id']]['sha256'],
          'mode':'continuous_resample_pitch_changes','samples':samples,'rate':RATE,'channels':2,'lowpass_hz':cutoff,
          'precision':'Analytic inverse clock, float64 positions, linear PCM interpolation; pitch changes and quality limits explicit'})
    return receipts


def cleanup(edl,work):
    for i,_ in tracks(edl):
        for name in (f'decode-warp-{i}.f32',f'audio-warp-{i}.f32'):
            path=work/name;path.resolve().relative_to(work.resolve())
            if path.is_file() and not path.is_symlink():path.unlink()
