"""Synthetic metadata archives only: no pixels, application launch or inference."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backlot.studio_routes import create_studio_router
from lib import production_studio as studio
from lib import krita_document
from lib.pipeline_loader import load_pipeline_readonly
from lib.production_agent import LocalAgent
from tools.analysis import local_applications as tools
from tools.tool_registry import ToolRegistry

XML = b'''<?xml version="1.0"?><!DOCTYPE DOC PUBLIC "-//KDE//DTD krita 2.0//EN" "http://www.calligra.org/DTD/krita-2.0.dtd">
<DOC><IMAGE width="640" height="480" colorspacename="RGBA">
<layers><layer name="Group" nodetype="grouplayer" visible="1"><layers>
<layer name="Synthetic" nodetype="paintlayer" opacity="255"/></layers></layer>
<layer name="Other" nodetype="paintlayer"/></layers></IMAGE></DOC>'''


class KritaDocumentInspectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root / 'fixture'
        self.project.mkdir()
        replacement = patch.object(studio, 'project_path', return_value=self.project)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.inputs = {'project_id': 'fixture', 'input_path': 'synthetic.kra'}
        self.path = self.project / self.inputs['input_path']

    def fixture(self, xml=XML, mime=b'application/x-krita', extra=None):
        with zipfile.ZipFile(self.path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('mimetype', mime)
            archive.writestr('maindoc.xml', xml)
            for name, raw in (extra or {}).items():
                entry = zipfile.ZipInfo(name)
                entry.filename = name  # retain malformed backslashes on Windows for the rejection test
                archive.writestr(entry, raw)

    def inspect(self):
        return tools.KritaDocumentInspect().execute(self.inputs)

    def test_dimensions_hierarchy_and_provenance_without_mutation(self):
        self.fixture(extra={'mergedimage.png': b'not decoded'})
        original = self.path.read_bytes()
        result = self.inspect()
        self.assertTrue(result.success, result.error)
        self.assertEqual((result.data['width'], result.data['height']), (640, 480))
        self.assertEqual([r['parent_index'] for r in result.data['layers']], [None, 0, None])
        self.assertEqual(result.data['provenance']['input_sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(result.data['provenance']['maindoc_sha256'], hashlib.sha256(XML).hexdigest())
        self.assertEqual(self.path.read_bytes(), original)
        for key in ('pixels_decoded', 'document_modified', 'krita_launched', 'visual_quality_verified'):
            self.assertFalse(result.data[key])
        self.assertTrue(result.data['merged_preview_present'])

    def test_no_external_dtd_or_entity_resolution(self):
        self.fixture()
        with patch('socket.socket', side_effect=AssertionError('network forbidden')):
            self.assertTrue(self.inspect().success)
        for declaration in (b'<!ENTITY e "expanded">', b'<!ENTITY e SYSTEM "file:///private">'):
            self.fixture(xml=b'<!DOCTYPE DOC [' + declaration + b']><DOC><IMAGE width="1" height="1"/></DOC>')
            result = self.inspect()
            self.assertFalse(result.success)
            self.assertIn('KRITA_XML_UNSAFE', result.error)

    def test_invalid_dimensions_missing_image_and_malformed_xml(self):
        for xml in (b'<DOC/>', b'<bad/>', b'<DOC>', b'<?xml version="1.0" encoding="unknown-codec"?><DOC/>', XML.replace(b'640', b'-1'),
                    XML.replace(b'640', b'1000001'), XML.replace(b'640', b'NaN')):
            self.fixture(xml=xml)
            self.assertFalse(self.inspect().success)

    def test_unsupported_zip_mimetype_and_missing_entries(self):
        self.path.write_bytes(b'not ZIP')
        self.assertFalse(self.inspect().success)
        self.fixture(mime=b'application/zip')
        self.assertFalse(self.inspect().success)
        with zipfile.ZipFile(self.path, 'w') as archive:
            archive.writestr('mimetype', b'application/x-krita')
        self.assertFalse(self.inspect().success)

    def test_zip_path_and_duplicate_rejection_without_extraction(self):
        for name in ('../escape', '/absolute', 'C:/private', 'back\\slash'):
            self.fixture(extra={name: b'x'})
            self.assertFalse(self.inspect().success)
        self.fixture()
        with self.assertWarns(UserWarning), zipfile.ZipFile(self.path, 'a') as archive:
            archive.writestr('maindoc.xml', XML)
        self.assertFalse(self.inspect().success)
        self.assertFalse((self.root / 'escape').exists())

    def test_archive_xml_depth_and_size_limits(self):
        self.fixture()
        with patch.object(krita_document, 'MAX_ARCHIVE', 10):
            self.assertIn('KRITA_LIMIT', self.inspect().error)
        with patch.object(krita_document, 'MAX_XML', 10):
            self.assertIn('KRITA_LIMIT', self.inspect().error)
        self.fixture(xml=b'<DOC>' + b'<layers>' * 130 + b'</layers>' * 130 + b'</DOC>')
        self.assertIn('KRITA_LIMIT', self.inspect().error)

    def test_paths_and_unknown_parameters_rejected(self):
        self.fixture()
        outside = self.root / 'outside.kra'
        outside.write_bytes(self.path.read_bytes())
        for extra in ({'input_path': '../outside.kra'}, {'input_path': str(outside)},
                      {'input_path': 'missing.kra'}, {'output_path': 'overwrite.kra'}):
            result = tools.KritaDocumentInspect().execute({**self.inputs, **extra})
            self.assertFalse(result.success)

    def test_api_returns_same_metadata_and_rejects_cross_origin(self):
        self.fixture()
        app = FastAPI()
        app.include_router(create_studio_router())
        with TestClient(app) as client:
            response = client.post('/api/studio/applications/krita/inspect', json=self.inputs)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['layer_count'], 3)
            self.assertEqual(client.post('/api/studio/applications/krita/inspect', json={**self.inputs, 'input_path': '../outside.kra'}).status_code, 400)
            self.assertEqual(client.post('/api/studio/applications/krita/inspect', json=self.inputs,
                                         headers={'Origin': 'https://outside.example'}).status_code, 403)

    def test_registry_and_actual_agent_dispatch(self):
        self.fixture()
        registry = ToolRegistry()
        registry.register_module(tools)
        agent = LocalAgent.__new__(LocalAgent)
        agent.pid, agent.path, agent.registry = 'fixture', self.project, registry
        agent.request = {'pipeline': 'animation'}
        agent.manifest = load_pipeline_readonly('animation')
        agent.reads = {'skills/' + agent.manifest['stages'][0]['skill'] + '.md'}
        agent.event = Mock()
        result = agent.dispatch('execute_tool', {'name': 'krita_document_inspect', 'inputs': self.inputs})
        self.assertTrue(result['success'], result['error'])
        self.assertEqual(result['data']['layer_count'], 3)
        with patch('lib.external_applications.catalog', return_value=[{'id': 'krita', 'configured': True, 'file_found': True} ]):
            result = agent.dispatch('execute_tool', {'name': 'local_application_inventory', 'inputs': {}})
        self.assertTrue(result['success'])
        self.assertFalse(result['data']['applications_launched'])

    def test_inventory_redacts_paths_and_preserves_registration_semantics(self):
        with patch('lib.external_applications.catalog', return_value=[{
                'id': 'krita', 'configured': True, 'file_found': False, 'executable': 'private-path',
                'inspection_tools': ['krita_document_inspect']} ]):
            result = tools.LocalApplicationInventory().execute({})
        self.assertNotIn('executable', result.data['applications'][0])
        self.assertFalse(result.data['applications'][0]['file_found'])
        self.assertFalse(result.data['automation_verified'])
