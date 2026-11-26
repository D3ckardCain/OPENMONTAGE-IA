import {makePeaks,paintPeaks} from './editor-waveform.js';
import {videoDuration} from './editor-time.js';

export function initializeSfx({host,getProject,getEdl,getRevision,has,cursor,insert,recover,favorite}){
  const open=document.createElement('button');open.type='button';open.id='edit-sfx-open';open.textContent='Efectos sonoros · catálogo';open.hidden=true;host.append(open);
  const drag=document.createElement('button');drag.type='button';drag.id='edit-sfx-drag';drag.hidden=true;drag.draggable=true;host.append(drag);
  const dialog=document.createElement('dialog');dialog.className='sfx-window';dialog.setAttribute('aria-labelledby','sfx-heading');
  dialog.innerHTML=`<header><h2 id="sfx-heading">Efectos sonoros locales</h2><button type="button" data-close>Cerrar</button></header><p>Preescuchar no modifica el montaje. Sonidos existentes, sin generación ni descargas.</p><div class="sfx-search"><label>Buscar ES/EN<input type="search" data-query maxlength="200"></label><label>Categoría<select data-category><option value="">Todas</option></select></label><label><input type="checkbox" data-favorites> Favoritos de este proyecto</label></div><p role="status" data-status></p><div class="sfx-transport"><audio controls preload="none"></audio><button type="button" data-stop>Detener preescucha</button><span data-playing>Sin preescucha</span></div><section class="sfx-selection"><strong data-selected>Selecciona un efecto</strong><label>Inicio en montaje (s)<input data-start type="number" min="0" step="0.001" value="0"></label><button type="button" data-cursor>Usar cursor</button><label>Entrada de fuente (s)<input data-in type="number" min="0" step="0.001" value="0"></label><label>Salida de fuente (s)<input data-out type="number" min="0" step="0.001" value="0"></label><label>Ganancia<input data-gain type="number" min="0" max="4" step="0.05" value="1"></label><button type="button" data-add disabled>Añadir al montaje</button><button type="button" data-recover hidden>Recuperar inserción</button><button type="button" data-wave disabled>Ver forma de onda</button><canvas width="640" height="60" hidden aria-label="Forma de onda de la fuente seleccionada"></canvas></section><div class="sfx-results" role="region" aria-label="Tarjetas de efectos"></div><button type="button" data-more hidden>Mostrar más efectos</button>`;
  document.body.append(dialog);const q=s=>dialog.querySelector(s),audio=q('audio');let items=[],selected=null,playing=null,busy=false,sequence=0,total=0,project=null,timer=null,categories=false;
  const peaks=new Map(),message=text=>q('[data-status]').textContent=text;
  const fresh=nodeButton('Nueva inserción tras recuperación');fresh.hidden=true;q('.sfx-selection').append(fresh);
  const prepareDrag=nodeButton('Preparar arrastre a audio');q('.sfx-selection').append(prepareDrag);prepareDrag.onclick=()=>{if(!selected){message('Selecciona un efecto primero.');return;}dialog.close();drag.focus();};
  drag.ondragstart=event=>{if(!selected)return;event.dataTransfer.setData('application/x-openmontage-sfx',JSON.stringify({id:selected.id}));};
  drag.onclick=()=>{dialog.showModal();};
  function nodeButton(text){const b=document.createElement('button');b.type='button';b.textContent=text;return b;}
  const tokenKey=()=> 'studio-sfx-insertion:'+getProject();let memoryToken=null;
  const token=()=>{try{return JSON.parse(sessionStorage.getItem(tokenKey()))||memoryToken;}catch{return memoryToken;}};
  function remember(value){memoryToken=value;try{value?sessionStorage.setItem(tokenKey(),JSON.stringify(value)):sessionStorage.removeItem(tokenKey());}catch{/* server receipt remains authoritative */}}
  function buttons(){q('[data-add]').disabled=busy||!selected?.available||!getProject()||Boolean(token());q('[data-wave]').disabled=!selected?.available||busy;q('[data-recover]').hidden=!token();q('[data-recover]').disabled=busy;}
  function stop(){audio.pause();audio.removeAttribute('src');audio.load();playing=null;q('[data-playing]').textContent='Sin preescucha';}
  function choose(row){if(selected?.id!==row.id)stop();selected=row;drag.textContent='Arrastrar a audio: '+row.name;drag.hidden=!getProject();q('[data-selected]').textContent=row.name+' · '+row.duration.toFixed(3)+' s';q('[data-start]').value=(getProject()?cursor():0).toFixed(3);q('[data-in]').value=0;q('[data-out]').value=Math.min(row.duration,getProject()?Math.max(0,videoDuration(getEdl())-cursor()):row.duration).toString();q('canvas').hidden=true;for(const card of q('.sfx-results').children)card.setAttribute('aria-selected',String(card.dataset.sfxId===row.id));buttons();}
  async function play(row){
    if(playing!==row.id){stop();audio.src=row.audio_url;playing=row.id;}
    q('[data-playing]').textContent=row.name;
    try{await audio.play();}catch(error){message('Preescucha no disponible: '+error.message);}
  }
  audio.onerror=()=>message('Audio ausente, unidad no disponible o formato no reproducible. El proyecto se conserva.');
  const node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
  function card(row){
    const box=node('article','');box.className='sfx-card';box.dataset.sfxId=row.id;box.setAttribute('aria-selected',String(selected?.id===row.id));
    box.append(node('h3',row.name),node('p',row.category_es+' · '+row.duration.toFixed(3)+' s · '+row.channels+' canal(es) · '+row.sample_rate+' Hz'),node('p',row.library+' · '+row.license+' (declaración del paquete)'));
    const author=row.aliases[0],link=node('a',author.author);link.href=author.source_url;link.target='_blank';link.rel='noopener noreferrer';box.append(link);
    if(!row.available)box.append(node('p',row.reason));
    const controls=node('div','');controls.className='sfx-card-actions';
    const button=(label,fn)=>{const b=node('button',label);b.type='button';b.disabled=!row.available;b.onclick=fn;controls.append(b);return b;};
    button('Reproducir',()=>play(row));button('Pausar',()=>{if(playing===row.id)audio.pause();});button('Detener',()=>{if(playing===row.id)stop();});
    const select=button('Seleccionar',()=>choose(row));select.title='Selecciona y usa Preparar arrastre a audio para descubrir la pista';
    const fav=button('Favorito',async()=>{try{const ids=new Set(getEdl().sfx_favorites||[]);ids.has(row.id)?ids.delete(row.id):ids.add(row.id);await favorite([...ids]);fav.setAttribute('aria-pressed',String(ids.has(row.id)));if(q('[data-favorites]').checked)await load();}catch(error){message(error.message);}});fav.disabled=!getProject();fav.setAttribute('aria-pressed',String(getProject()&&(getEdl().sfx_favorites||[]).includes(row.id)));
    box.append(controls);return box;
  }
  async function load(more=false){
    const serial=++sequence;const offset=more?items.length:0;
    const params=new URLSearchParams({q:q('[data-query]').value,category:q('[data-category]').value,offset:String(offset),limit:'24',favorites:String(q('[data-favorites]').checked),project_id:getProject()||''});
    message('Consultando catálogo local…');
    try{const response=await fetch('/api/studio/editor/sfx?'+params),value=await response.json();if(!response.ok)throw Error(value.detail||'No se pudo consultar el catálogo');if(serial!==sequence)return;
      if(!categories){for(const [id,label]of Object.entries(value.categories))q('[data-category]').add(new Option(label,id));categories=true;}
      items=more?[...items,...value.items]:value.items;total=value.total;
      if(!more)q('.sfx-results').replaceChildren();for(const row of value.items)q('.sfx-results').append(card(row));q('[data-more]').hidden=items.length>=total;
      message(items.length+' de '+total+' efectos · '+(value.reason||'Contenido local; no se analiza ni convierte al abrir.'));buttons();
    }catch(error){if(serial===sequence)message(error.message);}
  }
  open.onclick=()=>{dialog.showModal();load();};q('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',stop);q('[data-stop]').onclick=stop;
  q('[data-query]').oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>load(),200);};q('[data-category]').onchange=()=>load();q('[data-favorites]').onchange=()=>load();q('[data-more]').onclick=()=>load(true);
  q('[data-cursor]').onclick=()=>{if(!getProject()){message('Selecciona un proyecto para insertar.');return;}q('[data-start]').value=cursor().toFixed(3);if(selected)q('[data-out]').value=Math.min(selected.duration,Math.max(0,videoDuration(getEdl())-cursor())).toString();};
  async function add(row,startOverride){
    if(busy||token()||!row)return;busy=true;buttons();const pid=getProject();
    const start=startOverride??Number(q('[data-start]').value),first=startOverride===undefined?Number(q('[data-in]').value):0,last=startOverride===undefined?Number(q('[data-out]').value):Math.min(row.duration,videoDuration(getEdl())-start);
    const payload={request_id:crypto.randomUUID(),revision:getRevision(),asset_id:row.id,start_seconds:start,in_seconds:first,out_seconds:last,gain:Number(q('[data-gain]').value)};
    remember({pid,request_id:payload.request_id});
    try{await insert(payload);remember(null);const text='Efecto añadido en '+start.toFixed(3)+' s · fuente '+first.toFixed(3)+'–'+last.toFixed(3)+' s. Recorte, ganancia y fades siguen en el inspector de audio.';message(text);if(!dialog.open&&document.getElementById('edit-message'))document.getElementById('edit-message').textContent=text;}
    catch(error){message('Respuesta de inserción incierta o rechazada: '+error.message+' Recupera antes de repetir.');}
    finally{busy=false;buttons();}
  }
  q('[data-add]').onclick=()=>add(selected);
  q('[data-recover]').onclick=async()=>{const receipt=token();if(!receipt||busy)return;busy=true;buttons();try{const value=await recover(receipt.request_id);remember(null);fresh.hidden=true;message(value.sfx_receipt.currently_applied?'Inserción recuperada sin duplicar.':'Recibo completado; la inserción ya fue deshecha. No se repite.');}catch(error){fresh.hidden=error.status!==404;message('Recuperación: '+error.message+' El token se conserva.'+(error.status===404?' Puedes preparar una nueva inserción explícita.':''));}finally{busy=false;buttons();}};
  fresh.onclick=()=>{remember(null);fresh.hidden=true;buttons();message('Nueva inserción preparada; se conserva el formulario.');};
  q('[data-wave]').onclick=async()=>{if(!selected)return;const row=selected;try{let data=peaks.get(row.sha256);if(!data){const response=await fetch(row.audio_url);if(!response.ok)throw Error('No se pudo leer el sonido');const context=new AudioContext();try{const buffer=await context.decodeAudioData(await response.arrayBuffer());data=makePeaks(buffer.getChannelData(0),buffer.sampleRate);}finally{await context.close();}peaks.set(row.sha256,data);if(peaks.size>10)peaks.delete(peaks.keys().next().value);}if(row.id===selected?.id){q('canvas').hidden=false;paintPeaks(q('canvas'),data);}}catch(error){message('Forma de onda no disponible: '+error.message);}};
  const tracks=document.getElementById('edit-tracks');
  tracks.addEventListener('dragover',event=>{if(event.dataTransfer.types.includes('application/x-openmontage-sfx')&&event.target.closest('.editor-audio'))event.preventDefault();});
  tracks.addEventListener('drop',event=>{if(!event.dataTransfer.types.includes('application/x-openmontage-sfx'))return;const lane=event.target.closest('.editor-audio');if(!lane)return;event.preventDefault();event.stopImmediatePropagation();try{const data=JSON.parse(event.dataTransfer.getData('application/x-openmontage-sfx')),row=items.find(x=>x.id===data.id)||(selected?.id===data.id?selected:null);if(!row)return;const seconds=(event.clientX-lane.getBoundingClientRect().left)/Number(document.getElementById('edit-zoom').value);add(row,Math.max(0,Math.min(videoDuration(getEdl()),seconds)));}catch(error){message(error.message);}},true);
  function draw(){open.hidden=!has('sfx_catalog');if(project!==getProject()){stop();if(dialog.open)dialog.close();selected=null;drag.hidden=true;memoryToken=null;fresh.hidden=true;project=getProject();buttons();}}
  return {draw};
}
