// New #115 UI only: synthetic ASR/EDL report, no media/model or live Studio.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs');
const assert=require('assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXE});
 try{
  const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];let gets=0,posts=0,mode='ok';
  page.on('pageerror',error=>errors.push(error.message));
  const span=(a,b)=>({start_seconds:a,end_seconds:b,start_rational:[a,1],end_rational:[b,1]});
  const report={revision:3,set_id:'set',words:Array.from({length:101},(_,i)=>({clip_id:'clip'+i,word_index:1,
    text:i===1?'<img src=x onerror=alert(1)>':'No',source:span(1,2),timeline:span(.5,1),
    speaker:'speaker0',language:'es',timing_status:'estimated'})),excluded_word_occurrences:1,
    clips:[{clip_id:'clip0',source_inspected:true,coverage_complete_declared:false,
      excluded_words:[{text:'No',word_index:1,reason:'partial_source_word'}]}],warnings:['Solo conversión de reloj, no alineación nueva.']};
  await page.route('**/*',route=>{
   const req=route.request(),url=new URL(req.url());if(req.method()!=='GET'){posts++;return route.abort();}
   if(url.pathname==='/studio')return route.fulfill({contentType:'text/html',body:fs.readFileSync('backlot/ui/studio.html','utf8').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'')});
   if(['/ui/editor-candidates-ui.js','/ui/studio.css','/ui/editor.css'].includes(url.pathname))return route.fulfill({contentType:url.pathname.endsWith('.css')?'text/css':'text/javascript',body:fs.readFileSync('backlot'+url.pathname,'utf8')});
   if(url.pathname.endsWith('/subtitle-words')){
    gets++;assert.equal(url.searchParams.get('set_id'),'set');
    return route.fulfill({status:mode==='error'?400:200,contentType:'application/json',body:JSON.stringify(mode==='error'?{detail:'Fuente cambió'}:{...report,revision:mode==='stale'?4:3})});
   }
   return route.fulfill({status:404,body:'Not a fixture route'});
  });
  await page.goto('http://127.0.0.1:4775/studio');
  await page.evaluate(async()=>{
   const {initializeCandidatesUI}=await import('/ui/editor-candidates-ui.js');
   window.commands=0;window.support=true;
   window.fixture={sources:{s1:{kind:'video',original_name:'Fixture metadata only'}},candidate_sets:[{id:'set',source_id:'s1',words:[{index:0,word:'No',start:1,end:2}],candidates:[],
    coverage:{processed_seconds:3,source_seconds:10,fraction:.3,word_count:1,complete:false,processed_ranges:[[0,3]],unprocessed_ranges:[[3,10]]}}]};
   window.ui=initializeCandidatesUI({q:id=>document.getElementById(id),getEdl:()=>window.fixture,getProject:()=> 'qa',getRevision:()=>3,
    has:name=>name==='clip_candidates'||(name==='subtitle_words'&&window.support),run:()=>{window.commands++;},reviewSource:()=>{},
    inspectWords:async id=>{const r=await fetch('/api/studio/editor/qa/subtitle-words?set_id='+encodeURIComponent(id));const data=await r.json();if(!r.ok)throw Error(data.detail);return data;}});
   window.before=JSON.stringify(window.fixture);window.ui.draw();
  });
  await page.locator('#edit-candidates-panel>summary').click();
  const button=page.getByRole('button',{name:'Inspeccionar palabras en el reloj del montaje'});
  await button.click();await page.waitForFunction(()=>document.querySelector('.editor-word-clock table'));
  assert.equal(await page.locator('.editor-word-clock tr').count(),101); // header + first100, not101 output words
  assert((await page.locator('#edit-candidate-list').textContent()).includes('Se muestran100ocurrencias'));
  assert((await page.locator('#edit-candidate-list').textContent()).includes('palabra cortada por el límite'));
  assert((await page.locator('#edit-candidate-list').textContent()).includes('Cobertura ASR parcial'));
  assert.equal(await page.locator('.editor-word-clock img').count(),0);
  mode='stale';await button.click();await page.waitForFunction(()=>document.querySelector('#edit-candidate-list').textContent.includes('El montaje cambió'));
  assert.equal(await page.locator('.editor-word-clock').count(),0);
  mode='error';await button.click();await page.waitForFunction(()=>document.querySelector('#edit-candidate-list').textContent.includes('Fuente cambió'));
  assert.equal(await page.evaluate(()=>window.commands),0);assert(await page.evaluate(()=>JSON.stringify(window.fixture)===window.before));
  await page.evaluate(()=>{window.support=false;window.ui.reset();window.ui.draw();});
  assert.equal(await page.getByRole('button',{name:'Inspeccionar palabras en el reloj del montaje'}).count(),0);
  assert.equal(gets,3);assert.equal(posts,0);assert.deepEqual(errors,[]);
  console.log(JSON.stringify({scope:'Synthetic #115 report, real UI module, no media/ASR/live4750',
   gets,posts,commands:0,read_only:true,display_limit:100,stale_revision_rejected:true,
   partial_word_warning:true,text_only_rendering:true,old_capability_hidden:true,page_errors:errors}));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
