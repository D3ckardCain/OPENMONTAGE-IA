"""Bounded, read-only KRA metadata inspection; never decodes or edits pixels."""
from datetime import datetime, timezone
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
from xml.parsers import expat
import zipfile
from lib import production_studio as studio

MAX_ARCHIVE = 128 * 1024 * 1024
MAX_XML = 2 * 1024 * 1024


def xml_metadata(raw):
    parser = expat.ParserCreate()
    depth, count, images, layers, parents = 0, 0, [], [], []

    def reject(*args):
        raise ValueError('KRITA_XML_UNSAFE: no se admiten entidades XML')

    def start(tag, attrs):
        nonlocal depth, count
        depth += 1
        count += 1
        if depth > 128 or count > 10000:
            raise ValueError('KRITA_LIMIT: estructura XML demasiado grande')
        if count == 1 and tag != 'DOC':
            raise ValueError('KRITA_FORMAT: raíz XML no admitida')
        if tag == 'IMAGE':
            if depth != 2 or images:
                raise ValueError('KRITA_FORMAT: se requiere una sola imagen principal')
            dimensions = []
            for key in ('width', 'height'):
                value = attrs.get(key, '')
                if not re.fullmatch(r'[0-9]{1,7}', value) or not 1 <= int(value) <= 1000000:
                    raise ValueError('KRITA_FORMAT: dimensiones inválidas')
                dimensions.append(int(value))
            images.append({'width': dimensions[0], 'height': dimensions[1],
                           'color_space': attrs.get('colorspacename', '')[:200]})
        if tag == 'layer':
            if not images:
                raise ValueError('KRITA_FORMAT: capa sin imagen')
            parent = parents[-1][1] if parents else None
            layers.append({'index': len(layers), 'parent_index': parent,
                           'name': attrs.get('name', '')[:1000],
                           'node_type': attrs.get('nodetype', '')[:200],
                           'visible_declared': attrs.get('visible'),
                           'opacity_declared': attrs.get('opacity')})
            parents.append((depth, len(layers) - 1))

    def end(tag):
        nonlocal depth
        if parents and parents[-1][0] == depth:
            parents.pop()
        depth -= 1

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.EntityDeclHandler = reject
    parser.ExternalEntityRefHandler = reject
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.Parse(raw, True)
    if len(images) != 1:
        raise ValueError('KRITA_FORMAT: falta IMAGE')
    return {**images[0], 'layers': layers, 'layer_count': len(layers)}


def inspect(project_id, input_path):
    root = studio.project_path(project_id).resolve()
    source = Path(input_path)
    source = (source if source.is_absolute() else root / source).resolve()
    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise ValueError('KRITA_PATH: el archivo debe estar dentro del proyecto') from exc
    if source.suffix.lower() != '.kra' or not source.is_file():
        raise ValueError('KRITA_PATH: indica un archivo .kra existente del proyecto')
    with source.open('rb') as stream:
        raw = stream.read(MAX_ARCHIVE + 1)
    if not raw or len(raw) > MAX_ARCHIVE:
        raise ValueError('KRITA_LIMIT: contenedor vacío o mayor de 128 MiB')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            names = [e.filename for e in entries]
            if len(entries) > 10000 or len(names) != len(set(names)):
                raise ValueError('KRITA_FORMAT: entradas duplicadas o demasiadas')
            for entry in entries:
                name = entry.orig_filename
                if '\\' in name or ':' in name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or entry.flag_bits & 1:
                    raise ValueError('KRITA_FORMAT: entrada insegura o cifrada')

            def read(name, limit):
                info = archive.getinfo(name)
                if info.file_size > limit:
                    raise ValueError('KRITA_LIMIT: metadatos demasiado grandes')
                with archive.open(info) as stream:
                    value = stream.read(limit + 1)
                if len(value) > limit:
                    raise ValueError('KRITA_LIMIT: metadatos demasiado grandes')
                return value

            if read('mimetype', 64).strip() != b'application/x-krita':
                raise ValueError('KRITA_FORMAT: mimetype no corresponde a Krita')
            xml = read('maindoc.xml', MAX_XML)
            result = xml_metadata(xml)
            result['merged_preview_present'] = 'mergedimage.png' in names
    except (zipfile.BadZipFile, LookupError, expat.ExpatError, NotImplementedError, RuntimeError) as exc:
        raise ValueError('KRITA_FORMAT: contenedor o XML no admitido') from exc
    return {'schema_version': '1.0', **result, 'scope': 'declared_document_metadata_only',
            'pixels_decoded': False, 'document_modified': False, 'krita_launched': False,
            'visual_quality_verified': False, 'provenance': {
                'project_id': project_id, 'project_relative_path': relative.as_posix(),
                'input_sha256': hashlib.sha256(raw).hexdigest(), 'input_bytes': len(raw),
                'maindoc_sha256': hashlib.sha256(xml).hexdigest(),
                'inspected_at_utc': datetime.now(timezone.utc).isoformat(),
                'network_accessed': False, 'metadata_is_untrusted_source_data': True}}
