"""UI handoff contract with synthetic transport; no inference claims."""
import os
import pytest
pytest.importorskip('playwright.sync_api')
from playwright.sync_api import sync_playwright, expect
from tests.backlot.test_ui_bug_bash import staged_backlot_server


def test_projects_menu_refreshes_agent_created_projects_without_losing_selection(staged_backlot_server):
    """Shared-project discovery/DOM contract; no audiovisual claims."""
    projects=[{'project_id':'shared-a','title':'Selected JSON project'}]
    state={'revision':0,'edit_sha256':'a'*64,'undo':[],'redo':[],'events':[],
           'edit_decisions':{'version':'1.0','render_runtime':'ffmpeg','cuts':[], 'audio_tracks':[],
             'cues':[],'sources':{},'output':{'ratio':'16:9','fps':24,'fit':'pad'},
             'subtitle_style':{'size':32,'position':'bottom','mode':'soft'}}}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=projects))
        page.route('**/api/studio/editor/shared-a',lambda route:route.fulfill(json=state))
        page.route('**/api/studio/editor/shared-a/render',lambda route:route.fulfill(json={'status':'idle'}))
        page.goto(staged_backlot_server+'/studio?edit=shared-a#library')
        expect(page.locator('#edit-revision')).to_have_text('Revisión 0 · guardado local')
        projects.append({'project_id':'shared-b','title':'Created through another client'})
        page.locator('[data-section="edit-projects"]').click()
        expect(page.locator('#edit-project option[value="shared-b"]')).to_have_count(1)
        expect(page.locator('#edit-project')).to_have_value('shared-a')
        expect(page.locator('#edit-revision')).to_have_text('Revisión 0 · guardado local')
        browser.close()


def test_save_keeps_preview_but_edit_invalidates_it(staged_backlot_server):
    """Transport/DOM regression only; real FFmpeg evidence is a separate opt-in run."""
    state = {'revision':0,'edit_sha256':'a'*64,'undo':[],'redo':[],'events':[],
             'edit_decisions':{'version':'1.0','render_runtime':'ffmpeg','cuts':[], 'audio_tracks':[],
                'cues':[],'sources':{},'output':{'ratio':'16:9','fps':24,'fit':'pad'},
                'subtitle_style':{'size':32,'position':'bottom','mode':'soft'}}}
    job = {'status':'completed','attempt':'fixture','revision':0,'edit_sha256':'a'*64,
           'current':True,'preview':True,'url':'/fixture-editor-preview.mp4','subtitle_mode':'none'}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page()
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[{'project_id':'save-fixture','title':'JSON fixture'}]))
        page.route('**/api/studio/editor/save-fixture',lambda route:route.fulfill(json=state))
        page.route('**/api/studio/editor/save-fixture/render',lambda route:route.fulfill(json=job))
        page.route('**/fixture-editor-preview.mp4',lambda route:route.fulfill(status=204))
        def command(route):
            data=route.request.post_data_json
            assert data['revision']==state['revision']
            state['revision']+=1
            if data['operation']=='output':
                state['edit_sha256']='b'*64
                state['edit_decisions']['output']['ratio']=data['ratio']
            route.fulfill(json=state)
        page.route('**/api/studio/editor/save-fixture/command',command)
        page.goto(staged_backlot_server+'/studio?edit=save-fixture#video')
        expect(page.locator('#edit-player')).to_have_attribute('src','/fixture-editor-preview.mp4')
        page.locator('#edit-save').click()
        expect(page.locator('#edit-revision')).to_have_text('Revisión 1 · guardado local')
        expect(page.locator('#edit-player')).to_have_attribute('src','/fixture-editor-preview.mp4')
        page.locator('#edit-reopen').click()
        expect(page.locator('#manual-editor')).not_to_have_attribute('aria-busy','true')
        expect(page.locator('#edit-player')).to_have_attribute('src','/fixture-editor-preview.mp4')
        page.locator('#edit-preset').select_option('9:16');page.locator('#edit-output').click()
        expect(page.locator('#edit-revision')).to_have_text('Revisión 2 · guardado local')
        expect(page.locator('#edit-player')).not_to_have_attribute('src','/fixture-editor-preview.mp4')
        browser.close()


@pytest.mark.parametrize('width,height', [(1280,720),(1920,1080),(2560,1440),(3440,1440),(640,720)])
def test_manual_editor_layout_and_shared_revision_controls(staged_backlot_server, width, height, tmp_path):
    """Browser/transport evidence, with labeled synthetic JSON; no media or AI."""
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
        page.goto(staged_backlot_server + '/studio?edit=ui-fixture#video')
        expect(page.locator('#edit-revision')).to_have_text('Revisión 0 · guardado local')
        assert page.locator('#manual-editor').is_visible()
        assert page.locator('#legacy-studio').is_hidden()
        assert page.locator('#edit-player').count() == 1
        assert page.locator('#manual-editor').bounding_box()['width'] >= width - 32
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
        page.locator('[data-section="subtitles"]').click()
        assert page.locator('#edit-subtitle-panel').is_visible()
        assert page.locator('#edit-project').input_value() == 'ui-fixture'
        page.locator('[data-section="audio"]').click()
        assert page.locator('#edit-subtitle-panel').is_hidden()
        page.locator('#edit-preset').select_option('9:16')
        page.locator('#edit-output').click()
        expect(page.locator('#edit-revision')).to_have_text('Revisión 1 · guardado local')
        assert calls == [{'operation':'output','revision':0,'ratio':'9:16','fps':24}]
        page.locator('#edit-save').click()
        expect(page.locator('#edit-revision')).to_have_text('Revisión 2 · guardado local')
        page.locator('#edit-reopen').click()
        assert page.locator('#edit-project').input_value() == 'ui-fixture'
        page.locator('[data-section="video"]').click()
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
    """Real EDL snapshot, intercepted transport. Layout evidence only, not playback."""
    import json
    from pathlib import Path
    fixture=json.loads(Path('tests/fixtures/editor_existing_project_layout.json').read_text(encoding='utf-8'))
    pid=fixture['project_id'];state=fixture['state'];job=fixture['render']
    output=Path('tests/qa/output/studio-editor');output.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('OPENMONTAGE_TEST_CHROMIUM'))
        page=browser.new_page(viewport={'width':width,'height':height});errors=[];writes=[]
        page.add_init_script("""if(!localStorage.getItem('layout-test-seeded')){
            localStorage.setItem('edit-layout-version','2');localStorage.setItem('edit-track-size','160');
            localStorage.setItem('edit-library-size','180');localStorage.setItem('unrelated-preference','keep');
            localStorage.setItem('layout-test-seeded','true');}""")
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:writes.append(request.url) if request.method=='POST' else None)
        page.route('**/api/studio/editor/projects',lambda route:route.fulfill(json=[{'project_id':pid,'title':fixture['title']}]))
        page.route('**/api/studio/editor/'+pid,lambda route:route.fulfill(json=state))
        page.route('**/api/studio/editor/'+pid+'/render',lambda route:route.fulfill(json=job))
        page.route('**/media/**',lambda route:route.fulfill(status=204))
        page.route('**/api/studio/editor/'+pid+'/source/**',lambda route:route.fulfill(status=204))
        page.goto(staged_backlot_server+'/studio?edit='+pid+'#video')
        expect(page.locator('#edit-revision')).to_contain_text(str(state['revision']))
        expect(page.locator('#edit-player')).to_have_attribute('src',job['url'])
        expect(page.locator('#edit-render-status')).to_contain_text('texto visible quemado')
        # Stress the intrinsic 1920x1080 media size without claiming decoded frames.
        page.locator('#edit-player').evaluate('(v)=>{v.width=1920;v.height=1080}')
        def bounds():
            return page.evaluate('''()=>({viewport:{width:innerWidth,height:innerHeight},
                document:{width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight},
                panels:Object.fromEntries(['editor-library','editor-monitor','editor-inspector','editor-timeline'].map(id=>{
                  const r=document.getElementById(id).getBoundingClientRect();return [id,{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}]}))})''')
        def contained():
            b=bounds();assert b['document']['height']<=height+1;assert b['document']['width']<=width+1
            for panel in b['panels'].values():
                assert panel['y']>=0 and panel['bottom']<=height+1
            assert b['panels']['editor-timeline']['height']>=159
            positions=page.evaluate('''()=>Object.fromEntries(['editor-upper','editor-timeline','edit-tracks','editor-tools'].map(id=>{const r=document.getElementById(id).getBoundingClientRect();return [id,{top:r.top,bottom:r.bottom}]}))''')
            assert positions['editor-timeline']['top']>=positions['editor-upper']['bottom']
            assert positions['editor-tools']['top']>=positions['edit-tracks']['bottom']-1
            assert positions['editor-tools']['bottom']<=positions['editor-timeline']['bottom']+1
            return b
        before=contained();src=page.locator('#edit-player').get_attribute('src')
        assert before['panels']['editor-library']['width']>=319
        assert before['panels']['editor-timeline']['height']>=359
        assert page.evaluate("localStorage.getItem('edit-layout-version')")=='4'
        fit_scale=float(page.locator('#edit-zoom').input_value())
        assert fit_scale>160
        ticks=page.locator('.editor-ruler span').all_text_contents()
        assert max(float(t.split()[0]) for t in ticks)<=3.5
        page.locator('#edit-zoom-in').click()
        assert float(page.locator('#edit-zoom').input_value())>fit_scale
        page.locator('#edit-fit').click()
        assert abs(float(page.locator('#edit-zoom').input_value())-fit_scale)<.01
        assert page.locator('#editor-inspector #edit-clip-form').count()==1
        assert page.locator('#editor-inspector #edit-subtitle-panel').count()==1
        assert page.locator('#edit-tracks .editor-ruler').count()==1
        assert page.locator('#edit-tracks .editor-cues .editor-clip').count()==len(state['edit_decisions']['cues'])
        track_bounds=page.locator('#edit-tracks').bounding_box()
        for lane in page.locator('#edit-tracks .editor-lane').all():
            lane_bounds=lane.bounding_box()
            assert lane_bounds['y']>=track_bounds['y']-1
            assert lane_bounds['y']+lane_bounds['height']<=track_bounds['y']+track_bounds['height']+1
        assert page.locator('#edit-split').is_disabled()
        page.screenshot(path=str(output/f'existing-layout-{width}x{height}-default.png'),full_page=True)
        for identifier,dx,dy in [('library',60,0),('inspector',-50,0),('timeline',0,-40)]:
            box=page.locator('#edit-split-'+identifier).bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+dx,y+dy,steps=5);page.mouse.up()
        page.locator('#edit-split-timeline').focus();page.keyboard.press('ArrowUp')
        resized=contained()
        assert resized['panels']['editor-library']['width']>=before['panels']['editor-library']['width']+55
        assert resized['panels']['editor-inspector']['width']>=before['panels']['editor-inspector']['width']+45
        assert resized['panels']['editor-timeline']['height']>=before['panels']['editor-timeline']['height']+50
        assert resized['panels']['editor-monitor']['height']<before['panels']['editor-monitor']['height']
        page.reload();expect(page.locator('#edit-revision')).to_contain_text(str(state['revision']))
        restored=contained()
        for identifier in resized['panels']:
            for dimension in ['width','height']:
                assert abs(restored['panels'][identifier][dimension]-resized['panels'][identifier][dimension])<=1
        page.locator('#edit-layout-options summary').click()
        page.locator('#edit-hide-library').check();page.locator('#edit-hide-inspector').check()
        page.locator('#edit-hide-library').uncheck();page.locator('#edit-hide-inspector').uncheck()
        page.keyboard.press('Escape')
        assert abs(contained()['panels']['editor-library']['width']-resized['panels']['editor-library']['width'])<=1
        for section in ['audio','subtitles','video']:
            page.locator('[data-section="'+section+'"]').click();contained()
            assert page.locator('#edit-project').input_value()==pid
        page.locator('.editor-cues .editor-clip').first.click()
        assert page.locator('#edit-subtitle-panel').is_visible()
        assert page.locator('#edit-cue-index').input_value()=='1'
        assert state['edit_decisions']['cues'][0]['text'] in page.locator('#edit-srt').input_value()
        contained();page.locator('[data-section="video"]').click()
        # Enormous saved preferences must be clamped to a usable current viewport.
        page.evaluate("localStorage.setItem('edit-track-size','9999');localStorage.setItem('edit-library-size','9999')")
        page.reload();expect(page.locator('#edit-revision')).to_contain_text(str(state['revision']))
        clamped=contained();assert clamped['panels']['editor-monitor']['height']>=199
        page.locator('#edit-split-timeline').focus();page.keyboard.press('Home');contained()
        page.locator('#edit-split-timeline').focus();page.keyboard.press('End');contained()
        assert page.locator('#edit-player').get_attribute('src')==src
        page.locator('.editor-video .editor-clip').first.click()
        expect(page.locator('#edit-clip-form')).to_be_visible()
        assert not page.locator('#edit-split').is_disabled()
        assert page.locator('#edit-player').get_attribute('src')==src
        page.locator('#edit-view-source').click()
        assert page.locator('#edit-player').get_attribute('src')!=src
        page.locator('#edit-show-montage').click()
        expect(page.locator('#edit-player')).to_have_attribute('src',src)
        assert page.locator('#edit-clip-tools').get_attribute('open') is not None
        scroll=page.locator('#editor-inspector').evaluate('(p)=>{p.scrollTop=p.scrollHeight;return {top:p.scrollTop,height:p.clientHeight,total:p.scrollHeight,overflow:getComputedStyle(p).overflowY}}')
        assert scroll['overflow']=='auto' and scroll['top']>0
        contained()
        assert not writes and not errors
        page.screenshot(path=str(output/f'existing-layout-{width}x{height}-clamped.png'),full_page=True)
        (output/f'existing-layout-{width}x{height}.json').write_text(json.dumps({
            'scope':fixture['scope'],'project_id':pid,'revision':state['revision'],'edit_sha256':state['edit_sha256'],
            'before':before,'resized':resized,'restored':restored,'clamped':clamped,'inspector_scroll':scroll,'writes':writes,'page_errors':errors},indent=2),encoding='utf-8')
        page.locator('#edit-layout-options summary').click();page.locator('#edit-layout-reset').click();page.keyboard.press('Escape')
        reset=contained();assert reset['panels']['editor-library']['width']==320
        assert page.evaluate("localStorage.getItem('unrelated-preference')")=='keep'
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
        page.goto(staged_backlot_server+'/studio?edit='+pid+'#video')
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
        page.goto(staged_backlot_server+'/studio?edit='+pid+'#video')
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
        page.goto(staged_backlot_server+'/studio?edit='+pid+'#audio')
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
        page.goto(staged_backlot_server+'/studio?edit='+pid+'#video')
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
        page.goto(staged_backlot_server+'/studio?edit='+pid+'#video')
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
        page.goto(staged_backlot_server+'/studio?edit='+pid+'#video')
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
        output.locator('[name=platform]').select_option('youtube');output.locator('[type=submit]').click()
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
        assert state['edit_decisions']['cuts'][1]['transition']['duration_seconds']==.25
        page.locator('#edit-layers-panel summary').click()
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
