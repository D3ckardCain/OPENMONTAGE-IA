"""Align a static layer's existing normalized rectangle; no new canvas."""


def apply(edl,data):
    if data.get('operation')!='layer_align':return False
    from lib import studio_editor as edit
    if set(data)-{'operation','revision','id','horizontal','vertical','margin'}:raise ValueError('Parámetros de alineación desconocidos')
    layer=edit._item(edl.get('layers',[]),data['id'])
    if layer.get('locked'):raise edit.Conflict('Capa bloqueada')
    if any(layer.get(k) for k in ('motion','position_keyframes','transform_keyframes')):raise ValueError('Alineación de caja estática: conserva la animación y revísala antes de moverla')
    horizontal=data.get('horizontal','keep');vertical=data.get('vertical','keep');margin=edit.number(data.get('margin',0),0,.25)
    if horizontal not in ('keep','left','center','right') or vertical not in ('keep','top','middle','bottom'):raise ValueError('Alineación horizontal/vertical desconocida')
    if horizontal=='keep' and vertical=='keep':raise ValueError('Selecciona al menos un eje de alineación')
    if horizontal!='keep':
        if layer['width']+2*margin>1+1e-9:raise ValueError('La capa no cabe en el margen horizontal elegido')
        layer['x']={'left':margin,'center':(1-layer['width'])/2,'right':1-margin-layer['width']}[horizontal]
    if vertical!='keep':
        if layer['height']+2*margin>1+1e-9:raise ValueError('La capa no cabe en el margen vertical elegido')
        layer['y']={'top':margin,'middle':(1-layer['height'])/2,'bottom':1-margin-layer['height']}[vertical]
    return True
