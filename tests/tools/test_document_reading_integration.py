"""Offline fixtures exercise the Studio dispatch and the real isolated worker."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from lib import document_reading as reader
from lib import production_studio as studio
from lib.production_agent import LocalAgent


RSS = b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Offline RSS</title><link>https://example.test/</link>
<item><guid isPermaLink="false">rss-1</guid><title>First item</title><link>https://example.test/one</link>
<pubDate>Mon, 23 Nov 2026 10:00:00 GMT</pubDate><description>Fixture summary</description></item>
<item><guid isPermaLink="false">rss-2</guid><title>Second item</title></item></channel></rss>'''
ATOM = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="es">
<id>urn:offline:feed</id><title>Datos sintéticos</title><updated>2026-11-23T10:00:00Z</updated>
<entry><id>urn:offline:entry</id><title>Átomo</title><link href="https://example.test/atom"/>
<updated>2026-11-23T10:00:00Z</updated><author><name>Ana</name></author>
<content type="text">Contenido conservado de una prueba offline.</content></entry></feed>'''.encode('utf-8')
HTML = '''<!DOCTYPE html><html lang="es"><head>
<meta charset="utf-8"><title>Artículo sintético</title>
<meta name="author" content="Ana Ejemplo"><meta name="description" content="Descripción offline">
<meta property="og:site_name" content="Diario de prueba">
<meta property="article:published_time" content="2026-11-22T10:00:00Z">
<link rel="canonical" href="https://example.test/article"></head>
<body><nav>MENÚ DESCARTADO</nav><article><h1>Artículo sintético</h1>
<p>Esta noticia sintética permite comprobar la extracción de texto principal desde un archivo
HTML local. La prueba conserva el autor, la fecha declarada y el enlace de procedencia.
Toda la información de este artículo forma parte de una entrada controlada para las pruebas.</p>
<p>El segundo párrafo aporta contexto suficiente para identificar el cuerpo del artículo.
El procesamiento ocurre sin consultar servidores externos y conserva caracteres como á y ñ.</p>
</article><script>IGNORE_THIS_SCRIPT</script></body></html>'''.encode('utf-8')


class DocumentReadingIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.agent = LocalAgent.__new__(LocalAgent)
        self.agent.path = self.root

    def read(self, name, raw, kind, **options):
        python = reader.RUNTIME / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if not python.is_file():
            self.skipTest('Provision the isolated document-reading runtime for parser integration tests')
        source = self.root / name
        source.write_bytes(raw)
        result = self.agent.dispatch('read_project_file', {
            'path': name, 'document_format': kind, **options,
        })
        self.assertEqual(source.read_bytes(), raw)
        self.assertEqual(result['provenance']['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['provenance']['bytes'], len(raw))
        self.assertEqual(result['provenance']['project_relative_path'], name)
        self.assertFalse(result['provenance']['network_accessed'])
        self.assertEqual(result['content_role'], 'untrusted_source_document')
        return result

    def test_rss_pagination_dates_and_provenance(self):
        first = self.read('feed.rss', RSS, 'feed', limit=1, source_url='https://example.test/rss')
        self.assertEqual(first['feed_version'], 'rss20')
        self.assertEqual(first['entry_total'], 2)
        self.assertEqual(first['entries'][0]['id'], 'rss-1')
        self.assertEqual(first['entries'][0]['published'], 'Mon, 23 Nov 2026 10:00:00 GMT')
        self.assertEqual(first['next_offset'], 1)
        second = self.read('feed.rss', RSS, 'feed', offset=1, limit=1)
        self.assertEqual(second['entries'][0]['entry_index'], 1)
        self.assertEqual(second['entries'][0]['id'], 'rss-2')
        self.assertIsNone(second['next_offset'])
        self.assertFalse(first['provenance']['source_url_verified'])

    def test_atom_preserves_unicode_author_and_content(self):
        result = self.read('feed.atom', ATOM, 'feed')
        self.assertEqual(result['feed_version'], 'atom10')
        entry = result['entries'][0]
        self.assertEqual(entry['title'], 'Átomo')
        self.assertEqual(entry['author'], 'Ana')
        self.assertIn('Contenido conservado', entry['content'][0]['value'])

    def test_html_text_and_declared_metadata(self):
        result = self.read('article.html', HTML, 'html', source_url='https://example.test/input')
        self.assertIn('segundo párrafo', result['text'])
        self.assertNotIn('IGNORE_THIS_SCRIPT', result['text'])
        self.assertNotIn('MENÚ DESCARTADO', result['text'])
        self.assertEqual(result['metadata']['title'], 'Artículo sintético')
        self.assertEqual(result['metadata']['author'], 'Ana Ejemplo')
        self.assertEqual(result['metadata']['url'], 'https://example.test/article')
        self.assertEqual(result['provenance']['supplied_source_url'], 'https://example.test/input')
        self.assertEqual(result['metadata']['date'], '2026-11-22')
        self.assertFalse(result['text_truncated'])

    def test_html_declared_charset(self):
        raw = HTML.decode('utf-8').replace('utf-8', 'iso-8859-1').encode('iso-8859-1')
        result = self.read('latin.html', raw, 'html')
        self.assertIn('párrafo', result['text'])

    def test_plain_reader_keeps_existing_contract(self):
        path = self.root / 'notes.txt'
        path.write_text('Texto original', encoding='utf-8')
        self.assertEqual(self.agent.dispatch('read_project_file', {'path': 'notes.txt'}), {
            'path': str(path), 'content': 'Texto original',
        })

    def test_parent_paths_and_unsupported_options_are_rejected(self):
        outside = self.root.parent / (self.root.name + '-outside.rss')
        outside.write_bytes(RSS)
        self.addCleanup(outside.unlink)
        with self.assertRaises(ValueError):
            self.agent.dispatch('read_project_file', {
                'path': str(outside), 'document_format': 'feed',
            })
        (self.root / 'test.html').write_bytes(HTML)
        for options in ({'source_url': 'ftp://example.test/'}, {'source_url': 'file:///private'},
                        {'source_url': 'https://user:secret@example.test/'}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.agent.dispatch('read_project_file', {
                    'path': 'test.html', 'document_format': 'html', **options,
                })

    def test_empty_oversized_and_nonfeed_documents_fail(self):
        for raw in (b'', b'x' * 500_001, b'https://example.test/secret', b'not a feed'):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                self.read('invalid.rss', raw, 'feed')

    def test_feed_dtd_and_entities_are_rejected(self):
        raw = b'<!DOCTYPE rss [<!ENTITY secret SYSTEM "file:///private">]><rss>&secret;</rss>'
        with self.assertRaisesRegex(ValueError, 'DTD'):
            self.read('entities.rss', raw, 'feed')

    def test_missing_runtime_and_timeout_are_actionable(self):
        path = self.root / 'feed.rss'
        path.write_bytes(RSS)
        with patch.object(reader, 'RUNTIME', self.root / 'absent'), self.assertRaisesRegex(ValueError, 'aislado'):
            reader.read_document(path, self.root, 'feed')
        runtime = self.root / 'mock-runtime'
        python = runtime / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        python.parent.mkdir(parents=True)
        python.touch()
        with patch.object(reader, 'RUNTIME', runtime), patch.object(
                reader.subprocess, 'run', side_effect=subprocess.TimeoutExpired('worker', 45)):
            with self.assertRaisesRegex(ValueError, '45 segundos'):
                reader.read_document(path, self.root, 'feed')

    def test_worker_network_guard(self):
        from lib.document_reading_worker import offline_only
        for event in ('socket.connect', 'socket.getaddrinfo', 'socket.__new__'):
            with self.assertRaises(PermissionError):
                offline_only(event, ())

    def test_structured_options_require_format(self):
        (self.root / 'notes.txt').write_text('Plain input', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'document_format'):
            self.agent.dispatch('read_project_file', {'path': 'notes.txt', 'limit': 1})

    def test_symlink_cannot_escape_project(self):
        outside = self.root.parent / (self.root.name + '-linked.rss')
        outside.write_bytes(RSS)
        self.addCleanup(outside.unlink)
        link = self.root / 'linked.rss'
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest('Symbolic links unavailable on this host')
        with self.assertRaises(ValueError):
            self.agent.dispatch('read_project_file', {
                'path': 'linked.rss', 'document_format': 'feed',
            })

    def test_feed_pages_fit_agent_transport_and_keep_all_entry_indexes(self):
        items = ''.join(
            '<item><guid isPermaLink="false">item-' + str(index) + '</guid>'
            '<description>' + 'x' * 1900 + '</description></item>'
            for index in range(180))
        raw = ('<rss version="2.0"><channel><title>Large feed</title>' + items + '</channel></rss>').encode()
        indexes = []
        offset = 0
        while offset is not None:
            page = self.read('large.rss', raw, 'feed', offset=offset, limit=100)
            self.assertLess(len(json.dumps(page, ensure_ascii=False)), 100_000)
            indexes.extend(entry['entry_index'] for entry in page['entries'])
            self.assertIn('summary', page['entries'][0]['truncated_fields'])
            next_offset = page['next_offset']
            if next_offset is not None:
                self.assertGreater(next_offset, offset)
            offset = next_offset
        self.assertEqual(indexes, list(range(180)))

    def test_html_character_pages_fit_transport_and_cover_full_text(self):
        paragraphs = ''.join(
            '<p>Offline paragraph number ' + str(index) +
            ' contains synthetic article text for testing complete extraction and character pagination.</p>'
            for index in range(800))
        raw = ('<html><body><article>' + paragraphs + '</article></body></html>').encode()
        first = self.read('large.html', raw, 'html', limit=50_000)
        self.assertGreater(first['text_characters'], 50_000)
        self.assertEqual(first['next_offset'], 50_000)
        self.assertLess(len(json.dumps(first, ensure_ascii=False)), 100_000)
        second = self.read('large.html', raw, 'html', offset=first['next_offset'], limit=50_000)
        self.assertIsNone(second['next_offset'])
        self.assertEqual(len(first['text'] + second['text']), first['text_characters'])

    def test_feed_bytes_are_not_reinterpreted_as_a_filename(self):
        target = self.root / 'real.rss'
        target.write_bytes(RSS)
        with self.assertRaises(ValueError):
            self.read('pointer.rss', str(target).encode(), 'feed')

    def test_agent_run_delivers_parsed_evidence_to_its_transport(self):
        python = reader.RUNTIME / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if not python.is_file():
            self.skipTest('Provision the isolated document-reading runtime for transport integration')
        project = self.root / 'transport'
        project.mkdir()
        (project / 'feed.atom').write_bytes(ATOM)
        studio.save_json(project / 'production_request.json', {
            'project_id': 'transport', 'title': 'Offline transport fixture',
            'brief': 'Read a saved synthetic feed', 'pipeline': 'animation',
            'language': 'es', 'automatic': False,
        })
        received = []
        contracts = []

        def chat(messages, tools):
            contracts.append(messages[0]['content'])
            if messages[-1]['role'] == 'tool':
                received.append(json.loads(messages[-1]['content']))
                return {'content': 'Offline document fixture checked'}
            return {'tool_calls': [{'function': {
                'name': 'read_project_file',
                'arguments': {'path': 'feed.atom', 'document_format': 'feed'},
            }}]}

        with patch.object(studio, 'PROJECTS_DIR', self.root), patch.object(
                studio, 'CONFIG_DIR', self.root / 'config'), patch(
                'lib.resource_sampling.ResourceSampler') as sampler:
            sampler.return_value.finish.return_value = {}
            worker = LocalAgent('transport', chat=chat)
            worker.run()
        self.assertEqual(len(received), 1)
        self.assertIn('Recorre next_offset para leer páginas adicionales.', contracts[0])
        self.assertNotIn('error', received[0])
        self.assertEqual(received[0]['entries'][0]['title'], 'Átomo')
        self.assertEqual(received[0]['provenance']['sha256'], hashlib.sha256(ATOM).hexdigest())
        self.assertEqual(studio.read_json(project / 'job.json')['status'], 'awaiting_input')
