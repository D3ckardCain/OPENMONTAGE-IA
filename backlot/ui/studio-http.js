// One request, no retries. A client deadline never proves server work stopped.
export class StudioHTTPError extends Error{
  constructor(message,{code,status=0,uncertain=false}={}){
    super(message);this.name='StudioHTTPError';this.code=code;this.status=status;this.uncertain=uncertain;
  }
}
const uncertainNote=' La respuesta no confirma si el servidor aplicó la operación. Consulta su estado antes de repetir; cerrar HTTP no detiene necesariamente el cálculo.';
function detail(value){
  if(typeof value==='string')return value.trim().slice(0,1000);
  if(Array.isArray(value))return value.slice(0,5).map(item=>{
    if(typeof item==='string')return item.slice(0,200);
    const field=Array.isArray(item?.loc)?item.loc.filter(x=>x!=='body').join('.')+': ':'';
    return field+detail(item?.msg||item?.message||'Dato no válido');
  }).join(' · ');
  if(value&&typeof value==='object')return detail(value.message||value.msg||value.error);
  return '';
}
function httpError(status,payload,mutating){
  const labels={400:'Solicitud rechazada',401:'Autenticación requerida',403:'Acceso denegado',404:'Recurso no encontrado',
    409:'El estado cambió; consulta la revisión antes de reenviar',422:'Hay datos no válidos'};
  const message=(labels[status]||(status>=500?'Error interno de Studio':'Error de Studio'))+' (HTTP '+status+')';
  const explanation=detail(payload?.detail??payload?.message);
  const uncertain=mutating&&status>=500;
  return new StudioHTTPError(message+(explanation?': '+explanation:'')+(uncertain?uncertainNote:''),
    {code:status===403?'forbidden':status===409?'conflict':status>=500?'server':'http',status,uncertain});
}

export async function requestJSON(path,data,{timeoutMs=0,signal,fetcher=globalThis.fetch}={}){
  if(!Number.isFinite(timeoutMs)||timeoutMs<0||timeoutMs>600000)throw new StudioHTTPError('Plazo de cliente no válido',{code:'invalid_request'});
  const mutating=data!==undefined;
  let body;
  try{if(mutating)body=JSON.stringify(data);}catch{throw new StudioHTTPError('No se pudieron preparar los datos de la solicitud',{code:'invalid_request'});}
  if(signal?.aborted)throw new StudioHTTPError('Solicitud cancelada antes de enviarla',{code:'cancelled'});
  const controller=new AbortController();let timer=null,started=false,observedStatus=0,cause=null,abort;
  const uncertain=()=>mutating&&started&&!(observedStatus>=400&&observedStatus<500);
  const stopped=reason=>new StudioHTTPError((reason==='timeout'?'Se agotó la espera del navegador.':'Se canceló la espera del navegador.')+
    (uncertain()?uncertainNote:' No se ha confirmado que necesite reiniciar Studio.'),
    {code:reason,status:observedStatus,uncertain:uncertain()});
  const deadline=new Promise((resolve,reject)=>{
    abort=()=>{cause='cancelled';controller.abort();reject(stopped(cause));};
    if(signal)signal.addEventListener('abort',abort,{once:true});
    if(timeoutMs)timer=setTimeout(()=>{cause='timeout';controller.abort();reject(stopped(cause));},timeoutMs);
  });
  try{
    const operation=(async()=>{
      started=true;
      const response=await fetcher(path,{...(mutating?{method:'POST',headers:{'Content-Type':'application/json'},body}:{}),signal:controller.signal});
      observedStatus=response.status;
      if(response.status===204)return null;
      const raw=await response.text();let value;
      try{value=JSON.parse(raw);}catch{
        if(!response.ok)throw httpError(response.status,null,mutating);
        throw new StudioHTTPError('Studio devolvió una respuesta JSON vacía o no válida.'+(mutating?uncertainNote:''),
          {code:'invalid_response',status:response.status,uncertain:mutating});
      }
      if(!response.ok)throw httpError(response.status,value,mutating);
      return value;
    })();
    return await (timeoutMs||signal?Promise.race([operation,deadline]):operation);
  }catch(error){
    if(error instanceof StudioHTTPError)throw error;
    if(cause)throw stopped(cause);
    throw new StudioHTTPError('No se pudo completar la conexión con Studio.'+(uncertain()?uncertainNote:' Comprueba su estado; este fallo no demuestra que necesite reiniciar.'),
      {code:'network',status:observedStatus,uncertain:uncertain()});
  }finally{
    if(timer!==null)clearTimeout(timer);
    if(signal)signal.removeEventListener('abort',abort);
  }
}
