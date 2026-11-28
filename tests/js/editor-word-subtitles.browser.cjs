// Isolated real Chromium DOM, synthetic candidates; no network or Studio writes.
const {chromium}=require('playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({headless:true,...(process.env.QA_CHROME?{executablePath:process.env.QA_CHROME}:{})});
  try{
    const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',r=>r.abort());
    const source=fs.readFileSync('backlot/ui/editor-word-subtitles.js','utf8').replace('export function','function');
    await page.setContent('<main id="host"></main>');
    await page.addScriptTag({content:source+`;window.appendSubtitleDraft=appendSubtitleDraft;`});
    async function setup(options={}){
      await page.evaluate(options=>{
        window.pid='test';window.revision=4;window.loads=0;window.calls=[];
        const draft={revision:4,ready:!options.blocked,blockers:options.blocked?['Revisa palabras cortadas']:[],warnings:['Sin ASR nuevo'],input_edl_sha256:'a',word_data_sha256:'b',cues:options.blocked?[]:[{start_seconds:0,end_seconds:1,text:'No retires protección. 🙂'}]};
        const host=document.getElementById('host');host.replaceChildren();
        appendSubtitleDraft({parent:host,dataset:{id:'set'},getProject:()=>pid,getRevision:()=>revision,
          loadDraft:async()=>{loads++;if(options.loadError)throw Error('Lectura fallida');return draft;},
          run:async(op,params)=>{calls.push({op,params});if(options.sendError)throw Error('Respuesta perdida; revisa estado, no repetir automáticamente');revision++;}});
      },options);
    }
    const prepare=()=>page.getByRole('button',{name:'Preparar borrador',exact:false}).click();
    const apply=()=>page.getByRole('button',{name:'Aplicar borrador revisado',exact:true});
    await setup();await prepare();assert(await apply().isDisabled());
    assert(await page.getByText('0.000–1.000 s · No retires protección. 🙂',{exact:true}).isVisible());
    await page.getByLabel('Revisé texto', {exact:false}).check();
    await page.getByLabel('Autorizo reemplazar',{exact:false}).check();await apply().click();
    let state=await page.evaluate(()=>({calls,loads}));assert.equal(state.loads,1);assert.equal(state.calls.length,1);
    assert.equal(state.calls[0].op,'subtitle_from_words');assert.deepEqual(state.calls[0].params,{set_id:'set',input_edl_sha256:'a',word_data_sha256:'b',reviewed:true,replace_existing:true});
    assert(await page.getByText('Borrador aplicado al proyecto compartido.',{exact:false}).isVisible());
    await setup({blocked:true});await prepare();assert.equal(await apply().count(),0);assert.equal(await page.evaluate(()=>calls.length),0);
    await setup();await prepare();await page.getByLabel('Revisé texto',{exact:false}).check();await page.evaluate(()=>revision++);await apply().click();assert.equal(await page.evaluate(()=>calls.length),0);assert(await page.getByText('Cambió el proyecto; prepara de nuevo el borrador.',{exact:true}).isVisible());
    await setup({sendError:true});await prepare();await page.getByLabel('Revisé texto',{exact:false}).check();await apply().click();assert.equal(await page.evaluate(()=>calls.length),1);assert(await page.getByText('Respuesta perdida;', {exact:false}).isVisible());
    await setup({loadError:true});await prepare();assert(await page.getByText('Lectura fallida',{exact:true}).isVisible());assert.equal(await apply().count(),0);
    await setup();await prepare();await page.getByLabel('Revisé texto',{exact:false}).check();await page.evaluate(()=>pid='other');await apply().click();assert.equal(await page.evaluate(()=>calls.length),0);
    assert.deepEqual(errors,[]);console.log(JSON.stringify({passed:6,scope:'Isolated real Chromium controls, synthetic responses, no Studio or media calls',page_errors:errors}));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
