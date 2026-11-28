"""UI handoff contract with synthetic transport; no inference claims."""
import os
import pytest
pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright, expect
from tests.backlot.test_ui_bug_bash import staged_backlot_server


def test_projects_menu_refreshes_agent_created_projects_without_losing_selection(staged_backlot_server):
    """The current project picker refresh preserves the open project's selection/revision."""
    projects=[{'project_id':'shared-a','title':'Selected JSON project'}]
    state={'revision':0,'edit_sha256':'a'*64,'undo':[],'redo':[],'events':[],
           'edit_decisions':{'version':'1.0','render_runtime':'ffmpeg','cuts':[], 'audio_tracks':[],
             'cues':[],'sources':{},'output':{'ratio':'16:9','fps':24,'fit':'pad'},
             'subtitle_style':{'size':32,'position':'bottom','mode':'soft'}}}
    project_reads=[]
    def project_list(route):
        project_reads.append(route.request.method)
        route.fulfill(json=projects)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/editor/projects',project_list)
        page.route('**/api/studio/editor/shared-a',lambda route:route.fulfill(json=state))
        page.route('**/api/studio/comfy-history/projects/shared-a',lambda route:route.fulfill(json={'reports':[]}))
        page.goto(staged_backlot_server+'/studio?project=shared-a#library')
        expect(page.locator('#project-select')).to_have_value('shared-a')
        expect(page.locator('#edit-revision')).to_have_text('Revisión 0')
        projects.append({'project_id':'shared-b','title':'Created through another client'})
        page.locator('#main-nav [data-module="projects"]').click()
        page.locator('#refresh-status').click()
        expect(page.locator('#project-select option[value="shared-b"]')).to_have_count(1)
        expect(page.locator('#project-select')).to_have_value('shared-a')
        expect(page.locator('#edit-revision')).to_have_text('Revisión 0')
        assert len(project_reads)>=2
        browser.close()

def test_rendered_preview_survives_save_but_content_edit_invalidates_it(staged_backlot_server):
    """Synthetic transport checks preview identity; no FFmpeg/media claim."""
    state = {'revision':0,'edit_sha256':'a'*64,'render_sha256':'a'*64,'undo':[],'redo':[],'events':[],
             'edit_decisions':{'version':'1.0','render_runtime':'ffmpeg',
                'cuts':[{'id':'clip-1','source':'assets/clip.mp4','source_id':'source-1',
                         'in_seconds':0,'out_seconds':4,'speed':1,'muted':False,'gain':1,
                         'fade_in':0,'fade_out':0,'start_seconds':0}],
                'audio_tracks':[],'cues':[],
                'sources':{'source-1':{'path':'assets/clip.mp4','original_name':'clip.mp4',
                    'kind':'video','duration':4,'audio':False,'sha256':'c'*64}},
                'output':{'ratio':'16:9','fps':24,'fit':'pad'},
                'subtitle_style':{'size':32,'position':'bottom','mode':'soft'}}}
    job = {'status':'completed','attempt':'fixture','revision':0,'edit_sha256':'a'*64,
           'render_sha256':'a'*64,'current':True,'preview':True,
           'url':'/fixture-editor-preview.mp4','subtitle_mode':'none'}
    calls=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[{'project_id':'save-fixture','title':'JSON fixture'}]))
        page.route('**/api/studio/editor/save-fixture',lambda route:route.fulfill(json=state))
        def render(route):
            if route.request.method=='POST':
                calls.append(route.request.post_data_json)
                route.fulfill(json={'status':'completed','preview':True})
            else:
                route.fulfill(json=job)
        page.route('**/api/studio/editor/save-fixture/render',render)
        page.route('**/fixture-editor-preview.mp4',lambda route:route.fulfill(status=204))
        def command(route):
            data=route.request.post_data_json
            assert data['revision']==state['revision']
            state['revision']+=1
            if data['operation']=='output':
                state['edit_sha256']='b'*64
                state['render_sha256']='b'*64
                state['edit_decisions']['output']['ratio']=data['ratio']
            route.fulfill(json=state)
        page.route('**/api/studio/editor/save-fixture/command',command)
        page.goto(staged_backlot_server+'/studio?project=save-fixture#video')
        expect(page.locator('#preview-refresh')).to_be_enabled()
        page.locator('#preview-refresh').click()
        expect(page.locator('#preview-video')).to_have_attribute('src','/fixture-editor-preview.mp4',timeout=5000)
        assert calls==[{'revision':0,'preview':True}]
        page.locator('#edit-save').click()
        expect(page.locator('#edit-revision')).to_contain_text('1')
        expect(page.locator('#preview-video')).to_have_attribute('src','/fixture-editor-preview.mp4')
        page.locator('#aspect-select').select_option('9:16')
        expect(page.locator('#edit-revision')).to_contain_text('2')
        expect(page.locator('#preview-video')).not_to_have_attribute('src','/fixture-editor-preview.mp4')
        expect(page.locator('#preview-status')).to_contain_text('El montaje cambió')
        browser.close()


@pytest.mark.parametrize('width,height', [(1280,720),(1920,1080),(2560,1440),(3440,1440),(640,720)])
def test_manual_editor_layout_and_shared_revision_controls(staged_backlot_server, width, height, tmp_path):
    """Current Studio layout and shared revision controls with synthetic state only."""
    from pathlib import Path
    import json
    state = {'revision':0, 'undo':[], 'redo':[], 'events':[], 'edit_decisions':{
        'version':'1.0', 'render_runtime':'ffmpeg', 'cuts':[], 'audio_tracks':[], 'cues':[], 'sources':{},
        'output':{'ratio':'16:9','fps':24,'fit':'pad'}, 'subtitle_style':{'size':32,'position':'bottom','mode':'soft'}}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page = browser.new_page(viewport={'width':width,'height':height})
        errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/api/studio/editor/projects', lambda route: route.fulfill(json=[{'project_id':'ui-fixture','title':'Proyecto JSON sintético · sin medios'}]))
        page.route('**/api/studio/editor/ui-fixture', lambda route: route.fulfill(json=state))
        page.route('**/api/studio/editor/ui-fixture/render', lambda route: route.fulfill(json={'status':'idle'}))
        calls = []
        def command(route):
            data = route.request.post_data_json
            calls.append(data)
            assert data['revision'] == state['revision']
            state['revision'] += 1
            if data['operation'] == 'output':
                state['edit_decisions']['output'] = {'ratio':data['ratio'],'fps':data['fps'],'fit':'pad'}
            route.fulfill(json=state)
        page.route('**/api/studio/editor/ui-fixture/command', command)
        page.goto(staged_backlot_server + '/studio?project=ui-fixture#video')
        expect(page.locator('#edit-revision')).to_have_text('Revisión 0')
        expect(page.locator('.edit-workbench')).to_be_visible()
        assert page.locator('#preview-video').count() == 1
        expect(page.locator('#timeline-tracks')).to_be_visible()
        expect(page.locator('#inspector')).to_be_visible()
        assert page.locator('.edit-workbench').bounding_box()['width'] >= width - 280
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
        page.locator('#aspect-select').select_option('9:16')
        expect(page.locator('#edit-revision')).to_have_text('Revisión 1')
        assert calls == [{'operation':'output','revision':0,'ratio':'9:16','fps':24}]
        page.locator('#edit-save').click()
        expect(page.locator('#edit-revision')).to_have_text('Revisión 2')
        page.reload()
        expect(page.locator('#edit-revision')).to_have_text('Revisión 2')
        expect(page.locator('#aspect-select')).to_have_value('9:16')
        output = Path('tests/qa/output/studio-editor')
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output/f'workspace-{width}x{height}.png'), full_page=True)
        (output/f'workspace-{width}x{height}.json').write_text(json.dumps({
            'viewport':{'width':width,'height':height}, 'scope':'synthetic JSON UI/transport; no media or inference',
            'horizontal_overflow':page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 1'),
            'commands':calls, 'page_errors':errors},ensure_ascii=False,indent=2), encoding='utf-8')
        assert not errors
        browser.close()


@pytest.mark.parametrize('width,height', [(1920,1080),(3440,1440)])
def test_existing_project_panel_resize_and_viewport_containment(staged_backlot_server, width, height):
    """Current Studio separators resize panels and persist per-browser layout locally."""
    import json
    from copy import deepcopy
    from pathlib import Path
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    state=deepcopy(fixture['state']);pid=fixture['project_id'];errors=[];writes=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':width,'height':height})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:writes.append(request.url) if request.method=='POST' else None)
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[{'project_id':pid,'title':fixture['title']}]))
        page.route('**/api/studio/editor/'+pid,lambda route:route.fulfill(json=state))
        page.route('**/api/studio/comfy-history/projects/'+pid,lambda route:route.fulfill(json={'reports':[]}))
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        workbench=page.locator('.edit-workbench')
        expect(workbench).to_be_visible()
        media=page.locator('#resize-media');inspector=page.locator('#resize-inspector');timeline=page.locator('#resize-timeline')
        for handle in (media,inspector,timeline):
            expect(handle).to_be_visible()
            assert handle.get_attribute('role')=='separator'
            assert handle.get_attribute('aria-valuenow') is not None
        def dimensions():
            return page.evaluate("""() => {
              const root=document.querySelector('.edit-workbench'),r=root.getBoundingClientRect();
              const rect=id=>{const x=document.querySelector(id).getBoundingClientRect();return {left:x.left,top:x.top,width:x.width,height:x.height,right:x.right,bottom:x.bottom}};
              return {root:{left:r.left,top:r.top,width:r.width,height:r.height,right:r.right,bottom:r.bottom},
                media:rect('.media-panel'),monitor:rect('.monitor-panel'),inspector:rect('.inspector-panel'),timeline:rect('.timeline-panel'),
                overflow:document.documentElement.scrollWidth>innerWidth};
            }""")
        before=dimensions()
        def drag(selector,dx,dy):
            box=page.locator(selector).bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+dx,y+dy,steps=4);page.mouse.up()
        drag('#resize-media',48,0)
        after_media=dimensions()
        assert after_media['media']['width']>before['media']['width']+20
        drag('#resize-inspector',-48,0)
        after_inspector=dimensions()
        assert after_inspector['inspector']['width']>after_media['inspector']['width']+20
        drag('#resize-timeline',0,-48)
        after_timeline=dimensions()
        assert after_timeline['timeline']['height']>after_inspector['timeline']['height']+20
        for value in (after_media,after_inspector,after_timeline):
            assert value['media']['left']>=value['root']['left']-1
            assert value['inspector']['right']<=value['root']['right']+1
            assert value['monitor']['width']>=360
            assert not value['overflow']
        saved=page.evaluate("localStorage.getItem('openmontage.studio.editor-layout.v1')")
        assert saved and json.loads(saved).keys()=={'media','inspector','timeline'}
        expected=after_timeline
        page.reload()
        expect(page.locator('#resize-timeline')).to_be_visible()
        restored=dimensions()
        for panel in ('media','monitor','inspector','timeline'):
            assert abs(restored[panel]['width']-expected[panel]['width'])<=2
            assert abs(restored[panel]['height']-expected[panel]['height'])<=2
        page.locator('#resize-media').focus();page.keyboard.press('ArrowRight')
        keyboard=dimensions()
        assert keyboard['media']['width']>restored['media']['width']
        assert page.evaluate("localStorage.getItem('unrelated-preference')") is None
        assert not writes and errors==[]
        browser.close()


def test_cursor_split_uses_shared_revisioned_contract_and_undo(staged_backlot_server):
    """UI contract with intercepted JSON, not local AV playback."""
    from copy import deepcopy
    import json
    from pathlib import Path
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    state=deepcopy(fixture['state']);original=deepcopy(state);pid=fixture['project_id'];calls=[];trim_ends=[41.75,42-1/24]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1920,'height':1080})
        page.route('**/api/studio/editor/projects',lambda r:r.fulfill(json=[{'project_id':pid,'title':'Cursor contract fixture'}]))
        page.route('**/api/studio/editor/'+pid,lambda r:r.fulfill(json=state))
        page.route('**/api/studio/editor/'+pid+'/render',lambda r:r.fulfill(json=fixture['render']))
        page.route('**/media/**',lambda r:r.fulfill(status=204))
        page.route('**/api/studio/editor/'+pid+'/source/**',lambda r:r.fulfill(status=204))
        def command(route):
            data=route.request.post_data_json;calls.append(data);assert data['revision']==state['revision']
            revision=state['revision']+1
            if data['operation']=='split':
                assert data['at']==pytest.approx(11);assert data['track']=='video'
                clip=state['edit_decisions']['cuts'][1];assert data['id']==clip['id']
                state['edit_decisions']['cuts'].append({**clip,'id':'split-part','in_seconds':data['at']})
                clip['out_seconds']=data['at'];state['edit_sha256']='b'*64;state['undo']=[original['edit_decisions']]
            elif data['operation']=='trim':
                assert data['track']=='video';assert data['in_seconds']==40
                assert data['out_seconds']==pytest.approx(trim_ends.pop(0))
                state['edit_decisions']['cuts'][0]['out_seconds']=data['out_seconds'];state['edit_sha256']='c'*64;state['undo']=[original['edit_decisions']]
            elif data['operation']=='clip':
                assert data['track']=='audio';assert data['start_seconds']==pytest.approx(.5)
                state['edit_decisions']['audio_tracks'][0]['start_seconds']=data['start_seconds'];state['edit_sha256']='d'*64;state['undo']=[original['edit_decisions']]
            elif data['operation']=='cue_update':
                assert data['index']==0;assert data['text']=='Edited offline cue';assert data['start_seconds']==.5;assert data['end_seconds']==1.5
                state['edit_decisions']['cues'][0].update(start_seconds=.5,end_seconds=1.5,text=data['text']);state['edit_sha256']='e'*64;state['undo']=[original['edit_decisions']]
            else:
                assert data['operation']=='undo';state.clear();state.update(deepcopy(original))
            state['revision']=revision;route.fulfill(json=state)
        page.route('**/api/studio/editor/'+pid+'/command',command)
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        expect(page.locator('#edit-player')).to_have_attribute('src',fixture['render']['url'])
        page.locator('.editor-video .editor-clip').nth(1).click()
        expect(page.locator('#edit-player')).to_have_attribute('src',fixture['render']['url'])
        ruler=page.get_by_role('slider',name='Regla temporal del montaje en segundos');ruler.focus()
        page.keyboard.press('Home');page.keyboard.press('Shift+ArrowRight');page.keyboard.press('Shift+ArrowRight')
        for _ in range(12):page.keyboard.press('ArrowRight')
        assert float(ruler.get_attribute('aria-valuenow'))==pytest.approx(2.5)
        page.locator('#edit-split-cursor').click()
        expect(page.locator('.editor-video .editor-clip')).to_have_count(3)
        expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+1))
        page.locator('#edit-undo').click()
        expect(page.locator('.editor-video .editor-clip')).to_have_count(2)
        page.locator('#edit-reopen').click()
        expect(page.locator('#edit-player')).to_have_attribute('src',fixture['render']['url'])
        assert len(calls)==2
        def drag_edge(delta,cancel=False):
            handle=page.locator('.editor-video .editor-clip').first.locator('.editor-trim-out')
            box=handle.bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+delta,y,steps=5)
            if cancel:page.keyboard.press('Escape')
            page.mouse.up()
        drag_edge(25,cancel=True);assert len(calls)==2
        zoom=float(page.locator('#edit-zoom').input_value());drag_edge(-zoom*.25)
        expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+3))
        page.locator('#edit-undo').click();expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+4))
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        handle=page.locator('.editor-video .editor-clip').first.locator('.editor-trim-out');handle.focus();page.keyboard.press('ArrowLeft')
        expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+5))
        page.locator('#edit-undo').click();expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+6))
        assert len(calls)==6 and not trim_ends
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        zoom=float(page.locator('#edit-zoom').input_value())
        page.locator('.editor-audio .editor-clip').first.drag_to(page.locator('.editor-audio'),source_position={'x':20,'y':20},target_position={'x':20+zoom*.5,'y':35})
        expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+7))
        expect(page.locator('#edit-timeline-note')).to_be_visible()
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('#edit-undo').click();expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+8))
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('.editor-cues .editor-clip').first.click()
        form=page.locator('#edit-cue-form')
        form.locator('[name=start_seconds]').fill('0.5');form.locator('[name=end_seconds]').fill('1.5');form.locator('[name=text]').fill('Edited offline cue')
        form.locator('button[type=submit]').click()
        expect(page.locator('#edit-srt')).to_have_value('1\n00:00:00,500 --> 00:00:01,500\nEdited offline cue\n')
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('#edit-undo').click();expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+10))
        assert len(calls)==10
        browser.close()


@pytest.mark.parametrize('width,height',[(1920,1080),(3440,1440)])
def test_fit_long_timeline_includes_audio_tail_and_keyboard_cursor(staged_backlot_server,width,height):
    """Long metadata scenario derived from the existing source, no media payloads."""
    from copy import deepcopy
    import json
    from pathlib import Path
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    state=deepcopy(fixture['state']);pid=fixture['project_id'];edl=state['edit_decisions']
    edl['cuts'][0].update(in_seconds=0,out_seconds=30);edl['cuts'][1].update(in_seconds=40,out_seconds=70)
    edl['audio_tracks'][0].update(start_seconds=62,in_seconds=0,out_seconds=4,speed=1)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':width,'height':height})
        page.route('**/api/studio/editor/projects',lambda r:r.fulfill(json=[{'project_id':pid,'title':'Long JSON timeline; no CI media'}]))
        page.route('**/api/studio/editor/'+pid,lambda r:r.fulfill(json=state))
        page.route('**/api/studio/editor/'+pid+'/render',lambda r:r.fulfill(json={'status':'idle'}))
        page.route('**/api/studio/editor/'+pid+'/source/**',lambda r:r.fulfill(status=204))
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        expect(page.locator('#edit-revision')).to_contain_text(str(state['revision']))
        ruler=page.get_by_role('slider',name='Regla temporal del montaje en segundos')
        assert float(ruler.get_attribute('aria-valuemax'))==66
        assert page.locator('#edit-timeline-note').is_visible()
        assert page.locator('#edit-tracks').evaluate('(n)=>n.scrollWidth<=n.clientWidth+1')
        page.locator('#edit-zoom-in').click();scale=float(page.locator('#edit-zoom').input_value())
        page.reload();expect(page.locator('#edit-revision')).to_contain_text(str(state['revision']))
        assert float(page.locator('#edit-zoom').input_value())==pytest.approx(scale)
        page.locator('#edit-fit').click();ruler=page.get_by_role('slider',name='Regla temporal del montaje en segundos');ruler.focus()
        page.keyboard.press('End');assert float(ruler.get_attribute('aria-valuenow'))==66
        output=Path('tests/qa/output/studio-editor');output.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(output/f'fit-long-{width}x{height}.png'),full_page=True)
        browser.close()


def test_waveform_and_meter_use_decoded_data_with_explicit_mock_scope(staged_backlot_server):
    """Mock AudioContext only; no claim of local audio playback or listening."""
    import json
    from pathlib import Path
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    pid=fixture['project_id']
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1920,'height':1080})
        page.add_init_script('''window.audioFixture={decodes:0,sources:0};window.AudioContext=class{
          constructor(){this.destination={};} async close(){} async resume(){}
          async decodeAudioData(){audioFixture.decodes++;const samples=Float32Array.from({length:192000},(_,i)=>Math.sin(i/48000*2*Math.PI*110)*.5);return {sampleRate:48000,getChannelData(){return samples}};}
          createMediaElementSource(){audioFixture.sources++;return {connect(){},disconnect(){}};}
          createAnalyser(){return {fftSize:2048,connect(){},getFloatTimeDomainData(a){a.fill(.25)}};}
        };''')
        page.route('**/api/studio/editor/projects',lambda r:r.fulfill(json=[{'project_id':pid,'title':'SYNTHETIC decoder; no AV playback'}]))
        page.route('**/api/studio/editor/'+pid,lambda r:r.fulfill(json=fixture['state']))
        page.route('**/api/studio/editor/'+pid+'/render',lambda r:r.fulfill(json=fixture['render']))
        page.route('**/media/**',lambda r:r.fulfill(status=204))
        page.route('**/api/studio/editor/'+pid+'/source/**',lambda r:r.fulfill(status=204))
        page.goto(staged_backlot_server+'/studio?project='+pid+'#audio')
        canvas=page.locator('.editor-track-waveform').first;expect(canvas).to_be_visible()
        assert canvas.evaluate('(c)=>c.getContext("2d").getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)')
        page.locator('.editor-audio .editor-clip').first.click()
        expect(page.locator('#edit-waveform')).to_be_visible()
        assert page.evaluate('audioFixture.decodes')==1
        page.locator('#edit-meter-toggle').click()
        expect(page.locator('#edit-meter-toggle')).to_have_attribute('aria-pressed','true')
        assert page.locator('#edit-meter').is_hidden()
        page.locator('#edit-player').evaluate('(p)=>{Object.defineProperty(p,"paused",{configurable:true,value:false});p.dispatchEvent(new Event("play"))}')
        expect(page.locator('#edit-meter')).to_be_visible()
        assert float(page.locator('#edit-meter').get_attribute('value'))==pytest.approx(-12.0411998266)
        page.locator('#edit-player').evaluate('(p)=>{Object.defineProperty(p,"paused",{configurable:true,value:true});p.dispatchEvent(new Event("pause"))}')
        expect(page.locator('#edit-meter-level')).to_contain_text('Detenido')
        page.locator('#edit-meter-toggle').click();expect(page.locator('#edit-meter')).to_be_hidden()
        assert page.evaluate('audioFixture.sources')==1
        browser.close()


@pytest.mark.parametrize('supported',[False,True])
def test_advanced_timeline_uses_capabilities_and_atomic_model(staged_backlot_server,supported):
    """Intercepted transport, actual pure backend edits; no AV payload or playback."""
    from copy import deepcopy
    import json
    from pathlib import Path
    from lib import studio_editor as editor
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    state=deepcopy(fixture['state']);pid=fixture['project_id'];original=deepcopy(state['edit_decisions']);calls=[]
    state['render_sha256']=editor.render_digest(original)
    job={**fixture['render'],'render_sha256':state['render_sha256']}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1920,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        if not supported:page.route('**/api/studio/editor/capabilities',lambda r:r.fulfill(status=404,json={'detail':'Older running server'}))
        page.route('**/api/studio/editor/projects',lambda r:r.fulfill(json=[{'project_id':pid,'title':'Atomic metadata fixture; no AV'}]))
        page.route('**/api/studio/editor/'+pid,lambda r:r.fulfill(json=state))
        page.route('**/api/studio/editor/'+pid+'/render',lambda r:r.fulfill(json=job))
        page.route('**/api/studio/editor/'+pid+'/source/**',lambda r:r.fulfill(status=204))
        page.route('**/media/**',lambda r:r.fulfill(status=204))
        def command(route):
            data=route.request.post_data_json;calls.append(data);assert data['revision']==state['revision']
            if data['operation']=='undo':state['edit_decisions']=state['undo'].pop()
            else:
                edl=deepcopy(state['edit_decisions']);editor._apply_edit(edl,data);editor._validate_edit(edl)
                state['undo'].append(state['edit_decisions']);state['edit_decisions']=edl
            state['revision']+=1;state['edit_sha256']=editor.edit_digest(state['edit_decisions']);state['render_sha256']=editor.render_digest(state['edit_decisions'])
            route.fulfill(json=state)
        page.route('**/api/studio/editor/'+pid+'/command',command)
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        expect(page.locator('#edit-player')).to_have_attribute('src',job['url'])
        clips=page.locator('.editor-video .editor-clip');clips.nth(0).click();clips.nth(1).click(modifiers=['Control'])
        if not supported:
            assert page.locator('#edit-advanced-tools').is_hidden()
            assert page.locator('#edit-flags-panel').is_hidden()
            assert page.locator('.editor-video [aria-pressed=true]').count()==1
            assert not calls and not errors;browser.close();return
        assert page.locator('.editor-video [aria-pressed=true]').count()==2
        page.locator('#edit-duplicate').click();expect(clips).to_have_count(4)
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('#edit-undo').click();expect(clips).to_have_count(2)
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        clips.nth(0).click();page.locator('#edit-delete-gap').click()
        expect(clips.nth(0)).to_contain_text('Vacío negro/silencio')
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('#edit-undo').click();expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('#edit-show-montage').click();expect(page.locator('#edit-player')).to_have_attribute('src',job['url'])
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('#edit-marker-add').click();expect(page.locator('.editor-marker')).to_have_count(1)
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        expect(page.locator('#edit-player')).to_have_attribute('src',job['url'])
        clips.nth(0).click();page.locator('#edit-clip-form [name=locked]').check();page.locator('#edit-flags-apply').click()
        expect(clips.nth(0).locator('.editor-trim-handle')).to_have_count(0)
        expect(page.locator('#edit-player')).to_have_attribute('src',job['url'])
        assert not errors
        browser.close()


def test_render_cancel_button_sends_attempt_and_allows_new_attempt(staged_backlot_server):
    """UI transport contract only; real child exit is tested independently."""
    import json
    from copy import deepcopy
    from pathlib import Path
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    pid=fixture['project_id'];job={'status':'running','attempt':'owned-attempt'};calls=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1920,'height':1080});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/api/studio/editor/projects',lambda r:r.fulfill(json=[{'project_id':pid,'title':'Cancel metadata fixture'}]))
        page.route('**/api/studio/editor/'+pid,lambda r:r.fulfill(json=fixture['state']))
        def render_status(route):
            if route.request.method=='POST':
                calls.append(route.request.post_data_json);job.update(status='running',attempt='second-attempt')
            route.fulfill(json=deepcopy(job))
        page.route('**/api/studio/editor/'+pid+'/render',render_status)
        def cancel(route):
            calls.append(route.request.post_data_json);assert calls[-1]=={'attempt':'owned-attempt'}
            route.fulfill(json={**job,'status':'cancelling'});job.update(status='cancelled',process_stopped=True)
        page.route('**/api/studio/editor/'+pid+'/render/cancel',cancel)
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        expect(page.locator('#edit-render-cancel')).to_be_visible()
        expect(page.locator('#edit-export')).to_be_disabled()
        page.locator('#edit-render-cancel').click()
        expect(page.locator('#edit-render-status')).to_contain_text('Render cancelado')
        expect(page.locator('#edit-render-cancel')).to_be_hidden()
        expect(page.locator('#edit-export')).to_be_enabled()
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('#edit-preview').click();expect(page.locator('#edit-render-cancel')).to_be_visible()
        assert calls==[{'attempt':'owned-attempt'},{'revision':fixture['state']['revision'],'preview':True}]
        assert not errors
        browser.close()


def test_effect_controls_commit_shared_edl_and_reopen(staged_backlot_server):
    """Actual model and browser controls; intercepted transport, not local AV QA."""
    from copy import deepcopy
    import json
    from pathlib import Path
    from lib import studio_editor as editor
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    state=deepcopy(fixture['state']);pid=fixture['project_id'];calls=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1920,'height':1080});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/api/studio/editor/projects',lambda r:r.fulfill(json=[{'project_id':pid,'title':'Effects metadata fixture'}]))
        page.route('**/api/studio/editor/'+pid,lambda r:r.fulfill(json=state))
        page.route('**/api/studio/editor/'+pid+'/render',lambda r:r.fulfill(json={'status':'idle'}))
        page.route('**/api/studio/editor/'+pid+'/source/**',lambda r:r.fulfill(status=204))
        def command(route):
            data=route.request.post_data_json;calls.append(data);assert data['revision']==state['revision']
            if data['operation']=='undo':state['edit_decisions']=state['undo'].pop()
            else:
                value=deepcopy(state['edit_decisions']);editor._apply_edit(value,data);editor._validate_edit(value)
                state['undo'].append(state['edit_decisions']);state['edit_decisions']=value
            state['revision']+=1;state['edit_sha256']=editor.edit_digest(state['edit_decisions']);state['render_sha256']=editor.render_digest(state['edit_decisions'])
            route.fulfill(json=state)
        page.route('**/api/studio/editor/'+pid+'/command',command)
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        clips=page.locator('.editor-video .editor-clip');expect(clips).to_have_count(2);clips.nth(0).click()
        page.locator('#edit-transform-panel summary').click()
        form=page.locator('#edit-transform-form');form.locator('[name=fit]').select_option('crop')
        form.locator('[name=zoom]').fill('1.5');form.locator('[name=flip_h]').check();form.locator('[type=submit]').click()
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        assert state['edit_decisions']['cuts'][0]['transform']['zoom']==1.5
        page.locator('#edit-title-panel summary').click()
        title=page.locator('#edit-title-form');title.locator('[name=text]').fill('Manual fixture title')
        title.locator('[name=start_seconds]').fill('0');title.locator('[name=end_seconds]').fill('1')
        title.locator('[type=submit]').click();expect(page.locator('.editor-titles button')).to_have_count(1)
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        page.locator('#edit-output-custom-panel summary').click()
        output=page.locator('#edit-output-custom-form');output.locator('[name=width]').fill('640');output.locator('[name=height]').fill('360')
        output.locator('[name=platform]').select_option('youtube');output.locator('[name=fps]').fill('30');output.locator('[type=submit]').click()
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        assert state['edit_decisions']['output']['width']==640
        page.locator('#edit-mix-panel summary').click()
        mix=page.locator('#edit-mix-form');mix.locator('[name=normalize]').check();mix.locator('[name=target_lufs]').fill('-18');mix.locator('[type=submit]').click()
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        assert state['edit_decisions']['audio_mix']['target_lufs']==-18
        page.locator('#edit-reopen').click();expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        assert output.locator('[name=width]').input_value()=='640'
        assert title.locator('[name=text]').input_value()=='Manual fixture title'
        page.locator('#edit-undo').click();expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        assert 'audio_mix' not in state['edit_decisions']
        clips.nth(1).click();page.locator('#edit-transition-panel summary').click()
        page.locator('#edit-transition-form [name=duration_seconds]').fill('0.25')
        page.locator('#edit-transition-form [type=submit]').click()
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        transition=state['edit_decisions']['cuts'][1].get('transition')
        assert transition and transition.get('duration_seconds')==8/30, (
            f"transition not committed; operations={[c.get('operation') for c in calls]}; "
            f"notice={page.locator('#edit-message').inner_text()!r}")
        page.locator('#edit-layers-panel > summary').click()
        layer=page.locator('#edit-layer-form');layer.locator('[name=in_seconds]').fill('0')
        layer.locator('[name=out_seconds]').fill('1');layer.locator('[name=start_seconds]').fill('0.5')
        layer.locator('[type=submit]').click();expect(page.locator('.editor-layers button')).to_have_count(1)
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        layer.locator('[name=opacity]').fill('0.5');layer.locator('[type=submit]').click()
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        assert state['edit_decisions']['layers'][0]['opacity']==.5
        page.locator('#edit-undo').click();expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        assert state['edit_decisions']['layers'][0]['opacity']==1
        page.locator('#edit-reopen').click();expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        assert layer.locator('[name=opacity]').input_value()=='1'
        assert [c['operation'] for c in calls]==['transform','title_add','output_custom','audio_mix','undo','transition','layer_add','layer_update','undo']
        assert not errors
        browser.close()


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
        impacts=[]
        def impact(route):
            impacts.append(route.request.url)
            route.fulfill(json={'family_count':1,'note':'Relaciones locales; compatibilidad sin verificar.',
                'families':[{'title':'Family fixture','backend':'native','required_modules':['torch'],
                    'declared_configuration':{'model_dir':'D:/current'},'companion_file_count':1,
                    'companion_files':[{'destination':'D:/models/config.json'}]}]})
        page.route('**/api/studio/updates/impact?*',impact)
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
        resumes=[]
        page.route('**/api/studio/updates/downloads?*',lambda route:route.fulfill(json={
            'rows':[{'job_id':'a'*32,'status':'interrupted','historical':True,'bytes_present':4,
                     'expected_bytes':9,'note':'Historial recuperado; reanudación explícita.'}],
            'note':'Historial local de descargas.','history_warning':None}))
        def resume_download(route):
            resumes.append(route.request.post_data_json)
            route.fulfill(json={'job_id':'resumed','status':'candidate_ready','bytes_present':9,'expected_bytes':9,
                'note':'Candidato comprobado otra vez.'})
        page.route('**/api/studio/updates/downloads/'+'a'*32+'/resume',resume_download)
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
        page.get_by_role('button',name='Revisar impacto del archivo',exact=True).click()
        page.get_by_text('1 familias relacionadas por el catálogo',exact=True).wait_for()
        assert len(impacts)==1 and not calls
        page.locator('[data-update-impact] summary').click()
        assert 'torch' in page.locator('[data-update-impact]').inner_text()
        assert 'D:/models/config.json' in page.locator('[data-update-impact]').inner_text()
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
        page.get_by_role('button',name='Ver descargas de este candidato',exact=True).click()
        page.get_by_text('Descarga interrumpida al reiniciar; reanudación pendiente',exact=True).wait_for()
        assert not resumes
        page.get_by_role('button',name='Reanudar trabajo guardado',exact=True).click()
        page.get_by_text('Candidato descargado y verificado; modelo actual sin cambios',exact=True).wait_for()
        assert resumes==[{}]
        document_button=page.get_by_role('button',name='Leer README.md en el panel',exact=True)
        document_button.click()
        page.get_by_text('Solicitud rechazada (HTTP 400): Documento no disponible',exact=True).wait_for()
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
        page.locator('#notice').get_by_text('Solicitud rechazada (HTTP 400): Fuente no disponible',exact=True).wait_for()
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


def test_sports_query_clears_previous_result_and_preserves_unknowns(staged_backlot_server):
    schema={
        'coverage_note':'Solo UEFA',
        'competitions':['champions'],
        'parameters':{'properties':{
            'edition':{'type':'integer','minimum':1955},
            'player_id':{'type':'string'},
            'metrics':{'type':'array'},
            'phase':{'type':'string','enum':['TOURNAMENT','ALL']},
        }},
        'actions':[
            {'name':'compare_players','fields':['competition'],'required':['competition']},
            {'name':'player','fields':['competition','edition','player_id','metrics','phase'],
             'required':['competition','edition','player_id','metrics'],'defaults':{'phase':'TOURNAMENT'}},
            {'name':'definitions','fields':['competition'],'required':['competition']},
        ],
    }
    calls=[]
    def query(route):
        calls.append(route.request.post_data_json)
        route.fulfill(json={
            'success':len(calls)==1,
            'data':{
                'fuente':'UEFA',
                'registros':[{
                    'nombre':'<img src=x onerror=alert(1)>',
                    'fixture_stat':'fresh-result','goals':0,'assists':None,
                }],
            } if len(calls)==1 else None,
            'error':'Fuente temporalmente no disponible',
            'note':'Consulta de fixture sintético',
        })
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={
            'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188',
                        'model':'fixture','resource_roots':[]},'pipelines':[],'projects':[],
        }))
        page.route('**/api/studio/football/schema',lambda route:route.fulfill(json=schema))
        page.route('**/api/studio/football/query',query)
        page.goto(staged_backlot_server+'/studio#sports')
        expect(page.locator('#sports-action')).to_have_value('compare_players')
        page.locator('#sports-form button[type="submit"]').click()
        page.wait_for_function('document.querySelector("#sports-results").textContent.includes("fresh-result")')
        result=page.locator('#sports-results')
        assert result.get_by_text('goals: 0',exact=False).count()==1
        assert result.get_by_text('assists: desconocido',exact=False).count()==1
        assert result.locator('img').count()==0
        expect(page.locator('#sports-copy')).to_be_enabled()
        page.locator('#sports-form button[type="submit"]').click()
        expect(result).to_contain_text('Fuente temporalmente no disponible')
        assert 'fresh-result' not in result.inner_text()
        expect(page.locator('#sports-copy')).to_be_disabled()
        assert calls==[
            {'competition':'champions','action':'compare_players'},
            {'competition':'champions','action':'compare_players'},
        ]
        page.locator('#sports-action').select_option('player')
        page.locator('#sports-fields [name="edition"]').fill('2027')
        page.locator('#sports-fields [name="player_id"]').fill('12345')
        page.locator('#sports-fields [name="metrics"]').fill('goals, assists')
        page.locator('#sports-fields [name="phase"]').select_option('ALL')
        page.locator('#sports-form button[type="submit"]').click()
        expect(result).to_contain_text('Fuente temporalmente no disponible')
        assert calls[-1]=={
            'competition':'champions','action':'player','edition':2027,
            'player_id':'12345','metrics':['goals','assists'],'phase':'ALL',
        }
        page.locator('#sports-action').select_option('definitions')
        assert page.locator('#sports-fields [name]').count()==0
        assert errors==[]
        browser.close()

def test_football_definition_picker_uses_entity_and_competition_scope(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page();errors=[];calls=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={
            'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188',
                        'model':'fixture','resource_roots':[]},'pipelines':[],'projects':[]}))
        schema={'coverage_note':'Solo UEFA','competitions':['champions','europa'],
            'parameters':{'entity':{'type':'string'},'metrics':{'type':'array'}},
            'actions':[{'name':'definitions','fields':['competition'],'required':['competition']},
                {'name':'ranking','fields':['competition','entity','metrics'],'required':['competition','entity','metrics'],
                 'choices':{'entity':['player','team']}}]}
        page.route('**/api/studio/football/schema',lambda route:route.fulfill(json=schema))
        def query(route):
            calls.append(route.request.post_data_json)
            route.fulfill(json={'success':True,'note':'Fixture metadata','data':{
                'definiciones':[{'name':'goals','actors':['PLAYER']},{'name':'possession','actors':['TEAM']}]}})
        page.route('**/api/studio/football/query',query)
        page.goto(staged_backlot_server+'/studio#sports')
        expect(page.locator('#sports-action')).to_have_value('definitions')
        page.locator('#sports-form button[type="submit"]').click()
        expect(page.locator('#sports-results')).to_contain_text('Fixture metadata')
        assert calls==[{'competition':'champions','action':'definitions'}]
        page.locator('#sports-action').select_option('ranking')
        picker=page.get_by_role('combobox',name='Métrica de las definiciones oficiales',exact=True)
        assert picker.locator('option[value=goals]').count()==1
        assert picker.locator('option[value=possession]').count()==0
        page.get_by_role('button',name='Añadir métrica elegida',exact=True).click()
        page.get_by_role('button',name='Añadir métrica elegida',exact=True).click()
        metrics=page.locator('#sports-fields [name="metrics"]')
        assert metrics.input_value()=='goals'
        page.locator('#sports-fields [name="entity"]').select_option('team')
        assert metrics.input_value()==''
        assert picker.locator('option[value=possession]').count()==1
        assert picker.locator('option[value=goals]').count()==0
        page.locator('#sports-competition').select_option('europa')
        assert page.locator('#sports-definition-picker').is_hidden()
        assert calls==[{'competition':'champions','action':'definitions'}]
        assert errors==[]
        browser.close()

def test_official_id_followup_prepares_form_without_new_query(staged_backlot_server):
    """A reviewed UEFA follow-up fills the redesigned Comparativas form only."""
    schema={'coverage_note':'Solo UEFA','competitions':['champions'],
      'parameters':{'edition':{'type':'integer'},'player_id':{'type':'string'},'metrics':{'type':'array'}},
      'actions':[{'name':'compare_players','fields':['competition'],'required':['competition']},
        {'name':'player','fields':['competition','edition','player_id','metrics'],
         'required':['competition','edition','player_id','metrics']}]}
    calls=[]
    def query(route):
        calls.append(route.request.post_data_json)
        route.fulfill(json={'success':True,'note':'Fixture sintético','data':{
          'fuente':'UEFA','registros':[{'id':'123','nombre':'Fixture player'}]},
          'followups':[{'label':'Preparar jugador de prueba','query':{
            'action':'player','competition':'champions','edition':2027,
            'player_id':'123','metrics':['goals']}}]})
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={
            'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188',
                        'model':'fixture','resource_roots':[]},'pipelines':[],'projects':[]}))
        page.route('**/api/studio/football/schema',lambda route:route.fulfill(json=schema))
        page.route('**/api/studio/football/query',query)
        page.goto(staged_backlot_server+'/studio#sports')
        expect(page.locator('#sports-action')).to_have_value('compare_players')
        page.locator('#sports-form button[type="submit"]').click()
        page.get_by_role('button',name='Preparar jugador de prueba',exact=True).click()
        assert page.locator('#sports-action').input_value()=='player'
        assert page.locator('#sports-fields [name="player_id"]').input_value()=='123'
        assert page.locator('#sports-fields [name="edition"]').input_value()=='2027'
        assert page.locator('#sports-fields [name="metrics"]').input_value()=='goals'
        assert len(calls)==1
        assert calls[0]['action']=='compare_players'
        assert calls[0]['competition']=='champions'
        assert not errors
        browser.close()

def test_application_version_checks_require_explicit_action(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page();calls=[];errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={
            'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188',
                        'resource_roots':[],'model':''},'pipelines':[],'projects':[]}))
        page.route('**/api/studio/updates?*',lambda route:route.fulfill(json={
            'models':0,'applications':1,'untracked_catalog_files':0,'next_offset':None,'note':'fixture',
            'rows':[{'kind':'application','id':'deno','label':'Deno','configured':True,
                     'file_found':True,'live_check_supported':True}]}))
        def version(route):
            args=route.request.post_data_json;calls.append(args)
            route.fulfill(json={'status':'update_available' if args['online'] else 'local_version_checked',
                'local_version':'2.9.0','latest_version':'v2.10.0' if args['online'] else None,
                'note':'Consulta explícita; no instala ni actualiza.'})
        page.route('**/api/studio/updates/application-version',version)
        page.route('**/api/studio/updates/application-version-history?*',lambda route:route.fulfill(json={
            'note':'Resultados históricos; no certifican la versión actual.',
            'rows':[{'checked_at':'2026-11-22T20:00:00+00:00','local_version':'2.9.0',
                     'latest_version':'v2.10.0','local_executable':'D:/tools/deno.exe',
                     'executable_state':'configuration_changed'}]}))
        page.goto(staged_backlot_server+'/studio#models')
        page.locator('#updates-load').click()
        page.locator('#updates-result summary').click()
        assert not calls
        page.get_by_role('button',name='Ver versión local sin consulta remota',exact=True).click()
        page.get_by_text('Versión local comprobada; sin consulta remota',exact=True).wait_for()
        assert calls==[{'identifier':'deno','online':False}]
        page.get_by_role('button',name='Comparar versión instalada',exact=True).click()
        page.get_by_text('Hay una versión estable posterior',exact=True).wait_for()
        assert calls[-1]=={'identifier':'deno','online':True}
        before=len(calls)
        page.get_by_role('button',name='Ver historial de versiones',exact=True).click()
        page.get_by_text('La ruta configurada cambió',exact=True).wait_for()
        assert '2026-11-22T20:00:00+00:00' in page.locator('[data-application-version-history]').inner_text()
        assert len(calls)==before
        assert not errors
        browser.close()


def test_media_version_pair_is_explicit_and_warns_about_mismatch(staged_backlot_server):
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page();calls=[];errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={
            'settings':{'ollama_url':'http://127.0.0.1:11434','comfyui_url':'http://127.0.0.1:8188',
                        'resource_roots':[],'model':''},'pipelines':[],'projects':[]}))
        page.route('**/api/studio/updates?*',lambda route:route.fulfill(json={
            'models':0,'applications':2,'untracked_catalog_files':0,'next_offset':None,'note':'fixture',
            'rows':[{'kind':'application','id':identifier,'label':label,'configured':True,
                     'file_found':True,'live_check_supported':False}
                    for identifier,label in [('ffmpeg','FFmpeg'),('ffprobe','FFprobe')]]}))
        def media(route):
            calls.append(route.request.post_data_json)
            route.fulfill(json={'status':'version_mismatch','note':'Identificadores distintos; revisar sin instalar.',
                'applications':[{'id':'ffmpeg','local_version':'7.1.1'},{'id':'ffprobe','local_version':'8.0'}]})
        page.route('**/api/studio/updates/media-versions',media)
        page.goto(staged_backlot_server+'/studio#models')
        page.locator('#updates-load').click()
        page.get_by_text('FFmpeg · ejecutable encontrado',exact=True).click()
        assert not calls
        page.get_by_role('button',name='Comparar FFmpeg y FFprobe locales',exact=True).click()
        page.get_by_text('FFmpeg y FFprobe tienen versiones diferentes',exact=True).wait_for()
        assert 'ffmpeg: 7.1.1' in page.locator('[data-media-versions]').inner_text()
        assert 'ffprobe: 8.0' in page.locator('[data-media-versions]').inner_text()
        assert calls==[{}] and not errors
        browser.close()

@pytest.mark.parametrize('width', [375, 768, 1024, 1440])
def test_studio_editor_chrome_responsive_controls_and_icons(staged_backlot_server, width):
    """Computed responsive contract for the current Studio navigation; not visual approval."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page = browser.new_page(viewport={'width': width, 'height': 900})
        page.goto(staged_backlot_server + '/studio', wait_until='domcontentloaded')
        nav = page.locator('#main-nav')
        expect(nav).to_be_visible()
        data = page.evaluate("""() => {
          const nav = document.querySelector('#main-nav');
          const buttons = [...nav.querySelectorAll('button.nav-item')];
          const rect = nav.getBoundingClientRect();
          return {
            navLeft: rect.left,
            navRight: rect.right,
            navClientWidth: nav.clientWidth,
            navScrollWidth: nav.scrollWidth,
            pageScrollWidth: document.documentElement.scrollWidth,
            buttons: buttons.map(button => {
              const b = button.getBoundingClientRect();
              const icon = button.querySelector('svg');
              const i = icon && icon.getBoundingClientRect();
              const label = button.querySelector('span');
              const style = getComputedStyle(label || button);
              return {
                height: b.height,
                fontSize: parseFloat(style.fontSize),
                alignItems: getComputedStyle(button).alignItems,
                iconCentered: !i || Math.abs((i.top + i.height / 2) - (b.top + b.height / 2)) <= 1
              };
            })
          };
        }""")
        assert data['navLeft'] >= 0
        assert data['navRight'] <= width + 1
        assert data['pageScrollWidth'] <= width + 1
        assert data['buttons'] and len(data['buttons']) >= 8
        assert all(button['alignItems'] == 'center' and button['iconCentered'] for button in data['buttons'])
        if width <= 680:
            assert data['navScrollWidth'] >= data['navClientWidth']
            assert all(button['height'] >= 32 and button['fontSize'] >= 12 for button in data['buttons'])
        browser.close()



def test_pending_agent_approval_ignores_duplicate_click(staged_backlot_server):
    """A forced duplicate event cannot submit a second approval while pending."""
    import time
    calls=[]
    def delayed_approval(route):
        calls.append(route.request.method)
        time.sleep(.25)
        route.fulfill(json={'started':True,'project_id':'gate-idea'})
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        # Isolate identity and project state; exercise the current agent drawer
        # without depending on a real job or the production API.
        page.route('**/api/studio/identity',lambda route:route.fulfill(json={'restart_required':False}))
        page.route('**/api/studio/projects/gate-idea',lambda route:route.fulfill(json={
            'request':{'title':'Synthetic approval fixture'},
            'job':{'status':'awaiting_human','message':'Review fixture','events':[]},
            'active':False,
            'stages':[{'name':'Review fixture','status':'awaiting_human'}],
            'artifacts':[],'outputs':[],'board_url':'/fixture',
            'reference_video_url':'','channel_research':None,'channel_performance':None,
        }))
        page.route('**/api/studio/projects/gate-idea/approve',delayed_approval)
        page.goto(staged_backlot_server+'/studio?project=gate-idea')
        page.locator('#agent-toggle').click()
        expect(page.locator('#agent-drawer')).to_be_visible()
        approval=page.locator('#agent-approve')
        expect(approval).to_be_visible()
        approval.evaluate("el=>{el.click();el.dispatchEvent(new MouseEvent('click',{bubbles:true}));}")
        page.wait_for_timeout(700)
        assert calls==['POST']
        expect(page.locator('#agent-action-result')).to_contain_text('Aprobación registrada')
        browser.close()

def test_agent_activity_keeps_last_snapshot_during_temporary_read_failure(staged_backlot_server):
    """The user-facing drawer retains its last read and recovers on its next poll."""
    from copy import deepcopy
    pid = 'agent-ui-fixture'
    edit = {'revision':0,'undo':[],'redo':[],'events':[],'edit_decisions':{
        'version':'1.0','render_runtime':'ffmpeg','cuts':[],'audio_tracks':[],'cues':[],'sources':{},
        'output':{'ratio':'16:9','fps':24,'fit':'pad'},
        'subtitle_style':{'size':32,'position':'bottom','mode':'soft'}}}
    project = {'active':True,'production_pipeline_available':True,
        'job':{'status':'running','events':[{'kind':'stage','message':'Lectura inicial disponible','at':'2026-11-28T00:00:00Z'}]},
        'stages':[{'name':'Guion','status':'in_progress'}],'artifacts':[],'outputs':[]}
    reads=[]; writes=[]; recovery={'enabled':False}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1280,'height':800})
        # The editor module keeps loadAgentActivity private. Accelerate only its
        # five-second poll and exercise the same drawer toggle users activate.
        page.add_init_script("""(() => {
          const native = window.setInterval.bind(window);
          window.setInterval = (callback, delay, ...args) =>
            native(callback, delay === 5000 ? 100 : delay, ...args);
        })();""")
        page.on('request',lambda request:writes.append(request.url) if request.method=='POST' else None)
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[{'project_id':pid,'title':'Agent panel JSON fixture'}]))
        page.route('**/api/studio/editor/'+pid,lambda route:route.fulfill(json=edit))
        def project_state(route):
            assert route.request.method=='GET'
            reads.append(route.request.method)
            if len(reads)>=2 and not recovery['enabled']:
                route.abort('failed')
                return
            result=deepcopy(project)
            if recovery['enabled']:
                result['job']['events']=[{'kind':'stage','message':'Lectura recuperada','at':'2026-11-28T00:00:05Z'}]
            route.fulfill(json=result)
        page.route('**/api/studio/projects/'+pid,project_state)
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        page.locator('#agent-toggle').click()
        expect(page.locator('#events')).to_contain_text('Lectura inicial disponible')
        expect(page.locator('#agent-status')).to_contain_text('Conexión temporalmente no disponible',timeout=3000)
        expect(page.locator('#events')).to_contain_text('Lectura inicial disponible')
        recovery['enabled']=True
        expect(page.locator('#events')).to_contain_text('Lectura recuperada',timeout=3000)
        assert len(reads)>=3
        assert writes==[]
        browser.close()


def test_sports_followup_prepares_form_without_sending_second_query(staged_backlot_server):
    """A returned follow-up fills the new Comparativas form; the user submits it."""
    schema={'coverage_note':'Solo UEFA','competitions':['champions'],
      'parameters':{'edition':{'type':'integer'},'player_id':{'type':'string'},'metrics':{'type':'array'}},
      'actions':[{'name':'definitions','fields':['competition'],'required':['competition']},
        {'name':'player','fields':['competition','edition','player_id','metrics'],
         'required':['competition','edition','player_id','metrics']}]}
    calls=[]
    def query(route):
        calls.append(route.request.post_data_json)
        route.fulfill(json={'success':True,'note':'Fixture sintético','data':{
          'fuente':'UEFA','registros':[{'nombre':'Jugador de prueba'}]},
          'followups':[{'label':'Preparar jugador de prueba','query':{
            'action':'player','competition':'champions','edition':2027,
            'player_id':'12345','metrics':['goals']}}]})
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/football/schema',lambda route:route.fulfill(json=schema))
        page.route('**/api/studio/football/query',query)
        page.goto(staged_backlot_server+'/studio#sports')
        page.locator('#main-nav [data-module="sports"]').click()
        expect(page.locator('#sports-competition option')).to_have_count(1)
        page.locator('#sports-form button[type="submit"]').click()
        page.get_by_role('button',name='Preparar jugador de prueba').click()
        expect(page.locator('#sports-action')).to_have_value('player')
        expect(page.locator('#sports-fields [name="edition"]')).to_have_value('2027')
        expect(page.locator('#sports-fields [name="player_id"]')).to_have_value('12345')
        expect(page.locator('#sports-fields [name="metrics"]')).to_have_value('goals')
        assert calls==[{'competition':'champions','action':'definitions'}]
        browser.close()


def test_sports_failed_query_clears_previous_result_and_disables_copy(staged_backlot_server):
    """A failed later lookup cannot leave an older report available to copy."""
    calls=[]
    def query(route):
        calls.append(route.request.post_data_json)
        if len(calls)==1:
            route.fulfill(json={'success':True,'data':{'fuente':'UEFA','fixture':'resultado anterior'}})
        else:
            route.fulfill(status=503,json={'detail':'Fuente temporalmente no disponible'})
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        schema={'competitions':['champions'],'parameters':{},
          'actions':[{'name':'definitions','fields':['competition'],'required':['competition']}]}
        page.route('**/api/studio/football/schema',lambda route:route.fulfill(json=schema))
        page.route('**/api/studio/football/query',query)
        page.goto(staged_backlot_server+'/studio#sports')
        page.locator('#main-nav [data-module="sports"]').click()
        page.locator('#sports-form button[type="submit"]').click()
        expect(page.locator('#sports-results')).to_contain_text('resultado anterior')
        expect(page.locator('#sports-copy')).to_be_enabled()
        page.locator('#sports-form button[type="submit"]').click()
        expect(page.locator('#sports-results')).to_contain_text('Fuente temporalmente no disponible')
        expect(page.locator('#sports-results')).not_to_contain_text('resultado anterior')
        expect(page.locator('#sports-copy')).to_be_disabled()
        assert calls==[{'competition':'champions','action':'definitions'}]*2
        browser.close()


def test_wan_text_to_video_stays_disabled_until_backend_identity_matches(staged_backlot_server):
    """An old resident backend must not trigger preflight or expose the prompt."""
    pid='qa-t2v-stale-backend'
    identity={'restart_required':True,'resident':{'sha256':'a'*64},'disk':{'sha256':'b'*64}}
    edit={'revision':0,'undo':[],'redo':[],'events':[],'edit_decisions':{
        'version':'1.0','render_runtime':'ffmpeg','cuts':[],'audio_tracks':[],'cues':[],'sources':{},
        'output':{'ratio':'16:9','fps':24,'fit':'pad'},
        'subtitle_style':{'size':32,'position':'bottom','mode':'soft'}}}
    preflight=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/identity',lambda route:route.fulfill(json=identity))
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[{'project_id':pid,'title':'QA T2V · identidad antigua'}]))
        page.route('**/api/studio/editor/'+pid,lambda route:route.fulfill(json=edit))
        page.route('**/api/studio/editor/'+pid+'/text-to-video/availability',
                   lambda route:(preflight.append(route.request.url),route.fulfill(json={'available':True})))
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        expect(page.locator('#mode-text-to-video')).to_be_disabled()
        expect(page.locator('#text-to-video-prompt')).to_be_disabled()
        expect(page.locator('#text-to-video-status')).to_contain_text('necesita activación')
        assert preflight==[]
        browser.close()


def test_wan_text_to_video_receipt_preview_and_add_use_project_scoped_api(staged_backlot_server):
    """Synthetic UI/API transport only; it does not contact ComfyUI or infer."""
    pid='qa-t2v-ui-flow'
    identity={'restart_required':False,'resident':{'sha256':'a'*64},'disk':{'sha256':'a'*64}}
    edit={'revision':0,'undo':[],'redo':[],'events':[],'workspace':{'project_path':'/projects/qa-t2v-ui-flow'},
        'edit_decisions':{'version':'1.0','render_runtime':'ffmpeg','cuts':[],'audio_tracks':[],'cues':[],'sources':{},
        'output':{'ratio':'16:9','fps':24,'fit':'pad'},
        'subtitle_style':{'size':32,'position':'bottom','mode':'soft'}}}
    posts=[]
    added=[]
    def video_url(request_id):
        return f'/api/studio/editor/{pid}/text-to-video/requests/{request_id}/video'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.on('pageerror',lambda error:pytest.fail(f'Error de página: {error}'))
        page.route('**/api/studio/identity',lambda route:route.fulfill(json=identity))
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[{'project_id':pid,'title':'QA T2V sintético'}]))
        page.route('**/api/studio/editor/'+pid,lambda route:route.fulfill(json=edit))
        page.route('**/api/studio/editor/'+pid+'/render',lambda route:route.fulfill(json={'status':'idle'}))
        page.route('**/api/studio/comfy-history/projects/'+pid,lambda route:route.fulfill(json={'reports':[]}))
        page.route('**/api/studio/editor/'+pid+'/text-to-video/availability',
                   lambda route:route.fulfill(json={'available':True,'profile':'wan22-14b-t2v-4step',
                       'workflow':'wan22-t2v-4step.json','required_models':6}))
        def list_results(route):
            if not posts:
                route.fulfill(json=[])
                return
            request_id=posts[0]['request_id']
            route.fulfill(json=[{'request_id':request_id,'label':'Vídeo generado · Wan 2.2',
                'model':'Wan 2.2 fixture','bytes':1234,'completed_at':'2026-11-28T12:00:00Z',
                'video_url':video_url(request_id)}])
        page.route('**/api/studio/editor/'+pid+'/text-to-video/results',list_results)
        def submit(route):
            data=route.request.post_data_json
            posts.append(data)
            route.fulfill(status=202,json={'request_id':data['request_id'],'state':'queued'})
        page.route('**/api/studio/editor/'+pid+'/text-to-video',submit)
        def status(route):
            request_id=route.request.url.rsplit('/',1)[-1]
            route.fulfill(json={'request_id':request_id,'project_id':pid,'state':'completed',
                'profile':'wan22-14b-t2v-4step','completed_at':'2026-11-28T12:00:00Z',
                'video_url':video_url(request_id),'bytes':1234,'model':'Wan 2.2 fixture'})
        page.route('**/api/studio/editor/'+pid+'/text-to-video/requests/*',status)
        page.route('**/api/studio/editor/'+pid+'/text-to-video/requests/*/video',
                   lambda route:route.fulfill(status=204,content_type='video/mp4',body=b''))
        def add(route):
            added.append(route.request.post_data_json)
            request_id=route.request.url.split('/requests/',1)[1].rsplit('/add',1)[0]
            after=dict(edit)
            after['revision']=1
            after['edit_decisions']=dict(edit['edit_decisions'])
            after['edit_decisions']['sources']={'generated-source':{
                'path':f'medios_generados/wan-t2v-{request_id}.mp4','kind':'video','duration':2,
                'origin':'wan_t2v_receipt','original_name':'Vídeo generado · Wan 2.2'}}
            route.fulfill(json={'source_id':'generated-source','clip_id':'clip-1','edit':after})
        page.route('**/api/studio/editor/'+pid+'/text-to-video/requests/*/add',add)
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        expect(page.locator('#mode-text-to-video')).to_be_enabled()
        expect(page.locator('#text-to-video-mode-status')).to_have_text('Wan 2.2 local · disponible')
        page.locator('#mode-text-to-video').click()
        prompt='Nubes sintéticas sobre un paisaje geométrico'
        page.locator('#text-to-video-prompt').fill(prompt)
        page.locator('#text-to-video-submit').click()
        expect(page.locator('#text-to-video-status')).to_contain_text('Vídeo listo',timeout=5000)
        expect(page.locator('#text-to-video-results')).to_contain_text('Wan 2.2')
        assert len(posts)==1
        assert posts[0]['prompt']==prompt
        request_id=posts[0]['request_id']
        assert len(request_id)==32 and all(char in '0123456789abcdef' for char in request_id)
        page.locator('#text-to-video-results').get_by_role('button',name='Vista previa').click()
        expect(page.locator('#preview-video')).to_have_attribute('src',video_url(request_id))
        page.locator('#text-to-video-results').get_by_role('button',name='Añadir a la línea de tiempo').click()
        expect(page.locator('#edit-revision')).to_have_text('Revisión 1')
        assert added==[{'revision':0}]
        browser.close()

def test_agent_project_context_and_uncertain_clarification_retry_are_idempotent(staged_backlot_server):
    """Synthetic browser transport; one lost response must not duplicate a note."""
    import json
    from pathlib import Path
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    pid=fixture['project_id'];editor_state=fixture['state'];clarifications=[];posts=[]
    request={'title':'QA context fixture','brief':'No cortar la negación <script>alert(1)</script>.','language':'es','pipeline':'fixture'}
    project={'request':request,'job':{'status':'ready','events':[]},'stages':[],
             'active':False,'production_pipeline_available':True}
    identity={'schema_version':1,'api_protocol':1,'restart_required':False,
              'resident':{'sha256':'a'*64},'disk':{'sha256':'a'*64}}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.on('pageerror',lambda error:pytest.fail(f'JavaScript error: {error}'))
        def api(route):
            path=route.request.url.split('?',1)[0];method=route.request.method
            if path.endswith('/api/health'):route.fulfill(json={'ok':True,'app':'backlot'});return
            if path.endswith('/api/studio/identity'):route.fulfill(json=identity);return
            if path.endswith('/api/studio/bootstrap'):route.fulfill(json={'projects':[{'project_id':pid,'title':request['title']}],'settings':{}});return
            if path.endswith('/api/studio/storage'):route.fulfill(json={'active_projects_dir':'/fixture','configured_projects_dir':'/fixture','available':True});return
            if path.endswith('/api/studio/editor/capabilities'):route.fulfill(json={'commands':[]});return
            if path.endswith('/api/studio/editor/projects'):route.fulfill(json=[{'project_id':pid,'title':request['title']}]);return
            if path==f'/api/studio/editor/{pid}':route.fulfill(json=editor_state);return
            if path==f'/api/studio/comfy-history/projects/{pid}':route.fulfill(json={'reports':[]});return
            if path==f'/api/studio/projects/{pid}':route.fulfill(json=project);return
            if path==f'/api/studio/clarifications/{pid}' and method=='GET':
                route.fulfill(json={'clarifications':list(clarifications),'active':False});return
            if path==f'/api/studio/clarifications/{pid}' and method=='POST':
                payload=route.request.post_data_json;posts.append(payload)
                existing=next((item for item in clarifications if item['request_id']==payload['request_id']),None)
                if not posts[:-1]:
                    clarifications.append({'request_id':payload['request_id'],'message':payload['message'],'at':'2026-11-28T12:00:00Z'})
                    route.fulfill(status=503,json={'detail':'Respuesta perdida después de guardar'});return
                if existing is None:clarifications.append({'request_id':payload['request_id'],'message':payload['message'],'at':'2026-11-28T12:01:00Z'})
                route.fulfill(json={'saved':True,'duplicate':existing is not None});return
            route.fulfill(status=404,json={'detail':'No fixture for '+method+' '+path})
        page.route('**/api/**',api)
        page.goto(staged_backlot_server+f'/studio?project={pid}#video')
        page.locator('#project-select').select_option(pid)
        page.locator('#agent-toggle').click()
        expect(page.locator('#agent-request')).to_contain_text('QA context fixture')
        expect(page.locator('#agent-request')).to_contain_text(request['brief'])
        assert page.locator('#agent-request script').count()==0
        field=page.locator('#agent-clarification-text')
        field.fill(request['brief'])
        page.locator('#agent-clarification-form button[type=submit]').click()
        expect(page.locator('#agent-clarification-status')).to_contain_text('Respuesta no confirmada')
        field.fill(request['brief'])
        page.locator('#agent-clarification-form button[type=submit]').click()
        expect(page.locator('.agent-clarification')).to_have_count(1)
        expect(page.locator('#agent-clarifications')).to_contain_text(request['brief'])
        assert len(posts)==2 and posts[0]['request_id']==posts[1]['request_id']
        assert posts[0]['message']==posts[1]['message']==request['brief']
        assert page.locator('#agent-clarifications script').count()==0
        browser.close()

