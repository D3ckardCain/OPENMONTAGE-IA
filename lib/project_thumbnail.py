"""Check a local thumbnail against the selected editorial variant."""
import base64
import binascii
import hashlib
import io
import re
import warnings

from PIL import Image, UnidentifiedImageError

from lib import production_studio as studio
from lib.channel_dossiers import _digest
from lib.packaging_options import read as packaging_read


def _manifest(project):
    return project/'artifacts/thumbnail_review.json'


def current(pid):
    project=studio.project_path(pid)
    manifest=_manifest(project)
    if manifest.is_symlink():raise ValueError('Imagen de miniatura ausente o alterada')
    record=studio.read_json(manifest)
    if record is None:return {'status':'missing','message':'Aún no hay imagen de miniatura asociada a la selección.'}
    if (not isinstance(record,dict) or not isinstance(record.get('filename'),str)
            or not re.fullmatch(r'[0-9a-f]{64}\.(?:png|jpg)',record['filename'])
            or record.get('revision')!=_digest({k:v for k,v in record.items() if k!='revision'})):
        raise ValueError('Imagen de miniatura ausente o alterada')
    path=project/'thumbnails'/record['filename']
    if not path.is_file() or path.is_symlink():
        raise ValueError('Imagen de miniatura ausente o alterada')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=record.get('sha256'):
        raise ValueError('Imagen de miniatura ausente o alterada')
    packaging=packaging_read(pid)
    if packaging['revision']!=record.get('packaging_revision') or packaging['selected_id']!=record.get('selected_id'):
        raise ValueError('La miniatura pertenece a otra selección editorial')
    return {'status':'review',**record,'url':f'/media/{pid}/thumbnails/{record["filename"]}',
            'limits':'Imagen local para revisión visual. Verifica texto, hechos, licencias y el tamaño exigido por cada plataforma antes de publicar.'}


def stage(pid,data):
    if not isinstance(data,dict) or set(data)!={'image_base64','expected_packaging_revision'} or not isinstance(data['image_base64'],str):
        raise ValueError('Imagen y versión editorial requeridas')
    try:raw=base64.b64decode(data['image_base64'],validate=True)
    except (ValueError,binascii.Error):raise ValueError('Contenido base64 inválido') from None
    if not 1<=len(raw)<=8_000_000:raise ValueError('Imagen vacía o superior a 8 MB')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                width,height=image.size;fmt=image.format
                if fmt not in ('PNG','JPEG') or getattr(image,'n_frames',1)!=1:
                    raise ValueError('Usa PNG o JPEG estático')
                if width*height>16_000_000 or width<640 or height<360 or abs(width/height-16/9)>0.03:
                    raise ValueError('Usa formato horizontal 16:9 de al menos 640 × 360 y máximo 16 megapíxeles')
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:image.load()
    except (UnidentifiedImageError,OSError,Image.DecompressionBombWarning,Image.DecompressionBombError) as exc:
        raise ValueError('No se pudo decodificar la imagen') from exc
    project=studio.project_path(pid)
    digest=hashlib.sha256(raw).hexdigest();name=digest+('.png' if fmt=='PNG' else '.jpg')
    with studio.LOCK:
        packaging=packaging_read(pid)
        if (packaging['revision']!=data['expected_packaging_revision'] or not packaging['selected_id']):
            raise ValueError('Elige y guarda una variante actual antes de asociar la imagen')
        folder=project/'thumbnails';folder.mkdir(exist_ok=True)
        path=folder/name
        if not path.exists():
            if len(list(folder.iterdir()))>=20:raise ValueError('Límite de 20 imágenes de miniatura alcanzado')
            with path.open('xb') as output:output.write(raw)
        record={'filename':name,'sha256':digest,'width':width,'height':height,'bytes':len(raw),
                'format':fmt,'packaging_revision':packaging['revision'],
                'selected_id':packaging['selected_id'],'reviewed':False,'saved_at_utc':studio.now()}
        record['revision']=_digest(record)
        studio.save_json(_manifest(project),record)
    return current(pid)
