"""Additional offline engines; imported only by the isolated model worker."""
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys


def _local(path):
    path=Path(path).resolve()
    if not path.exists():raise ValueError('Recurso local ausente: '+str(path))
    return path


def run(request):
    # worker directory is on sys.path even when the application is elsewhere.
    try:from lib.model_adapter_worker import local_file,required,torch_setup
    except ImportError:from model_adapter_worker import local_file,required,torch_setup
    family=request['family'];data=request['inputs'];model=Path(request['model_dir']);out=Path(request['output_dir'])
    if family=='dwpose':
        import cv2
        import numpy as np
        import onnxruntime as ort
        source=_local(request.get('source_dir') or '')
        candidates=[source/'ControlNet-v1-1-nightly/annotator/dwpose',source/'annotator/dwpose',source]
        folder=next((p for p in candidates if (p/'onnxdet.py').is_file() and (p/'onnxpose.py').is_file()),None)
        if folder is None:raise ValueError('source_dir debe contener las rutinas ONNX originales de DWPose')
        def module(name):
            spec=importlib.util.spec_from_file_location('openmontage_'+name,folder/(name+'.py'))
            mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
        provider='CUDAExecutionProvider' if data.get('device','cpu')=='cuda' else 'CPUExecutionProvider'
        if provider not in ort.get_available_providers():raise ValueError('Proveedor ONNX solicitado no disponible: '+provider)
        det=ort.InferenceSession(str(_local(model/'yolox_l.onnx')),providers=[provider])
        pose=ort.InferenceSession(str(_local(model/'dw-ll_ucoco_384.onnx')),providers=[provider])
        image=cv2.imread(local_file(data,'input_path'))
        if image is None:raise ValueError('Imagen DWPose ilegible')
        boxes=module('onnxdet').inference_detector(det,image)
        if boxes is None or len(boxes)==0:keypoints=np.empty((0,133,2));scores=np.empty((0,133))
        else:keypoints,scores=module('onnxpose').inference_pose(pose,boxes,image)
        result={'schema':'coco_wholebody_133','keypoints':keypoints.tolist(),'scores':scores.tolist(),'coordinate_space':'pixels','width':image.shape[1],'height':image.shape[0]}
        path=out/'pose.json';path.write_text(json.dumps(result),encoding='utf-8')
        canvas=np.zeros_like(image);threshold=data.get('threshold',0.3)
        for person,confidence in zip(keypoints,scores):
            for point,score in zip(person,confidence):
                if float(score)>=threshold:cv2.circle(canvas,tuple(int(v) for v in point),3,(0,255,0),-1)
        preview=out/'pose-points.png'
        if not cv2.imwrite(str(preview),canvas):raise ValueError('No se pudo escribir la vista de puntos')
        return {'success':True,'outputs':[str(path),str(preview)],'people':len(keypoints)}
    torch,device,dtype=torch_setup(data)
    if family in ('longcat','longcat-avatar'):
        if device!='cuda':raise ValueError('El motor original LongCat preparado requiere CUDA')
        if sys.platform=='win32':raise ValueError('El motor original requiere NCCL en Linux/WSL; no se sustituye por pesos ComfyUI diferentes')
        source=_local(required(request,'source_dir'))
        os.environ.update(MASTER_ADDR='127.0.0.1',MASTER_PORT='6016',WORLD_SIZE='1',RANK='0',LOCAL_RANK='0')
        if family=='longcat-avatar':
            entry=_local(source/'run_demo_avatar_single_audio_to_video.py')
            base=model.parent/'LongCat-Video'
            if not base.is_dir():raise ValueError('El motor Avatar original requiere LongCat-Video junto a la carpeta Avatar; conserva esa disposición o usa un enlace local')
            if data.get('seed') is not None:raise ValueError('El CLI Avatar original no expone seed; no se ignora el valor solicitado')
            if data.get('frames') is not None or data.get('fps') is not None:raise ValueError('Avatar v1.0 utiliza 93 frames y 16 fps por segmento; no expone frames/fps por CLI')
            width=data.get('width',832);height=data.get('height',480)
            if (width,height) not in ((832,480),(1280,768)):raise ValueError('Avatar original admite 832x480 o 1280x768')
            payload={'prompt':required(data,'text'),'cond_image':local_file(data,'input_path'),'cond_audio':{'person1':local_file(data,'reference_audio')}}
            input_json=out/'avatar-input.json';input_json.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
            sys.argv=[str(entry),'--input_json',str(input_json),'--checkpoint_dir',str(model),
                '--output_dir',str(out),'--model_type','avatar-v1.0','--stage_1','ai2v',
                '--resolution','480p' if height==480 else '720p','--num_segments','1',
                '--num_inference_steps',str(data.get('steps',50))]
            # Relative audio intermediates belong to this project, not the repo.
            os.chdir(out);runpy.run_path(str(entry),run_name='__main__')
            outputs=[str(p) for p in out.glob('*.mp4') if p.stat().st_size]
            if not outputs:raise ValueError('Avatar no produjo un video')
            return {'success':True,'outputs':outputs}
        import torch.distributed as dist
        import numpy as np
        from transformers import AutoTokenizer,UMT5EncoderModel
        from torchvision.io import write_video
        from longcat_video.pipeline_longcat_video import LongCatVideoPipeline
        from longcat_video.modules.scheduling_flow_match_euler_discrete import FlowMatchEulerDiscreteScheduler
        from longcat_video.modules.autoencoder_kl_wan import AutoencoderKLWan
        from longcat_video.modules.longcat_video_dit import LongCatVideoTransformer3DModel
        from longcat_video.context_parallel import context_parallel_util
        torch.cuda.set_device(0);dist.init_process_group(backend='nccl',rank=0,world_size=1)
        try:
            context_parallel_util.init_context_parallel(context_parallel_size=1,global_rank=0,world_size=1)
            kwargs={'torch_dtype':torch.bfloat16,'local_files_only':True}
            pipe=LongCatVideoPipeline(tokenizer=AutoTokenizer.from_pretrained(str(model),subfolder='tokenizer',local_files_only=True),
                text_encoder=UMT5EncoderModel.from_pretrained(str(model),subfolder='text_encoder',**kwargs),
                vae=AutoencoderKLWan.from_pretrained(str(model),subfolder='vae',**kwargs),
                scheduler=FlowMatchEulerDiscreteScheduler.from_pretrained(str(model),subfolder='scheduler',local_files_only=True),
                dit=LongCatVideoTransformer3DModel.from_pretrained(str(model),subfolder='dit',cp_split_hw=context_parallel_util.get_optimal_split(1),**kwargs))
            pipe.to(0)
            with torch.inference_mode():video=pipe.generate_t2v(prompt=required(data,'text'),negative_prompt=data.get('negative_prompt',''),
                height=data.get('height',480),width=data.get('width',832),num_frames=data.get('frames',93),
                num_inference_steps=data.get('steps',50),guidance_scale=4.0,
                generator=torch.Generator(device='cuda').manual_seed(data.get('seed',0)))[0]
            path=out/'video.mp4';tensor=(torch.from_numpy(np.asarray(video))*255).clamp(0,255).to(torch.uint8)
            write_video(str(path),tensor,fps=data.get('fps',15),video_codec='libx264',options={'crf':'18'})
            return {'success':True,'outputs':[str(path)]}
        finally:dist.destroy_process_group()
    if family=='cogvideo':
        from diffusers import CogVideoXPipeline
        from diffusers.utils import export_to_video
        frames=data.get('frames',49)
        if frames%4!=1:raise ValueError('CogVideoX requiere frames = 4n+1')
        pipe=CogVideoXPipeline.from_pretrained(str(model),torch_dtype=dtype,local_files_only=True)
        pipe.vae.enable_slicing();pipe.vae.enable_tiling()
        if device=='cuda':pipe.enable_sequential_cpu_offload()
        else:pipe.to(device)
        generator=torch.Generator(device='cpu').manual_seed(data.get('seed',0))
        with torch.inference_mode():
            video=pipe(prompt=required(data,'text'),negative_prompt=data.get('negative_prompt'),
                width=data.get('width',720),height=data.get('height',480),num_frames=frames,
                num_inference_steps=data.get('steps',50),generator=generator).frames[0]
        path=out/'video.mp4';export_to_video(video,str(path),fps=data.get('fps',8))
        return {'success':True,'outputs':[str(path)]}
    if family=='lama':
        import numpy as np
        from PIL import Image
        from omegaconf import OmegaConf
        from saicinpainting.training.trainers import load_checkpoint
        # The downloaded ZIP must be extracted; it is not a TorchScript weight.
        config=_local(model/'config.yaml');checkpoint=_local(model/'models/best.ckpt')
        cfg=OmegaConf.load(str(config));cfg.training_model.predict_only=True;cfg.visualizer.kind='noop'
        net=load_checkpoint(cfg,str(checkpoint),strict=False,map_location='cpu');net.freeze();net.to(device)
        image=Image.open(local_file(data,'input_path')).convert('RGB')
        mask=Image.open(local_file(data,'mask_path')).convert('L')
        if mask.size!=image.size:raise ValueError('La máscara debe tener el tamaño de la imagen; blanco indica zona a reconstruir')
        rgb=np.asarray(image,dtype=np.float32).transpose(2,0,1)/255
        matte=(np.asarray(mask,dtype=np.float32)[None]>0).astype(np.float32)
        h,w=matte.shape[1:];padding=((0,0),(0,(-h)%8),(0,(-w)%8))
        batch={'image':torch.from_numpy(np.pad(rgb,padding,mode='symmetric'))[None].to(device),
               'mask':torch.from_numpy(np.pad(matte,padding,mode='symmetric'))[None].to(device)}
        with torch.inference_mode():result=net(batch)['inpainted'][0].permute(1,2,0).detach().cpu().numpy()[:h,:w]
        path=out/'inpainted.png';Image.fromarray(np.clip(result*255,0,255).astype('uint8')).save(path)
        return {'success':True,'outputs':[str(path)]}
    if family=='magihuman':
        if device!='cuda':raise ValueError('MagiHuman original requiere device=cuda')
        if sys.platform=='win32':raise ValueError('MagiHuman original requiere un runtime Linux/WSL preparado')
        source=_local(required(request,'source_dir'));entry=_local(source/'inference/pipeline/entry.py')
        config=_local(required(request,'runtime_config'));cfg=json.loads(config.read_text(encoding='utf-8'))
        # Validate every weight/config path instead of letting upstream resolve a
        # Hub identifier or its placeholder /path/to/checkpoints locations.
        engine=cfg.get('engine_config',{});evaluation=cfg.get('evaluation_config',{})
        if engine.get('cp_size',1)!=1:raise ValueError('Este adaptador prepara ejecución con una GPU; cp_size debe ser 1')
        for key,value in {**engine,**evaluation}.items():
            if key=='load' or key.endswith(('_path','_ckpt')):
                if not isinstance(value,str) or not Path(value).is_absolute():raise ValueError('Usa una ruta local absoluta para '+key)
                _local(value)
        if 'load' not in engine:raise ValueError('Falta engine_config.load')
        prefix=out/'magihuman';args=[str(entry),'--config-load-path',str(config),'--prompt',required(data,'text'),
            '--output_path',str(prefix),'--seconds',str(data.get('seconds',4)),
            '--br_width',str(data.get('width',448)),'--br_height',str(data.get('height',256)),
            '--seed',str(data.get('seed',0))]
        if data.get('input_path'):args+=['--image_path',local_file(data,'input_path')]
        if data.get('reference_audio'):args+=['--audio_path',local_file(data,'reference_audio')]
        sys.path.insert(0,str(source));sys.argv=args
        os.environ.update(MASTER_ADDR='127.0.0.1',MASTER_PORT='6016',WORLD_SIZE='1',RANK='0',LOCAL_RANK='0',LOCAL_WORLD_SIZE='1')
        os.chdir(source)
        runpy.run_path(str(entry),run_name='__main__')
        outputs=[str(p) for p in out.glob('magihuman*') if p.suffix.lower() in ('.mp4','.wav','.webm') and p.is_file() and p.stat().st_size]
        if not outputs:raise ValueError('MagiHuman no produjo video/audio en el destino del proyecto')
        return {'success':True,'outputs':outputs}
    raise ValueError('Motor adicional desconocido: '+family)
