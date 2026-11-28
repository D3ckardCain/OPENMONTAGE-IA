// Shared server requests and receipts; session storage holds only recovery tokens.
export function initializePiperUI({host,getProject,getRevision,reopen}){
  const panel=document.createElement('details');panel.className='editor-audio-tool';
  panel.innerHTML='<summary>Voces locales Piper</summary><button type="button" data-load>Consultar voces</button><label>Voz<select data-voice></select></label><label>Hablante<select data-speaker></select></label><p data-license></p><textarea data-text maxlength="1000" aria-label="Texto de preescucha">Esta es una prueba breve de voz local.</textarea><button type="button" data-preview disabled>Crear preescucha local</button><button type="button" data-recover>Recuperar última solicitud</button><button type="button" data-new>Nueva solicitud (otra toma)</button><audio controls></audio><button type="button" data-import disabled>Incorporar a biblioteca de audio</button><p role="status" data-status></p>';
  host.append(panel);
  const q=s=>panel.querySelector(s);
  let voices=[],sample=null,busy=false;
  const status=t=>{q('[data-status]').textContent=t;};
  const storageKey=pid=>'studio-piper-request:'+pid;
  const memoryTokens=new Map();
  // A browser storage failure must not turn a completed response into an error.
  const stored=pid=>{if(memoryTokens.has(pid))return memoryTokens.get(pid);try{return sessionStorage.getItem(storageKey(pid));}catch{return null;}};
  const remember=(pid,id)=>{memoryTokens.set(pid,id);try{sessionStorage.setItem(storageKey(pid),id);}catch{/* in-memory/server evidence remains */}};
  const current=()=>voices.find(v=>v.id===q('[data-voice]').value);
  function controls(){
    for(const name of ['[data-load]','[data-voice]','[data-speaker]','[data-text]','[data-recover]','[data-new]'])q(name).disabled=busy;
    q('[data-preview]').disabled=busy||!current()?.available||current()?.blocked||current()?.preview_contract!==1;
    q('[data-import]').disabled=busy||!sample||sample.pid!==getProject();
  }
  function invalidate(){
    sample=null;q('audio').pause();q('audio').removeAttribute('src');q('audio').load();controls();
  }
  async function api(url,body){
    const r=await fetch('/api/studio/editor/'+url,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
    const d=await r.json();if(!r.ok){const e=Error(d.detail||r.status);e.status=r.status;throw e;}return d;
  }
  function select(){
    const v=current();q('[data-speaker]').replaceChildren();
    for(const [label,id] of Object.entries(v?.speakers||{}))q('[data-speaker]').add(new Option(label+' · '+id,id));
    q('[data-license]').textContent=v?.attribution||'';invalidate();
    status(v?.blocked?'VCTK antiguo bloqueado: base Lessac.':v?.preview_contract!==1?
      'Backend anterior: la recuperación requiere activación manual; no se repite una síntesis por error HTTP.':
      'Preescucha disponible; naturalidad/calidad requieren escucha.');
  }
  const inputs=()=>({voice:q('[data-voice]').value,speaker_id:Number(q('[data-speaker]').value),text:q('[data-text]').value});
  function show(result,pid){
    if(pid!==getProject()){status('Resultado guardado en el proyecto anterior; recupéralo allí.');return;}
    sample={...result,pid};q('audio').src='/api/studio/editor/'+encodeURIComponent(pid)+'/piper/audio/'+result.relative_path.split('/').pop();
    status((result.reused?'Resultado recuperado sin repetir síntesis · ':'')+result.seconds.toFixed(2)+' s · escucha antes de aprobar. Atribución guardada junto al WAV.');
  }
  q('[data-load]').onclick=async()=>{try{
    voices=await api('piper/voices');q('[data-voice]').replaceChildren();for(const v of voices)q('[data-voice]').add(new Option(v.id,v.id));select();
  }catch(e){status(e.message+' · Comprueba la identidad del backend.');}};
  q('[data-voice]').onchange=select;
  for(const control of ['[data-speaker]','[data-text]'])q(control).oninput=invalidate;
  document.getElementById('edit-project')?.addEventListener('change',invalidate);
  q('[data-new]').onclick=()=>{
    const pid=getProject();if(pid){memoryTokens.delete(pid);try{sessionStorage.removeItem(storageKey(pid));}catch{/* no persistent storage */}}
    invalidate();status('Nueva solicitud preparada. Solo Crear preescucha iniciará otra toma; las anteriores se conservan.');
  };
  q('[data-preview]').onclick=async()=>{
    const pid=getProject();if(!pid){status('Abre un proyecto editable primero');return;}
    const data=inputs();busy=true;invalidate();status('Comprobando la solicitud guardada…');
    try{
      let id=stored(pid);
      if(id){
        try{
          const record=await api(encodeURIComponent(pid)+'/piper/requests/'+id);
          if(record.inputs&&Object.keys(data).some(k=>record.inputs[k]!==data[k]))id=null;
        }catch(e){if(e.status!==404)throw e;}
      }
      id=id||crypto.randomUUID().replaceAll('-','');remember(pid,id);
      status('Solicitud '+id+' · sintetizando localmente; perder HTTP no acredita detener el cálculo.');
      show(await api(encodeURIComponent(pid)+'/piper/preview',{...data,request_id:id}),pid);
    }catch(e){status(e.message+' · Usa Recuperar última solicitud; no se reintenta automáticamente.');}
    finally{busy=false;controls();}
  };
  q('[data-recover]').onclick=async()=>{
    const pid=getProject(),id=pid&&stored(pid);if(!id){status('No hay token de solicitud para este proyecto en esta pestaña.');return;}
    busy=true;invalidate();
    try{
      const record=await api(encodeURIComponent(pid)+'/piper/requests/'+id);
      if(pid!==getProject())return;
      if(record.state==='completed'&&record.result){
        q('[data-voice]').value=record.inputs.voice;select();q('[data-speaker]').value=String(record.inputs.speaker_id);q('[data-text]').value=record.inputs.text;
        show({...record.result,reused:true},pid);
      }else status('Solicitud '+record.state+' · '+(record.error||'Espera y consulta otra vez; no se ha detenido ni repetido el proveedor.'));
    }catch(e){status(e.message);}finally{busy=false;controls();}
  };
  q('[data-import]').onclick=async()=>{try{
    if(!sample||sample.pid!==getProject())throw Error('Crea o recupera una preescucha para este proyecto');
    await api(encodeURIComponent(sample.pid)+'/register',{relative_path:sample.relative_path,revision:getRevision()});await reopen();
    status('Audio incorporado al proyecto compartido; puedes añadirlo a la pista y deshacer mediante los controles existentes.');
  }catch(e){status(e.message);}};
  return panel;
}
