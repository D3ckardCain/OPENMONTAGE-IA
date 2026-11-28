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


def test_manual_editor_split_undo_redo_and_reopen_use_current_studio_contract(staged_backlot_server):
    """Exercise the current Studio timeline UI with synthetic API state; no media playback."""
    from copy import deepcopy
    import json
    from pathlib import Path

    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    original=deepcopy(fixture['state'])
    state=deepcopy(original)
    pid=fixture['project_id']
    calls=[]
    split_snapshot=None
    project={'project_id':pid,'title':'Montaje de prueba','project_path':'QA/Montaje de prueba'}

    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':1920,'height':1080})
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/health',lambda route:route.fulfill(json={'ok':True,'app':'backlot'}))
        page.route('**/api/studio/identity',lambda route:route.fulfill(json={'restart_required':False,'resident':{'sha256':'a'*64},'disk':{'sha256':'a'*64}}))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={'settings':{},'pipelines':[],'projects':[project]}))
        page.route('**/api/studio/storage',lambda route:route.fulfill(json={'active_projects_dir':'QA','available':True}))
        page.route('**/api/studio/editor/capabilities',lambda route:route.fulfill(json={'commands':['split','undo','redo','save']}))
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[project]))
        page.route('**/api/studio/editor/'+pid,lambda route:route.fulfill(json=state))
        page.route('**/api/studio/comfy-history/projects/'+pid,lambda route:route.fulfill(json={'reports':[]}))
        page.route('**/api/studio/editor/'+pid+'/text-to-video/availability',lambda route:route.fulfill(json={'available':False,'reason':'No generation in this UI fixture.'}))

        def command(route):
            nonlocal split_snapshot
            data=route.request.post_data_json
            calls.append(data)
            assert data['revision']==state['revision']
            operation=data['operation']
            if operation=='split':
                assert data['track']=='video'
                assert data['at']==pytest.approx(2.5)
                cuts=state['edit_decisions']['cuts']
                index=next(i for i,clip in enumerate(cuts) if clip['id']==data['id'])
                assert index==1
                clip=cuts[index]
                assert clip['in_seconds']==pytest.approx(10.5)
                assert clip['out_seconds']==pytest.approx(12)
                clip['out_seconds']=11
                cuts.insert(index+1,{**clip,'id':'split-part','in_seconds':11,'out_seconds':12})
                split_snapshot=deepcopy(state['edit_decisions'])
                state['undo']=[deepcopy(original['edit_decisions'])]
                state['redo']=[]
            elif operation=='undo':
                assert split_snapshot is not None
                state['edit_decisions']=deepcopy(original['edit_decisions'])
                state['undo']=[]
                state['redo']=[deepcopy(split_snapshot)]
            elif operation=='redo':
                assert split_snapshot is not None
                state['edit_decisions']=deepcopy(split_snapshot)
                state['undo']=[deepcopy(original['edit_decisions'])]
                state['redo']=[]
            elif operation=='save':
                assert len(state['edit_decisions']['cuts'])==3
            else:
                raise AssertionError(f'Unexpected editor operation: {operation}')
            state['revision']+=1
            state['edit_sha256']=str(state['revision']).zfill(64)
            route.fulfill(json=deepcopy(state))

        page.route('**/api/studio/editor/'+pid+'/command',command)
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']))
        video_clips=page.locator('#timeline-tracks .track-row').first.locator('.timeline-clip')
        expect(video_clips).to_have_count(2)
        video_clips.nth(1).click()
        page.locator('#playhead').fill('2.5')
        page.locator('#clip-split').click()
        expect(page.locator('#timeline-tracks .track-row').first.locator('.timeline-clip')).to_have_count(3)
        expect(page.locator('#edit-undo')).to_be_enabled()
        page.locator('#edit-undo').click()
        expect(page.locator('#timeline-tracks .track-row').first.locator('.timeline-clip')).to_have_count(2)
        expect(page.locator('#edit-redo')).to_be_enabled()
        page.locator('#edit-redo').click()
        expect(page.locator('#timeline-tracks .track-row').first.locator('.timeline-clip')).to_have_count(3)
        page.locator('#edit-save').click()
        expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+4))
        page.reload()
        expect(page.locator('#edit-revision')).to_contain_text(str(original['revision']+4))
        expect(page.locator('#timeline-tracks .track-row').first.locator('.timeline-clip')).to_have_count(3)
        assert [call['operation'] for call in calls]==['split','undo','redo','save']
        assert not errors
        browser.close()

@pytest.mark.parametrize('width,height',[(1920,1080),(3440,1440)])
def test_timeline_includes_audio_tail_in_current_studio_layout(staged_backlot_server,width,height):
    """Current Studio DOM shows complete video/audio/subtitle tracks and their shared duration."""
    from copy import deepcopy
    import json
    from pathlib import Path

    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    state=deepcopy(fixture['state'])
    pid=fixture['project_id']
    edl=state['edit_decisions']
    edl['cuts'][0].update(in_seconds=0,out_seconds=30)
    edl['cuts'][1].update(in_seconds=40,out_seconds=70)
    edl['audio_tracks'][0].update(start_seconds=62,in_seconds=0,out_seconds=4,speed=1)
    project={'project_id':pid,'title':'Long JSON timeline; no CI media'}

    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':width,'height':height})
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/api/health',lambda route:route.fulfill(json={'ok':True,'app':'backlot'}))
        page.route('**/api/studio/identity',lambda route:route.fulfill(json={'restart_required':False,'resident':{'sha256':'a'*64},'disk':{'sha256':'a'*64}}))
        page.route('**/api/studio/bootstrap',lambda route:route.fulfill(json={'settings':{},'pipelines':[],'projects':[project]}))
        page.route('**/api/studio/storage',lambda route:route.fulfill(json={'active_projects_dir':'QA','available':True}))
        page.route('**/api/studio/editor/capabilities',lambda route:route.fulfill(json={'commands':['split','undo','redo','save']}))
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[project]))
        page.route('**/api/studio/editor/'+pid,lambda route:route.fulfill(json=state))
        page.route('**/api/studio/comfy-history/projects/'+pid,lambda route:route.fulfill(json={'reports':[]}))
        page.route('**/api/studio/editor/'+pid+'/text-to-video/availability',lambda route:route.fulfill(json={'available':False,'reason':'Synthetic browser fixture.'}))
        page.goto(staged_backlot_server+'/studio?project='+pid+'#video')
        expect(page.locator('#edit-revision')).to_contain_text(str(state['revision']))
        expect(page.locator('#timeline-duration')).to_contain_text('66.00 s')
        rows=page.locator('#timeline-tracks .track-row')
        expect(rows).to_have_count(3)
        expect(rows.nth(0).locator('.track-name')).to_have_text('Vídeo')
        expect(rows.nth(1).locator('.track-name')).to_have_text('Audio')
        expect(rows.nth(2).locator('.track-name')).to_have_text('Subtítulos')
        position=page.get_by_role('spinbutton',name='Posición del cabezal en segundos')
        expect(position).to_be_visible()
        position.fill('66')
        page.screenshot(path=f'tests/qa/output/studio-editor/timeline-audio-tail-{width}x{height}.png',full_page=True)
        assert errors==[]
        browser.close()
