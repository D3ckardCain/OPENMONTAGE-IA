"""Browser contract for explicitly loading saved-only video evidence."""
import io
import json

import pytest

pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright, expect
from PIL import Image

from tests.backlot.test_ui_bug_bash import staged_backlot_server


def test_video_evidence_is_explicit_local_and_rejects_unmatched_source(staged_backlot_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        project_response = page.request.post(
            staged_backlot_server + '/api/studio/editor/projects',
            data=json.dumps({'title': 'Synthetic saved-evidence browser test'}),
            headers={'Content-Type': 'application/json'})
        assert project_response.ok, project_response.text()
        project_id = project_response.json()['project_id']
        gallery_requests = []
        image_buffer = io.BytesIO()
        Image.new('RGB', (2, 2), '#18324a').save(image_buffer, format='JPEG')
        jpeg = image_buffer.getvalue()
        def intercept(route):
            url = route.request.url
            if url.endswith(f'/api/studio/editor/{project_id}/video-evidence'):
                gallery_requests.append(url)
                route.fulfill(json={
                    'contract': 'local-video-evidence-gallery-v1', 'read_only': True,
                    'asr_executed': False, 'coverage': 'partial_sampled_images_only', 'warnings': [],
                    'items': [{
                        'id': 'a' * 64, 'source_sha256': 'b' * 64,
                        'requested_range': [9.5, 11.5], 'frame_count': 1,
                        'frames': [{'pts_seconds': 10.5, 'pts_rational': [21, 2]}],
                        'contact_sheet_sha256': 'c' * 64,
                        'contact_sheet_url': f'/api/studio/editor/{project_id}/video-evidence/{"a" * 64}/contact-sheet',
                        'coverage': 'partial_sampled_images_only', 'gaps': 'Audio y movimiento no inspeccionados.',
                        'transcript': {'word_count': 1, 'status': 'saved', 'coverage': 'partial',
                            'asr_executed': False, 'words': [{'text': 'palabra', 'start_seconds': 10.0,
                            'end_seconds': 10.2}], 'provenance': {'engine': 'synthetic-fixture'}}
                    }]
                })
            elif url.endswith('/contact-sheet'):
                route.fulfill(status=200, body=jpeg, content_type='image/jpeg',
                              headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})
            else:
                route.continue_()
        page.route('**/api/**', intercept)
        try:
            page.goto(f'{staged_backlot_server}/studio?edit={project_id}', wait_until='domcontentloaded')
            expect(page.locator('#edit-video-evidence-refresh')).to_be_visible()
            page.wait_for_timeout(250)
            assert gallery_requests == []
            page.locator('#edit-video-evidence-refresh').click()
            expect(page.get_by_text('1 recibo(s) verificado(s)', exact=False)).to_be_visible()
            expect(page.get_by_text('palabra · 00:10.000–00:10.200', exact=True)).to_be_visible()
            expect(page.get_by_text('Ir al PTS 00:10.500 de la fuente', exact=True)).to_be_disabled()
            image = page.locator('.video-evidence-card img')
            expect(image).to_be_visible()
            page.wait_for_function("document.querySelector('.video-evidence-card img')?.naturalWidth===2")
            assert len(gallery_requests) == 1
            assert page.evaluate("() => [...document.images].filter(img => new URL(img.src).origin !== location.origin).length") == 0
        finally:
            browser.close()
