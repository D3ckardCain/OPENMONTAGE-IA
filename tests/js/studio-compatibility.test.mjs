import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classify,inspectCompatibility } from '../../backlot/ui/studio-compatibility.js';
const caps={api_protocol:1,backend_build:'a'.repeat(64),version:'3.0',shared_revision:true,commands:['batch'],render_cancel:true};
const data={schema_version:1,api_protocol:1,restart_required:false,resident:{status:'available',sha256:caps.backend_build},ui:{status:'available',sha256:'ui'},editor:caps};
test('matching identity, contract and capabilities accepted; additive fields harmless',()=>{
  assert.equal(classify({...data,future:42},caps,'ui').ok,true);
});
test('resident mismatch needs restart, stale page only reload; no guessed restart on I/O failure',()=>{
  assert.equal(classify({...data,restart_required:true},caps,'ui').kind,'restart');
  assert.equal(classify(data,caps,'old').kind,'reload');
  assert.equal(classify({...data,restart_required:null},caps,'ui').kind,'unknown');
  assert.equal(classify(null,null,'',404).kind,'restart');
  for(const status of [0,403,500])assert.equal(classify(null,null,'',status).kind,'unknown');
});
test('protocol, capabilities and resident identity must agree',()=>{
  for(const changed of [{api_protocol:2},{backend_build:'other'},{commands:[]},{shared_revision:false},{version:'4.0'},{render_cancel:false}])
    assert.equal(classify(data,{...caps,...changed},'ui').kind,'incompatible');
});
test('offline/invalid JSON fail visibly and a later check recovers without writes',async()=>{
  const calls=[];
  const fetcher=async(path,options)=>{calls.push([path,options]);return {status:200,ok:true,json:async()=>path.endsWith('identity')?data:caps};};
  assert.equal((await inspectCompatibility(async()=>{throw Error('offline');},'ui')).kind,'unknown');
  assert.equal((await inspectCompatibility(async()=>({status:200,json:async()=>{throw Error('JSON');}}),'ui')).kind,'unknown');
  assert.equal((await inspectCompatibility(fetcher,'ui')).ok,true);
  assert.equal(calls.length,2);
  assert.ok(calls.every(([,options])=>options.cache==='no-store'&&!options.method));
});
test('bounded timeout aborts transport, does not loop or restart',async()=>{
  let aborted=0;
  const fetcher=(_,options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>{aborted++;reject(Error('abort'));}));
  assert.equal((await inspectCompatibility(fetcher,'ui',10)).kind,'unknown');
  assert.equal(aborted,2);
});
test('legacy identity does not remove advertised ability to cancel an owned render',async()=>{
  const result=await inspectCompatibility(async path=>path.endsWith('identity')?{status:404,ok:false}:{status:200,ok:true,json:async()=>caps},'');
  assert.equal(result.kind,'restart');assert.equal(result.ok,false);assert.equal(result.caps.render_cancel,true);
});
test('actual banner, explicit recheck and recovery use DOM status without automatic restart',async()=>{
  const nodes=new Map(['studio-compatibility','studio-compatibility-message','studio-compatibility-check'].map(id=>[id,{hidden:false,dataset:{},listeners:{},addEventListener(type,fn){this.listeners[type]=fn;}}]));
  const events=[];let old=true;
  globalThis.document={hidden:false,getElementById:id=>nodes.get(id),querySelector:()=>({content:'ui'}),addEventListener(){},dispatchEvent:event=>events.push(event.detail)};
  globalThis.CustomEvent=class{constructor(type,options){this.type=type;this.detail=options.detail;}};
  globalThis.fetch=async path=>path.endsWith('identity')&&old?{status:404,ok:false}:{status:200,ok:true,json:async()=>path.endsWith('identity')?data:caps};
  try{
    const module=await import('../../backlot/ui/studio-compatibility.js?dom-test');
    await module.compatibilityReady;
    assert.equal(nodes.get('studio-compatibility').hidden,false);
    assert.match(nodes.get('studio-compatibility-message').textContent,/manualmente/);
    old=false;await nodes.get('studio-compatibility-check').listeners.click();
    assert.equal(nodes.get('studio-compatibility').hidden,true);
    assert.equal(module.compatibilityState().ok,true);assert.equal(events.length,2);
  }finally{delete globalThis.document;delete globalThis.CustomEvent;delete globalThis.fetch;}
});
