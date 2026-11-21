"""Repeatable local model diagnostics, separate from creative productions.

A controlled voice sample and optional ASR round trip produce inspectable files
and measurements. Successful measurements do not establish perceptual quality.
"""
from __future__ import annotations
import array
import hashlib
import json
import math
import re
import sys
import threading
import time
import unicodedata
import uuid
import wave
from pathlib import Path
from lib import production_studio as studio
from lib import production_agent as agent


def root():return studio.CONFIG_DIR/'validations'


def folder(identifier):
    if not re.fullmatch(r'check-[a-f0-9]{12}',identifier):raise ValueError('Prueba inválida')
    path=root()/identifier
    if not (path/'report.json').is_file():raise FileNotFoundError('Prueba no encontrada')
    return path


def signature(family,model_dir,voice=None):
    from lib.model_adapters import configuration,expected_files
    model=Path(model_dir);files=[]
    for name in expected_files(family,model):
        if family=='kokoro' and name.startswith('voices/') and name!='voices/'+str(voice)+'.pt':continue
        p=model/name
        if p.is_file():
            st=p.stat();files.append([name,st.st_size,st.st_mtime_ns])
    if family=='kokoro' and voice:
        name='voices/'+voice+'.pt';p=model/name
        if p.is_file() and not any(item[0]==name for item in files):
            st=p.stat();files.append([name,st.st_size,st.st_mtime_ns])
    if not files:raise ValueError('No hay archivos del modelo para identificar esta prueba')
    cfg=configuration(family)
    payload={'family':family,'voice':voice,'model_dir':str(model.resolve()),'files':sorted(files),
             'python_executable':cfg.get('python_executable') or sys.executable,'source_dir':cfg.get('source_dir',''),
             'worker_code_sha256':hashlib.sha256(Path(__file__).with_name('model_adapter_worker.py').read_bytes()).hexdigest()}
    # This digest identifies metadata/configuration; it is NOT a model-content hash.
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()


def current_evidence(family,model_dir):
    if family not in ('kokoro','faster-whisper') or not model_dir:return None
    paths=sorted(root().glob('check-*/report.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]
    for path in paths:
        report=studio.read_json(path,{})
        record=report.get('models',{}).get(family,{})
        if not record.get('inference_measured') or not (path.parent/'voice/voice.wav').is_file():continue
        if family=='faster-whisper' and not (path.parent/'transcription/result.json').is_file():continue
        try:matches=record['signature']==signature(family,model_dir,record.get('voice'))
        except (OSError,ValueError,KeyError):continue
        if matches:
            return {'validation_id':report['id'],'created_at':report['created_at'],'voice':record.get('voice'),
                    'inference_verified':True,'scope':'single_controlled_sample','quality_review':report.get('human_review'),
                    'identity_basis':'file paths, sizes, modification times, worker code and configured runtime; not model-content hashes'}
    return None


def measure_wav(path):
    with wave.open(str(path),'rb') as wav:
        channels=wav.getnchannels();rate=wav.getframerate();width=wav.getsampwidth();frames=wav.getnframes()
        if channels!=1 or width!=2 or rate<8000 or frames<=0:raise ValueError('Se esperaba WAV PCM16 mono con muestras reales')
        if frames/rate>300:raise ValueError('La muestra supera cinco minutos')
        count=0;total=0;peak=0;clipped=0
        while True:
            raw=wav.readframes(16384)
            if not raw:break
            samples=array.array('h');samples.frombytes(raw)
            if sys.byteorder!='little':samples.byteswap()
            for value in samples:
                value=abs(value);total+=value*value;peak=max(peak,value);clipped+=value>=32767
            count+=len(samples)
        if count!=frames:raise ValueError('WAV truncado o número de muestras incoherente')
        rms=math.sqrt(total/count)/32768
        result={'duration_seconds':frames/rate,'sample_rate':rate,'channels':channels,'sample_width_bytes':width,
                'peak':peak/32768,'rms':rms,'clipped_fraction':clipped/count,'samples':count,'decoded':True}
        if result['duration_seconds']<0.1 or peak==0:raise ValueError('El audio no contiene una muestra audible verificable')
        return result


def words(text):
    text=unicodedata.normalize('NFKD',text.casefold())
    text=''.join(c for c in text if not unicodedata.combining(c))
    return re.findall(r'\w+',text,flags=re.UNICODE)


def compare_transcript(reference,transcript):
    a=words(reference);b=words(transcript);previous=list(range(len(b)+1))
    for i,left in enumerate(a,1):
        row=[i]
        for j,right in enumerate(b,1):row.append(min(row[-1]+1,previous[j]+1,previous[j-1]+(left!=right)))
        previous=row
    return {'word_edits':previous[-1],'reference_words':len(a),'recognized_words':len(b),
            'word_error_rate':previous[-1]/max(len(a),1),'normalization':'case, accents and punctuation ignored',
            'quality_pass':None,'note':'WER es una medida diagnóstica, no aprobación de voz o traducción.'}


def save(path,**values):
    with studio.LOCK:
        report=studio.read_json(path/'report.json',{});report.update(values,updated_at=studio.now())
        studio.save_json(path/'report.json',report)
    return report


def read(identifier):
    path=folder(identifier);report=studio.read_json(path/'report.json')
    with agent.ACTIVE_LOCK:active='validation:'+identifier in agent.ACTIVE
    if report['status']=='running' and not active:report.update(status='interrupted',message='El proceso anterior terminó. Conserva los resultados; una nueva prueba tendrá su propio registro.')
    report['active']=active
    if (path/'voice/voice.wav').is_file():report['audio_url']='/api/studio/validations/'+identifier+'/audio'
    return report


def execute(identifier,registry=None):
    path=folder(identifier);report=studio.read_json(path/'report.json');request=report['request'];started=time.monotonic()
    models={}
    try:
        from lib.model_adapters import diagnostics
        info=diagnostics('kokoro')
        if not info['ready']:save(path,status='blocked',message='Kokoro: '+'; '.join(info['problems']),diagnostics=info);return
        voice=request['voice']
        if voice not in info.get('available_voices',[]):raise ValueError('La voz española elegida no está instalada: '+voice)
        initial=signature('kokoro',info['model_dir'],voice)
        save(path,status='running',message='Generando muestra local de voz; no se descargan pesos.')
        if registry is None:
            from tools.tool_registry import registry
            registry.ensure_discovered()
        tool=registry.get('model_kokoro')
        if tool is None or not agent.LocalAgent.permitted(tool):raise ValueError('Adaptador local de Kokoro no disponible')
        output=path/'voice';output.mkdir(exist_ok=True)
        inputs={'text':request['text'],'language':'es','voice':voice,'device':request['device'],'output_dir':str(output),'timeout':600}
        if tool.estimate_cost(inputs)!=0:raise ValueError('La prueba requiere coste cero')
        result=tool.execute(inputs)
        if not result.success or result.cost_usd!=0:raise ValueError(result.error or 'La generación no terminó a coste cero')
        audio=output/'voice.wav'
        metrics=measure_wav(audio)
        if initial!=signature('kokoro',info['model_dir'],voice):raise ValueError('Los archivos/configuración cambiaron durante la prueba')
        models['kokoro']={'signature':initial,'voice':voice,'model_dir':info['model_dir'],'inference_measured':True}
        save(path,models=models,audio=metrics,status='audio_measured',message='Audio decodificado y medido. Falta escuchar y revisar pronunciación.',quality_review_required=True)
        if request['transcribe']:
            info_asr=diagnostics('faster-whisper')
            if not info_asr['ready']:
                save(path,status='partial',message='Audio disponible; transcripción bloqueada por dependencias.',transcription={'status':'blocked','problems':info_asr['problems']})
                return
            model_signature=signature('faster-whisper',info_asr['model_dir'])
            asr=registry.get('model_faster_whisper')
            if asr is None or not agent.LocalAgent.permitted(asr):raise ValueError('Adaptador local de transcripción no disponible')
            asr_dir=path/'transcription';asr_dir.mkdir(exist_ok=True)
            inputs={'input_path':str(audio),'language':'es','device':request['device'],'output_dir':str(asr_dir),'timeout':600}
            if asr.estimate_cost(inputs)!=0:raise ValueError('La transcripción requiere coste cero')
            result=asr.execute(inputs)
            if not result.success or result.cost_usd!=0:raise ValueError(result.error or 'La transcripción falló')
            transcript=studio.read_json(asr_dir/'result.json',{})
            segments=transcript.get('segments',[])
            recognized=' '.join(s.get('text','') for s in segments).strip()
            if not recognized:raise ValueError('El transcriptor no reconoció texto')
            for segment in segments:
                for item in [segment]+segment.get('words',[]):
                    start=item.get('start');end=item.get('end')
                    if not isinstance(start,(int,float)) or not isinstance(end,(int,float)) or not math.isfinite(start) or not math.isfinite(end) or not 0<=start<=end<=metrics['duration_seconds']+1:raise ValueError('Marcas de tiempo fuera de la muestra')
            if model_signature!=signature('faster-whisper',info_asr['model_dir']):raise ValueError('Los pesos ASR cambiaron durante la prueba')
            models['faster-whisper']={'signature':model_signature,'model_dir':info_asr['model_dir'],'inference_measured':True}
            save(path,models=models,transcription={'status':'measured','text':recognized,'segments':segments,'comparison':compare_transcript(request['text'],recognized)})
        save(path,status='review_required',message='Prueba terminada. Escucha la muestra y revisa el texto antes de aprobar calidad.')
    except Exception as exc:save(path,status='partial' if models else 'failed',models=models,message=str(exc)[:1800])
    finally:
        try:save(path,elapsed_seconds=round(time.monotonic()-started,3))
        finally:
            with agent.ACTIVE_LOCK:agent.ACTIVE.pop('validation:'+identifier,None)


def start(data):
    if not isinstance(data,dict) or set(data)-{'text','voice','device','transcribe'}:raise ValueError('Solicitud de prueba inválida')
    text=data.get('text');voice=data.get('voice');device=data.get('device','cpu');transcribe=data.get('transcribe',True)
    if not isinstance(text,str) or not 1<=len(text.strip())<=2000:raise ValueError('Escribe una muestra de hasta 2000 caracteres')
    if not isinstance(voice,str) or not re.fullmatch(r'e[fm]_[a-z0-9_]+',voice):raise ValueError('Selecciona una voz española local de Kokoro')
    if device not in ('cpu','cuda') or type(transcribe) is not bool:raise ValueError('Opciones de prueba inválidas')
    identifier='check-'+uuid.uuid4().hex[:12]
    with agent.ACTIVE_LOCK:
        if agent.ACTIVE:raise ValueError('Espera a que termine la producción o prueba activa')
        path=root()/identifier;path.mkdir(parents=True)
        save(path,id=identifier,created_at=studio.now(),status='running',message='Preparando diagnóstico local',
             request={'text':text.strip(),'voice':voice,'device':device,'transcribe':transcribe},models={},quality_review_required=True)
        thread=threading.Thread(target=execute,args=(identifier,),daemon=True,name=identifier)
        agent.ACTIVE['validation:'+identifier]=(thread,threading.Event());thread.start()
    return {'id':identifier}


def review(identifier,data):
    path=folder(identifier)
    if not isinstance(data,dict) or set(data)-{'accepted','comment'} or type(data.get('accepted')) is not bool or not isinstance(data.get('comment',''),str) or len(data.get('comment',''))>4000:raise ValueError('Revisión inválida')
    with agent.ACTIVE_LOCK:
        if 'validation:'+identifier in agent.ACTIVE:raise ValueError('La prueba sigue activa')
        report=studio.read_json(path/'report.json')
        if not report.get('audio',{}).get('decoded'):raise ValueError('No hay una muestra de audio medida para revisar')
        return save(path,status=('reviewed' if data['accepted'] else 'rejected') if report['status']=='review_required' else report['status'],human_review={'accepted':data['accepted'],'comment':data.get('comment',''),'at':studio.now()},quality_review_required=False)
