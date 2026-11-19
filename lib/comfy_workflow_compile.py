"""Compile local ComfyUI canvases using the installed server's node contracts.

Pure transformation: never submits a prompt, installs nodes or downloads weights.
Ambiguous widgets/bypasses fail rather than silently changing a model or prompt.
"""
from copy import deepcopy

PRIMITIVES={'INT','FLOAT','BOOLEAN','STRING','COMBO'}
NOTES={'Note','MarkdownNote'}
MISSING=object()


def link_table(graph):
    result={}
    for link in graph.get('links',[]):
        if isinstance(link,list):
            key,origin,slot,target,target_slot,*_=link
        else:
            key=link['id'];origin=link['origin_id'];slot=link['origin_slot'];target=link['target_id'];target_slot=link['target_slot']
        result[str(key)]=(str(origin),int(slot),str(target),int(target_slot))
    return result


def widget_values(node,info):
    fields=info.get('input',{})
    definitions={**fields.get('required',{}),**fields.get('optional',{})}
    named=node.get('widgets_values_named')
    raw=node.get('widgets_values',[])
    if isinstance(raw,dict):named=raw
    if named is not None:
        return {k:deepcopy(v) for k,v in named.items() if k in definitions}
    names=[]
    order=info.get('input_order',{})
    ordered=[*order.get('required',fields.get('required',{})),*order.get('optional',fields.get('optional',{}))]
    for key in ordered:
        definition=definitions[key];kind=definition[0];options=definition[1] if len(definition)>1 and isinstance(definition[1],dict) else {}
        if options.get('forceInput'):continue
        if isinstance(kind,list) or isinstance(kind,str) and kind in PRIMITIVES:names.append(key)
    values={};index=0
    for key in names:
        if index>=len(raw):
            # Linked widget values are normally retained, but optional widgets
            # may be absent in older saved canvases. Required values stay absent.
            break
        values[key]=deepcopy(raw[index]);index+=1
        if key in ('seed','noise_seed') and index<len(raw) and raw[index] in ('fixed','increment','decrement','randomize'):
            index+=1
    extra=raw[index:]
    if node['type']=='LoadImage' and extra==['image']:extra=[]
    if node['type']=='LoadAudio' and all(v is None for v in extra):extra=[]
    if node['type']=='PrimitiveInt' and extra in (['fixed'],['increment'],['decrement'],['randomize']):extra=[]
    if extra:raise ValueError('Widgets ambiguos en '+str(node['id'])+' / '+node['type']+'; exporta API desde esa versión de ComfyUI')
    return values


def compile_canvas(canvas,object_info,output_node=None):
    """Resolve subgraphs, reroutes and bypasses; retain one output's ancestry."""
    if not isinstance(canvas,dict) or not isinstance(canvas.get('nodes'),list):raise ValueError('Lienzo ComfyUI inválido')
    definitions={g['id']:g for g in canvas.get('definitions',{}).get('subgraphs',[])}
    flat={};cache={};resolving=set();contexts={}

    def context(graph,prefix='',parent=None,instance=None):
        ctx={'graph':graph,'prefix':prefix,'parent':parent,'instance':instance,
             'nodes':{str(n['id']):n for n in graph['nodes']},'links':link_table(graph)}
        contexts[prefix]=ctx
        return ctx

    root=context(canvas)

    def child(ctx,node):
        prefix=ctx['prefix']+str(node['id'])+':'
        return contexts.get(prefix) or context(definitions[node['type']],prefix,ctx,node)

    def linked(ctx,port):
        link=port.get('link')
        if link is None:return MISSING
        item=ctx['links'].get(str(link))
        if item is None:raise ValueError('Enlace ausente: '+str(link))
        return endpoint(ctx,item[0],item[1])

    def external(ctx,slot):
        specs=ctx['graph'].get('inputs',[])
        if slot>=len(specs):raise ValueError('Entrada de subgrafo ausente')
        spec=specs[slot];instance=ctx['instance'];parent=ctx['parent']
        for port in instance.get('inputs',[]):
            if port['name']==spec['name']:
                value=linked(parent,port)
                if value is not MISSING:return value
        values=instance.get('widgets_values',[])
        named=instance.get('widgets_values_named')
        if isinstance(values,dict):named=values
        if named is not None:return deepcopy(named.get(spec['name'],MISSING)) if spec['name'] in named else MISSING
        proxy=instance.get('properties',{}).get('proxyWidgets',[])
        if values and proxy:
            if len(values)!=len(proxy):raise ValueError('Proxy widgets ambiguos en '+str(instance['id']))
            for index,(nodeid,field) in enumerate(proxy):
                for lid in spec.get('linkIds',[]):
                    edge=ctx['links'].get(str(lid))
                    if edge and edge[2]==str(nodeid):
                        target=ctx['nodes'][str(nodeid)]
                        if target.get('inputs',[])[edge[3]]['name']==field:return deepcopy(values[index])
        elif values:
            widgets=[p for p in specs if p.get('type') in PRIMITIVES]
            if len(values)!=len(widgets):raise ValueError('Entradas expuestas ambiguas en '+str(instance['id']))
            for index,p in enumerate(widgets):
                if p['name']==spec['name']:return deepcopy(values[index])
        return MISSING

    def endpoint(ctx,nodeid,slot):
        token=(ctx['prefix'],str(nodeid),slot)
        if token in cache:return cache[token]
        if token in resolving:raise ValueError('Ciclo en el workflow')
        resolving.add(token)
        try:
            if ctx['parent'] is not None and str(nodeid)==str(ctx['graph'].get('inputNode',{}).get('id',-10)):
                value=external(ctx,slot)
            else:
                node=ctx['nodes'].get(str(nodeid))
                if node is None:raise ValueError('Nodo de origen ausente: '+str(nodeid))
                mode=node.get('mode',0);kind=node['type']
                if mode==2:raise ValueError('La salida depende de un nodo desactivado: '+str(nodeid))
                if mode==4 or kind in ('Reroute','PrimitiveNode'):
                    ports=node.get('inputs',[])
                    if kind=='PrimitiveNode':
                        raw=node.get('widgets_values',[])
                        if not raw:raise ValueError('PrimitiveNode sin valor')
                        value=deepcopy(raw[0])
                    else:
                        output_type=node.get('outputs',[{}])[slot].get('type')
                        matches=[p for p in ports if p.get('link') is not None and (p.get('type')==output_type or kind=='Reroute')]
                        if len(matches)!=1:raise ValueError('Bypass ambiguo en '+str(nodeid))
                        value=linked(ctx,matches[0])
                elif kind in definitions:
                    sub=child(ctx,node);outputs=sub['graph'].get('outputs',[])
                    if slot>=len(outputs):raise ValueError('Salida de subgrafo ausente')
                    edges=[sub['links'][str(l)] for l in outputs[slot].get('linkIds',[]) if str(l) in sub['links']]
                    sources={(e[0],e[1]) for e in edges}
                    if len(sources)!=1:raise ValueError('Salida de subgrafo ambigua')
                    origin,output_slot=next(iter(sources));value=endpoint(sub,origin,output_slot)
                elif kind=='ComfySwitchNode':
                    ports={p['name']:p for p in node.get('inputs',[])}
                    switch=linked(ctx,ports.get('switch',{}))
                    if switch is MISSING:switch=widget_values(node,object_info[kind]).get('switch')
                    if isinstance(switch,list) and switch[0] in flat and flat[switch[0]]['class_type']=='PrimitiveBoolean':switch=flat[switch[0]]['inputs'].get('value')
                    if type(switch) is not bool:raise ValueError('Switch dinámico: exporta su workflow API o fija la selección antes de preparar')
                    port=ports.get('on_true' if switch else 'on_false')
                    if port is None:raise ValueError('Falta la rama seleccionada del switch')
                    value=linked(ctx,port)
                    if value is MISSING:raise ValueError('La rama seleccionada del switch no tiene entrada')
                else:
                    build(ctx,node);value=[ctx['prefix']+str(nodeid),slot]
            cache[token]=value
            return value
        finally:resolving.remove(token)

    def build(ctx,node):
        key=ctx['prefix']+str(node['id'])
        if key in flat:return
        kind=node['type'];info=object_info.get(kind)
        if info is None:raise ValueError('Falta el nodo ComfyUI: '+kind)
        if info.get('api_node') or str(info.get('category','')).lower().startswith(('api/','api node','partner/')):raise ValueError('Nodo de servicio externo no permitido: '+kind)
        values=widget_values(node,info)
        # Install a placeholder to make any recursive reference detectable by
        # endpoint's cycle guard rather than infinitely recursing.
        flat[key]={'class_type':kind,'inputs':values,'_meta':{'title':node.get('title',kind)}}
        for port in node.get('inputs',[]):
            value=linked(ctx,port)
            if value is not MISSING:values[port['name']]=value

    outputs=[n for n in canvas['nodes'] if n.get('mode',0)==0 and object_info.get(n['type'],{}).get('output_node')]
    if output_node is None:
        if len(outputs)!=1:raise ValueError('Selecciona un único nodo de salida: '+', '.join(str(n['id']) for n in outputs))
        output_node=str(outputs[0]['id'])
    selected=root['nodes'].get(str(output_node))
    if selected is None or selected not in outputs:raise ValueError('Nodo de salida no activo o no exportable')
    endpoint(root,str(output_node),0)
    reachable=set()
    def visit(key):
        if key in reachable:return
        reachable.add(key)
        for value in flat[key]['inputs'].values():
            if isinstance(value,list) and len(value)==2 and isinstance(value[0],str) and value[0] in flat and isinstance(value[1],int):visit(value[0])
    visit(str(output_node));flat={key:value for key,value in flat.items() if key in reachable}
    if len(flat)>200:raise ValueError('Workflow expandido demasiado grande')
    return flat,str(output_node)


def node_types(canvas):
    """Node schemas needed for preparation, without touching a ComfyUI queue."""
    subs=canvas.get('definitions',{}).get('subgraphs',[])
    ids={g['id'] for g in subs}
    return sorted({n['type'] for graph in [canvas,*subs] for n in graph.get('nodes',[])
                   if n['type'] not in ids|NOTES|{'Reroute','PrimitiveNode'} and n.get('mode',0)!=2})
