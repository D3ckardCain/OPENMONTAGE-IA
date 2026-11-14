"""Catalog-to-runtime binding. No downloads, creative routing or inference claims."""
from __future__ import annotations
import functools
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from lib import production_studio as studio
from tools._comfyui.client import ComfyUIError
from tools.base_tool import BaseTool, ToolResult, ToolRuntime, ToolTier, ToolStatus, ResourceProfile, Determinism

# Each native entry names a real worker implementation and its import dependencies.
NATIVE={
 'kokoro':('tts',['torch','kokoro','soundfile']),
 'faster-whisper':('transcription',['faster_whisper']),
 'm2m100':('translation',['torch','transformers','sentencepiece']),
 'minilm':('text_embeddings',['sentence_transformers']),
 'siglip':('image_text_similarity',['torch','transformers','PIL']),
 'grounding-dino':('object_detection',['torch','transformers','PIL']),
 'florence':('image_analysis',['torch','transformers','PIL']),
 'birefnet':('background_removal',['torch','transformers','torchvision','PIL']),
 'qwen3':('text_generation',['torch','transformers','accelerate']),
 'qwen-vl':('image_analysis',['torch','transformers','accelerate','PIL']),
 'smolvlm':('image_analysis',['torch','transformers','PIL']),
 'parakeet':('transcription',['torch','transformers','soundfile']),
 'qwen-tts':('tts',['torch','qwen_tts','soundfile']),
 'voice-design':('tts',['torch','qwen_tts','soundfile']),
 'aligner':('forced_alignment',['torch','qwen_asr']),
 'chatterbox':('tts',['torch','chatterbox','soundfile']),
 'cosyvoice':('tts',['torch','cosyvoice','torchaudio']),
 'depth':('depth_estimation',['torch','depth_anything_v2','cv2']),
 'silero':('voice_activity',['onnxruntime','numpy','soundfile']),
 'ocr-latin':('ocr',['paddleocr']),
 'ocr-det':('text_detection',['paddleocr']),
}
# Remaining downloaded stacks use an explicit, validated ComfyUI API graph.
# Binding a family does not assert that a compatible graph/node pack is installed.
VIDEO={'wan','cosmos','ltx-legacy','mochi','cogvideo','kandinsky','longcat','longcat-avatar','magihuman','ltx23','ltx25','hunyuan15','framepack','h3','wan-vace','wan-camera','wan-control','wan-s2v'}
IMAGE={'qwen-image','flux-klein','z-image','qwen-edit','lama'}

def catalogs():
    result={}
    for p in sorted((studio.REPO_ROOT/'docs/models').glob('*.json')):
        data=studio.read_json(p);files={e['destination']:e for e in data['files']}
        for group in data['groups']:result[group['id']]={**group,'entries':[files[f] for f in group['files']]}
    return result

CATALOG=catalogs()

def spec(family):
    if family in NATIVE:
        capability,deps=NATIVE[family];backend='native'
    else:
        backend='comfyui';deps=[]
        capability='video_generation' if family in VIDEO else 'image_generation' if family in IMAGE else 'music_generation' if family=='acestep' else 'pose_estimation'
    return {'family':family,'backend':backend,'capability':capability,'dependencies':deps}


def configuration(family):
    defaults={'workflow_path':str(studio.REPO_ROOT/'tools/_comfyui/workflows/wan22-t2v-4step.json'),'output_node':'16'} if family=='wan' else {}
    return {**defaults,**studio.settings().get('adapter_settings',{}).get(family,{})}


def configure(family,data):
    if family not in CATALOG:raise ValueError('Modelo desconocido')
    if set(data)-{'python_executable','model_dir','workflow_path','output_node','source_dir'}:raise ValueError('Configuración de adaptador desconocida')
    for name,value in data.items():
        if not isinstance(value,str) or len(value)>4000:raise ValueError('Configuración inválida')
        if name!='output_node' and value and not Path(value).is_absolute():raise ValueError('Usa una ruta absoluta para '+name)
    with studio.LOCK:
        current=studio.settings();bindings=current.get('adapter_settings',{})
        bindings[family]={**bindings.get(family,{}),**data};current['adapter_settings']=bindings
        studio.save_json(studio.CONFIG_DIR/'settings.json',current)
    dependency_probe.cache_clear()
    return configuration(family)


def model_candidates(family):
    explicit=configuration(family).get('model_dir')
    if explicit:return [Path(explicit)]
    relatives=[]
    for entry in CATALOG[family]['entries']:
        path=entry['destination'].replace('\\','/')
        marker='/DESCARGAS_MODELOS/'
        if marker in path:
            folder=path.split(marker,1)[1].split('/')[0]
            if folder not in relatives:relatives.append(folder)
    result=[]
    for root in studio.settings()['resource_roots']:
        root=Path(root)
        for folder in relatives:
            result.extend([root/'DESCARGAS_MODELOS'/folder,root/'OPENMONTAJE-IA'/'DESCARGAS_MODELOS'/folder,root/folder])
            if root.name==folder:result.append(root)
    return list(dict.fromkeys(result))


def resolve_model(family):
    candidates=model_candidates(family)
    return next((p for p in candidates if p.is_dir()),None)


def expected_files(family,model):
    """Expected local files for this variant, not unrelated variants in its group."""
    result=[]
    for entry in CATALOG[family]['entries']:
        dest=entry['destination'].replace('\\','/')
        marker='/DESCARGAS_MODELOS/'+model.name+'/'
        if marker in dest:result.append(dest.split(marker,1)[1])
    if not result and configuration(family).get('model_dir'):
        # Explicitly moved directory: use the first catalog repository as variant.
        paths=[e['destination'].replace('\\','/').split('/DESCARGAS_MODELOS/',1)[-1] for e in CATALOG[family]['entries'] if '/DESCARGAS_MODELOS/' in e['destination'].replace('\\','/')]
        if paths:
            prefix=paths[0].split('/')[0]+'/'
            result=[p[len(prefix):] for p in paths if p.startswith(prefix)]
    return result


@functools.lru_cache(maxsize=64)
def dependency_probe(python,modules,mtime,source_dir=''):
    script='import sys; sys.path.insert(0,'+repr(source_dir)+'); import importlib.util,json; mods='+repr(list(modules))+'; print(json.dumps({m:importlib.util.find_spec(m) is not None for m in mods}))'
    try:
        result=subprocess.run([python,'-c',script],capture_output=True,text=True,timeout=15)
        if result.returncode:raise ValueError(result.stderr[-300:])
        return json.loads(result.stdout.strip().splitlines()[-1])
    except Exception:return {m:False for m in modules}


def diagnostics(family,probe=True):
    s=spec(family);cfg=configuration(family)
    result={**s,'configuration':cfg,'inference_verified':False,'problems':[]}
    if s['backend']=='comfyui':
        path=Path(cfg.get('workflow_path',''))
        result['workflow_configured']=path.is_file() and bool(cfg.get('output_node'))
        if not result['workflow_configured']:result['problems'].append('Falta workflow API compatible y nodo de salida; no basta tener los pesos.')
        if result['workflow_configured'] and probe:
            try:
                from lib.model_comfy_adapter import graph_config,validate_graph
                server=studio.settings()['comfyui_url']
                studio.local_request(server,'/system_stats',timeout=2)
                graph,node=graph_config(family,{})
                validate_graph(family,graph,node,server)
            except Exception as exc:result['problems'].append('ComfyUI/workflow: '+str(exc)[:500])
        result['ready']=result['workflow_configured'] and not result['problems']
        return result
    model=resolve_model(family);result['model_dir']=str(model) if model else None
    if model is None:result['problems'].append('No se encuentra la carpeta local del modelo en los recursos configurados.')
    missing=[];optional_missing=[]
    if model:
        if family=='kokoro':result['available_voices']=[p.stem for p in sorted((model/'voices').glob('*.pt')) if p.is_file() and p.stat().st_size]
        for relative in expected_files(family,model):
            p=model/relative
            if relative.lower().endswith(('.json','.safetensors','.bin','.pth','.pt','.onnx','.model','.pdiparams','.yml','.yaml','.py','.txt','.tiktoken')) and (not p.is_file() or not p.stat().st_size):
                (optional_missing if family=='kokoro' and relative.startswith('voices/') else missing).append(relative)
        for index in model.glob('*.index.json'):
            try:
                for filename in set(studio.read_json(index).get('weight_map',{}).values()):
                    p=(model/filename).resolve();p.relative_to(model.resolve())
                    if not p.is_file() or not p.stat().st_size:missing.append(filename)
            except (ValueError,TypeError):result['problems'].append('Índice de pesos inválido: '+index.name)
        if missing:result['problems'].append('Ficheros necesarios ausentes o vacíos: '+', '.join(sorted(set(missing))))
    result['missing_files']=sorted(set(missing))
    result['optional_missing_files']=sorted(set(optional_missing))
    python=cfg.get('python_executable') or sys.executable
    modules=tuple(s['dependencies']);mtime=Path(python).stat().st_mtime if Path(python).is_file() else 0
    available=dependency_probe(python,modules,mtime,cfg.get('source_dir','')) if probe and model is not None else {}
    result['python_executable']=python;result['dependencies']=available
    result['required_modules']=list(modules)
    if probe and model is not None and not all(available.values()):result['problems'].append('Dependencias Python ausentes: '+', '.join(m for m,ok in available.items() if not ok))
    result['ready']=model is not None and not result['problems']
    return result


class LocalModelAdapter(BaseTool):
    version='0.1.0'
    runtime=ToolRuntime.LOCAL_GPU
    tier=ToolTier.GENERATE
    determinism=Determinism.STOCHASTIC
    supports={'offline_weights':True,'automatic_weight_download':False,'isolated_native_process':True}
    user_visible_verification=['Inspect output files and review voice/image/text quality before approving production']
    provider='local_downloaded_models'
    agent_skills=[]
    resource_profile=ResourceProfile(network_required=False)
    dependencies=[]
    install_instructions='Configura carpetas de recursos y el adaptador en /studio. Usa un Python aislado con las dependencias de docs/ADAPTADORES_MODELOS_ES.md. No se descargan pesos automáticamente.'
    idempotency_key_fields=[]
    side_effects=['writes requested artifacts inside output_dir']
    input_schema={'type':'object','additionalProperties':False,'required':['output_dir'], 'properties':{
        'output_dir':{'type':'string'},'text':{'type':'string','maxLength':50000},'input_path':{'type':'string'},'reference_audio':{'type':'string'},
        'reference_text':{'type':'string'},'language':{'type':'string'},'source_language':{'type':'string'},'voice':{'type':'string'},
        'instruction':{'type':'string'},'labels':{'type':'array','items':{'type':'string'},'maxItems':100},'texts':{'type':'array','items':{'type':'string'},'maxItems':100},
        'device':{'enum':['cpu','cuda']},'max_new_tokens':{'type':'integer','minimum':1,'maximum':8192},'speed':{'type':'number','minimum':0.5,'maximum':2},
        'threshold':{'type':'number','minimum':0,'maximum':1},'timeout':{'type':'integer','minimum':10,'maximum':14400},
        'workflow_json':{'type':'object'},'output_node':{'type':'string'},'bindings':{'type':'object'},'resume_prompt_id':{'type':'string'}}}

    def get_status(self):
        return ToolStatus.AVAILABLE if diagnostics(self.family)['ready'] else ToolStatus.UNAVAILABLE

    def get_info(self):
        result=super().get_info();result['adapter']=diagnostics(self.family);result['usage_manual']='docs/ADAPTADORES_MODELOS_ES.md'
        return result

    def estimate_cost(self,inputs):return 0.0

    def execute(self,inputs):
        from jsonschema import validate
        try:
            validate(inputs,self.input_schema)
            output=Path(inputs['output_dir']).resolve();output.mkdir(parents=True,exist_ok=True)
            info=diagnostics(self.family)
            if not info['ready']:return ToolResult(success=False,error='; '.join(info['problems']),data={'adapter':info})
            if info['backend']=='comfyui':
                from lib.model_comfy_adapter import execute_workflow
                data=execute_workflow(self.family,inputs,output)
            else:
                request=output/('adapter-'+self.family+'-request.json');response=output/('adapter-'+self.family+'-response.json')
                response.unlink(missing_ok=True)
                studio.save_json(request,{'family':self.family,'model_dir':info['model_dir'],'inputs':inputs,'output_dir':str(output),'source_dir':configuration(self.family).get('source_dir','')})
                env={**os.environ,'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_DATASETS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1','TOKENIZERS_PARALLELISM':'false'}
                if inputs.get('device','cpu')=='cpu':env['CUDA_VISIBLE_DEVICES']=''
                worker=Path(__file__).with_name('model_adapter_worker.py')
                result=subprocess.run([info['python_executable'],str(worker),str(request),str(response)],env=env,capture_output=True,text=True,timeout=inputs.get('timeout',1800))
                if not response.is_file():raise RuntimeError('El runtime no devolvió un resultado: '+result.stderr[-1000:])
                data=studio.read_json(response)
                if not data.get('success'):raise RuntimeError(data.get('error','Inferencia fallida'))
                if result.returncode:raise RuntimeError('El proceso terminó con error después de escribir la respuesta')
            for filename in data.get('outputs',[]):
                p=Path(filename).resolve();p.relative_to(output)
                if not p.is_file() or not p.stat().st_size:raise ValueError('Salida declarada ausente o vacía')
            if not data.get('outputs'):raise ValueError('El adaptador no produjo archivos')
            return ToolResult(success=True,data={**data,'family':self.family,'cost_usd':0})
        except ComfyUIError as exc:
            return ToolResult(success=False,error=str(exc),data={'prompt_id':exc.prompt_id,'family':self.family,'resume_supported':bool(exc.prompt_id)})
        except subprocess.TimeoutExpired:
            return ToolResult(success=False,error='Timeout del proceso local. No se cambia de modelo ni se descarga una alternativa.')
        except Exception as exc:return ToolResult(success=False,error=str(exc)[:1800])
