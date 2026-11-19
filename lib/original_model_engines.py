"""Headless bridges for pinned original model sources and original weights.

No GUI server, shell, installer or model downloader is started by this module.
Source snapshots are checked before adapting their documented example inputs.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys


def pinned_source(identifier,source):
    records=json.loads((Path(__file__).resolve().parents[1]/'docs/runtime_sources.json').read_text(encoding='utf-8'))
    record=records[identifier];path=Path(source)/record['path']
    text=path.read_text(encoding='utf-8').replace('\r\n','\n')
    if hashlib.sha256(text.encode()).hexdigest()!=record['sha256']:
        raise ValueError('El código original cambió: prepara la revisión '+record['revision']+' de '+record['repo']+' antes de probar '+identifier)
    return path,text


def patch_assignments(text,overrides,filename):
    tree=ast.parse(text,filename=filename);found=set()
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in overrides:
                if name in found:raise ValueError('Asignación ambigua en el ejemplo original: '+name)
                node.value=ast.parse(repr(overrides[name]),mode='eval').body;found.add(name)
    if found!=set(overrides):raise ValueError('El ejemplo no expone: '+', '.join(sorted(set(overrides)-found)))
    return compile(ast.fix_missing_locations(tree),filename,'exec')


def run(request):
    try:from lib.model_adapter_worker import local_file,required,torch_setup
    except ImportError:from model_adapter_worker import local_file,required,torch_setup
    family=request['family'];data=request['inputs'];model=Path(request['model_dir']);out=Path(request['output_dir'])
    source=Path(required(request,'source_dir')).resolve()
    torch,device,dtype=torch_setup(data)
    if device!='cuda':raise ValueError('El motor original seleccionado requiere CUDA; solicita device=cuda')
    sys.path.insert(0,str(source))
    if family in ('wan-camera','wan-control'):
        identifier='camera-script' if family=='wan-camera' else 'control-script'
        path,text=pinned_source(identifier,source)
        config=source/'config/wan2.2/wan_civitai_i2v.yaml'
        if not config.is_file():raise ValueError('Falta el YAML original de VideoX-Fun')
        overrides={'model_name':str(model),'config_path':str(config),'prompt':required(data,'text'),
            'negative_prompt':data.get('negative_prompt',''),'sample_size':[data.get('height',480),data.get('width',832)],
            'video_length':data.get('frames',81),'fps':data.get('fps',16),'seed':data.get('seed',0),
            'num_inference_steps':data.get('steps',50),'save_path':str(out),
            'start_image':local_file(data,'input_path') if data.get('input_path') else None,
            'end_image':None,'ref_image':None,'control_video':local_file(data,'control_video') if family=='wan-control' else None,
            'control_camera_txt':local_file(data,'camera_path') if family=='wan-camera' else None,
            'fsdp_text_encoder':False,'enable_teacache':False,'GPU_memory_mode':'sequential_cpu_offload'}
        os.chdir(source)
        exec(patch_assignments(text,overrides,str(path)),{'__file__':str(path),'__name__':'__main__'})
    elif family=='wan-s2v':
        path,_=pinned_source('s2v-script',source)
        if data.get('fps') is not None:raise ValueError('El motor S2V original determina fps; no se ignora un fps solicitado')
        sys.argv=[str(path),'--task','s2v-14B','--ckpt_dir',str(model),
            '--size',str(data.get('width',1024))+'*'+str(data.get('height',704)),
            '--prompt',required(data,'text'),'--image',local_file(data,'input_path'),
            '--audio',local_file(data,'reference_audio'),'--infer_frames',str(data.get('frames',80)),
            '--sample_steps',str(data.get('steps',40)),'--base_seed',str(data.get('seed',0)),
            '--offload_model','True','--t5_cpu','--num_clip','1','--save_file',str(out/'video.mp4')]
        os.chdir(source);runpy.run_path(str(path),run_name='__main__')
    elif family=='framepack':
        path,text=pinned_source('framepack-script',source)
        if any(k in data for k in ('frames','fps','width','height')):raise ValueError('El motor FramePack original determina tamaño y fps; usa seconds para su duración')
        config=Path(required(request,'runtime_config'));cfg=json.loads(config.read_text(encoding='utf-8'))
        backbone=Path(required(cfg,'backbone_dir'));vision=Path(required(cfg,'vision_dir'))
        if not backbone.is_absolute() or not backbone.is_dir() or not vision.is_absolute() or not vision.is_dir():raise ValueError('Indica backbone_dir y vision_dir como carpetas locales completas')
        import numpy as np
        import einops
        import traceback
        from PIL import Image
        from transformers import LlamaModel,CLIPTextModel,LlamaTokenizerFast,CLIPTokenizer,SiglipImageProcessor,SiglipVisionModel
        from diffusers import AutoencoderKLHunyuanVideo
        from diffusers_helper.models.hunyuan_video_packed import HunyuanVideoTransformer3DModelPacked
        from diffusers_helper import memory,utils,hunyuan,bucket_tools,clip_vision
        from diffusers_helper.pipelines.k_diffusion_hunyuan import sample_hunyuan
        args={'local_files_only':True}
        text_encoder=LlamaModel.from_pretrained(str(backbone),subfolder='text_encoder',torch_dtype=torch.float16,**args).cpu()
        text_encoder_2=CLIPTextModel.from_pretrained(str(backbone),subfolder='text_encoder_2',torch_dtype=torch.float16,**args).cpu()
        tokenizer=LlamaTokenizerFast.from_pretrained(str(backbone),subfolder='tokenizer',**args)
        tokenizer_2=CLIPTokenizer.from_pretrained(str(backbone),subfolder='tokenizer_2',**args)
        vae=AutoencoderKLHunyuanVideo.from_pretrained(str(backbone),subfolder='vae',torch_dtype=torch.float16,**args).cpu()
        feature_extractor=SiglipImageProcessor.from_pretrained(str(vision),subfolder='feature_extractor',**args)
        image_encoder=SiglipVisionModel.from_pretrained(str(vision),subfolder='image_encoder',torch_dtype=torch.float16,**args).cpu()
        transformer=HunyuanVideoTransformer3DModelPacked.from_pretrained(str(model),torch_dtype=torch.bfloat16,**args).cpu()
        for net in (text_encoder,text_encoder_2,vae,image_encoder,transformer):net.eval();net.requires_grad_(False)
        vae.enable_slicing();vae.enable_tiling();transformer.high_quality_fp32_output_for_inference=True
        memory.DynamicSwapInstaller.install_model(transformer,device=memory.gpu)
        memory.DynamicSwapInstaller.install_model(text_encoder,device=memory.gpu)
        class Queue:
            def top(self):return None
            def push(self,item):pass
        class Stream:input_queue=Queue();output_queue=Queue()
        namespace={'torch':torch,'np':np,'einops':einops,'traceback':traceback,'os':os,'Image':Image,
            'high_vram':False,'text_encoder':text_encoder,'text_encoder_2':text_encoder_2,
            'tokenizer':tokenizer,'tokenizer_2':tokenizer_2,'vae':vae,'feature_extractor':feature_extractor,
            'image_encoder':image_encoder,'transformer':transformer,'stream':Stream(),'outputs_folder':str(out),
            'sample_hunyuan':sample_hunyuan,'make_progress_bar_html':lambda *a:''}
        for module in (memory,utils,hunyuan,bucket_tools,clip_vision):
            namespace.update({name:getattr(module,name) for name in dir(module) if not name.startswith('_') and name not in namespace})
        tree=ast.parse(text,filename=str(path));worker=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
        exec(compile(ast.Module(body=[worker],type_ignores=[]),str(path),'exec'),namespace)
        image=np.asarray(Image.open(local_file(data,'input_path')).convert('RGB'))
        namespace['worker'](image,required(data,'text'),data.get('negative_prompt',''),data.get('seed',0),
            data.get('seconds',5),9,data.get('steps',25),1.0,10.0,0.0,6.0,False,18)
    else:raise ValueError('Motor original desconocido')
    outputs=[str(p.resolve()) for p in out.rglob('*.mp4') if p.is_file() and p.stat().st_size]
    if not outputs:raise ValueError('El motor original no produjo video en el destino del proyecto; revisa su registro')
    return {'success':True,'outputs':outputs,'engine':'original_offline','family':family}
