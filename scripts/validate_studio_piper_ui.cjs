// Opt-in: four Spanish WAVs, or one VCTK WAV with --vctk, in an existing QA project.
// Uses existing local runtime and models; never downloads or installs anything.
// PLAYWRIGHT_MODULE and CHROME_EXE must name existing local installations.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs');
const base=process.argv[2],pid=process.argv[3];
const vctkOnly=process.argv.includes('--vctk');
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(base||'')||!/^edit-[a-z0-9-]+$/.test(pid||''))
  throw Error('Usage: node script.cjs http://127.0.0.1:PORT edit-QA-ID');
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROME_EXE,headless:true,
    args:['--autoplay-policy=no-user-gesture-required']});
  try{
    const page=await browser.newPage({viewport:{width:1920,height:1080}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(`${base}/studio?edit=${encodeURIComponent(pid)}#audio`);
    const panel=page.locator('details').filter({has:page.locator('[data-load]')});
    await panel.locator('summary').click();await panel.locator('[data-load]').click();
    await page.waitForFunction(()=>document.querySelector('[data-voice]').options.length===4);
    const results=[];
    const samples=vctkOnly?[['en_GB-vctk-medium','54']]:[['es_ES-davefx-medium','0'],
      ['es_ES-carlfm-x_low','0'],['es_ES-sharvard-medium','0'],['es_ES-sharvard-medium','1']];
    if(vctkOnly)await panel.locator('[data-text]').fill('This is a short local voice test.');
    for(const [voice,speaker] of samples){
      await panel.locator('[data-voice]').selectOption(voice);
      await panel.locator('[data-speaker]').selectOption(speaker);
      const response=page.waitForResponse(r=>r.url().includes('/piper/preview')&&r.request().method()==='POST');
      await panel.locator('[data-preview]').click();const r=await response;const receipt=await r.json();
      if(!r.ok())throw Error(JSON.stringify(receipt));
      const audio=panel.locator('audio');await audio.evaluate(a=>a.play());
      await page.waitForFunction(()=>{const a=document.querySelector('details audio');return a&&a.ended;},null,{timeout:15000});
      const playback=await audio.evaluate(a=>({duration:a.duration,currentTime:a.currentTime,
        ended:a.ended,readyState:a.readyState,error:a.error?.message||null}));
      results.push({voice,speaker:Number(speaker),seconds:receipt.seconds,
        sample_rate:receipt.sample_rate,relative_path:receipt.relative_path,playback,
        attribution:await panel.locator('[data-license]').textContent()});
    }
    await page.screenshot({path:vctkOnly?'.runtime/piper/panel-vctk-retrained.png':'.runtime/piper/panel-spanish.png'});
    if(!vctkOnly)await panel.locator('[data-voice]').selectOption('en_GB-vctk-medium');
    const vctk={speaker_count:await panel.locator('[data-speaker] option').count(),
      disabled:await panel.locator('[data-preview]').isDisabled(),
      status:await panel.locator('[data-status]').textContent()};
    if(vctk.speaker_count!==109||(vctkOnly&&vctk.disabled))throw Error('VCTK retrain activation failed');
    if(errors.length)throw Error(JSON.stringify(errors));
    await page.screenshot({path:vctkOnly?'.runtime/piper/panel-vctk-retrained.png':'.runtime/piper/panel-vctk.png'});
    const report={scope:`real Studio ${base}; installed headless Chrome; not human listening`,
      project_id:pid,results,vctk,errors};
    fs.writeFileSync(vctkOnly?'.runtime/piper/browser-vctk-results.json':'.runtime/piper/browser-results.json',JSON.stringify(report,null,2));
    console.log(JSON.stringify(report));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
