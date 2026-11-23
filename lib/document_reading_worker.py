"""Standalone offline worker, invoked with the document runtime and raw stdin."""
import importlib.metadata
import io
import json
import re
import sys


def offline_only(event, args):
    if event.startswith('socket.'):
        raise PermissionError('El lector documental funciona sin red')


def bounded_fields(values):
    result = {}
    truncated = []
    for name, value in values.items():
        if isinstance(value, str) and len(value) > 1000:
            value = value[:1000]
            truncated.append(name)
        elif isinstance(value, list):
            if len(value) > 10 or any(isinstance(item, str) and len(item) > 1000 for item in value):
                truncated.append(name)
            value = [item[:1000] if isinstance(item, str) else item for item in value[:10]]
        result[name] = value
    return result, truncated


def read_feed(raw, source_url, offset, limit):
    import feedparser

    # BytesIO keeps feedparser from interpreting input as a URL or filename.
    if re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b', raw.replace(b'\x00', b''), re.I):
        raise ValueError('El lector de feeds rechaza declaraciones DTD y entidades')
    headers = {'content-location': source_url} if source_url else {}
    parsed = feedparser.parse(io.BytesIO(raw), response_headers=headers)
    if not parsed.version:
        raise ValueError('El archivo no identifica un feed RSS/Atom compatible')
    fields = ('id', 'title', 'link', 'published', 'updated', 'author', 'summary', 'language')
    entries = []
    page_characters = 0
    for index, item in enumerate(parsed.entries[offset:offset + limit], start=offset):
        entry, truncated = bounded_fields({field: item.get(field) for field in fields})
        entry['entry_index'] = index
        entry['content'] = []
        content_items = item.get('content', [])
        for content_index, content in enumerate(content_items[:5]):
            value, content_truncated = bounded_fields({
                field: content.get(field) for field in ('type', 'language', 'value')})
            entry['content'].append(value)
            truncated.extend('content.' + str(content_index) + '.' + name for name in content_truncated)
        if len(content_items) > 5:
            truncated.append('content')
        entry['truncated_fields'] = truncated
        size = len(json.dumps(entry, ensure_ascii=False))
        if page_characters + size > 60_000:
            break
        entries.append(entry)
        page_characters += size
    warnings = []
    if parsed.get('bozo'):
        warnings.append('Feed recuperado con anomalías: ' + str(parsed.get('bozo_exception'))[:200])
    feed, truncated = bounded_fields({field: parsed.feed.get(field) for field in fields})
    next_offset = offset + len(entries)
    return {
        'document_format': 'feed',
        'parser': {'name': 'feedparser', 'version': importlib.metadata.version('feedparser')},
        'feed_version': parsed.version,
        'feed': feed,
        'feed_truncated_fields': truncated,
        'entries': entries,
        'entry_total': len(parsed.entries),
        'offset': offset,
        'next_offset': next_offset if next_offset < len(parsed.entries) else None,
        'warnings': warnings,
    }


def read_html(raw, source_url, offset, limit):
    import trafilatura

    document = trafilatura.bare_extraction(
        raw, url=source_url or None, with_metadata=True, include_comments=False,
        date_extraction_params={'extensive_search': False},
    )
    if document is None or not document.text:
        raise ValueError('El HTML no contiene texto principal extraíble')
    fields = ('title', 'author', 'url', 'hostname', 'description', 'sitename',
              'date', 'categories', 'tags', 'language', 'license')
    text = document.text
    metadata, truncated = bounded_fields({field: getattr(document, field, None) for field in fields})
    end = offset + limit
    return {
        'document_format': 'html',
        'parser': {'name': 'trafilatura', 'version': importlib.metadata.version('trafilatura')},
        'text': text[offset:end],
        'text_characters': len(text),
        'offset': offset,
        'next_offset': end if end < len(text) else None,
        'text_truncated': offset > 0 or end < len(text),
        'metadata': metadata,
        'metadata_truncated_fields': truncated,
        'warnings': [],
    }


def main():
    sys.addaudithook(offline_only)
    try:
        raw = sys.stdin.buffer.read(500_001)
        if not raw or len(raw) > 500_000:
            raise ValueError('Documento vacío o demasiado grande')
        document_format, source_url, offset, limit = sys.argv[1:]
        if document_format == 'feed':
            result = read_feed(raw, source_url, int(offset), int(limit))
        elif document_format == 'html':
            result = read_html(raw, source_url, int(offset), int(limit))
        else:
            raise ValueError('Formato documental inválido')
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    except Exception as exc:
        sys.stdout.buffer.write(json.dumps({'error': str(exc)[:300]}).encode('utf-8'))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
