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
        selected_profiles=[]
        profiles={'presets':[{'id':'wan22-5b-t2v','label':'Wan 2.2 · 5B · texto a video','note':'Perfil local de prueba','required_models':['wan2.2_ti2v_5B_fp16.safetensors']}],'current':{'preset':'wan22-14b-t2v-4step'}}
        page.route('**/api/studio/wan-presets',lambda r:r.fulfill(json=profiles))
        def select_profile(route):
            selected_profiles.append(route.request.post_data_json);profiles['current']=selected_profiles[-1];route.fulfill(json=profiles['current'])
        page.route('**/api/studio/adapters/wan',select_profile)
        page.get_by_role('button',name='Ver perfiles y modelo seleccionado').click()
        page.locator('#wan-profile-list summary').click()
        page.get_by_role('button',name='Seleccionar Wan 2.2 · 5B · texto a video',exact=True).click()
        page.wait_for_function('document.querySelector("#wan-profile-list").textContent.includes("Selección actual: wan22-5b-t2v")')
        assert selected_profiles==[{'preset':'wan22-5b-t2v'}]
        bindings=[]
        page.route('**/api/studio/adapters',lambda r:r.fulfill(json=[{'family':'kokoro','backend':'native','ready':False,'problems':['Falta runtime'],'configuration':{},'model_dir':None,'python_executable':'/runtime/python','available_voices':['ef_dora']}]))
        def save_binding(route):
            bindings.append(route.request.post_data_json);route.fulfill(json=bindings[-1])
        page.route('**/api/studio/adapters/kokoro',save_binding)
        page.get_by_role('button',name='Detectar adaptadores y dependencias').click()
        page.locator('#adapter-list summary').click()
        page.locator('#adapter-list [name=model_dir]').fill('/models/kokoro')
        page.get_by_role('button',name='Guardar adaptador',exact=True).click()
        page.wait_for_function('document.querySelector("#notice").textContent.includes("kokoro guardado")')
        assert bindings[0]['model_dir']=='/models/kokoro'
        check_id='check-123456abcdef';requests=[];reviews=[]
        def create_check(route):
            requests.append(route.request.post_data_json);route.fulfill(json={'id':check_id})
        measured={'id':check_id,'created_at':'fixture','status':'review_required','message':'Escucha la muestra','active':False,'request':{'voice':'ef_dora'},'audio':{'decoded':True,'duration_seconds':1},'audio_url':'/api/studio/validations/'+check_id+'/audio','models':{},'quality_review_required':True}
        page.route('**/api/studio/validations',create_check)
        page.route('**/api/studio/validations/'+check_id,lambda r:r.fulfill(json=measured))
        page.route('**/api/studio/validations/'+check_id+'/audio',lambda r:r.fulfill(body=b'fixture',content_type='audio/wav'))
        def review_check(route):
            reviews.append(route.request.post_data_json);measured['human_review']=reviews[-1];route.fulfill(json=measured)
        page.route('**/api/studio/validations/'+check_id+'/review',review_check)
        page.locator('#voice-check [name=voice]').select_option('ef_dora')
        page.get_by_role('button',name='Ejecutar prueba local',exact=True).click()
        page.locator('#validation-result h3').wait_for()
        assert requests[0]['voice']=='ef_dora' and requests[0]['transcribe'] is True
        assert page.locator('#validation-audio').get_attribute('src').endswith('/audio')
        page.get_by_role('button',name='Aprobar voz después de escuchar',exact=True).click()
        page.wait_for_function('document.querySelector("#validation-result pre").textContent.includes("accepted")')
        assert reviews[0]['accepted'] is True

        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert errors==[]
        browser.close()
