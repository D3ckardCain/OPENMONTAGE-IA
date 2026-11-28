"""Opt-in new short synthetic PCM checks, no files/voice/video/models/network."""
import array
from copy import deepcopy
import json
import math
import subprocess
from lib.media_executables import require_media
from lib.studio_audio_processing import DEFAULT,filter_suffix


def run(executable,expression,settings=None):
    suffix=filter_suffix({'audio_processing':settings})
    result=subprocess.run([executable,'-v','error','-f','lavfi','-i',
        'aevalsrc='+expression+':s=48000:d=0.5','-af',
        'aformat=sample_fmts=fltp:channel_layouts=stereo'+suffix,
        '-f','f32le','-c:a','pcm_f32le','pipe:1'],capture_output=True,check=True,timeout=10)
    samples=array.array('f');samples.frombytes(result.stdout)
    assert len(samples)==48000
    return samples[::2]


def amplitude(samples,frequency):
    data=samples[4800:];start=4800
    cosine=sum(x*math.cos(2*math.pi*frequency*(i+start)/48000) for i,x in enumerate(data))
    sine=sum(x*math.sin(2*math.pi*frequency*(i+start)/48000) for i,x in enumerate(data))
    return 2*math.hypot(cosine,sine)/len(data)


def main():
    executable=require_media('ffmpeg');expression='0.05*sin(2*PI*120*t)+0.05*sin(2*PI*6000*t)'
    base=run(executable,expression);eq=deepcopy(DEFAULT);eq['eq'].update(bass_db=6,treble_db=-6)
    changed=run(executable,expression,eq)
    gains={str(f):20*math.log10(amplitude(changed,f)/amplitude(base,f)) for f in (120,6000)}
    assert abs(gains['120']-6)<.5 and abs(gains['6000']+6)<.5,gains
    plain=run(executable,'0.7*sin(2*PI*440*t)');compressor=deepcopy(DEFAULT)
    compressor['compressor'].update(enabled=True,threshold_db=-18,ratio=4,attack_ms=5,release_ms=100)
    compressed=run(executable,'0.7*sin(2*PI*440*t)',compressor)
    rms=lambda values:math.sqrt(sum(x*x for x in values[9600:])/len(values[9600:]))
    ratio=rms(compressed)/rms(plain);assert 0<ratio<.65,ratio
    bypass=deepcopy(eq);bypass['bypass']=True;assert filter_suffix({'audio_processing':bypass})==''
    print(json.dumps({'scope':'Four distinct new 0.5s synthetic PCM cases; no speech/video','ffmpeg':executable,
        'eq_gain_db':gains,'compressor_output_input_rms_ratio':ratio,'bypass_adds_no_filter':True,
        'sample_frames_each':24000,'human_listening':False},indent=2))


if __name__=='__main__':main()
