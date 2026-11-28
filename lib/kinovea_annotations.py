"""Read KVA 2.1 annotations without loading a video or evaluating drawings."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import hashlib
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from xml.parsers import expat
from lib import production_studio as studio

MAX_BYTES = 2 * 1024 * 1024


def parse(raw):
    builder = ET.TreeBuilder()
    parser = expat.ParserCreate()
    depth, count = 0, 0

    def reject(*args):
        raise ValueError('KINOVEA_XML_UNSAFE: no se admiten DTD o entidades')

    def start(name, attrs):
        nonlocal depth, count
        depth += 1
        count += 1
        if depth > 64 or count > 10000:
            raise ValueError('KINOVEA_LIMIT: XML demasiado complejo')
        builder.start(name, attrs)

    def end(name):
        nonlocal depth
        builder.end(name)
        depth -= 1

    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.CharacterDataHandler = builder.data
    parser.StartDoctypeDeclHandler = reject
    parser.EntityDeclHandler = reject
    parser.ExternalEntityRefHandler = reject
    try:
        parser.Parse(raw, True)
    except (expat.ExpatError, LookupError) as exc:
        raise ValueError('KINOVEA_FORMAT: XML no admitido') from exc
    root = builder.close()
    if root.tag != 'KinoveaVideoAnalysis':
        raise ValueError('KINOVEA_FORMAT: raíz XML no admitida')

    def one(element, tag, required=False):
        matches = element.findall(tag)
        if len(matches) > 1 or (required and not matches):
            raise ValueError('KINOVEA_FORMAT: campo ausente o duplicado ' + tag)
        if matches and list(matches[0]):
            raise ValueError('KINOVEA_FORMAT: campo compuesto no admitido ' + tag)
        return (matches[0].text or '').strip() if matches else None

    def integer(value, name):
        if value is None:
            return None
        if not re.fullmatch(r'[+-]?[0-9]{1,19}', value) or abs(int(value)) > 2**63 - 1:
            raise ValueError('KINOVEA_TIME_INVALID: entero inválido ' + name)
        return int(value)

    def positive(value, name, zero=False):
        if value is None:
            return None
        try:
            number = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError('KINOVEA_TIME_INVALID: número inválido ' + name) from exc
        if not number.is_finite() or number < 0 or (not zero and number == 0) or number > Decimal('1e15') or (number > 0 and number < Decimal('1e-12')):
            raise ValueError('KINOVEA_TIME_INVALID: magnitud inválida ' + name)
        return number

    version = one(root, 'FormatVersion', True)
    if version != '2.1':
        raise ValueError('KINOVEA_VERSION_UNSUPPORTED: solo formato KVA 2.1; no se convierte automáticamente')
    origin = integer(one(root, 'TimeOrigin'), 'TimeOrigin')
    first = integer(one(root, 'FirstTimeStamp'), 'FirstTimeStamp')
    average = positive(one(root, 'AverageTimeStampsPerFrame'), 'AverageTimeStampsPerFrame')
    video_fps = positive(one(root, 'VideoFramerate'), 'VideoFramerate')
    capture_fps = positive(one(root, 'CaptureFramerate'), 'CaptureFramerate', zero=True)
    groups = root.findall('Keyframes')
    if len(groups) > 1:
        raise ValueError('KINOVEA_FORMAT: Keyframes duplicado')
    frames = list(groups[0]) if groups else []
    if len(frames) > 1000 or any(frame.tag != 'Keyframe' for frame in frames):
        raise ValueError('KINOVEA_LIMIT: lista de keyframes no admitida')
    result = []
    for frame in frames:
        timestamp = integer(one(frame, 'Timestamp', True), 'Timestamp')
        drawings = frame.findall('Drawings')
        if len(drawings) > 1:
            raise ValueError('KINOVEA_FORMAT: Drawings duplicado')
        types = {}
        for drawing in list(drawings[0]) if drawings else []:
            types[drawing.tag] = types.get(drawing.tag, 0) + 1
        row = {'timestamp_raw': timestamp, 'name': (one(frame, 'Name') or '')[:2000],
               'drawing_count': sum(types.values()), 'drawing_types': types}
        if origin is not None and average is not None:
            delta = Decimal(timestamp - origin) / average
            offset = int(delta.to_integral_value(rounding=ROUND_HALF_EVEN))
            row['frame_offset_from_time_origin'] = offset
            for key, fps in (('playback_seconds_from_time_origin', video_fps), ('capture_seconds_from_time_origin', capture_fps)):
                if fps:
                    seconds = float(Decimal(offset) / fps)
                    if not math.isfinite(seconds):
                        raise ValueError('KINOVEA_TIME_INVALID: segundos no finitos')
                    row[key] = seconds
        result.append(row)
    return {'format_version': version, 'producer_declared': (one(root, 'Producer') or '')[:200],
            'keyframe_count': len(result), 'keyframes': result,
            'timing_declared': {'time_origin_raw': origin, 'first_timestamp_raw': first,
                'average_timestamps_per_frame': str(average) if average is not None else None,
                'video_framerate': str(video_fps) if video_fps is not None else None,
                'capture_framerate': str(capture_fps) if capture_fps is not None else None},
            'timestamp_unit': 'native_ticks_not_assumed_milliseconds',
            'frame_rounding': 'nearest_integer_ties_to_even_as_declared_kinovea_clock',
            'video_loaded': False, 'kinovea_launched': False, 'drawings_evaluated': False,
            'spatial_calibration_verified': False, 'content_generated': False}


def inspect(project_id, input_path):
    root = studio.project_path(project_id).resolve()
    path = Path(input_path)
    path = (path if path.is_absolute() else root / path).resolve()
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError('KINOVEA_PATH: el archivo debe estar dentro del proyecto') from exc
    if path.suffix.lower() != '.kva' or not path.is_file():
        raise ValueError('KINOVEA_PATH: indica un .kva existente')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('KINOVEA_LIMIT: XML vacío o mayor de 2 MiB')
    data = parse(raw)
    data['provenance'] = {'project_id': project_id, 'project_relative_path': relative.as_posix(),
                          'input_sha256': hashlib.sha256(raw).hexdigest(), 'input_bytes': len(raw),
                          'reader_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                          'created_at_utc': datetime.now(timezone.utc).isoformat(),
                          'metadata_is_untrusted_source_data': True, 'network_accessed': False}
    return data
