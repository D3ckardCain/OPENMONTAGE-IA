"""UI handoff contract with synthetic transport; no inference claims."""
import pytest
pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright
from tests.backlot.test_ui_bug_bash import staged_backlot_server


def test_studio_creation_control_and_review(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/api/studio/bootstrap',lambda r:r.fulfill(json={'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture-local','resource_roots':[]},'pipelines':[{'name':'animated-explainer','stages':['research','compose']}],'projects':[]}))
        captured=[]
        def create(route):
            captured.append(route.request.post_data_json)
            route.fulfill(json={'project_id':'video-fixture'})
        page.route('**/api/studio/projects',create)
        state={'request':{'title':'Animales originales'},'job':{'status':'blocked','message':'Falta el runtime compatible','events':[{'at':'fixture','kind':'error','message':'Dependencia no disponible'}]},'stages':[{'name':'research','status':'in_progress'}],'artifacts':[{'name':'source_notes.json','url':'/media/video-fixture/artifacts/source_notes.json'}],'outputs':[],'board_url':'/p/video-fixture'}
        page.route('**/api/studio/projects/video-fixture',lambda r:r.fulfill(json=state))
        actions=[]
        def action(route):
            actions.append(route.request.url.rsplit('/',1)[-1]);route.fulfill(json={'started':True})
        page.route('**/api/studio/projects/video-fixture/start',action)
        page.goto(staged_backlot_server+'/studio?reference=https%3A%2F%2Fyoutube.com%2F%40fixture&title=Canal')
        assert page.locator('#create [name=reference]').input_value()=='https://youtube.com/@fixture'
        page.locator('#create [name=title]').fill('Animales originales')
        page.locator('#create [name=brief]').fill('Video educativo original de 60 segundos')
        page.locator('#create [name=automatic]').check()
        page.get_by_role('button',name='Crear proyecto de producción',exact=True).click()
        page.locator('#status').get_by_text('blocked',exact=True).wait_for()
        assert captured[0]['title']=='Animales originales'
        assert captured[0]['automatic'] is True
        assert 'Falta el runtime' in page.locator('#message').inner_text()
        assert page.get_by_role('link',name='source_notes.json').count()==1
        assert page.locator('#outputs video').count()==0
        page.get_by_role('button',name='Iniciar / reanudar agentes').click()
        page.wait_for_function('document.querySelector("#status").textContent === "blocked"')
        assert actions==['start']
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert errors==[]
        browser.close()
