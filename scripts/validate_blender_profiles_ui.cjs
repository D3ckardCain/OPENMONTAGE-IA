// Live isolated Studio only: real selection API, no Blender launch or render.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('assert/strict'),fs=require('fs');
(async()=>{
 const base=process.env.BLENDER_PROFILE_STUDIO_URL||'http://127.0.0.1:4778';
 const endpoint=new URL(base);assert.equal(endpoint.hostname,'127.0.0.1');assert.notEqual(endpoint.port,'4750','Use an isolated copy, never active4750');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXE});
 const report={scope:'Isolated server, real profile selection API; no4750 mutation or application launch',posts:[],blocked:[],errors:[]};
 try{
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  page.on('pageerror',e=>report.errors.push(e.message));
  await page.route('**/*',route=>{
   const r=route.request(),url=new URL(r.url());
   if(url.origin!==base)return route.abort();
   if(!['GET','HEAD'].includes(r.method())){
    if(url.pathname==='/api/studio/applications/blender/profile'&&r.method()==='POST')report.posts.push(r.postDataJSON());
    else {report.blocked.push(url.pathname);return route.abort();}
   }
   return route.continue();
  });
  await page.goto(base+'/studio#applications');
  await page.waitForFunction(()=>typeof document.querySelector('#applications-load')?.onclick==='function');
  await page.locator('#applications-load').click();
  const detail=page.locator('#applications-result>details').filter({has:page.locator('[data-blender-profile]')});
  await detail.locator('summary').click();
  assert.equal(await detail.locator('[data-blender-profile]').inputValue(),'blender-4.5');
  assert.equal(await detail.locator('[data-blender-profile] option').count(),3);
  report.compatibility=await page.evaluate(async()=>{const m=await import('/ui/studio-compatibility.js');return m.compatibilityState();});
  assert(report.compatibility.ok);
  for(const id of ['blender-5.3','blender-4.5']){
   await detail.locator('[data-blender-profile]').selectOption(id);
   const response=page.waitForResponse(r=>r.url().endsWith('/applications/blender/profile')&&r.request().method()==='POST');
   await detail.locator('[data-blender-profile-save]').click();
   const data=await(await response).json();assert.equal(data.profile_id,id);assert(data.saved);
   await page.waitForFunction(id=>document.querySelector('#applications-result [data-blender-profile]')?.value===id,id);
   await detail.locator('summary').click();
   assert.equal(await detail.locator('[data-blender-profile]').inputValue(),id);
   report[id]=await detail.innerText();
  }
  assert.equal(report.posts.length,2);assert.deepEqual(report.blocked,[]);assert.deepEqual(report.errors,[]);
  await page.screenshot({path:'.runtime/qa/blender117-profiles-ui.png'});
  report.success=true;
 }finally{fs.writeFileSync('.runtime/qa/blender117-profiles-ui.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));}
})().catch(e=>{console.error(e);process.exitCode=1;});
