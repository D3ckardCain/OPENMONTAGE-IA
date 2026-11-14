"""Real local UI flow with synthetic API fixtures; no YouTube requests."""
import json
import pytest
pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright
from tests.backlot.test_ui_bug_bash import staged_backlot_server


def test_channel_filters_results_and_mobile(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        page=browser.new_page(viewport={'width':1280,'height':900})
        page.route('**/api/research/channels/status',lambda route:route.fulfill(json={'configured':True}))
        captured=[]
        def respond(route):
            captured.append(route.request.post_data_json)
            route.fulfill(json={'result_type':'channels','retrieved_at_utc':'2026-11-14T00:00:00Z',
                'results':[{'id':'UC'+'a'*22,'title':'<img src=x onerror=alert(1)>',
                    'viewCount':2000000,'subscriberCount_public_rounded':10000,'videoCount':30,
                    'content_review':{'matched':1,'inspected':10,'sample_requested':10}}],
                'scope':{'candidate_channels':50,'lookup_mode':'handle' if route.request.post_data_json['query'].startswith('@') else 'keywords','content_filter_scope':'recent_upload_sample'},'excluded':{}})
        page.route('**/api/research/channels',respond)
        page.goto(staged_backlot_server+'/channels')
        page.get_by_role('button',name='Filtros',exact=False).click()
        page.locator('[name=min_views]').fill('1000000')
        page.locator('[name=min_subscribers]').fill('1000')
        page.locator('[name=language]').select_option('es')
        page.locator('[name=content_type]').select_option('medium')
        page.locator('[name=published_within]').select_option('month')
        page.get_by_role('button',name='Aplicar filtros').click()
        page.locator('#query').fill('animales')
        page.get_by_role('button',name='Buscar canales',exact=True).click()
        page.locator('.channel').wait_for()
        assert captured[0]['filters']['min_views']==1000000
        assert captured[0]['filters']['min_subscribers']==1000
        assert captured[0]['filters']['published_within']=='month'
        assert page.locator('.channel h2').inner_text()=='<img src=x onerror=alert(1)>'
        assert page.locator('.channel img').count()==0
        assert 'canales encontrados' in page.locator('#status').inner_text()
        page.locator('#query').fill('@example')
        page.get_by_role('button',name='Buscar canales',exact=True).click()
        page.locator('.channel').wait_for()
        assert captured[1]['query']=='@example'
        assert 'Canal identificado directamente' in page.locator('#scope').inner_text()
        # Cancel must not apply edited filters, and applying filters clears old results.
        page.get_by_role('button',name='Filtros',exact=False).click()
        page.locator('[name=min_views]').fill('9999999')
        page.get_by_role('button',name='Cancelar',exact=True).click()
        page.get_by_role('button',name='Filtros',exact=False).click()
        assert page.locator('[name=min_views]').input_value()=='1000000'
        page.get_by_role('button',name='Restablecer todo').click()
        page.get_by_role('button',name='Aplicar filtros').click()
        assert page.locator('.channel').count()==0
        page.set_viewport_size({'width':390,'height':844})
        page.get_by_role('button',name='Filtros',exact=False).click()
        assert page.locator('dialog').is_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.get_by_role('button',name='Cancelar',exact=True).click()
        page.unroute('**/api/research/channels')
        page.route('**/api/research/channels',lambda route:route.fulfill(status=429,json={
            'error':'La cuota de YouTube se agotó. Espera antes de repetir.',
            'error_code':'QUOTA_EXCEEDED','retryable':False}))
        page.get_by_role('button',name='Buscar canales',exact=True).click()
        page.get_by_text('La cuota de YouTube se agotó. Espera antes de repetir.',exact=True).wait_for()
        assert page.locator('.channel').count()==0
        assert page.locator('#query').input_value()=='@example'
        assert page.get_by_role('button',name='Buscar canales',exact=True).is_enabled()
        batches=[]
        def batch_response(route):
            batches.append(route.request.post_data_json)
            route.fulfill(status=429,json={'error':'Cuota agotada en segundo tema',
                'error_code':'QUOTA_EXCEEDED','result_type':'channels','complete':False,'partial':True,
                'queries':['animales','geografía'],'completed_queries':[{'query':'animales'}],
                'pending_queries':['geografía'],'results':[{'id':'UC'+'b'*22,'title':'Canal de prueba',
                    'viewCount':5000000,'subscriberCount_public_rounded':1000,'videoCount':10,
                    'matched_queries':['animales']}]})
        page.route('**/api/research/channels/batch',batch_response)
        page.locator('#query').fill('animales\ngeografía')
        page.get_by_role('button',name='Buscar canales',exact=True).click()
        page.get_by_text('Cuota agotada en segundo tema',exact=True).wait_for()
        assert batches[0]['queries']==['animales','geografía']
        assert batches[0]['max_requests']==300
        assert 'LOTE INCOMPLETO' in page.locator('#scope').inner_text()
        assert 'geografía' in page.locator('#scope').inner_text()
        assert page.locator('.channel').count()==1
        assert 'animales' in page.locator('.channel').inner_text()
        browser.close()
