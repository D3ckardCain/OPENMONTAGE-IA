import {test} from 'node:test';
import assert from 'node:assert/strict';
import {requestJSON,StudioHTTPError} from '../../backlot/ui/studio-http.js';

const json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json'}});
const reject=async(fn,check)=>assert.rejects(fn,error=>{assert(error instanceof StudioHTTPError);check(error);return true;});

test('successful JSON preserves data and one POST only',async()=>{
  let calls=0;
  const input={title:'¿Qué cambió?',path:'D:\\Datos\\ruta larga'};
  const result=await requestJSON('/api/studio/settings',input,{fetcher:async(path,options)=>{
    calls++;assert.equal(options.method,'POST');assert.deepEqual(JSON.parse(options.body),input);return json({ok:true});
  }});
  assert.deepEqual(result,{ok:true});assert.equal(calls,1);assert.equal(input.title,'¿Qué cambió?');
});
for(const status of [400,401,403,404,409,422,500,503])test('HTTP '+status+' keeps status and never retries',async()=>{
  let calls=0;
  await reject(()=>requestJSON('/api/studio/projects',{title:'Preserved'},{fetcher:async()=>{calls++;return json({detail:'Motivo explícito'},status);}}),error=>{
    assert.equal(error.status,status);assert.match(error.message,new RegExp('HTTP '+status));assert.match(error.message,/Motivo explícito/);
    assert.equal(error.uncertain,status>=500);
  });
  assert.equal(calls,1);
});
test('structured validation fields are readable without object coercion',async()=>{
  await reject(()=>requestJSON('/api/studio/projects',{}, {fetcher:async()=>json({detail:[{loc:['body','title'],msg:'Campo requerido'}]},422)}),error=>{
    assert.match(error.message,/title: Campo requerido/);assert(!error.message.includes('[object Object]'));
  });
});
test('HTML server error remains HTTP500 without exposing body as application markup',async()=>{
  await reject(()=>requestJSON('/api/studio/projects',{}, {fetcher:async()=>new Response('<html>private server traceback</html>',{status:500})}),error=>{
    assert.equal(error.code,'server');assert.equal(error.status,500);assert(!error.message.includes('traceback'));assert(error.uncertain);
  });
});
test('empty error body keeps HTTP403 classification',async()=>{
  await reject(()=>requestJSON('/api/studio/settings',{}, {fetcher:async()=>new Response('',{status:403})}),error=>{
    assert.equal(error.code,'forbidden');assert.equal(error.uncertain,false);
  });
});
for(const raw of ['','<html>not JSON</html>'])test('invalid success response is explicit: '+JSON.stringify(raw),async()=>{
  await reject(()=>requestJSON('/api/studio/projects',{}, {fetcher:async()=>new Response(raw)}),error=>{
    assert.equal(error.code,'invalid_response');assert(error.uncertain);
  });
});
test('204 is an explicit empty success',async()=>{
  assert.equal(await requestJSON('/api/studio/settings',{}, {fetcher:async()=>new Response(null,{status:204})}),null);
});
for(const data of [undefined,{}])test('network failure does not invent restart or completion: '+(data?'POST':'GET'),async()=>{
  let calls=0;
  await reject(()=>requestJSON('/api/studio/projects',data,{fetcher:async()=>{calls++;throw new TypeError('fetch failed');}}),error=>{
    assert.equal(error.code,'network');assert.equal(error.uncertain,data!==undefined);
    assert(!error.message.includes('reinicia automáticamente'));
  });assert.equal(calls,1);
});
test('deadline stops the wait even if the test transport ignores AbortSignal',async()=>{
  let calls=0,signal;
  await reject(()=>requestJSON('/api/studio/projects',{}, {timeoutMs:10,fetcher:async(path,options)=>{calls++;signal=options.signal;return new Promise(()=>{});}}),error=>{
    assert.equal(error.code,'timeout');assert(error.uncertain);assert.match(error.message,/cerrar HTTP no detiene/);
  });assert.equal(calls,1);assert(signal.aborted);
});
test('deadline includes response body reading, not just headers',async()=>{
  await reject(()=>requestJSON('/api/studio/bootstrap',undefined,{timeoutMs:10,fetcher:async()=>({status:200,ok:true,text:()=>new Promise(()=>{})})}),error=>{
    assert.equal(error.code,'timeout');assert.equal(error.status,200);assert.equal(error.uncertain,false);
  });
});
test('already cancelled request is never sent',async()=>{
  const controller=new AbortController();controller.abort();let calls=0;
  await reject(()=>requestJSON('/api/studio/projects',{}, {signal:controller.signal,fetcher:async()=>{calls++;return json({});}}),error=>{
    assert.equal(error.code,'cancelled');assert.equal(error.uncertain,false);
  });assert.equal(calls,0);
});
test('external cancellation after send is uncertain, not compute-stopped',async()=>{
  const controller=new AbortController();let release;
  const sent=new Promise(resolve=>{release=resolve;});
  const pending=requestJSON('/api/studio/projects',{}, {signal:controller.signal,fetcher:async()=>{release();return new Promise(()=>{});}});
  await sent;controller.abort();
  await reject(()=>pending,error=>{assert.equal(error.code,'cancelled');assert(error.uncertain);});
});
test('default does not impose a new deadline on existing long operations',async()=>{
  const result=await requestJSON('/api/studio/long-operation',{}, {fetcher:async()=>{
    await new Promise(resolve=>setTimeout(resolve,15));return json({completed:true});
  }});assert(result.completed);
});
test('local serialization errors do not send a request',async()=>{
  let calls=0;
  await reject(()=>requestJSON('/api/studio/settings',{x:1n},{fetcher:async()=>{calls++;return json({});}}),error=>{
    assert.equal(error.code,'invalid_request');assert.equal(error.uncertain,false);
  });assert.equal(calls,0);
});
for(const timeoutMs of [-1,Infinity,600001])test('invalid timeout '+timeoutMs+' is rejected before fetch',async()=>{
  let calls=0;
  await reject(()=>requestJSON('/api/studio/bootstrap',undefined,{timeoutMs,fetcher:async()=>{calls++;return json({});}}),error=>assert.equal(error.code,'invalid_request'));
  assert.equal(calls,0);
});
