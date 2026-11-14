"""Execute an explicitly bound ComfyUI API graph for a downloaded family."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from lib import production_studio as studio
from tools._comfyui.client import ComfyUIClient,ComfyUIError


def graph_config(family,inputs):
    from lib.model_adapters import configuration
    cfg=configuration(family)
    graph=inputs.get('workflow_json')
    if graph is None:
        path=Path(cfg.get('workflow_path',''))
        if not path.is_file() or path.stat().st_size>2000000:raise ValueError('Falta un workflow API compatible de menos de 2 MB')
        graph=studio.read_json(path)
    graph=json.loads(json.dumps(graph))
    if not isinstance(graph,dict) or not graph or len(graph)>200:raise ValueError('Workflow API inválido; exporta formato API, no el lienzo de la interfaz')
    for key,node in graph.items():
        if not isinstance(node,dict) or not isinstance(node.get('class_type'),str) or not isinstance(node.get('inputs'),dict):raise ValueError('Nodo API inválido: '+str(key))
    for node_id,patch in inputs.get('bindings',{}).items():
        if node_id not in graph or not isinstance(patch,dict):raise ValueError('Binding apunta a un nodo desconocido')
        for field,value in patch.items():
            if field not in graph[node_id]['inputs']:raise ValueError('Binding apunta a un campo desconocido')
            graph[node_id]['inputs'][field]=value
    output=str(inputs.get('output_node') or cfg.get('output_node') or '')
    if output not in graph:raise ValueError('Falta el nodo de salida del workflow')
    return graph,output


def validate_graph(family,graph,output,server):
    from lib.model_adapters import CATALOG
    files={e['path'].replace('\\','/').split('/')[-1] for e in CATALOG[family]['entries'] if e['path'].endswith(('.safetensors','.pth','.pt','.bin','.onnx','.ckpt'))}
    if family=='lama':files|={'big-lama.pt','big-lama','lama'}
    strings=[]
    def walk(value):
        if isinstance(value,str):strings.append(value.replace('\\','/').split('/')[-1])
        elif isinstance(value,dict):
            for v in value.values():walk(v)
        elif isinstance(value,list):
            for v in value:walk(v)
    for node in graph.values():walk(node['inputs'])
    if not files.intersection(strings):raise ValueError('El workflow no referencia pesos de la familia seleccionada: '+family)
    infos={}
    for name in sorted({node['class_type'] for node in graph.values()}):
        data=studio.local_request(server,'/object_info/'+quote(name,safe=''),timeout=10)
        if name not in data:raise ValueError('Falta el nodo ComfyUI: '+name)
        info=data[name]
        if info.get('api_node') or str(info.get('category','')).casefold().startswith(('api/','api node','partner/')):raise ValueError('Nodo de servicio externo no autorizado por presupuesto cero: '+name)
        infos[name]=info
    for node in graph.values():
        fields=infos[node['class_type']].get('input',{})
        definitions={**fields.get('required',{}),**fields.get('optional',{})}
        for key,value in node['inputs'].items():
            definition=definitions.get(key)
            # Combo lists advertise the model names actually registered in ComfyUI.
            if definition and isinstance(definition[0],list) and isinstance(value,str) and value not in definition[0]:raise ValueError('Valor/modelo no registrado en '+node['class_type']+'.'+key+': '+value)
    if not infos[graph[output]['class_type']].get('output_node',False):raise ValueError('El nodo elegido no es un nodo de salida ComfyUI')


def execute_workflow(family,inputs,output):
    server=studio.settings()['comfyui_url'];graph,node=graph_config(family,inputs)
    validate_graph(family,graph,node,server)
    digest=hashlib.sha256(json.dumps(graph,sort_keys=True).encode()).hexdigest()
    client=ComfyUIClient(server_url=server);ledger=output/('comfy-'+family+'-job.json')
    resume=inputs.get('resume_prompt_id')
    if resume:
        saved=studio.read_json(ledger,{})
        if saved.get('prompt_id')!=resume or saved.get('workflow_sha256')!=digest:raise ValueError('La reanudación no coincide con el workflow registrado')
        prompt_id=resume
    else:
        prompt_id=client.submit(graph)
        studio.save_json(ledger,{'family':family,'prompt_id':prompt_id,'workflow_sha256':digest,'output_node':node,'server':server,'submitted_at':studio.now(),'status':'submitted'})
    try:
        entry=client.poll(prompt_id,timeout=inputs.get('timeout',1800),interval=2)
        record=entry.get('outputs',{}).get(node,{})
        items=record.get('images') or record.get('video') or record.get('gifs') or record.get('audio') or []
        if not items:raise ValueError('El nodo no produjo medios descargables')
        paths=[]
        for i,item in enumerate(items):
            suffix=Path(item['filename']).suffix.lower()
            if suffix not in ('.png','.jpg','.jpeg','.webp','.mp4','.webm','.gif','.wav','.mp3','.flac','.ogg'):raise ValueError('Formato de salida no admitido: '+suffix)
            path=output/(family+'-'+str(i)+suffix)
            client.download(item['filename'],item.get('subfolder',''),path,item.get('type','output'));paths.append(str(path))
        result={'success':True,'outputs':paths,'prompt_id':prompt_id,'workflow_sha256':digest}
        studio.save_json(ledger,{**studio.read_json(ledger),'status':'completed','outputs':paths})
        return result
    except ComfyUIError as exc:
        raise ComfyUIError(str(exc),prompt_id=prompt_id) from exc
