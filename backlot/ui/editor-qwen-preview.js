import {requestJSON} from './studio-http.js';
import {compatibilityState} from './studio-compatibility.js';

// Real requests only. A lost HTTP response is recovered by ID, never retried.
export function initializeQwenPreview({host,getProject,getRevision,getEdl,capture,applyInputs,registerPreview,onJobState=()=>{}}){
  const root=document.createElement('div');
  root.innerHTML='<label>Dispositivo explícito<select data-device><option value="cuda">CUDA BF16 preparado</option><option value="cpu">CPU FP32, si hay RAM</option></select></label><label>Máximo de tokens nuevos<input data-tokens type="number" min="8" max="256" value="128"></label><label>Semilla<input data-seed type="number" min="0" max="2147483647" value="42"></label><button type="button" data-start disabled>Crear preescucha Qwen local</button><button type="button" data-cancel disabled>Cancelar worker Qwen</button><button type="button" data-recover>Recuperar última solicitud Qwen</button><button type="button" data-new>Nueva solicitud Qwen (otra toma)</button><button type="button" data-history>Consultar solicitudes del proyecto</button><label>Solicitud guardada<select data-request></select></label><button type="button" data-open>Abrir estado guardado</button><button type="button" data-use disabled>Cargar parámetros de esta solicitud</button><pre data-inputs hidden></pre><audio controls hidden></audio><button type="button" data-import disabled>Registrar preescucha Qwen en biblioteca</button><p data-preview-message role="status"></p>';
  host.append(root);const q=s=>root.querySelector(s);
  let profile=null,backend=false,busy=false,job=null,sample=null,owner=null,planKey=null,timer=null;
  const live=()=>['running','cancelling','unknown','interrupted'].includes(job?.state);
  const storageKey=pid=>'studio-qwen-preview:'+pid;
  const token=pid=>{try{return JSON.parse(sessionStorage.getItem(storageKey(pid))||'null');}catch{return null;}};
  const remember=(pid,value)=>{try{sessionStorage.setItem(storageKey(pid),JSON.stringify(value));}catch{/* persistent server record remains */}};
  const message=text=>{q('[data-preview-message]').textContent=text;};
  const base=pid=>'/api/studio/editor/'+encodeURIComponent(pid);
  const api=(path,data)=>requestJSON(path,data,{timeoutMs:15000});
  const options=()=>({device:q('[data-device]').value,max_new_tokens:Number(q('[data-tokens]').value),seed:Number(q('[data-seed]').value)});
  function normalized(value){
    const result={profile:value.profile,language:value.language,text:value.text,device:value.device||'cuda',max_new_tokens:value.max_new_tokens??128,seed:value.seed??42};
    if(value.profile==='voice-design')result.instruction=value.instruction;
    else Object.assign(result,{reference_source_id:value.reference_source_id,reference_text:value.reference_text,reference_authorized:value.reference_authorized===true});
    return result;
  }
  const inputs=()=>normalized({...capture(),...options()});
  function stopAudio(){sample=null;q('audio').pause();q('audio').removeAttribute('src');q('audio').hidden=true;q('audio').load();}
  function controls(){
    q('[data-start]').disabled=busy||live()||!backend||!profile?.preview_available||!getProject()||!compatibilityState().ok;
    q('[data-cancel]').disabled=busy||!job?.request_id||!live();
    q('[data-new]').disabled=busy||live();q('[data-use]').disabled=busy||live()||!job?.inputs;
    for(const name of ['history','open','request'])q('[data-'+name+']').disabled=busy||live();
    for(const name of ['device','tokens','seed'])q('[data-'+name+']').disabled=busy||live();
    q('[data-import]').disabled=busy||live()||!sample||sample.pid!==getProject()||Object.values(getEdl().sources).some(s=>s.path===sample.relative_path);
  }
  function setBusy(value){busy=value;controls();onJobState();}
  function present(value){
    job=value;stopAudio();const progress=value.progress;
    q('[data-inputs]').hidden=!value.inputs;q('[data-inputs]').textContent=value.inputs?JSON.stringify(normalized(value.inputs),null,2):'';
    const label={running:'Worker local activo',cancelling:'Cancelación solicitada; esperando salida del worker',cancelled:'Solicitud cancelada',completed:'Preescucha completada; escucha humana pendiente',failed:'Preescucha fallida',invalid:'Salida modificada; no reutilizable',interrupted:'Worker sin reconciliar tras cambio de servidor',unknown:'Respuesta incierta; recupera estado antes de repetir'}[value.state]||value.state;
    message(label+(progress?` · ${progress.phase} · pasadas registradas: ${progress.forward_count||0}`:'')+(value.error?' · '+value.error:''));
    if(value.state==='completed'&&value.result){
      if(JSON.stringify(normalized(value.inputs))===JSON.stringify(inputs())){sample={pid:getProject(),...value.result};q('audio').src=sample.url;q('audio').hidden=false;}
      else message(label+' · Se conservan los parámetros actuales, que difieren. Carga explícitamente los de la solicitud para escucharla.');
    }
    controls();onJobState();
  }
  async function poll(pid,id){
    if(pid!==getProject())return;
    try{const value=await api(base(pid)+'/qwen/requests/'+id);if(pid!==getProject())return;present(value);if(['running','cancelling'].includes(value.state))timer=setTimeout(()=>poll(pid,id),700);}
    catch(error){if(pid===getProject())present({...(job||{}),request_id:id,state:error.status===404?'failed':'unknown',error:error.message});}
  }
  function draw(selected,available){
    profile=selected;backend=available;const pid=getProject();
    if(owner!==pid){clearTimeout(timer);owner=pid;job=null;planKey=null;stopAudio();}
    const plan=pid?getEdl().qwen_tts_plan:null,next=JSON.stringify([pid,plan]);
    if(next!==planKey){planKey=next;if(plan){q('[data-device]').value=plan.device||profile?.diagnostic.device||'cuda';q('[data-tokens]').value=plan.max_new_tokens??128;q('[data-seed]').value=plan.seed??42;}}
    if(sample&&job?.inputs&&JSON.stringify(normalized(job.inputs))!==JSON.stringify(inputs()))stopAudio();
    controls();
  }
  host.addEventListener('input',event=>{if(!root.contains(event.target)){stopAudio();controls();}});
  for(const name of ['device','tokens','seed'])q('[data-'+name+']').oninput=()=>{stopAudio();controls();};
  q('[data-start]').onclick=async()=>{
    if(busy||live())return;setBusy(true);const pid=getProject(),value=inputs();let sent=false;
    try{
      if(!value.text.trim()||value.text.length>300)throw Error('Preescucha:1–300caracteres; texto conservado.');
      const signature=JSON.stringify(value),saved=token(pid),id=saved?.signature===signature?saved.id:crypto.randomUUID().replaceAll('-','');
      remember(pid,{id,signature});job={request_id:id,state:'unknown'};
      sent=true;const response=await api(base(pid)+'/qwen/preview',{...value,request_id:id,revision:getRevision()});
      if(pid!==getProject())return;present(response);if(['running','cancelling'].includes(response.state))timer=setTimeout(()=>poll(pid,id),100);
    }catch(error){if(pid===getProject())present({...job,state:!sent||(error.status>=400&&error.status<500)?'failed':'unknown',error:error.message});}
    finally{setBusy(false);}
  };
  q('[data-cancel]').onclick=async()=>{if(busy||!job?.request_id)return;const pid=getProject(),id=job.request_id;busy=true;controls();clearTimeout(timer);try{const value=await api(base(pid)+'/qwen/requests/'+id+'/cancel',{});if(pid===getProject()){present(value);timer=setTimeout(()=>poll(pid,id),100);}}catch(error){message('Cierre sin confirmar: '+error.message);}finally{busy=false;controls();}};
  const recover=id=>{if(!id){message('Sin request_id guardado; consulta solicitudes del proyecto.');return;}clearTimeout(timer);poll(getProject(),id);};
  q('[data-recover]').onclick=()=>recover(token(getProject())?.id);
  q('[data-open]').onclick=()=>recover(q('[data-request]').value);
  q('[data-history]').onclick=async()=>{const pid=getProject();try{const value=await api(base(pid)+'/qwen/requests');if(pid!==getProject())return;q('[data-request]').replaceChildren(...value.rows.map(v=>new Option(v.profile+' · '+v.state+' · '+v.request_id,v.request_id)));message(value.note);}catch(error){message(error.message);}};
  q('[data-new]').onclick=()=>{if(live())return;remember(getProject(),null);job=null;stopAudio();message('Otra toma requiere pulsar Crear preescucha explícitamente.');controls();};
  q('[data-use]').onclick=()=>{if(job?.inputs&&!live()){applyInputs(job.inputs);for(const [name,key]of [['device','device'],['tokens','max_new_tokens'],['seed','seed']])q('[data-'+name+']').value=job.inputs[key];present(job);}};
  q('[data-import]').onclick=async()=>{if(busy||!sample)return;setBusy(true);try{await registerPreview(sample.relative_path);message('WAV registrado en biblioteca compartida; no se duplica ni sintetiza.');}catch(error){message(error.message);}finally{setBusy(false);}};
  return {draw,options,active:()=>busy||live()};
}
