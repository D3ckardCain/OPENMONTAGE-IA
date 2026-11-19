"""Complete preparation recipes for the downloaded catalog; no inference here."""
import json
from pathlib import Path
from lib import production_studio as studio
from lib.comfy_workflow_compile import compile_canvas

TEMPLATES=Path(__file__).resolve().parents[1]/'tools/_comfyui/reference_templates'
PARAMETERS={'text','negative_prompt','width','height','frames','steps','seed','fps','seconds','server_image','server_audio','server_image_2'}
# Explicit semantic bindings, reviewed against the pinned source canvases.
# Output ancestry pruning removes unused alternative branches before binding.
TEXT={
 'qwen-edit':('170:151','prompt'),'qwen-image':('76:6','text'),
 'flux-klein':('75:74','text'),'z-image':('57:27','text'),
 'wan-camera':('81','text'),'wan-control':('99','text'),'wan-s2v':('6','text'),
 'ltx-legacy':('6','text'),'ltx23':('267:266','value'),'ltx25':('405:376','value'),
 'hunyuan15':('44','text'),'h3':('140:131','prompt'),
 'kandinsky':('12:7','text'),'acestep':('94','tags'),'mochi':('6','text'),
 'cosmos':('42','text'),'wan-vace':('92','text'),'framepack':('47','text')}
OUTPUTS={'qwen-edit':'9','qwen-image':'60','flux-klein':'9','z-image':'9','wan-camera':'106',
 'wan-control':'98','wan-s2v':'113','ltx-legacy':'79','ltx23':'75','ltx25':'75',
 'hunyuan15':'102','h3':'92','kandinsky':'11','acestep':'107','mochi':'42',
 'cosmos':'69','wan-vace':'17','framepack':'23'}
REQUIRED={
 'wan-camera':['text','input_path','camera_path'],'wan-control':['text','control_video'],
 'wan-s2v':['text','input_path','reference_audio'],'framepack':['text','input_path'],
 'longcat':['text'],'longcat-avatar':['text','input_path','reference_audio'],
 'cogvideo':['text'],'dwpose':['input_path'],'lama':['input_path','mask_path'],'magihuman':['text'],
 'faster-whisper':['input_path'],'parakeet':['input_path'],'silero':['input_path'],
 'minilm':['text'],'siglip':['input_path','labels'],'grounding-dino':['input_path','text'],
 'florence':['input_path'],'birefnet':['input_path'],'qwen3':['text'],
 'qwen-vl':['input_path','text'],'smolvlm':['input_path','text'],'depth':['input_path'],
 'ocr-latin':['input_path'],'ocr-det':['input_path'],'m2m100':['text','source_language','language'],
 'kokoro':['text','voice'],'qwen-tts':['text','voice','language'],
 'voice-design':['text','instruction','language'],'aligner':['input_path','text','language'],
 'chatterbox':['text'],'cosyvoice':['text','reference_audio','reference_text'],
}


def validate_bindings(bindings):
    if not isinstance(bindings,dict) or set(bindings)-PARAMETERS:raise ValueError('Parámetros de workflow desconocidos')
    for parameter,targets in bindings.items():
        if not isinstance(targets,list) or not 1<=len(targets)<=20:raise ValueError('Indica destinos para '+parameter)
        for target in targets:
            if not isinstance(target,dict) or set(target)!={'node','field'} or not all(isinstance(v,str) and 0<len(v)<=200 for v in target.values()):raise ValueError('Destino de parámetro inválido')
    return bindings


def recipes():
    from lib.model_adapters import CATALOG,spec
    manifest=json.loads((TEMPLATES/'manifest.json').read_text(encoding='utf-8'))
    refs={r['family']:r for r in manifest['templates']}
    rows=[]
    for family,group in CATALOG.items():
        native=spec(family)['backend']=='native'
        ref=refs.get(family) if not native else None
        rows.append({'family':family,'title':group.get('title',family),'engine':spec(family)['backend'],
            'recipe_kind':'isolated_native_workflow' if native else 'wan_api_preset' if family=='wan' else 'canvas_compiler',
            'preparation_implemented':native or family=='wan' or family in OUTPUTS,
            'required_inputs':[*REQUIRED.get(family,['text']),'output_dir'],
            'reference':ref,'output_node':OUTPUTS.get(family),
            'variant_review_required':bool(ref and ref.get('variant_review_required')),
            'runtime_requirements':spec(family)['dependencies'],
            'platform_note':'Motor original NCCL: Linux/WSL y CUDA; requiere runtime separado' if family in ('longcat','longcat-avatar','magihuman') else None,
            'inference_verified':False,'downloads_started':False})
    return rows


def default_bindings(family,graph):
    bindings={}
    def add(param,node,field):
        if node in graph and field in graph[node]['inputs']:
            bindings.setdefault(param,[]).append({'node':node,'field':field})
    if family in TEXT:add('text',*TEXT[family])
    for node_id,node in graph.items():
        kind=node['class_type'];values=node['inputs'];title=node.get('_meta',{}).get('title','').lower()
        if 'negative' in title and 'text' in values:add('negative_prompt',node_id,'text')
        for parameter,field in [('seed','seed'),('seed','noise_seed')]:
            if not isinstance(values.get(field),list):add(parameter,node_id,field)
        if kind in ('KSampler','KSamplerAdvanced','SamplerCustom','BasicScheduler','FramePackSampler','Wan2_2VaceFunSampler'):add('steps',node_id,'steps')
        if kind.startswith('Empty') or kind in ('CosmosImageToVideoLatent','WanImageToVideo','WanCameraImageToVideo','HunyuanVideo15ImageToVideo'):
            for field in ('width','height'):add(field,node_id,field)
            add('frames',node_id,'length')
        if kind in ('CreateVideo','VHS_VideoCombine'):add('fps',node_id,'fps' if 'fps' in values else 'frame_rate')
    images=[key for key,n in graph.items() if n['class_type']=='LoadImage']
    audio=[key for key,n in graph.items() if n['class_type']=='LoadAudio']
    if len(images)==1:add('server_image',images[0],'image')
    if len(audio)==1:add('server_audio',audio[0],'audio')
    # Multiple image roles must be explicitly assigned, never guessed.
    return bindings


def prepare(family,data):
    """Read node schemas and save an API graph; never touches /prompt or queues."""
    from lib.model_adapters import CATALOG,configure,spec
    from lib.model_comfy_adapter import validate_graph
    if family not in CATALOG:raise ValueError('Familia desconocida')
    if spec(family)['backend']=='native' or family=='wan':return {'family':family,'prepared':True,'requires_inference_test':True,'generation_started':False}
    if set(data)-{'output_node','model_map','parameter_bindings'}:raise ValueError('Configuración de preparación desconocida')
    ref=next(r for r in recipes() if r['family']==family)['reference']
    canvas=json.loads((TEMPLATES/ref['file']).read_text(encoding='utf-8'))
    server=studio.settings()['comfyui_url']
    infos=studio.local_request(server,'/object_info',timeout=30)
    graph,output=compile_canvas(canvas,infos,str(data.get('output_node') or OUTPUTS[family]))
    model_map=data.get('model_map',{})
    if not isinstance(model_map,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in model_map.items()):raise ValueError('model_map debe relacionar nombres exactos de pesos locales')
    # Replacement applies only to model-name fields, never prompts/filenames.
    used=set()
    for node in graph.values():
        for field,value in node['inputs'].items():
            if isinstance(value,str) and value in model_map and (field.endswith(('_name','_path')) or field in ('model','model_name','checkpoint','ckpt_name')):
                node['inputs'][field]=model_map[value];used.add(value)
    if set(model_map)-used:raise ValueError('Hay pesos de model_map que no aparecen en esta rama del workflow')
    bindings=data.get('parameter_bindings',default_bindings(family,graph));validate_bindings(bindings)
    for targets in bindings.values():
        for target in targets:
            if target['node'] not in graph or target['field'] not in graph[target['node']]['inputs']:raise ValueError('Binding fuera del workflow preparado')
    if 'text' not in bindings:raise ValueError('No se encontró el binding de texto; especifica parameter_bindings')
    validate_graph(family,graph,output,server,object_info=infos,strict=True)
    path=studio.CONFIG_DIR/'prepared_workflows'/(family+'.api.json')
    studio.save_json(path,graph)
    configure(family,{'workflow_path':str(path.resolve()),'output_node':output,'parameter_bindings':bindings})
    report={'family':family,'prepared':True,'generation_started':False,'inference_verified':False,
        'workflow_path':str(path),'output_node':output,'nodes':len(graph),'parameter_bindings':bindings,
        'source':ref,'requires_inference_test':True}
    studio.save_json(path.with_suffix('.preparation.json'),report)
    return report
