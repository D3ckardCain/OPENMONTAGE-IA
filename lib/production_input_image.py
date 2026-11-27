"""Validate and stage project source images without contacting a GPU runtime."""
import base64
import binascii
import hashlib
import io
import warnings

from PIL import Image, UnidentifiedImageError

from lib import production_studio as studio


def stage_image(project_id, data):
    project = studio.project_path(project_id)
    if set(data) != {'image_base64'} or not isinstance(data['image_base64'], str):
        raise ValueError('Se requiere image_base64')
    try:
        raw = base64.b64decode(data['image_base64'], validate=True)
    except (ValueError, binascii.Error):
        raise ValueError('Contenido base64 inválido')
    if not 1 <= len(raw) <= 8_000_000:
        raise ValueError('La imagen debe ocupar como máximo 8 MB')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                width, height = image.size
                fmt = image.format
                if fmt not in ('PNG', 'JPEG') or getattr(image, 'n_frames', 1) != 1:
                    raise ValueError('Usa una imagen PNG o JPEG estática')
                if width * height > 16_000_000:
                    raise ValueError('La imagen supera 16 millones de píxeles')
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError('No se pudo decodificar la imagen') from exc
    digest = hashlib.sha256(raw).hexdigest()
    name = digest + ('.png' if fmt == 'PNG' else '.jpg')
    folder = project / 'originales' / 'imagenes'
    with studio.LOCK:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        if not path.exists():
            if len(list(folder.glob('*'))) >= 100:
                raise ValueError('El proyecto ya contiene 100 imágenes de entrada')
            with path.open('xb') as stream:
                stream.write(raw)
        record = {'filename': name, 'relative_path': f'originales/imagenes/{name}',
                  'sha256': digest, 'width': width, 'height': height,
                  'bytes': len(raw), 'format': fmt, 'url': f'/media/{project_id}/originales/imagenes/{name}',
                  'comfyui_uploaded': False, 'generation_started': False}
        studio.save_json(project / 'source_image.json', record)
    return record


def current_image(project_id):
    return studio.read_json(studio.project_path(project_id) / 'source_image.json')

