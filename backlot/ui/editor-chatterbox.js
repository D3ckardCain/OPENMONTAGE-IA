import {requestJSON} from './studio-http.js';
// Existing samples only: no synthesis, model loading or request submission.
const host=document.querySelector('#edit-waveform-status')?.parentElement;
if(host){
  const box=document.createElement('details');
  box.innerHTML='<summary>Voces Chatterbox · muestras guardadas</summary><button type="button" data-load>Consultar muestras existentes</button><label>Muestra<select data-sample disabled></select></label><audio data-audio controls preload="metadata" hidden></audio><p data-source></p><p role="status" data-message></p>';
  host.append(box);
  const q=s=>box.querySelector(s),audio=q('[data-audio]'),select=q('[data-sample]');
  let profiles=[];
  const storageKey='studio-chatterbox-saved-sample';
  function draw(){
    const row=profiles.find(r=>r.id===select.value),sample=row?.cached_sample;
    audio.pause();audio.hidden=!sample?.available;
    if(sample?.available){
      audio.src=sample.url;
      q('[data-source]').textContent=`${row.locale} · ${sample.duration_seconds.toFixed(2)} s · ${sample.sample_rate} Hz · muestra existente. Escucha humana pendiente.`;
      q('[data-message]').textContent='Reproducir no genera otra voz ni carga el modelo. La creación de nuevas tomas desde Audio sigue pendiente.';
      try{localStorage.setItem(storageKey,row.id);}catch{}
    }else{
      audio.removeAttribute('src');q('[data-source]').textContent='';
      q('[data-message]').textContent='No hay una muestra guardada elegible para este perfil. No se inicia síntesis automáticamente.';
    }
    audio.load();
  }
  q('[data-load]').onclick=async()=>{
    const button=q('[data-load]');if(button.disabled)return;button.disabled=true;
    try{
      const value=await requestJSON('/api/studio/editor/chatterbox/profiles');profiles=value.samples?.length?value.samples:value.profiles;
      let previous=select.value;try{previous=previous||localStorage.getItem(storageKey);}catch{}
      select.replaceChildren(...profiles.map(r=>new Option(r.locale+(r.cached_sample?.available?' · muestra guardada':' · sin muestra'),r.id)));
      if(profiles.some(r=>r.id===previous))select.value=previous;
      select.disabled=!profiles.length;draw();
    }catch(error){q('[data-message]').textContent=error.message;}
    finally{button.disabled=false;}
  };
  select.onchange=draw;
  audio.onerror=()=>{q('[data-message]').textContent='No se pudo leer la muestra. Consulta su estado antes de reintentar; no se ha sintetizado otra toma.';};
}
