"""Explicit local WAN workflow choices. No model downloads or silent fallback."""
from copy import deepcopy
from lib import production_studio as studio

PRESETS={
 'wan22-14b-i2v-4step':{'label':'Wan 2.2 · 14B · imagen a video · 4 pasos','workflow':'wan22-i2v-4step.json','output_node':'108',
   'required_models':['wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors','wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors','wan_2.1_vae.safetensors','umt5_xxl_fp8_e4m3fn_scaled.safetensors','wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors','wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors'],
   'note':'Requiere server_image: nombre de una imagen ya cargada en ComfyUI. La prueba manual I2V no valida automáticamente este perfil de cuatro pasos.'},
 'wan22-5b-t2v':{'label':'Wan 2.2 · 5B · texto a video','workflow':'wan22-5b-t2v.json','output_node':'11',
   'required_models':['wan2.2_ti2v_5B_fp16.safetensors','wan2.2_vae.safetensors','umt5_xxl_fp8_e4m3fn_scaled.safetensors'],
   'note':'Ruta 5B con offloading de ComfyUI. Requiere comprobar memoria, nodos y resultado en el equipo.'},
 'wan22-14b-t2v-4step':{'label':'Wan 2.2 · 14B · texto a video · 4 pasos','workflow':'wan22-t2v-4step.json','output_node':'16',
   'required_models':['wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors','wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors','wan_2.1_vae.safetensors','umt5_xxl_fp8_e4m3fn_scaled.safetensors','wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors','wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors'],
   'note':'Perfil 14B existente; no se considera validado para una GPU de 8 GB.'}}


def config(name):
    if name not in PRESETS:raise ValueError('Perfil WAN desconocido')
    item=PRESETS[name]
    return {'workflow_path':str(studio.REPO_ROOT/'tools/_comfyui/workflows'/item['workflow']),'output_node':item['output_node'],'preset':name}


def catalog():return [{'id':name,**deepcopy(item)} for name,item in PRESETS.items()]


def apply_parameters(graph,preset,inputs):
    """Technical input binding, not prompt authoring or creative selection."""
    if preset not in PRESETS:raise ValueError('Perfil WAN desconocido')
    graph=deepcopy(graph)
    positive,negative,latent,sampler,video={
        'wan22-5b-t2v':('4','5','7','8','10'),
        'wan22-14b-t2v-4step':('2','3','11','12','15'),
        'wan22-14b-i2v-4step':('93','89','98','86','94'),
    }[preset]
    if preset=='wan22-14b-i2v-4step':
        image=inputs.get('server_image')
        if not isinstance(image,str) or not image.strip():raise ValueError('Indica server_image: una imagen ya cargada en ComfyUI')
        graph['97']['inputs']['image']=image
    if 'text' in inputs:graph[positive]['inputs']['text']=inputs['text']
    if 'negative_prompt' in inputs:graph[negative]['inputs']['text']=inputs['negative_prompt']
    for source,target in [('width','width'),('height','height'),('frames','length')]:
        if source in inputs:graph[latent]['inputs'][target]=inputs[source]
    if 'steps' in inputs:
        if preset!='wan22-5b-t2v' and inputs['steps']!=4:raise ValueError('El perfil LoRA 14B está fijado a cuatro pasos')
        graph[sampler]['inputs']['steps']=inputs['steps']
    if 'seed' in inputs:graph[sampler]['inputs']['seed' if preset=='wan22-5b-t2v' else 'noise_seed']=inputs['seed']
    if 'fps' in inputs:graph[video]['inputs']['fps']=inputs['fps']
    width=graph[latent]['inputs']['width'];height=graph[latent]['inputs']['height'];frames=graph[latent]['inputs']['length']
    if width%32 or height%32:raise ValueError('El perfil WAN requiere ancho y alto múltiplos de 32')
    if frames%4!=1:raise ValueError('El número de cuadros debe tener la forma 4n+1')
    if not graph[positive]['inputs']['text'].strip():raise ValueError('Escribe el prompt antes de ejecutar WAN')
    return graph
