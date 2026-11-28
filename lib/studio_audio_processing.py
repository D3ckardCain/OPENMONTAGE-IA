"""Small bounded per-clip EQ/compressor. No live DSP, inference or new engines."""
from copy import deepcopy

RENDER_CONTRACT = 'clip-eq3-compressor-v1'
DEFAULT = {'bypass':False,'eq':{'bass_db':0.,'mid_db':0.,'treble_db':0.},
           'compressor':{'enabled':False,'threshold_db':-18.,'ratio':3.,'attack_ms':20.,'release_ms':250.}}


def normalize(value):
    from lib.studio_editor import number
    if value is None:return None
    if not isinstance(value,dict) or set(value)-set(DEFAULT):raise ValueError('Cadena de audio no admitida')
    result=deepcopy(DEFAULT)
    for flag in ('bypass',):
        if flag in value:
            if type(value[flag]) is not bool:raise ValueError('Bypass requiere booleano')
            result[flag]=value[flag]
    for group in ('eq','compressor'):
        settings=value.get(group,{})
        if not isinstance(settings,dict) or set(settings)-set(DEFAULT[group]):raise ValueError('Parámetro de audio desconocido')
        result[group].update(settings)
    for key in result['eq']:result['eq'][key]=number(result['eq'][key],-12,12)
    compressor=result['compressor']
    if type(compressor['enabled']) is not bool:raise ValueError('Compresor requiere enabled booleano')
    for key,low,high in [('threshold_db',-40,-6),('ratio',1,20),('attack_ms',2,200),('release_ms',20,2000)]:
        compressor[key]=number(compressor[key],low,high)
    return result


def effective(value):
    value=normalize(value)
    if value is None or value['bypass']:return None
    result={}
    if any(value['eq'].values()):result['eq']=value['eq']
    if value['compressor']['enabled'] and value['compressor']['ratio']!=1:
        result['compressor']={k:v for k,v in value['compressor'].items() if k!='enabled'}
    return result or None


def filter_suffix(clip):
    value=effective(clip.get('audio_processing'))
    if value is None:return ''
    filters=[]
    for key,hz in [('bass_db',120),('mid_db',1000),('treble_db',6000)]:
        gain=value.get('eq',{}).get(key,0)
        if gain:filters.append(f'equalizer=f={hz}:t=o:w=1:g={gain:.12g}')
    if 'compressor' in value:
        c=value['compressor'];threshold=10**(c['threshold_db']/20)
        filters.append(f"acompressor=threshold={threshold:.12g}:ratio={c['ratio']:.12g}:"
                       f"attack={c['attack_ms']:.12g}:release={c['release_ms']:.12g}:makeup=1")
    return ','+','.join(filters)


def apply(edl,data):
    if data.get('operation')!='audio_processing':return False
    from lib import studio_editor as edit
    track=data.get('track','video')
    if track not in ('video','audio'):raise ValueError('Pista desconocida')
    item=edit._item(edl['audio_tracks'] if track=='audio' else edl['cuts'],data['id'])
    if item.get('locked'):raise edit.Conflict('Clip bloqueado')
    if item.get('kind')=='gap' or not edl['sources'][item['source_id']].get('audio'):
        raise ValueError('El clip no contiene audio')
    settings=normalize(data['processing'])
    if settings is None:item.pop('audio_processing',None)
    else:item['audio_processing']=settings
    return True


def validate(edl):
    for clip in edl['cuts']+edl['audio_tracks']:
        if 'audio_processing' in clip:normalize(clip['audio_processing'])
