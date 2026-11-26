"""Bounded GLB container/JSON inspection; never launches Blender or decodes mesh payload."""
import hashlib
import json
import math
from pathlib import Path
import struct


def inspect(path):
    path=Path(path)
    if not path.is_file() or path.suffix.lower()!='.glb':raise ValueError('Selecciona un GLB local existente')
    stat=path.stat()
    if not 20<=stat.st_size<=64*1024*1024:raise ValueError('Inspección GLB limitada a64MB')
    chunks=[];document=None;json_hash=None
    with path.open('rb') as stream:
        raw_header=stream.read(12)
        if len(raw_header)!=12:raise ValueError('Cabecera GLB truncada')
        magic,version,total=struct.unpack('<4sII',raw_header)
        if magic!=b'glTF' or version!=2 or total!=stat.st_size:raise ValueError('Cabecera/longitud GLB2 no válidas')
        offset=12
        while offset<total:
            if total-offset<8:raise ValueError('Cabecera de chunk GLB truncada')
            header=stream.read(8)
            if len(header)!=8:raise ValueError('Chunk GLB truncado')
            length,kind=struct.unpack('<II',header);offset+=8
            if length%4 or length>total-offset:raise ValueError('Chunk GLB fuera de límites/alineación')
            if not chunks and kind!=0x4e4f534a:raise ValueError('El primer chunk debe ser JSON')
            if kind==0x4e4f534a:
                if document is not None or length>4*1024*1024:raise ValueError('JSON GLB duplicado o superior a4MB')
                raw=stream.read(length);json_hash=hashlib.sha256(raw).hexdigest();document=json.loads(raw.decode('utf-8').rstrip(' '))
            else:stream.seek(length,1)
            chunks.append(dict(type=hex(kind),bytes=length));offset+=length
    if not isinstance(document,dict) or document.get('asset',{}).get('version')!='2.0':raise ValueError('JSON glTF2 no reconocido')
    nodes=document.get('nodes',[])
    if not isinstance(nodes,list) or len(nodes)>10000:raise ValueError('Grafo de nodos fuera de presupuesto')
    checked=[]
    def vector(value,count):
        if not isinstance(value,list) or len(value)!=count or any(type(x) not in (int,float) or not math.isfinite(x) for x in value):raise ValueError('Transformación GLB no finita o de longitud incorrecta')
        return value
    for index,node in enumerate(nodes):
        if not isinstance(node,dict):raise ValueError('Nodo GLB debe ser objeto')
        if 'matrix' in node:
            if any(k in node for k in ('translation','rotation','scale')):raise ValueError('Nodo no puede mezclar matriz y TRS')
            value=dict(matrix_column_major=vector(node['matrix'],16))
        else:
            scale=vector(node.get('scale',[1,1,1]),3)
            value=dict(translation=vector(node.get('translation',[0,0,0]),3),
                       rotation_xyzw=vector(node.get('rotation',[0,0,0,1]),4),scale=scale,
                       non_uniform_scale=len(set(scale))>1,negative_or_zero_scale=any(s<=0 for s in scale))
        children=node.get('children',[])
        if not isinstance(children,list) or any(type(c) is not int or not 0<=c<len(nodes) for c in children):raise ValueError('Índice hijo fuera del grafo')
        checked.append(dict(index=index,name=str(node.get('name',''))[:256],mesh=node.get('mesh'),children=children,**value))
    # Iterative depth-first check avoids recursive stack exhaustion on malformed files.
    states=[0]*len(nodes)
    for node in range(len(nodes)):
        stack=[(node,False)]
        while stack:
            current,exit=stack.pop()
            if exit:states[current]=2;continue
            if states[current]==1:raise ValueError('Ciclo en el grafo GLB')
            if states[current]==2:continue
            states[current]=1;stack.append((current,True));stack.extend((c,False) for c in checked[current]['children'])
    materials=[]
    entries=document.get('materials',[])
    if not isinstance(entries,list) or len(entries)>1000:raise ValueError('Materiales fuera del presupuesto1000')
    for item in entries:
        if not isinstance(item,dict):raise ValueError('Material GLB debe ser objeto')
        pbr=item.get('pbrMetallicRoughness',{})
        if not isinstance(pbr,dict):raise ValueError('PBR debe ser objeto')
        for key in ('metallicFactor','roughnessFactor'):
            value=pbr.get(key,1)
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:raise ValueError('Factor PBR fuera de limites')
        materials.append(dict(name=str(item.get('name',''))[:256],base_color_factor=vector(pbr.get('baseColorFactor',[1,1,1,1]),4),
            metallic_factor=pbr.get('metallicFactor',1),roughness_factor=pbr.get('roughnessFactor',1),
            alpha_mode=item.get('alphaMode','OPAQUE'),textures_declared=any(k.endswith('Texture') for k in item) or any(k.endswith('Texture') for k in pbr)))
    external=sum(1 for section in ('buffers','images') for item in document.get(section,[]) if item.get('uri') and not item['uri'].startswith('data:'))
    after=path.stat()
    if (stat.st_size,stat.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('GLB cambió durante inspección')
    return dict(contract='glb-metadata-inspection-v1',bytes=total,chunks=chunks,json_sha256=json_hash,
        nodes=checked,mesh_count=len(document.get('meshes',[])),material_count=len(materials),materials=materials,
        animations=len(document.get('animations',[])),external_resources_not_read=external,
        required_extensions=document.get('extensionsRequired',[]),
        axes='glTF2 right-handed Y-up; no conversion applied',unit_hint='glTF convention meters; authored scale not verified',
        full_file_hashed=False,mesh_payload_decoded=False,blender_started=False,import_validated=False,
        limitations=['JSON transforms/PBR declarations only; no world bounds, visual quality or texture verification.',
                     'Compressed meshes/extensions need a compatible importer; no remote resources fetched.'])
