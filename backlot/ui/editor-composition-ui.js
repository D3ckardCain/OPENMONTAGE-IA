// Real revisioned composition operations; render is required to see AV effects.
import {videoDuration} from './editor-time.js';
import {initializeLayerKeyframes} from './editor-layer-keyframes.js';
export function initializeCompositionUI({q,getEdl,getProject,getSelection,has,run,cursor}){
  const root=document.createElement('div');q('editor-inspector').append(root);
  root.innerHTML=`<details id="edit-transition-panel" hidden><summary>Transici&#243;n por negro</summary><form id="edit-transition-form"><label>Duraci&#243;n por lado (s)<input name="duration_seconds" type="number" min="0.017" max="2" step="0.001" value="0.25" required></label><button type="submit">Aplicar al corte anterior</button><button id="edit-transition-remove" type="button">Quitar transici&#243;n</button></form><p>Oscurece y aten&#250;a el final anterior y el inicio seleccionado. No solapa clips ni cambia tiempos. Fundido cruzado no disponible.</p></details>
  <details id="edit-layers-panel" hidden><summary>Capas de v&#237;deo</summary><label>Capa<select id="edit-layer-select"></select></label><form id="edit-layer-form"><label>Fuente de v&#237;deo<select name="source_id" required></select></label><label>Entrada de fuente (s)<input name="in_seconds" type="number" min="0" step="0.001" required></label><label>Salida de fuente (s)<input name="out_seconds" type="number" min="0.001" step="0.001" required></label><label>Inicio en montaje (s)<input name="start_seconds" type="number" min="0" step="0.001" required></label><label>Velocidad<input name="speed" type="number" min="0.25" max="4" step="0.05" required></label><label>X (0&#8211;1)<input name="x" type="number" min="0" max="1" step="0.01" required></label><label>Y (0&#8211;1)<input name="y" type="number" min="0" max="1" step="0.01" required></label><label>Anchura (0&#8211;1)<input name="width" type="number" min="0.05" max="1" step="0.01" required></label><label>Altura (0&#8211;1)<input name="height" type="number" min="0.05" max="1" step="0.01" required></label><label>Opacidad<input name="opacity" type="number" min="0" max="1" step="0.05" required></label><button type="submit">Guardar capa</button><button id="edit-layer-cursor" type="button">Inicio en cursor</button></form><button id="edit-layer-remove" type="button">Quitar capa</button><button id="edit-layer-lower" type="button">Bajar capa</button><button id="edit-layer-raise" type="button">Subir capa</button><p>Hasta4 capas dentro de la duraci&#243;n del montaje. Encaje seleccionable y movimiento lineal; solo imagen. Su audio se a&#241;ade por la pista de audio. Prepara vista previa para comprobar composici&#243;n.</p></details>`;
  const layerForm=q('edit-layer-form');
  const extras=document.createElement('div');extras.innerHTML='<label>Encaje<select name="fit"><option value="pad">Bandas</option><option value="crop">Llenar por recorte</option></select></label><label><input name="motion_enabled" type="checkbox"> Movimiento lineal por tiempo absoluto</label><label>Desplazamiento X<input name="motion_dx" type="number" min="-1" max="1" step=".01" value="0"></label><label>Desplazamiento Y<input name="motion_dy" type="number" min="-1" max="1" step=".01" value="0"></label><label>Duración del movimiento (s)<input name="motion_duration" type="number" min=".001" max="7200" step=".001" value="1"></label>';layerForm.append(extras);
  let transitionKey=null,layerKey=null;
  const keyframes=initializeLayerKeyframes({root,q,getEdl,getProject,has,run});
  const values=(form,data)=>{for(const [k,v]of Object.entries(data))if(form.elements[k])form.elements[k].value=v;};
  function drawSelection(){
    let item;try{item=getSelection();}catch{/* no selection */}
    const supported=has('transition')&&item?.track==='video'&&getEdl().cuts.indexOf(item.clip)>0;
    q('edit-transition-panel').hidden=!supported;
    const key=JSON.stringify([getProject(),item?.id,item?.clip.transition]);
    if(key!==transitionKey){values(q('edit-transition-form'),{duration_seconds:item?.clip.transition?.duration_seconds??.25});transitionKey=key;}
    q('edit-transition-remove').disabled=!item?.clip.transition;
  }
  function drawLayer(force=false){
    const edl=getEdl(),id=q('edit-layer-select').value,layer=edl.layers?.find(l=>l.id===id),sources=Object.entries(edl.sources).filter(([,s])=>s.kind==='video');
    const key=JSON.stringify([getProject(),layer||null,sources.map(([k])=>k),videoDuration(edl)]);
    if(force||key!==layerKey){
      const form=q('edit-layer-form');form.elements.source_id.replaceChildren(...sources.map(([k,s])=>new Option(s.original_name||s.path,k)));
      const start=Math.min(cursor(),Math.max(0,videoDuration(edl)-1/edl.output.fps)),source=sources[0];
      values(form,layer||{source_id:source?.[0]||'',in_seconds:0,out_seconds:Math.min(source?.[1].duration||0,2,videoDuration(edl)-start),start_seconds:start,speed:1,x:.65,y:.05,width:.3,height:.3,opacity:1});form.elements.fit.value=layer?.fit||'pad';form.elements.motion_enabled.checked=Boolean(layer?.motion);form.elements.motion_dx.value=layer?.motion?.dx??0;form.elements.motion_dy.value=layer?.motion?.dy??0;form.elements.motion_duration.value=layer?.motion?.duration_seconds??1;layerKey=key;
    }
    q('edit-layer-remove').disabled=!layer;q('edit-layer-lower').disabled=!layer||edl.layers.indexOf(layer)===0;
    q('edit-layer-raise').disabled=!layer||edl.layers.indexOf(layer)===edl.layers.length-1;
    q('edit-layer-form').querySelector('[type=submit]').disabled=!sources.length||videoDuration(edl)<=0;
    keyframes.draw();
  }
  function draw(){
    drawSelection();q('edit-layers-panel').hidden=!has('layers');const id=q('edit-layer-select').value;
    q('edit-layer-select').replaceChildren(new Option('Nueva capa',''),...(getEdl().layers||[]).map((l,i)=>new Option((i+1)+' · '+l.start_seconds.toFixed(3)+' s',l.id)));
    q('edit-layer-select').value=id;drawLayer();
  }
  q('edit-transition-form').onsubmit=e=>{e.preventDefault();run('transition',{id:getSelection().id,type:'dip_black',duration_seconds:Number(e.target.elements.duration_seconds.value)});};
  q('edit-transition-remove').onclick=()=>run('transition',{id:getSelection().id,type:'none'});
  q('edit-layer-select').onchange=()=>drawLayer(true);
  q('edit-layer-cursor').onclick=()=>{q('edit-layer-form').elements.start_seconds.value=cursor();};
  q('edit-layer-form').elements.source_id.onchange=()=>{const f=q('edit-layer-form'),source=getEdl().sources[f.elements.source_id.value];values(f,{in_seconds:0,out_seconds:Math.min(source.duration,2,videoDuration(getEdl())-Number(f.elements.start_seconds.value))});};
  q('edit-layer-form').onsubmit=async e=>{
    e.preventDefault();const id=q('edit-layer-select').value,old=new Set((getEdl().layers||[]).map(l=>l.id)),data={source_id:e.target.elements.source_id.value};
    for(const k of ['in_seconds','out_seconds','start_seconds','speed','x','y','width','height','opacity'])data[k]=Number(e.target.elements[k].value);
    data.fit=e.target.elements.fit.value;data.motion=e.target.elements.motion_enabled.checked?{dx:Number(e.target.elements.motion_dx.value),dy:Number(e.target.elements.motion_dy.value),duration_seconds:Number(e.target.elements.motion_duration.value),phase_seconds:getEdl().layers?.find(l=>l.id===id)?.motion?.phase_seconds||0}:null;if(id)data.id=id;await run(id?'layer_update':'layer_add',data);
    if(!id){const layer=(getEdl().layers||[]).find(l=>!old.has(l.id));if(layer)selectLayer(layer.id);}
  };
  q('edit-layer-remove').onclick=()=>run('layer_remove',{id:q('edit-layer-select').value});
  for(const [id,delta]of [['edit-layer-lower',-1],['edit-layer-raise',1]])q(id).onclick=()=>{const layer=getEdl().layers.find(l=>l.id===q('edit-layer-select').value);run('layer_move',{id:layer.id,index:getEdl().layers.indexOf(layer)+delta});};
  function selectLayer(id){q('edit-layers-panel').open=true;q('edit-layer-select').value=id;drawLayer(true);q('edit-layer-form').elements.in_seconds.focus();}
  return {draw,drawSelection,selectLayer};
}
