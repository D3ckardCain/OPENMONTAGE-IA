"""Synthetic KVA only; no source video, app, spatial measurements or pictures."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backlot.studio_routes import create_studio_router
from lib import production_studio as studio
from lib import kinovea_annotations as reader
from lib.pipeline_loader import load_pipeline_readonly
from lib.production_agent import LocalAgent
from tools.analysis import kinovea_annotations as tool
from tools.tool_registry import ToolRegistry

XML = b'''<?xml version="1.0"?><KinoveaVideoAnalysis>
<FormatVersion>2.1</FormatVersion><Producer>synthetic</Producer><FullPath>private-video.mp4</FullPath>
<AverageTimeStampsPerFrame>1000</AverageTimeStampsPerFrame><TimeOrigin>10000</TimeOrigin>
<FirstTimeStamp>0</FirstTimeStamp><VideoFramerate>25</VideoFramerate><CaptureFramerate>250</CaptureFramerate>
<Keyframes><Keyframe><Timestamp>0</Timestamp><Name>Before</Name><Drawings><Angle/><Line/></Drawings></Keyframe>
<Keyframe><Timestamp>10000</Timestamp><Name>Origin</Name></Keyframe>
<Keyframe><Timestamp>20000</Timestamp><Name>After</Name><Drawings><Line/></Drawings></Keyframe></Keyframes>
</KinoveaVideoAnalysis>'''


class KinoveaAnnotationsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root / 'fixture'
        self.project.mkdir()
        replacement = patch.object(studio, 'project_path', return_value=self.project)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.path = self.project / 'fixture.kva'
        self.path.write_bytes(XML)
        self.inputs = {'project_id': 'fixture', 'input_path': 'fixture.kva'}

    def inspect(self, raw=None):
        if raw is not None:
            self.path.write_bytes(raw)
        return tool.KinoveaAnnotations().execute(self.inputs)

    def test_origin_slow_motion_and_drawing_counts_preserve_input(self):
        with patch('socket.socket', side_effect=AssertionError('no network')):
            r = self.inspect()
        self.assertTrue(r.success, r.error)
        self.assertEqual([k['playback_seconds_from_time_origin'] for k in r.data['keyframes']], [-0.4, 0, 0.4])
        self.assertEqual([k['capture_seconds_from_time_origin'] for k in r.data['keyframes']], [-0.04, 0, 0.04])
        self.assertEqual(r.data['keyframes'][0]['drawing_types'], {'Angle': 1, 'Line': 1})
        self.assertEqual(r.data['provenance']['input_sha256'], hashlib.sha256(XML).hexdigest())
        self.assertEqual(self.path.read_bytes(), XML)
        self.assertNotIn('private-video', str(r.data))
        self.assertFalse(r.data['video_loaded'])
        self.assertFalse(r.data['drawings_evaluated'])
        self.assertFalse(r.data['content_generated'])

    def test_missing_clock_metadata_does_not_invent_time_or_fps(self):
        raw = b'<KinoveaVideoAnalysis><FormatVersion>2.1</FormatVersion><Keyframes><Keyframe><Timestamp>100000</Timestamp></Keyframe></Keyframes></KinoveaVideoAnalysis>'
        r = self.inspect(raw)
        self.assertTrue(r.success, r.error)
        self.assertEqual(r.data['keyframes'][0]['timestamp_raw'], 100000)
        self.assertNotIn('playback_seconds_from_time_origin', r.data['keyframes'][0])
        self.assertIsNone(r.data['timing_declared']['video_framerate'])
        r = self.inspect(XML.replace(b'<CaptureFramerate>250', b'<CaptureFramerate>0'))
        self.assertTrue(r.success, r.error)
        self.assertNotIn('capture_seconds_from_time_origin', r.data['keyframes'][0])

    def test_rounding_ties_to_even_and_fractional_frame_ticks(self):
        raw = XML.replace(b'<Timestamp>0', b'<Timestamp>10500').replace(b'<Timestamp>20000', b'<Timestamp>11500')
        r = self.inspect(raw)
        self.assertTrue(r.success, r.error)
        self.assertEqual([r.data['keyframes'][i]['frame_offset_from_time_origin'] for i in (0, 2)], [0, 2])

    def test_versions_duplicates_and_invalid_timing_rejected(self):
        for raw in (XML.replace(b'>2.1<', b'>2.0<'), XML.replace(b'>2.1<', b'>9.0<'),
                    XML.replace(b'<VideoFramerate>25', b'<VideoFramerate>NaN'),
                    XML.replace(b'<VideoFramerate>25', b'<VideoFramerate>0'),
                    XML.replace(b'<VideoFramerate>25', b'<VideoFramerate>1e-10000'),
                    XML.replace(b'<TimeOrigin>10000', b'<TimeOrigin>not-an-integer'),
                    XML.replace(b'<Timestamp>0</Timestamp>', b'<Timestamp>0</Timestamp><Timestamp>1</Timestamp>'),
                    XML.replace(b'<TimeOrigin>10000</TimeOrigin>', b'<TimeOrigin>1</TimeOrigin><TimeOrigin>2</TimeOrigin>')):
            self.assertFalse(self.inspect(raw).success)

    def test_external_entities_dtd_encoding_and_malformed_xml_rejected(self):
        for raw in (b'<!DOCTYPE KinoveaVideoAnalysis SYSTEM "https://remote/dtd">'+XML.split(b'?>', 1)[1],
                    b'<!DOCTYPE DOC [<!ENTITY e SYSTEM "file:///private">]><DOC>&e;</DOC>',
                    b'<?xml version="1.0" encoding="unknown-codec"?><KinoveaVideoAnalysis/>', b'<bad/>', b'<bad>'):
            self.assertFalse(self.inspect(raw).success)

    def test_limits_and_workspace_escape(self):
        with patch.object(reader, 'MAX_BYTES', 10):
            self.assertFalse(self.inspect().success)
        self.assertFalse(self.inspect(b'<root>' * 65 + b'</root>' * 65).success)
        outside = self.root / 'outside.kva'
        outside.write_bytes(XML)
        for changes in ({'input_path': '../outside.kva'}, {'input_path': str(outside)},
                        {'input_path': 'video.mp4'}, {'output_path': 'drawing.png'}):
            self.assertFalse(tool.KinoveaAnnotations().execute({**self.inputs, **changes}).success)

    def test_api_and_real_agent_dispatch_without_processes(self):
        app = FastAPI()
        app.include_router(create_studio_router())
        with TestClient(app) as client:
            response = client.post('/api/studio/applications/kinovea/annotations', json=self.inputs)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['keyframe_count'], 3)
            self.assertEqual(client.post('/api/studio/applications/kinovea/annotations', json=self.inputs, headers={'Origin': 'https://remote.example'}).status_code, 403)
        registry = ToolRegistry()
        registry.register_module(tool)
        agent = LocalAgent.__new__(LocalAgent)
        agent.pid, agent.path, agent.registry = 'fixture', self.project, registry
        agent.request = {'pipeline': 'animation'}
        agent.manifest = load_pipeline_readonly('animation')
        agent.reads = {'skills/' + agent.manifest['stages'][0]['skill'] + '.md'}
        agent.event = Mock()
        r = agent.dispatch('execute_tool', {'name': 'kinovea_annotations', 'inputs': self.inputs})
        self.assertTrue(r['success'], r['error'])
        self.assertEqual(r['data']['keyframe_count'], 3)
        with self.assertRaisesRegex(ValueError, 'otro proyecto'):
            agent.dispatch('execute_tool', {'name': 'kinovea_annotations', 'inputs': {**self.inputs, 'project_id': 'outside'}})
