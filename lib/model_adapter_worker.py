"""Isolated inference worker. All model paths are local; Hub is offline.

Run with a request JSON and response JSON. Heavy libraries are imported only in
this process, never during tool discovery or web-server startup.
"""
from __future__ import annotations
import dataclasses
import json
import os
import sys
from pathlib import Path

def offline_environment():
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE'):
        os.environ[key]='1'
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1'


def plain(value):
    if dataclasses.is_dataclass(value):return plain(dataclasses.asdict(value))
    if isinstance(value,dict):return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [plain(v) for v in value]
    if hasattr(value,'tolist'):return value.tolist()
    if hasattr(value,'__dict__'):return plain(vars(value))
    if isinstance(value,(str,int,float,bool)) or value is None:return value
    return str(value)


def required(data,key):
    value=data.get(key)
    if not isinstance(value,str) or not value.strip():raise ValueError('Falta '+key)
    return value


def local_file(data,key):
    p=Path(required(data,key)).resolve()
    if not p.is_file() or not p.stat().st_size:raise ValueError('Archivo local ausente: '+key)
    return str(p)


def qwen_language(value):
    return {'en':'English','es':'Spanish','zh':'Chinese','ja':'Japanese','ko':'Korean','de':'German','fr':'French','ru':'Russian','pt':'Portuguese','it':'Italian'}.get(value,value)


def torch_setup(data):
    import torch
    device=data.get('device','cpu')
    if device=='cuda' and not torch.cuda.is_available():raise ValueError('CUDA solicitado no está disponible; no se cambia a CPU silenciosamente')
    return torch,device,torch.float32 if device=='cpu' else torch.float16


def run(request):
    family=request['family'];m=Path(request['model_dir']);data=request['inputs'];out=Path(request['output_dir'])
    if request.get('source_dir'):
        source=Path(request['source_dir']);sys.path.insert(0,str(source));sys.path.insert(0,str(source/'third_party'/'Matcha-TTS'))
    if not m.is_dir():raise ValueError('Carpeta de pesos ausente')
    def report(value,filename='result.json'):
        path=out/filename;path.write_text(json.dumps(plain(value),ensure_ascii=False,indent=2),encoding='utf-8')
        return {'success':True,'outputs':[str(path)],'result':plain(value)}
    def audio(value,sr):
        import numpy as np
        import soundfile as sf
        if hasattr(value,'detach'):value=value.detach().cpu().numpy()
        value=np.asarray(value).squeeze()
        if value.ndim!=1 or not value.size:raise ValueError('La voz no produjo audio mono válido')
        path=out/'voice.wav';sf.write(str(path),value,int(sr),subtype='PCM_16')
        return {'success':True,'outputs':[str(path)],'sample_rate':int(sr),'duration_seconds':len(value)/int(sr)}
    if family=='faster-whisper':
        from faster_whisper import WhisperModel
        device=data.get('device','cpu')
        model=WhisperModel(str(m),device=device,compute_type='int8' if device=='cpu' else 'float16',local_files_only=True)
        segments,info=model.transcribe(local_file(data,'input_path'),language=data.get('language'),word_timestamps=True)
        return report({'language':info.language,'duration_seconds':info.duration,'segments':[{'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word,'probability':w.probability} for w in s.words or []]} for s in segments]})
    if family=='minilm':
        from sentence_transformers import SentenceTransformer
        model=SentenceTransformer(str(m),device=data.get('device','cpu'),local_files_only=True)
        texts=data.get('texts') or [required(data,'text')]
        return report({'texts':texts,'embeddings':model.encode(texts,normalize_embeddings=True).tolist()})
    if family in ('ocr-latin','ocr-det'):
        from paddleocr import TextRecognition,TextDetection
        cls=TextRecognition if family=='ocr-latin' else TextDetection
        name='latin_PP-OCRv5_mobile_rec' if family=='ocr-latin' else 'PP-OCRv5_mobile_det'
        model=cls(model_name=name,model_dir=str(m),device='gpu:0' if data.get('device')=='cuda' else 'cpu')
        return report({'predictions':[p.json for p in model.predict(local_file(data,'input_path'))]})
    if family=='silero':
        import numpy as np
        import soundfile as sf
        import onnxruntime as ort
        wave,sr=sf.read(local_file(data,'input_path'),dtype='float32')
        if sr!=16000 or wave.ndim!=1:raise ValueError('Silero requiere WAV mono a 16000 Hz; prepara el audio antes')
        session=ort.InferenceSession(str(m/'onnx/model.onnx'),providers=['CPUExecutionProvider'])
        state=np.zeros((2,1,128),dtype=np.float32);context=np.zeros((1,64),dtype=np.float32);segments=[]
        for start in range(0,len(wave),512):
            chunk=wave[start:start+512];chunk=np.pad(chunk,(0,512-len(chunk))).reshape(1,-1)
            x=np.concatenate([context,chunk],axis=1)
            probability,state=session.run(None,{'input':x,'state':state,'sr':np.array(16000,dtype=np.int64)})
            context=x[:,-64:]
            score=float(np.asarray(probability).reshape(-1)[0])
            if score>=data.get('threshold',0.5):segments.append({'start':start/sr,'end':min(start+512,len(wave))/sr,'speech_probability':score})
        return report({'speech_windows':segments,'window_seconds':512/16000,'sample_rate':sr})
    torch,device,dtype=torch_setup(data)
    if family=='kokoro':
        from kokoro import KModel,KPipeline
        model=KModel(config=str(m/'config.json'),model=str(m/'kokoro-v1_0.pth')).to(device).eval()
        voice=Path(data.get('voice','af_heart'))
        if not voice.is_absolute():voice=m/'voices'/(str(voice)+('.pt' if voice.suffix!='.pt' else ''))
        if not voice.is_file():raise ValueError('Falta la voz local '+str(voice))
        voice_tensor=torch.load(str(voice),map_location=device,weights_only=True)
        languages={'en':'a','en-US':'a','en-GB':'b','es':'e','fr':'f','hi':'h','it':'i','pt':'p','ja':'j','zh':'z'}
        lang=languages.get(data.get('language','en'),data.get('language','a'))
        pipe=KPipeline(lang_code=lang,model=model,device=device)
        chunks=[item[2] for item in pipe(required(data,'text'),voice=voice_tensor,speed=data.get('speed',1)) if item[2] is not None]
        if not chunks:raise ValueError('Kokoro no produjo segmentos')
        return audio(torch.cat(chunks),24000)
    if family in ('qwen-tts','voice-design'):
        from qwen_tts import Qwen3TTSModel
        model=Qwen3TTSModel.from_pretrained(str(m),device_map=device,dtype=dtype,local_files_only=True,attn_implementation='eager')
        args={'text':required(data,'text'),'language':qwen_language(required(data,'language')),'max_new_tokens':data.get('max_new_tokens',2048)}
        if family=='voice-design':values,sr=model.generate_voice_design(**args,instruct=required(data,'instruction'))
        else:values,sr=model.generate_voice_clone(**args,ref_audio=local_file(data,'reference_audio'),ref_text=required(data,'reference_text'))
        return audio(values[0],sr)
    if family=='chatterbox':
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        model=ChatterboxMultilingualTTS.from_local(m,device=device)
        args={'language_id':required(data,'language')}
        if data.get('reference_audio'):args['audio_prompt_path']=local_file(data,'reference_audio')
        return audio(model.generate(required(data,'text'),**args),model.sr)
    if family=='cosyvoice':
        from cosyvoice.cli.cosyvoice import AutoModel
        model=AutoModel(model_dir=str(m),load_trt=False,load_vllm=False,fp16=device=='cuda')
        chunks=[part['tts_speech'] for part in model.inference_zero_shot(required(data,'text'),required(data,'reference_text'),local_file(data,'reference_audio'),stream=False,speed=data.get('speed',1))]
        if not chunks:raise ValueError('CosyVoice no produjo audio')
        return audio(torch.cat(chunks,dim=1),model.sample_rate)
    if family=='aligner':
        from qwen_asr import Qwen3ForcedAligner
        model=Qwen3ForcedAligner.from_pretrained(str(m),dtype=dtype,device_map=device,local_files_only=True)
        return report({'alignment':model.align(audio=local_file(data,'input_path'),text=required(data,'text'),language=qwen_language(required(data,'language')))})
    if family=='depth':
        import cv2
        import numpy as np
        from depth_anything_v2.dpt import DepthAnythingV2
        model=DepthAnythingV2(encoder='vits',features=64,out_channels=[48,96,192,384])
        model.load_state_dict(torch.load(str(m/'depth_anything_v2_vits.pth'),map_location='cpu',weights_only=True))
        model.to(device).eval();image=cv2.imread(local_file(data,'input_path'))
        if image is None:raise ValueError('Imagen no reconocida')
        with torch.inference_mode():depth=model.infer_image(image)
        raw=out/'depth.npy';np.save(str(raw),depth)
        scaled=((depth-depth.min())/max(float(depth.max()-depth.min()),1e-8)*65535).astype('uint16')
        image_path=out/'depth.png'
        if not cv2.imwrite(str(image_path),scaled):raise ValueError('No se pudo escribir el mapa')
        return {'success':True,'outputs':[str(raw),str(image_path)],'relative_depth':True}
    if family=='m2m100':
        from transformers import M2M100ForConditionalGeneration,M2M100Tokenizer
        tokenizer=M2M100Tokenizer.from_pretrained(str(m),local_files_only=True);tokenizer.src_lang=required(data,'source_language')
        model=M2M100ForConditionalGeneration.from_pretrained(str(m),local_files_only=True).to(device).eval()
        inputs=tokenizer(required(data,'text'),return_tensors='pt').to(device)
        with torch.inference_mode():ids=model.generate(**inputs,forced_bos_token_id=tokenizer.get_lang_id(required(data,'language')),max_new_tokens=data.get('max_new_tokens',512))
        return report({'text':tokenizer.batch_decode(ids,skip_special_tokens=True)[0],'language':data['language']})
    if family=='qwen3':
        from transformers import AutoTokenizer,AutoModelForCausalLM
        tokenizer=AutoTokenizer.from_pretrained(str(m),local_files_only=True)
        model=AutoModelForCausalLM.from_pretrained(str(m),local_files_only=True,torch_dtype=dtype).to(device).eval()
        prompt=tokenizer.apply_chat_template([{'role':'user','content':required(data,'text')}],tokenize=False,add_generation_prompt=True)
        inputs=tokenizer(prompt,return_tensors='pt').to(device)
        with torch.inference_mode():ids=model.generate(**inputs,max_new_tokens=data.get('max_new_tokens',1024))
        return report({'text':tokenizer.decode(ids[0,inputs['input_ids'].shape[1]:],skip_special_tokens=True)})
    from PIL import Image
    from transformers import AutoProcessor
    if family=='parakeet':
        import soundfile as sf
        from transformers import AutoModelForTDT
        waveform,sr=sf.read(local_file(data,'input_path'),dtype='float32')
        if sr!=16000 or waveform.ndim!=1:raise ValueError('Parakeet requiere audio mono a 16000 Hz')
        processor=AutoProcessor.from_pretrained(str(m),local_files_only=True)
        model=AutoModelForTDT.from_pretrained(str(m),local_files_only=True,torch_dtype=dtype).to(device).eval()
        inputs=processor(waveform,sampling_rate=sr,return_tensors='pt').to(device)
        with torch.inference_mode():ids=model.generate(**inputs)
        return report({'text':processor.batch_decode(ids,skip_special_tokens=True)[0]})
    image=Image.open(local_file(data,'input_path')).convert('RGB')
    if family in ('smolvlm','qwen-vl'):
        from transformers import AutoModelForImageTextToText
        processor=AutoProcessor.from_pretrained(str(m),local_files_only=True)
        model=AutoModelForImageTextToText.from_pretrained(str(m),local_files_only=True,torch_dtype=dtype).to(device).eval()
        messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':required(data,'text')}]}]
        prompt=processor.apply_chat_template(messages,add_generation_prompt=True)
        inputs=processor(text=prompt,images=[image],return_tensors='pt').to(device)
        with torch.inference_mode():ids=model.generate(**inputs,max_new_tokens=data.get('max_new_tokens',512))
        return report({'text':processor.batch_decode(ids[:,inputs['input_ids'].shape[1]:],skip_special_tokens=True)[0],'scope':'single_image'})
    if family=='florence':
        from transformers import AutoModelForCausalLM
        processor=AutoProcessor.from_pretrained(str(m),trust_remote_code=True,local_files_only=True)
        model=AutoModelForCausalLM.from_pretrained(str(m),trust_remote_code=True,local_files_only=True,torch_dtype=dtype).to(device).eval()
        task=data.get('instruction','<DETAILED_CAPTION>');prompt=task+data.get('text','')
        inputs=processor(text=prompt,images=image,return_tensors='pt').to(device)
        with torch.inference_mode():ids=model.generate(**inputs,max_new_tokens=data.get('max_new_tokens',1024),do_sample=False)
        text=processor.batch_decode(ids,skip_special_tokens=False)[0]
        return report(processor.post_process_generation(text,task=task,image_size=image.size))
    if family=='grounding-dino':
        import inspect
        from transformers import AutoModelForZeroShotObjectDetection
        processor=AutoProcessor.from_pretrained(str(m),local_files_only=True)
        model=AutoModelForZeroShotObjectDetection.from_pretrained(str(m),local_files_only=True).to(device).eval()
        text=required(data,'text');inputs=processor(images=image,text=text,return_tensors='pt').to(device)
        with torch.inference_mode():outputs=model(**inputs)
        method=processor.post_process_grounded_object_detection
        threshold='threshold' if 'threshold' in inspect.signature(method).parameters else 'box_threshold'
        return report(method(outputs,inputs.input_ids,**{threshold:data.get('threshold',0.3)},text_threshold=0.25,target_sizes=[image.size[::-1]]))
    if family=='siglip':
        from transformers import AutoModel
        processor=AutoProcessor.from_pretrained(str(m),local_files_only=True)
        model=AutoModel.from_pretrained(str(m),local_files_only=True).to(device).eval()
        labels=data.get('labels')
        if not labels:raise ValueError('SigLIP requiere labels para comparar la imagen')
        inputs=processor(text=labels,images=image,padding='max_length',return_tensors='pt').to(device)
        with torch.inference_mode():scores=model(**inputs).logits_per_image.sigmoid()[0].cpu().tolist()
        return report({'matches':[{'label':label,'score':score} for label,score in zip(labels,scores)]})
    if family=='birefnet':
        from torchvision import transforms
        from transformers import AutoModelForImageSegmentation
        model=AutoModelForImageSegmentation.from_pretrained(str(m),trust_remote_code=True,local_files_only=True).to(device).eval()
        transform=transforms.Compose([transforms.Resize((1024,1024)),transforms.ToTensor(),transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
        with torch.inference_mode():mask=model(transform(image).unsqueeze(0).to(device))[-1].sigmoid().cpu()[0]
        mask=transforms.ToPILImage()(mask).resize(image.size);image.putalpha(mask)
        path=out/'cutout.png';image.save(path)
        return {'success':True,'outputs':[str(path)]}
    raise ValueError('No hay implementación nativa para '+family)


def block_network():
    import socket
    original=socket.socket.connect
    original_ex=socket.socket.connect_ex
    def offline(sock,address):
        if isinstance(address,(tuple,list)):raise RuntimeError('Runtime sin red: instala previamente la dependencia local que falta')
        return original(sock,address)
    def no_datagrams(*args,**kwargs):raise RuntimeError('Runtime sin red: descarga automática deshabilitada')
    def offline_ex(sock,address):
        if isinstance(address,(tuple,list)):raise RuntimeError('Runtime sin red: descarga automática deshabilitada')
        return original_ex(sock,address)
    socket.socket.connect=offline
    socket.socket.connect_ex=offline_ex
    socket.socket.sendto=no_datagrams


def main():
    offline_environment()
    block_network()
    response=Path(sys.argv[2])
    try:
        request=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        result=run(request);code=0
    except Exception as exc:result={'success':False,'error':type(exc).__name__+': '+str(exc)[:1600]};code=1
    response.write_text(json.dumps(plain(result),ensure_ascii=False),encoding='utf-8')
    return code

if __name__=='__main__':raise SystemExit(main())
