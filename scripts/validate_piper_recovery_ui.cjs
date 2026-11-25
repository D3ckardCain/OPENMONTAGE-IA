// New E05 UI regression only: synthetic backend and WAV, never a speech model.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs');
const assert=require('assert/strict');
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROME_EXE,headless:true});
  try{
    const page=await browser.newPage();
    const records=new Map();let posts=0,providers=0,failResponse=true;
    const speakers=Object.fromEntries(Array.from({length:109},(_,i)=>['speaker'+i,i]));
    const voices=[{id:'test-voice',available:true,blocked:false,preview_contract:1,speakers,attribution:'Synthetic fixture, no real voice'}];
    const wav=Buffer.alloc(204);wav.write('RIFF',0);wav.writeUInt32LE(196,4);wav.write('WAVEfmt ',8);wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(1,22);wav.writeUInt32LE(8000,24);wav.writeUInt32LE(16000,28);wav.writeUInt16LE(2,32);wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(160,40);
    await page.route('**/*',async route=>{
      const req=route.request(),url=new URL(req.url());
      const reply=d=>route.fulfill({contentType:'application/json',body:JSON.stringify(d)});
      if(url.pathname==='/test')return route.fulfill({contentType:'text/html',body:'<select id="edit-project"></select><main></main>'});
      if(url.pathname.endsWith('/piper/voices'))return reply(voices);
      if(url.pathname.endsWith('/piper/preview')){
        posts++;const data=req.postDataJSON();let record=records.get(data.request_id);
        if(!record){providers++;record={state:'completed',request_id:data.request_id,inputs:{voice:data.voice,speaker_id:data.speaker_id,text:data.text},result:{request_id:data.request_id,seconds:.01,relative_path:'assets/audio/piper-'+data.request_id+'.wav'}};records.set(data.request_id,record);}
        if(failResponse){failResponse=false;return route.abort('connectionreset');}
        return reply({...record.result,reused:true});
      }
      if(url.pathname.includes('/piper/requests/'))return reply(records.get(url.pathname.split('/').pop()));
      if(url.pathname.includes('/piper/audio/'))return route.fulfill({contentType:'audio/wav',body:wav});
      return route.fulfill({status:404,body:'Not a fixture route'});
    });
    const source=fs.readFileSync('backlot/ui/editor-piper-ui.js','utf8').replace('export function initializePiperUI','window.initializePiperUI=function');
    async function initialize(){
      await page.goto('http://127.0.0.1:4779/test');await page.addScriptTag({content:source});
      await page.evaluate(()=>window.initializePiperUI({host:document.querySelector('main'),getProject:()=> 'qa',getRevision:()=>0,reopen:async()=>{}}));
      await page.locator('summary').click();await page.locator('[data-load]').click();
      await page.waitForFunction(()=>document.querySelector('[data-speaker]').options.length===109);
    }
    await initialize();await page.locator('[data-speaker]').selectOption('54');
    await page.locator('[data-preview]').click();
    await page.waitForFunction(()=>document.querySelector('[data-status]').textContent.includes('no se reintenta automáticamente'));
    assert.equal(providers,1);assert.equal(posts,1);
    await page.locator('[data-recover]').click();await page.waitForFunction(()=>document.querySelector('[data-status]').textContent.includes('recuperado sin repetir'));
    assert.equal(providers,1);assert.equal(posts,1);assert.equal(await page.locator('[data-speaker]').inputValue(),'54');
    await page.locator('[data-speaker]').selectOption('55');
    assert.equal(await page.locator('audio').getAttribute('src'),null);assert(await page.locator('[data-import]').isDisabled());
    await page.locator('[data-recover]').click();await page.waitForFunction(()=>document.querySelector('[data-speaker]').value==='54');
    await page.locator('[data-preview]').click();await page.waitForFunction(()=>document.querySelector('[data-status]').textContent.includes('recuperado sin repetir'));
    assert.equal(providers,1);assert.equal(posts,2);assert.equal(records.size,1);
    await initialize();await page.locator('[data-recover]').click();await page.waitForFunction(()=>document.querySelector('[data-speaker]').value==='54');
    assert.equal(providers,1);assert.equal(posts,2);
    await page.locator('[data-new]').click();assert.equal(providers,1);assert.equal(await page.locator('audio').getAttribute('src'),null);
    console.log(JSON.stringify({scope:'Synthetic E05 UI only; no real synthesis',lost_response_recovered:true,
      same_id_reused:true,reload_recovered:true,stale_audio_cleared:true,new_take_requires_explicit_action:true,providers,posts,receipts:records.size}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
