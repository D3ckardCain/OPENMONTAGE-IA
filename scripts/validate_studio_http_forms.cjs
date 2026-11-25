// E02: real Studio entry module/forms with an entirely synthetic intercepted API.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs');
const assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXE});
 const report={scope:'Real Studio JS/HTML, synthetic API only; no active4750, models or settings writes',cases:[],unexpected:[]};
 try{
  const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  // Only this fixture accelerates the explicit 30s local-form/read deadline.
  await page.addInitScript(()=>{const native=setTimeout;window.setTimeout=(fn,ms,...args)=>native(fn,ms===30000?(window.fixtureSlowDeadline?1000:80):ms,...args);});
  const settings={ollama_url:'http://127.0.0.1:11434',comfyui_url:'http://127.0.0.1:8188',model:'fixture-local',resource_roots:['D:\\Rutas con espacios\\áéíóúñ','C:\\Otra carpeta'],ffmpeg_path:'',ffprobe_path:'',yt_dlp_path:'',deno_path:''};
  const bootstrap={settings,pipelines:[{name:'framework-smoke',stages:[]}],projects:[]};
  let mode={kind:'http',status:400},posts=0,failBootstrap=false,releaseHeld;
  const allowed=new Set(['studio.js','studio-http.js','studio-production-forms.js','studio-form-request.js','studio.css','editor.css']);
  await page.route('**/*',async route=>{
   const request=route.request(),url=new URL(request.url());
   if(url.origin!=='http://127.0.0.1:4776'){report.unexpected.push(url.href);return route.abort();}
   if(url.pathname==='/studio'){
    const html=fs.readFileSync('backlot/ui/studio.html','utf8').replace(/<script\b[^>]*src="\/ui\/editor\.js"[^>]*><\/script>/,'');
    return route.fulfill({contentType:'text/html',body:html});
   }
   if(url.pathname.startsWith('/ui/')&&allowed.has(url.pathname.slice(4))){
    const path='backlot/ui/'+url.pathname.slice(4);return route.fulfill({contentType:path.endsWith('.css')?'text/css':'text/javascript',body:fs.readFileSync(path,'utf8')});
   }
   if(url.pathname==='/api/studio/bootstrap')return route.fulfill({status:failBootstrap?500:200,contentType:'application/json',body:JSON.stringify(failBootstrap?{detail:'Fixture refresh failed'}:bootstrap)});
   if(url.pathname==='/api/studio/football/desk-editions')return route.fulfill({contentType:'application/json',body:'{"editions":[]}'});
   if(request.method()==='POST'&&['/api/studio/projects','/api/studio/settings'].includes(url.pathname)){
    posts++;const current={...mode};
    if(url.pathname==='/api/studio/settings')assert.deepEqual(request.postDataJSON().resource_roots,['D:\\Ruta larga con acentos\\áéíóúñ','C:\\Otra carpeta']);
    if(current.kind==='network')return route.abort('internetdisconnected');
    if(current.kind==='held')await new Promise(resolve=>{releaseHeld=resolve;});
    await new Promise(resolve=>setTimeout(resolve,current.kind==='timeout'?180:current.delay||15));
    let status=current.status||200,body;
    if(current.kind==='html')body='<html>Do not display raw traceback</html>';
    else if(current.kind==='invalid')body='';
    else if(current.kind==='ack-refresh-fails'){status=200;failBootstrap=true;body=JSON.stringify({project_id:'fixture-created-once'});}
    else body=JSON.stringify(current.kind==='success'?{ok:true}:{detail:current.detail||'Fixture error '+status});
    try{return await route.fulfill({status,contentType:current.kind==='html'?'text/html':'application/json',body});}
    catch{/* A deliberately timed-out synthetic request may already be closed. */return;}
   }
   if(url.pathname==='/favicon.ico')return route.fulfill({status:204});
   report.unexpected.push(url.pathname);return route.abort();
  });
  await page.goto('http://127.0.0.1:4776/studio#production');
  await page.waitForFunction(()=>document.querySelector('#create').pipeline.options.length>0);
  assert.equal(await page.locator('#settings [name=roots]').inputValue(),settings.resource_roots.join('\n'),'Bootstrap must preserve separate paths as actual lines');
  const scenarios=[{kind:'http',status:400},{kind:'http',status:403},{kind:'http',status:422,detail:[{loc:['body','title'],msg:'Campo obligatorio'}]},
   {kind:'http',status:500},{kind:'html',status:500},{kind:'invalid',status:200},{kind:'network'},{kind:'timeout'}];
  for(const formName of ['create','settings'])for(const scenario of scenarios){
   mode=scenario;failBootstrap=false;
   await page.locator('.editor-menu [data-section="'+(formName==='create'?'production':'models')+'"]').click();
   const form=page.locator('#'+formName);
   await form.evaluate(n=>{for(let p=n.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;});
   const field=form.locator(formName==='create'?'[name=brief]':'[name=roots]');
   const value=formName==='create'?'No pierdas la negación: ¿Qué cambió? 🧪':'D:\\Ruta larga con acentos\\áéíóúñ\nC:\\Otra carpeta';
   if(formName==='create')await form.locator('[name=title]').fill('Proyecto sintético sin ejecución');
   await field.fill(value);await field.focus();
   const before=posts;
   const pending=await form.evaluate(n=>{n.requestSubmit();n.requestSubmit();return{busy:n.getAttribute('aria-busy'),disabled:[...n.querySelectorAll('button')].every(b=>b.disabled)};});
   assert.equal(pending.busy,'true');assert(pending.disabled);
   await page.waitForFunction(id=>!document.getElementById(id).hasAttribute('aria-busy'),formName);
   assert.equal(posts-before,1,'Double submit or automatic retry');assert.equal(await field.inputValue(),value);
   assert(await field.evaluate(n=>n===document.activeElement),'Focus lost after local error');
   assert(await form.locator('button').isEnabled());assert(await page.locator('.editor-menu [data-section=library]').isEnabled());
   const notice=await page.locator('#notice').textContent();
   assert(!notice.includes('Unexpected token')&&!notice.includes('traceback')&&!notice.includes('[object Object]'),notice);
   if(scenario.status>=400)assert(notice.includes('HTTP '+scenario.status),notice);
   else if(scenario.kind==='timeout')assert(notice.includes('espera del navegador'),notice);
   else if(scenario.kind==='network')assert(notice.includes('conexión'),notice);
   else assert(notice.includes('JSON'),notice);
   if(['timeout','network'].includes(scenario.kind)||scenario.status>=500||scenario.kind==='invalid')assert(notice.includes('Consulta su estado antes de repetir'),notice);
   report.cases.push({form:formName,...scenario,posts:posts-before,input_preserved:true,focus_preserved:true,workspace_enabled:true,notice});
  }
  mode={kind:'http',status:400};
  await page.locator('.editor-menu [data-section=production]').click();
  await page.locator('#create button').click();await page.waitForFunction(()=>!document.querySelector('#create').hasAttribute('aria-busy'));
  assert(await page.locator('#create button').evaluate(n=>n===document.activeElement));report.submit_button_focus_restored=true;
  await page.evaluate(async()=>{
    const {runFormRequest}=await import('/ui/studio-form-request.js');
    const form=document.querySelector('#create'),button=form.querySelector('button');button.disabled=true;
    await runFormRequest(form,async()=>{throw Error('Synthetic local callback');},()=>{});
    if(!button.disabled)throw Error('Originally disabled control was enabled');button.disabled=false;
  });report.original_disabled_state_preserved=true;
  mode={kind:'held',status:403};await page.evaluate(()=>window.fixtureSlowDeadline=true);
  await page.locator('#create').evaluate(n=>n.requestSubmit());
  await page.locator('.editor-menu [data-section=library]').click();
  assert.equal(await page.locator('#create').getAttribute('aria-busy'),'true');assert(releaseHeld);releaseHeld();
  await page.waitForFunction(()=>!document.querySelector('#create').hasAttribute('aria-busy'));
  assert(await page.locator('.editor-menu [data-section=library]').evaluate(n=>n===document.activeElement));
  report.user_navigation_focus_not_stolen=true;await page.evaluate(()=>window.fixtureSlowDeadline=false);
  mode={kind:'http',status:400,detail:'Ruta de prueba no disponible: D:\\'+('directorio'.repeat(65))+'\\modelo.onnx'};
  await page.locator('.editor-menu [data-section=production]').click();
  await page.locator('#create').evaluate(n=>n.requestSubmit());await page.waitForFunction(()=>!document.querySelector('#create').hasAttribute('aria-busy'));
  const geometry=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
  assert(geometry.scrollWidth<=geometry.width+1,'Long error overflow '+JSON.stringify(geometry));report.long_error_wrapped=geometry;
  mode={kind:'ack-refresh-fails'};failBootstrap=false;
  await page.locator('.editor-menu [data-section=production]').click();
  const create=page.locator('#create'),before=posts;await create.evaluate(n=>n.requestSubmit());
  await page.waitForFunction(()=>!document.querySelector('#create').hasAttribute('aria-busy'));
  const notice=await page.locator('#notice').textContent();
  assert.equal(posts-before,1);assert(notice.includes('Proyecto creado (fixture-created-once)')&&notice.includes('No repitas la creación'),notice);
  report.acknowledged_creation={posts:posts-before,refresh_failed:true,notice};
  failBootstrap=false;mode={kind:'success'};
  await page.locator('.editor-menu [data-section=models]').click();
  const form=page.locator('#settings');await form.evaluate(n=>n.requestSubmit());
  await page.waitForFunction(()=>!document.querySelector('#settings').hasAttribute('aria-busy'));
  assert.equal(await page.locator('#notice').textContent(),'Configuración guardada.');report.recovery_after_local_errors=true;
  assert.deepEqual(report.unexpected,[]);assert.deepEqual(errors,[]);report.page_errors=errors;
  fs.writeFileSync('.runtime/qa/studio-http-forms.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
