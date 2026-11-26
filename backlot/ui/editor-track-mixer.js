// Persisted logical lanes, shared graph for preview/export; never browser-only mute.
export function initializeTrackMixer({host,getEdl,getProject,has,run}) {
  const root=document.createElement('details');root.id='edit-track-mixer';root.hidden=true;
  root.innerHTML='<summary>Mezclador de pistas</summary><form><fieldset></fieldset></form><p>Vídeo: audio de todos los cortes. Audio: todos los clips añadidos. Solo de pista filtra pistas; solo de clip sigue filtrando clips. Silencio prevalece. Prepara el montaje para escuchar los cambios; no es mezcla en directo.</p><p role="status"></p>';
  const form=root.querySelector('form'),set=root.querySelector('fieldset'),status=root.querySelector('[role=status]');
  for(const [lane,name] of [['video','Audio del vídeo'],['audio','Clips de audio']]){
    const strip=document.createElement('fieldset');strip.innerHTML=`<legend>${name}</legend><label>Nivel lineal (0–4)<input name="${lane}_gain" type="number" min="0" max="4" step="0.01" value="1" required></label><label><input name="${lane}_muted" type="checkbox">Silencio</label><label><input name="${lane}_solo" type="checkbox">Solo</label>`;set.append(strip);
  }
  const save=document.createElement('button');save.type='submit';save.textContent='Guardar mezclador';set.append(save);
  const reset=document.createElement('button');reset.type='button';reset.textContent='Restablecer pistas';set.append(reset);host.before(root);
  let key=null,busy=false;
  function draw(){root.hidden=!has('track_mixer');set.disabled=busy||root.hidden;const mixer=getEdl().track_mixer||{},next=JSON.stringify([getProject(),mixer]);if(next===key)return;key=next;for(const lane of ['video','audio']){form.elements[lane+'_gain'].value=mixer[lane]?.gain??1;for(const flag of ['muted','solo'])form.elements[lane+'_'+flag].checked=mixer[lane]?.[flag]??false;}}
  async function submit(mixer){if(busy)return;busy=true;draw();status.textContent='Guardando…';try{await run('track_mixer',{mixer});status.textContent='Mezclador guardado. Prepara el montaje para escucharlo.';}catch(error){status.textContent='Guardado no confirmado: '+error.message+' Recupera el estado antes de repetir.';}finally{busy=false;draw();}}
  form.onsubmit=event=>{event.preventDefault();if(!form.reportValidity())return;const mixer={};for(const lane of ['video','audio'])mixer[lane]={gain:Number(form.elements[lane+'_gain'].value),muted:form.elements[lane+'_muted'].checked,solo:form.elements[lane+'_solo'].checked};submit(mixer);};reset.onclick=()=>submit({});
  return {draw,reset(){key=null;}};
}
