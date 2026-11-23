"""UI handoff contract with synthetic transport; no inference claims."""
import os
import pytest
pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright
from tests.backlot.test_ui_bug_bash import staged_backlot_server


def test_update_file_remote_comparison_without_local_reads(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={
            'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188',
                        'resource_roots':[],'model':''},'pipelines':[],'projects':[]}))
        page.route('**/api/studio/updates?*',lambda route:route.fulfill(json={
            'models':1,'applications':0,'untracked_catalog_files':0,'next_offset':None,'note':'fixture',
            'rows':[{'kind':'model','id':'Org/Video','catalog_file_count':1,'catalog_revisions':['a'*40]}]}))
        page.route('**/api/studio/updates/files?*',lambda route:route.fulfill(json={
            'note':'fixture','next_offset':None,'rows':[{
                'index':0,'filename':'nested/model.safetensors','destination':'D:/models/model.safetensors'}]}))
        calls=[]
        def compare(route):
            calls.append(route.request.url)
            if len(calls)==3:
                route.fulfill(status=400,json={'detail':'Fuente no disponible'})
            else:
                route.fulfill(json={'status':'remote_matches_catalog' if len(calls)==1 else 'remote_comparison_inconclusive',
                    'remote_revision':'f'*40,'remote_bytes':7,'remote_sha256':'b'*64 if len(calls)==1 else None,
                    'license_review':{'declared':['mit'],'model_card_url':'https://huggingface.co/Org/Video/blob/'+'f'*40+'/README.md','license_file_urls':[]},
                    'compatibility_review':{'reason':'Windows, adaptador y hardware sin validar.'},
                    'access_review':{'gated':'manual','private':False},
                    'note':'Comparación del catálogo; no comprueba el disco local.'})
        page.route('**/api/studio/updates/remote-file-check?*',compare)
        plan_calls=[]
        def plan(route):
            plan_calls.append(route.request.url)
            route.fulfill(json={'status':'candidate_plan_prepared','note':'Plan sin cambios en disco.',
                'original_destination':'D:/models/model.safetensors',
                'candidate':{'destination':'D:/models/.openmontage-updates/candidate.safetensors','sha256':'c'*64},
                'additional_storage_bytes_at_least':9,'pending_checks':['Validar compatibilidad real.']})
        page.route('**/api/studio/updates/plan?*',plan)
        candidate_checks=[]
        def check_candidate(route):
            candidate_checks.append(route.request.url)
            route.fulfill(json={'status':'candidate_matches_remote','bytes_read':9,
                'note':'Integridad comprobada; compatibilidad pendiente.'})
        page.route('**/api/studio/updates/candidate-check?*',check_candidate)
        space_checks=[]
        def check_space(route):
            space_checks.append(route.request.url)
            route.fulfill(json={'status':'insufficient_space','free_space_verified':True,
                'free_bytes':8,'required_bytes':9,'checked_at':'2026-11-22T20:00:00+00:00',
                'measured_path':'D:/models','note':'Medición puntual; no reserva espacio.'})
        page.route('**/api/studio/updates/candidate-space?*',check_space)
        downloads=[]
        def download(route):
            downloads.append(route.request.post_data_json)
            route.fulfill(json={'job_id':'fixture','status':'candidate_ready','bytes_present':9,'expected_bytes':9,
                'note':'Candidato separado; no cambia el modelo actual.'})
        page.route('**/api/studio/updates/downloads',download)
        document_calls=[]
        def document(route):
            document_calls.append(route.request.url)
            if len(document_calls)==1:
                route.fulfill(status=400,json={'detail':'Documento no disponible'})
            else:
                route.fulfill(json={'remote_revision':'f'*40,'sha256':'c'*64,
                    'text':'Terms <script>window.remoteExecuted=true</script>',
                    'checked_at':'2026-11-22T20:00:00+00:00','retrieval':'offline_cache' if 'offline=true' in route.request.url else 'online',
                    'note':'Texto externo; no acredita permisos ni compatibilidad.'})
        page.route('**/api/studio/updates/document?*',document)
        page.route('**/api/studio/updates/documents?*',lambda route:route.fulfill(json={
            'rows':[{'filename':'README.md','remote_revision':'f'*40,'checked_at':'2026-11-22T20:00:00+00:00'}],
            'next_offset':None,'invalid_records':0,'note':'Evidencias locales históricas.'}))
        local_reads=[]
        page.route('**/api/studio/updates/local-check?*',lambda route:local_reads.append(route.request.url))
        page.goto(staged_backlot_server+'/studio#models')
        page.locator('#updates-load').click()
        page.locator('#updates-result summary').click()
        page.get_by_role('button',name='Ver archivos y comprobar uno',exact=True).click()
        button=page.get_by_role('button',name='Comparar archivo con revisión remota actual',exact=True)
        button.click()
        page.get_by_text('El archivo remoto coincide con el catálogo',exact=True).wait_for()
        assert 'f'*40 in page.locator('[data-remote-file-check]').inner_text()
        assert 'Licencia declarada: mit' in page.locator('[data-remote-file-check]').inner_text()
        assert 'hardware sin validar' in page.locator('[data-remote-file-check]').inner_text()
        assert page.get_by_role('link',name='Consultar evidencia en la revisión').get_attribute('href')=='https://huggingface.co/Org/Video/blob/'+'f'*40+'/README.md'
        page.get_by_role('button',name='Preparar plan de candidato separado',exact=True).click()
        page.get_by_text('Plan preparado; comprobaciones pendientes',exact=True).wait_for()
        assert len(plan_calls)==1 and 'revision='+'f'*40 in plan_calls[0]
        assert 'D:/models/model.safetensors' in page.locator('[data-remote-file-check]').inner_text()
        page.get_by_role('button',name='Comprobar espacio para el candidato',exact=True).click()
        page.get_by_text('Espacio insuficiente para el candidato',exact=True).wait_for()
        assert len(space_checks)==1 and 'revision='+'f'*40 in space_checks[0]
        assert 'Libre: 8 bytes' in page.locator('[data-remote-file-check]').inner_text()
        page.get_by_role('button',name='Comprobar SHA-256 del candidato',exact=True).click()
        page.get_by_text('El candidato coincide con la revisión remota',exact=True).wait_for()
        assert len(candidate_checks)==1 and 'revision='+'f'*40 in candidate_checks[0]
        page.get_by_role('button',name='Descargar/reanudar candidato separado',exact=True).click()
        page.get_by_text('Candidato descargado y verificado; modelo actual sin cambios',exact=True).wait_for()
        assert downloads==[{'identifier':'Org/Video','index':0,'revision':'f'*40,'expected_sha256':'c'*64}]
        document_button=page.get_by_role('button',name='Leer README.md en el panel',exact=True)
        document_button.click()
        page.get_by_text('Documento no disponible',exact=True).wait_for()
        assert document_button.is_enabled()
        document_button.click()
        page.locator('[data-remote-file-check] [data-update-document-text]').wait_for()
        assert '<script>window.remoteExecuted=true</script>' in page.locator('[data-remote-file-check] [data-update-document-text]').inner_text()
        assert page.evaluate('window.remoteExecuted') is None
        assert all('revision='+'f'*40 in url and 'filename=README.md' in url for url in document_calls)
        page.get_by_role('button',name='Ver documentos guardados',exact=True).click()
        page.get_by_role('button',name='Leer copia guardada de README.md',exact=True).click()
        page.locator('[data-cached-update-documents] pre').wait_for()
        assert 'offline=true' in document_calls[-1]
        assert 'Sin consulta de red' in page.locator('[data-cached-update-documents]').inner_text()
        assert '2026-11-22T20:00:00+00:00' in page.locator('[data-cached-update-documents]').inner_text()
        button.click()
        page.get_by_text('Metadatos insuficientes para confirmar coincidencia',exact=True).wait_for()
        assert page.locator('[data-remote-file-check]').count()==1
        assert 'El archivo remoto coincide' not in page.locator('[data-remote-file-check]').inner_text()
        button.click()
        page.locator('#notice').get_by_text('Fuente no disponible',exact=True).wait_for()
        assert button.is_enabled()
        assert page.locator('[data-remote-file-check]').count()==0
        assert all('identifier=Org%2FVideo&index=0' in url for url in calls)
        assert not local_reads and not errors
        browser.close()


def test_studio_creation_control_and_review(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get("OPENMONTAGE_TEST_CHROMIUM"))
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/api/studio/bootstrap',lambda r:r.fulfill(json={'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture-local','resource_roots':[]},'pipelines':[{'name':'animated-explainer','stages':['research','compose']}],'projects':[]}))
        captured=[]
        def create(route):
            captured.append(route.request.post_data_json)
            route.fulfill(json={'project_id':'video-fixture'})
        page.route('**/api/studio/projects',create)
        state={'render_verification':{'status':'passed','outputs':[{'width':1080,'height':1920,'duration_seconds':60,'audio_streams':1,'full_decode_passed':True}]},'request':{'title':'Animales originales'},'job':{'status':'blocked','message':'Falta el runtime compatible','events':[{'at':'fixture','kind':'error','message':'Dependencia no disponible'}]},'stages':[{'name':'research','status':'in_progress'}],'artifacts':[{'name':'source_notes.json','url':'/media/video-fixture/artifacts/source_notes.json'}],'outputs':[],'board_url':'/p/video-fixture'}
        page.route('**/api/studio/projects/video-fixture',lambda r:r.fulfill(json=state))
        actions=[]
        def action(route):
            actions.append(route.request.url.rsplit('/',1)[-1]);route.fulfill(json={'started':True})
        page.route('**/api/studio/projects/video-fixture/start',action)
        page.goto(staged_backlot_server+'/studio?reference=https%3A%2F%2Fyoutube.com%2F%40fixture&title=Canal&brief=Encargo+editable')
        assert page.locator('#create [name=brief]').input_value()=='Encargo editable'
        assert page.locator('#create [name=reference]').input_value()=='https://youtube.com/@fixture'
        page.locator('#create [name=title]').fill('Animales originales')
        page.locator('#create [name=brief]').fill('Video educativo original de 60 segundos')
        page.locator('#create [name=automatic]').check()
        page.get_by_role('button',name='Crear proyecto de producción',exact=True).click()
        page.locator('#status').get_by_text('blocked',exact=True).wait_for()
        assert captured[0]['title']=='Animales originales'
        assert captured[0]['automatic'] is True
        assert 'Falta el runtime' in page.locator('#message').inner_text()
        assert '1080×1920' in page.locator('#render-verification').inner_text()
        assert 'no acredita calidad visual' in page.locator('#render-verification').inner_text()
        recoveries=[]
        def recover(route):recoveries.append(route.request.post_data_json);route.fulfill(json={'status':'completed','generation_started':False})
        page.route('**/api/studio/final-delivery/video-fixture/retry',recover)
        page.locator('#retry-final-delivery').click()
        page.get_by_text('Entrega final recuperada sin volver a generar.',exact=True).wait_for()
        assert recoveries==[{}]
        assert page.get_by_role('link',name='source_notes.json').count()==1
        assert page.locator('#outputs video').count()==0
        page.get_by_role('button',name='Iniciar / reanudar agentes').click()
        page.wait_for_function('document.querySelector("#status").textContent === "blocked"')
        assert actions==['start']
        translation_calls=[]
        def translate(route):
            if route.request.method=='POST':
                translation_calls.append(route.request.post_data_json);route.fulfill(json={'started':True,'production_started':False})
            else:route.fulfill(json={'status':'completed','language':'ko','text':'fixture translated script','resumed_segments':1})
        page.route('**/api/studio/translation/video-fixture',translate)
        page.get_by_text('Traducir un guion con MADLAD local',exact=True).click()
        page.locator('#translation-text').fill('Original script')
        page.locator('#translation-start').click()
        page.get_by_role('textbox',name='Guion traducido',exact=True).wait_for()
        assert page.get_by_role('textbox',name='Guion traducido',exact=True).input_value()=='fixture translated script'
        assert translation_calls==[{'text':'Original script'}]
        versions={'summary':{'total':3,'rendered':1,'awaiting_human':0,'blocked':0,'unavailable':1},'versions':[{'project_id':'version-en','language':'en','status':'existing'},{'project_id':'version-ko','language':'ko','status':'unavailable'},{'project_id':'version-de','language':'de','status':'existing','job_status':'rendered','verification_status':'passed','final_copy_registered':True,'can_enqueue':False}]}
        batches=[]
        page.route('**/api/studio/language-versions/video-fixture',lambda route:route.fulfill(json=versions))
        def queue_versions(route):
            batches.append(route.request.post_data_json);route.fulfill(json={'added':['version-en'],'existing':[],'generation_started':False})
        page.route('**/api/studio/queue/enqueue-batch',queue_versions)
        page.get_by_text('Preparar versiones en otros idiomas',exact=True).click()
        language_saves=[]
        def source_language(route):
            if route.request.method=='POST':language_saves.append(route.request.post_data_json)
            route.fulfill(json={'note':'Sugerencia, no verificación','detected_language':'en','confirmed_language':'en' if language_saves else None,'confirmation_outdated':False})
        page.route('**/api/studio/reference-language/video-fixture',source_language)
        page.locator('#source-language-load').click()
        page.wait_for_function('document.querySelector("#source-language").value==="en"')
        page.locator('#source-language-save').click()
        page.wait_for_function('document.querySelector("#source-language-result").textContent.includes("Confirmado: en")')
        assert language_saves==[{'language':'en'}]
        page.locator('#versions-load').click()
        page.get_by_role('checkbox',name='Seleccionar en',exact=True).check()
        assert page.get_by_role('checkbox',name='Seleccionar ko',exact=True).count()==0
        assert page.get_by_role('checkbox',name='Seleccionar de',exact=True).count()==0
        assert '3 versiones · 1 terminadas' in page.locator('#versions-result').inner_text()
        page.get_by_role('button',name='Añadir versiones seleccionadas a la cola',exact=True).click()
        page.wait_for_function('document.querySelector("#notice").textContent.includes("1 añadidas")')
        assert batches==[{'project_ids':['version-en']}]
        shared=[]
        def share_analysis(route):
            shared.append(route.request.post_data_json);route.fulfill(json={'versions':[{'project_id':'version-en','status':'shared'}],'generation_started':False})
        page.route('**/api/studio/reference-reuse/video-fixture',share_analysis)
        page.get_by_role('button',name='Compartir análisis base con las seleccionadas',exact=True).click()
        page.wait_for_function('document.querySelector("#notice").textContent.includes("version-en: shared")')
        assert shared==[{'project_ids':['version-en']}]
        page.route('**/api/studio/language-requirements/video-fixture',lambda route:route.fulfill(json={'note':'No certifica soporte de idioma','candidates':[{'family':'fixture-voice','capability':'tts','files_configured':False,'problems':['Falta voz local'],'required_modules':['fixture_module']}]}))
        page.locator('#versions-requirements').click()
        page.locator('#versions-requirements-result summary').click()
        assert 'Falta voz local' in page.locator('#versions-requirements-result').inner_text()
        assert 'fixture_module' in page.locator('#versions-requirements-result').inner_text()
        assert actions==['start']
        selected_profiles=[]
        profiles={'presets':[{'id':'wan22-5b-t2v','label':'Wan 2.2 · 5B · texto a video','note':'Perfil local de prueba','required_models':['wan2.2_ti2v_5B_fp16.safetensors']}],'current':{'preset':'wan22-14b-t2v-4step'}}
        page.route('**/api/studio/wan-presets',lambda r:r.fulfill(json=profiles))
        def select_profile(route):
            selected_profiles.append(route.request.post_data_json);profiles['current']=selected_profiles[-1];route.fulfill(json=profiles['current'])
        page.route('**/api/studio/adapters/wan',select_profile)
        page.get_by_role('button',name='Modelos y discos',exact=True).click()
        page.route('**/api/studio/resources',lambda route:route.fulfill(json={'notes':['Registro por inventario'],'inventories':[{'Nombre':'ADATA','Serie':'A','Fecha':'fixture'},{'Nombre':'SEAGATE','Serie':'B','Fecha':'fixture'}],'groups':[{'label':'MADLAD','files':[{'filename':'model.safetensors','destination_folder':'/models','status':'recorded_path_size_unknown','download_url':'https://example.org/duplicate','inventory_path_matches':[{'serial':'A','path':'D:/models/model.safetensors','bytes':123,'captured_at':'fixture'}]}]}]}))
        page.locator('#catalog').click()
        page.locator('#resource-list summary').click()
        assert 'Ruta registrada; tamaño del catálogo desconocido' in page.locator('#resource-list').inner_text()
        assert 'D:/models/model.safetensors' in page.locator('#resource-list').inner_text()
        assert page.locator('#resource-list a').count()==0
        page.route('**/api/studio/download-plan',lambda route:route.fulfill(json={'note':'Revisar inventarios','planned_files':1,'inventories':[{'Nombre':'ADATA','Serie':'A','Fecha':'fixture'},{'Nombre':'SEAGATE','Serie':'B','Fecha':'fixture'}],'filename_collisions_across_folders':[],'folders':[{'destination_folder':'D:/weights/model','files':[{'filename':'model.bin','url':'https://example.org/model.bin','size_bytes':None}]}],'without_download_url':[],'downloads_started':0}))
        page.locator('#download-plan').click()
        page.locator('#download-plan-result summary').click()
        assert page.locator('#download-plan-result textarea').input_value()=='https://example.org/model.bin'
        assert 'Guardar en: D:/weights/model' in page.locator('#download-plan-result').inner_text()
        page.get_by_role('button',name='Ver perfiles y modelo seleccionado').click()
        page.locator('#wan-profile-list summary').click()
        page.get_by_role('button',name='Seleccionar Wan 2.2 · 5B · texto a video',exact=True).click()
        page.wait_for_function('document.querySelector("#wan-profile-list").textContent.includes("Selección actual: wan22-5b-t2v")')
        assert selected_profiles==[{'preset':'wan22-5b-t2v'}]
        bindings=[]
        page.route('**/api/studio/adapters',lambda r:r.fulfill(json=[{'family':'kokoro','backend':'native','ready':False,'problems':['Falta runtime'],'configuration':{},'model_dir':None,'python_executable':'/runtime/python','available_voices':['ef_dora'],'suspicious_files':['voices/ef_bad.pt'],'optional_missing_files':['voices/ef_bad.pt']}]))
        def save_binding(route):
            bindings.append(route.request.post_data_json);route.fulfill(json=bindings[-1])
        page.route('**/api/studio/adapters/kokoro',save_binding)
        page.get_by_role('button',name='Detectar adaptadores y dependencias').click()
        page.locator('#adapter-list summary').click()
        assert 'Archivos sospechosos: voices/ef_bad.pt' in page.locator('#adapter-list').inner_text()
        assert 'Recursos opcionales ausentes o rechazados' in page.locator('#adapter-list').inner_text()
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
        page.get_by_role('button',name='Historial y pruebas',exact=True).click()
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


def test_reference_download_and_local_analysis_controls(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get("OPENMONTAGE_TEST_CHROMIUM"));page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda r:r.fulfill(json={'settings':{
            'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture',
            'resource_roots':[],'ffmpeg_path':'/local/ffmpeg','ffprobe_path':'/local/ffprobe',
            'yt_dlp_path':'/local/yt-dlp','deno_path':'/local/deno'},
            'pipelines':[{'name':'animated-explainer','stages':[]}],
            'projects':[{'project_id':'video-fixture','title':'Fixture'}]}))
        page.route('**/api/studio/projects/video-fixture',lambda r:r.fulfill(json={
            'reference_video_url':'https://www.youtube.com/watch?v=M2oOPhZtTdU',
            'request':{'title':'Fixture'},'job':{'status':'ready','message':'Ready','events':[]},
            'stages':[],'outputs':[],'artifacts':[],'board_url':'/p/video-fixture'}))
        page.route('**/api/studio/reference-video/video-fixture',lambda r:r.fulfill(json={
            'status':'partial','frames':[],'gaps':['Modelo no preparado: fixture'],
            'external_fact_check':'not_performed'}))
        requests=[]
        def analyze(route):requests.append(route.request.post_data_json);route.fulfill(json={'started':True})
        page.route('**/api/studio/reference-video/video-fixture/analyze',analyze)
        page.goto(staged_backlot_server+'/studio?project=video-fixture')
        page.locator('#title').get_by_text('Fixture',exact=True).wait_for()
        page.get_by_role('button',name='Referencias e imágenes',exact=True).click()
        assert page.locator('[data-pane=references]').is_visible()
        assert not page.locator('[data-pane=models]').is_visible()
        assert page.locator('#reference-url').input_value()=='https://www.youtube.com/watch?v=M2oOPhZtTdU'
        page.locator('#reference-url').fill('https://youtu.be/M2oOPhZtTdU')
        page.locator('#reference-vision').uncheck()
        page.locator('#reference-summary').uncheck()
        page.locator('#reference-download').click()
        page.locator('#reference-result h3').get_by_text('Análisis: partial',exact=True).wait_for()
        assert requests==[{'url':'https://youtu.be/M2oOPhZtTdU','vision':False,
            'transcribe':True,'summary':False,'vision_model':'smolvlm'}]
        assert 'Modelo no preparado' in page.locator('#reference-result').inner_text()
        page.locator('#reference-report').click()
        assert len(requests)==1
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert errors==[]
        browser.close()


def test_setup_discovery_binding_and_runtime_forms_without_execution(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1280,'height':900});errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda r:r.fulfill(json={'settings':{
            'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture',
            'resource_roots':[]},'pipelines':[],'projects':[]}))
        discovery_calls=[];bindings=[];runtime_saves=[]
        path='/local/'+('long-directory-name/'*12)+'ffmpeg.exe'
        def discovery(route):
            discovery_calls.append(route.request.post_data_json)
            route.fulfill(json={'entries_examined':3,'limited':False,'roots':[{'path':'/local','available':True}],
                'applications':[{'id':'ffmpeg','label':'FFmpeg','configured_executable':'','candidates':[path]}],
                'python_candidates':[],'installers_not_executed':['/local/Avogadro-setup.exe'],
                'errors':[],'note':'No se ejecutó ningún candidato.'})
        page.route('**/api/studio/setup/discover',discovery)
        def bind(route):bindings.append(route.request.post_data_json);route.fulfill(json={'saved':True,'launched':False})
        page.route('**/api/studio/applications/ffmpeg',bind)
        def runtime(route):
            if route.request.method=='POST':runtime_saves.append(route.request.post_data_json);route.fulfill(json={'saved':True,'generation_started':False})
            else:route.fulfill(json={'fields':{'backbone_dir':'Backbone local','vision_dir':'Vision local'},'values':{'backbone_dir':'','vision_dir':''}})
        page.route('**/api/studio/setup/runtime/framepack',runtime)
        page.goto(staged_backlot_server+'/studio#setup')
        assert page.locator('[data-pane=setup]').is_visible()
        page.locator('#setup-roots').fill('/local')
        page.locator('#setup-discover').click()
        page.get_by_text('No se ejecutó ningún candidato.',exact=True).wait_for()
        assert discovery_calls==[{'roots':['/local']}]
        assert bindings==[]
        page.locator('#setup-discovery-result details').first.locator('summary').click()
        page.get_by_role('button',name='Vincular esta ruta de FFmpeg',exact=True).click()
        page.get_by_text('Ruta de FFmpeg guardada. El ejecutable no se inició.',exact=True).wait_for()
        assert bindings==[{'executable':path}]
        page.locator('#setup-runtime-load').click()
        page.locator('#setup-runtime-form [name=backbone_dir]').fill('/local/backbone')
        page.locator('#setup-runtime-form [name=vision_dir]').fill('/local/vision')
        page.get_by_role('button',name='Guardar configuración del motor',exact=True).click()
        page.get_by_text('Configuración de framepack guardada. No se movieron pesos ni se inició generación.',exact=True).wait_for()
        assert runtime_saves==[{'backbone_dir':'/local/backbone','vision_dir':'/local/vision'}]
        page.locator('#setup-runtime-family').select_option('magihuman')
        assert not page.locator('#setup-runtime-form').is_visible()
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert errors==[]
        browser.close()


def test_queue_controls_inspection_and_progress(staged_backlot_server):
    """Queue transport is mocked; no inference, downloads or production start."""
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture','resource_roots':[]},'pipelines':[],'projects':[]}))
        state={'status':'paused','worker_active':False,'projects_root':'/data/projects','items':[
            {'id':'first','project_id':'first','title':'Primero','status':'blocked','projects_root':'/data/projects','message':'Revisar recursos','progress':{'available':True,'status':'awaiting_human','message':'Revisa imágenes','updated_at':'fixture-time','completed_stages':1,'total_stages':2,'stages':[{'name':'script','status':'completed'},{'name':'assets','status':'awaiting_human'}]}},
            {'id':'second','project_id':'second','title':'Segundo','status':'pending','projects_root':'/other/projects','progress':{'available':False,'message':'Conecta el disco original'}}]}
        calls=[]
        page.route('**/api/studio/queue',lambda route:route.fulfill(json=state))
        page.route('**/api/studio/queue/inspect',lambda route:route.fulfill(json={'ready':False,'worker_active':False,'note':'No ejecuta modelos','model_status':{'configured':'fixture','installed':True,'checked':True},'storage':{'problems':['Videos finales: disco no disponible']},'problems':[],'items':[]}))
        def mutate(route):
            action=route.request.url.rsplit('/',1)[-1];payload=route.request.post_data_json;calls.append((action,payload))
            if action=='move':state['items'].reverse()
            if action=='remove':state['items']=[item for item in state['items'] if item['id']!=payload['id']]
            route.fulfill(json={'updated':True,'generation_started':False})
        page.route('**/api/studio/queue/move',mutate)
        page.route('**/api/studio/queue/remove',mutate)
        page.goto(staged_backlot_server+'/studio#queue')
        page.locator('#queue-load').click()
        page.locator('#queue-result details').first.locator('summary').click()
        assert 'Revisa imágenes' in page.locator('#queue-result').inner_text()
        assert '1 / 2 etapas completadas' in page.locator('#queue-result').inner_text()
        page.locator('#queue-load').click()
        page.wait_for_function('document.querySelector("#queue-result details").open')
        page.locator('#queue-result details').nth(1).locator('summary').click()
        assert page.locator('#queue-result details').nth(1).get_by_role('button',name='Abrir proyecto',exact=True).is_disabled()
        page.get_by_role('button',name='Subir',exact=True).click()
        page.wait_for_function('document.querySelector("#queue-result summary").textContent.startsWith("Segundo")')
        page.locator('#queue-result details').first.get_by_role('button',name='Retirar de la cola',exact=True).click()
        page.wait_for_function('document.querySelectorAll("#queue-result details").length===1')
        page.locator('#queue-inspect').click()
        page.get_by_text('Videos finales: disco no disponible',exact=True).wait_for()
        assert calls==[('move',{'id':'second','direction':'up'}),('remove',{'id':'second'})]
        assert errors==[]
        browser.close()


def test_final_catalog_availability_errors_and_disconnected_disk(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture','resource_roots':[]},'pipelines':[],'projects':[]}))
        report={'root_available':True,'truncated':True,'note':'Disponibilidad sin verificar integridad','projects':[{'project_id':'first','title':'Mi video','verification_status':'passed','copied':True,'outputs':[{'path':'/finals/good.mp4','available':True},{'path':'/finals/missing.mp4','available':False}]}],'errors':[{'project_id':'broken','message':'Recibo ilegible'}]}
        page.route('**/api/studio/finals',lambda route:route.fulfill(json=report))
        page.goto(staged_backlot_server+'/studio#finals')
        page.locator('#finals-load').click()
        page.locator('#finals-result summary').click()
        assert 'Disponible: /finals/good.mp4' in page.locator('#finals-result').inner_text()
        assert 'No disponible: /finals/missing.mp4' in page.locator('#finals-result').inner_text()
        assert 'Lista parcial' in page.locator('#finals-result').inner_text()
        assert 'Recibo ilegible' in page.locator('#finals-result').inner_text()
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        report.update(root_available=False,truncated=False,projects=[],errors=[])
        page.locator('#finals-load').click()
        page.get_by_text('El disco de proyectos no está disponible. Conéctalo para consultar los finales.',exact=True).wait_for()
        assert 'No hay entregas' not in page.locator('#finals-result').inner_text()
        assert errors==[]
        browser.close()


def test_official_football_queries_clear_old_results_on_failure(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture','resource_roots':[]},'pipelines':[],'projects':[]}))
        page.route('**/api/studio/football/schema',lambda route:route.fulfill(json={'coverage_note':'Solo UEFA','competitions':['champions'],'parameters':{'edition':{'type':'integer','minimum':1955},'player_id':{'type':'string'},'metrics':{'type':'array'},'phase':{'type':'string','enum':['TOURNAMENT','ALL']}},'actions':[{'name':'definitions','fields':['competition'],'required':['competition']},{'name':'player','fields':['competition','edition','player_id','metrics','phase'],'required':['competition','edition','player_id','metrics'],'defaults':{'phase':'TOURNAMENT'}}]}))
        calls=[]
        def query(route):
            calls.append(route.request.post_data_json)
            route.fulfill(json={'success':len(calls)==1,'data':{'fixture_stat':'fresh-result','fuente':'UEFA','registros':[{'nombre':'<img src=x onerror=alert(1)>','estadisticas':{'goals':0,'assists':None}}],'advertencia':'Alcance de prueba','consultas':[{'url':'https://www.uefa.com/fixture','consultado_utc':'fixture-time'}]} if len(calls)==1 else None,'error':'Fuente temporalmente no disponible','note':'Consulta sin respaldo antiguo'})
        page.route('**/api/studio/football/query',query)
        page.goto(staged_backlot_server+'/studio#football')
        page.locator('#football-load').click()
        page.locator('#football-query').click()
        page.wait_for_function('document.querySelector("#football-result").textContent.includes("fresh-result")')
        assert page.locator('#football-result tbody tr').count()==1
        assert page.locator('#football-result').get_by_role('cell',name='0',exact=True).count()==1
        assert page.locator('#football-result').get_by_role('cell',name='Dato no disponible',exact=True).count()==1
        assert page.locator('#football-result img').count()==0
        assert page.get_by_role('link',name='Fuente oficial',exact=True).get_attribute('href')=='https://www.uefa.com/fixture'
        page.locator('#football-query').click()
        page.get_by_text('Fuente temporalmente no disponible',exact=True).wait_for()
        assert 'fresh-result' not in page.locator('#football-result').inner_text()
        assert calls==[{'action':'definitions','competition':'champions'}]*2
        page.locator('#football-action').select_option('player')
        page.locator('[data-football-field=edition]').fill('2027')
        page.locator('[data-football-field=player_id]').fill('12345')
        page.locator('[data-football-field=metrics]').fill('goals, assists')
        page.locator('[data-football-field=phase]').select_option('ALL')
        page.locator('#football-query').click()
        page.wait_for_function('document.querySelector("#football-query").disabled===false')
        assert calls[-1]=={'action':'player','competition':'champions','edition':2027,'player_id':'12345','metrics':['goals','assists'],'phase':'ALL'}
        page.locator('#football-action').select_option('definitions')
        assert page.locator('[data-football-field]').count()==0
        browser.close()


def test_football_definition_picker_uses_entity_and_competition_scope(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture','resource_roots':[]},'pipelines':[],'projects':[]}))
        schema={'coverage_note':'UEFA','competitions':['champions','europa'],'parameters':{'entity':{'type':'string'},'metrics':{'type':'array'}},'actions':[{'name':'definitions','fields':['competition'],'required':['competition']},{'name':'ranking','fields':['competition','entity','metrics'],'required':['competition','entity','metrics'],'choices':{'entity':['player','team']}}]}
        page.route('**/api/studio/football/schema',lambda route:route.fulfill(json=schema))
        page.route('**/api/studio/football/query',lambda route:route.fulfill(json={'success':True,'note':'Fixture metadata','data':{'definiciones':[{'name':'goals','actors':['PLAYER']},{'name':'possession','actors':['TEAM']}]}}))
        page.goto(staged_backlot_server+'/studio#football')
        page.locator('#football-load').click();page.locator('#football-query').click()
        page.wait_for_function('document.querySelector("#football-result").textContent.includes("Fixture metadata")')
        page.locator('#football-action').select_option('ranking')
        picker=page.get_by_role('combobox',name='Métrica de las definiciones oficiales',exact=True)
        assert picker.locator('option[value=goals]').count()==1
        assert picker.locator('option[value=possession]').count()==0
        picker.select_option('goals')
        page.get_by_role('button',name='Añadir métrica elegida',exact=True).click()
        page.get_by_role('button',name='Añadir métrica elegida',exact=True).click()
        assert page.locator('[data-football-field=metrics]').input_value()=='goals'
        page.locator('[data-football-field=entity]').select_option('team')
        assert page.locator('[data-football-field=metrics]').input_value()==''
        assert picker.locator('option[value=possession]').count()==1
        assert picker.locator('option[value=goals]').count()==0
        page.locator('#football-competition').select_option('europa')
        assert page.locator('[data-football-metric-picker]').count()==0
        browser.close()


def test_official_id_followup_prepares_form_without_new_query(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188','model':'fixture','resource_roots':[]},'pipelines':[],'projects':[]}))
        page.route('**/api/studio/football/schema',lambda route:route.fulfill(json={'coverage_note':'Fixture','competitions':['champions'],'parameters':{'edition':{'type':'integer'},'player_id':{'type':'string'},'metrics':{'type':'array'}},'actions':[{'name':'definitions','fields':['competition'],'required':['competition']},{'name':'player','fields':['competition','edition','player_id','metrics'],'required':['competition','edition','player_id','metrics']}]}))
        calls=[]
        def query(route):
            calls.append(route.request.post_data_json)
            route.fulfill(json={'success':True,'note':'Fixture','data':{'fuente':'UEFA','registros':[{'id':'123','nombre':'Fixture player'}]},'followups':[{'row_index':0,'label':'Preparar jugador de prueba','query':{'action':'player','competition':'champions','edition':2027,'player_id':'123','metrics':['goals']}}]})
        page.route('**/api/studio/football/query',query)
        page.goto(staged_backlot_server+'/studio#football')
        page.locator('#football-load').click();page.locator('#football-query').click()
        page.get_by_role('button',name='Preparar jugador de prueba',exact=True).click()
        assert page.locator('#football-action').input_value()=='player'
        assert page.locator('[data-football-field=player_id]').input_value()=='123'
        assert page.locator('[data-football-field=edition]').input_value()=='2027'
        assert page.locator('[data-football-field=metrics]').input_value()=='goals'
        assert len(calls)==1
        browser.close()
