"""Offline checks for the saved video-evidence gallery; no extraction or inference."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from backlot.editor_routes import create_editor_router
from lib import production_studio as studio
from lib.video_evidence_gallery import contact_sheet_bytes, list_saved_evidence


class VideoEvidenceGalleryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'project'
        (self.root / 'artifacts' / 'evidence').mkdir(parents=True)
        self.image = self.root / 'artifacts' / 'evidence' / 'contact-sheet.jpg'
        Image.new('RGB', (2, 2), '#18324a').save(self.image, format='JPEG')
        self.source_sha = 'a' * 64
        self.call_id = 'call-evidence-1'
        self.report = {
            'contract': 'local-video-evidence-v1', 'source_sha256': self.source_sha,
            'source_duration_seconds': 20.0, 'requested_range': [9.5, 11.5],
            'frame_count': 1, 'frames': [{'path': str(self.root / 'private-frame.png'),
                'pts_seconds': 10.5, 'pts_rational': [21, 2], 'clock': 'source_presentation_time',
                'timestamp_method': 'ffprobe+ffmpeg_showinfo'}],
            'contact_sheet': str(self.image),
            'files': [{'name': self.image.name, 'sha256': hashlib.sha256(self.image.read_bytes()).hexdigest(),
                       'bytes': self.image.stat().st_size}],
            'coverage': 'partial_sampled_images_only', 'gaps': 'Audio and motion not inspected',
            'sampling': 'uniform_targets_selected_on_real_decoded_pts', 'inference_executed': False,
            'transcript': {'status': 'reused_declared_not_independently_aligned', 'asr_executed': False,
                'coverage': 'saved Portuguese words', 'word_data_sha256': 'b' * 64,
                'provenance': {'engine': 'faster-whisper', 'model': 'large-v3', 'language': 'por',
                               'path': 'must-not-leak'},
                'words': [{'index': 0, 'word': 'Olá', 'start_seconds': 10.0,
                           'end_seconds': 10.4, 'partial': False}]}}
        self.tool_content = json.dumps({'success': True, 'data': self.report}, ensure_ascii=False)

    def tearDown(self):
        self.temp.cleanup()

    def save_session(self, message=None):
        (self.root / 'agent_session.json').write_text(json.dumps({'version': 2, 'messages': [
            message or {'role': 'tool', 'tool_name': 'frame_sampler', 'tool_call_id': self.call_id,
                        'content': self.tool_content}]}), encoding='utf-8')

    def test_saved_pts_words_and_jpeg_are_read_without_asr(self):
        self.save_session()
        result = list_saved_evidence(self.root)
        self.assertEqual(result['contract'], 'local-video-evidence-gallery-v1')
        self.assertTrue(result['read_only'])
        self.assertFalse(result['asr_executed'])
        self.assertEqual(len(result['items']), 1)
        item = result['items'][0]
        self.assertEqual(item['frames'][0]['pts_rational'], [21, 2])
        self.assertEqual(item['transcript']['words'][0]['text'], 'Olá')
        self.assertEqual(item['transcript']['provenance']['model'], 'large-v3')
        self.assertNotIn('path', json.dumps(item))
        self.assertEqual(contact_sheet_bytes(self.root, item['id']), self.image.read_bytes())

    def test_compacted_receipt_requires_matching_archive_and_call_id(self):
        artifact_name = 'agent_receipt_' + 'c' * 64
        receipt_sha = hashlib.sha256(self.tool_content.encode('utf-8')).hexdigest()
        archive = {'version': 1, 'archive_id': 'c' * 64, 'tool_name': 'frame_sampler',
                   'tool_call_id': self.call_id, 'receipt_sha256': receipt_sha,
                   'content': self.tool_content}
        (self.root / 'artifacts' / f'{artifact_name}.json').write_text(json.dumps(archive), encoding='utf-8')
        summary = {'compacted': True, 'tool_name': 'frame_sampler', 'tool_call_id': self.call_id,
                   'receipt_sha256': receipt_sha, 'artifact_name': artifact_name,
                   'archive_path': f'artifacts/{artifact_name}.json'}
        self.save_session({'role': 'tool', 'tool_name': 'frame_sampler', 'tool_call_id': self.call_id,
                           'content': json.dumps(summary)})
        self.assertEqual(len(list_saved_evidence(self.root)['items']), 1)
        summary['tool_call_id'] = 'other-call'
        self.save_session({'role': 'tool', 'tool_name': 'frame_sampler', 'tool_call_id': self.call_id,
                           'content': json.dumps(summary)})
        result = list_saved_evidence(self.root)
        self.assertEqual(result['items'], [])
        self.assertIn('saved_evidence_skipped', result['warnings'])

    def test_tampered_or_outside_contact_sheet_is_not_returned(self):
        self.save_session()
        item = list_saved_evidence(self.root)['items'][0]
        self.image.write_bytes(b'changed')
        with self.assertRaises(FileNotFoundError):
            contact_sheet_bytes(self.root, item['id'])
        self.image.write_bytes(b'')
        outside = Path(self.temp.name) / 'outside.jpg'
        Image.new('RGB', (1, 1)).save(outside, format='JPEG')
        self.report['contact_sheet'] = str(outside)
        self.report['files'][0] = {'name': outside.name,
            'sha256': hashlib.sha256(outside.read_bytes()).hexdigest(), 'bytes': outside.stat().st_size}
        self.tool_content = json.dumps({'success': True, 'data': self.report})
        self.save_session()
        self.assertEqual(list_saved_evidence(self.root)['items'], [])

    def test_missing_session_is_read_only_and_empty(self):
        result = list_saved_evidence(self.root)
        self.assertEqual(result['items'], [])
        self.assertFalse((self.root / 'agent_session.json').exists())

    def test_api_returns_same_project_scoped_read_only_contact_sheet(self):
        self.save_session()
        original = studio.project_path
        studio.project_path = lambda project_id: self.root if project_id == 'test-project' else (_ for _ in ()).throw(FileNotFoundError())
        try:
            app = FastAPI()
            async def body(_request, _limit=None):
                return {}
            app.include_router(create_editor_router(body))
            with TestClient(app) as client:
                response = client.get('/api/studio/editor/test-project/video-evidence')
                self.assertEqual(response.status_code, 200)
                item = response.json()['items'][0]
                image = client.get(item['contact_sheet_url'])
                self.assertEqual(image.status_code, 200)
                self.assertEqual(image.headers['content-type'], 'image/jpeg')
                self.assertEqual(image.headers['cache-control'], 'private, no-store')
                self.assertEqual(image.content, self.image.read_bytes())
                self.assertEqual(client.get('/api/studio/editor/other-project/video-evidence').status_code, 404)
        finally:
            studio.project_path = original


if __name__ == '__main__':
    unittest.main()
