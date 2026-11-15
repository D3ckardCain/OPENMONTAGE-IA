const $=s=>document.querySelector(s);let pid=new URLSearchParams(location.search).get('project'),busy=false;
const notice=s=>{$('#notice').textContent=s||'';};
async function api(path,data){const r=await fetch('/api/studio/'+path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});let v=await r.json();if(!r.ok)throw Error(typeof v.detail==='string'?v.detail:JSON.stringify(v.detail));return v;}
function node(tag,text){let n=document.createElement(tag);n.textContent=text;return n;}
function link(label,url){let a=node('a',label);a.href=url;return a;}
let importedComfyHistory=null;
$('#comfy-history').onchange=async e=>{
 const box=$('#comfy-history-result'),file=e.target.files[0];
 box.replaceChildren();importedComfyHistory=null;$('#comfy-history-save').disabled=true;if(!file)return;
 try{
  if(file.size>8000000)throw Error('Historial demasiado grande (máximo 8 MB)');
  const parsed=JSON.parse(await file.text());
  const report=await api('comfy-history/report',parsed);
  importedComfyHistory=parsed;$('#comfy-history-save').disabled=!report.jobs.length;
  const labels={completed:'Completado',failed:'Error o interrupción',unknown:'Estado sin confirmar'};
  box.append(node('p',report.jobs.length+' trabajos · informe temporal · calidad visual sin evaluar'));
  for(const job of report.jobs){
   const d=document.createElement('details');
   d.append(node('summary',job.prompt_id+' · '+labels[job.status]));
   d.append(node('p',job.elapsed_seconds===null?'Tiempo de ejecución no disponible':'Tiempo de ejecución: '+job.elapsed_seconds.toFixed(2)+' segundos'));
   d.append(node('p','Duración del medio: sin verificar'));
   for(const item of job.artifacts)d.append(node('p','Nodo '+item.node_id+' · '+item.type+' / '+item.subfolder+' / '+item.filename));
   if(!job.artifacts.length)d.append(node('p','Sin archivos declarados en este historial.'));
   box.append(d);
  }
 }catch(error){box.replaceChildren(node('p','No se pudo leer el historial: '+error.message));}
};
async function bootstrap(){const b=await api('bootstrap');const f=$('#settings');f.ollama_url.value=b.settings.ollama_url;f.ffmpeg_path.value=b.settings.ffmpeg_path||'';f.ffprobe_path.value=b.settings.ffprobe_path||'';f.comfyui_url.value=b.settings.comfyui_url;f.roots.value=b.settings.resource_roots.join('\n');f.model.replaceChildren(new Option(b.settings.model||'Sin modelo seleccionado',b.settings.model));$('#create').pipeline.replaceChildren(...b.pipelines.map(p=>new Option(p.name+' · '+p.stages.length+' etapas',p.name)));$('#projects').replaceChildren(...b.projects.map(p=>{let n=node('button',p.title);n.onclick=()=>select(p.project_id);return n;}));}
async function select(id){pid=id;history.replaceState(null,'','/studio?project='+encodeURIComponent(pid));$('#creation').hidden=true;$('#production').hidden=false;await refresh();}
async function refresh(){if(!pid||busy)return;busy=true;try{const s=await api('projects/'+pid);$('#title').textContent=s.request.title;$('#status').textContent=s.job.status;$('#message').textContent=s.job.message;$('#board').href=s.board_url;$('#approve').hidden=s.job.status!=='awaiting_human';$('#stages').replaceChildren(...s.stages.map(x=>{let n=node('div',x.name+' · '+x.status);n.className='stage '+x.status;return n;}));$('#artifacts').replaceChildren(...s.artifacts.map(x=>link(x.name,x.url)));$('#outputs').replaceChildren(...s.outputs.map(x=>{let d=node('div','');d.append(link(x.name,x.url));if(/\.(mp4|webm)$/i.test(x.name)){let v=document.createElement('video');v.controls=true;v.src=x.url;d.append(v);}return d;}));$('#events').textContent=(s.job.events||[]).map(x=>x.at+' ['+x.kind+'] '+x.message).join('\n');}catch(e){notice(e.message);}finally{busy=false;}}
$('#new').onclick=()=>{pid=null;history.replaceState(null,'','/studio');$('#creation').hidden=false;$('#production').hidden=true;notice('');};
$('#create').onsubmit=async e=>{e.preventDefault();let f=e.target;try{let p=await api('projects',{title:f.elements.namedItem('title').value,brief:f.brief.value,pipeline:f.pipeline.value,language:f.language.value,reference:f.reference.value,automatic:f.automatic.checked});await bootstrap();await select(p.project_id);notice('Proyecto creado. Inicia los agentes cuando el modelo local esté configurado.');}catch(e){notice(e.message);}};
$('#settings').onsubmit=async e=>{e.preventDefault();let f=e.target;try{await api('settings',{ffmpeg_path:f.ffmpeg_path.value,ffprobe_path:f.ffprobe_path.value,ollama_url:f.ollama_url.value,comfyui_url:f.comfyui_url.value,model:f.model.value,resource_roots:f.roots.value.split('\n').map(x=>x.trim()).filter(Boolean)});notice('Configuración guardada.');}catch(e){notice(e.message);}};
$('#check').onclick=async()=>{try{$('#runtime').textContent='Comprobando…';const s=await api('runtime');$('#runtime').textContent=JSON.stringify(s,null,2);let selected=$('#settings').model.value;$('#settings').model.replaceChildren(new Option('Selecciona un modelo',''),...s.models.map(m=>new Option(m,m,m===selected,m===selected)));}catch(e){notice(e.message);}};
for(const b of document.querySelectorAll('[data-action]'))b.onclick=async()=>{if(!pid)return;try{await api('projects/'+pid+'/'+b.dataset.action,{});await refresh();}catch(e){notice(e.message);}};
$('#inventory').onchange=async e=>{try{for(const f of e.target.files){if(f.size>32000000)throw Error('Inventario demasiado grande');let r=await api('inventories',JSON.parse(await f.text()));notice('Inventario '+r.serial+': '+r.files+' archivos registrados.');}}catch(e){notice(e.message);}};
$('#catalog').onclick=async()=>{try{const c=await api('resources');let box=$('#resource-list');box.replaceChildren(node('p',c.notes.join(' ')),node('p','Inventarios: '+c.inventories.map(x=>x.Nombre+' · '+x.Serie+' · '+x.Fecha).join(' / ')));for(const g of c.groups){let d=document.createElement('details');d.append(node('summary',g.label+' · '+g.files.filter(x=>x.status==='recorded_size_match').length+'/'+g.files.length+' registrados'));for(const f of g.files){let n=node('div','');n.className='resource';n.append(node('strong',f.filename+' · '+f.status),node('p','Carpeta del catálogo: '+f.destination_folder));if(f.status!=='recorded_size_match'&&c.inventories.length>=2&&f.download_url)n.append(link(f.download_url,f.download_url));else if(f.status!=='recorded_size_match')n.append(node('p','Importa ambos inventarios antes de decidir una descarga.'));d.append(n);}box.append(d);}}catch(e){notice(e.message);}};
$('#tools').onclick=async()=>{try{$('#tool-list').textContent='Comprobando dependencias locales…';$('#tool-list').textContent=JSON.stringify(await api('tools'),null,2);}catch(e){notice(e.message);}};
try{await bootstrap();const q=new URLSearchParams(location.search);$('#create').reference.value=q.get('reference')||'';$('#create').elements.namedItem('title').value=q.get('title')||'';if(pid)await select(pid);}catch(e){notice(e.message);}setInterval(refresh,3000);

$('#clarify').onclick=async()=>{if(!pid)return;try{await api('clarifications/'+pid,{message:$('#clarification').value});notice('Aclaración guardada. Reanuda los agentes.');}catch(e){notice(e.message);}};

$('#adapters').onclick=async()=>{try{notice('Comprobando modelos locales y entornos Python…');const items=await api('adapters');const box=$('#adapter-list');box.replaceChildren();const kokoro=items.find(x=>x.family==='kokoro');$('#voice-check').elements.namedItem('voice').replaceChildren(new Option('Selecciona una voz',''),...(kokoro?.available_voices||[]).filter(v=>/^e[fm]_/.test(v)).map(v=>new Option(v,v)));for(const item of items){const d=document.createElement('details');d.append(node('summary',item.family+' · '+item.backend+' · '+(item.ready?'Requisitos locales encontrados':'Necesita configuración')));d.append(node('p',item.problems.join(' · ')||'Inferencia y calidad pendientes de validar.'));const form=document.createElement('form');const fields=item.backend==='native'?['model_dir','python_executable','source_dir']:['workflow_path','output_node'];for(const name of fields){const label=node('label',name);const input=document.createElement('input');input.name=name;input.value=item.configuration[name]||((name==='model_dir'?item.model_dir:name==='python_executable'?item.python_executable:'')||'');label.append(input);form.append(label);}const save=node('button','Guardar adaptador');save.type='submit';form.append(save);form.onsubmit=async e=>{e.preventDefault();try{const cfg={};for(const name of fields)cfg[name]=form.elements.namedItem(name).value;await api('adapters/'+item.family,cfg);notice('Adaptador '+item.family+' guardado. Vuelve a detectar para comprobarlo.');}catch(e){notice(e.message);}};d.append(form);box.append(d);}notice('Diagnóstico terminado. No se han descargado pesos.');}catch(e){notice(e.message);}};

let checkId=null,checkTimer=null;
async function showValidation(){if(!checkId)return;try{const r=await api('validations/'+checkId),box=$('#validation-result');box.replaceChildren(node('h3',r.id+' · '+r.status),node('p',r.message));const audio=$('#validation-audio');audio.hidden=!r.audio_url;if(r.audio_url&&audio.getAttribute('src')!==r.audio_url)audio.src=r.audio_url;if(!r.audio_url){audio.pause();audio.removeAttribute('src');}box.append(node('pre',JSON.stringify({audio:r.audio,transcription:r.transcription,models:r.models,human_review:r.human_review,elapsed_seconds:r.elapsed_seconds},null,2)));if(!r.active){clearInterval(checkTimer);checkTimer=null;if(r.audio?.decoded){for(const [label,accepted] of [['Aprobar voz después de escuchar',true],['Rechazar voz',false]]){const b=node('button',label);b.onclick=async()=>{try{await api('validations/'+checkId+'/review',{accepted,comment:''});await showValidation();}catch(e){notice(e.message);}};box.append(b);}}}}catch(e){notice(e.message);clearInterval(checkTimer);}}
$('#voice-check').onsubmit=async e=>{e.preventDefault();const f=e.target;try{const result=await api('validations',{text:f.elements.namedItem('text').value,voice:f.elements.namedItem('voice').value,device:f.elements.namedItem('device').value,transcribe:f.elements.namedItem('transcribe').checked});checkId=result.id;await showValidation();clearInterval(checkTimer);checkTimer=setInterval(showValidation,3000);}catch(e){notice(e.message);}};
$('#check-history').onclick=async()=>{try{clearInterval(checkTimer);checkTimer=null;const results=await api('validations');const box=$('#validation-result');box.replaceChildren();for(const r of results){const b=node('button',r.created_at+' · '+r.status+' · '+r.request.voice);b.onclick=()=>{checkId=r.id;showValidation();};box.append(b);}if(!results.length)box.append(node('p','Todavía no hay pruebas ejecutadas en este equipo.'));}catch(e){notice(e.message);}};

$('#wan-profiles').onclick=async()=>{try{const data=await api('wan-presets'),box=$('#wan-profile-list');box.replaceChildren(node('p','Selección actual: '+(data.current.preset||'workflow personalizado')));for(const profile of data.presets){const d=document.createElement('details');d.append(node('summary',profile.label));d.append(node('p',profile.note),node('pre',profile.required_models.join('\n')));const button=node('button','Seleccionar '+profile.label);button.onclick=async()=>{try{await api('adapters/wan',{preset:profile.id});notice('Perfil seleccionado: '+profile.label+'. Comprueba sus modelos y nodos antes de ejecutar.');await $('#wan-profiles').onclick();}catch(e){notice(e.message);}};d.append(button);box.append(d);}}catch(e){notice(e.message);}};

$('#comfy-history-save').onclick=async()=>{
 if(!pid){notice('Selecciona un proyecto antes de guardar el informe.');return;}
 if(!importedComfyHistory)return;
 const selected=pid;
 try{const result=await api('comfy-history/projects/'+encodeURIComponent(selected),importedComfyHistory);notice((result.duplicate?'El informe ya estaba guardado':'Informe guardado')+' en '+selected+'.');}catch(e){notice(e.message);}
};
$('#comfy-history-list').onclick=async()=>{
 if(!pid){notice('Selecciona un proyecto para consultar sus informes.');return;}
 const selected=pid;
 try{const result=await api('comfy-history/projects/'+encodeURIComponent(selected));
 const box=$('#comfy-history-result');box.replaceChildren(node('h3','Informes de '+selected));
 if(!result.reports.length)box.append(node('p','Todavía no hay informes guardados.'));
 for(const report of result.reports){const d=document.createElement('details');d.append(node('summary',report.imported_at+' · '+report.jobs.length+' trabajos'),node('pre',JSON.stringify(report.jobs,null,2)));appendComfyContext(d,report,selected);box.append(d);}
 }catch(e){notice(e.message);}
};

function appendComfyContext(container,report,project){
 const versions=report.context_versions||[],latest=versions.at(-1)?.values||{};
 container.append(node('p','Ficha declarada por el usuario · sin verificación automática · '+versions.length+' versiones'));
 const form=document.createElement('form');
 const fields={equipment:'Nombre del equipo',cpu:'Procesador',gpu:'GPU',vram:'VRAM',ram:'RAM',storage:'Ubicación de modelos y tipo de disco',test_conditions:'Condiciones: workflow, semilla, imagen, pasos, cuadros y caché'};
 for(const [key,label] of Object.entries(fields)){const item=node('label',label),input=document.createElement(key==='test_conditions'?'textarea':'input');input.name=key;input.maxLength=2000;input.value=latest[key]||'';item.append(input);form.append(item);}
 const save=node('button','Guardar ficha de esta prueba');save.type='submit';form.append(save);
 form.onsubmit=async event=>{event.preventDefault();save.disabled=true;
 try{const values={};for(const key of Object.keys(fields))values[key]=form.elements.namedItem(key).value;
 await api('comfy-history/projects/'+encodeURIComponent(project)+'/'+report.id+'/context',values);
 notice('Ficha guardada en '+project+'. Los tiempos originales se conservaron.');
 }catch(e){notice(e.message);}finally{save.disabled=false;}};
 container.append(form);
 if(versions.length){const previous=document.createElement('details');previous.append(node('summary','Historial de fichas'),node('pre',JSON.stringify(versions,null,2)));container.append(previous);}
}

function showSourceImage(image,project){const box=$('#source-image-result');box.replaceChildren(node('p','Proyecto: '+project));if(!image){box.append(node('p','Sin imagen preparada.'));return;}const preview=document.createElement('img');preview.src=image.url;preview.alt='Imagen de entrada del proyecto '+project;preview.style.maxWidth='320px';box.append(preview,node('p',image.width+' × '+image.height+' · '+image.bytes+' bytes · guardada en el proyecto, pendiente de enviar a ComfyUI'));}
$('#source-image').onchange=async event=>{const file=event.target.files[0];if(!file)return;if(!pid){notice('Selecciona un proyecto antes de cargar una imagen.');return;}const selected=pid;try{if(file.size>8000000)throw Error('La imagen supera 8 MB');const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(Error('No se pudo leer la imagen'));reader.readAsDataURL(file);});const image=await api('source-images/'+encodeURIComponent(selected),{image_base64:encoded});showSourceImage(image,selected);notice('Imagen preparada. No se inició ninguna generación.');}catch(e){notice(e.message);}};
$('#source-image-current').onclick=async()=>{if(!pid){notice('Selecciona un proyecto para ver su imagen.');return;}const selected=pid;try{const result=await api('source-images/'+encodeURIComponent(selected));showSourceImage(result.image,selected);}catch(e){notice(e.message);}};

$('#comfy-jobs-refresh').onclick=async()=>{if(!pid)return;const selected=pid;
 try{const result=await api('comfy-jobs/'+encodeURIComponent(selected));const box=$('#comfy-jobs-result');box.replaceChildren(node('p','Proyecto: '+selected));
 for(const warning of result.warnings)box.append(node('p',warning));
 if(!result.jobs.length)box.append(node('p','Sin trabajos registrados por la app. Las pruebas manuales de ComfyUI no aparecen automáticamente.'));
 for(const job of result.jobs){const d=document.createElement('details');d.append(node('summary',(job.family||'ComfyUI')+' · '+job.status+' · '+job.prompt_id),node('p','Estado local; no se consultó el servidor.'));
 if(job.last_error)d.append(node('p','Último error: '+job.last_error));
 d.append(node('pre',JSON.stringify({output_dir:job.output_dir,resume_prompt_id:job.resume_prompt_id},null,2)));box.append(d);}
 }catch(e){notice(e.message);}};

let referenceTimer=null;
async function loadReferenceReport(selected){try{const r=await api('reference-video/'+encodeURIComponent(selected));if(pid!==selected)return;const box=$('#reference-result');box.replaceChildren(node('h3','Análisis: '+r.status),node('p','Verificación de hechos externos: pendiente'));
 for(const frame of r.frames||[]){const d=node('div',frame.timestamp_seconds.toFixed(2)+' segundos');const image=document.createElement('img');image.src=frame.url;image.alt='Fotograma de referencia';image.style.maxWidth='240px';d.append(image);box.append(d);}
 box.append(node('pre',JSON.stringify(r,null,2)));if(!['queued','running'].includes(r.status)){clearInterval(referenceTimer);referenceTimer=null;}
 }catch(e){notice(e.message);clearInterval(referenceTimer);}}
$('#reference-video-file').onchange=async event=>{const file=event.target.files[0];if(!file)return;if(!pid){notice('Selecciona primero el proyecto.');return;}const selected=pid;try{if(file.size>500000000)throw Error('El video supera 500 MB');notice('Cargando video al proyecto local…');const response=await fetch('/api/studio/reference-video/'+encodeURIComponent(selected)+'/upload',{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});const result=await response.json();if(!response.ok)throw Error(result.detail);notice('Video guardado. El análisis todavía no se inició.');await loadReferenceReport(selected);}catch(e){notice(e.message);}};
$('#reference-analyze').onclick=async()=>{if(!pid){notice('Selecciona primero el proyecto.');return;}const selected=pid;try{await api('reference-video/'+encodeURIComponent(selected)+'/analyze',{});notice('Análisis local iniciado en CPU. Los modelos ausentes se indicarán en el informe.');clearInterval(referenceTimer);await loadReferenceReport(selected);referenceTimer=setInterval(()=>loadReferenceReport(selected),5000);}catch(e){notice(e.message);}};
$('#reference-report').onclick=async()=>{if(!pid)return;clearInterval(referenceTimer);await loadReferenceReport(pid);};
