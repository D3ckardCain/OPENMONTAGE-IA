// New guard checks: real loopback HTTP plus external attempts rejected before I/O.
const assert=require('node:assert/strict'),http=require('node:http'),dns=require('node:dns'),net=require('node:net');
require('../scripts/hyperframes_network_guard.cjs');
(async()=>{
 const server=http.createServer((req,res)=>res.end('local'));
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const url=new URL(`http://127.0.0.1:${server.address().port}/`);
  assert.equal(await(await fetch(url)).text(),'local');
  for(const value of ['https://example.invalid/',new URL('https://example.invalid/'),new Request('https://example.invalid/')])
   assert.throws(()=>fetch(value),{code:'OPENMONTAGE_OFFLINE'});
  assert.throws(()=>dns.lookup('example.invalid',()=>{}),{code:'OPENMONTAGE_OFFLINE'});
  assert.throws(()=>net.connect({host:'192.0.2.1',port:443}),{code:'OPENMONTAGE_OFFLINE'});
  console.log('PASS loopback HTTP and 5 external attempts blocked before I/O');
 }finally{await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1});
