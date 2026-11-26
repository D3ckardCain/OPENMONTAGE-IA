"""Pinned local CC0 SFX catalogue. No directory scans, network or inference."""
import hashlib
import json
import re
import struct
import unicodedata
import zipfile
from pathlib import Path
from lib import production_studio as studio

REVISION = '3d83d987d658601d8a1269eb691622bdcd427335'
REPOSITORY = 'Barty-Bart/motion-graphics'
MAX_ASSET_BYTES = 4_000_000
CATEGORIES = {'whoosh':'Whoosh / barrido', 'click':'Clic', 'pop':'Pop / aparición',
              'riser':'Ascenso / riser', 'impact':'Impacto', 'tick':'Tic / marcador',
              'typing':'Teclado', 'ding':'Campana / aviso', 'transition':'Transición',
              'glitch':'Glitch / interferencia', 'ambience':'Ambiente', 'ui-blip':'Interfaz / bleep'}
SEARCH_TERMS = {'heavy':'pesado fuerte','soft':'suave','light':'ligero','impactpunch':'puñetazo golpe',
                'wood':'madera','metal':'metal','door':'puerta','typing':'teclado escribir',
                'room':'habitación interior','water':'agua','rain':'lluvia','footstep':'pasos'}


def identity(path):
    s=Path(path).stat()
    return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def ogg_info(data):
    """Vorbis/Opus header + final granule, no audio decoding or analysis."""
    offset=0;packet=bytearray();ident=None;granule=0;serial=None
    while offset<len(data):
        if offset+27>len(data) or data[offset:offset+4]!=b'OggS' or data[offset+4]!=0:
            raise ValueError('Cabecera OGG no válida')
        stream=struct.unpack_from('<I',data,offset+14)[0]
        if serial is None:serial=stream
        if stream!=serial:raise ValueError('OGG encadenado no admitido por este catálogo')
        mark=struct.unpack_from('<Q',data,offset+6)[0]
        if mark!=(1<<64)-1:granule=max(granule,mark)
        n=data[offset+26];table=data[offset+27:offset+27+n]
        if len(table)!=n:raise ValueError('OGG truncado')
        start=offset+27+n;end=start+sum(table)
        if end>len(data):raise ValueError('OGG truncado')
        if ident is None:
            for length in table:
                packet.extend(data[start:start+length]);start+=length
                if length<255:ident=bytes(packet);break
        offset=end
    if not ident:raise ValueError('Falta identificación de audio OGG')
    if ident.startswith(b'\x01vorbis') and len(ident)>=30:
        channels=ident[11];rate=struct.unpack_from('<I',ident,12)[0];samples=granule
    elif ident.startswith(b'OpusHead') and len(ident)>=19:
        channels=ident[9];rate=48000;samples=granule-struct.unpack_from('<H',ident,10)[0]
    else:raise ValueError('Solo Vorbis/Opus en este catálogo')
    if channels not in (1,2) or not 8000<=rate<=192000 or samples<=0:
        raise ValueError('Audio OGG fuera de límites')
    return {'duration':samples/rate,'channels':channels,'sample_rate':rate,'kind':'audio','audio':True}


def prepare(archive, destination):
    """Explicit one-time preparation of an already completed local archive."""
    archive=Path(archive).resolve();destination=Path(destination)
    official=studio.read_json(Path(__file__).resolve().parents[1]/'docs/sfx/motion-graphics-official.json')
    before=identity(archive)
    old=studio.read_json(destination)
    if old and old.get('archive_identity')==before and old.get('revision')==REVISION:
        return {'reused':True,'files':old['source_files'],'assets':len(old['assets']),'new_hashes':0}
    if old:raise ValueError('El catálogo existente difiere; conservarlo y revisar antes de sustituir')
    assets={}
    with zipfile.ZipFile(archive) as z:
        if z.comment.decode('ascii')!=REVISION:raise ValueError('El ZIP no corresponde a la revisión fijada')
        prefix=z.namelist()[0].split('/')[0]+'/'
        license_bytes=z.read(prefix+official['license_path'])
        if git_blob(license_bytes)!=official['license_git_blob']:raise ValueError('Licencia distinta de la fijada')
        licenses={}
        for line in license_bytes.decode('utf-8').splitlines():
            if not line.startswith('| '):continue
            cells=[v.strip() for v in line.strip('|').split('|')]
            if len(cells)!=5 or not cells[0].endswith('.ogg'):continue
            url=re.search(r'\]\((https://[^)]+)\)',cells[4])
            if url:licenses[cells[0]]={'category':cells[1],'author':cells[3],'source_url':url[1]}
        for reference in official['files']:
            info=z.getinfo(prefix+reference['path'])
            if info.file_size!=reference['bytes'] or not 0<info.file_size<=MAX_ASSET_BYTES:
                raise ValueError('Tamaño de efecto inesperado')
            data=z.read(info);blob=git_blob(data)
            if blob!=reference['git_blob']:raise ValueError('Efecto distinto de la revisión oficial: '+reference['path'])
            relative=reference['path'].split('/sfx/',1)[1];license_row=licenses.get(relative)
            if not license_row:raise ValueError('Falta licencia individual: '+relative)
            sha=hashlib.sha256(data).hexdigest();asset_id='sfx-'+sha
            alias={'file':relative,'archive_entry':info.filename,'git_blob':blob,**license_row}
            if asset_id in assets:assets[asset_id]['aliases'].append(alias);continue
            category=license_row['category']
            assets[asset_id]={'id':asset_id,'sha256':sha,'bytes':len(data),**ogg_info(data),
                'name':Path(relative).stem.replace('-',' ').replace('_',' '),'category':category,
                'category_es':CATEGORIES.get(category,category),'library':'MotionGraphics CC0',
                'license':'CC0-1.0','license_evidence':'supplier_pinned_LICENSES.md',
                'attribution_required':False,'aliases':[alias]}
    if identity(archive)!=before:raise ValueError('El archivo cambió durante la preparación; no registrar')
    manifest={'schema_version':1,'repository':REPOSITORY,'revision':REVISION,'archive':str(archive),
              'archive_identity':before,'source_files':len(official['files']),'assets':list(assets.values()),
              'license_text':license_bytes.decode('utf-8'),'license_git_blob':official['license_git_blob'],
              'prepared_at':studio.now(),'no_network':True}
    studio.save_json(destination,manifest)
    return {'reused':False,'files':manifest['source_files'],'assets':len(assets),'new_hashes':len(official['files'])}


def manifest():
    value=studio.read_json(studio.CONFIG_DIR/'sfx-catalog.json')
    if value is None:return None
    if value.get('revision')!=REVISION or not isinstance(value.get('assets'),list):
        raise ValueError('Catálogo SFX incompatible; no se descarga ni repara automáticamente')
    return value


def archive_status(value):
    try:
        if identity(value['archive'])!=value['archive_identity']:
            return False,'El ZIP cambió desde la verificación; revisión necesaria'
        return True,''
    except PermissionError:return False,'Acceso al ZIP denegado'
    except OSError:
        anchor=Path(value['archive']).anchor
        return False,'Unidad no disponible' if not Path(anchor).exists() else 'ZIP ausente o no accesible'


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.lower()) if not unicodedata.combining(c))


def catalog(query='',category='',offset=0,limit=24,ids=None):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=48 or len(query)>200:
        raise ValueError('Consulta de catálogo fuera de límites')
    value=manifest()
    if value is None:return {'items':[],'total':0,'available':False,'reason':'Catálogo local aún no preparado; no hay descargas automáticas','categories':CATEGORIES}
    available,reason=archive_status(value);tokens=normalized(query).split();rows=[]
    for row in value['assets']:
        if ids is not None and row['id'] not in ids:continue
        text=normalized(' '.join([row['name'],row['category'],row['category_es'],*[a['file']+' '+a['author'] for a in row['aliases']]]))
        text+=' '+normalized(' '.join(words for key,words in SEARCH_TERMS.items() if key in text))
        if category and row['category']!=category:continue
        if not all(token in text for token in tokens):continue
        rows.append({**row,'available':available,'reason':reason,
            'audio_url':'/api/studio/editor/sfx/'+row['id']+'/audio'})
    return {'items':rows[offset:offset+limit],'total':len(rows),'offset':offset,'limit':limit,
            'available':available,'reason':reason,'categories':CATEGORIES,'source_files':value['source_files'],
            'unique_assets':len(value['assets']),'revision':value['revision']}


def find(asset_id):
    if not isinstance(asset_id,str) or not re.fullmatch(r'sfx-[0-9a-f]{64}',asset_id):raise ValueError('ID de efecto inválido')
    value=manifest()
    if value is None:raise ValueError('Catálogo SFX no preparado')
    row=next((a for a in value['assets'] if a['id']==asset_id),None)
    if row is None:raise FileNotFoundError('Efecto no registrado')
    if row['license']!='CC0-1.0':raise ValueError('Licencia no admitida por este perfil local')
    return value,row


def materialize(asset_id):
    """On-demand single asset cache; opening/searching never extracts the library."""
    with studio.LOCK:
        value,row=find(asset_id);available,reason=archive_status(value)
        if not available:raise ValueError(reason)
        folder=studio.CONFIG_DIR/'sfx-preview-cache';path=folder/(row['sha256']+'.ogg')
        receipt=studio.read_json(folder/(row['sha256']+'.json'))
        if receipt and path.is_file() and receipt.get('identity')==identity(path):return path,row
        if path.exists():raise ValueError('Caché SFX sin identidad válida; conservar archivo y revisar')
        folder.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(value['archive']) as z:
            entry=z.getinfo(row['aliases'][0]['archive_entry'])
            if entry.file_size!=row['bytes']:raise ValueError('Tamaño de efecto cambiado')
            data=z.read(entry)
        if identity(value['archive'])!=value['archive_identity']:raise ValueError('ZIP modificado durante lectura')
        # The unchanged archive/entry was already checked against the official
        # Git blob at preparation. ZIP CRC is checked by read; no repeated SHA.
        with path.open('xb') as stream:stream.write(data)
        studio.save_json(folder/(row['sha256']+'.json'),{'identity':identity(path),'sha256':row['sha256'],'revision':REVISION})
        return path,row
