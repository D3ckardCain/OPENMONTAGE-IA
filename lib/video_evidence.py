"""Bounded local frame evidence with real PTS; never ASR, vision inference or upload."""
import bisect
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from fractions import Fraction

from lib.media_executables import require_media
from lib.hyperframes_staging import identity, digest
from lib.studio_editor import INPUT_OPTIONS, number, edit_digest

VERSION = 'local-video-evidence-v1'


def _run(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise ValueError('FFmpeg/FFprobe evidence failed: ' + result.stderr[-1200:])
    return result


def _transcript(stored, source_sha, start, end):
    if stored is None:
        return dict(status='not_provided', words=[], coverage='unknown', asr_executed=False)
    if not isinstance(stored, dict) or stored.get('source_sha256') != source_sha:
        raise ValueError('Stored transcript does not match verified source content')
    words = stored.get('words')
    if not isinstance(words, list) or len(words) > 5000:
        raise ValueError('Stored transcript requires at most5000 words')
    selected = []
    for index, word in enumerate(words):
        a = number(word['start']); b = number(word['end'], a)
        if not isinstance(word.get('word'), str):
            raise ValueError('Invalid stored word text')
        if a < end and start < b:
            selected.append(dict(index=index, text=word['word'], start_seconds=a, end_seconds=b,
                                 partial=a < start or b > end))
    return dict(status='reused_declared_not_independently_aligned', words=selected,
                word_data_sha256=edit_digest(words), transcript_sha256=stored.get('transcript_sha256'),
                processed_ranges=stored.get('coverage', {}).get('processed_ranges', []),
                provenance=stored.get('provenance', {}), asr_executed=False)


def inspect(inputs):
    source = Path(inputs['input_path']).resolve(); output = Path(inputs['output_dir']).resolve()
    if not source.is_file():
        raise ValueError('Local source file missing')
    count = inputs.get('max_frames', 4); width = inputs.get('thumbnail_width', 320)
    if type(count) is not int or not 1 <= count <= 12 or type(width) is not int or not 128 <= width <= 640:
        raise ValueError('Evidence budget:1–12 frames, width128–640')
    start = number(inputs.get('start_seconds', 0)); end = number(inputs['end_seconds'], start)
    if not 0 < end - start <= 120:
        raise ValueError('Evidence range must be positive and at most120seconds')
    ffmpeg, ffprobe = require_media('ffmpeg'), require_media('ffprobe')
    before = identity(source); output.mkdir(parents=True, exist_ok=True)
    cache_file = output / '.source-hashes.json'
    if cache_file.is_symlink():
        raise ValueError('Linked cache not allowed')
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    row = cache.get(str(source), {})
    reused_hash = row.get('identity') == before
    sha = row['sha256'] if reused_hash else digest(source)
    if identity(source) != before:
        raise ValueError('Source changed during identity check')
    if inputs.get('source_sha256') not in (None, sha):
        raise ValueError('Registered source SHA256 differs; preserved')
    transcript = _transcript(inputs.get('stored_transcript'), sha, start, end)
    if not reused_hash:
        cache[str(source)] = dict(identity=before, sha256=sha)
        cache_file.write_text(json.dumps(cache, indent=2))
    runtime = {str(p): identity(Path(p)) for p in (ffmpeg, ffprobe)}
    key = edit_digest(dict(contract=VERSION, source_sha256=sha, start=start, end=end,
                           max_frames=count, width=width, runtime=runtime))
    folder = output / key; manifest = folder / 'receipt.json'
    if manifest.is_file():
        if cache.get('__receipts', {}).get(key) != digest(manifest):
            raise ValueError('Evidence receipt changed; no silent cache reuse')
        report = json.loads(manifest.read_text())
        for item in report['files']:
            path = (folder / item['name']).resolve(); path.relative_to(folder)
            if not path.is_file() or digest(path) != item['sha256']:
                raise ValueError('Cached evidence changed; preserve and inspect before rebuilding')
        return dict(report, cache_reused=True, source_hash_reused=reused_hash, transcript=transcript)
    if folder.exists():
        raise ValueError('Incomplete evidence directory exists; not silently overwritten')
    info = json.loads(_run([ffprobe, '-v', 'error', *INPUT_OPTIONS, '-select_streams', 'v:0',
                           '-show_entries', 'stream=time_base,duration:format=duration',
                           '-of', 'json', str(source)]).stdout)
    if not info.get('streams'):
        raise ValueError('Source has no video stream')
    duration = float(info.get('format', {}).get('duration') or info['streams'][0]['duration'])
    if end > duration:
        raise ValueError('Requested evidence range exceeds source duration')
    timebase = Fraction(info['streams'][0]['time_base'])
    metadata = json.loads(_run([ffprobe, '-v', 'error', *INPUT_OPTIONS, '-select_streams', 'v:0',
        '-read_intervals', f'{start}%{end}', '-show_frames', '-show_entries',
        'frame=best_effort_timestamp,best_effort_timestamp_time', '-of', 'json', str(source)]).stdout)
    pts = sorted({Fraction(int(f['best_effort_timestamp'])) * timebase for f in metadata.get('frames', [])
                  if 'best_effort_timestamp' in f and start <= Fraction(int(f['best_effort_timestamp'])) * timebase < end})
    if not pts:
        raise ValueError('No decoded frame PTS in requested range')
    targets = [start + (end-start)*(i+.5)/count for i in range(count)]
    selected = sorted({pts[min(bisect.bisect_left(pts, Fraction(str(t))), len(pts)-1)] for t in targets})
    folder.mkdir()
    expression = '+'.join(f'between(t,{float(t)-1e-7:.9f},{float(t)+1e-7:.9f})' for t in selected)
    result = _run([ffmpeg, '-nostdin', '-v', 'info', '-n', '-copyts', *INPUT_OPTIONS,
        '-i', str(source), '-an', '-vf', f"select='{expression}',showinfo,scale={width}:-2",
        '-fps_mode', 'vfr', '-frames:v', str(len(selected)), str(folder/'frame-%02d.png')])
    measured = [float(v) for v in re.findall(r'\bpts_time:([-+0-9.eE]+)', result.stderr)]
    images = sorted(folder.glob('frame-*.png'))
    if len(images) != len(selected) or len(measured) < len(selected):
        raise ValueError('Frame count/PTS extraction mismatch; partial evidence retained')
    from PIL import Image, ImageDraw
    height = max(Image.open(p).height for p in images); columns = min(4, len(images))
    sheet = Image.new('RGB', (columns*width, math.ceil(len(images)/columns)*(height+24)), '#0d1117')
    draw = ImageDraw.Draw(sheet); frames = []
    for i, (path, expected, observed) in enumerate(zip(images, selected, measured)):
        if abs(float(expected)-observed) > 1e-4:
            raise ValueError('Decoded PTS differs from selected source PTS')
        with Image.open(path) as image:
            sheet.paste(image.convert('RGB'), ((i%columns)*width, (i//columns)*(height+24)+24))
        draw.text(((i%columns)*width+4, (i//columns)*(height+24)+4), f'{i+1} / PTS {observed:.6f}s', fill='white')
        frames.append(dict(path=str(path), pts_seconds=observed, pts_rational=[expected.numerator, expected.denominator],
                           clock='source_presentation_time', timestamp_method='ffprobe+ffmpeg_showinfo'))
    sheet.save(folder/'contact-sheet.jpg')
    if identity(source) != before:
        raise ValueError('Source changed during extraction; no completed receipt')
    files = [dict(name=p.name, sha256=digest(p), bytes=p.stat().st_size) for p in [*images, folder/'contact-sheet.jpg']]
    report = dict(contract=VERSION, source_sha256=sha, source_duration_seconds=duration,
        requested_range=[start,end], requested_budget=count, frame_count=len(frames), frames=frames,
        contact_sheet=str(folder/'contact-sheet.jpg'), files=files, runtime=runtime,
        sampling='uniform_targets_selected_on_real_decoded_pts', coverage='partial_sampled_images_only',
        gaps='Motion, audio, unsampled frames and semantic claims not evaluated',
        inference_executed=False, transcript=transcript, cache_reused=False, source_hash_reused=reused_hash)
    manifest.write_text(json.dumps(report, indent=2), encoding='utf-8')
    cache.setdefault('__receipts', {})[key] = digest(manifest)
    cache_file.write_text(json.dumps(cache, indent=2))
    return report
