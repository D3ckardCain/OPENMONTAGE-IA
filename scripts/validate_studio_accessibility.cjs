// E02 contract: real Studio markup/CSS in an offline fixture, no application JS.
// Requires existing Playwright + browser. Never connects to Studio or installs tools.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs');
const assert=require('assert/strict');

function rgb(value){
  const numbers=value.match(/[\d.]+/g)?.map(Number);
  if(!/^rgba?\(/.test(value)||!numbers||numbers.length<3||(numbers[3]!==undefined&&numbers[3]!==1))throw Error('Unsupported/transparent contrast pair: '+value);
  return numbers.slice(0,3);
}
function luminance(color){
  const linear=color.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});
  return linear[0]*.2126+linear[1]*.7152+linear[2]*.0722;
}
function contrast(a,b){const x=luminance(rgb(a)),y=luminance(rgb(b));return(Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
function pass(pair){return contrast(pair.color,pair.background)>=4.5;}

(async()=>{
  assert.equal(contrast('rgb(0, 0, 0)','rgb(255, 255, 255)'),21);
  assert.equal(contrast('rgb(20, 20, 20)','rgb(20, 20, 20)'),1);
  const baseline={color:'rgb(230, 237, 243)',background:'rgb(35, 134, 54)'};
  assert(!pass(baseline),'Original primary pair must be a negative fixture');
  const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXE});
  const report={scope:'Offline real-markup/CSS fixture in installed browser; not active4750, screen reader or WCAG certification',
    browser:browser.version(),platform:process.platform,node:process.version,
    original_pair:baseline,original_ratio:contrast(baseline.color,baseline.background),viewports:[],requests:[]};
  try{
    const page=await browser.newPage();
    page.on('request',request=>report.requests.push(request.url()));
    await page.route('**/*',route=>route.abort());
    const html=fs.readFileSync('backlot/ui/studio.html','utf8').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'').replace(/<link\b[^>]*>/gi,'');
    const css=fs.readFileSync('backlot/ui/studio.css','utf8')+'\n'+fs.readFileSync('backlot/ui/editor.css','utf8');
    for(const width of [320,390,768,1280]){
      await page.setViewportSize({width,height:900});await page.setContent(html);await page.addStyleTag({content:css});
      const declared=await page.locator('button[type=submit],#create button').evaluateAll(nodes=>nodes.filter(n=>!n.disabled).map(n=>{
        const s=getComputedStyle(n);return {text:n.textContent.trim(),color:s.color,background:s.backgroundColor};
      }));
      assert(declared.length>0&&declared.every(pass),'Declared primary pair regression');
      assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).backgroundColor),'rgb(13, 17, 23)');
      await page.evaluate(()=>{
        const header=document.querySelector('header').cloneNode(true);
        const creation=document.querySelector('#creation').cloneNode(true);
        const actions=[...document.querySelectorAll('[data-action]')].map(b=>{b=b.cloneNode(true);b.hidden=false;return b;});
        const main=document.createElement('main');main.id='legacy-studio';
        const aside=document.createElement('aside');aside.textContent='Fixture offline · sin acciones de producción';
        const section=document.createElement('section');section.append(creation);
        const row=document.createElement('div');row.className='row';row.append(...actions);section.append(row);
        const resource=document.createElement('p');resource.className='resource';resource.textContent='Ruta aportada: D:\\OPENMONTAJE-IA\\Modelos\\'+'carpeta-muy-larga-áéíóúñ'.repeat(15)+'\\recurso.onnx';section.append(resource);
        main.append(aside,section);document.body.replaceChildren(header,main);
        const form=document.querySelector('#create');form.pipeline.add(new Option('Pipeline de prueba sin ejecución','fixture'));
        form.title.value='Proyecto de prueba con acentos: ¿Qué cambió?';
        form.brief.value='Texto sintético preservado. No generar voz ni vídeo.';
        window.fixtureEvents={submits:0,actions:[]};
        form.addEventListener('submit',event=>{event.preventDefault();window.fixtureEvents.submits++;});
        for(const button of actions)button.addEventListener('click',()=>window.fixtureEvents.actions.push(button.dataset.action));
      });
      const button=page.locator('#create button');
      const colors=()=>button.evaluate(n=>{const s=getComputedStyle(n);return{color:s.color,background:s.backgroundColor,fontSize:s.fontSize};});
      const normal=await colors();assert(pass(normal),JSON.stringify({width,normal}));
      assert.equal(normal.background,baseline.background,'GitHub Dark green must remain unchanged');
      await button.hover();const hover=await colors();assert(pass(hover));
      await page.mouse.down();const pressed=await colors();assert(pass(pressed));await page.mouse.up();
      await button.evaluate(n=>n.disabled=true);assert(await button.isDisabled());await button.evaluate(n=>n.disabled=false);
      const controls=await page.locator('#create').evaluate(form=>[...form.elements].map(n=>n.tagName==='BUTTON'?'#create button':`#create [name="${n.name}"]`));
      const focusPairs=[];
      await page.locator(controls[0]).focus();
      for(let i=0;i<controls.length;i++){
        const selected=page.locator(controls[i]);
        assert(await selected.evaluate(n=>n===document.activeElement&&n.matches(':focus-visible')),'Keyboard focus '+controls[i]);
        const focus=await selected.evaluate(n=>{const s=getComputedStyle(n);let background='rgb(13, 17, 23)';
          for(let parent=n.parentElement;parent;parent=parent.parentElement){const color=getComputedStyle(parent).backgroundColor;if(color!=='rgba(0, 0, 0, 0)'){background=color;break;}}
          return{width:parseFloat(s.outlineWidth),style:s.outlineStyle,color:s.outlineColor,background};});
        assert(focus.width>=2&&focus.style==='solid','Visible focus contract '+JSON.stringify(focus));
        assert(contrast(focus.color,focus.background)>=3,'Focus contrast '+JSON.stringify(focus));focusPairs.push(focus);
        if(i<controls.length-1)await page.keyboard.press('Tab');
      }
      await page.keyboard.press('Shift+Tab');assert(await page.locator(controls.at(-2)).evaluate(n=>n===document.activeElement));
      await page.keyboard.press('Tab');await page.keyboard.press('Enter');
      assert.equal(await page.evaluate(()=>window.fixtureEvents.submits),2); // pointer and Enter, fixture handlers only
      for(const action of ['start','stop','approve']){
        const target=page.locator(`[data-action="${action}"]`);await page.keyboard.press('Tab');
        assert(await target.evaluate(n=>n===document.activeElement&&n.matches(':focus-visible')),'Action order '+action);
        await page.keyboard.press('Space');await page.keyboard.press('Enter');
      }
      assert.deepEqual(await page.evaluate(()=>window.fixtureEvents.actions),['start','start','stop','stop','approve','approve']);
      assert.equal(await page.locator('#create [name=brief]').inputValue(),'Texto sintético preservado. No generar voz ni vídeo.');
      assert.equal(await page.locator('#create [name=title]').inputValue(),'Proyecto de prueba con acentos: ¿Qué cambió?');
      const geometry=await page.evaluate(()=>({scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,
        controls:[...document.querySelectorAll('#create input,#create textarea,#create select,#create button,[data-action]')].map(n=>{const r=n.getBoundingClientRect();return{left:r.left,right:r.right,width:r.width};})}));
      assert(geometry.scrollWidth<=width+1,JSON.stringify({width,geometry}));
      assert(geometry.controls.every(r=>r.left>=-1&&r.right<=width+1),'Controls clipped '+width);
      await page.evaluate(()=>document.documentElement.style.setProperty('--studio-primary-foreground','#e6edf3'));
      assert(!pass(await colors()),'Token mutation must expose original contrast regression');
      await page.evaluate(()=>document.documentElement.style.removeProperty('--studio-primary-foreground'));
      assert(pass(await colors()));
      report.viewports.push({width,normal,contrast:contrast(normal.color,normal.background),hover:pass(hover),pressed:pass(pressed),
        declared_primary_styles_checked:declared.length,declared_scope:'computed colors only; includes hidden controls, not full-panel interaction',
        inactive_state:'native disabled; excluded from contrast criterion',keyboard_controls:controls.length,focusPairs,tab_reverse:true,enter_space:true,geometry});
      if(width===320||width===1280)await page.screenshot({path:'.runtime/qa/studio-e02-'+width+'.png',fullPage:true});
    }
    await page.evaluate(()=>document.documentElement.style.zoom='2');
    const zoom=await page.evaluate(()=>({scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth}));
    assert(zoom.scrollWidth<=zoom.viewport+1,JSON.stringify(zoom));report.zoom={mode:'CSS zoom2 emulation; not OS/browser zoom',...zoom};
    await page.emulateMedia({forcedColors:'active'});
    await page.locator('#create button').focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');
    report.forced_colors=await page.locator('#create button').evaluate(n=>{const s=getComputedStyle(n);return {
      mode:'browser emulation, not physical Windows high-contrast testing',visible:n.matches(':focus-visible'),outline:s.outline,width:parseFloat(s.outlineWidth)};});
    assert(report.forced_colors.visible&&report.forced_colors.width>=2);
    assert.deepEqual(report.requests,[],'Fixture must not access API/network');
    const output=process.env.REPORT_PATH||'.runtime/qa/studio-accessibility.json';fs.writeFileSync(output,JSON.stringify(report,null,2));
    console.log(JSON.stringify(report));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
