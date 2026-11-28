"""Editable editorial plan kept separate from the pipeline's approved script."""
import re

from lib import production_studio as studio
from lib.channel_dossiers import _digest

BLOCKS=('apertura','contexto','desarrollo','resolucion','cierre')


def _path(pid):
    return studio.project_path(pid)/'artifacts/editorial_script_outline.json'


def read(pid):
    path=_path(pid)
    record=studio.read_json(path)
    if record is None:
        request=studio.read_json(studio.project_path(pid)/'production_request.json')
        return {'status':'empty','title':request['title'],'target_seconds':60,
            'blocks':[{'kind':kind,'narration':'','voice_direction':'','visual_direction':'','source_ref':''} for kind in BLOCKS],
            'revision':None,'message':'Plantilla vacía. Guarda una versión para que el agente pueda consultarla.'}
    if not isinstance(record,dict) or record.get('project_id')!=pid or record.get('revision')!=_digest({k:v for k,v in record.items() if k!='revision'}):
        raise ValueError('Borrador editorial alterado')
    return {'status':'draft',**record,'analysis':analyze(record)}


def analyze(data):
    pace=150
    words=sum(len(re.findall(r'\b\w+\b',block['narration'],re.UNICODE)) for block in data['blocks'])
    return {'word_count':words,'estimated_speech_seconds':round(words*60/pace,1),
            'target_seconds':data['target_seconds'],
            'without_source':[b['kind'] for b in data['blocks'] if b['narration'].strip() and not b['source_ref'].strip()],
            'without_voice':[b['kind'] for b in data['blocks'] if b['narration'].strip() and not b['voice_direction'].strip()],
            'without_visual':[b['kind'] for b in data['blocks'] if b['narration'].strip() and not b['visual_direction'].strip()],
            'limits':'150 palabras/minuto es una estimación. Las referencias escritas no verifican hechos. Borrador sin aprobación para voz, render o publicación.'}


def save(pid,data):
    if not isinstance(data,dict) or set(data)!={'title','target_seconds','blocks','expected_revision'}:
        raise ValueError('Campos del borrador inválidos')
    title=data['title'];duration=data['target_seconds'];blocks=data['blocks']
    if not isinstance(title,str) or not 1<=len(title.strip())<=150 or type(duration) is not int or not 15<=duration<=3600:
        raise ValueError('Título o duración inválidos')
    if not isinstance(blocks,list) or len(blocks)!=len(BLOCKS):raise ValueError('Se requieren cinco bloques editoriales')
    for kind,block in zip(BLOCKS,blocks):
        if not isinstance(block,dict) or set(block)!={'kind','narration','voice_direction','visual_direction','source_ref'} or block['kind']!=kind:
            raise ValueError('Bloques editoriales inválidos')
        for field,max_length in (('narration',4000),('voice_direction',500),('visual_direction',500),('source_ref',1000)):
            value=block[field]
            if not isinstance(value,str) or len(value)>max_length:raise ValueError('Campo del bloque inválido: '+field)
    if not any(b['narration'].strip() for b in blocks):raise ValueError('Escribe la narración de al menos un bloque')
    with studio.LOCK:
        current=read(pid)
        if data['expected_revision']!=current['revision']:
            raise ValueError('El borrador cambió en otra ventana. Recárgalo antes de guardar')
        record={'project_id':pid,'title':title.strip(),'target_seconds':duration,'blocks':blocks,
                'updated_at_utc':studio.now(),'status':'draft'}
        record['revision']=_digest(record)
        studio.save_json(_path(pid),record)
    return read(pid)
