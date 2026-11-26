import {requestJSON} from './studio-http.js';
// Existing samples only: no synthesis, model loading or request submission.
const host=document.querySelector('#edit-waveform-status')?.parentElement;
if(host){
  const box=document.createElement('div');
  box.innerHTML='<button type="button" data-open>Voces Chatterbox · muestras guardadas</button><dialog data-window aria-labelledby="chatterbox-window-title"><div class="voice-window-heading"><h3 id="chatterbox-window-title">Muestras Chatterbox guardadas</h3><button type="button" data-close>Cerrar</button></div><p>Pruebas locales existentes, no perfiles de voz nuevos. Reproducir no sintetiza ni carga modelos.</p><button type="button" data-load>Actualizar muestras</button><div class="voice-sample-grid" data-cards></div><audio data-audio controls preload="metadata" hidden></audio><p data-source></p><p role="status" data-message></p></dialog><style>[data-window]{color:#e6edf3;background:#0d1117;border:1px solid #484f58;border-radius:12px;width:min(850px,94vw);max-height:85vh;overflow:auto;padding:20px}[data-window]::backdrop{background:#000a}.voice-window-heading{display:flex;justify-content:space-between;align-items:center;gap:12px}.voice-sample-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:16px 0}.voice-sample-grid article{padding:16px;margin:0;min-width:0}.voice-sample-grid article[data-selected=true]{border-color:#58a6ff}.voice-sample-grid h4{margin:0 0 8px}.voice-sample-grid button:focus-visible,[data-window] button:focus-visible{outline:2px solid #58a6ff;outline-offset:3px}[data-window] audio{width:100%}</style>';
  host.append(box);
  const q=s=>box.querySelector(s),audio=q('[data-audio]'),dialog=q('[data-window]');
  let profiles=[],selected='';
  const storageKey='studio-chatterbox-saved-sample';
  function draw(id){
    selected=id;const row=profiles.find(r=>r.id===id),sample=row?.cached_sample;
    for(const card of q('[data-cards]').children){const active=card.dataset.profile===id;card.dataset.selected=String(active);card.querySelector('button').setAttribute('aria-pressed',String(active));}
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
  async function load(){
    const button=q('[data-load]');if(button.disabled)return;button.disabled=true;
    try{
      const value=await requestJSON('/api/studio/editor/chatterbox/profiles');profiles=value.samples?.length?value.samples:value.profiles;
      let previous=selected;try{previous=previous||localStorage.getItem(storageKey);}catch{}
      q('[data-cards]').replaceChildren();
      for(const row of profiles){
        const card=document.createElement('article');card.dataset.profile=row.id;
        const title=document.createElement('h4');title.textContent='Prueba '+row.locale;
        const info=document.createElement('p');info.textContent=row.cached_sample?.available?`${row.cached_sample.duration_seconds.toFixed(2)} s · ${row.cached_sample.sample_rate} Hz · muestra de QA guardada`:'Sin muestra elegible';
        const play=document.createElement('button');play.type='button';play.textContent='Reproducir '+row.locale;play.disabled=!row.cached_sample?.available;
        play.onclick=async()=>{draw(row.id);try{await audio.play();}catch(error){q('[data-message]').textContent='No se pudo reproducir: '+error.message;}};
        card.append(title,info,play);q('[data-cards]').append(card);
      }
      draw(profiles.some(r=>r.id===previous)?previous:profiles[0]?.id);
    }catch(error){q('[data-message]').textContent=error.message;}
    finally{button.disabled=false;}
  }
  q('[data-load]').onclick=load;
  q('[data-open]').onclick=()=>{dialog.showModal();load();};
  q('[data-close]').onclick=()=>dialog.close();
  dialog.onclose=()=>audio.pause();
  audio.onerror=()=>{q('[data-message]').textContent='No se pudo leer la muestra. Consulta su estado antes de reintentar; no se ha sintetizado otra toma.';};
}
