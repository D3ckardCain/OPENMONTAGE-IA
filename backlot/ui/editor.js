// Shared server revision is authoritative. No browser-only project fork.
import { initializeEditorLayout } from './editor-layout.js';
import { timelineEnd,videoDuration,fitZoom,tickStep,clipStart,sourceTime,splitAtCursor } from './editor-time.js';
const q = id => document.getElementById(id);
let project = new URLSearchParams(location.search).get('edit'), state = null, selection = null;
let preview = null, sourceKey = null, renderTimer = null, pending = false, workspace = location.hash.slice(1) || 'video';
let cursor=0, zoomMode='fit', ruler=null;
function storeView(){if(project)try{localStorage.setItem('edit-timeline-view:'+project,JSON.stringify({mode:zoomMode,zoom:Number(q('edit-zoom').value),cursor}));}catch{/* optional */}}
function loadView(){
  cursor=0;zoomMode='fit';try{const v=JSON.parse(localStorage.getItem('edit-timeline-view:'+project));if(v){zoomMode=v.mode==='manual'?'manual':'fit';if(Number.isFinite(v.zoom)&&v.zoom>0)q('edit-zoom').value=Math.min(10000,v.zoom);if(Number.isFinite(v.cursor))cursor=Math.max(0,Math.min(timelineEnd(edl()),v.cursor));}}catch{/* optional */}
}
function fitTimeline(){if(!state)return;zoomMode='fit';q('edit-tracks').scrollLeft=0;drawTracks();storeView();}
function zoomTimeline(factor){if(!state)return;zoomMode='manual';q('edit-zoom').value=Math.max(.001,Math.min(Number(q('edit-zoom').max),Number(q('edit-zoom').value)*factor));drawTracks();storeView();}
function seekTimeline(time){
  if(!state)return;cursor=Math.max(0,Math.min(timelineEnd(edl()),Math.round(time*edl().output.fps)/edl().output.fps));
  const p=q('edit-player');
  if(preview){if(cursor<=videoDuration(edl()))p.currentTime=cursor;else p.pause();}
  else if(sourceKey&&selection){try{const item=selected(),at=sourceTime(edl(),item.clip,item.track,cursor);if(sourceKey===item.clip.source_id&&at>=item.clip.in_seconds&&at<=item.clip.out_seconds)p.currentTime=at;}catch{/* selection removed */}}
  updatePlayhead();storeView();
}
const message = text => { q('edit-message').textContent = text; };
const element = (tag, text) => { const n = document.createElement(tag); n.textContent = text; return n; };
const seconds = c => {const raw=(c.out_seconds-c.in_seconds)/c.speed;return edl().sources[c.source_id].kind==='video'?Math.round(raw*edl().output.fps)/edl().output.fps:raw;};
const edl = () => state.edit_decisions;
const base = () => '/api/studio/editor/' + encodeURIComponent(project);
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  const value = await response.json();
  if (!response.ok) throw Error(response.status===404 && path==='/api/studio/editor/projects' ? 'Esta instancia de Studio necesita reiniciarse para activar la API del editor. El espacio visual está preparado; las operaciones aún no están disponibles aquí.' : value.detail || 'Error de edición');
  return value;
}
async function task(fn) {
  if (pending) return;
  pending = true;
  q('manual-editor').setAttribute('aria-busy', 'true');
  try { await fn(); } catch (error) { message(error.message); }
  finally { pending = false; q('manual-editor').removeAttribute('aria-busy'); }
}
function requireProject() { if (!state || !project) throw Error('Selecciona o crea un proyecto de edición'); }
async function command(operation, params={}) {
  requireProject();
  state = await api(base() + '/command', {operation, revision:state.revision, ...params});
  invalidate(); draw(); message('Guardado · revisión ' + state.revision);
}
function invalidate() {
  if (preview && !(preview.edit_sha256 && state.edit_sha256 ? preview.edit_sha256 === state.edit_sha256 : preview.revision === state.revision)) {
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
  project = id; state = value; selection = null; sourceKey = null; preview = null;
  q('edit-player').pause(); q('edit-player').removeAttribute('src'); q('edit-player').load();
  q('edit-monitor-title').textContent = 'Montaje reabierto · selecciona una fuente o prepara la vista previa';
  const url = new URL(location.href); url.searchParams.set('edit', project); history.replaceState(null, '', url);
  q('edit-project').value = project; loadView();draw(); await checkRender();
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
function selectClip(clip, track) {
  selection = {id:clip.id, track}; q('edit-clip-tools').open=true; drawInspector(); drawTracks();
  if(workspace==='audio'&&edl().sources[clip.source_id].audio)waveform(clip.source_id);
}
function drawInspector() {
  const form = q('edit-clip-form'); let item;
  for(const id of ['edit-split','edit-split-cursor','edit-remove','edit-left','edit-right','edit-view-source'])q(id).disabled=true;
  try { item = selected(); } catch { form.hidden = true; q('edit-selection').textContent = 'Selecciona un clip en las pistas.'; return; }
  q('edit-split').disabled=q('edit-remove').disabled=false;
  q('edit-split-cursor').disabled=q('edit-view-source').disabled=false;
  form.hidden = false; const c = item.clip;
  q('edit-selection').textContent = edl().sources[c.source_id].original_name + ' · ' + item.track;
  for (const key of ['in_seconds','out_seconds','speed','gain','fade_in','fade_out','start_seconds']) form.elements[key].value = c[key];
  form.elements.muted.checked = c.muted;
  form.elements.split.value = ((c.in_seconds + c.out_seconds) / 2).toFixed(3);
  q('edit-audio-start').hidden = item.track !== 'audio';
  q('edit-left').disabled = item.list.indexOf(c) === 0;
  q('edit-right').disabled = item.list.indexOf(c) === item.list.length - 1;
}
function drawTracks() {
  const box = q('edit-tracks'); box.replaceChildren();
  const end=timelineEnd(edl());
  q('edit-zoom').max=Math.min(10000,5000000/Math.max(1,end));
  if(zoomMode==='fit')q('edit-zoom').value=fitZoom(edl(),box.clientWidth);
  const zoom=Number(q('edit-zoom').value),width=Math.max(box.clientWidth-2,end*zoom+48);
  ruler=element('div','');ruler.className='editor-ruler';ruler.style.width=width+'px';
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
    let start = 0;
    for (let index = 0; index < clips.length; index++) {
      const clip = clips[index], button = element('button', edl().sources[clip.source_id].original_name + '\n' + seconds(clip).toFixed(3) + ' s' + (clip.muted ? ' · silencio' : ''));
      button.type = 'button'; button.className = 'editor-clip'; button.draggable = true;
      button.style.width = Math.max(10, seconds(clip) * Number(q('edit-zoom').value)) + 'px';
      if(track==='audio'){button.style.left=(clip.start_seconds*Number(q('edit-zoom').value))+'px';button.style.top=(index*64+8)+'px';}
      button.title = 'Inicio: ' + (track === 'audio' ? clip.start_seconds : start).toFixed(3) + ' s · seleccionar para editar';
      if(track==='video'){const thumb=document.createElement('video');thumb.muted=true;thumb.preload='metadata';thumb.src=sourceUrl(clip.source_id)+'#t='+clip.in_seconds;thumb.setAttribute('aria-hidden','true');button.prepend(thumb);}
      button.setAttribute('aria-pressed', String(selection?.id === clip.id));
      button.onclick = () => selectClip(clip, track);
      button.ondragstart = event => event.dataTransfer.setData('application/x-openmontage-clip', JSON.stringify({id:clip.id, track}));
      button.ondragover = event => event.preventDefault();
      button.ondrop = event => { event.preventDefault(); task(async () => {
        const from = JSON.parse(event.dataTransfer.getData('application/x-openmontage-clip'));
        if (from.track !== track) throw Error('No se puede cambiar el tipo de pista arrastrando');
        await command('move', {...from, index});
      }); };
      lane.append(button); start += seconds(clip);
    }
    if (!clips.length) lane.append(element('p','Añade un medio desde la biblioteca.'));
    if(track==='audio'&&clips.length){const scale=element('div','');scale.className='editor-audio-scale';scale.style.width=(Math.max(...clips.map(c=>c.start_seconds+seconds(c)))*Number(q('edit-zoom').value))+'px';lane.append(scale);lane.style.height=(clips.length*64+16)+'px';}
    const cursor=element('div','');cursor.className='editor-playhead';cursor.setAttribute('aria-hidden','true');lane.append(cursor);
    box.append(lane);
  }
  box.append(element('h3','Subtítulos · tiempos del montaje'));
  const cues=element('div','');cues.className='editor-lane editor-cues';cues.style.width=width+'px';
  for(const [index,cue] of edl().cues.entries()){
    const button=element('button',cue.text);button.type='button';button.className='editor-clip';
    button.style.left=(cue.start_seconds*zoom)+'px';button.style.width=Math.max(10,(cue.end_seconds-cue.start_seconds)*zoom)+'px';
    button.title=`Subtítulo ${index+1} · ${cue.start_seconds}–${cue.end_seconds} s · editar debajo de pistas`;
    button.setAttribute('aria-label',`Editar subtítulo ${index+1}: ${cue.text}`);
    button.onclick=()=>{
      document.querySelector('.editor-menu [data-section="subtitles"]').click();q('edit-cue-index').value=index+1;
      const input=q('edit-srt'),at=input.value.indexOf(cue.text);input.focus();if(at>=0)input.setSelectionRange(at,at+cue.text.length);
      seekTimeline(cue.start_seconds);
    };cues.append(button);
  }
  if(!edl().cues.length)cues.append(element('p','Sin subtítulos; importa o edita SRT debajo de las pistas.'));
  const cursor=element('div','');cursor.className='editor-playhead';cursor.setAttribute('aria-hidden','true');cues.append(cursor);box.append(cues);
  const note=q('edit-timeline-note'),tail=end-videoDuration(edl());note.hidden=tail<.02;
  note.textContent=tail>=.02?'Colas fuera del vídeo: '+tail.toFixed(3)+' s. La salida actual termina con el vídeo; ajusta esas pistas antes de exportar.':'';
  box.onscroll=drawRuler;drawRuler();updatePlayhead();
}
function drawRuler(){
  if(!state||!ruler)return;const box=q('edit-tracks'),zoom=Number(q('edit-zoom').value),tick=tickStep(zoom,edl().output.fps);
  ruler.replaceChildren();
  const start=Math.floor(box.scrollLeft/zoom/tick)*tick,end=Math.min(timelineEnd(edl()),(box.scrollLeft+box.clientWidth)/zoom);
  for(let t=start,n=0;t<=end+1e-7&&n<200;n++,t+=tick){const label=element('span',Number(t.toFixed(3))+' s');label.style.left=(t*zoom)+'px';ruler.append(label);}
  const head=element('div','');head.className='editor-playhead';head.style.left=(cursor*zoom)+'px';ruler.append(head);
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
function draw() {
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
  drawTracks(); drawInspector();
  q('edit-duration').textContent = edl().cuts.reduce((total,c) => total+seconds(c),0).toFixed(3) + ' s de montaje';
  q('edit-preset').value = edl().output.ratio; q('edit-fps').value = edl().output.fps;
  q('edit-srt').value = formatSrt(edl().cues); q('edit-srt-download').href = base() + '/subtitles';
  q('edit-ass-download').href = base() + '/subtitles.ass';
  q('edit-subtitle-mode').value = edl().subtitle_style.mode;
  q('edit-subtitle-size').value = edl().subtitle_style.size;
  q('edit-subtitle-position').value = edl().subtitle_style.position;
  q('edit-cps').replaceChildren(...edl().cues.map((c,i) => element('p', `#${i+1}: ${(c.text.replace(/\s/g,'').length/(c.end_seconds-c.start_seconds)).toFixed(1)} caracteres/s`)));
  q('edit-events').replaceChildren(...state.events.slice(-12).reverse().map(e => element('p',`r${e.revision} · ${e.origin} · ${e.operation} · ${e.at}`)));
}
async function checkRender() {
  if (!project || !state) return;
  const captured = project, result = await api(base() + '/render'); if (captured !== project) return;
  const subtitles = result.subtitle_mode === 'burn' ? 'texto visible quemado' : result.subtitle_mode === 'mov_text' ? 'subtítulos seleccionables, sin estilo quemado' : 'sin subtítulos incorporados';
  q('edit-render-status').textContent = result.status === 'running' ? 'FFmpeg está preparando el montaje; no se puede editar durante el render.' : result.status === 'failed' || result.status === 'interrupted' ? result.error : result.status === 'completed' ? (result.current ? 'Montaje de revisión ' + result.revision + (result.preview ? ' · vista previa a media resolución' : ' · exportación final local') + ' · ' + subtitles : 'Resultado anterior: prepara la revisión actual.') : 'Sin montaje renderizado.';
  q('edit-preview').disabled = q('edit-export').disabled = result.status === 'running';
  if (result.status === 'completed' && result.current && (result.edit_sha256 && state.edit_sha256 ? result.edit_sha256 === state.edit_sha256 : result.revision === state.revision)) {
    if (preview?.attempt !== result.attempt) {
      preview = result; sourceKey = null; q('edit-player').src=result.url; q('edit-player').playbackRate=1;
      q('edit-player').onloadedmetadata = null; q('edit-monitor-title').textContent='Montaje real · revisión '+result.revision;
    }
    q('edit-download').hidden=false; q('edit-download').href=result.url;
  }
  clearTimeout(renderTimer);
  if (result.status === 'running') renderTimer=setTimeout(() => task(checkRender),1500);
}
async function render(previewOnly) {
  requireProject(); await api(base()+'/render',{revision:state.revision,preview:previewOnly}); await checkRender();
}
async function waveform(key) {
  const canvas=q('edit-waveform'), status=q('edit-waveform-status'); canvas.hidden=true; status.hidden=false;
  const info=edl().sources[key], captured=project,capturedSelection=selection?.id;
  if (info.bytes > 100_000_000) { status.textContent='Forma de onda no disponible para archivos mayores de 100 MB. La reproducción sigue disponible.'; return; }
  let context;
  try {
    status.textContent='Decodificando audio local para la forma de onda…';
    const response=await fetch(sourceUrl(key)); if(!response.ok)throw Error('No se pudo leer el audio');
    context=new AudioContext(); const buffer=await context.decodeAudioData(await response.arrayBuffer());
    if(captured!==project || (sourceKey!==key&&selection?.id!==capturedSelection))return;
    const channel=buffer.getChannelData(0), ctx=canvas.getContext('2d'), step=Math.max(1,Math.ceil(channel.length/canvas.width));
    ctx.clearRect(0,0,canvas.width,canvas.height); ctx.strokeStyle='#3fb950'; ctx.beginPath();
    for(let x=0;x<canvas.width;x++){let min=1,max=-1; for(let i=x*step;i<Math.min(channel.length,(x+1)*step);i++){min=Math.min(min,channel[i]);max=Math.max(max,channel[i]);}ctx.moveTo(x,(1+min)*70);ctx.lineTo(x,(1+max)*70);}ctx.stroke();
    canvas.hidden=false;status.textContent='Forma de onda real · primer canal · archivo completo (sin efectos del montaje).';
    canvas.onclick=event=>{q('edit-player').currentTime=(event.offsetX/canvas.clientWidth)*buffer.duration;};
  } catch(error){status.textContent='Forma de onda no disponible: '+error.message;} finally{if(context)await context.close();}
}
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
q('edit-output').onclick=()=>task(()=>command('output',{ratio:q('edit-preset').value,fps:Number(q('edit-fps').value)}));
q('edit-preview').onclick=()=>task(()=>render(true));q('edit-export').onclick=()=>task(()=>render(false));
q('edit-play').onclick=()=>task(async()=>{const p=q('edit-player');if(!p.currentSrc)throw Error('Selecciona una fuente o prepara la vista previa');if(p.paused)await p.play();else p.pause();});
q('edit-show-montage').onclick=()=>task(async()=>{requireProject();await checkRender();if(!preview)message('El montaje actual aún no tiene vista previa guardada. Usa Preparar vista previa del montaje.');});
q('edit-player').ontimeupdate=()=>{const p=q('edit-player');if(preview)cursor=p.currentTime||0;else if(selection&&state){try{const item=selected();if(sourceKey===item.clip.source_id)cursor=clipStart(edl(),item.clip,item.track)+Math.max(0,(p.currentTime-item.clip.in_seconds)/item.clip.speed);}catch{/* removed */}}q('edit-time').textContent=new Date(Math.max(0,p.currentTime)*1000).toISOString().slice(11,23);q('edit-caption').textContent=preview?.subtitle_mode==='mov_text'?(edl().cues.find(c=>c.start_seconds<=p.currentTime&&p.currentTime<c.end_seconds)?.text||''):'';if(!preview&&selection){try{const item=selected();if(sourceKey===item.clip.source_id&&p.currentTime>=item.clip.out_seconds)p.pause();}catch{/* selection removed */}}updatePlayhead();};
q('edit-player').onerror=()=>message('El navegador no pudo reproducir este archivo. Puedes preparar la vista previa MP4 con FFmpeg; no se modifica el original.');
q('edit-srt-import').onchange=event=>task(async()=>{requireProject();const f=event.target.files[0];if(!f)return;if(f.size>500000)throw Error('SRT superior a 500 KB');const response=await fetch(base()+'/subtitles/import?filename='+encodeURIComponent(f.name)+'&revision='+state.revision,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:f});const value=await response.json();if(!response.ok)throw Error(value.detail);state=value;invalidate();draw();message('SRT importado y validado; se conservan sus bytes originales. Aplica los cambios posteriores del campo SRT por separado.');});
q('edit-srt-save').onclick=()=>task(()=>command('subtitles',{srt:q('edit-srt').value}));
q('edit-cue-offset-apply').onclick=()=>task(()=>command('cue_offset',{seconds:Number(q('edit-cue-offset').value)}));
q('edit-cue-split').onclick=()=>task(()=>command('cue_split',{index:Number(q('edit-cue-index').value)-1,at:Number(q('edit-cue-at').value),text_index:Number(q('edit-cue-text-index').value)}));
q('edit-cue-merge').onclick=()=>task(()=>command('cue_merge',{index:Number(q('edit-cue-index').value)-1}));
q('edit-subtitle-style').onclick=()=>task(()=>command('subtitle_style',{size:Number(q('edit-subtitle-size').value),position:q('edit-subtitle-position').value,mode:q('edit-subtitle-mode').value}));
q('edit-zoom').oninput=()=>{zoomMode='manual';if(state)drawTracks();storeView();};
q('edit-fit').onclick=fitTimeline;q('edit-zoom-out').onclick=()=>zoomTimeline(1/1.25);q('edit-zoom-in').onclick=()=>zoomTimeline(1.25);
q('edit-view-source').onclick=()=>task(()=>{const item=selected();showSource(item.clip.source_id,item.clip);});
q('edit-split-cursor').onclick=()=>task(()=>{const item=selected();return command('split',splitAtCursor(edl(),item.clip,item.track,cursor));});
new ResizeObserver(()=>{if(state&&zoomMode==='fit')drawTracks();}).observe(q('edit-tracks'));

function showWorkspace(){q('edit-subtitle-panel').hidden=workspace!=='subtitles';q('edit-waveform').hidden=true;q('edit-waveform-status').hidden=workspace!=='audio';if(workspace==='audio'&&sourceKey&&edl().sources[sourceKey].audio)waveform(sourceKey);if(workspace==='library')q('edit-import').focus();if(workspace==='edit-projects')q('edit-project').focus();}
window.addEventListener('studio-workspace',event=>{workspace=event.detail;showWorkspace();if(workspace==='edit-projects')projects().catch(error=>message(error.message));});
document.addEventListener('keydown',event=>{if(q('manual-editor').hidden||/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName))return;if(event.ctrlKey||event.metaKey){if(event.key.toLowerCase()!=='z')return;}else if(!event.altKey){const key=event.key.toLowerCase();if(key==='f'){event.preventDefault();fitTimeline();return;}if(key==='+'||key==='='){event.preventDefault();zoomTimeline(1.25);return;}if(key==='-'){event.preventDefault();zoomTimeline(1/1.25);return;}if(key==='s'){event.preventDefault();q('edit-split-cursor').click();return;}}if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='z'){event.preventDefault();task(()=>command(event.shiftKey?'redo':'undo'));}});
initializeEditorLayout();
showWorkspace();task(async()=>{try{await projects();if(project)await reopen();}catch(error){for(const control of q('manual-editor').querySelectorAll('button,input,select,textarea'))control.disabled=true;throw error;}});
