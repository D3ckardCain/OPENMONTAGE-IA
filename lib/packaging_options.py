"""Project-local editorial title and thumbnail concepts; no image generation."""
from lib import production_studio as studio
from lib.channel_dossiers import _digest


def _path(pid):
    return studio.project_path(pid)/'artifacts/packaging_options.json'


def read(pid):
    path=_path(pid)
    if path.is_symlink():raise ValueError('Opciones de título y miniatura alteradas')
    record=studio.read_json(path)
    if record is None:
        return {'status':'empty','revision':None,'selected_id':None,'options':[],
                'limits':'Conceptos editoriales. Vista de texto, sin imagen creada ni predicción de clics.'}
    if (not isinstance(record,dict) or record.get('project_id')!=pid
            or record.get('revision')!=_digest({k:v for k,v in record.items() if k!='revision'})):
        raise ValueError('Opciones de título y miniatura alteradas')
    return {'status':'draft',**record,
            'limits':'La selección registra una preferencia editorial. Comprueba hechos, licencias, legibilidad e imagen final antes de publicar.'}


def save(pid,data):
    if not isinstance(data,dict) or set(data)!={'options','selected_id','expected_revision'}:
        raise ValueError('Campos de opciones inválidos')
    options=data['options'];selected=data['selected_id']
    if not isinstance(options,list) or not 2<=len(options)<=5:
        raise ValueError('Prepara entre dos y cinco variantes')
    ids=set();titles=set()
    for index,option in enumerate(options,1):
        if not isinstance(option,dict) or set(option)!={'id','title','overlay','visual_concept','source_note'}:
            raise ValueError('Variante inválida')
        if option['id']!=str(index):raise ValueError('IDs de variante inválidos')
        ids.add(option['id'])
        for field,maximum in (('title',100),('overlay',45),('visual_concept',500),('source_note',500)):
            value=option[field]
            if not isinstance(value,str) or (field in ('title','visual_concept') and not value.strip()) or len(value)>maximum:
                raise ValueError('Campo de variante inválido: '+field)
        key=option['title'].strip().casefold()
        if key in titles:raise ValueError('Títulos repetidos')
        titles.add(key)
    if selected is not None and selected not in ids:raise ValueError('Selecciona una variante guardada')
    with studio.LOCK:
        current=read(pid)
        if data['expected_revision']!=current['revision']:
            raise ValueError('Las variantes cambiaron en otra ventana. Recarga antes de guardar')
        record={'project_id':pid,'options':options,'selected_id':selected,
                'updated_at_utc':studio.now()}
        record['revision']=_digest(record)
        studio.save_json(_path(pid),record)
    return read(pid)
