"""Read-only, project-scoped gallery for previously saved local video evidence."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re


CONTRACT = 'local-video-evidence-gallery-v1'
EVIDENCE_CONTRACT = 'local-video-evidence-v1'
MAX_SESSION_BYTES = 12 * 1024 * 1024
MAX_RECEIPT_BYTES = 4 * 1024 * 1024
MAX_CONTACT_SHEET_BYTES = 8 * 1024 * 1024
MAX_CONTACT_BYTES_TOTAL = 24 * 1024 * 1024
MAX_MESSAGES = 12_000
MAX_RECORDS = 40
MAX_WORDS = 1_000
_HEX64 = re.compile(r'^[a-f0-9]{64}$')
_ARCHIVE = re.compile(r'^agent_receipt_[a-f0-9]{64}$')


def _stable_bytes(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError('not_regular_file')
    before = path.stat()
    if before.st_size < 0 or before.st_size > limit:
        raise ValueError('file_size_limit')
    data = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, getattr(before, 'st_ino', None)) != (
            after.st_size, after.st_mtime_ns, getattr(after, 'st_ino', None)) or len(data) != after.st_size:
        raise ValueError('file_changed_during_read')
    return data


def _json_file(path: Path, limit: int) -> dict:
    try:
        value = json.loads(_stable_bytes(path, limit).decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('invalid_json') from exc
    if not isinstance(value, dict):
        raise ValueError('invalid_json_object')
    return value


def _archive_content(root: Path, summary: dict, message: dict) -> tuple[str, str]:
    name = summary.get('artifact_name')
    rel = summary.get('archive_path')
    if not isinstance(name, str) or not _ARCHIVE.fullmatch(name) or rel != f'artifacts/{name}.json':
        raise ValueError('invalid_archive_reference')
    directory = root / 'artifacts'
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('archive_missing')
    archive_path = directory / f'{name}.json'
    archive = _json_file(archive_path, MAX_RECEIPT_BYTES)
    content = archive.get('content')
    expected = summary.get('receipt_sha256')
    call_id = message.get('tool_call_id')
    if (not isinstance(content, str) or not isinstance(expected, str) or not _HEX64.fullmatch(expected)
            or hashlib.sha256(content.encode('utf-8')).hexdigest() != expected
            or archive.get('receipt_sha256') != expected
            or archive.get('archive_id') != name.removeprefix('agent_receipt_')
            or archive.get('tool_name') != 'frame_sampler'
            or archive.get('tool_call_id') != call_id
            or summary.get('tool_name') != 'frame_sampler'
            or summary.get('tool_call_id') != call_id):
        raise ValueError('archive_identity_mismatch')
    return content, expected


def _finite(value) -> float:
    if isinstance(value, bool):
        raise ValueError('invalid_number')
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('invalid_number')
    return result


def _provenance(value: object) -> dict:
    if not isinstance(value, dict):
        return {}
    allowed = {'engine', 'model', 'model_id', 'revision', 'language', 'language_code',
               'method', 'created_at', 'asr_version', 'transcript_sha256',
               'word_data_sha256', 'source_sha256', 'coverage'}
    result = {}
    for key in allowed:
        item = value.get(key)
        if isinstance(item, str) and len(item) <= 240:
            result[key] = item
        elif type(item) in (int, float, bool):
            result[key] = item
    return result


def _transcript(value: object) -> dict:
    if not isinstance(value, dict):
        return {'status': 'not_provided', 'words': [], 'word_count': 0,
                'asr_executed': False, 'provenance': {}}
    raw_words = value.get('words', [])
    if not isinstance(raw_words, list):
        raw_words = []
    words = []
    for item in raw_words[:MAX_WORDS]:
        if not isinstance(item, dict):
            continue
        text = item.get('text', item.get('word'))
        if not isinstance(text, str) or len(text) > 500:
            continue
        try:
            start, end = _finite(item.get('start_seconds')), _finite(item.get('end_seconds'))
        except (TypeError, ValueError):
            continue
        if start < 0 or end <= start:
            continue
        words.append({'index': item.get('index') if type(item.get('index')) is int else len(words),
                      'text': text, 'start_seconds': start, 'end_seconds': end,
                      'partial': item.get('partial') is True})
    return {'status': str(value.get('status', 'saved'))[:120], 'words': words,
            'word_count': len(raw_words), 'truncated': len(raw_words) > len(words),
            'coverage': str(value.get('coverage', 'unknown'))[:120],
            'asr_executed': value.get('asr_executed') is True,
            'transcript_sha256': value.get('transcript_sha256') if isinstance(value.get('transcript_sha256'), str) and _HEX64.fullmatch(value['transcript_sha256']) else None,
            'word_data_sha256': value.get('word_data_sha256') if isinstance(value.get('word_data_sha256'), str) and _HEX64.fullmatch(value['word_data_sha256']) else None,
            'provenance': _provenance(value.get('provenance'))}


def _contact(root: Path, report: dict) -> tuple[Path, bytes, str]:
    raw = report.get('contact_sheet')
    if not isinstance(raw, str) or len(raw) > 4096:
        raise ValueError('contact_sheet_missing')
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    artifact_root = root / 'artifacts'
    if artifact_root.is_symlink() or not artifact_root.is_dir():
        raise ValueError('contact_sheet_missing')
    try:
        lexical_root = Path(os.path.abspath(artifact_root))
        lexical_candidate = Path(os.path.abspath(candidate))
        lexical_relative = lexical_candidate.relative_to(lexical_root)
        root_resolved = artifact_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root_resolved)
    except (OSError, ValueError) as exc:
        raise ValueError('contact_sheet_outside_artifacts') from exc
    cursor = artifact_root
    for part in lexical_relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError('contact_sheet_symlink')
    files = report.get('files')
    manifest = next((row for row in files if isinstance(row, dict) and row.get('name') == resolved.name), None) if isinstance(files, list) else None
    if not isinstance(manifest, dict):
        raise ValueError('contact_sheet_not_in_manifest')
    expected = manifest.get('sha256'); expected_bytes = manifest.get('bytes')
    if not isinstance(expected, str) or not _HEX64.fullmatch(expected) or type(expected_bytes) is not int:
        raise ValueError('contact_sheet_manifest_invalid')
    if expected_bytes < 4 or expected_bytes > MAX_CONTACT_SHEET_BYTES:
        raise ValueError('contact_sheet_size_limit')
    data = _stable_bytes(resolved, MAX_CONTACT_SHEET_BYTES)
    if len(data) != expected_bytes or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('contact_sheet_hash_mismatch')
    if not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
        raise ValueError('contact_sheet_not_jpeg')
    return resolved, data, expected


def _report(root: Path, message: dict, index: int) -> tuple[dict, bytes, str] | None:
    content = message.get('content')
    if not isinstance(content, str) or len(content.encode('utf-8')) > MAX_RECEIPT_BYTES:
        raise ValueError('receipt_size_limit')
    value = json.loads(content)
    receipt_sha = hashlib.sha256(content.encode('utf-8')).hexdigest()
    if isinstance(value, dict) and value.get('compacted') is True:
        content, receipt_sha = _archive_content(root, value, message)
        value = json.loads(content)
    if not isinstance(value, dict) or value.get('success') is False:
        return None
    report = value.get('data', value)
    if not isinstance(report, dict) or report.get('contract') != EVIDENCE_CONTRACT:
        return None
    if report.get('inference_executed') is not False or report.get('coverage') != 'partial_sampled_images_only':
        raise ValueError('coverage_contract_invalid')
    source_sha = report.get('source_sha256')
    if not isinstance(source_sha, str) or not _HEX64.fullmatch(source_sha):
        raise ValueError('source_identity_invalid')
    span = report.get('requested_range')
    frames = report.get('frames')
    if not isinstance(span, list) or len(span) != 2 or not isinstance(frames, list) or not 1 <= len(frames) <= 12:
        raise ValueError('frame_range_invalid')
    start, end = _finite(span[0]), _finite(span[1])
    if start < 0 or end <= start or end - start > 120:
        raise ValueError('frame_range_invalid')
    clean_frames = []
    for frame in frames:
        if not isinstance(frame, dict):
            raise ValueError('frame_invalid')
        pts = _finite(frame.get('pts_seconds'))
        rational = frame.get('pts_rational')
        if pts < start or pts >= end or not isinstance(rational, list) or len(rational) != 2 or any(type(v) is not int for v in rational) or rational[1] <= 0:
            raise ValueError('frame_pts_invalid')
        clean_frames.append({'pts_seconds': pts, 'pts_rational': rational,
                             'clock': str(frame.get('clock', 'source_presentation_time'))[:80],
                             'timestamp_method': str(frame.get('timestamp_method', 'unknown'))[:120]})
    path, image, image_sha = _contact(root, report)
    call_id = message.get('tool_call_id')
    evidence_id = hashlib.sha256(f'{call_id or index}:{receipt_sha}:{source_sha}'.encode()).hexdigest()
    duration = _finite(report.get('source_duration_seconds'))
    if duration <= 0:
        raise ValueError('source_duration_invalid')
    transcript = _transcript(report.get('transcript'))
    return ({'id': evidence_id, 'tool_call_id': call_id if isinstance(call_id, str) else None,
             'receipt_sha256': receipt_sha, 'source_sha256': source_sha,
             'source_duration_seconds': duration, 'requested_range': [start, end],
             'frame_count': len(clean_frames), 'frames': clean_frames,
             'contact_sheet_sha256': image_sha, 'coverage': 'partial_sampled_images_only',
             'gaps': str(report.get('gaps', 'Unmuestreado no revisado'))[:1000],
             'sampling': str(report.get('sampling', 'unknown'))[:160],
             'transcript': transcript}, image, str(path))


def _records(project_path: Path) -> tuple[list[tuple[dict, bytes, str]], list[str]]:
    root = Path(project_path).resolve()
    if not root.is_dir():
        return [], ['project_unavailable']
    session_path = root / 'agent_session.json'
    if not session_path.exists():
        return [], []
    try:
        session = _json_file(session_path, MAX_SESSION_BYTES)
    except (OSError, ValueError):
        return [], ['session_unavailable_or_invalid']
    messages = session.get('messages')
    if not isinstance(messages, list):
        return [], ['session_messages_invalid']
    warnings = []
    rows = []
    total = 0
    candidates = messages[-MAX_MESSAGES:]
    for index, message in enumerate(candidates):
        if not isinstance(message, dict) or message.get('role') != 'tool' or message.get('tool_name') != 'frame_sampler':
            continue
        try:
            record = _report(root, message, index)
            if record is None:
                continue
            row, image, path = record
            if total + len(image) > MAX_CONTACT_BYTES_TOTAL:
                warnings.append('contact_sheet_total_limit')
                break
            total += len(image)
            rows.append((row, image, path))
            if len(rows) >= MAX_RECORDS:
                warnings.append('record_limit')
                break
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            warnings.append('saved_evidence_skipped')
    unique = {}
    for row in rows:
        unique[row[0]['id']] = row
    return list(unique.values()), list(dict.fromkeys(warnings))


def list_saved_evidence(project_path: Path) -> dict:
    rows, warnings = _records(project_path)
    return {'contract': CONTRACT, 'coverage': 'partial_sampled_images_only', 'items': [row[0] for row in rows],
            'warnings': warnings, 'read_only': True, 'asr_executed': False}


def contact_sheet_bytes(project_path: Path, evidence_id: str) -> bytes:
    if not isinstance(evidence_id, str) or not _HEX64.fullmatch(evidence_id):
        raise ValueError('invalid_evidence_id')
    rows, _ = _records(project_path)
    for row, image, _path in rows:
        if row['id'] == evidence_id:
            return image
    raise FileNotFoundError('Saved contact sheet not found or no longer verified')
