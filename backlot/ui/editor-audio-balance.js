// One revisioned command, shared with the agent; no playback-only audio fork.
export function initializeAudioBalance({host,getEdl,getProject,getSelection,has,run}) {
  const root=document.createElement('details');root.hidden=true;root.id='edit-balance-panel';
  root.innerHTML=`<summary>Balance estéreo del clip</summary><form id="edit-balance-form"><fieldset><label>Izquierda −1 · centro 0 · derecha +1<input aria-label="Balance estéreo" name="balance" type="range" min="-1" max="1" step="0.01" value="0"></label><output aria-live="polite">0.00 · centro</output><button type="submit">Guardar balance</button><button type="button">Centrar</button></fieldset></form><p>Atenúa el canal opuesto, sin amplificar ni mezclar canales. No es panorama espacial. Prepara la vista previa para escuchar el montaje; reproducir la fuente no aplica estos cambios.</p><p role="status"></p>`;
  host.before(root);
  const form=root.querySelector('form'),field=form.elements.balance,output=root.querySelector('output'),status=root.querySelector('[role=status]'),centre=root.querySelector('button[type=button]');
  let key=null,busy=false;
  function label(){const value=Number(field.value);output.textContent=value.toFixed(2)+(value<0?' · izquierda':value>0?' · derecha':' · centro');}
  function draw(item){
    if(item===undefined){try{item=getSelection();}catch{/* no selection */}}
    const source=item?.clip?.source_id&&getEdl().sources[item.clip.source_id];
    const enabled=has('audio_balance')&&item?.clip?.kind!=='gap'&&source?.audio;
    root.hidden=!enabled;form.querySelector('fieldset').disabled=!enabled||busy||Boolean(item?.clip?.locked);
    const next=JSON.stringify([getProject(),item?.id,item?.track,item?.clip?.stereo_balance,item?.clip?.locked]);
    if(next!==key){key=next;field.value=item?.clip?.stereo_balance??0;status.textContent='';label();}
  }
  async function save(value){
    if(busy)return;let item;try{item=getSelection();}catch{return;}
    if(!has('audio_balance')||item.clip.locked)return;
    busy=true;draw(item);status.textContent='Guardando…';
    try{await run('audio_balance',{id:item.id,track:item.track,balance:value});status.textContent='Balance guardado en el proyecto.';}
    catch(error){status.textContent='No se confirmó el guardado: '+error.message+' Recupera el estado antes de repetir.';}
    finally{busy=false;draw();}
  }
  field.oninput=label;form.onsubmit=event=>{event.preventDefault();save(Number(field.value));};
  centre.onclick=()=>{field.value=0;label();save(0);};
  return {draw,reset(){key=null;}};
}
