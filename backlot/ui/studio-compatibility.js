// Pure classifier also used by offline tests. No restart/download actions.
export function classify(identity,caps,pageBuild,status=200){
  const fail=(kind,message)=>({ok:false,kind,message});
  if(status===404)return fail('restart','Esta instancia de Studio es anterior al contrato de compatibilidad. Reinicia Studio manualmente cuando no haya trabajos activos; no se reinicia automáticamente.');
  if(status!==200||!identity)return fail('unknown','No se pudo comprobar la compatibilidad de Studio. Comprueba la conexión y vuelve a consultar; no se ha demostrado que necesite reiniciar.');
  if(identity.schema_version!==1||identity.api_protocol!==1||caps?.api_protocol!==1)
    return fail('incompatible','Interfaz y API de Studio incompatibles. Usa una copia coherente del proyecto y reinicia Studio manualmente cuando no haya trabajos activos.');
  if(identity.restart_required===true)return fail('restart','Studio mantiene código anterior en memoria. Hace falta reiniciar Studio manualmente cuando no haya trabajos activos para cargar los cambios.');
  if(identity.restart_required!==false||identity.resident?.status!=='available'||identity.ui?.status!=='available')
    return fail('unknown','No se pudo verificar la identidad de los archivos de Studio. Revisa su acceso antes de editar.');
  if(!pageBuild||pageBuild!==identity.ui.sha256)
    return fail('reload','La interfaz abierta pertenece a otra revisión o no tiene identidad. Recarga esta página para usar los archivos actuales; no se reinicia Studio.');
  if(caps.backend_build!==identity.resident.sha256||caps.version!=='3.0'||caps.shared_revision!==true||
     !Array.isArray(caps.commands)||!Array.isArray(identity.editor?.commands)||
     JSON.stringify([...caps.commands].sort())!==JSON.stringify([...identity.editor.commands].sort())||
     caps.render_cancel!==identity.editor.render_cancel)
    return fail('incompatible','La API y sus capacidades no corresponden a la misma revisión. No se enviarán cambios desde el editor; recarga y comprueba la instancia de Studio.');
  return {ok:true,kind:'compatible',message:'Interfaz y API compatibles · '+identity.resident.sha256.slice(0,12)};
}
let current={ok:false,kind:'checking',message:'Comprobando compatibilidad de Studio…'};
export const compatibilityState=()=>current;
export async function inspectCompatibility(fetcher=fetch,pageBuild='',timeout=4000){
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeout);
  try{
    const [response,capResponse]=await Promise.all([
      fetcher('/api/studio/identity',{cache:'no-store',signal:controller.signal}),
      fetcher('/api/studio/editor/capabilities',{cache:'no-store',signal:controller.signal})]);
    const caps=capResponse.ok?await capResponse.json():null;
    if(response.status!==200)return {...classify(null,null,pageBuild,response.status),caps};
    if(!capResponse.ok&&capResponse.status!==404)return {...classify(null,null,pageBuild,capResponse.status),caps};
    const data=await response.json();
    return {...classify(data,caps,pageBuild),caps};
  }catch{return {...classify(null,null,pageBuild,0),caps:null};}
  finally{clearTimeout(timer);}
}
let checkSequence=0;
export async function checkCompatibility(){
  const sequence=++checkSequence;
  const banner=document.getElementById('studio-compatibility');
  const result=await inspectCompatibility(fetch,document.querySelector('meta[name="studio-ui-build"]')?.content||'');
  if(sequence!==checkSequence)return current;
  current=result;
  if(banner){banner.hidden=current.ok;banner.dataset.kind=current.kind;document.getElementById('studio-compatibility-message').textContent=current.message;}
  document.dispatchEvent(new CustomEvent('studio-compatibility',{detail:current}));
  return current;
}
export const compatibilityReady=typeof document==='undefined'?Promise.resolve(current):checkCompatibility();
if(typeof document!=='undefined'){
  document.getElementById('studio-compatibility-check')?.addEventListener('click',checkCompatibility);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)checkCompatibility();});
}
