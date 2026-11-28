// Opt-in owned QA process only. Installed package files remain untouched.
const {registerHooks}=require('node:module');
registerHooks({load(url,context,nextLoad){const value=nextLoad(url,context);
 if(url.endsWith('/chunk-F3U5D5L3.js')){let source=Buffer.isBuffer(value.source)?value.source.toString('utf8'):String(value.source);
  let count=0;source=source.replace(/(session\.captureStep\s*=\s*[^;]+;)/g,match=>{count++;return match+'\nconsole.error("[qa186-capture-step]",session.captureStep);';});
  if(count!==12)throw Error('QA186 trace source drift: expected12 capture-step assignments, got '+count);
  console.error('[qa186-trace-loaded]',count);return {...value,source};
 }return value;}});
