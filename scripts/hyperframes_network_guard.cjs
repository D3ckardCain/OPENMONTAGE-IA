// Child-process guard for local render QA. It does not change Windows networking.
const fs=require('node:fs'),net=require('node:net'),dns=require('node:dns');
function check(host){
 const name=String(host||'localhost').replace(/^\[|\]$/g,'').toLowerCase();
 const local=['localhost','127.0.0.1','::1'].includes(name);
 if(process.env.OPENMONTAGE_HF_NETWORK_LOG)fs.appendFileSync(process.env.OPENMONTAGE_HF_NETWORK_LOG,JSON.stringify({host:name,allowed:local})+'\n');
 if(!local){const error=Error('Offline HyperFrames profile refused external host: '+name);error.code='OPENMONTAGE_OFFLINE';throw error;}
}
const connect=net.Socket.prototype.connect;
net.Socket.prototype.connect=function(...args){
 const a=Array.isArray(args[0])?args[0]:args,options=a[0];
 if(!(options&&typeof options==='object'&&options.path))check(options&&typeof options==='object'?(options.host||options.hostname):(typeof a[1]==='string'?a[1]:'localhost'));
 return connect.apply(this,args);
};
const lookup=dns.lookup;dns.lookup=function(host,...args){check(host);return lookup.call(this,host,...args);};
if(global.fetch){const fetch=global.fetch;global.fetch=function(input,...args){check(new URL(input instanceof URL?input.href:typeof input==='string'?input:input.url).hostname);return fetch.call(this,input,...args);};}
