import { initializePiperUI } from './editor-piper-ui.js';
import { initializeQwenUI } from './editor-qwen.js';
import { initializeComponentsUI } from './editor-components.js';
import { initializeSfx } from './editor-sfx.js';
import { initializeMixMeter } from './editor-mix-meter.js';
import { appendVolumeAutomation } from './editor-volume-automation.js';
import { initializeSubtitleLayout } from './editor-subtitle-layout.js';
import { initializeSubtitleKaraoke } from './editor-subtitle-karaoke.js';
// Shared server revision is authoritative. No browser-only project fork.
import { initializeEditorLayout } from './editor-layout.js';
import { timelineEnd,videoDuration,fitZoom,tickStep,clipStart,sourceTime,splitAtCursor,snapTime,editPoints,trimByDelta,moveCue,clipDuration,previewMatches,audioTrimByDelta,sourceToTimeline } from './editor-time.js';
import { makePeaks,paintPeaks,signalLevel } from './editor-waveform.js';
import { initializeEffectsUI } from './editor-effects-ui.js';
import { initializeCompositionUI } from './editor-composition-ui.js';
import { compatibilityReady,compatibilityState } from './studio-compatibility.js';
import { initializeCandidatesUI } from './editor-candidates-ui.js';
import { initializeCropPreview } from './editor-crop-preview.js';
import { languageSelection,languageParams } from './editor-subtitle-language.js';
const q = id => document.getElementById(id);
let project = new URLSearchParams(location.search).get('edit'), state = null, selection = null;
let preview = null, sourceKey = null, renderTimer = null, pending = false, workspace = location.hash.slice(1) || 'video';
let cursor=0, zoomMode='fit', ruler=null, edgeGesture=null;
let effectsUI=null;
let finalMixMeter=null;
let subtitleLayout=null;
let subtitleKaraoke=null;
let compositionUI=null;
let candidatesUI=null,cropPreview=null,qwenPanel=null,componentsUI=null,sfxPanel=null;
let cancelSupported=false,renderAttempt=null;
const capabilities=new Set(),selectedIds=new Set();
async function loadCapabilities(){
  applyCapabilities(await compatibilityReady);
}
function applyCapabilities(result){
  capabilities.clear();cancelSupported=result.caps?.render_cancel===true;
  if(result.ok){for(const name of result.caps.commands)capabilities.add(name);}
  if(q('edit-ripple-volume-label'))q('edit-ripple-volume-label').hidden=!capabilities.has('ripple_volume_points');
  q('edit-advanced-tools').hidden=!capabilities.has('batch');q('edit-flags-panel').hidden=!capabilities.has('flags');q('edit-markers-panel').hidden=!capabilities.has('markers');
}
const waveformCache=new Map();let waveformQueue=Promise.resolve(),waveformSelection=0;
document.addEventListener('studio-compatibility',event=>applyCapabilities(event.detail));
let meterContext=null,meterSource=null,meterAnalyser=null,meterEnabled=false,meterFrame=0,meterSamples=null,lastMeter='Sin medición';
function meterLoop(){
  cancelAnimationFrame(meterFrame);if(!meterEnabled)return;
  if(q('edit-player').paused){q('edit-meter-level').textContent='Detenido · '+lastMeter;return;}
  meterAnalyser.getFloatTimeDomainData(meterSamples);const level=signalLevel(meterSamples);
  lastMeter=`RMS ${level.dbfs.toFixed(1)} dBFS · pico ${level.peak>0?(20*Math.log10(level.peak)).toFixed(1):'-96'} dBFS (mono)`;
  q('edit-meter').hidden=false;q('edit-meter').value=Math.min(0,level.dbfs);q('edit-meter-level').textContent=lastMeter;
  meterFrame=requestAnimationFrame(meterLoop);
}
q('edit-meter-toggle').onclick=async()=>{
  const button=q('edit-meter-toggle');button.disabled=true;
  try{
    if(meterEnabled){meterEnabled=false;cancelAnimationFrame(meterFrame);q('edit-meter').hidden=true;q('edit-meter-level').textContent='Medidor desactivado';}
    else{
      if(!meterContext){meterContext=new AudioContext();meterSource=meterContext.createMediaElementSource(q('edit-player'));meterAnalyser=meterContext.createAnalyser();meterAnalyser.fftSize=2048;meterSamples=new Float32Array(meterAnalyser.fftSize);meterSource.connect(meterAnalyser);meterAnalyser.connect(meterContext.destination);}
      await meterContext.resume();meterEnabled=true;meterLoop();
    }
  }catch(error){meterEnabled=false;q('edit-meter-level').textContent='Medidor no disponible: '+error.message;if(meterSource&&meterContext){try{meterSource.disconnect();meterSource.connect(meterContext.destination);await meterContext.resume();}catch{/* keep error visible */}}}
  finally{button.disabled=false;button.setAttribute('aria-pressed',String(meterEnabled));button.textContent=meterEnabled?'Desactivar medidor':'Activar medidor';}
};
q('edit-player').addEventListener('play',()=>{if(meterEnabled)meterLoop();});
q('edit-player').addEventListener('pause',()=>{cancelAnimationFrame(meterFrame);if(meterEnabled)q('edit-meter-level').textContent='Detenido · '+lastMeter;});
function loadWaveform(key){
  const info=edl().sources[key],pid=project,cacheKey=pid+':'+info.sha256;
  if(waveformCache.has(cacheKey))return waveformCache.get(cacheKey);
  const promise=waveformQueue.then(async()=>{
    if(info.bytes>100000000||info.duration>300)throw Error('Límite local de waveform: 100 MB y 5 minutos por fuente. La reproducción sigue disponible.');
    const response=await fetch('/api/studio/editor/'+encodeURIComponent(pid)+'/source/'+encodeURIComponent(key));
    if(!response.ok)throw Error('No se pudo leer el audio local');
    const context=new AudioContext();
    try{const buffer=await context.decodeAudioData(await response.arrayBuffer());return makePeaks(buffer.getChannelData(0),buffer.sampleRate);}finally{await context.close();}
  });
  waveformQueue=promise.catch(()=>{});waveformCache.set(cacheKey,promise);
  if(waveformCache.size>4)waveformCache.delete(waveformCache.keys().next().value);
  return promise;
}
function addTrackWaveform(button,clip,index){
  const canvas=document.createElement('canvas');canvas.className='editor-track-waveform';canvas.width=Math.min(2048,Math.max(1,Math.ceil(seconds(clip)*Number(q('edit-zoom').value))));canvas.height=48;
  canvas.setAttribute('aria-hidden','true');canvas.hidden=true;button.prepend(canvas);
  const status=element('small','Forma de onda: '+(index<4?'decodificando…':'selecciona el clip'));status.className='editor-waveform-note';button.append(status);
  if(index>=4&&selection?.id!==clip.id)return;
  const pid=project;
  loadWaveform(clip.source_id).then(peaks=>{if(pid!==project||!canvas.isConnected)return;paintPeaks(canvas,peaks,clip.in_seconds,clip.out_seconds);canvas.hidden=false;status.textContent='Fuente · primer canal';}).catch(error=>{if(status.isConnected)status.textContent='Forma de onda no disponible';button.title=error.message;});
}
function storeView(){if(project)try{localStorage.setItem('edit-timeline-view:'+project,JSON.stringify({mode:zoomMode,zoom:Number(q('edit-zoom').value),cursor,snap:q('edit-snapping').checked}));}catch{/* optional */}}
function loadView(){
  cursor=0;zoomMode='fit';q('edit-snapping').checked=true;try{const v=JSON.parse(localStorage.getItem('edit-timeline-view:'+project));if(v){zoomMode=v.mode==='manual'?'manual':'fit';if(Number.isFinite(v.zoom)&&v.zoom>0)q('edit-zoom').value=Math.min(10000,v.zoom);if(Number.isFinite(v.cursor))cursor=Math.max(0,Math.min(timelineEnd(edl()),v.cursor));q('edit-snapping').checked=v.snap!==false;}}catch{/* optional */}
}
function fitTimeline(){if(!state)return;zoomMode='fit';q('edit-tracks').scrollLeft=0;drawTracks();storeView();}
function zoomTimeline(factor){if(!state)return;zoomMode='manual';q('edit-zoom').value=Math.max(.001,Math.min(Number(q('edit-zoom').max),Number(q('edit-zoom').value)*factor));drawTracks();storeView();}
function seekTimeline(time){
  if(!state||!Number.isFinite(time))return;cursor=Math.max(0,Math.min(timelineEnd(edl()),Math.round(time*edl().output.fps)/edl().output.fps));
  const p=q('edit-player');
  if(preview){if(cursor<=videoDuration(edl()))p.currentTime=cursor;else p.pause();}
  else if(sourceKey&&selection){try{const item=selected(),at=sourceTime(edl(),item.clip,item.track,cursor);if(sourceKey===item.clip.source_id&&at>=item.clip.in_seconds&&at<=item.clip.out_seconds)p.currentTime=at;}catch{/* selection removed */}}
  updatePlayhead();storeView();
}
const message = text => { q('edit-message').textContent = text; };
const element = (tag, text) => { const n = document.createElement(tag); n.textContent = text; return n; };
const seconds = c => clipDuration(c,edl(),c.kind==='gap'||edl().sources[c.source_id].kind==='video');
const edl = () => state.edit_decisions;
const base = () => '/api/studio/editor/' + encodeURIComponent(project);
async function api(path, data) {
  if(data!==undefined&&!path.endsWith('/render/cancel')&&!compatibilityState().ok)throw Error(compatibilityState().message);
  const response = await fetch(path, data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  const value = await response.json();
  if (!response.ok) {const error=Error(response.status===404 && path==='/api/studio/editor/projects' ? 'Esta instancia de Studio necesita reiniciarse para activar la API del editor. El espacio visual está preparado; las operaciones aún no están disponibles aquí.' : value.detail || 'Error de edición');error.status=response.status;throw error;}
  return value;
}
async function task(fn,propagate=false) {
  if (pending) {if(propagate)throw Error('Hay una operación pendiente');return;}
  pending = true;
  q('manual-editor').setAttribute('aria-busy', 'true');
  try { await fn(); } catch (error) { message(error.message);if(propagate)throw error; }
  finally { pending = false; q('manual-editor').removeAttribute('aria-busy'); }
}
function requireProject() { if(!compatibilityState().ok)throw Error(compatibilityState().message);if (!state || !project) throw Error('Selecciona o crea un proyecto de edición'); }
async function command(operation, params={}) {
  requireProject();
  if(operation==='silence_apply'&&capabilities.has('ripple_volume_points')&&!('move_volume_points' in params))params={...params,move_volume_points:q('edit-ripple-volume').checked};
  state = await api(base() + '/command', {operation, revision:state.revision, ...params});
  invalidate(); draw(); message('Guardado · revisión ' + state.revision);
}
function invalidate() {
  if (preview && !previewMatches(preview,state)) {
    q('edit-player').pause(); q('edit-player').removeAttribute('src'); q('edit-player').load();
    preview = null; q('edit-download').hidden = true;
    q('edit-monitor-title').textContent = 'Montaje modificado · prepara una nueva vista previa';
    q('edit-render-status').textContent = 'La revisión anterior no representa este montaje.';
  }
}
async function projects() {
  const values = await api('/api/studio/editor/projects');
  q('edit-project').replaceChildren(new Option('Selecciona un proyecto', ''), ...values.map(p => new Option(p.title, p.project_id)));
  q('edit-project').value = project || '';
}
async function reopen(id=project) {
  if (!id) throw Error('Selecciona un proyecto');
  const value = await api('/api/studio/editor/' + encodeURIComponent(id));
  project = id; state = value; selection = null;selectedIds.clear(); sourceKey = null; preview = null;lastMeter='Sin medici\u00f3n para este proyecto';q('edit-meter').hidden=true;q('edit-meter-level').textContent=lastMeter;
  q('edit-ripple-volume').checked=false;
  q('edit-player').pause(); q('edit-player').removeAttribute('src'); q('edit-player').load();
  q('edit-download').hidden=true;
  q('edit-monitor-title').textContent = 'Montaje reabierto · selecciona una fuente o prepara la vista previa';
  const url = new URL(location.href); url.searchParams.set('edit', project); history.replaceState(null, '', url);
  q('edit-project').value = project;effectsUI?.reset();candidatesUI?.reset();cropPreview?.reset(); loadView();draw(); await checkRender();
  message('Proyecto reabierto desde disco · revisión ' + state.revision);
}
async function importFiles(files) {
  requireProject();
  for (const file of files) {
    message('Importando ' + file.name + ' · se conserva el original');
    const response = await fetch(base() + '/upload?filename=' + encodeURIComponent(file.name) + '&revision=' + state.revision,
      {method:'POST', headers:{'Content-Type':'application/octet-stream'}, body:file});
    const value = await response.json(); if (!response.ok) throw Error(value.detail);
    state = value; invalidate(); draw();
  }
  message('Medios importados con procedencia. Pulsa Añadir para incluirlos en el montaje.');
}
function sourceUrl(key) { return base() + '/source/' + encodeURIComponent(key); }
function showSource(key, clip=null) {
  const info = edl().sources[key], player = q('edit-player');
  preview = null; sourceKey = key; player.src = sourceUrl(key); player.playbackRate = clip?.speed || 1;
  player.onloadedmetadata = () => { player.currentTime = clip?.in_seconds || 0; };
  q('edit-monitor-title').textContent = 'Fuente individual · ' + info.original_name;
  q('edit-render-status').textContent = 'Fuente individual; no incluye el montaje ni su mezcla. Prepara la vista previa para comprobarlos.';
  q('edit-download').hidden = true;
  if (workspace === 'audio' && info.audio) waveform(key);
}
function selected() {
  requireProject();
  if (!selection) throw Error('Selecciona un clip');
  const list = selection.track === 'audio' ? edl().audio_tracks : edl().cuts;
  const clip = list.find(c => c.id === selection.id);
  if (!clip) throw Error('El clip ya no existe');
  return {list, clip, ...selection};
}
function selectClip(clip, track, event=null) {
  const extend=capabilities.has('batch')&&selection?.track===track&&event;
  if(extend&&event.shiftKey){const items=track==='audio'?edl().audio_tracks:edl().cuts;const a=items.findIndex(c=>c.id===selection.id),b=items.indexOf(clip);for(const c of items.slice(Math.min(a,b),Math.max(a,b)+1))selectedIds.add(c.id);}
  else if(extend&&(event.ctrlKey||event.metaKey)){if(selectedIds.has(clip.id))selectedIds.delete(clip.id);else selectedIds.add(clip.id);}
  else{selectedIds.clear();selectedIds.add(clip.id);}
  selection=selectedIds.size?{id:selectedIds.has(clip.id)?clip.id:[...selectedIds].at(-1),track}:null;
  q('edit-clip-tools').open=true; drawInspector(); drawTracks();
  if(workspace==='audio'&&clip.kind!=='gap'&&edl().sources[clip.source_id].audio)waveform(clip.source_id);
}
function drawInspector() {
  effectsUI?.drawSelection();compositionUI?.drawSelection();
  cropPreview?.selectionChanged();
  const form = q('edit-clip-form'); let item;
  for(const id of ['edit-split','edit-split-cursor','edit-remove','edit-left','edit-right','edit-view-source'])q(id).disabled=true;
  for(const id of ['edit-duplicate','edit-delete-gap','edit-delete-ripple'])q(id).disabled=true;
  q('edit-selection-count').textContent=selectedIds.size?selectedIds.size+' clips · '+selection?.track:'Sin selección';
  try { item = selected(); } catch { form.hidden = true; q('edit-selection').textContent = 'Selecciona un clip en las pistas.'; return; }
  const locked=Boolean(item.clip.locked),items=item.track==='audio'?edl().audio_tracks:edl().cuts,anyLocked=items.some(c=>selectedIds.has(c.id)&&c.locked);
  q('edit-split').disabled=q('edit-remove').disabled=locked;
  q('edit-split-cursor').disabled=locked;q('edit-view-source').disabled=item.clip.kind==='gap';
  q('edit-duplicate').disabled=q('edit-delete-gap').disabled=anyLocked||!selectedIds.size;q('edit-delete-ripple').disabled=anyLocked||item.track!=='video';
  form.hidden = false; const c = item.clip;
  q('edit-selection').textContent = (c.kind==='gap'?'Vacío negro/silencio':edl().sources[c.source_id].original_name) + ' · ' + item.track;
  for (const key of ['in_seconds','out_seconds','speed','gain','fade_in','fade_out','start_seconds']) form.elements[key].value = c[key];
  form.elements.muted.checked = c.muted;
  form.elements.solo.checked=Boolean(c.solo);form.elements.locked.checked=locked;
  form.querySelector('button:not([type=button])').disabled=locked;q('edit-clip-settings').disabled=locked;
  form.elements.split.value = ((c.in_seconds + c.out_seconds) / 2).toFixed(3);
  q('edit-audio-start').hidden = item.track !== 'audio';
  q('edit-left').disabled = locked||item.list.indexOf(c) === 0;
  q('edit-right').disabled = locked||item.list.indexOf(c) === item.list.length - 1;
  q('edit-remove').textContent=item.track==='video'?'Quitar y cerrar hueco':'Quitar audio';
}
function addTrimHandles(button,clip,track){
  button.dataset.clipId=clip.id;
  if(clip.locked)return;
  for(const edge of track==='video'||capabilities.has('audio_trim_position')?['in','out']:['out']){
    const paramsFor=delta=>track==='audio'&&edge==='in'?audioTrimByDelta(edl(),clip,delta):trimByDelta(edl(),clip,track,edge,delta);
    const save=params=>command(track==='audio'&&edge==='in'?'audio_trim_position':'trim',params);
    const handle=element('span','');handle.className='editor-trim-handle editor-trim-'+edge;handle.tabIndex=0;
    handle.dataset.focus='edge:'+track+':'+clip.id+':'+edge;
    handle.draggable=false;handle.setAttribute('role','slider');handle.setAttribute('aria-label',`${track} ${clip.id}: recortar ${edge==='in'?'entrada':'salida'}`);
    handle.setAttribute('aria-valuemin','0');handle.setAttribute('aria-valuemax',String(clip.kind==='gap'?clip.gap_duration:edl().sources[clip.source_id].duration));handle.setAttribute('aria-valuenow',String(clip[edge+'_seconds']));
    handle.title=track==='video'?'Recorte con cierre de hueco · flechas: un fotograma · Mayús: un segundo':edge==='in'?'Recortar entrada de audio y mover su inicio atómicamente':'Recortar salida de audio · conserva su posición';
    handle.onclick=event=>{event.preventDefault();event.stopPropagation();};
    const cancel=()=>{edgeGesture=null;document.documentElement.classList.remove('editor-edge-drag');drawTracks();};
    handle.onpointerdown=event=>{
      if(event.button!==0||pending)return;event.preventDefault();event.stopPropagation();
      selection={id:clip.id,track};selectedIds.clear();selectedIds.add(clip.id);q('edit-clip-tools').open=true;drawInspector();
      for(const node of q('edit-tracks').querySelectorAll('[data-clip-id]'))node.setAttribute('aria-pressed',String(node.dataset.clipId===clip.id));
      edgeGesture={x:event.clientX,params:null,cancel};handle.setPointerCapture(event.pointerId);document.documentElement.classList.add('editor-edge-drag');
    };
    handle.onpointermove=event=>{
      if(!edgeGesture||!handle.hasPointerCapture(event.pointerId))return;
      const zoom=Number(q('edit-zoom').value),initial=clipStart(edl(),clip,track)+(edge==='out'?seconds(clip):0);
      const raw=initial+(event.clientX-edgeGesture.x)/zoom,time=snapTime(raw,editPoints(edl(),cursor,raw),zoom,q('edit-snapping').checked);
      const params=paramsFor(time-initial);edgeGesture.params=params;
      button.style.width=Math.max(10,(params.out_seconds-params.in_seconds)/clip.speed*zoom)+'px';
      if(track==='audio'&&edge==='in')button.style.left=(params.start_seconds*zoom)+'px';
      message('Recorte '+params.in_seconds.toFixed(3)+'–'+params.out_seconds.toFixed(3)+' s de fuente · suelta para guardar · Esc cancela');
    };
    handle.onpointerup=event=>{
      if(!edgeGesture)return;event.stopPropagation();const params=edgeGesture.params;edgeGesture=null;document.documentElement.classList.remove('editor-edge-drag');
      if(params&&(params.in_seconds!==clip.in_seconds||params.out_seconds!==clip.out_seconds))task(async()=>{try{await save(params);}finally{drawTracks();}});else drawTracks();
    };
    handle.onpointercancel=cancel;
    handle.onkeydown=event=>{
      if(!['ArrowLeft','ArrowRight'].includes(event.key))return;event.preventDefault();event.stopPropagation();
      const delta=(event.key==='ArrowRight'?1:-1)*(event.shiftKey?1:1/edl().output.fps);
      task(()=>save(paramsFor(delta)));
    };button.append(handle);
  }
}
function drawTracks() {
  const box = q('edit-tracks'),focus=box.contains(document.activeElement)?document.activeElement.dataset.focus:null; box.replaceChildren();
  const end=timelineEnd(edl());
  q('edit-zoom').max=Math.min(10000,5000000/Math.max(1,end));
  if(zoomMode==='fit')q('edit-zoom').value=fitZoom(edl(),box.clientWidth);
  const zoom=Number(q('edit-zoom').value),width=Math.max(box.clientWidth-2,end*zoom+48);
  ruler=element('div','');ruler.className='editor-ruler';ruler.style.width=width+'px';
  ruler.dataset.focus='ruler';
  ruler.tabIndex=0;ruler.setAttribute('role','slider');ruler.setAttribute('aria-valuemin','0');ruler.setAttribute('aria-valuemax',String(end));
  ruler.setAttribute('aria-label','Regla temporal del montaje en segundos');
  box.append(ruler);
  const seek=event=>seekTimeline((event.clientX-ruler.getBoundingClientRect().left)/Number(q('edit-zoom').value));
  ruler.onpointerdown=event=>{if(event.button!==0)return;event.preventDefault();ruler.setPointerCapture(event.pointerId);ruler.focus();seek(event);};
  ruler.onpointermove=event=>{if(ruler.hasPointerCapture(event.pointerId))seek(event);};
  ruler.onkeydown=event=>{let next=cursor;if(event.key==='Home')next=0;else if(event.key==='End')next=end;else if(event.key==='ArrowLeft')next-=event.shiftKey?1:1/edl().output.fps;else if(event.key==='ArrowRight')next+=event.shiftKey?1:1/edl().output.fps;else return;event.preventDefault();seekTimeline(next);};
  for (const [track, title, clips] of [['video','Vídeo · cortes secuenciales',edl().cuts],['audio','Audio · tiempos independientes',edl().audio_tracks]]) {
    box.append(element('h3', title)); const lane = element('div',''); lane.className = 'editor-lane editor-' + track;
    lane.style.width=width+'px';
    lane.style.backgroundSize=(Number(q('edit-zoom').value)*5)+'px 100%';
    const dropAudio=(event,from)=>task(()=>{
      const clip=edl().audio_tracks.find(c=>c.id===from.id);if(!clip)throw Error('El clip de audio de origen no está en este proyecto.');
      const zoom=Number(q('edit-zoom').value),raw=(event.clientX-lane.getBoundingClientRect().left)/zoom-(from.grabSeconds||0);
      const start_seconds=Math.max(0,snapTime(raw,editPoints(edl(),cursor,raw),zoom,q('edit-snapping').checked));
      return command('clip',{id:clip.id,track:'audio',start_seconds});
    });
    lane.ondragover=event=>event.preventDefault();
    lane.ondrop=event=>{event.preventDefault();const from=JSON.parse(event.dataTransfer.getData('application/x-openmontage-clip'));if(from.track!==track){message('No se puede cambiar el tipo de pista arrastrando');return;}if(track==='audio')dropAudio(event,from);else task(()=>command('move',{...from,index:clips.length-1}));};
    let start = 0;
    for (let index = 0; index < clips.length; index++) {
      const clip = clips[index], button = element('button', (clip.kind==='gap'?'Vacío negro/silencio':edl().sources[clip.source_id].original_name) + '\n' + seconds(clip).toFixed(3) + ' s' + (clip.muted ? ' · silencio' : '')+(clip.locked?' · bloqueado':''));
      button.type = 'button'; button.className = 'editor-clip'; button.draggable = true;
      button.dataset.focus='clip:'+track+':'+clip.id;
      button.style.width = Math.max(10, seconds(clip) * Number(q('edit-zoom').value)) + 'px';
      if(track==='audio'){button.style.left=(clip.start_seconds*Number(q('edit-zoom').value))+'px';button.style.top=(index*64+8)+'px';}
      button.title = 'Inicio: ' + (track === 'audio' ? clip.start_seconds : start).toFixed(3) + ' s · seleccionar para editar';
      if(track==='video'&&clip.kind!=='gap'){const thumb=document.createElement('video');thumb.muted=true;thumb.preload='metadata';thumb.src=sourceUrl(clip.source_id)+'#t='+clip.in_seconds;thumb.setAttribute('aria-hidden','true');button.prepend(thumb);}
      button.setAttribute('aria-pressed', String(selectedIds.has(clip.id)));
      if(track==='audio')addTrackWaveform(button,clip,index);
      button.onclick = event => selectClip(clip, track,event);
      if(clip.locked)button.draggable=false;
      button.ondragstart = event => {if(event.target.closest('.editor-trim-handle')){event.preventDefault();return;}event.dataTransfer.setData('application/x-openmontage-clip', JSON.stringify({id:clip.id, track,grabSeconds:(event.clientX-button.getBoundingClientRect().left)/Number(q('edit-zoom').value)}));};
      button.ondragover = event => event.preventDefault();
      button.ondrop = event => { event.preventDefault();event.stopPropagation();const from=JSON.parse(event.dataTransfer.getData('application/x-openmontage-clip'));if(track==='audio'&&from.track==='audio'){dropAudio(event,from);return;} task(async () => {
        if (from.track !== track) throw Error('No se puede cambiar el tipo de pista arrastrando');
        await command('move', {...from, index});
      }); };
      addTrimHandles(button,clip,track);lane.append(button); start += seconds(clip);
    }
    if (!clips.length) lane.append(element('p','Añade un medio desde la biblioteca.'));
    if(track==='audio'&&clips.length){const scale=element('div','');scale.className='editor-audio-scale';scale.style.width=(Math.max(...clips.map(c=>c.start_seconds+seconds(c)))*Number(q('edit-zoom').value))+'px';lane.append(scale);lane.style.height=(clips.length*64+16)+'px';}
    const head=element('div','');head.className='editor-playhead';head.setAttribute('aria-hidden','true');lane.append(head);
    box.append(lane);
    appendVolumeAutomation({box,track,width,zoom,edl:edl(),has:name=>capabilities.has(name),run:(op,params)=>task(()=>command(op,params),true),cursor:()=>cursor,project});
  }
  box.append(element('h3','Subtítulos · tiempos del montaje'));
  const cues=element('div','');cues.className='editor-lane editor-cues';cues.style.width=width+'px';
  cues.ondragover=event=>{if(event.dataTransfer.types.includes('application/x-openmontage-cue'))event.preventDefault();};
  cues.ondrop=event=>{
    if(!event.dataTransfer.types.includes('application/x-openmontage-cue'))return;event.preventDefault();
    task(()=>{const from=JSON.parse(event.dataTransfer.getData('application/x-openmontage-cue')),cue=edl().cues[from.index];if(!cue)throw Error('Subtítulo de origen no encontrado.');
      const zoom=Number(q('edit-zoom').value),raw=(event.clientX-cues.getBoundingClientRect().left)/zoom-from.grabSeconds;
      const time=snapTime(raw,editPoints(edl(),cursor,raw),zoom,q('edit-snapping').checked);q('edit-cue-index').value=from.index+1;
      return command('cue_update',{index:from.index,...moveCue(edl(),cue,time)});
    });
  };
  for(const [index,cue] of edl().cues.entries()){
    const button=element('button',cue.text);button.type='button';button.className='editor-clip';
    button.dataset.focus='cue:'+index;
    button.style.left=(cue.start_seconds*zoom)+'px';button.style.width=Math.max(10,(cue.end_seconds-cue.start_seconds)*zoom)+'px';
    button.title=`Subtítulo ${index+1} · ${cue.start_seconds}–${cue.end_seconds} s · editar debajo de pistas`;
    button.setAttribute('aria-label',`Editar subtítulo ${index+1}: ${cue.text}`);
    button.draggable=true;button.ondragstart=event=>event.dataTransfer.setData('application/x-openmontage-cue',JSON.stringify({index,grabSeconds:(event.clientX-button.getBoundingClientRect().left)/Number(q('edit-zoom').value)}));
    button.onclick=()=>{
      document.querySelector('.editor-menu [data-section="subtitles"]').click();q('edit-cue-index').value=index+1;
      drawCueInspector();q('edit-cue-form').elements.text.focus();
      seekTimeline(cue.start_seconds);
    };cues.append(button);
  }
  if(!edl().cues.length)cues.append(element('p','Sin subtítulos; importa o edita SRT debajo de las pistas.'));
  const head=element('div','');head.className='editor-playhead';head.setAttribute('aria-hidden','true');cues.append(head);box.append(cues);
  if(edl().titles?.length){
    box.append(element('h3','Títulos · texto visible'));const lane=element('div','');lane.className='editor-lane editor-cues editor-titles';lane.style.width=width+'px';
    for(const title of edl().titles){const button=element('button',title.text);button.type='button';button.className='editor-clip';button.style.left=(title.start_seconds*zoom)+'px';button.style.width=Math.max(10,(title.end_seconds-title.start_seconds)*zoom)+'px';button.onclick=()=>{effectsUI?.selectTitle(title.id);seekTimeline(title.start_seconds);};lane.append(button);}box.append(lane);
  }
  for(const [index,layer]of (edl().layers||[]).entries()){
    box.append(element('h3','Capa visual '+(index+1)));const lane=element('div','');lane.className='editor-lane editor-cues editor-layers';lane.style.width=width+'px';
    const button=element('button',edl().sources[layer.source_id].original_name||'Capa');button.type='button';button.className='editor-clip';button.style.left=(layer.start_seconds*zoom)+'px';button.style.width=Math.max(10,(layer.out_seconds-layer.in_seconds)/layer.speed*zoom)+'px';button.onclick=()=>{compositionUI?.selectLayer(layer.id);seekTimeline(layer.start_seconds);};lane.append(button);box.append(lane);
  }
  const rows=3+Math.max(0,edl().audio_tracks.length-1)+(edl().titles?.length?1:0)+(edl().layers?.length||0);
  if(q('manual-editor').dataset.timelineRows!==String(rows)){q('manual-editor').dataset.timelineRows=rows;window.dispatchEvent(new Event('studio-tracks-layout'));}
  const note=q('edit-timeline-note'),tail=end-videoDuration(edl());note.hidden=tail<.02;
  note.textContent=tail>=.02?'Colas fuera del vídeo: '+tail.toFixed(3)+' s. La salida actual termina con el vídeo; ajusta esas pistas antes de exportar.':'';
  box.onscroll=drawRuler;drawRuler();updatePlayhead();
  if(focus)box.querySelector('[data-focus="'+CSS.escape(focus)+'"]')?.focus({preventScroll:true});
}
function drawRuler(){
  if(!state||!ruler)return;const box=q('edit-tracks'),zoom=Number(q('edit-zoom').value),tick=tickStep(zoom,edl().output.fps);
  ruler.replaceChildren();
  const start=Math.floor(box.scrollLeft/zoom/tick)*tick,end=Math.min(timelineEnd(edl()),(box.scrollLeft+box.clientWidth)/zoom);
  for(let t=start,n=0;t<=end+1e-7&&n<200;n++,t+=tick){const label=element('span',Number(t.toFixed(3))+' s');label.style.left=(t*zoom)+'px';ruler.append(label);}
  const head=element('div','');head.className='editor-playhead';head.style.left=(cursor*zoom)+'px';ruler.append(head);
  for(const marker of edl().markers||[]){
    const x=marker.seconds*zoom;if(x<box.scrollLeft-10||x>box.scrollLeft+box.clientWidth+10)continue;
    const button=element('button','▼');button.type='button';button.className='editor-marker';button.style.left=x+'px';button.title=marker.label+' · '+marker.seconds.toFixed(3)+' s';button.setAttribute('aria-label','Ir al marcador '+(marker.label||marker.seconds));
    button.onpointerdown=event=>event.stopPropagation();button.onclick=event=>{event.stopPropagation();seekTimeline(marker.seconds);q('edit-marker-select').value=marker.id;drawMarkerInspector();};ruler.append(button);
  }
}
function updatePlayhead(){
  if(!state)return;cursor=Math.min(cursor,timelineEnd(edl()));
  for(const head of document.querySelectorAll('.editor-playhead'))head.style.left=(cursor*Number(q('edit-zoom').value))+'px';
  if(ruler){ruler.setAttribute('aria-valuenow',String(cursor));ruler.setAttribute('aria-valuetext',cursor.toFixed(3)+' segundos');}
}
function formatSrt(cues) {
  const stamp = s => new Date(Math.round(s * 1000)).toISOString().slice(11,23).replace('.', ',');
  return cues.map((c,i) => `${i+1}\n${stamp(c.start_seconds)} --> ${stamp(c.end_seconds)}\n${c.text}\n`).join('\n');
}
function drawCueInspector(){
  if(!state)return;const form=q('edit-cue-form'),cue=edl().cues[Number(q('edit-cue-index').value)-1];
  form.hidden=!cue;if(!cue)return;
  for(const key of ['start_seconds','end_seconds','text'])form.elements[key].value=cue[key];
}
function drawMarkerInspector(){
  const marker=(edl().markers||[]).find(m=>m.id===q('edit-marker-select').value);
  q('edit-marker-time').value=marker?.seconds??cursor;q('edit-marker-label').value=marker?.label||'';
  for(const id of ['edit-marker-save','edit-marker-remove','edit-marker-go'])q(id).disabled=!marker;
}
function pruneSelection(){
  if(!selection){selectedIds.clear();return;}
  const items=selection.track==='audio'?edl().audio_tracks:edl().cuts;
  for(const id of selectedIds)if(!items.some(c=>c.id===id))selectedIds.delete(id);
  if(!items.some(c=>c.id===selection.id))selection=selectedIds.size?{...selection,id:[...selectedIds][0]}:null;
}
function draw() {
  subtitleKaraoke?.draw();
  subtitleLayout?.draw();
  finalMixMeter?.draw();
  sfxPanel?.draw();
  candidatesUI?.draw();cropPreview?.selectionChanged();qwenPanel?.draw();componentsUI?.draw();
  q('edit-revision').textContent = 'Revisión ' + state.revision + ' · guardado local';
  q('edit-undo').disabled = !state.undo.length; q('edit-redo').disabled = !state.redo.length;
  const list = q('edit-sources'); list.replaceChildren();
  for (const [key, info] of Object.entries(edl().sources)) {
    const item = element('div',''); item.className = 'editor-source';const name=element('strong',info.original_name);name.title=info.original_name;item.append(name);
    if (info.kind === 'video') { const image = document.createElement('video'); image.preload='metadata'; image.muted=true; image.src=sourceUrl(key)+'#t=0.1'; image.setAttribute('aria-label','Miniatura de '+info.original_name); item.append(image); }
    item.append(element('small', info.kind + ' · ' + info.duration.toFixed(3) + ' s · ' + info.bytes + ' bytes'));
    const play = element('button','Ver fuente'); play.onclick = () => showSource(key);
    const add = element('button','Añadir a pista'); add.onclick = () => task(() => command('add',{source_id:key}));
    item.append(play, add);
    const provenance = element('details',''); provenance.append(element('summary','Procedencia'),element('small',info.path+' · SHA256 '+info.sha256+' · '+info.imported_at)); item.append(provenance); list.append(item);
  }
  pruneSelection();drawTracks(); drawInspector();
  q('edit-duration').textContent = edl().cuts.reduce((total,c) => total+seconds(c),0).toFixed(3) + ' s de montaje';
  q('edit-preset').value = edl().output.ratio; q('edit-fps').value = edl().output.fps;
  q('edit-srt').value = formatSrt(edl().cues); q('edit-srt-download').href = base() + '/subtitles';
  q('edit-ass-download').href = base() + '/subtitles.ass';
  q('edit-subtitle-mode').value = edl().subtitle_style.mode;
  q('edit-subtitle-language').value=languageSelection(edl().subtitle_style);
  q('edit-subtitle-language-label').hidden=!capabilities.has('subtitle_language');
  q('edit-subtitle-size').value = edl().subtitle_style.size;
  q('edit-subtitle-position').value = edl().subtitle_style.position;
  q('edit-cps').replaceChildren(...edl().cues.map((c,i) => element('p', `#${i+1}: ${(c.text.replace(/\s/g,'').length/(c.end_seconds-c.start_seconds)).toFixed(1)} caracteres/s`)));
  drawCueInspector();
  const selectedMarker=q('edit-marker-select').value;
  q('edit-marker-select').replaceChildren(new Option('Selecciona marcador',''),...(edl().markers||[]).map(m=>new Option(m.seconds.toFixed(3)+' s · '+m.label,m.id)));
  q('edit-marker-select').value=selectedMarker;drawMarkerInspector();
  effectsUI?.draw();compositionUI?.draw();
  q('edit-events').replaceChildren(...state.events.slice(-12).reverse().map(e => element('p',`r${e.revision} · ${e.origin} · ${e.operation} · ${e.at}`)));
}
async function checkRender() {
  if (!project || !state) return;
  const captured = project, result = await api(base() + '/render'); if (captured !== project) return;
  renderAttempt=result.attempt;const active=['running','cancelling'].includes(result.status);
  q('edit-render-cancel').hidden=!cancelSupported||!active;q('edit-render-cancel').disabled=result.status==='cancelling';
  const subtitles = result.subtitle_mode === 'burn' ? 'texto visible quemado' : result.subtitle_mode === 'mov_text' ? 'subtítulos seleccionables, sin estilo quemado' : 'sin subtítulos incorporados';
  q('edit-render-status').textContent = result.status === 'running' ? 'FFmpeg está preparando el montaje; no se puede editar durante el render.' : result.status === 'failed' || result.status === 'interrupted' ? result.error : result.status === 'completed' ? (result.current ? 'Montaje de revisión ' + result.revision + (result.preview ? ' · vista previa a media resolución' : ' · exportación final local') + ' · ' + subtitles : 'Resultado anterior: prepara la revisión actual.') : 'Sin montaje renderizado.';
  if(result.status==='cancelling')q('edit-render-status').textContent='Cancelando FFmpeg; el proyecto seguirá ocupado hasta confirmar la salida del proceso.';
  if(result.status==='cancelled')q('edit-render-status').textContent='Render cancelado; el parcial no se publica. Puedes volver a preparar el montaje sin repetir ediciones.';
  q('edit-preview').disabled = q('edit-export').disabled = active;
  if(result.status!=='completed'||!result.current)q('edit-download').hidden=true;
  if (result.status === 'completed' && result.current && previewMatches(result,state)) {
    if (preview?.attempt !== result.attempt) {
      preview = result; sourceKey = null; q('edit-player').src=result.url; q('edit-player').playbackRate=1;
      const seek=cursor,pid=project;
      q('edit-player').onloadedmetadata = ()=>{if(project===pid&&preview?.attempt===result.attempt)q('edit-player').currentTime=Math.min(seek,videoDuration(edl()));};
      q('edit-monitor-title').textContent='Montaje real · revisión '+result.revision;
    }
    q('edit-download').hidden=false; q('edit-download').href=result.url;
  }
  clearTimeout(renderTimer);
  if (active) renderTimer=setTimeout(() => task(checkRender),1500);
}
async function render(previewOnly) {
  requireProject(); await api(base()+'/render',{revision:state.revision,preview:previewOnly}); await checkRender();
}
async function waveform(key) {
  const canvas=q('edit-waveform'),status=q('edit-waveform-status'),pid=project,token=++waveformSelection;
  canvas.hidden=true;q('edit-waveform-retry').hidden=true;status.hidden=false;status.textContent='Decodificando audio local para forma de onda…';
  try{
    const peaks=await loadWaveform(key);if(pid!==project||token!==waveformSelection)return;
    paintPeaks(canvas,peaks);canvas.hidden=false;status.textContent='Forma de onda real · primer canal · fuente completa, sin efectos ni mezcla.';
    canvas.onclick=event=>{const time=(event.offsetX/canvas.clientWidth)*peaks.duration;
      if(sourceKey===key)q('edit-player').currentTime=time;
      else if(selection){const item=selected();seekTimeline(sourceToTimeline(edl(),item.clip,item.track,Math.max(item.clip.in_seconds,Math.min(item.clip.out_seconds,time))));}
    };
  }catch(error){if(pid===project&&token===waveformSelection){status.textContent='Forma de onda no disponible: '+error.message;q('edit-waveform-retry').hidden=edl().sources[key].duration>300||edl().sources[key].bytes>100000000;q('edit-waveform-retry').dataset.source=key;}}
}
q('edit-waveform-retry').onclick=async()=>{const key=q('edit-waveform-retry').dataset.source;if(!state||!edl().sources[key])return;waveformCache.delete(project+':'+edl().sources[key].sha256);await waveform(key);drawTracks();};
q('edit-create').onclick=()=>task(async()=>{const title=prompt('Título del nuevo montaje');if(!title)return;const result=await api('/api/studio/editor/projects',{title});project=result.project_id;await projects();await reopen();});
q('edit-project').onchange=event=>task(()=>reopen(event.target.value));
q('edit-reopen').onclick=()=>task(()=>reopen());
q('edit-save').onclick=()=>task(()=>command('save'));
q('edit-undo').onclick=()=>task(()=>command('undo'));q('edit-redo').onclick=()=>task(()=>command('redo'));
q('edit-import').onchange=event=>task(()=>importFiles(event.target.files));
q('edit-register').onclick=()=>task(async()=>{requireProject();state=await api(base()+'/register',{revision:state.revision,relative_path:q('edit-relative').value});invalidate();draw();message('Medio registrado sin mover el original.');});
const library=document.querySelector('.editor-library');library.ondragover=event=>event.preventDefault();library.ondrop=event=>{event.preventDefault();task(()=>importFiles(event.dataTransfer.files));};
q('edit-clip-form').onsubmit=event=>{event.preventDefault();task(()=>{const item=selected(),f=event.target;return command('trim',{id:item.id,track:item.track,in_seconds:Number(f.elements.in_seconds.value),out_seconds:Number(f.elements.out_seconds.value)});});};
q('edit-split').onclick=()=>task(()=>{const item=selected();return command('split',{id:item.id,track:item.track,at:Number(q('edit-clip-form').elements.split.value)});});
q('edit-remove').onclick=()=>task(()=>{const item=selected();return command('remove',{id:item.id,track:item.track});});
for(const [id,delta] of [['edit-left',-1],['edit-right',1]])q(id).onclick=()=>task(()=>{const item=selected();return command('move',{id:item.id,track:item.track,index:item.list.indexOf(item.clip)+delta});});
q('edit-clip-settings').onclick=()=>task(()=>{const item=selected(),f=q('edit-clip-form'),params={id:item.id,track:item.track,muted:f.elements.muted.checked};for(const k of ['speed','gain','fade_in','fade_out','start_seconds'])params[k]=Number(f.elements[k].value);return command('clip',params);});
q('edit-flags-apply').onclick=()=>task(()=>{const item=selected(),f=q('edit-clip-form');return command('flags',{id:item.id,track:item.track,muted:f.elements.muted.checked,solo:f.elements.solo.checked,locked:f.elements.locked.checked});});
q('edit-duplicate').onclick=()=>task(async()=>{
  const item=selected(),before=new Set((item.track==='audio'?edl().audio_tracks:edl().cuts).map(c=>c.id));
  await command('duplicate',{track:item.track,ids:[...selectedIds]});
  selectedIds.clear();for(const clip of item.track==='audio'?edl().audio_tracks:edl().cuts)if(!before.has(clip.id))selectedIds.add(clip.id);
  selection={track:item.track,id:[...selectedIds][0]};drawTracks();drawInspector();
});
const rippleVolumeLabel=document.createElement('label');rippleVolumeLabel.id='edit-ripple-volume-label';rippleVolumeLabel.hidden=true;rippleVolumeLabel.title='Solo cierre global de vídeo y aplicación de silencios: elimina puntos del tramo, desplaza los posteriores y conserva bordes con transición de una muestra. Desactivado: tiempos absolutos.';const rippleVolume=document.createElement('input');rippleVolume.type='checkbox';rippleVolume.id='edit-ripple-volume';rippleVolumeLabel.append(rippleVolume,document.createTextNode('Ripple: mover puntos de volumen'));q('edit-advanced-tools').append(rippleVolumeLabel);
for(const [id,operation] of [['edit-delete-gap','delete_keep_gap'],['edit-delete-ripple','ripple_delete']])q(id).onclick=()=>task(()=>{const item=selected(),params={track:item.track,ids:[...selectedIds]};if(operation==='ripple_delete'&&capabilities.has('ripple_volume_points'))params.move_volume_points=rippleVolume.checked;return command(operation,params);});
q('edit-marker-add').onclick=()=>task(async()=>{
  requireProject();const before=new Set((edl().markers||[]).map(m=>m.id));
  await command('marker_add',{seconds:cursor,label:'Marcador '+(before.size+1)});
  q('edit-marker-select').value=edl().markers.find(m=>!before.has(m.id)).id;drawMarkerInspector();
});
q('edit-marker-select').onchange=drawMarkerInspector;
q('edit-marker-go').onclick=()=>seekTimeline(Number(q('edit-marker-time').value));
q('edit-marker-save').onclick=()=>task(()=>command('marker_update',{id:q('edit-marker-select').value,seconds:Number(q('edit-marker-time').value),label:q('edit-marker-label').value}));
q('edit-marker-remove').onclick=()=>task(()=>command('marker_remove',{id:q('edit-marker-select').value}));
q('edit-output').onclick=()=>task(()=>command('output',{ratio:q('edit-preset').value,fps:Number(q('edit-fps').value)}));
q('edit-preview').onclick=()=>task(()=>render(true));q('edit-export').onclick=()=>task(()=>render(false));
q('edit-render-cancel').onclick=()=>task(async()=>{requireProject();await api(base()+'/render/cancel',{attempt:renderAttempt});await checkRender();});
q('edit-play').onclick=()=>task(async()=>{const p=q('edit-player');if(!p.currentSrc)throw Error('Selecciona una fuente o prepara la vista previa');if(p.paused)await p.play();else p.pause();});
q('edit-show-montage').onclick=()=>task(async()=>{requireProject();await checkRender();if(!preview)message('El montaje actual aún no tiene vista previa guardada. Usa Preparar vista previa del montaje.');});
q('edit-player').ontimeupdate=()=>{const p=q('edit-player');if(preview)cursor=p.currentTime||0;else if(selection&&state){try{const item=selected();if(sourceKey===item.clip.source_id)cursor=sourceToTimeline(edl(),item.clip,item.track,Math.max(item.clip.in_seconds,p.currentTime));}catch{/* removed */}}q('edit-time').textContent=new Date(Math.max(0,p.currentTime)*1000).toISOString().slice(11,23);q('edit-caption').textContent=preview?.subtitle_mode==='mov_text'?(edl().cues.find(c=>c.start_seconds<=p.currentTime&&p.currentTime<c.end_seconds)?.text||''):'';if(!preview&&selection){try{const item=selected();if(sourceKey===item.clip.source_id&&p.currentTime>=item.clip.out_seconds)p.pause();}catch{/* selection removed */}}updatePlayhead();};
q('edit-player').onerror=()=>message('El navegador no pudo reproducir este archivo. Puedes preparar la vista previa MP4 con FFmpeg; no se modifica el original.');
q('edit-srt-import').onchange=event=>task(async()=>{requireProject();const f=event.target.files[0];if(!f)return;if(f.size>500000)throw Error('SRT superior a 500 KB');const response=await fetch(base()+'/subtitles/import?filename='+encodeURIComponent(f.name)+'&revision='+state.revision,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:f});const value=await response.json();if(!response.ok)throw Error(value.detail);state=value;invalidate();draw();message('SRT importado y validado; se conservan sus bytes originales. Aplica los cambios posteriores del campo SRT por separado.');});
q('edit-srt-save').onclick=()=>task(()=>command('subtitles',{srt:q('edit-srt').value}));
q('edit-cue-index').oninput=drawCueInspector;
q('edit-cue-form').onsubmit=event=>{event.preventDefault();const f=event.target;task(()=>command('cue_update',{index:Number(q('edit-cue-index').value)-1,start_seconds:Number(f.elements.start_seconds.value),end_seconds:Number(f.elements.end_seconds.value),text:f.elements.text.value}));};
q('edit-cue-offset-apply').onclick=()=>task(()=>command('cue_offset',{seconds:Number(q('edit-cue-offset').value)}));
q('edit-cue-split').onclick=()=>task(()=>command('cue_split',{index:Number(q('edit-cue-index').value)-1,at:Number(q('edit-cue-at').value),text_index:Number(q('edit-cue-text-index').value)}));
q('edit-cue-merge').onclick=()=>task(()=>command('cue_merge',{index:Number(q('edit-cue-index').value)-1}));
q('edit-subtitle-style').onclick=()=>task(()=>command('subtitle_style',{size:Number(q('edit-subtitle-size').value),position:q('edit-subtitle-position').value,mode:q('edit-subtitle-mode').value,...languageParams(q('edit-subtitle-language').value,capabilities.has('subtitle_language'))}));
q('edit-zoom').oninput=()=>{zoomMode='manual';if(state)drawTracks();storeView();};
q('edit-snapping').onchange=storeView;
q('edit-fit').onclick=fitTimeline;q('edit-zoom-out').onclick=()=>zoomTimeline(1/1.25);q('edit-zoom-in').onclick=()=>zoomTimeline(1.25);
q('edit-view-source').onclick=()=>task(()=>{const item=selected();showSource(item.clip.source_id,item.clip);});
q('edit-split-cursor').onclick=()=>task(()=>{const item=selected();return command('split',splitAtCursor(edl(),item.clip,item.track,cursor));});
let measuredTimelineWidth=0;
new ResizeObserver(()=>{const width=q('edit-tracks').clientWidth;if(width===measuredTimelineWidth)return;measuredTimelineWidth=width;if(state&&zoomMode==='fit'&&!edgeGesture)drawTracks();}).observe(q('edit-tracks'));

function showWorkspace(){document.body.dataset.editorWorkspace=workspace;piperPanel.hidden=workspace!=='audio';waveformSelection++;q('edit-waveform-retry').hidden=true;q('edit-subtitle-panel').hidden=workspace!=='subtitles';q('edit-waveform').hidden=true;q('edit-waveform-status').hidden=workspace!=='audio';if(workspace==='audio'&&state){if(selection){try{const item=selected();if(item.clip.kind!=='gap'&&edl().sources[item.clip.source_id].audio)waveform(item.clip.source_id);}catch{/* removed */}}else if(sourceKey&&edl().sources[sourceKey].audio)waveform(sourceKey);}if(workspace==='library')q('edit-import').focus();if(workspace==='edit-projects')q('edit-project').focus();window.dispatchEvent(new Event('studio-tracks-layout'));}
window.addEventListener('studio-workspace',event=>{workspace=event.detail;showWorkspace();if(workspace==='edit-projects')projects().catch(error=>message(error.message));});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&edgeGesture){event.preventDefault();edgeGesture.cancel();return;}if(q('manual-editor').hidden||/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName))return;if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='d'&&capabilities.has('duplicate')&&selection){event.preventDefault();q('edit-duplicate').click();return;}if(event.key==='Delete'&&capabilities.has('batch')&&selection){event.preventDefault();q(event.shiftKey?'edit-delete-ripple':'edit-delete-gap').click();return;}if(event.ctrlKey||event.metaKey){if(event.key.toLowerCase()!=='z')return;}else if(!event.altKey){if(event.key.toLowerCase()==='m'&&capabilities.has('markers')){event.preventDefault();q('edit-marker-add').click();return;}const key=event.key.toLowerCase();if(key==='f'){event.preventDefault();fitTimeline();return;}if(key==='+'||key==='='){event.preventDefault();zoomTimeline(1.25);return;}if(key==='-'){event.preventDefault();zoomTimeline(1/1.25);return;}if(key==='s'){event.preventDefault();q('edit-split-cursor').click();return;}}if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='z'){event.preventDefault();task(()=>command(event.shiftKey?'redo':'undo'));}});
effectsUI=initializeEffectsUI({q,getEdl:edl,getProject:()=>project,getSelection:selected,run:(op,params)=>task(()=>command(op,params)),runBalance:(op,params)=>task(()=>command(op,params),true),has:name=>capabilities.has(name),cursor:()=>cursor});
finalMixMeter=initializeMixMeter({host:q('edit-mix-panel'),getProject:()=>project,getRevision:()=>state?.revision,getDigest:()=>state?.render_sha256,has:name=>capabilities.has(name)});
subtitleLayout=initializeSubtitleLayout({host:q('edit-cps'),getProject:()=>project,getEdl:edl,has:name=>capabilities.has(name),run:(op,params)=>task(()=>command(op,params),true),inspect:index=>{q('edit-cue-index').value=index+1;drawCueInspector();seekTimeline(edl().cues[index].start_seconds);}});
subtitleKaraoke=initializeSubtitleKaraoke({host:q('edit-cps'),getProject:()=>project,getEdl:edl,has:name=>capabilities.has(name),run:(op,params)=>task(()=>command(op,params),true),seek:seekTimeline});
candidatesUI=initializeCandidatesUI({q,getEdl:edl,getProject:()=>project,getRevision:()=>state?.revision,inspectWords:setId=>api(base()+'/subtitle-words?set_id='+encodeURIComponent(setId)),loadSubtitleDraft:setId=>api(base()+'/subtitle-draft?set_id='+encodeURIComponent(setId)),loadSilenceProposal:proposal=>api(base()+'/silence-proposal',proposal),run:(op,params)=>task(()=>command(op,params),true),has:name=>capabilities.has(name),reviewSource:showSource});
cropPreview=initializeCropPreview({q,getEdl:edl,getSelection:selected,sourceUrl});
compositionUI=initializeCompositionUI({q,getEdl:edl,getProject:()=>project,getSelection:selected,run:(op,params)=>task(()=>command(op,params)),runStrict:(op,params)=>task(()=>command(op,params),true),has:name=>capabilities.has(name),cursor:()=>cursor});
componentsUI=initializeComponentsUI({host:q('edit-sources').parentElement,getEdl:edl,getProject:()=>project,has:name=>capabilities.has(name),run:(op,params)=>task(()=>command(op,params),true),editTitle:id=>effectsUI.selectTitle(id),editLayer:id=>compositionUI.selectLayer(id)});
const piperPanel=initializePiperUI({host:q('edit-waveform-status').parentElement,getProject:()=>project,getRevision:()=>state.revision,reopen});
sfxPanel=initializeSfx({host:q('edit-waveform-status').parentElement,getProject:()=>project,getEdl:edl,getRevision:()=>state.revision,has:name=>capabilities.has(name),cursor:()=>cursor,
  insert:payload=>task(async()=>{state=await api(base()+'/sfx/insert',payload);invalidate();draw();},true),
  recover:async id=>{let value;await task(async()=>{value=await api(base()+'/sfx/requests/'+encodeURIComponent(id));state=value;invalidate();draw();},true);return value;},
  favorite:ids=>task(()=>command('sfx_favorites',{ids}),true)});
qwenPanel=initializeQwenUI({host:q('edit-waveform-status').parentElement,getEdl:edl,getProject:()=>project,getRevision:()=>state.revision,run:(op,params)=>task(()=>command(op,params),true),registerPreview:relative=>task(async()=>{requireProject();if(Object.values(edl().sources).some(s=>s.path===relative))return;state=await api(base()+'/register',{revision:state.revision,relative_path:relative});invalidate();draw();},true)});
initializeEditorLayout();
showWorkspace();task(async()=>{try{await loadCapabilities();await projects();if(project)await reopen();}catch(error){for(const control of q('manual-editor').querySelectorAll('button,input,select,textarea'))control.disabled=true;throw error;}});


