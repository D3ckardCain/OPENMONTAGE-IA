const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const state={identity:null,bootstrap:null,storage:null,capabilities:null,projects:[],edit:null,pid:null,previewRenderSha:null,renderTask:null,renderTimer:null,renderPollToken:0,selectedSource:null,selectedClip:null,selectedTrack:'video',busy:false,lastSports:null,sportsDefinitions:null,sportsDefinitionCompetition:null};
state.pid=new URLSearchParams(location.search).get('project');
const names={video:'Vídeo',audio:'Audio',subtitles:'Subtítulos',library:'Biblioteca',projects:'Proyectos',channels:'Investigación',sports:'Comparativas',thumbnails:'Miniaturas',avatars:'Avatares',clips:'Clips y tráileres',settings:'Preferencias'};
const capabilityLabels={subtitle_karaoke:'Karaoke por palabras',subtitle_layout:'Diseño de subtítulos',subtitle_reflow:'Reflujo de texto',ripple_volume_points:'Automatización de volumen con ripple',track_volume_points:'Automatización de volumen por pista',mix_meter:'Medición de mezcla',audio_ducking:'Ducking de audio',track_mixer:'Mezclador por pista',audio_processing:'Procesamiento de audio',sfx_catalog:'Catálogo de efectos de sonido',crossfade:'Fundidos cruzados',audio_balance:'Balance de audio',layer_transform_keyframes:'Keyframes de transformación',layer_position_keyframes:'Keyframes de posición',batch:'Edición por lotes',duplicate:'Duplicar clip',markers:'Marcadores',flags:'Mute, solo y bloqueo',audio_trim_position:'Corte y posición de audio',delete_keep_gap:'Borrar conservando hueco',ripple_delete:'Borrado ripple',transform:'Transformación',titles:'Títulos',output_custom:'Formato personalizado',audio_mix:'Mezcla de audio',transition:'Transiciones',layers:'Capas',clip_candidates:'Candidatos de clips',subtitle_language:'Idioma de subtítulos',subtitle_words:'Inspección de palabras',subtitle_from_words:'Subtítulos desde palabras',silence_apply:'Aplicar propuesta de silencios',qwen_tts_plan:'Plan de voz Qwen',reference_plan:'Plan desde referencia',component_add:'Añadir componente visual',component_remove:'Quitar componente visual',clip_color:'Color por clip',color_compare:'Comparación de color',clip_color_hsl_hue:'Tono HSL por clip',clip_color_curves:'Curvas de color',clip_speed_ramp:'Rampa de velocidad',speed_ramp_plan:'Plan de velocidad',clip_smooth_speed:'Velocidad suave',smooth_speed_plan:'Plan de velocidad suave',layer_align:'Alinear capa'};
let toastTimer;
function toast(message){const el=$('#toast');el.textContent=message;el.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('visible'),3500)}
async function req(path,{method='GET',body,headers={},raw=false}={}){const response=await fetch(path,{method,headers:body instanceof FormData?headers:{'Content-Type':'application/json',...headers},body:body===undefined?undefined:body instanceof FormData?body:JSON.stringify(body),cache:'no-store'});if(!response.ok){let message=`HTTP ${response.status}`;try{const x=await response.json();message=x.detail||x.error||message}catch{}throw Error(message)}if(raw)return response;if(response.status===204)return null;return response.json()}
async function tryApi(path,opts){try{return await req(path,opts)}catch(e){return{__error:e.message}}}
function setModule(name){if(!names[name])name='video';$$('.nav-item').forEach(b=>{const active=b.dataset.module===name;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});$$('.module-page').forEach(p=>p.classList.toggle('active',p.dataset.page===name));$('#page-name').textContent=names[name];history.replaceState(null,'',location.pathname+location.search+'#'+name);if(name==='projects')renderProjects();if(name==='channels')loadChannelStatus();if(name==='sports')loadSportsSchema()}
$$('.nav-item').forEach(b=>b.addEventListener('click',()=>setModule(b.dataset.module)));
$('#refresh-status').onclick=()=>initialize(true);$('#agent-toggle').onclick=()=>{const open=$('#agent-drawer').hidden;$('#agent-drawer').hidden=!open;$('#agent-toggle').setAttribute('aria-expanded',String(open));if(open){startAgentActivityPolling();loadAgentActivity()}else stopAgentActivityPolling()};$('#agent-close').onclick=()=>{$('#agent-drawer').hidden=true;$('#agent-toggle').setAttribute('aria-expanded','false');stopAgentActivityPolling()};
const agentJobLabels={ready:'Listo',running:'En curso',awaiting_human:'Revisión pendiente',awaiting_input:'Espera una respuesta',interrupted:'Interrumpido',stopped:'Detenido',blocked:'Bloqueado',completed:'Completado',failed:'Fallido'};
const agentStageLabels={pending:'Pendiente',in_progress:'En curso',completed:'Completada',awaiting_human:'Revisión',blocked:'Bloqueada',failed:'Fallida',skipped:'Omitida'};
function safeProjectMediaUrl(value){try{const url=new URL(String(value||''),location.origin),prefix='/media/'+encodeURIComponent(state.pid)+'/';return url.origin===location.origin&&url.pathname.startsWith(prefix)?url.pathname+url.search:null}catch{return null}}
function renderAgentRequest(request){
  const root=$('#agent-request');if(!root)return;root.replaceChildren();
  if(!request||typeof request!=='object'){root.textContent='No hay un encargo de producción asociado a este proyecto.';return}
  const card=document.createElement('article');card.className='agent-request-card';
  const title=document.createElement('strong');title.textContent=String(request.title||'Proyecto sin título');card.append(title);
  const brief=typeof request.brief==='string'?request.brief:'';
  if(brief){const summary=document.createElement('p');summary.textContent=brief.length>320?brief.slice(0,320).trimEnd()+'…':brief;card.append(summary);if(brief.length>320){const details=document.createElement('details'),label=document.createElement('summary'),full=document.createElement('p');label.textContent='Ver encargo completo';full.textContent=brief;details.append(label,full);card.append(details)}}
  const meta=document.createElement('small'),language=typeof request.language==='string'&&request.language?request.language:'idioma no indicado';meta.textContent='Idioma: '+language;card.append(meta);root.append(card)
}
function agentClarificationStorageKey(pid){return 'openmontage.agent-clarification-pending.'+pid}
function readAgentClarificationPending(pid){try{return JSON.parse(localStorage.getItem(agentClarificationStorageKey(pid))||'null')}catch{return null}}
function saveAgentClarificationPending(pid,value){try{localStorage.setItem(agentClarificationStorageKey(pid),JSON.stringify(value));return true}catch{return false}}
function clearAgentClarificationPending(pid){try{localStorage.removeItem(agentClarificationStorageKey(pid))}catch{}}
function renderAgentClarifications(rows){
  const root=$('#agent-clarifications');if(!root)return;root.replaceChildren();
  if(!Array.isArray(rows)||!rows.length){const empty=document.createElement('li');empty.className='empty-state';empty.textContent='Aún no hay aclaraciones guardadas.';root.append(empty);return}
  for(const item of rows.slice(-30).reverse()){if(!item||typeof item!=='object')continue;const row=document.createElement('li');row.className='agent-clarification';const text=document.createElement('p'),time=document.createElement('time');text.textContent=String(item.message||'Aclaración sin texto');row.append(text);if(typeof item.at==='string'&&item.at){time.dateTime=item.at;time.textContent=item.at;row.append(time)}root.append(row)}
}
function renderAgentActivity(projectState={}){
  const root=$('#events'),status=$('#agent-status'),stagesRoot=$('#agent-stages'),artifactsRoot=$('#agent-artifacts'),controls=$('#agent-controls');
  if(!root)return;
  const job=projectState?.job&&typeof projectState.job==='object'?projectState.job:{},stages=Array.isArray(projectState?.stages)?projectState.stages:[],events=Array.isArray(job.events)?job.events:[];
  const active=projectState?.active===true,jobStatus=String(job.status||'unknown'),completed=stages.filter(item=>item?.status==='completed').length,productionAvailable=projectState?.production_pipeline_available!==false;
  status.textContent=state.pid?(productionAvailable?(agentJobLabels[jobStatus]||'Estado sin clasificar'):'Proyecto de edición')+' · '+(active?'Agente activo':'Agente inactivo')+(stages.length?' · '+completed+'/'+stages.length+' etapas completadas':''):'Elige un proyecto para ver su estado.';
  renderAgentRequest(projectState?.request);const clarificationButton=$('#agent-clarification-save');if(clarificationButton)clarificationButton.disabled=!state.pid||active||state.identity?.restart_required!==false;
  stagesRoot.replaceChildren();stagesRoot.hidden=!stages.length;
  for(const stage of stages){if(!stage||typeof stage!=='object')continue;const row=document.createElement('li'),name=document.createElement('strong'),value=document.createElement('span');row.dataset.status=String(stage.status||'pending');name.textContent=String(stage.name||'Etapa');value.textContent=agentStageLabels[stage.status]||'Estado sin clasificar';row.append(name,value);if(stage.error){const error=document.createElement('small');error.textContent=String(stage.error);row.append(error)}stagesRoot.append(row)}
  artifactsRoot.replaceChildren();const artifactGroups=[['Artefactos',projectState?.artifacts],['Entregas',projectState?.outputs]];let artifactCount=0;
  for(const [label,items] of artifactGroups){if(!Array.isArray(items)||!items.length)continue;const section=document.createElement('section'),heading=document.createElement('h4'),list=document.createElement('ul');heading.textContent=label;for(const item of items.slice(-8)){if(!item||typeof item!=='object')continue;const href=safeProjectMediaUrl(item.url);if(!href)continue;const li=document.createElement('li'),link=document.createElement('a');link.href=href;link.textContent=String(item.name||'Archivo del proyecto');li.append(link);list.append(li);artifactCount++}if(list.childElementCount){section.append(heading,list);artifactsRoot.append(section)}}
  artifactsRoot.hidden=!artifactCount;
  const startButton=$('#agent-start'),stopButton=$('#agent-stop'),approveButton=$('#agent-approve');
  if(startButton&&stopButton&&approveButton){const canStart=!active&&['ready','interrupted','stopped','awaiting_input'].includes(jobStatus),canApprove=!active&&stages.some(item=>item?.status==='awaiting_human');startButton.hidden=!(state.pid&&canStart&&state.identity?.restart_required===false);startButton.textContent=jobStatus==='ready'?'Iniciar agente':'Reanudar agente';stopButton.hidden=!(state.pid&&active&&state.identity?.restart_required===false);approveButton.hidden=!(state.pid&&canApprove&&state.identity?.restart_required===false);controls.hidden=startButton.hidden&&stopButton.hidden&&approveButton.hidden}
  root.replaceChildren();const recent=events.slice(-12).reverse();if(!recent.length){const empty=document.createElement('div');empty.className='empty-state';empty.textContent=state.pid?'No hay actividad registrada para este proyecto.':'Elige un proyecto para ver su actividad local.';root.append(empty);return}
  for(const ev of recent){if(!ev||typeof ev!=='object')continue;const kind=String(ev.kind||'event'),card=document.createElement('article');card.className='agent-activity-card';card.dataset.kind=ev.outcome==='unknown'?'error':kind;const title=document.createElement('strong');title.textContent=ev.outcome==='unknown'?'Resultado incierto':String(ev.message||kind);card.append(title);if(ev.at){const time=document.createElement('time');time.dateTime=String(ev.at);time.textContent=String(ev.at);card.append(time)}if(ev.outcome==='unknown'){const note=document.createElement('small');note.textContent='No repitas la escritura hasta reconciliar su recibo.';card.append(note)}const usage=ev.ollama_usage||ev.usage;if(kind==='model_usage'&&usage&&typeof usage==='object'){const metrics=document.createElement('div');metrics.className='agent-activity-metrics';for(const key of ['prompt_eval_count','eval_count','total_duration'])if(usage[key]!==undefined){const item=document.createElement('span');item.textContent=key==='prompt_eval_count'?'Tokens de entrada: '+usage[key]:key==='eval_count'?'Tokens de respuesta: '+usage[key]:'Duración total (ns): '+usage[key];metrics.append(item)}if(metrics.childElementCount)card.append(metrics)}root.append(card)}
}
let agentActivityTimer=null,agentActivityRequest=0;
function stopAgentActivityPolling(){if(agentActivityTimer){clearInterval(agentActivityTimer);agentActivityTimer=null}agentActivityRequest++}
function startAgentActivityPolling(){stopAgentActivityPolling();if($('#agent-drawer').hidden)return;agentActivityTimer=setInterval(()=>{if(!document.hidden&&!$('#agent-drawer').hidden)loadAgentActivity()},5000)}
let agentMemorySnapshotPid=null,agentMemoryAgentActive=null,agentMemoryRequest=0;
function memoryKindLabel(kind){return kind==='explicit_preference'?'Preferencia explícita':kind==='creative_decision'?'Decisión creativa':String(kind||'Memoria')}
function renderAgentMemory(data){
  const root=$('#agent-memory-list'),status=$('#agent-memory-status');if(!root||!status)return;root.replaceChildren();
  if(data.__error||!Array.isArray(data.entries)){status.textContent='No se pudo leer la memoria del proyecto; puedes actualizar para reintentar.';return}
  const active=!!data.agent_active;agentMemoryAgentActive=active;const compatible=state.identity?.restart_required===false,canWrite=!!state.pid&&compatible&&!active;const addButton=$('#agent-memory-add'),saveButton=$('#agent-memory-save');if(addButton)addButton.disabled=!canWrite;if(saveButton)saveButton.disabled=!canWrite;
  status.textContent=data.truncated?'Se muestran las entradas recientes; hay más historial.':data.entries.length?'Memoria local con origen y revisión del proyecto.':'Todavía no hay preferencias ni decisiones guardadas.';
  for(const entry of data.entries){
    const row=document.createElement('li');row.className='agent-memory-item';row.dataset.memoryId=String(entry.memory_id||'');
    const heading=document.createElement('strong');heading.textContent=memoryKindLabel(entry.kind);
    const body=document.createElement('p');body.textContent=String(entry.text||'');
    const meta=document.createElement('small');const revision=entry.captured_revision_matches?'Coincide con la revisión actual':'Guardada con otra revisión del proyecto';meta.textContent=String(entry.source_type||'origen no declarado')+' · '+String(entry.source_ref||'sin referencia')+' · '+revision+' · '+(entry.active?'Activa':'Retirada del índice');
    const trust=document.createElement('small');trust.textContent='Contexto solamente; no sustituye las instrucciones actuales.';
    row.append(heading,body,meta,trust);
    if(entry.active){
      const actions=document.createElement('div');actions.className='agent-memory-actions';
      if(['explicit_preference','creative_decision'].includes(entry.kind)){const edit=document.createElement('button');edit.type='button';edit.className='quiet-button';edit.textContent='Corregir';edit.title='Guarda la corrección como una versión nueva y conserva esta referencia';edit.disabled=!canWrite;edit.onclick=()=>openAgentMemoryForm(entry);actions.append(edit)}
      const forget=document.createElement('button');forget.type='button';forget.className='quiet-button';forget.textContent='Retirar del índice';forget.title='Deja de recuperar esta memoria; conserva el recibo local';forget.disabled=!canWrite;forget.onclick=()=>changeAgentMemory({operation:'forget',memory_id:entry.memory_id});actions.append(forget);row.append(actions)
    }
    root.append(row)
  }
  if(!compatible)status.textContent='Backend pendiente de activación; memoria en modo de solo lectura.';
  else if(active)status.textContent='El agente está usando este proyecto; memoria en modo de solo lectura.';
}
function openAgentMemoryForm(entry=null){
  if(!state.pid||state.identity?.restart_required!==false){$('#agent-memory-status').textContent='Backend pendiente de activación; memoria en solo lectura.';return}if(agentMemoryAgentActive!==false){$('#agent-memory-status').textContent=agentMemoryAgentActive?'El agente está usando este proyecto; memoria en solo lectura.':'Espera a cargar el estado del proyecto antes de editar memoria.';return}
  const form=$('#agent-memory-form');if(!form)return;form.hidden=false;$('#agent-memory-kind').value=entry?.kind||'explicit_preference';
  $('#agent-memory-text').value=entry?.text||'';$('#agent-memory-source').value='';form.dataset.supersedesId=entry?.memory_id||'';
  $('#agent-memory-save').textContent=entry?'Guardar corrección':'Guardar versión';
  $('#agent-memory-status').textContent=entry?'La corrección creará una versión nueva y retirará del índice la anterior.':'La entrada se guardará solo en este proyecto.';
  $('#agent-memory-text').focus()
}
function closeAgentMemoryForm(){const form=$('#agent-memory-form');if(!form)return;form.hidden=true;form.reset();delete form.dataset.supersedesId}
async function loadAgentMemory(pid=state.pid){
  const status=$('#agent-memory-status'),requestId=++agentMemoryRequest;
  if(!pid){agentMemorySnapshotPid=null;agentMemoryAgentActive=null;$('#agent-memory-list')?.replaceChildren();$('#agent-memory-add').disabled=true;$('#agent-memory-save').disabled=true;closeAgentMemoryForm();if(status)status.textContent='Elige un proyecto para consultar su memoria.';return}
  if(agentMemorySnapshotPid!==pid){agentMemoryAgentActive=null;$('#agent-memory-list')?.replaceChildren();$('#agent-memory-add').disabled=true;$('#agent-memory-save').disabled=true;closeAgentMemoryForm()}
  status.textContent='Leyendo memoria local del proyecto…';const data=await tryApi('/api/studio/projects/'+encodeURIComponent(pid)+'/memory');
  if(requestId!==agentMemoryRequest||pid!==state.pid)return;
  if(data.__error){status.textContent='No se pudo consultar la memoria local; no se envió ningún cambio.';return}
  agentMemorySnapshotPid=pid;renderAgentMemory(data)
}
async function changeAgentMemory(payload){
  const pid=state.pid,status=$('#agent-memory-status');if(!pid)return false;
  if(state.identity?.restart_required!==false){status.textContent='Backend pendiente de activación; no se envió el cambio.';return false}if(agentMemoryAgentActive!==false){status.textContent=agentMemoryAgentActive?'El agente está usando este proyecto; no se envió el cambio.':'Espera a cargar el estado del proyecto; no se envió el cambio.';return false}
  status.textContent=payload.operation==='forget'?'Retirando del índice local…':'Guardando nueva versión en el proyecto…';let confirmed=false;
  try{await req('/api/studio/projects/'+encodeURIComponent(pid)+'/memory',{method:'POST',body:payload});confirmed=true;status.textContent=payload.operation==='forget'?'Entrada retirada del índice; recibo conservado.':'Nueva versión guardada con procedencia.'}
  catch(error){status.textContent='Respuesta incierta; se consultará la memoria antes de considerar otro intento.'}
  await loadAgentMemory(pid);return confirmed
}
async function submitAgentMemory(event){
  event.preventDefault();const form=$('#agent-memory-form'),text=$('#agent-memory-text').value.trim(),source=$('#agent-memory-source').value.trim();
  if(!state.pid||!text||!source)return;const payload={operation:'remember',kind:$('#agent-memory-kind').value,text,source_ref:source};
  if(form.dataset.supersedesId)payload.supersedes_id=form.dataset.supersedesId;
  if(await changeAgentMemory(payload))closeAgentMemoryForm()
}
let agentActivitySnapshotPid=null;
async function loadAgentActivity(){
  const root=$('#events');if(!root)return;const pid=state.pid;
  if(!pid){agentActivitySnapshotPid=null;agentMemorySnapshotPid=null;agentMemoryAgentActive=null;$('#agent-memory-add').disabled=true;$('#agent-memory-save').disabled=true;$('#agent-memory-list')?.replaceChildren();$('#agent-memory-status').textContent='Elige un proyecto para consultar su memoria.';closeAgentMemoryForm();renderAgentActivity({});return}
  const requestId=++agentActivityRequest,hasCurrentSnapshot=agentActivitySnapshotPid===pid;
  if(!hasCurrentSnapshot){$('#agent-status').textContent='Cargando estado local…';root.textContent='Cargando actividad local…';$('#agent-stages').replaceChildren();$('#agent-stages').hidden=true;$('#agent-artifacts').replaceChildren();$('#agent-artifacts').hidden=true;$('#agent-controls').hidden=true}
  const data=await tryApi(`/api/studio/projects/${encodeURIComponent(pid)}`);
  if(requestId!==agentActivityRequest||pid!==state.pid)return;
  if(data.__error){
    $('#agent-status').textContent=hasCurrentSnapshot
      ?'Conexión temporalmente no disponible · se conserva la última lectura y se volverá a consultar.'
      :'No se pudo leer el estado: '+data.__error;
    if(!hasCurrentSnapshot)root.textContent='Actividad no disponible; se reintentará automáticamente.';
    return;
  }
  agentActivitySnapshotPid=pid;delete root.dataset.stale;renderAgentActivity(data);await loadAgentClarifications(pid,requestId,data.active===true);if(agentMemorySnapshotPid!==pid||agentMemoryAgentActive!==(data.active===true))await loadAgentMemory(pid)
}
async function loadAgentClarifications(pid,activityRequest,active){
  const host=$('#agent-clarifications');if(!host)return;
  const data=await tryApi(`/api/studio/clarifications/${encodeURIComponent(pid)}`);
  if(activityRequest!==agentActivityRequest||pid!==state.pid)return;
  if(data.__error||!Array.isArray(data.clarifications)){renderAgentClarifications([]);$('#agent-clarification-status').textContent='No se pudieron leer las aclaraciones guardadas.';$('#agent-clarification-save').disabled=true;return}
  renderAgentClarifications(data.clarifications);const pending=readAgentClarificationPending(pid),saved=pending&&data.clarifications.find(item=>item?.request_id===pending.request_id);
  if(saved){clearAgentClarificationPending(pid);$('#agent-clarification-text').value='';$('#agent-clarification-status').textContent='La aclaración pendiente ya estaba guardada en el proyecto.'}
  else if(pending){const field=$('#agent-clarification-text');if(!field.value)field.value=String(pending.message||'');$('#agent-clarification-status').textContent='La respuesta anterior no se confirmó. Puedes reintentar el mismo texto; se reutilizará el mismo identificador.'}
  else $('#agent-clarification-status').textContent='Solo se guarda en el proyecto seleccionado. Las nuevas notas se bloquean mientras el agente trabaja.';
  const button=$('#agent-clarification-save');if(button)button.disabled=active||data.active===true||state.identity?.restart_required!==false
}
async function submitAgentClarification(event){
  event.preventDefault();const pid=state.pid,field=$('#agent-clarification-text'),button=$('#agent-clarification-save'),status=$('#agent-clarification-status'),message=field.value.trim();
  if(!pid||!message)return;
  if(state.identity?.restart_required!==false){status.textContent='Backend pendiente de activación; no se guardó la aclaración.';return}
  let pending=readAgentClarificationPending(pid);
  if(pending&&pending.message!==message){status.textContent='Primero reconcilia la aclaración pendiente. Reintentar usa el mismo texto y el mismo identificador.';return}
  if(!pending){const bytes=crypto.getRandomValues(new Uint8Array(16));pending={request_id:[...bytes].map(value=>value.toString(16).padStart(2,'0')).join(''),message};if(!saveAgentClarificationPending(pid,pending)){status.textContent='No se pudo guardar el identificador local; no se envió la aclaración.';return}}
  button.disabled=true;status.textContent='Guardando aclaración en el proyecto…';
  try{const result=await req(`/api/studio/clarifications/${encodeURIComponent(pid)}`,{method:'POST',body:pending});clearAgentClarificationPending(pid);field.value='';status.textContent=result.duplicate?'Esta aclaración ya estaba guardada.':'Aclaración guardada en el proyecto.';await loadAgentActivity()}
  catch(error){status.textContent=`Respuesta no confirmada (${error.message}). Reintenta el mismo texto; el identificador se conserva para evitar duplicados.`}
  finally{button.disabled=!state.pid||state.identity?.restart_required!==false}
}
$('#agent-clarification-form')?.addEventListener('submit',submitAgentClarification);
$('#agent-memory-form')?.addEventListener('submit',submitAgentMemory);
$('#agent-memory-add')?.addEventListener('click',()=>openAgentMemoryForm());
$('#agent-memory-refresh')?.addEventListener('click',()=>loadAgentMemory(state.pid));
$('#agent-memory-cancel')?.addEventListener('click',closeAgentMemoryForm);
let agentActionPending=false;
async function runAgentAction(action){if(agentActionPending)return;const result=$('#agent-action-result'),buttons=[$('#agent-start'),$('#agent-stop'),$('#agent-approve')];if(!state.pid||state.identity?.restart_required!==false){result.textContent='Acción no disponible: activa y verifica el backend compatible.';return}agentActionPending=true;buttons.forEach(button=>button.disabled=true);result.textContent='Enviando acción…';try{const response=await req(`/api/studio/projects/${encodeURIComponent(state.pid)}/${action}`,{method:'POST',body:{}});result.textContent=action==='stop'?(response.requested?'Detención solicitada; el cierre del proceso aún no está confirmado.':'No hay agente activo que detener.') :action==='approve'?'Aprobación registrada; se solicitó continuar la siguiente etapa.':'Inicio solicitado; revisa el estado del agente.';await loadAgentActivity()}catch(error){result.textContent='La acción no se confirmó: '+error.message}finally{agentActionPending=false;buttons.forEach(button=>button.disabled=false)}}
$('#agent-start').onclick=()=>runAgentAction('resume');$('#agent-stop').onclick=()=>runAgentAction('stop');$('#agent-approve').onclick=()=>runAgentAction('approve');
function readOnlyReason(){return state.identity?.restart_required?`Backend pendiente de activación (${state.identity.disk?.sha256?.slice(0,10)||'revisión nueva'}). Las escrituras solo se habilitan si la API activa confirma el contrato.`:''}
async function initialize(refresh=false){$('#connection-label').textContent='Conectando…';const [health,identity,bootstrap,storage,caps]=await Promise.all([tryApi('/api/health'),tryApi('/api/studio/identity'),tryApi('/api/studio/bootstrap'),tryApi('/api/studio/storage'),tryApi('/api/studio/editor/capabilities')]);state.identity=identity?.__error?null:identity;state.bootstrap=bootstrap?.__error?null:bootstrap;state.storage=storage?.__error?null:storage;state.capabilities=caps?.__error?null:caps;const online=!health?.__error&&health?.ok===true;$('#connection-label').textContent=online?'Studio local':'Servidor no disponible';$('#backend-warning').hidden=!(identity?.restart_required);if(identity?.restart_required){$('#identity-short').textContent=`API ${identity.resident?.sha256?.slice(0,8)||'—'} · disco ${identity.disk?.sha256?.slice(0,8)||'—'}`;$('#backend-warning').querySelector('small').textContent='La UI nueva se sirve desde disco. Identidad avisa que el proceso backend no coincide; no se reiniciará automáticamente. Cada operación depende de que su ruta activa responda.'}if(bootstrap&&!bootstrap.__error){state.projects=bootstrap.projects||[];renderProjects()}if(storage&&!storage.__error){$('#root-path').textContent=storage.active_projects_dir||'Carpeta predeterminada del repositorio';$('#root-note').textContent=storage.environment_override?'La ruta activa viene de una variable del proceso.':'Los archivos originales se copian al espacio del proyecto y se conservan en origen. Modelos compartidos permanecen fuera.';$('#storage-detail').replaceChildren(makeKV('Ruta activa',storage.active_projects_dir||'No disponible'),makeKV('Ruta configurada',storage.configured_projects_dir||'Predeterminada'),makeKV('Sobrescritura del proceso',storage.environment_override?'Sí':'No'),makeKV('Disponible',storage.available?'Sí':'No'))}if(caps&&!caps.__error){const ops=Array.isArray(caps.commands)?caps.commands:Array.isArray(caps.operations)?caps.operations:Object.keys(caps.commands||{});$('#capability-list').replaceChildren(...ops.slice(0,36).map(x=>{const d=document.createElement('div');d.className='capability-row';d.innerHTML=`<span>${esc(capabilityLabels[typeof x==='string'?x:x.name]||'Otra capacidad local')}</span><small>Disponible en API</small>`;return d}));$('#thumbnail-capability').textContent=`API de edición ${ops.length?'activa':'sin lista'}; la composición/generación de miniaturas no se declara disponible aquí.`;$('#clips-capability').textContent=ops.some(x=>String(x).includes('clip_candidate'))?'La API anuncia candidatos de clips; inspección y aceptación requieren abrir un proyecto.':'No se encontró un comando de candidatos de clips en la API activa.'}else{$('#capability-list').innerHTML='<div class="empty-state">La API de edición no está disponible en este proceso.</div>';$('#thumbnail-capability').textContent='No se confirmó el contrato de edición del backend activo.'}loadProjectsForEditor();if(state.pid)await openEditor(state.pid);if(refresh)toast('Estado actualizado')}
function makeKV(label,value){const d=document.createElement('div');d.className='capability-row';const a=document.createElement('span'),b=document.createElement('small');a.textContent=label;b.textContent=value;d.append(a,b);return d}
function esc(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function loadProjectsForEditor(){const data=await tryApi('/api/studio/editor/projects');if(!data.__error){state.projects=data;const select=$('#project-select'),current=state.pid;select.replaceChildren(new Option('Selecciona un proyecto',''),...data.map(p=>new Option(p.title,p.project_id)));if(current&&data.some(p=>p.project_id===current))select.value=current;renderProjects()}else{$('#editor-lock').hidden=false;$('#editor-lock').textContent='El proceso activo no expone la API de edición manual. Las operaciones de edición quedan sin activar; no se sustituye por un flujo simulado.'}}
function renderProjects(){const list=$('#projects-grid');list.replaceChildren();const descending=$('#project-sort')?.value==='title-desc';const projects=[...state.projects].sort((a,b)=>String(a.title||a.project_id).localeCompare(String(b.title||b.project_id),'es',{numeric:true,sensitivity:'base'})*(descending?-1:1));for(const p of projects){const card=document.createElement('article');card.className='project-card';const title=document.createElement('h2');title.textContent=p.title||p.project_id;const path=document.createElement('p');const projectPath=typeof p.project_path==='string'?p.project_path.trim():'';path.className=`project-path${projectPath?'':' missing'}`;path.textContent=projectPath||'Ubicación no informada';if(projectPath)path.title=projectPath;const button=document.createElement('button');button.className='quiet-button';button.textContent='Abrir en editor';button.onclick=()=>{state.pid=p.project_id;$('#project-select').value=p.project_id;setModule('video');openEditor(p.project_id)};card.append(title,path,button);list.append(card)}}
$('#project-sort').onchange=renderProjects;
function showCreate(){const d=$('#create-dialog');$('#new-title').value='';d.showModal();$('#new-title').focus()}
$('#top-new-project').onclick=showCreate;$('#new-project-inline').onclick=showCreate;$('#projects-create').onclick=showCreate;
$('#create-form').addEventListener('submit',async e=>{if(e.submitter?.value==='cancel')return;e.preventDefault();const title=$('#new-title').value.trim();if(!title)return;try{const created=await req('/api/studio/editor/projects',{method:'POST',body:{title}});$('#create-dialog').close();state.pid=created.project_id;state.edit=created;state.projects.unshift({project_id:created.project_id,title,project_path:created.project_path});renderProjects();setModule('video');await openEditor(state.pid);toast(`Proyecto creado · ${created.project_path}`)}catch(err){toast(`No se pudo crear: ${err.message}`)}});
$('#project-select').onchange=async e=>{state.pid=e.target.value||null;state.selectedClip=null;state.selectedSource=null;if(state.pid){await openEditor(state.pid)}else{syncProjectUrl(null);state.edit=null;renderEditor()}};
$('#social-toggle').onclick=()=>{const open=$('#social-panel').hidden;$('#social-panel').hidden=!open;$('#social-toggle').setAttribute('aria-expanded',String(open))};$('#social-platform').onchange=e=>{const defaults={tiktok:'9:16',instagram:'9:16',facebook:'4:5',youtube:'16:9'};$('#social-format').value=defaults[e.target.value]||'16:9'};$('#social-apply').onclick=()=>{if(!state.edit){toast('Abre un proyecto editable');return}command({operation:'output',ratio:$('#social-format').value,fps:state.edit.edit_decisions.output?.fps||24})};
function syncProjectUrl(projectId){const url=new URL(location.href);if(projectId)url.searchParams.set('project',projectId);else url.searchParams.delete('project');history.replaceState(null,'',url.pathname+url.search+url.hash)}
async function openEditor(pid){if(state.pid!==pid){stopRenderPolling();state.renderTask=null;state.previewRenderSha=null;const prior=$('#preview-video');if(prior){prior.removeAttribute('src');prior.load()}}state.pid=pid;syncProjectUrl(pid);try{const result=await req(`/api/studio/editor/${encodeURIComponent(pid)}`);state.edit=result;$('#editor-lock').hidden=true;$('#project-path').textContent=result.workspace?.project_path||state.projects.find(p=>p.project_id===pid)?.project_path||'Ruta no declarada';$('#project-path').title=$('#project-path').textContent;$('#edit-revision').textContent=`Revisión ${result.revision??'—'}`;$('#aspect-select').value=result.edit_decisions?.output?.ratio||'16:9';const style=result.edit_decisions?.subtitle_style||{};$('#subtitle-size').value=String(style.size||32);$('#subtitle-position').value=style.position||'bottom';$('#subtitle-mode').value=style.mode||'soft';$('#subtitle-language').value=style.language||'und';$('#subtitle-style-apply').disabled=false;$('#edit-save').disabled=false;$('#edit-export').disabled=false;$('#preview-refresh').disabled=false;renderEditor();await resumeRender(pid);await loadComfyHistory(pid);if(!$('#agent-drawer').hidden)await loadAgentActivity()}catch(err){state.edit=null;$('#subtitle-style-apply').disabled=true;$('#editor-lock').hidden=false;$('#editor-lock').textContent=`Este servidor no puede abrir el proyecto editable: ${err.message}. No se ha cambiado ni creado ningún dato.`;renderEditor()}}
async function loadComfyHistory(pid){const host=$('#comfy-history-result');if(!host||!pid)return;const data=await tryApi(`/api/studio/comfy-history/projects/${encodeURIComponent(pid)}`);if(state.pid!==pid)return;host.replaceChildren();if(data.__error){const note=document.createElement('div');note.className='empty-state';note.textContent='No se pudieron consultar los informes de este proyecto.';host.append(note);return}const reports=Array.isArray(data.reports)?data.reports:[];if(!reports.length){const note=document.createElement('div');note.className='empty-state';note.textContent='Aún no hay informes guardados en este proyecto.';host.append(note);return}for(const report of [...reports].reverse()){const card=document.createElement('article');card.className='comfy-history-report';const title=document.createElement('strong');title.textContent=`Informe · ${report.imported_at||'fecha desconocida'}`;const summary=document.createElement('small');const jobs=Array.isArray(report.jobs)?report.jobs:[];const completed=jobs.filter(job=>job.status==='completed').length;const failed=jobs.filter(job=>job.status==='failed').length;const unknown=jobs.length-completed-failed;summary.textContent=`${jobs.length} trabajos · ${completed} completados · ${failed} fallidos · ${unknown} desconocidos`;card.append(title,summary);host.append(card)}}
$('#comfy-history-import').onclick=async()=>{const status=$('#comfy-history-status'),button=$('#comfy-history-import'),pid=state.pid;if(!pid){status.textContent='Selecciona un proyecto antes de guardar el informe.';return}let historyValue;try{historyValue=JSON.parse($('#comfy-history').value)}catch{status.textContent='El contenido no es JSON válido.';return}if(!historyValue||Array.isArray(historyValue)||typeof historyValue!=='object'){status.textContent='El historial debe ser un objeto JSON.';return}button.disabled=true;status.textContent='Guardando resumen en el proyecto…';try{const saved=await req(`/api/studio/comfy-history/projects/${encodeURIComponent(pid)}`,{method:'POST',body:historyValue});status.textContent=saved.duplicate?'Este informe ya estaba guardado en el proyecto.':'Informe guardado en el proyecto.';$('#comfy-history').value='';await loadComfyHistory(pid)}catch(error){status.textContent=`No se guardó el informe: ${error.message}`}finally{button.disabled=false}};
function edited(){if(!state.edit)return;const currentPreview=$('#preview-video');if(currentPreview?.getAttribute('src')&&state.previewRenderSha&&state.edit.render_sha256&&state.previewRenderSha!==state.edit.render_sha256){currentPreview.removeAttribute('src');currentPreview.load();state.previewRenderSha=null;$('#viewer-empty').hidden=false;$('#preview-status').textContent='El montaje cambió; prepara una nueva vista previa.'}const edl=state.edit.edit_decisions||{};const sources=edl.sources||{};const media=$('#media-list');media.replaceChildren();let count=0;for(const [id,src] of Object.entries(sources)){count++;const row=document.createElement('button');row.className='media-row'+(state.selectedSource===id?' selected':'');row.type='button';const icon=document.createElement('span');icon.className='media-kind';icon.innerHTML=src.kind==='audio'?'<svg><use href="#i-audio"/></svg>':'<svg><use href="#i-video"/></svg>';const label=document.createElement('span');label.className='media-label';const strong=document.createElement('strong');strong.textContent=src.original_name||src.path;const small=document.createElement('small');small.textContent=`${src.kind||'medio'} · ${src.duration?Number(src.duration).toFixed(1)+' s':'duración no disponible'}`;label.append(strong,small);row.append(icon,label);row.onclick=()=>{state.selectedSource=id;state.selectedGeneratedRequestId=null;renderEditor()};row.ondblclick=()=>addSource(id);media.append(row)}$('#media-count').textContent=`${count} elemento${count===1?'':'s'}`;if(!count)media.innerHTML='<div class="empty-state">Importa medios propios<br><small>Se copian al proyecto; el original se conserva.</small></div>';const cuts=edl.cuts||[],audio=edl.audio_tracks||[];renderTracks(cuts,audio,edl);renderInspector(edl);renderCues(edl);$('#edit-revision').textContent=`Revisión ${state.edit.revision??'—'}`;$('#edit-undo').disabled=!(state.edit.undo||[]).length;$('#edit-redo').disabled=!(state.edit.redo||[]).length;$('#timeline-add').disabled=!state.selectedSource;$('#clip-split').disabled=!state.selectedClip;$('#clip-remove').disabled=!state.selectedClip;$('#subtitle-add').disabled=false;$('#subtitle-download').href=`/api/studio/editor/${encodeURIComponent(state.pid)}/subtitles`;$('#subtitle-download').classList.remove('disabled-link');$('#subtitle-download').setAttribute('aria-disabled','false');$('#viewer-empty').hidden=!!$('#preview-video').getAttribute('src');$('#audio-status').textContent=`${audio.length} pista${audio.length===1?'':'s'} en el proyecto`;$('#audio-tracks').replaceChildren(...audio.map((clip,i)=>audioCard(clip,i)));renderOutputMix(edl.audio_mix||{});$('#library-list').replaceChildren(...Object.entries(sources).map(([id,s])=>libraryCard(id,s)));$('#timeline-duration').textContent=`Duración: ${timelineDuration(cuts,audio,edl.output?.fps||24).toFixed(2)} s`;$('#edit-dirty').textContent='Guardado';$('#edit-export').disabled=!cuts.length;$('#preview-refresh').disabled=!cuts.length;syncRenderControls()}
function renderEditor(){if(!state.edit){$('#media-list').innerHTML='<div class="empty-state">Abre un proyecto editable<br><small>Los originales se copian dentro del proyecto.</small></div>';$('#media-count').textContent='0 elementos';$('#timeline-tracks').innerHTML='<div class="empty-track">La línea de tiempo está vacía</div>';$('#inspector').innerHTML='<div class="empty-state">Selecciona un clip</div>';$('#subtitle-list').innerHTML='<div class="empty-state">Selecciona un proyecto con vídeo para editar bloques.</div>';$('#audio-tracks').innerHTML='<div class="empty-state">Abre un proyecto editable para ver y ajustar sus pistas de audio.</div>';$('#edit-save').disabled=$('#edit-export').disabled=$('#preview-refresh').disabled=$('#timeline-add').disabled=true;$('#subtitle-download').classList.add('disabled-link');return}edited()}
function renderTracks(cuts,audio,edl){const root=$('#timeline-tracks');root.replaceChildren();if(!cuts.length&&!audio.length){root.innerHTML='<div class="empty-track">La línea de tiempo está vacía</div>';return}const videos=document.createElement('div');videos.className='track-row';const vname=document.createElement('div');vname.className='track-name';vname.textContent='Vídeo';const vlane=document.createElement('div');vlane.className='track-lane';cuts.forEach((clip,index)=>vlane.append(clipButton(clip,index,'video',edl)));videos.append(vname,vlane);root.append(videos);const ar=document.createElement('div');ar.className='track-row';const an=document.createElement('div');an.className='track-name';an.textContent='Audio';const al=document.createElement('div');al.className='track-lane';audio.forEach((clip,index)=>al.append(clipButton(clip,index,'audio',edl)));ar.append(an,al);root.append(ar);const cues=edl.cues||[];const sr=document.createElement('div');sr.className='track-row';const sn=document.createElement('div');sn.className='track-name';sn.textContent='Subtítulos';const sl=document.createElement('div');sl.className='track-lane';for(const cue of cues.slice(0,60)){const block=document.createElement('div');block.className='timeline-clip';block.style.background='#3a2c4f';block.style.borderColor='#7957a8';block.title=`${cue.start_seconds}–${cue.end_seconds} s`;block.innerHTML=`<span>${esc(cue.text)}</span>`;sl.append(block)}sr.append(sn,sl);root.append(sr);$('#ruler-time').textContent=`${timelineDuration(cuts,audio,edl.output?.fps||24).toFixed(1)} s`}
function clipButton(clip,index,track,edl){const b=document.createElement('button');b.type='button';b.className='timeline-clip '+(track==='audio'?'audio ':'')+(state.selectedClip===clip.id?'selected':'');b.title=`${clip.source} · ${clip.in_seconds}–${clip.out_seconds} s`;const name=edl.sources?.[clip.source_id]?.original_name||clip.source||'Clip';const span=document.createElement('span');span.textContent=`${index+1}. ${name}`;const duration=document.createElement('small');duration.textContent=`${Math.max(0,clip.out_seconds-clip.in_seconds).toFixed(1)}s`;b.append(span,duration);b.onclick=()=>{state.selectedClip=clip.id;state.selectedTrack=track;renderEditor()};return b}
function timelineDuration(cuts,audio=[],fps=24){const frameRate=Number(fps)||24;const videoEnd=cuts.reduce((sum,c)=>sum+Math.round((Number(c.out_seconds)-Number(c.in_seconds))/(Number(c.speed)||1)*frameRate)/frameRate,0);const audioEnd=audio.reduce((end,c)=>{const duration=Math.round((Number(c.out_seconds)-Number(c.in_seconds))/(Number(c.speed)||1)*frameRate)/frameRate;return Math.max(end,(Number(c.start_seconds)||0)+Math.max(0,duration))},0);return Math.max(videoEnd,audioEnd)}
function renderInspector(edl){const box=$('#inspector');box.replaceChildren();const clip=[...(state.selectedTrack==='audio'?edl.audio_tracks||[]:edl.cuts||[])].find(x=>x.id===state.selectedClip);if(!clip){box.innerHTML='<div class="empty-state">Selecciona un clip<br><small>Los controles disponibles aparecerán aquí.</small></div>';return}const source=edl.sources?.[clip.source_id];const title=document.createElement('h3');title.className='clip-title';title.textContent=source?.original_name||clip.source||'Clip';box.append(title);for(const [key,label] of [['in_seconds','Entrada (s)'],['out_seconds','Salida (s)'],['speed','Velocidad'],['gain','Ganancia']]){if(key==='speed'&&state.selectedTrack==='audio')continue;if(key==='gain'&&state.selectedTrack!=='audio')continue;const row=document.createElement('div');row.className='field-row';const l=document.createElement('label');l.textContent=label;const inp=document.createElement('input');inp.type='number';inp.step=key.includes('seconds')?'.01':'.05';inp.value=clip[key]??(key==='gain'?1:1);inp.dataset.field=key;row.append(l,inp);box.append(row)}const actions=document.createElement('div');actions.className='field-actions';for(const [label,fn] of [['Aplicar cambios',applyInspector],['Dividir aquí',()=>command({operation:'split',id:clip.id,track:state.selectedTrack,at:Number($('#playhead').value)})],['Mover antes',()=>moveClip(-1)],['Mover después',()=>moveClip(1)],['Mute',()=>command({operation:'clip',id:clip.id,track:state.selectedTrack,muted:!clip.muted})],['Solo',()=>command({operation:'clip',id:clip.id,track:state.selectedTrack,solo:!clip.solo})]]){const b=document.createElement('button');b.className='quiet-button';b.type='button';b.textContent=label;b.onclick=fn;actions.append(b)}box.append(actions)}
function applyInspector(){const clip=(state.selectedTrack==='audio'?state.edit.edit_decisions.audio_tracks:state.edit.edit_decisions.cuts).find(x=>x.id===state.selectedClip);if(!clip)return;const body={operation:'trim',id:clip.id,track:state.selectedTrack,in_seconds:Number($('[data-field="in_seconds"]').value),out_seconds:Number($('[data-field="out_seconds"]').value)};command(body)}
function moveClip(delta){const arr=state.selectedTrack==='audio'?state.edit.edit_decisions.audio_tracks:state.edit.edit_decisions.cuts;const i=arr.findIndex(x=>x.id===state.selectedClip),next=Math.min(arr.length-1,Math.max(0,i+delta));if(i<0||next===i)return;command({operation:'move',id:state.selectedClip,track:state.selectedTrack,index:next})}
async function command(payload){if(!state.pid||!state.edit||state.busy)return;state.busy=true;try{const result=await req(`/api/studio/editor/${encodeURIComponent(state.pid)}/command`,{method:'POST',body:{...payload,revision:state.edit.revision}});state.edit=result;renderEditor();toast('Cambio aplicado · puedes deshacerlo')}catch(e){toast(`No se aplicó el cambio: ${e.message}`);await openEditor(state.pid)}finally{state.busy=false;if(state.edit)renderOutputMix(state.edit.edit_decisions?.audio_mix||{})}}
function hasCapability(name){const caps=state.capabilities;if(!caps||state.identity?.restart_required!==false)return false;const entries=Array.isArray(caps.commands)?caps.commands:Array.isArray(caps.operations)?caps.operations:Object.keys(caps.commands||{});return entries.some(entry=>(typeof entry==='string'?entry:entry?.name)===name)}
function renderOutputMix(mix={}){const panel=$('#audio-output-mix-panel'),form=$('#audio-output-mix-form');if(!panel||!form)return;const available=hasCapability('audio_mix');panel.hidden=!available;if(!available)return;const canEdit=!!state.pid&&!!state.edit&&!state.busy;form.elements.gain.value=String(mix.gain??1);form.elements.normalize.checked=!!mix.normalize;form.elements.target_lufs.value=String(mix.target_lufs??-16);form.elements.target_lufs.disabled=!canEdit||!form.elements.normalize.checked;for(const control of form.elements)control.disabled=!canEdit||(control.name==='target_lufs'&&!form.elements.normalize.checked);$('#audio-output-mix-apply').disabled=!canEdit;$('#audio-output-mix-status').textContent=state.pid?'Montaje editable':'Selecciona un proyecto'}
$('#audio-output-mix-form')?.addEventListener('submit',event=>{event.preventDefault();if(!hasCapability('audio_mix')||!state.edit)return;const form=event.currentTarget,gain=Number(form.elements.gain.value),target=Number(form.elements.target_lufs.value),normalize=form.elements.normalize.checked;if(!Number.isFinite(gain)||gain<0||gain>4){toast('La ganancia debe estar entre 0 y 4');return}if(!Number.isFinite(target)||target< -40||target> -5){toast('El objetivo LUFS debe estar entre -40 y -5');return}command({operation:'audio_mix',gain,normalize,target_lufs:target})});
$('#audio-output-mix-form')?.elements.normalize.addEventListener('change',event=>{$('#audio-output-mix-form').elements.target_lufs.disabled=!event.target.checked||!state.edit||!hasCapability('audio_mix')});
async function addSource(id){await command({operation:'add',source_id:id})}
$('#timeline-add').onclick=()=>state.selectedSource&&addSource(state.selectedSource);$('#clip-split').onclick=()=>command({operation:'split',id:state.selectedClip,track:state.selectedTrack,at:Number($('#playhead').value)});$('#clip-remove').onclick=()=>command({operation:'remove',id:state.selectedClip,track:state.selectedTrack});$('#edit-undo').onclick=()=>command({operation:'undo'});$('#edit-redo').onclick=()=>command({operation:'redo'});$('#edit-save').onclick=()=>command({operation:'save'});$('#aspect-select').onchange=e=>{if(state.edit)command({operation:'output',ratio:e.target.value,fps:state.edit.edit_decisions.output?.fps||24})};$('#playhead').oninput=e=>{$('#timecode').textContent=secondsTime(Number(e.target.value))};function secondsTime(s){const fps=state.edit?.edit_decisions?.output?.fps||24,frame=Math.floor((s%1)*fps),total=Math.max(0,Math.floor(s));return`${String(Math.floor(total/3600)).padStart(2,'0')}:${String(Math.floor(total/60)%60).padStart(2,'0')}:${String(total%60).padStart(2,'0')}:${String(frame).padStart(2,'0')}`}
$('#media-file').addEventListener('change',e=>uploadFiles(e.target.files));$('#library-file').addEventListener('change',e=>uploadFiles(e.target.files));async function uploadFiles(files){if(!state.pid||!state.edit){toast('Abre primero un proyecto editable');return}for(const file of files){try{const response=await fetch(`/api/studio/editor/${encodeURIComponent(state.pid)}/upload?filename=${encodeURIComponent(file.name)}&revision=${state.edit.revision}`,{method:'POST',body:file});if(!response.ok){let err=`HTTP ${response.status}`;try{err=(await response.json()).detail||err}catch{}throw Error(err)}state.edit=await response.json()}catch(err){toast(`No se importó ${file.name}: ${err.message}`);break}}eReset();renderEditor();toast('Importación copiada al proyecto; origen conservado')}function eReset(){for(const id of ['media-file','library-file'])$('#'+id).value=''}
function stopRenderPolling(){if(state.renderTimer){clearInterval(state.renderTimer);state.renderTimer=null}}
function syncRenderControls(){
  const task=state.renderTask,current=!!task&&task.pid===state.pid&&task.pending,uncertain=current&&task.status==='unknown';
  const canRender=!!state.pid&&!!state.edit&&(state.edit.edit_decisions?.cuts||[]).length>0;
  $('#preview-refresh-label').textContent=uncertain?'Consultar estado':'Previsualizar';
  $('#preview-refresh').disabled=!canRender||(current&&!uncertain);
  $('#edit-export').disabled=!canRender||current;
  const activeStates=['running','cancelling'];
  const canCancel=current&&!!task.attempt&&(activeStates.includes(task.status)||activeStates.includes(task.lastStatus));
  const cancel=$('#edit-render-cancel');
  cancel.hidden=!canCancel;
  cancel.disabled=!!task?.cancelPending||!!task?.cancelRequested||task?.status==='cancelling';
  cancel.textContent=task?.status==='cancelling'||task?.cancelRequested?'Cancelando…':'Cancelar render';
}
function setRenderStatus(pid,message){if(state.pid===pid)$('#preview-status').textContent=message}
function finishRender(task,result){
  if(state.renderTask?.token!==task.token)return;
  stopRenderPolling();state.renderTask=null;
  if(state.pid===task.pid){
    const status=result?.status||'unknown';
    $('#preview-status').textContent=status==='idle'?'No hay un render activo; no se inició.':`${task.preview?'Vista previa':'Exportación'}: ${status}`;
    if(result?.url){
      const video=$('#preview-video');
      if(result.current===true){state.previewRenderSha=result.render_sha256||result.edit_sha256||null;video.src=result.url;video.load();$('#viewer-empty').hidden=true}
      else{state.previewRenderSha=null;video.removeAttribute('src');video.load();$('#viewer-empty').hidden=false;$('#preview-status').textContent='La vista previa ya no corresponde al montaje actual. Prepárala de nuevo.'}
    }
    if(result?.error)toast(result.error);
  }
  syncRenderControls();
}
async function resumeRender(pid){
  const result=await tryApi(`/api/studio/editor/${encodeURIComponent(pid)}/render`);
  if(state.pid!==pid||result.__error||!['running','cancelling'].includes(result.status))return;
  const token=++state.renderPollToken;
  state.renderTask={pid,preview:result.preview===true,attempt:result.attempt||null,status:result.status,lastStatus:result.status,pending:true,cancelRequested:result.status==='cancelling',cancelPending:false,token};
  syncRenderControls();setRenderStatus(pid,result.status==='cancelling'?'Reanudando seguimiento de cancelación…':'Render en curso; seguimiento recuperado.');
  pollRender(token);
}
function pollRender(token){
  stopRenderPolling();let checks=0,checking=false;
  const check=async()=>{
    const task=state.renderTask;if(!task||task.token!==token||checking)return;
    checking=true;checks++;
    const result=await tryApi(`/api/studio/editor/${encodeURIComponent(task.pid)}/render`);
    const current=state.renderTask;
    if(!current||current.token!==token){checking=false;return}
    if(result.__error){
      current.status='unknown';setRenderStatus(current.pid,'No se pudo confirmar el estado; consulta de nuevo antes de iniciar otro render.');syncRenderControls();
    }else{
      if(typeof result.attempt==='string'&&result.attempt)current.attempt=result.attempt;
      if(['running','cancelling'].includes(result.status)){
        current.status=result.status;current.lastStatus=result.status;
        if(result.status==='cancelling')current.cancelRequested=true;
        if(result.status==='running'&&current.cancelRequested&&!current.cancelPending){current.cancelRequested=false;setRenderStatus(current.pid,'La consulta confirma que el render sigue activo; ya puedes reintentar la cancelación de este mismo intento.');}
        else setRenderStatus(current.pid,result.status==='cancelling'?'Cancelación solicitada; esperando confirmación del proceso…':'Render en curso…');
        syncRenderControls();
      }else if(['completed','failed','cancelled','error','idle'].includes(result.status)){
        checking=false;finishRender(current,result);return;
      }else{
        current.status='unknown';setRenderStatus(current.pid,'Estado sin confirmar; no repitas el inicio. Consulta de nuevo.');syncRenderControls();
      }
    }
    checking=false;
    if(checks>=90){stopRenderPolling();setRenderStatus(task.pid,'Seguimiento en pausa; pulsa «Consultar estado» antes de volver a iniciar.');if(state.renderTask?.token===token){state.renderTask.status='unknown';syncRenderControls()}}
  };
  state.renderTimer=setInterval(check,1500);check();
}
async function startRender(preview){
  const existing=state.renderTask;
  if(existing?.pid===state.pid&&existing.pending){pollRender(existing.token);return}
  if(!state.pid||!state.edit)return;
  stopRenderPolling();const token=++state.renderPollToken,pid=state.pid;
  const task={pid,preview,attempt:null,status:'starting',lastStatus:null,pending:true,cancelRequested:false,cancelPending:false,token};state.renderTask=task;
  syncRenderControls();setRenderStatus(pid,preview?'Preparando vista previa…':'Exportando…');
  try{
    const result=await req(`/api/studio/editor/${encodeURIComponent(pid)}/render`,{method:'POST',body:{revision:state.edit.revision,preview}});
    if(state.renderTask?.token!==token)return;
    if(typeof result.attempt==='string'&&result.attempt)task.attempt=result.attempt;
    task.status=result.status||'running';task.lastStatus=task.status;
  }catch(error){
    if(state.renderTask?.token!==token)return;
    task.status='unknown';setRenderStatus(pid,`No se confirmó el inicio (${error.message}); consultando estado sin repetir la solicitud.`);
  }
  syncRenderControls();pollRender(token);
}
async function cancelRender(){
  const task=state.renderTask;
  if(!task||task.pid!==state.pid||!task.pending||!task.attempt||task.cancelRequested||task.cancelPending)return;
  task.cancelRequested=true;task.cancelPending=true;task.status='cancelling';syncRenderControls();setRenderStatus(task.pid,'Solicitando cancelación…');
  try{
    const result=await req(`/api/studio/editor/${encodeURIComponent(task.pid)}/render/cancel`,{method:'POST',body:{attempt:task.attempt}});
    if(state.renderTask?.token!==task.token)return;
    task.cancelPending=false;task.status=result.status||'cancelling';task.lastStatus=task.status;setRenderStatus(task.pid,'Cancelación solicitada; verificando que termine el proceso.');
  }catch(error){
    if(state.renderTask?.token!==task.token)return;
    task.cancelPending=false;task.status='unknown';setRenderStatus(task.pid,`Respuesta de cancelación incierta (${error.message}); consultando estado sin repetir.`);
  }
  syncRenderControls();pollRender(task.token);
}
$('#preview-refresh').onclick=()=>{const task=state.renderTask;if(task?.pid===state.pid&&task.pending){pollRender(task.token);return}startRender(true)};
$('#edit-export').onclick=()=>{if(state.renderTask?.pid===state.pid&&state.renderTask.pending){pollRender(state.renderTask.token);return}if(!state.pid)return;if(!confirm('Exportar el montaje del proyecto a su destino local?'))return;startRender(false)};
$('#edit-render-cancel').onclick=cancelRender;
function audioCard(clip,index){const wrap=document.createElement('div');wrap.className='audio-track';const info=document.createElement('div'),name=document.createElement('strong'),small=document.createElement('small');name.textContent=state.edit.edit_decisions.sources?.[clip.source_id]?.original_name||clip.source||`Pista ${index+1}`;small.textContent=`${clip.muted?'Silenciada':clip.solo?'Solo':'Activa'} · ganancia ${clip.gain??1}`;info.append(name,small);const range=document.createElement('input');range.type='range';range.min='0';range.max='2';range.step='.01';range.value=clip.gain??1;range.setAttribute('aria-label',`Ganancia de ${name.textContent}`);range.onchange=()=>command({operation:'clip',id:clip.id,track:'audio',gain:Number(range.value)});const buttons=document.createElement('div');for(const flag of ['muted','solo']){const b=document.createElement('button');b.className='quiet-button';b.textContent=flag==='muted'?'Mute':'Solo';b.setAttribute('aria-pressed',String(!!clip[flag]));b.onclick=()=>command({operation:'clip',id:clip.id,track:'audio',[flag]:!clip[flag]});buttons.append(b)}wrap.append(info,range,buttons);return wrap}
function libraryCard(id,s){const d=document.createElement('article');d.className='library-card';const title=document.createElement('strong');title.textContent=s.original_name||s.path;const meta=document.createElement('small');meta.textContent=`${s.kind||'medio'} · ${s.bytes??'tamaño desconocido'} bytes · SHA-256 ${s.sha256||'no disponible'}`;d.append(title,meta);return d}
function renderCues(edl){const root=$('#subtitle-list');root.replaceChildren();const cues=edl.cues||[];if(!cues.length){root.innerHTML='<div class="empty-state">No hay bloques de subtítulos. Importa un SRT para empezar.</div>';return}cues.forEach((cue,index)=>{const row=document.createElement('div');row.className='cue-row';const start=document.createElement('input');start.type='number';start.step='.01';start.value=cue.start_seconds;start.setAttribute('aria-label',`Inicio del bloque ${index+1}`);const end=document.createElement('input');end.type='number';end.step='.01';end.value=cue.end_seconds;end.setAttribute('aria-label',`Fin del bloque ${index+1}`);const text=document.createElement('textarea');text.value=cue.text;text.rows=1;text.setAttribute('aria-label',`Texto del bloque ${index+1}`);const actions=document.createElement('div');actions.className='cue-actions';const save=document.createElement('button');save.className='quiet-button';save.textContent='Aplicar';save.onclick=()=>command({operation:'cue_update',index,start_seconds:Number(start.value),end_seconds:Number(end.value),text:text.value});const measure=document.createElement('button');measure.className='quiet-button';measure.textContent='Medir glifos';measure.disabled=edl.subtitle_style?.mode!=='burn';measure.title=measure.disabled?'La medición con FFmpeg solo aplica a subtítulos quemados.':'';const result=document.createElement('small');result.className='cue-measurement';result.setAttribute('aria-live','polite');measure.onclick=async()=>{const revision=state.edit?.revision;measure.disabled=true;result.textContent='Midiendo con FFmpeg local…';try{const value=await req(`/api/studio/editor/${encodeURIComponent(state.pid)}/subtitles/quality/cues/${index}/glyphs`);if(state.edit?.revision!==revision)return;if(value.revision!==revision)throw Error('El montaje cambió; vuelve a medir.');if(!value.bbox){result.textContent=value.status==='no_glyph_pixels'?'No se detectaron píxeles de texto.':'Sin caja medible.';return}const [x1,y1,x2,y2]=value.bbox;result.textContent=`Caja ${x1},${y1}–${x2},${y2} px · ${value.fits_safe_area?'dentro':'fuera'} del área segura (${value.width}×${value.height})`;result.dataset.state=value.fits_safe_area?'ok':'warning'}catch(error){result.textContent=`Medición no disponible: ${error.message}`}finally{if(state.edit?.revision===revision)measure.disabled=edl.subtitle_style?.mode!=='burn'}};actions.append(save,measure,result);row.append(start,end,text,actions);root.append(row)})}
$('#subtitle-file').addEventListener('change',async e=>{const file=e.target.files?.[0];if(!file||!state.pid||!state.edit){toast('Abre un proyecto editable antes de importar subtítulos');return}try{const response=await fetch(`/api/studio/editor/${encodeURIComponent(state.pid)}/subtitles/import?filename=${encodeURIComponent(file.name)}&revision=${state.edit.revision}`,{method:'POST',body:file});if(!response.ok){const x=await response.json().catch(()=>({}));throw Error(x.detail||`HTTP ${response.status}`)}state.edit=await response.json();renderEditor();toast('SRT importado; original conservado en el proyecto')}catch(err){toast(`No se importó el SRT: ${err.message}`)}finally{e.target.value=''}});$('#subtitle-add').disabled=true;$('#subtitle-add').title='La API activa no ofrece insertar un bloque vacío; importa un SRT y edita sus bloques.';
$('#subtitle-style-apply').onclick=()=>command({operation:'subtitle_style',size:Number($('#subtitle-size').value),position:$('#subtitle-position').value,mode:$('#subtitle-mode').value,language:$('#subtitle-language').value});
const studioChannelFilterNumeric=['min_views','max_views','max_channel_age_days','min_subscribers','max_subscribers','min_minutes','max_minutes','min_publication_views','min_matching_publications','sample_size'];let studioAppliedChannelFilters={sample_size:10,published_within:'month',discovery_mode:'recent_publications',sort_by:'matching_publication_views'};let studioChannelFilterSnapshot=[];function readStudioChannelFilters(){const form=$('#channel-filter-form'),filters={};for(const [name,raw]of new FormData(form)){if(raw==='')continue;let value=raw;if(studioChannelFilterNumeric.includes(name)){value=Number(raw);if(!Number.isSafeInteger(value)||value<0)throw Error('Usa n\u00fameros enteros no negativos.')}filters[name]=name==='country'?value.toUpperCase():value}for(const [low,high]of [['min_views','max_views'],['min_subscribers','max_subscribers'],['min_minutes','max_minutes']])if(filters[low]!==undefined&&filters[high]!==undefined&&filters[low]>filters[high])throw Error('El m\u00ednimo no puede superar al m\u00e1ximo.');if(filters.min_matching_publications<1||filters.min_matching_publications>filters.sample_size)throw Error('Las coincidencias m\u00ednimas deben estar entre 1 y el tama\u00f1o de la muestra.');if(filters.discovery_mode==='recent_publications'&&filters.published_within==='any')throw Error('Selecciona una fecha reciente para descubrir canales por publicaciones.');if(filters.sort_by==='matching_publication_views'&&filters.published_within==='any')throw Error('Selecciona una fecha reciente para ordenar por publicaciones coincidentes.');return filters}function restoreStudioChannelFilterValues(values){const form=$('#channel-filter-form');for(const [name,value]of values)form.elements.namedItem(name).value=value}const studioChannelFilterDialog=$('#channel-filter-dialog'),studioChannelFilterForm=$('#channel-filter-form');$('#channel-filter-open').onclick=()=>{studioChannelFilterSnapshot=[...new FormData(studioChannelFilterForm)];$('#channel-filter-error').textContent='';studioChannelFilterDialog.showModal()};function cancelStudioChannelFilters(){restoreStudioChannelFilterValues(studioChannelFilterSnapshot);studioChannelFilterDialog.close()}$('#channel-filter-close').onclick=cancelStudioChannelFilters;$('#channel-filter-cancel').onclick=cancelStudioChannelFilters;studioChannelFilterDialog.addEventListener('cancel',event=>{event.preventDefault();cancelStudioChannelFilters()});$('#channel-filter-reset').onclick=()=>studioChannelFilterForm.reset();$('#channel-recent-preset').onclick=()=>{for(const name of ['min_views','max_views','max_channel_age_days'])studioChannelFilterForm.elements.namedItem(name).value='';restoreStudioChannelFilterValues([['published_within','month'],['min_publication_views','100000'],['min_matching_publications','3'],['sample_size','20'],['sort_by','matching_publication_views'],['discovery_mode','recent_publications']])};$('#channel-young-preset').onclick=()=>{studioChannelFilterForm.elements.namedItem('min_views').value='1000000';studioChannelFilterForm.elements.namedItem('max_views').value='';studioChannelFilterForm.elements.namedItem('max_channel_age_days').value='90'};studioChannelFilterForm.onsubmit=event=>{event.preventDefault();try{studioAppliedChannelFilters=readStudioChannelFilters();studioChannelFilterDialog.close();const count=Object.entries(studioAppliedChannelFilters).filter(([key,value])=>key!=='sample_size'&&key!=='sort_by'&&key!=='discovery_mode'&&value!=='any'&&!(key==='min_matching_publications'&&value===1)&&!(['min_views','min_minutes','min_publication_views'].includes(key)&&value===0)).length;$('#channel-filter-count').textContent=count?'('+count+')':'';const root=$('#channel-results');root.replaceChildren();const message=document.createElement('div');message.className='empty-state';message.textContent='Filtros aplicados. Pulsa Consultar YouTube para buscar.';root.append(message)}catch(error){$('#channel-filter-error').textContent=error.message}};
async function loadChannelStatus(){const [config,status]=await Promise.all([tryApi('/api/research/channels/configuration'),tryApi('/api/research/channels/status')]);const statusKnown=!!status&&!status.__error&&!config?.__error;const configured=statusKnown&&status.configured===true;const badge=$('#channel-connector'),submit=$('#channel-submit'),readiness=$('#channel-readiness');badge.textContent=config?.__error?'API de canales no disponible':status?.__error?'YouTube \u00b7 estado no disponible':configured?'YouTube \u00b7 conector configurado':'YouTube \u00b7 requiere configuraci\u00f3n';badge.classList.toggle('neutral',!configured);submit.disabled=!configured;submit.textContent=configured?'Consultar YouTube':'Requiere configuraci\u00f3n';submit.title=configured?'Consulta p\u00fablica bajo demanda':'El servidor debe confirmar la configuraci\u00f3n antes de habilitar consultas';readiness.dataset.state=configured?'ready':'blocked';readiness.textContent=configured?'Configuraci\u00f3n detectada; consulta sujeta a cuota y respuesta p\u00fablica.':statusKnown?'Configura el conector en el servidor para habilitar la consulta.':'No se pudo confirmar la configuraci\u00f3n; la consulta permanece desactivada.'}
$('#channel-form').onsubmit=async e=>{e.preventDefault();const query=$('#channel-query').value.trim();if(!query)return;const box=$('#channel-results'),submit=$('#channel-submit'),filterButton=$('#channel-filter-open'),wasEnabled=!submit.disabled;submit.disabled=true;filterButton.disabled=true;box.replaceChildren();const pending=document.createElement('div');pending.className='empty-state';pending.textContent='Consultando YouTube con los filtros seleccionados\u2026';box.append(pending);try{const data=await req('/api/research/channels',{method:'POST',body:{query,pages:Number($('#channel-pages').value),filters:{...studioAppliedChannelFilters}}});renderChannelResults(data)}catch(err){box.replaceChildren();const card=document.createElement('article');card.className='result-card';const h=document.createElement('h3');h.textContent='Consulta no completada';const p=document.createElement('p');p.textContent=err.message;card.append(h,p);box.append(card)}finally{submit.disabled=!wasEnabled;filterButton.disabled=false}};
function renderChannelResults(data){const root=$('#channel-results');root.replaceChildren();const meta=document.createElement('article');meta.className='result-card';const heading=document.createElement('h3');heading.textContent='Alcance de la consulta';const p=document.createElement('p');p.textContent=`Fuente: ${data.source||data.provider||'YouTube Data API'} · Consultado: ${data.retrieved_at||data.retrieved_at_utc||'fecha no devuelta'} · Resultado: ${data.result_type||'respuesta del conector'}`;meta.append(heading,p);root.append(meta);const list=Array.isArray(data.channels)?data.channels:Array.isArray(data.results)?data.results:Array.isArray(data.items)?data.items:[];if(!list.length){const pre=document.createElement('pre');pre.className='result-card';pre.textContent=JSON.stringify(data,null,2);root.append(pre);return}for(const item of list){const card=document.createElement('article');card.className='result-card';const h=document.createElement('h3');h.textContent=item.title||item.channel_title||item.name||'Canal';card.append(h);const line=document.createElement('div');line.className='result-metrics';for(const [key,label]of [['subscriber_count','Suscriptores'],['view_count','Vistas'],['video_count','Videos']]){const s=document.createElement('span');s.textContent=`${label}: ${Number.isFinite(item[key])?item[key]:'desconocido'}`;if(!Number.isFinite(item[key]))s.className='unknown-value';line.append(s)}card.append(line);const url=item.url||item.channel_url||item.custom_url;if(url){const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=url;card.append(a)}const note=document.createElement('p');note.textContent=`Datos de la respuesta del conector · fecha ${item.retrieved_at||data.retrieved_at||'no disponible'}`;card.append(note);root.append(card)}}
$('#manual-data-toggle').onclick=()=>{$('#manual-data-form').hidden=!$('#manual-data-form').hidden};$('#manual-data-save').onclick=()=>{try{const raw=$('#manual-channel-data').value.trim();if(!raw)throw Error('Añade la información y su procedencia');const record={added_at:new Date().toISOString(),source_type:'user_supplied_unverified',content:raw};const all=JSON.parse(localStorage.getItem('om.channel.notes')||'[]');all.push(record);localStorage.setItem('om.channel.notes',JSON.stringify(all));const d=document.createElement('div');d.className='result-card';const p=document.createElement('p');p.textContent=`Aportado por el usuario · ${record.added_at} · no verificado`;const pre=document.createElement('pre');pre.textContent=raw;d.append(p,pre);$('#manual-data-saved').replaceChildren(d);toast('Aporte guardado en este navegador, no en el expediente remoto')}catch(err){toast(err.message)}};
const sportsActionLabels={collectible_card:'Ficha de colección',resolve_players:'Resolver nombres de jugadores',compare_players:'Comparar jugadores',ranking:'Clasificación',matches:'Partidos',match:'Partido',player:'Datos de jugador',player_history:'Historial de jugador',historical:'Datos históricos',coaches:'Entrenadores',coach_balance:'Balance de entrenador',teams:'Equipos',team:'Equipo',squad:'Plantilla',standings:'Tabla de posiciones',head_to_head:'Enfrentamiento directo',definitions:'Definiciones'};const sportsFieldLabels={competition:'Competición',edition:'Temporada',names:'Nombres de jugadores',metrics:'Métricas',phase:'Fase',entity:'Tipo de entidad',team_id:'ID de equipo',player_id:'ID de jugador',match_id:'ID de partido',coach_id:'ID de entrenador',order:'Orden',lineups:'Incluir alineaciones',team1:'ID de primer equipo',team2:'ID de segundo equipo',metric:'Métrica'};
const competitionLabels={champions:'Liga de Campeones UEFA',women_champions:'Liga de Campeones Femenina UEFA',europa:'Liga Europa UEFA',conference:'Liga Conferencia UEFA',euro:'Eurocopa UEFA',nations:'Liga de Naciones UEFA',supercup:'Supercopa UEFA',finalissima:'Finalissima',qualifiers:'Clasificación europea'};
function renderSportsDefinitionPicker(){
  const root=$('#sports-definition-picker');if(!root)return;
  root.replaceChildren();
  const entityField=$('#sports-fields [name="entity"]'),metricsField=$('#sports-fields [name="metrics"]');
  const competition=$('#sports-competition').value,entity=entityField?.value||'';
  const actor={player:'PLAYER',players:'PLAYER',team:'TEAM',teams:'TEAM'}[entity];
  const definitions=state.sportsDefinitions;
  if(!actor||!metricsField||!Array.isArray(definitions)||state.sportsDefinitionCompetition!==competition){root.hidden=true;return}
  const items=definitions.filter(item=>item&&typeof item.name==='string'&&Array.isArray(item.actors)&&
    item.actors.some(value=>String(value).toUpperCase()===actor));
  if(!items.length){root.hidden=true;return}
  const label=document.createElement('label');label.textContent='Métrica de las definiciones oficiales';
  const select=document.createElement('select');select.setAttribute('aria-label',label.textContent);
  select.append(...items.map(item=>new Option(item.name,item.name)));label.append(select);
  const button=document.createElement('button');button.type='button';button.className='quiet-button';button.textContent='Añadir métrica elegida';
  button.addEventListener('click',()=>{
    const selected=select.value;if(!selected)return;
    const values=metricsField.value.split(',').map(value=>value.trim()).filter(value=>value&&!['standard','all'].includes(value.toLowerCase()));
    if(!values.includes(selected))values.push(selected);
    metricsField.value=values.join(', ');metricsField.dispatchEvent(new Event('input',{bubbles:true}));
  });
  const note=document.createElement('small');note.textContent='Filtrado por la competición UEFA consultada y el tipo de entidad.';
  root.append(label,button,note);root.hidden=false;
}
async function loadSportsSchema(){if(state.sportsSchema)return;const schema=await tryApi('/api/studio/football/schema');if(schema.__error){$('#sports-connector').textContent='Cobertura: UEFA \u00b7 esquema no disponible';$('#sports-connector').classList.add('neutral');return}state.sportsSchema=schema;$('#sports-connector').textContent='Cobertura: UEFA \u00b7 bajo demanda';$('#sports-connector').classList.add('neutral');$('#sports-competition').replaceChildren(...(schema.competitions||[]).map(c=>new Option(competitionLabels[c]||'Competici\u00f3n UEFA',c)));$('#sports-action').replaceChildren(...(schema.actions||[]).map(a=>new Option(sportsActionLabels[a.name]||'Consulta deportiva',a.name)));if(schema.actions?.some(a=>a.name==='compare_players'))$('#sports-action').value='compare_players';$('#sports-action').onchange=renderSportsFields;$('#sports-competition').onchange=()=>{state.sportsDefinitions=null;state.sportsDefinitionCompetition=null;renderSportsDefinitionPicker()};renderSportsFields();const note=document.createElement('span');note.textContent=schema.coverage_note||'Cobertura limitada a UEFA';$('#sports-route-note').replaceChildren(note)}
function renderSportsFields(){
  const root=$('#sports-fields');root.replaceChildren();
  const action=state.sportsSchema?.actions?.find(a=>a.name===$('#sports-action').value);
  if(!action){renderSportsDefinitionPicker();return}
  const properties=state.sportsSchema.parameters?.properties||{};
  for(const field of action.fields||[]){
    if(field==='competition')continue;
    const label=document.createElement('label');label.textContent=sportsFieldLabels[field]||'Parámetro';
    let input;
    if(field==='entity'&&action.choices?.entity){
      input=document.createElement('select');
      input.append(...action.choices.entity.map(x=>new Option(x==='player'?'Jugador':x==='team'?'Equipo':x==='players'?'Jugadores':'Equipos',x)));
      input.addEventListener('change',()=>{if(state.sportsDefinitions){const metrics=$('#sports-fields [name="metrics"]');if(metrics)metrics.value=''}renderSportsDefinitionPicker()});
    }else if(field==='phase'&&properties.phase?.enum){
      input=document.createElement('select');input.append(...properties.phase.enum.map(x=>new Option(x==='TOURNAMENT'?'Torneo':x==='QUALIFYING'?'Clasificación':'Todas las fases',x)));
    }else if(field==='order'&&properties.order?.enum){
      input=document.createElement('select');input.append(...properties.order.enum.map(x=>new Option(x==='ASC'?'Ascendente':'Descendente',x)));
    }else if(field==='lineups'){input=document.createElement('input');input.type='checkbox'}
    else if(field==='names'||field==='metrics'){input=document.createElement('textarea');input.rows=field==='names'?2:1;input.placeholder=field==='names'?'Nombre 1, Nombre 2':'standard, all o métricas separadas por comas'}
    else{input=document.createElement('input');input.type=properties[field]?.type==='integer'?'number':'text';input.autocomplete='off'}
    input.name=field;input.dataset.fieldType=field==='names'?'names':field==='metrics'?'metrics':field==='lineups'?'boolean':properties[field]?.type||'string';
    input.dataset.required=(action.required||[]).includes(field)?'true':'false';label.append(input);root.append(label);
  }
  renderSportsDefinitionPicker();
}
function prepareSportsFollowup(query){
  if(!query||typeof query!=='object'||Array.isArray(query)){toast('La consulta sugerida no tiene un formato válido.');return}
  const schema=state.sportsSchema,action=schema?.actions?.find(item=>item.name===query.action);
  if(!action||!(schema.competitions||[]).includes(query.competition)){
    toast('La sugerencia no coincide con el esquema UEFA cargado.');return
  }
  $('#sports-action').value=query.action;$('#sports-competition').value=query.competition;renderSportsFields();
  for(const field of $('#sports-fields').querySelectorAll('[name]')){
    if(!Object.prototype.hasOwnProperty.call(query,field.name))continue;
    const value=query[field.name];
    if(field.type==='checkbox'){field.checked=value===true;continue}
    if(Array.isArray(value))field.value=value.join(', ');
    else if(typeof value==='string'||typeof value==='number')field.value=String(value);
  }
  toast('Consulta preparada. Revisa los campos y pulsa «Consultar fuente».')
}
$('#sports-form').onsubmit=async e=>{
  e.preventDefault();const action=$('#sports-action').value,inputs={competition:$('#sports-competition').value,action};
  for(const el of $('#sports-fields').querySelectorAll('[name]')){
    const type=el.dataset.fieldType;let v=type==='boolean'?el.checked:el.value.trim();
    if(type!=='boolean'&&!v&&el.dataset.required==='true'){toast(`Completa el campo ${el.name}`);return}
    if(type==='boolean'){inputs[el.name]=v;continue}
    if(!v)continue;
    if(type==='names')v=v.split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean);
    else if(type==='metrics'&&v!=='standard'&&v!=='all')v=v.split(',').map(x=>x.trim()).filter(Boolean);
    else if(type==='integer'){v=Number(v);if(!Number.isSafeInteger(v)){toast(`${el.name} debe ser un número entero`);return}}
    inputs[el.name]=v
  }
  const root=$('#sports-results');state.lastSports=null;$('#sports-copy').disabled=true;root.innerHTML='<div class="empty-state">Consultando la fuente…</div>';if(action==='definitions'){state.sportsDefinitions=null;state.sportsDefinitionCompetition=null;renderSportsDefinitionPicker()}
  try{const result=await req('/api/studio/football/query',{method:'POST',body:inputs});renderSportsResult(result);if(action==='definitions'){const items=result?.success&&Array.isArray(result.data?.definiciones)?result.data.definiciones:[];state.sportsDefinitions=items;state.sportsDefinitionCompetition=inputs.competition;renderSportsDefinitionPicker()}}
  catch(err){state.lastSports=null;$('#sports-copy').disabled=true;root.replaceChildren();const p=document.createElement('p');p.textContent=err.message;root.append(p)}
};
function renderSportsResult(result){
  const root=$('#sports-results');root.replaceChildren();
  if(!result?.success){
    state.lastSports=null;$('#sports-copy').disabled=true;
    const card=document.createElement('article');card.className='result-card';
    const heading=document.createElement('h3');heading.textContent='Consulta sin resultado';
    const message=document.createElement('p');message.textContent=result?.error||'La fuente no devolvió datos';
    card.append(heading,message);root.append(card);return
  }
  state.lastSports=result;$('#sports-copy').disabled=false;
  const data=result.data||{},card=document.createElement('article');card.className='result-card';
  const h=document.createElement('h3');h.textContent=sportsActionLabels[$('#sports-action').value]||'Resultado oficial';
  const meta=document.createElement('p');meta.textContent=`Fuente: ${data.fuente||'UEFA'} · Consulta local: ${new Date().toISOString()} · Estadísticas persistidas: no`;card.append(h,meta);
  for(const [key,value] of Object.entries(data.alcance||{})){const p=document.createElement('p');p.textContent=`${sportsFieldLabels[key]||'Contexto'}: ${value??'desconocido'}`;card.append(p)}
  const rows=Array.isArray(data.registros)?data.registros:Array.isArray(data.records)?data.records:[];
  if(rows.length){const list=document.createElement('div');list.className='result-rows';for(const row of rows){const p=document.createElement('p');p.textContent=Object.entries(row).map(([k,v])=>`${sportsFieldLabels[k]||k}: ${v??'desconocido'}`).join(' · ');list.append(p)}card.append(list)}
  else{const pre=document.createElement('pre');pre.textContent=JSON.stringify(data,null,2);card.append(pre)}
  const note=document.createElement('p');note.textContent=result.note||'Respeta temporada, fase, fuente y contexto devueltos por la respuesta oficial.';card.append(note);
  const followups=Array.isArray(result.followups)?result.followups:Array.isArray(data.followups)?data.followups:[];
  const actions=document.createElement('div');actions.className='sports-followups';
  for(const item of followups.slice(0,20)){
    if(!item||typeof item.label!=='string'||!item.label.trim()||item.label.length>120)continue;
    const button=document.createElement('button');button.type='button';button.className='quiet-button';button.textContent=item.label.trim();
    button.addEventListener('click',()=>prepareSportsFollowup(item.query));actions.append(button)
  }
  if(actions.childElementCount){const title=document.createElement('h4');title.textContent='Siguientes consultas';card.append(title,actions)}
  root.append(card)
}
$('#sports-copy').onclick=async()=>{if(!state.lastSports)return;await navigator.clipboard.writeText(JSON.stringify(state.lastSports.data,null,2));toast('Comparativa copiada')};
$('#agent-project-link').onclick=e=>{e.preventDefault();if(state.pid)setModule('video');else setModule('projects')};
$('#subtitle-download').onclick=e=>{if(!state.pid){e.preventDefault();toast('Selecciona un proyecto editable')}};
window.addEventListener('hashchange',()=>setModule(location.hash.slice(1)));
initialize().then(()=>{const initial=location.hash.slice(1);if(names[initial])setModule(initial);else if(state.pid){$('#project-select').value=state.pid;openEditor(state.pid)}}).catch(e=>{console.error(e);$('#connection-label').textContent='Error de conexión'});


function monitorPercent(value){return Number.isFinite(value)?`${Math.round(value)}`:'—'}
function monitorGB(value){return Number.isFinite(value)?`${(value/1073741824).toFixed(1)} GB`:'desconocido'}
function monitorGBCompact(value){return Number.isFinite(value)?String(Math.round(value/1073741824)):'—'}
function updateMonitorText(id,value){const node=$(`#${id}`);if(node)node.textContent=value}
async function refreshSystemMonitor(){
  const root=$('#system-monitor');if(!root)return;
  const data=await tryApi('/api/studio/system-metrics');
  if(data.__error){root.dataset.state='unavailable';root.title='El backend activo no expone las métricas locales; se muestran guiones. Sin telemetría externa.';$('#system-monitor-status').textContent='Métricas locales no disponibles en este backend';return}
  root.dataset.state='ready';root.title='Lecturas locales del sistema operativo; ninguna telemetría sale del equipo.';
  const cpu=data.cpu||{};updateMonitorText('system-cpu-use',monitorPercent(cpu.usage_percent));updateMonitorText('system-cpu-temp',Number.isFinite(cpu.temperature_c)?String(Math.round(cpu.temperature_c)):'—');
  const gpu=Array.isArray(data.gpus)?data.gpus[0]:null;updateMonitorText('system-gpu-use',monitorPercent(gpu?.usage_percent));updateMonitorText('system-gpu-temp',Number.isFinite(gpu?.temperature_c)?String(Math.round(gpu.temperature_c)):'—');
  const memory=data.memory||{};updateMonitorText('system-memory-use',monitorPercent(memory.usage_percent));
  const memoryNode=$('#system-memory');memoryNode.title=`RAM: ${monitorGB(memory.used_bytes)} usados de ${monitorGB(memory.total_bytes)}`;
  const disks=Array.isArray(data.disks)?data.disks:[];const diskRoot=$('#system-disks-value');diskRoot.replaceChildren();const diskColors=['#f85149','#58a6ff','#bc8cff','#3fb950','#d29922'];for(const [index,d] of disks.entries()){const name=String(d.name||'Disco').replace(/[\\/]+$/,'')||'Disco';const total=d.total_bytes,free=d.free_bytes;const used=Number.isFinite(total)&&Number.isFinite(free)?Math.max(0,total-free):null;const unit=document.createElement('span');unit.className='disk-unit';unit.style.setProperty('--disk-color',diskColors[index%diskColors.length]);const dot=document.createElement('i');dot.className='disk-dot';dot.setAttribute('aria-hidden','true');const label=document.createElement('strong');label.className='disk-label';label.textContent=`${name.replace(/:$/,'')}:`;const value=document.createElement('span');value.className='disk-value';const percent=Number.isFinite(d.usage_percent)?`${monitorPercent(d.usage_percent)}% · `:'';value.textContent=Number.isFinite(used)&&Number.isFinite(total)?`${percent}${monitorGBCompact(used)}/${monitorGBCompact(total)} GB`:'—';unit.title=`${name}: ${monitorPercent(d.usage_percent)}% ocupado; ${monitorGB(free)} libres de ${monitorGB(total)}`;unit.append(dot,label,value);diskRoot.append(unit)}if(!disks.length)diskRoot.textContent='—';
  $('#system-disks').title=disks.length?disks.map(d=>`${d.name}: ${monitorPercent(d.usage_percent)}% ocupado; ${monitorGB(d.free_bytes)} libres de ${monitorGB(d.total_bytes)}`).join(' | '):'No se detectaron volúmenes fijos disponibles';
  $('#system-gpu').title=gpu?`${gpu.name}: uso y temperatura del primer adaptador NVIDIA reportado por nvidia-smi`:'No hay lectura NVIDIA disponible; se muestran guiones';
  $('#system-monitor-status').textContent=`Actualizado ${data.collected_at||'sin fecha'}`;
}
refreshSystemMonitor();setInterval(refreshSystemMonitor,5000);

// Wan 2.2 T2V is enabled only when the active Studio identity and the local
// read-only preflight agree. Receipts, not browser paths, identify outputs.
state.textToVideo={available:false,results:[],pendingId:null,busy:false,phase:'idle',epoch:0};
state.selectedGeneratedRequestId=null;
const textVideoPendingKey=pid=>`openmontage.text-video.pending.${encodeURIComponent(pid)}`;
const textVideoRoot=pid=>`/api/studio/editor/${encodeURIComponent(pid)}/text-to-video`;
function textVideoStatus(message,error=false){const node=$('#text-to-video-status');if(node)node.textContent=message;if(node)node.dataset.state=error?'error':'ready'}
function textVideoControls(){
  const t=state.textToVideo,usable=!!(t?.available&&state.pid&&state.edit);
  const mode=$('#mode-text-to-video'),prompt=$('#text-to-video-prompt'),submit=$('#text-to-video-submit'),check=$('#text-to-video-check');
  if(mode){mode.disabled=!usable;mode.classList.toggle('unavailable',!usable);$('#text-to-video-mode-status').textContent=usable?'Wan 2.2 local · disponible':'No disponible';}
  if(prompt)prompt.disabled=!usable||t.busy||!!t.pendingId;
  if(submit)submit.disabled=!usable||t.busy||!!t.pendingId;
  if(check)check.disabled=!usable||t.busy;
}
function clearTextVideoPreview(){
  const video=$('#preview-video');if(video){video.pause();video.removeAttribute('src');delete video.dataset.textVideoPreview;video.load()}
  const empty=$('#viewer-empty');if(empty)empty.hidden=false;
}
function showTextVideoPreview(key,url,label){
  const video=$('#preview-video');if(!video||typeof url!=='string'||!url.startsWith('/api/studio/editor/'))return;
  if(video.dataset.textVideoPreview!==key){video.src=url;video.dataset.textVideoPreview=key;video.load()}
  $('#viewer-empty').hidden=true;$('#preview-status').textContent=`Vista previa · ${label||'medio del proyecto'}`;
}
function generatedVideoUrl(pid,requestId){return `${textVideoRoot(pid)}/requests/${encodeURIComponent(requestId)}/video`}
function renderTextVideoResults(){
  const results=state.pid?(state.textToVideo?.results||[]):[],root=$('#text-to-video-results'),media=$('#media-list');
  if(!root||!media)return;
  media.querySelectorAll('.text-video-media').forEach(node=>node.remove());
  root.replaceChildren();
  for(const result of results){
    if(!/^[a-f0-9]{32}$/.test(result.request_id||''))continue;
    const id=result.request_id,label=result.label||'Vídeo generado · Wan 2.2';
    const item=document.createElement('div');item.className='media-result-item text-video-media';
    const row=document.createElement('button');row.type='button';row.className='media-row media-generated'+(state.selectedGeneratedRequestId===id?' selected':'');
    const kind=document.createElement('span');kind.className='media-kind';kind.textContent='Wan';
    const detail=document.createElement('span');detail.className='media-label';
    const title=document.createElement('strong');title.textContent=label;
    const meta=document.createElement('small');meta.textContent=`MP4 · ${Number.isFinite(result.bytes)?`${Math.round(result.bytes/1048576)} MB`:'tamaño no informado'} · proyecto actual`;
    detail.append(title,meta);row.append(kind,detail);row.onclick=()=>selectGeneratedTextVideo(id,label);row.ondblclick=()=>addGeneratedTextVideo(id);
    const mediaActions=document.createElement('div');mediaActions.className='media-result-actions';const mediaPreview=document.createElement('button');mediaPreview.type='button';mediaPreview.className='quiet-button';mediaPreview.textContent='Vista previa';mediaPreview.onclick=()=>selectGeneratedTextVideo(id,label);const mediaAdd=document.createElement('button');mediaAdd.type='button';mediaAdd.className='quiet-button';mediaAdd.textContent='Añadir';mediaAdd.disabled=!state.edit||state.textToVideo.busy||state.busy;mediaAdd.onclick=()=>addGeneratedTextVideo(id);mediaActions.append(mediaPreview,mediaAdd);item.append(row,mediaActions);media.append(item);
    const card=document.createElement('article');card.className='text-video-result';
    const details=document.createElement('div');const heading=document.createElement('strong');heading.textContent=label;
    const info=document.createElement('small');info.textContent=`Completado ${result.completed_at||'sin fecha disponible'}${result.model?` · ${result.model}`:''}`;details.append(heading,info);
    const actions=document.createElement('div');actions.className='text-to-video-buttons';
    const preview=document.createElement('button');preview.type='button';preview.className='quiet-button';preview.textContent='Vista previa';preview.onclick=()=>selectGeneratedTextVideo(id,label);
    const add=document.createElement('button');add.type='button';add.className='primary-button';add.textContent='Añadir a la línea de tiempo';add.disabled=!state.edit||state.textToVideo.busy||state.busy;add.onclick=()=>addGeneratedTextVideo(id);
    actions.append(preview,add);card.append(details,actions);root.append(card);
  }
  const count=media.querySelectorAll('.media-row').length;$('#media-count').textContent=`${count} elemento${count===1?'':'s'}`;
  textVideoControls();
}
function selectGeneratedTextVideo(requestId,label='Vídeo generado · Wan 2.2'){
  if(!state.pid||!state.edit)return;
  state.selectedSource=null;state.selectedClip=null;state.selectedGeneratedRequestId=requestId;
  showTextVideoPreview(`receipt:${state.pid}:${requestId}`,generatedVideoUrl(state.pid,requestId),label);
  renderEditor();
}
async function refreshTextVideoResults(pid=state.pid,epoch=state.textToVideo.epoch){
  const results=await tryApi(`${textVideoRoot(pid)}/results`);
  if(epoch!==state.textToVideo.epoch||pid!==state.pid)return false;
  if(results.__error||!Array.isArray(results)){
    state.textToVideo.available=false;state.textToVideo.results=[];
    textVideoStatus(`El backend no expone la recuperación de recibos (${results.__error||'respuesta no válida'}). No se habilita generación.` ,true);
    textVideoControls();renderTextVideoResults();return false;
  }
  state.textToVideo.results=results;renderTextVideoResults();return true;
}
function loadPendingTextVideo(pid){try{return localStorage.getItem(textVideoPendingKey(pid))||null}catch{return null}}
function savePendingTextVideo(pid,id){try{localStorage.setItem(textVideoPendingKey(pid),id);return true}catch{return false}}
function clearPendingTextVideo(pid){try{localStorage.removeItem(textVideoPendingKey(pid))}catch{}}
function textVideoReceiptDefinitelyMissing(message){return typeof message==='string'&&message.includes('Trabajo de texto a vídeo no encontrado')}
function newTextVideoRequestId(){const bytes=crypto.getRandomValues(new Uint8Array(16));return [...bytes].map(x=>x.toString(16).padStart(2,'0')).join('')}
function sleepTextVideo(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
async function textVideoRequestStatus(pid,id){return await tryApi(`${textVideoRoot(pid)}/requests/${encodeURIComponent(id)}`)}
async function finishTextVideoStatus(pid,id,result,epoch){
  if(epoch!==state.textToVideo.epoch||pid!==state.pid)return;
  const stateName=result.state||'unknown';state.textToVideo.phase=stateName;
  if(stateName==='completed'){
    state.textToVideo.pendingId=null;clearPendingTextVideo(pid);
    textVideoStatus('Vídeo listo en medios generados del proyecto. Revisa la lista y selecciona Vista previa.');
    await refreshTextVideoResults(pid,epoch);return;
  }
  if(['failed','error','invalid','cancelled'].includes(stateName)){
    state.textToVideo.pendingId=null;clearPendingTextVideo(pid);
    textVideoStatus(result.error||`El trabajo terminó: ${stateName}. Puedes revisar el estado antes de iniciar otro.`,true);
  }else if(stateName==='interrupted'){
    textVideoStatus(result.error||'Estado incierto. Consulta ComfyUI antes de decidir si reintentas; no se reenviará automáticamente.',true);
  }else{textVideoStatus(`Wan 2.2: ${stateName}${result.progress?` · ${result.progress}`:''}`)}
  textVideoControls();
}
async function pollTextVideo(pid,id,epoch){
  state.textToVideo.busy=true;state.textToVideo.phase='running';textVideoControls();
  for(let attempt=0;attempt<300;attempt++){
    if(epoch!==state.textToVideo.epoch||pid!==state.pid)return;
    const result=await textVideoRequestStatus(pid,id);
    if(result.__error){state.textToVideo.busy=false;if(textVideoReceiptDefinitelyMissing(result.__error)){state.textToVideo.pendingId=null;clearPendingTextVideo(pid);state.textToVideo.phase='ready';textVideoStatus('El servidor confirmó que no existe recibo ni reserva para este ID. Ya puedes enviar una solicitud nueva.')}else{state.textToVideo.phase='uncertain';textVideoStatus(`No se pudo confirmar el recibo (${result.__error}). Se conserva la solicitud para evitar duplicarla. Consulta el estado antes de reintentar.`,true)}textVideoControls();return}
    if(!['queued','running'].includes(result.state)){
      state.textToVideo.busy=false;await finishTextVideoStatus(pid,id,result,epoch);textVideoControls();renderTextVideoResults();return;
    }
    textVideoStatus(`Wan 2.2: ${result.state}. El trabajo sigue en ComfyUI; no vuelvas a enviarlo.`);await sleepTextVideo(1500);
  }
  state.textToVideo.busy=false;state.textToVideo.phase='uncertain';textVideoStatus('La espera superó el límite de consulta. El recibo se conserva; consulta su estado antes de repetir.',true);textVideoControls();
}
async function loadTextVideoProject(pid){
  const epoch=++state.textToVideo.epoch;state.textToVideo.available=false;state.textToVideo.results=[];state.textToVideo.busy=false;state.selectedGeneratedRequestId=null;
  state.textToVideo.pendingId=loadPendingTextVideo(pid);textVideoControls();renderTextVideoResults();
  if(!pid||!state.edit){textVideoStatus('Selecciona un proyecto para comprobar el flujo local.');return}
  if(state.identity?.restart_required!==false){textVideoStatus('El backend activo necesita activación o no confirma su identidad. No se consulta ni habilita el generador.',true);return}
  textVideoStatus('Comprobando el preflight local de Wan 2.2…');
  const check=await tryApi(`${textVideoRoot(pid)}/availability`);
  if(epoch!==state.textToVideo.epoch||pid!==state.pid)return;
  if(check.__error||check.available!==true){textVideoStatus(check.reason||check.__error||'El preflight Wan 2.2 no confirmó disponibilidad.',true);return}
  if(!await refreshTextVideoResults(pid,epoch))return;
  state.textToVideo.available=true;state.textToVideo.phase='ready';
  textVideoStatus(`Disponible · perfil ${check.profile||'Wan 2.2 T2V'} · workflow ${check.workflow||'confirmado'} · ${check.required_models??6} modelos requeridos.`);
  textVideoControls();
  const pending=state.textToVideo.pendingId;
  if(pending){
    if(!/^[a-f0-9]{32}$/.test(pending)){state.textToVideo.phase='uncertain';textVideoStatus('El recibo guardado en este navegador no tiene formato válido. No se enviará otro trabajo automáticamente.',true);textVideoControls();return}
    const result=await textVideoRequestStatus(pid,pending);
    if(epoch!==state.textToVideo.epoch||pid!==state.pid)return;
    if(result.__error){if(textVideoReceiptDefinitelyMissing(result.__error)){state.textToVideo.pendingId=null;clearPendingTextVideo(pid);state.textToVideo.phase='ready';textVideoStatus('El servidor confirmó que no existe recibo ni reserva para este ID. Ya puedes enviar una solicitud nueva.')}else{state.textToVideo.phase='uncertain';textVideoStatus(`No se confirmó el recibo guardado (${result.__error}); no se repetirá la solicitud.`,true)}textVideoControls();return}
    if(['queued','running'].includes(result.state)){pollTextVideo(pid,pending,epoch);return}
    await finishTextVideoStatus(pid,pending,result,epoch);textVideoControls();
  }
}
async function addGeneratedTextVideo(requestId){
  if(!state.pid||!state.edit||state.textToVideo.busy||state.busy)return;
  if(!/^[a-f0-9]{32}$/.test(requestId)){toast('El identificador del recibo no es válido');return}
  state.textToVideo.busy=true;textVideoControls();
  try{
    const result=await req(`${textVideoRoot(state.pid)}/requests/${encodeURIComponent(requestId)}/add`,{method:'POST',body:{revision:state.edit.revision}});
    if(!result?.edit||!result.source_id)throw Error('El backend no devolvió el medio registrado en el proyecto');
    state.edit=result.edit;state.selectedSource=result.source_id;state.selectedGeneratedRequestId=null;renderEditor();
    toast('Vídeo validado y añadido al montaje del proyecto');
    await refreshTextVideoResults(state.pid,state.textToVideo.epoch);
  }catch(error){textVideoStatus(`No se añadió el recibo: ${error.message}`,true);await openEditor(state.pid)}
  finally{state.textToVideo.busy=false;textVideoControls();renderTextVideoResults()}
}
async function submitTextVideo(event){
  event.preventDefault();const pid=state.pid,prompt=$('#text-to-video-prompt').value.trim();
  if(!state.textToVideo.available||!pid||!state.edit){textVideoStatus('El proyecto o el preflight local no están disponibles.',true);return}
  if(state.textToVideo.pendingId){textVideoStatus('Hay un recibo pendiente. Consulta su estado antes de iniciar otro trabajo.',true);return}
  if(!prompt||prompt.length>2000||prompt.includes('\0')){textVideoStatus('Escribe un prompt de 1 a 2000 caracteres.',true);return}
  const id=newTextVideoRequestId();if(!savePendingTextVideo(pid,id)){textVideoStatus('No se pudo guardar localmente el identificador de solicitud; no se envió el prompt.',true);return}
  state.textToVideo.pendingId=id;state.textToVideo.busy=true;state.textToVideo.phase='submitting';textVideoControls();textVideoStatus('Enviando una solicitud al ComfyUI local…');
  const result=await tryApi(textVideoRoot(pid),{method:'POST',body:{prompt,request_id:id}});
  state.textToVideo.busy=false;
  if(result.__error){state.textToVideo.phase='uncertain';textVideoStatus(`No se confirmó la respuesta del servidor (${result.__error}). Se conserva el ID; consulta el recibo y no lo reenvíes.`,true);textVideoControls();return}
  textVideoStatus(`Trabajo aceptado · ${result.state||'estado pendiente'}. Consultando el mismo recibo…`);textVideoControls();await pollTextVideo(pid,id,state.textToVideo.epoch);
}
$('#text-to-video-form')?.addEventListener('submit',submitTextVideo);
$('#text-to-video-check')?.addEventListener('click',async()=>{const pid=state.pid;if(!pid)return;await loadTextVideoProject(pid)});
$('#mode-text-to-video')?.addEventListener('click',()=>{if(!state.textToVideo.available)return;const panel=$('#text-to-video-panel');const opening=panel.hidden;panel.hidden=!opening;$('#mode-text-to-video').setAttribute('aria-pressed',String(opening));if(opening)$('#text-to-video-prompt').focus()});
const renderEditorBeforeTextVideo=renderEditor;
renderEditor=function(){renderEditorBeforeTextVideo();if(!state.textToVideo)return;renderTextVideoResults();if(state.selectedSource&&state.edit){const source=state.edit.edit_decisions?.sources?.[state.selectedSource];if(source?.origin==='wan_t2v_receipt')showTextVideoPreview(`source:${state.pid}:${state.selectedSource}`,`/api/studio/editor/${encodeURIComponent(state.pid)}/source/${encodeURIComponent(state.selectedSource)}`,source.original_name||'Vídeo generado');}const add=$('#timeline-add');if(add)add.disabled=!state.edit||(!state.selectedSource&&!state.selectedGeneratedRequestId)};
const openEditorBeforeTextVideo=openEditor;
openEditor=async function(pid){const changed=state.pid!==pid;if(changed){state.selectedSource=null;state.selectedClip=null;state.selectedGeneratedRequestId=null;clearTextVideoPreview()}await openEditorBeforeTextVideo(pid);if(state.pid===pid&&state.edit)await loadTextVideoProject(pid);else{state.textToVideo.available=false;state.textToVideo.results=[];textVideoControls();renderTextVideoResults()}};
$('#timeline-add')?.addEventListener('click',event=>{if(state.selectedGeneratedRequestId){event.preventDefault();event.stopImmediatePropagation();addGeneratedTextVideo(state.selectedGeneratedRequestId)}},true);
$('#project-select')?.addEventListener('change',()=>{if(!state.pid){state.textToVideo.epoch++;state.textToVideo.available=false;state.textToVideo.results=[];state.textToVideo.pendingId=null;state.selectedGeneratedRequestId=null;clearTextVideoPreview();textVideoStatus('Selecciona un proyecto para comprobar el flujo local.');textVideoControls();renderTextVideoResults()}});


const editorPanelLayoutKey='openmontage.studio.editor-layout.v1';
let editorPanelLayout={media:.18,inspector:.18,timeline:.32};
try{const saved=JSON.parse(localStorage.getItem(editorPanelLayoutKey)||'null');if(saved&&typeof saved==='object'){for(const key of ['media','inspector','timeline'])if(Number.isFinite(saved[key]))editorPanelLayout[key]=saved[key]}}catch{}
function clampLayout(v,min,max){return Math.min(max,Math.max(min,v))}
function applyEditorPanelLayout(){
  const root=$('.edit-workbench');if(!root)return;
  const width=root.clientWidth,height=root.clientHeight;
  const mediaHandle=$('#resize-media'),inspectorHandle=$('#resize-inspector'),timelineHandle=$('#resize-timeline');
  const mobile=matchMedia('(max-width:760px)').matches;
  if(mobile){[mediaHandle,inspectorHandle,timelineHandle].forEach(x=>{if(x)x.hidden=true});root.style.removeProperty('grid-template-columns');root.style.removeProperty('grid-template-rows');return}
  if(width<480||height<260)return;
  const gap=parseFloat(getComputedStyle(root).columnGap)||12;
  const rowGap=parseFloat(getComputedStyle(root).rowGap)||12;
  const compact=width<=1150;
  const mediaMin=compact?170:185,inspectorMin=190,monitorMin=compact?300:360;
  const mediaMax=Math.max(mediaMin,width-monitorMin-gap-(compact?0:inspectorMin+gap));
  const media=clampLayout(width*clampLayout(editorPanelLayout.media,.12,.36),mediaMin,mediaMax);
  let inspector=inspectorMin;
  if(!compact)inspector=clampLayout(width*clampLayout(editorPanelLayout.inspector,.12,.32),inspectorMin,width-media-monitorMin-2*gap);
  root.style.gridTemplateColumns=compact?media+'px minmax('+monitorMin+'px,1fr)':media+'px minmax('+monitorMin+'px,1fr) '+inspector+'px';
  const minTimeline=width>=1900?190:160,minTop=width>=1900?310:270;
  const timeline=clampLayout(height*clampLayout(editorPanelLayout.timeline,.2,.55),minTimeline,Math.max(minTimeline,height-minTop-rowGap));
  root.style.gridTemplateRows='minmax('+minTop+'px,1fr) '+timeline+'px'+(compact?' minmax(130px,auto)':'');
  const rootRect=root.getBoundingClientRect(),mediaRect=$('.media-panel').getBoundingClientRect(),monitorRect=$('.monitor-panel').getBoundingClientRect(),inspectorRect=$('.inspector-panel').getBoundingClientRect(),timelineRect=$('.timeline-panel').getBoundingClientRect();
  if(mediaHandle){mediaHandle.hidden=false;mediaHandle.style.left=(mediaRect.right-rootRect.left+gap/2-6)+'px';mediaHandle.style.height=Math.max(0,monitorRect.bottom-rootRect.top)+'px';mediaHandle.setAttribute('aria-valuenow',String(Math.round(media)))}
  if(inspectorHandle){inspectorHandle.hidden=compact;inspectorHandle.style.left=(inspectorRect.left-rootRect.left-gap/2-6)+'px';inspectorHandle.style.height=Math.max(0,monitorRect.bottom-rootRect.top)+'px';inspectorHandle.setAttribute('aria-valuenow',String(Math.round(inspector)))}
  if(timelineHandle){timelineHandle.hidden=false;timelineHandle.style.top=((compact?timelineRect.bottom-rootRect.top+rowGap/2:timelineRect.top-rootRect.top-rowGap/2)-6)+'px';timelineHandle.setAttribute('aria-valuenow',String(Math.round(timeline)))}
}
function persistEditorPanelLayout(){try{localStorage.setItem(editorPanelLayoutKey,JSON.stringify(editorPanelLayout))}catch{}}
function editPanelLayoutFromPointer(kind,event,rect,start){
  if(kind==='media')editorPanelLayout.media=clampLayout((start.mediaWidth+event.clientX-start.x)/rect.width,.12,.36);
  else if(kind==='inspector')editorPanelLayout.inspector=clampLayout((start.inspectorWidth+start.x-event.clientX)/rect.width,.12,.32);
  else{const delta=start.compact?event.clientY-start.y:start.y-event.clientY;editorPanelLayout.timeline=clampLayout((start.timelineHeight+delta)/rect.height,.2,.55)}
  applyEditorPanelLayout();
}
for(const [id,kind] of [['resize-media','media'],['resize-inspector','inspector'],['resize-timeline','timeline']]){
  const handle=$('#'+id);if(!handle)continue;
  handle.addEventListener('pointerdown',event=>{if(handle.hidden)return;event.preventDefault();const root=$('.edit-workbench'),rect=root.getBoundingClientRect(),start={x:event.clientX,y:event.clientY,mediaWidth:$('.media-panel').getBoundingClientRect().width,inspectorWidth:$('.inspector-panel').getBoundingClientRect().width,timelineHeight:$('.timeline-panel').getBoundingClientRect().height,compact:matchMedia('(max-width:1150px)').matches};try{handle.setPointerCapture(event.pointerId)}catch{};const move=e=>editPanelLayoutFromPointer(kind,e,rect,start),finish=()=>{handle.removeEventListener('pointermove',move);persistEditorPanelLayout();applyEditorPanelLayout()};handle.addEventListener('pointermove',move);handle.addEventListener('pointerup',finish,{once:true});handle.addEventListener('pointercancel',finish,{once:true})});
  handle.addEventListener('keydown',event=>{const step=event.shiftKey?40:12;let delta=0;if(kind==='media'&&['ArrowLeft','ArrowRight'].includes(event.key))delta=event.key==='ArrowRight'?step:-step;else if(kind==='inspector'&&['ArrowLeft','ArrowRight'].includes(event.key))delta=event.key==='ArrowLeft'?step:-step;else if(kind==='timeline'&&['ArrowUp','ArrowDown'].includes(event.key)){const compact=matchMedia('(max-width:1150px)').matches;delta=(event.key==='ArrowUp'?-1:1)*(compact?1:-1)*step;}else return;event.preventDefault();const root=$('.edit-workbench'),rect=root.getBoundingClientRect();if(kind==='media')editorPanelLayout.media=clampLayout((rect.width*editorPanelLayout.media+delta)/rect.width,.12,.36);else if(kind==='inspector')editorPanelLayout.inspector=clampLayout((rect.width*editorPanelLayout.inspector+delta)/rect.width,.12,.32);else editorPanelLayout.timeline=clampLayout((rect.height*editorPanelLayout.timeline+delta)/rect.height,.2,.55);applyEditorPanelLayout();persistEditorPanelLayout()});
}
window.addEventListener('resize',()=>requestAnimationFrame(applyEditorPanelLayout));
$$('.nav-item').forEach(button=>button.addEventListener('click',()=>requestAnimationFrame(applyEditorPanelLayout)));
applyEditorPanelLayout();
