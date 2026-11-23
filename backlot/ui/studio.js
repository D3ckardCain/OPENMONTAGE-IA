const $=s=>document.querySelector(s);let pid=new URLSearchParams(location.search).get('project'),busy=false,referenceTimer=null;
const notice=s=>{$('#notice').textContent=s||'';};
async function api(path,data){const r=await fetch('/api/studio/'+path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});let v=await r.json();if(!r.ok)throw Error(typeof v.detail==='string'?v.detail:JSON.stringify(v.detail));return v;}
function node(tag,text){let n=document.createElement(tag);n.textContent=text;return n;}
function link(label,url){let a=node('a',label);a.href=url;return a;}
const sectionLabels={scenes:'Mesa de escenas',production:'Producción',queue:'Cola de trabajos',finals:'Videos finales',football:'Fútbol · fuentes oficiales',references:'Referencias e imágenes',models:'Modelos y discos',applications:'Aplicaciones',setup:'Preparación del equipo',history:'Historial y pruebas'};
function showSection(name){
 if(!(name in sectionLabels))name='production';
 for(const pane of document.querySelectorAll('[data-pane]'))pane.hidden=pane.dataset.pane!==name;
 for(const button of document.querySelectorAll('[data-section]')){if(button.dataset.section===name)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');}
 $('#workspace-section').textContent=sectionLabels[name];
}
for(const button of document.querySelectorAll('[data-section]'))button.onclick=()=>{history.replaceState(null,'',location.pathname+location.search+'#'+button.dataset.section);showSection(button.dataset.section);};
window.addEventListener('hashchange',()=>showSection(location.hash.slice(1)==='resources'?'models':location.hash.slice(1)));
showSection(location.hash.slice(1)==='resources'?'models':location.hash.slice(1));
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
async function bootstrap(){const b=await api('bootstrap');const f=$('#settings');f.ollama_url.value=b.settings.ollama_url;f.ffmpeg_path.value=b.settings.ffmpeg_path||'';f.ffprobe_path.value=b.settings.ffprobe_path||'';f.yt_dlp_path.value=b.settings.yt_dlp_path||'';f.deno_path.value=b.settings.deno_path||'';f.comfyui_url.value=b.settings.comfyui_url;f.roots.value=b.settings.resource_roots.join('\n');f.model.replaceChildren(new Option(b.settings.model||'Sin modelo seleccionado',b.settings.model));$('#create').pipeline.replaceChildren(...b.pipelines.map(p=>new Option(p.name+' · '+p.stages.length+' etapas',p.name)));$('#projects').replaceChildren(...b.projects.map(p=>{let n=node('button',p.title);n.onclick=()=>select(p.project_id);return n;}));}
async function select(id){showSection('production');clearInterval(referenceTimer);referenceTimer=null;for(const name of ['reference-result','comfy-jobs-result','source-image-result','comfy-history-result','delivery-retry-result','versions-result','versions-requirements-result','translation-result','source-language-result'])$('#'+name).replaceChildren();pid=id;$('#channel-evidence-detail').replaceChildren();$('#source-language').value='';history.replaceState(null,'','/studio?project='+encodeURIComponent(pid));$('#creation').hidden=true;$('#production').hidden=false;await refresh();}
async function refresh(){if(!pid||busy)return;busy=true;try{const selected=pid;const s=await api('projects/'+selected);if(pid!==selected)return;const field=$('#reference-url');if(field.dataset.project!==selected){field.value=s.reference_video_url||'';field.dataset.project=selected;}const verification=$('#render-verification');verification.replaceChildren();if(s.render_verification){const v=s.render_verification;verification.append(node('h3','Verificación técnica: '+v.status+(s.verification_current?' · vigente':' · revisar datos o revisión')));if(v.error)verification.append(node('p',v.error));for(const reason of s.verification_reasons||[])verification.append(node('p',reason));for(const output of v.outputs||[])verification.append(node('p',output.width+'×'+output.height+' · '+output.duration_seconds.toFixed(2)+' s · '+output.audio_streams+' pistas de audio · decodificación completa: '+(output.full_decode_passed?'correcta':'sin confirmar')));verification.append(node('p','Esta revisión no acredita calidad visual, originalidad ni exactitud del contenido.'));}$('#final-delivery').replaceChildren();if(s.final_delivery?.copied){$('#final-delivery').append(node('h3','Destino de los videos finales'+(s.final_copy_current?'':' · copia de versión anterior')));for(const item of s.final_delivery.outputs)$('#final-delivery').append(node('p',item.path+' · copia verificada'));}$('#title').textContent=s.request.title;$('#status').textContent=s.job.status;$('#message').textContent=s.job.message;const research=$('#channel-research');research.replaceChildren();research.hidden=!s.channel_research;
 if(s.channel_research){const r=s.channel_research;research.append(node('h3','Investigación de canal · '+(r.status==='verified'?'copia íntegra':'revisar')));
  if(r.status==='verified')research.append(node('p',r.idea_title+' · '+r.publication_total+' publicaciones · '+(r.complete_period?'periodo completo':'periodo parcial')+' · consultado '+r.retrieved_at_utc),node('p','SHA-256: '+r.snapshot_sha256),node('p',r.vidiq_observation_total===null?'Observaciones vidIQ: no copiadas en este proyecto anterior':'Observaciones vidIQ manuales: '+r.vidiq_observation_total+' · separadas de YouTube'));
  research.append(node('p',r.message));if(r.status==='verified'){for(const [kind,label] of [['channel','Ver publicaciones'],['vidiq','Ver observaciones vidIQ']]){const button=node('button',label);button.type='button';button.onclick=()=>loadChannelEvidence(kind,0,selected);research.append(button);}}else $('#channel-evidence-detail').replaceChildren();if(r.status==='missing'){const restore=node('button','Recuperar copia local');restore.type='button';restore.onclick=async()=>{try{await api('projects/'+encodeURIComponent(selected)+'/restore-channel-research',{});setTimeout(refresh,0);notice('Investigación recuperada y verificada.');}catch(error){notice(error.message);}};research.append(restore);}}if(s.channel_performance){const r=s.channel_performance;research.hidden=false;research.append(node('h3','Rendimiento CSV · '+(r.status==='verified'?'copia íntegra':'revisar')),node('p',r.status==='verified'?(r.row_total+' filas · importado '+r.imported_at_utc+' · fuente aportada, sin verificar'):r.message));if(r.status==='verified'){const button=node('button','Ver rendimiento copiado');button.type='button';button.onclick=()=>loadChannelEvidence('performance',0,selected);research.append(button);}}const invalidResearch=(!!s.channel_research&&s.channel_research.status!=='verified')||(!!s.channel_performance&&s.channel_performance.status!=='verified');for(const action of ['start','approve']){const button=$('[data-action="'+action+'"]');button.disabled=invalidResearch;button.title=invalidResearch?'Revisa el expediente alterado antes de continuar':'';}$('#board').href=s.board_url;$('#approve').hidden=s.job.status!=='awaiting_human';$('#request-revision').hidden=s.job.status!=='awaiting_human';if(s.job.status!=='awaiting_human')$('#revision-form').hidden=true;$('#stages').replaceChildren(...s.stages.map(x=>{let n=node('div',x.name+' · '+x.status);n.className='stage '+x.status;return n;}));$('#artifacts').replaceChildren(...s.artifacts.map(x=>link(x.name,x.url)));$('#outputs').replaceChildren(...s.outputs.map(x=>{let d=node('div','');d.append(link(x.name,x.url));if(/\.(mp4|webm)$/i.test(x.name)){let v=document.createElement('video');v.controls=true;v.src=x.url;d.append(v);}return d;}));$('#events').textContent=(s.job.events||[]).map(x=>x.at+' ['+x.kind+'] '+x.message).join('\n');}catch(e){notice(e.message);}finally{busy=false;}}
async function loadChannelEvidence(kind,offset,selected){
 const box=$('#channel-evidence-detail');try{
  const route=kind==='channel'?'channel-research/':kind==='performance'?'channel-performance/':'vidiq-observations/';
  const data=await api(route+encodeURIComponent(selected)+'?offset='+offset+'&limit=20');
  if(pid!==selected)return;box.replaceChildren(node('h3',kind==='channel'?'Publicaciones de la captura':kind==='performance'?'Rendimiento copiado del CSV':'Observaciones manuales de vidIQ'));
  if(data.status==='not_copied'){box.append(node('p',data.message));return;}
  box.append(node('p',kind==='channel'?(data.publication_total+' publicaciones · '+(data.complete_period?'periodo completo':'periodo parcial')+' · '+data.retrieved_at_utc):kind==='performance'?(data.row_total+' filas · '+data.source):data.observation_total+' observaciones · '+data.source));
  const rows=kind==='channel'?data.publications:kind==='performance'?data.rows:data.observations;
  for(const row of rows){const item=document.createElement('div');item.className='resource';
   if(kind==='channel'){const id=row.id;if(typeof id==='string'&&/^[A-Za-z0-9_-]{11}$/.test(id))item.append(link(row.title||id,'https://www.youtube.com/watch?v='+id));else item.append(node('strong',row.title||'Video sin ID'));item.append(node('p','Vistas en la captura: '+(row.viewCount??'sin dato')));}
   else if(kind==='performance'){item.append(node('p',row.video_id+' · '+row.period_start+' a '+row.period_end),node('p','Impresiones: '+(row.impressions??'sin dato')+' · clics: '+(row.clicks??'sin dato')+' · vistas: '+(row.views??'sin dato')+' · clics/impresiones: '+(row.clicks_per_impression_percent??'sin dato')+' % · duración media: '+(row.average_view_duration_seconds??'sin dato')+' s · porcentaje medio visto: '+(row.average_watch_percent??'sin dato')+' %'));}
   else{item.append(node('p',row.video_id+' · '+row.observed_at_utc+' · '+row.source),node('p','Vistas: '+(row.views??'—')+' · VPH: '+(row.vph??'—')+' · Engagement: '+(row.engagement_percent??'—')+' % · Outlier: '+(row.outlier_ratio??'—')+'× · SEO: '+(row.seo_score??'—')+'/100'));if(row.notes)item.append(node('p',row.notes));}box.append(item);}
  if(!rows.length)box.append(node('p','Sin registros en esta página.'));
  if(offset>0){const prev=node('button','Anterior');prev.onclick=()=>loadChannelEvidence(kind,Math.max(0,offset-20),selected);box.append(prev);}
  if(data.next_offset!==null){const next=node('button','Siguiente');next.onclick=()=>loadChannelEvidence(kind,data.next_offset,selected);box.append(next);}
  box.append(node('p',data.limits||'Cifras históricas; revisa hechos y derechos antes de publicar.'));
 }catch(error){if(pid===selected)box.replaceChildren(node('p',error.message));}}
$('#new').onclick=()=>{showSection('production');clearInterval(referenceTimer);referenceTimer=null;for(const name of ['reference-result','comfy-jobs-result','source-image-result','comfy-history-result','delivery-retry-result','versions-result','versions-requirements-result','translation-result','source-language-result'])$('#'+name).replaceChildren();pid=null;$('#channel-evidence-detail').replaceChildren();history.replaceState(null,'','/studio');$('#creation').hidden=false;$('#production').hidden=true;notice('');};
$('#create').onsubmit=async e=>{e.preventDefault();let f=e.target;try{let q=new URLSearchParams(location.search),research_idea=q.has('channel_id')&&q.has('snapshot_id')&&q.has('idea_id')?{channel_id:q.get('channel_id'),snapshot_id:q.get('snapshot_id'),idea_id:q.get('idea_id')}:null;let p=await api('projects',{title:f.elements.namedItem('title').value,brief:f.brief.value,pipeline:f.pipeline.value,language:f.language.value,reference:f.reference.value,automatic:f.automatic.checked,...(research_idea?{research_idea}:{}),...(f.elements.namedItem('performance_import_id').value.trim()?{performance_import_id:f.elements.namedItem('performance_import_id').value.trim()}:{})});await bootstrap();await select(p.project_id);notice('Proyecto creado. Inicia los agentes cuando el modelo local esté configurado.');}catch(e){notice(e.message);}};
$('#settings').onsubmit=async e=>{e.preventDefault();let f=e.target;try{await api('settings',{yt_dlp_path:f.yt_dlp_path.value,deno_path:f.deno_path.value,ffmpeg_path:f.ffmpeg_path.value,ffprobe_path:f.ffprobe_path.value,ollama_url:f.ollama_url.value,comfyui_url:f.comfyui_url.value,model:f.model.value,resource_roots:f.roots.value.split('\n').map(x=>x.trim()).filter(Boolean)});notice('Configuración guardada.');}catch(e){notice(e.message);}};
$('#check').onclick=async()=>{try{$('#runtime').textContent='Comprobando…';const s=await api('runtime');$('#runtime').textContent=JSON.stringify(s,null,2);let selected=$('#settings').model.value;$('#settings').model.replaceChildren(new Option('Selecciona un modelo',''),...s.models.map(m=>new Option(m,m,m===selected,m===selected)));}catch(e){notice(e.message);}};
for(const b of document.querySelectorAll('[data-action]'))b.onclick=async()=>{if(!pid)return;try{await api('projects/'+pid+'/'+b.dataset.action,{});await refresh();}catch(e){notice(e.message);}};
$('#inventory').onchange=async e=>{try{for(const f of e.target.files){if(f.size>32000000)throw Error('Inventario demasiado grande');let r=await api('inventories',JSON.parse(await f.text()));notice('Inventario '+r.serial+': '+r.files+' archivos registrados.');}}catch(e){notice(e.message);}};
function remoteDocumentButton(identifier,revision,filename,panel,offline=false){
  const button=node('button',(offline?'Leer copia guardada de ':'Leer ')+filename+(offline?'':' en el panel'));button.type='button';
  const detail=node('div','');
  button.onclick=async()=>{
    button.disabled=true;detail.replaceChildren(node('p','Leyendo documento oficial…'));
    try{
      const result=await api('updates/document?'+new URLSearchParams({identifier,revision,filename,offline:String(offline)}));
      const content=node('pre',result.text);content.dataset.updateDocumentText='true';
      detail.replaceChildren(node('p',result.note),node('p','Revisión: '+result.remote_revision+' · SHA-256 del documento: '+result.sha256),content);
      detail.append(node('p',(result.retrieval==='offline_cache'?'Copia guardada · Sin consulta de red':'Consulta online')+' · Obtenido: '+result.checked_at));
      if(result.cache_warning)detail.append(node('p',result.cache_warning));
    }catch(error){detail.replaceChildren(node('p',error.message));}finally{button.disabled=false;}
  };
  panel.append(button,detail);
}
async function showCachedUpdateDocuments(identifier,detail,offset=0){
  detail.querySelector('[data-cached-update-documents]')?.remove();
  const panel=node('div','');panel.dataset.cachedUpdateDocuments='true';detail.append(panel);
  try{
    const result=await api('updates/documents?'+new URLSearchParams({identifier,offset:String(offset),limit:'10'}));
    panel.append(node('p',result.note));
    for(const row of result.rows){const item=node('div','');item.append(node('p',row.filename+' · Revisión: '+row.remote_revision+' · Obtenido: '+row.checked_at));remoteDocumentButton(identifier,row.remote_revision,row.filename,item,true);panel.append(item);}
    if(!result.rows.length)panel.append(node('p','No hay documentos guardados para este modelo en esta página.'));
    if(result.invalid_records)panel.append(node('p','Copias inválidas omitidas: '+result.invalid_records));
    if(offset>0){const prev=node('button','Documentos anteriores');prev.onclick=()=>showCachedUpdateDocuments(identifier,detail,Math.max(0,offset-10));panel.append(prev);}
    if(result.next_offset!==null){const next=node('button','Más documentos guardados');next.onclick=()=>showCachedUpdateDocuments(identifier,detail,result.next_offset);panel.append(next);}
  }catch(error){panel.replaceChildren(node('p',error.message));}
}
function watchCandidateDownload(job,box){
  const labels={queued:'En cola',checking:'Comprobando plan y destino',downloading:'Descargando candidato',verifying:'Verificando SHA-256',candidate_ready:'Candidato descargado y verificado; modelo actual sin cambios',failed:'Descarga fallida',cancelled:'Descarga cancelada; parcial conservado',partial_discarded:'Parcial descartado',interrupted:'Descarga interrumpida al reiniciar; reanudación pendiente',historical_candidate_ready:'Descarga terminada en el historial; archivo pendiente de nueva comprobación'};
  box.replaceChildren(node('p',labels[job.status]||job.status),node('p',(job.bytes_present||0)+' / '+(job.expected_bytes??'—')+' bytes'),node('p',job.message||job.note));
  if(job.historical&&job.message)box.append(node('p',job.note));
  if(job.history_warning)box.append(node('p',job.history_warning));
  const pending=['queued','checking','downloading','verifying'].includes(job.status);
  if(pending){const cancel=node('button','Cancelar descarga');cancel.onclick=async()=>{try{await api('updates/downloads/'+job.job_id+'/cancel',{});}catch(error){notice(error.message);}};box.append(cancel);
    setTimeout(async()=>{if(!box.isConnected)return;try{watchCandidateDownload(await api('updates/downloads/'+job.job_id),box);}catch(error){box.replaceChildren(node('p',error.message));}},1000);
  }else if(['failed','cancelled','interrupted','historical_candidate_ready'].includes(job.status)){
    const resume=node('button','Reanudar trabajo guardado');resume.onclick=async()=>{resume.disabled=true;try{watchCandidateDownload(await api('updates/downloads/'+job.job_id+'/resume',{}),box);}catch(error){box.append(node('p',error.message));resume.disabled=false;}};box.append(resume);
    if(job.status==='historical_candidate_ready')return;
    const discard=node('button','Descartar solo el parcial');discard.onclick=async()=>{discard.disabled=true;try{watchCandidateDownload(await api('updates/downloads/'+job.job_id+'/discard-partial',{}),box);}catch(error){box.append(node('p',error.message));discard.disabled=false;}};box.append(discard);
  }
}
function remoteFileCheckButton(identifier,file,line){
  const button=node('button','Comparar archivo con revisión remota actual');button.type='button';
  button.onclick=async()=>{
    button.disabled=true;
    line.querySelector('[data-remote-file-check]')?.remove();
    try{
      const result=await api('updates/remote-file-check?identifier='+encodeURIComponent(identifier)+'&index='+file.index);
      const labels={remote_matches_catalog:'El archivo remoto coincide con el catálogo',remote_differs_from_catalog:'El archivo remoto difiere del catálogo',missing_at_remote_revision:'El archivo no figura en esa revisión remota',remote_comparison_inconclusive:'Metadatos insuficientes para confirmar coincidencia'};
      const panel=node('div','');panel.dataset.remoteFileCheck='true';
      panel.append(node('p',labels[result.status]||result.status),node('p','Revisión consultada: '+result.remote_revision));
      if(result.remote_bytes!==null&&result.remote_bytes!==undefined)panel.append(node('p','Tamaño remoto: '+result.remote_bytes+' bytes'));
      if(result.remote_sha256)panel.append(node('p','SHA-256 remoto: '+result.remote_sha256));
      if(result.license_review){
        const review=result.license_review;
        panel.append(node('p','Licencia declarada: '+(review.declared.join(', ')||'sin metadatos suficientes')+' · Uso comercial y condiciones de coste pendientes de revisión.'));
        for(const url of [review.model_card_url,...review.license_file_urls]){const link=node('a','Consultar evidencia en la revisión');link.href=url;link.target='_blank';link.rel='noopener noreferrer';panel.append(link,node('br',''));}
        for(const url of [review.model_card_url,...review.license_file_urls])remoteDocumentButton(identifier,result.remote_revision,url.split('/').pop(),panel);
      }
      if(result.compatibility_review)panel.append(node('p','Compatibilidad: '+result.compatibility_review.reason));
      if(result.access_review)panel.append(node('p','Acceso sujeto a autorización: '+String(result.access_review.gated)+' · Privado: '+String(result.access_review.private)));
      const planButton=node('button','Preparar plan de candidato separado');planButton.type='button';
      const planDetail=node('div','');
      planButton.onclick=async()=>{planButton.disabled=true;try{
        const plan=await api('updates/plan?'+new URLSearchParams({identifier,index:String(file.index),revision:result.remote_revision}));
        const statuses={candidate_plan_prepared:'Plan preparado; comprobaciones pendientes',catalog_content_unchanged:'Sin cambio de contenido respecto al catálogo',blocked_missing_remote_file:'Plan bloqueado: archivo remoto ausente',blocked_insufficient_remote_metadata:'Plan bloqueado: faltan hash o tamaño remotos'};
        planDetail.replaceChildren(node('p',statuses[plan.status]||plan.status),node('p',plan.note));
        if(plan.candidate){planDetail.append(node('p','Ruta actual conservada: '+plan.original_destination),node('p','Candidato propuesto: '+plan.candidate.destination),node('p','Espacio adicional mínimo: '+plan.additional_storage_bytes_at_least+' bytes · espacio libre sin comprobar'),node('pre',plan.pending_checks.join('\n')));
          const verify=node('button','Comprobar SHA-256 del candidato');verify.type='button';const verification=node('div','');
          verify.onclick=async()=>{verify.disabled=true;verification.replaceChildren(node('p','Leyendo candidato…'));try{
            const checked=await api('updates/candidate-check?'+new URLSearchParams({identifier,index:String(file.index),revision:result.remote_revision}));
            const labels={candidate_matches_remote:'El candidato coincide con la revisión remota',candidate_differs_remote:'El candidato difiere de la revisión remota',not_checked_no_candidate:'No hay candidato verificable',missing_or_link:'Candidato ausente o enlace',unavailable_on_this_host:'Ruta no disponible en este equipo',changed_during_check:'El candidato cambió durante la lectura',candidate_parent_is_link:'La ruta del candidato contiene un enlace'};
            verification.replaceChildren(node('p',labels[checked.status]||checked.status),node('p',checked.bytes_read+' bytes leídos'),node('p',checked.note));
          }catch(error){verification.replaceChildren(node('p',error.message));}finally{verify.disabled=false;}};
          const spaceButton=node('button','Comprobar espacio para el candidato');spaceButton.type='button';const spaceDetail=node('div','');
          spaceButton.onclick=async()=>{spaceButton.disabled=true;try{
            const space=await api('updates/candidate-space?'+new URLSearchParams({identifier,index:String(file.index),revision:result.remote_revision}));
            const labels={space_available_for_candidate:'Espacio disponible para la copia del candidato',insufficient_space:'Espacio insuficiente para el candidato',unavailable_on_this_host:'Ruta no disponible en este equipo',destination_directory_unavailable:'Carpeta de destino no disponible',candidate_parent_is_link:'La ruta contiene un enlace',candidate_parent_not_directory:'La ruta contiene un archivo en lugar de carpeta',disk_space_unreadable:'No se pudo medir el espacio',not_checked_no_candidate:'No hay candidato verificable'};
            spaceDetail.replaceChildren(node('p',labels[space.status]||space.status),node('p',space.note));
            if(space.free_space_verified)spaceDetail.append(node('p','Libre: '+space.free_bytes+' bytes · mínimo del candidato: '+space.required_bytes+' bytes · Medido: '+space.checked_at),node('p','Carpeta medida: '+space.measured_path));
          }catch(error){spaceDetail.replaceChildren(node('p',error.message));}finally{spaceButton.disabled=false;}};
          const download=node('button','Descargar/reanudar candidato separado');download.type='button';const downloadBox=node('div','');
          download.onclick=async()=>{download.disabled=true;try{const job=await api('updates/downloads',{identifier,index:file.index,revision:result.remote_revision,expected_sha256:plan.candidate.sha256});watchCandidateDownload(job,downloadBox);}catch(error){downloadBox.replaceChildren(node('p',error.message));}finally{download.disabled=false;}};
          const jobs=node('button','Ver descargas de este candidato');jobs.type='button';jobs.onclick=async()=>{try{const list=await api('updates/downloads?'+new URLSearchParams({identifier,index:String(file.index),revision:result.remote_revision}));downloadBox.replaceChildren(node('p',list.note));if(list.history_warning)downloadBox.append(node('p',list.history_warning));for(const job of list.rows){const item=node('div','');downloadBox.append(item);watchCandidateDownload(job,item);}}catch(error){downloadBox.replaceChildren(node('p',error.message));}};
          planDetail.append(spaceButton,spaceDetail,verify,verification,download,jobs,downloadBox);
        }
      }catch(error){planDetail.replaceChildren(node('p',error.message));}finally{planButton.disabled=false;}};
      panel.append(node('p',result.note),planButton,planDetail);line.append(panel);
    }catch(error){notice(error.message);}finally{button.disabled=false;}
  };
  return button;
}
async function showUpdateFiles(identifier,detail,offset){try{const report=await api('updates/files?identifier='+encodeURIComponent(identifier)+'&offset='+offset+'&limit=10');detail.querySelector('[data-update-files]')?.remove();const panel=node('div','');panel.dataset.updateFiles='true';panel.append(node('p',report.note));for(const file of report.rows){const line=node('div','');line.append(node('p',file.filename+' · '+file.destination));const button=node('button','Comprobar SHA-256 local');button.type='button';button.onclick=async()=>{button.disabled=true;button.textContent='Leyendo archivo…';try{const result=await api('updates/local-check?identifier='+encodeURIComponent(identifier)+'&index='+file.index);line.querySelector('[data-local-check]')?.remove();const status=node('p',result.status+' · '+result.bytes_read+' bytes leídos'+(result.note?' · '+result.note:''));status.dataset.localCheck='true';line.append(status);}catch(error){notice(error.message);}finally{button.disabled=false;button.textContent='Comprobar SHA-256 local';}};line.append(button,remoteFileCheckButton(identifier,file,line));panel.append(line);}if(offset>0){const prev=node('button','Archivos anteriores');prev.onclick=()=>showUpdateFiles(identifier,detail,Math.max(0,offset-10));panel.append(prev);}if(report.next_offset!==null){const next=node('button','Más archivos');next.onclick=()=>showUpdateFiles(identifier,detail,report.next_offset);panel.append(next);}detail.append(panel);}catch(error){notice(error.message);}}
async function showUpdateTargets(offset=0){const box=$('#updates-result');try{const result=await api('updates?offset='+offset+'&limit=10');box.replaceChildren(node('p',result.models+' fuentes de modelos · '+result.applications+' aplicaciones · '+result.untracked_catalog_files+' archivos sin fuente rastreable'));for(const row of result.rows){const detail=document.createElement('details');detail.append(node('summary',(row.label||row.id)+' · '+(row.kind==='model'?row.catalog_file_count+' archivos del catálogo':row.file_found?'ejecutable encontrado':'ejecutable no comprobado')));if(row.kind==='model')detail.append(node('p','Revisiones de enlaces: '+row.catalog_revisions.join(', ')));if(row.kind==='model'){const cached=node('button','Ver documentos guardados');cached.type='button';cached.onclick=()=>showCachedUpdateDocuments(row.id,detail);detail.append(cached);const list=node('button','Ver archivos y comprobar uno');list.type='button';list.onclick=()=>showUpdateFiles(row.id,detail,0);detail.append(list);}if(row.source_url)detail.append(link(row.source_url,'Abrir fuente'));if(row.kind==='model'||row.live_check_supported){const check=node('button','Consultar fuente oficial');check.type='button';check.onclick=async()=>{check.disabled=true;try{const data=await api('updates/check?kind='+encodeURIComponent(row.kind)+'&identifier='+encodeURIComponent(row.id));detail.querySelector('[data-update-check]')?.remove();const panel=node('div','');panel.dataset.updateCheck='true';panel.append(node('p',data.status+' · '+(data.latest_revision||data.tag||'')),node('p',data.note));if(data.missing_file_count)panel.append(node('p',data.missing_file_count+' archivos del catálogo no figuran en la revisión remota; revisar compatibilidad antes de cualquier descarga.'));detail.append(panel);}catch(error){notice(error.message);}finally{check.disabled=false;}};detail.append(check);}else detail.append(node('p','Revisión manual: fuente de versiones pendiente de configurar.'));box.append(detail);}if(offset>0){const prev=node('button','Anterior');prev.onclick=()=>showUpdateTargets(Math.max(0,offset-10));box.append(prev);}if(result.next_offset!==null){const next=node('button','Siguiente');next.onclick=()=>showUpdateTargets(result.next_offset);box.append(next);}box.append(node('p',result.note));}catch(error){box.replaceChildren(node('p',error.message));}}
$('#updates-load').onclick=()=>showUpdateTargets();
$('#updates-discover').onsubmit=async event=>{event.preventDefault();const form=event.currentTarget,values=new FormData(form),box=$('#updates-discover-result');try{const report=await api('updates/discover?kind='+encodeURIComponent(values.get('kind'))+'&query='+encodeURIComponent(values.get('query')));box.replaceChildren(node('p',report.note));for(const row of report.rows){const item=node('p',row.id+' · '+(row.already_catalogued||row.already_integrated?'ya registrado':'nuevo candidato')+' · '+(row.description||row.pipeline_tag||''));item.append(link(row.url,' Abrir fuente'));box.append(item);}if(!report.rows.length)box.append(node('p','No hubo resultados en esta consulta.'));}catch(error){box.replaceChildren(node('p',error.message));}};

$('#catalog').onclick=async()=>{try{const c=await api('resources');let box=$('#resource-list');box.replaceChildren(node('p',c.notes.join(' ')),node('p','Inventarios: '+c.inventories.map(x=>x.Nombre+' · '+x.Serie+' · '+x.Fecha).join(' / ')));const labels={temporary_download_recorded:'Temporal de descarga registrado; revisar en FDM',possible_elsewhere_size_match:'Posible archivo en otra ubicación; revisar identidad',recorded_size_match:'Ruta y tamaño registrados',recorded_path_size_unknown:'Ruta registrada; tamaño del catálogo desconocido',recorded_size_mismatch:'Ruta registrada; tamaño distinto, revisar',not_recorded:'No consta en los inventarios'};for(const g of c.groups){let d=document.createElement('details');d.append(node('summary',g.label+' · '+g.files.filter(x=>x.status!=='not_recorded').length+'/'+g.files.length+' archivos con registro o candidato'));for(const f of g.files){let n=node('div','');n.className='resource';n.append(node('strong',f.filename+' · '+(labels[f.status]||f.status)),node('p','Carpeta del catálogo: '+f.destination_folder));for(const match of f.inventory_path_matches||f.inventory_matches||[])n.append(node('p','Inventario '+match.serial+' · '+match.path+' · '+match.bytes+' bytes · '+(match.captured_at||'fecha no disponible')));for(const match of f.inventory_temporary_matches||[])n.append(node('p','Temporal registrado: '+match.serial+' · '+match.path+' · '+match.bytes+' bytes. Su tamaño no confirma descarga completa; revisa FDM antes de renombrar, eliminar o descargar de nuevo.'));for(const match of f.inventory_other_locations||[])n.append(node('p','Otra ubicación candidata: '+match.serial+' · '+match.path+' · '+match.bytes+' bytes'));if(f.other_locations_partial)n.append(node('p','Lista parcial de candidatos: '+f.other_locations_count+' coincidencias de nombre y tamaño.'));if(f.status==='possible_elsewhere_size_match')n.append(node('p','Nombre y tamaño coincidentes no prueban identidad. Comprueba el archivo antes de moverlo o descargarlo de nuevo.'));if(f.status==='recorded_size_mismatch'||f.status==='recorded_path_size_unknown')n.append(node('p','Revisa el archivo registrado antes de descargarlo otra vez.'));if(f.status==='not_recorded'&&c.inventories.length>=2&&f.download_url)n.append(link(f.download_url,f.download_url));else if(f.status==='not_recorded')n.append(node('p','Importa ambos inventarios antes de decidir una descarga.'));d.append(n);}box.append(d);}}catch(e){notice(e.message);}};
$('#tools').onclick=async()=>{try{$('#tool-list').textContent='Comprobando dependencias locales…';$('#tool-list').textContent=JSON.stringify(await api('tools'),null,2);}catch(e){notice(e.message);}};
try{await bootstrap();const q=new URLSearchParams(location.search);$('#create').reference.value=q.get('reference')||'';$('#create').elements.namedItem('title').value=(q.get('title')||'').slice(0,150);$('#create').brief.value=(q.get('brief')||'').slice(0,12000);if(pid)await select(pid);}catch(e){notice(e.message);}setInterval(refresh,3000);

$('#request-revision').onclick=()=>{$('#revision-form').hidden=false;};
$('#revision-submit').onclick=async()=>{if(!pid)return;try{await api('revision/'+encodeURIComponent(pid),{reason:$('#revision-reason').value});$('#revision-reason').value='';$('#revision-form').hidden=true;await refresh();notice('Revisión guardada. Reanuda los agentes cuando quieras corregir esta etapa.');}catch(e){notice(e.message);}};
$('#clarify').onclick=async()=>{if(!pid)return;try{await api('clarifications/'+pid,{message:$('#clarification').value});notice('Aclaración guardada. Reanuda los agentes.');}catch(e){notice(e.message);}};

$('#adapters').onclick=async()=>{try{notice('Comprobando modelos locales y entornos Python…');const items=await api('adapters');const box=$('#adapter-list');box.replaceChildren();const kokoro=items.find(x=>x.family==='kokoro');$('#voice-check').elements.namedItem('voice').replaceChildren(new Option('Selecciona una voz',''),...(kokoro?.available_voices||[]).filter(v=>/^e[fm]_/.test(v)).map(v=>new Option(v,v)));for(const item of items){const d=document.createElement('details');d.append(node('summary',item.family+' · '+item.backend+' · '+(item.ready?'Requisitos locales encontrados':'Necesita configuración')));d.append(node('p',item.problems.join(' · ')||'Inferencia y calidad pendientes de validar.'));if(item.suspicious_files?.length)d.append(node('p','Archivos sospechosos: '+item.suspicious_files.join(', ')));if(item.optional_missing_files?.length)d.append(node('p','Recursos opcionales ausentes o rechazados: '+item.optional_missing_files.join(', ')));if(item.model_dir)d.append(node('p','Carpeta seleccionada: '+item.model_dir));const form=document.createElement('form');const fields=item.backend==='native'?['model_dir','python_executable','source_dir',...(['magihuman','framepack'].includes(item.family)?['runtime_config']:[])]:['workflow_path','output_node'];for(const name of fields){const label=node('label',name);const input=document.createElement('input');input.name=name;input.value=item.configuration[name]||((name==='model_dir'?item.model_dir:name==='python_executable'?item.python_executable:'')||'');label.append(input);form.append(label);}const save=node('button','Guardar adaptador');save.type='submit';form.append(save);form.onsubmit=async e=>{e.preventDefault();try{const cfg={};for(const name of fields)cfg[name]=form.elements.namedItem(name).value;await api('adapters/'+item.family,cfg);notice('Adaptador '+item.family+' guardado. Vuelve a detectar para comprobarlo.');}catch(e){notice(e.message);}};d.append(form);if(item.backend==='comfyui'&&item.family!=='wan'){const prepare=node('button','Preparar workflow sin generar');const options=document.createElement('textarea');options.placeholder='Opcional: JSON con model_map, parameter_bindings y output_node';prepare.onclick=async()=>{try{const report=await api('adapters/'+item.family+'/prepare',options.value.trim()?JSON.parse(options.value):{});d.append(node('pre',JSON.stringify(report,null,2)));notice('Workflow preparado. No se inició generación.');}catch(e){notice(e.message);}};d.append(options,prepare);}box.append(d);}notice('Diagnóstico terminado. No se han descargado pesos.');}catch(e){notice(e.message);}};

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

async function loadReferenceReport(selected){try{const r=await api('reference-video/'+encodeURIComponent(selected));if(pid!==selected)return;const box=$('#reference-result');box.replaceChildren(node('h3','Análisis: '+r.status),node('p','Verificación de hechos externos: pendiente'));
 if(r.reuse){box.append(node('p','Análisis compartido desde '+r.reuse.base_project_id+' · copia del informe: '+r.reuse.copied_at),node('p','Los fotogramas y subtítulos pertenecen al proyecto base; conserva su disco conectado.'));if(/^[a-z0-9][a-z0-9-]{0,99}$/.test(r.reuse.base_project_id))box.append(link('Abrir proyecto base','/studio?project='+encodeURIComponent(r.reuse.base_project_id)));}
 for(const frame of r.frames||[]){const d=node('div',frame.timestamp_seconds.toFixed(2)+' segundos');const image=document.createElement('img');image.src=frame.url;image.alt='Fotograma de referencia';image.style.maxWidth='240px';d.append(image);box.append(d);}
 if(r.transcript_srt_url)box.append(link('Descargar transcripción SRT',r.transcript_srt_url));
 box.append(node('pre',JSON.stringify(r,null,2)));if(!['queued','running','downloading'].includes(r.status)){clearInterval(referenceTimer);referenceTimer=null;}
 }catch(e){notice(e.message);clearInterval(referenceTimer);}}
$('#reference-video-file').onchange=async event=>{const file=event.target.files[0];if(!file)return;if(!pid){notice('Selecciona primero el proyecto.');return;}const selected=pid;try{if(file.size>500000000)throw Error('El video supera 500 MB');notice('Cargando video al proyecto local…');const response=await fetch('/api/studio/reference-video/'+encodeURIComponent(selected)+'/upload',{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});const result=await response.json();if(!response.ok)throw Error(result.detail);notice('Video guardado. El análisis todavía no se inició.');await loadReferenceReport(selected);}catch(e){notice(e.message);}};
$('#reference-analyze').onclick=async()=>{if(!pid){notice('Selecciona primero el proyecto.');return;}const selected=pid;try{await api('reference-video/'+encodeURIComponent(selected)+'/analyze',referenceOptions());notice('Análisis local iniciado en CPU. Los modelos ausentes se indicarán en el informe.');clearInterval(referenceTimer);await loadReferenceReport(selected);referenceTimer=setInterval(()=>loadReferenceReport(selected),5000);}catch(e){notice(e.message);}};
$('#reference-report').onclick=async()=>{if(!pid)return;clearInterval(referenceTimer);await loadReferenceReport(pid);};

function referenceOptions(){return {vision:$('#reference-vision').checked,transcribe:$('#reference-transcribe').checked,summary:$('#reference-summary').checked,vision_model:$('#reference-vision-model').value};}
$('#reference-download').onclick=async()=>{if(!pid){notice('Selecciona primero el proyecto.');return;}const selected=pid;try{const url=$('#reference-url').value.trim();if(!url)throw Error('Indica el enlace del video de YouTube');await api('reference-video/'+encodeURIComponent(selected)+'/analyze',{...referenceOptions(),url});notice('Descarga y análisis local iniciados.');clearInterval(referenceTimer);await loadReferenceReport(selected);referenceTimer=setInterval(()=>loadReferenceReport(selected),5000);}catch(e){notice(e.message);}};

$('#reference-runtime').onclick=async()=>{try{$('#reference-runtime-result').textContent=JSON.stringify(await api('reference-runtime'),null,2);}catch(e){notice(e.message);}};

function storageRow(value={},selected=false){const row=document.createElement('div');row.className='storage-volume';const pick=document.createElement('input');pick.type='radio';pick.name='active-volume';pick.checked=selected;pick.setAttribute('aria-label','Usar este disco al reiniciar');const name=document.createElement('input');name.dataset.field='name';name.placeholder='Nombre: Datos 8 TB 1';name.value=value.name||'';name.required=true;name.maxLength=80;const path=document.createElement('input');path.dataset.field='path';path.placeholder='Carpeta de proyectos de este disco';path.value=value.projects_dir||'';path.required=true;const remove=node('button','Quitar de esta lista');remove.type='button';remove.onclick=()=>row.remove();row.append(pick,name,path,remove);$('#storage-volumes').append(row);}
$('#storage-add').onclick=()=>storageRow();
$('#storage-load').onclick=async()=>{try{const state=await api('storage');$('#storage-volumes').replaceChildren();for(const volume of state.volumes)storageRow(volume,volume.projects_dir===state.configured_projects_dir);$('#storage-status').textContent=JSON.stringify(state,null,2);$('#storage-finals').value=state.final_outputs_dir||'';if(!state.volumes.length)notice('Todavía no hay discos registrados. Añade las carpetas que quieras utilizar.');}catch(e){notice(e.message);}};
$('#storage-config').onsubmit=async event=>{event.preventDefault();try{const rows=Array.from($('#storage-volumes').children);const volumes=rows.map(row=>({name:row.querySelector('[data-field=name]').value,projects_dir:row.querySelector('[data-field=path]').value}));const selected=rows.findIndex(row=>row.querySelector('[type=radio]').checked);if(selected<0)throw Error('Selecciona un disco de trabajo');await api('storage',{volumes,active_projects_dir:volumes[selected].projects_dir,final_outputs_dir:$('#storage-finals').value.trim()});notice('Discos guardados. Reinicia la app para aplicar la selección. No se movieron archivos.');await $('#storage-load').onclick();}catch(e){notice(e.message);}};

$('#storage-check').onclick=async()=>{try{const report=await api('storage/readiness'),box=$('#storage-readiness');box.replaceChildren(node('h3',report.ready?'Discos disponibles':'Revisa el almacenamiento'));for(const check of report.checks){const free=check.free_bytes===null?'Espacio sin consultar':(check.free_bytes/1073741824).toFixed(1)+' GiB libres';box.append(node('p',check.role+': '+check.path+' · '+(check.available?'conectado':'no disponible')+' · '+free));}for(const problem of report.problems)box.append(node('p',problem));box.append(node('p',report.note));}catch(e){notice(e.message);}};

$('#coverage-load').onclick=async()=>{try{const report=await api('integration-coverage'),box=$('#coverage-result');box.replaceChildren(node('p',report.total+' familias · '+report.prepared_recipes+' recetas preparadas · '+report.native_workers+' implementaciones nativas · '+report.bound_workflows+' workflows vinculados · '+report.reference_templates+' plantillas oficiales para preparar. Sin pruebas de inferencia.'));for(const model of report.models){const d=document.createElement('details');d.append(node('summary',model.family+' · '+model.preparation_state),node('p',model.title+' · '+model.capability),node('p',model.next_step),node('pre',JSON.stringify(model,null,2)));box.append(d);}}catch(e){notice(e.message);}};
$('#applications-load').onclick=async()=>{try{const report=await api('applications'),box=$('#applications-result');box.replaceChildren();for(const app of report.applications){const d=document.createElement('details');d.append(node('summary',app.label+' · '+(app.file_found?'Ejecutable localizado':'Pendiente de configurar')),node('p',app.purpose),node('p','Ejecutables admitidos: '+app.executables.join(', ')));if(app.automation_tools?.length)d.append(node('p','Automatización disponible para el productor: '+app.automation_tools.join(', ')+'. Requiere validar el runtime y los resultados.'));const label=node('label','Ruta del ejecutable instalado o portable'),input=document.createElement('input');input.value=app.executable;input.placeholder='Ruta absoluta del ejecutable';label.append(input);const save=node('button','Guardar ruta');save.onclick=async()=>{try{await api('applications/'+app.id,{executable:input.value});notice(app.label+': ruta guardada; no se abrió la aplicación.');}catch(e){notice(e.message);}};const file=document.createElement('input');file.placeholder='Archivo relativo al proyecto (opcional)';const open=node('button','Abrir desde el proyecto');open.onclick=async()=>{if(!pid){notice('Selecciona primero un proyecto.');return;}try{const result=await api('applications/'+app.id+'/launch',{project_id:pid,...(file.value?{file:file.value}:{})});notice(app.label+': proceso iniciado ('+result.pid+'). Revisa el resultado en su ventana.');}catch(e){notice(e.message);}};d.append(label,save);if(app.mode==='managed_cli')d.append(node('p','Controlada por los flujos del Estudio; no abre una aplicación separada.'));else d.append(file,open);box.append(d);}}catch(e){notice(e.message);}};

function showSetupReport(report){
 const box=$('#setup-report-result');
 box.replaceChildren(node('p',report.total_families+' familias · '+report.prepared_recipes+' recetas · '+report.summary));
 for(const model of report.models){
  const detail=document.createElement('details');
  detail.append(node('summary',model.family+' · '+(model.problems.length?'Requiere configuración':'Rutas encontradas; entorno sin probar')));
  for(const problem of model.problems)detail.append(node('p',problem));
  detail.append(node('p','Imports requeridos: '+(model.imports_required.join(', ')||'Nodos del servidor ComfyUI')),
   node('p','Entorno separado sugerido en el disco de la app: '+model.suggested_environment_dir));
  if(model.platform_requirement)detail.append(node('p',model.platform_requirement));
  if(model.source_reference)detail.append(node('p','Código requerido: '+model.source_reference.repo+' · '+model.source_reference.revision));
  detail.append(node('pre',JSON.stringify(model,null,2)));box.append(detail);
 }
 if(report.storage.problems.length)box.append(node('p',report.storage.problems.join(' · ')));
}
$('#setup-report').onclick=async()=>{try{showSetupReport(await api('setup'));notice('Revisión de rutas terminada. No se comprobaron dependencias ni se cargaron modelos.');}catch(e){notice(e.message);}};
$('#setup-save-report').onclick=async()=>{try{showSetupReport(await api('setup/report',{}));notice('Informe guardado en la configuración local de la app.');}catch(e){notice(e.message);}};
$('#setup-discover').onclick=async()=>{
 const button=$('#setup-discover');button.disabled=true;
 try{
  const text=$('#setup-roots').value.trim();
  const report=await api('setup/discover',text?{roots:text.split(/\r?\n/).map(s=>s.trim()).filter(Boolean)}:{});
  const box=$('#setup-discovery-result');box.replaceChildren(node('p',report.entries_examined+' entradas revisadas · '+(report.limited?'Búsqueda limitada; puedes acotar las carpetas':'Búsqueda terminada')));
  for(const root of report.roots)box.append(node('p',root.path+' · '+(root.available?'conectado':'no disponible')));
  for(const app of report.applications){
   if(!app.candidates.length)continue;
   const detail=document.createElement('details');detail.append(node('summary',app.label+' · '+app.candidates.length+' candidatos'));
   if(app.configured_executable)detail.append(node('p','Ruta conservada: '+app.configured_executable));
   for(const path of app.candidates){
    const use=node('button','Vincular esta ruta de '+app.label);
    use.onclick=async()=>{try{await api('applications/'+app.id,{executable:path});notice('Ruta de '+app.label+' guardada. El ejecutable no se inició.');use.disabled=true;}catch(e){notice(e.message);}};
    detail.append(node('p',path),use);
   }
   box.append(detail);
  }
  if(report.python_candidates.length){const detail=document.createElement('details');detail.append(node('summary','Intérpretes Python encontrados'));for(const path of report.python_candidates)detail.append(node('p',path));detail.append(node('p','Asigna el Python del entorno adecuado en el adaptador del modelo. No se comprueba su versión al buscar.'));box.append(detail);}
  if(report.installers_not_executed.length){const detail=document.createElement('details');detail.append(node('summary','Posibles instaladores, sin ejecutar'));for(const path of report.installers_not_executed)detail.append(node('p',path));box.append(detail);}
  for(const error of report.errors)box.append(node('p',error));
  box.append(node('p',report.note));notice('Búsqueda terminada. No se modificó ninguna ruta automáticamente.');
 }catch(e){notice(e.message);}finally{button.disabled=false;}
};
$('#setup-runtime-family').onchange=()=>{$('#setup-runtime-form').hidden=true;delete $('#setup-runtime-form').dataset.family;};
$('#setup-runtime-load').onclick=async()=>{
 const family=$('#setup-runtime-family').value;
 try{const report=await api('setup/runtime/'+family);if(family!==$('#setup-runtime-family').value)return;
  const form=$('#setup-runtime-form'),box=$('#setup-runtime-fields');box.replaceChildren();
  for(const [name,text] of Object.entries(report.fields)){const label=node('label',text),input=document.createElement('input');input.name=name;input.value=report.values[name]||'';input.placeholder='Ruta local absoluta';input.required=true;label.append(input);box.append(label);}
  form.dataset.family=family;form.hidden=false;
 }catch(e){notice(e.message);}
};
$('#setup-runtime-form').onsubmit=async event=>{
 event.preventDefault();const form=event.target,family=form.dataset.family;if(!family)return;
 const data=Object.fromEntries(new FormData(form));
 try{await api('setup/runtime/'+family,data);notice('Configuración de '+family+' guardada. No se movieron pesos ni se inició generación.');}catch(e){notice(e.message);}
};

let deliveryRecoveryPending=false;
$('#retry-final-delivery').onclick=async()=>{
 if(!pid||deliveryRecoveryPending)return;
 const selected=pid;deliveryRecoveryPending=true;$('#retry-final-delivery').disabled=true;
 try{$('#delivery-retry-result').textContent='Comprobando integridad y copiando al disco final. No se inicia generación.';
  await api('final-delivery/'+encodeURIComponent(selected)+'/retry',{});
  if(pid===selected){await refresh();$('#delivery-retry-result').textContent='Entrega final recuperada sin volver a generar.';}
 }catch(error){if(pid===selected)$('#delivery-retry-result').textContent=error.message;}
 finally{deliveryRecoveryPending=false;$('#retry-final-delivery').disabled=false;}
};

let queueRequest=0;
async function loadQueue(){
 const request=++queueRequest;const expanded=new Set([...$('#queue-result').querySelectorAll('details[open]')].map(detail=>detail.dataset.id));
 const report=await api('queue');if(request!==queueRequest)return;const box=$('#queue-result');box.replaceChildren(node('p','Estado: '+report.status+' · '+(report.message||'')));
 for(const item of report.items){const detail=document.createElement('details');detail.append(node('summary',item.title+' · '+item.status),node('p',item.projects_root),node('p',item.message||''));
  detail.dataset.id=item.id;detail.open=expanded.has(item.id);
  const progress=item.progress;if(progress){detail.append(node('p',progress.available?'Productor: '+progress.status+' · '+progress.message:progress.message));if(progress.updated_at)detail.append(node('p','Última actividad guardada: '+progress.updated_at));if(progress.total_stages){detail.append(node('p',progress.completed_stages+' / '+progress.total_stages+' etapas completadas'));for(const stage of progress.stages)detail.append(node('p',stage.name+' · '+stage.status));}}
  const open=node('button','Abrir proyecto');open.disabled=item.projects_root!==report.projects_root;open.onclick=()=>select(item.project_id);detail.append(open);
  if(['blocked','stopped','interrupted','awaiting_input','awaiting_human'].includes(item.status)){const retry=node('button','Volver a poner pendiente');retry.disabled=report.worker_active;retry.onclick=async()=>{try{await api('queue/retry',{id:item.id});await loadQueue();}catch(error){notice(error.message);}};detail.append(retry);}
  const remove=node('button','Retirar de la cola');remove.disabled=report.worker_active;remove.onclick=async()=>{try{await api('queue/remove',{id:item.id});await loadQueue();notice('Registro retirado; archivos del proyecto conservados.');}catch(error){notice(error.message);}};detail.append(remove);
  if(item.status==='pending')for(const [direction,label] of [['up','Subir'],['down','Bajar']]){const move=node('button',label);move.disabled=report.worker_active||report.items.indexOf(item)===(direction==='up'?0:report.items.length-1);move.onclick=async()=>{try{await api('queue/move',{id:item.id,direction});await loadQueue();}catch(error){notice(error.message);}};detail.append(move);}
  box.append(detail);
 }
 $('#queue-start').disabled=report.worker_active;
}
$('#queue-load').onclick=()=>loadQueue().catch(error=>notice(error.message));
$('#queue-add').onclick=async()=>{if(!pid){notice('Selecciona primero un proyecto existente.');return;}try{await api('queue/enqueue',{project_id:pid});await loadQueue();notice('Proyecto añadido. Añadirlo no inicia generación.');}catch(error){notice(error.message);}};
for(const action of ['start','pause'])$('#queue-'+action).onclick=async()=>{try{await api('queue/'+action,{});await loadQueue();}catch(error){notice(error.message);}};
setInterval(()=>{if(!document.querySelector('[data-pane=queue]').hidden)loadQueue().catch(error=>notice(error.message));},5000);

$('#queue-inspect').onclick=async()=>{const button=$('#queue-inspect');button.disabled=true;try{const report=await api('queue/inspect'),box=$('#queue-inspection');box.replaceChildren(node('h3',report.ready?'Cola preparada según estas comprobaciones':'Revisa la cola antes de ejecutar'),node('p',report.note),node('p','Ollama: '+(report.model_status.configured||'sin modelo seleccionado')+' · '+(report.model_status.installed?'instalado':report.model_status.checked?'no figura en Ollama':'sin comprobar')));for(const problem of report.storage.problems)box.append(node('p',problem));for(const problem of report.problems||[])box.append(node('p',problem));if(!report.items.length)box.append(node('p','No hay proyectos en la cola.'));for(const item of report.items)box.append(node('p',item.title+' · '+(item.problems.join('; ')||item.status)));}catch(error){notice(error.message);}finally{button.disabled=false;}};

$('#queue-freeze-pilot').onclick=async()=>{const button=$('#queue-freeze-pilot');button.disabled=true;try{await api('queue/freeze-pilot',{});await $('#production-metrics-load').onclick();notice('Piloto de diez proyectos fijado. No se inició producción.');}catch(error){notice(error.message);}finally{button.disabled=false;}};
$('#production-metrics-load').onclick=async()=>{const button=$('#production-metrics-load');button.disabled=true;try{const report=await api('production-metrics'),box=$('#production-metrics-result');box.replaceChildren(node('h3','Tiempos medidos de la cola'),node('p',report.note),node('p',report.completed_runs_measured+' trabajos medidos · '+report.elapsed_seconds_total+' segundos acumulados · pico RAM del equipo: '+(report.ram_peak_mb ?? 'sin medir')+' MB · pico VRAM NVIDIA: '+(report.vram_peak_mb ?? 'sin medir')+' MB · reintentos registrados: '+report.retries_recorded),node('p','Etapas aprobadas: '+report.approved_stage_count+' · causas de reintento: '+Object.entries(report.retry_causes_by_status||{}).map(([status,count])=>status+' '+count).join(' · ')+' · aprobación editorial en la primera decisión: '+(report.first_pass_approval_rate===null?'sin medir':Math.round(report.first_pass_approval_rate*100)+' %')+' ('+report.editorial_first_decisions_count+' etapas con decisión)'));const pilot=report.pilot_candidate;box.append(node('p',(pilot.frozen?'Piloto fijado':'Piloto provisional (primeros diez registros actuales)')+': '+pilot.completed+' / '+pilot.target_projects+' terminados · '+pilot.blocked_or_waiting+' bloqueados o en espera · duración '+pilot.completed_with_duration+' / '+pilot.completed+' · RAM '+pilot.completed_with_ram+' / '+pilot.completed+' · VRAM '+pilot.completed_with_vram+' / '+pilot.completed+' · mediciones completas: '+(pilot.measurements_complete?'sí':'no')+(pilot.missing_from_queue?' · '+pilot.missing_from_queue+' proyectos retirados de la cola':'')+(pilot.saved_pilot_on_other_root?' · el piloto guardado pertenece a otro disco':'')+(pilot.queue_projects_total>10?' · '+(pilot.queue_projects_total-10)+' registros fuera del corte':'')));box.append(node('p','Evidencia del piloto terminado: render técnicamente verificado '+pilot.completed_with_render_verification+' / '+pilot.completed+' · copia final registrada '+pilot.completed_with_final_copy+' / '+pilot.completed+' (si hay disco final configurado). Los recibos no vuelven a comprobar archivos ni calidad editorial.'));box.append(node('p','Solo piloto: '+pilot.completed_elapsed_seconds_total+' s de intentos finales terminados · pico RAM '+(pilot.ram_peak_mb ?? 'sin medir')+' MB · pico VRAM '+(pilot.vram_peak_mb ?? 'sin medir')+' MB · '+pilot.retries_recorded+' reintentos · primera decisión editorial '+(pilot.first_pass_approval_rate===null?'sin medir':Math.round(pilot.first_pass_approval_rate*100)+' %')+' ('+pilot.editorial_first_decisions_count+' etapas)'));const members=document.createElement('details');members.append(node('summary','Ver los proyectos del piloto'));for(const member of pilot.projects||[])members.append(node('p',(member.title||member.project_id)+' · '+member.status+' · '+member.project_id));box.append(members);for(const item of report.projects){box.append(node('p',(item.title||item.project_id)+' · '+item.status+' · '+(item.elapsed_seconds===null?'Duración no disponible':item.elapsed_seconds+' s')+(item.message?' · '+item.message:'')));const stages=Object.entries(item.stage_active_seconds||{});if(stages.length)box.append(node('p','Etapas activas: '+stages.map(([name,seconds])=>name+' '+seconds+' s').join(' · ')));for(const attempt of item.retry_history||[])box.append(node('p','Reintento tras '+attempt.status+' · '+(attempt.message||'Sin causa registrada')+' · '+(attempt.retried_at||'fecha no disponible')+(attempt.resource_usage?' · RAM '+(attempt.resource_usage.host_ram_peak_mb ?? 'sin medir')+' MB · VRAM '+(attempt.resource_usage.gpu_vram_peak_mb ?? 'sin medir')+' MB':'')+(attempt.stage_active_seconds?' · Etapas '+Object.entries(attempt.stage_active_seconds).map(([name,seconds])=>name+' '+seconds+' s').join(', '):'')));}}catch(error){notice(error.message);}finally{button.disabled=false;}};

const verificationLabels={passed:'Verificado técnicamente',failed:'Verificación fallida',running:'Verificación en curso',unknown:'Sin verificación'};
const integrityLabels={matches:'Coincide con el hash guardado',missing:'Archivo ausente',invalid_path:'Ruta fuera de la carpeta permitida',hash_mismatch:'Archivo modificado',changed_during_check:'El archivo cambió durante la lectura',unreadable:'No se pudo leer',receipt_mismatch:'El recibo no corresponde al render',destination_not_configured:'El disco final no está configurado'};
$('#finals-load').onclick=async()=>{const button=$('#finals-load');button.disabled=true;try{const report=await api('finals'),box=$('#finals-result');box.replaceChildren(node('p',report.note));if(report.truncated)box.append(node('p','Lista parcial: se alcanzó el límite de proyectos.'));if(report.root_available===false)box.append(node('p','El disco de proyectos no está disponible. Conéctalo para consultar los finales.'));else if(!report.projects.length)box.append(node('p','No hay entregas o verificaciones registradas en este disco.'));for(const project of report.projects){const detail=document.createElement('details');detail.append(node('summary',project.title+' · '+(verificationLabels[project.verification_status]||project.verification_status)+(project.verification_current?' · vigente':' · revisar datos o revisión')),node('p',project.copied?(project.final_copy_current?'Copia final registrada y vigente':'Copia registrada; revisar datos o revisión'):'Render en el proyecto'));if(project.football_selection)detail.append(node('p','Selección de fútbol al verificar: '+project.football_selection.selection_id.slice(0,12)+' · '+project.football_selection.selected_metrics.join(', ')+' · correspondencia visual pendiente de revisión'));for(const output of project.outputs)detail.append(node('p',(output.available?'Disponible: ':'No disponible: ')+output.path));const check=node('button','Comprobar integridad ahora');check.onclick=async()=>{check.disabled=true;check.textContent='Calculando hashes…';try{const result=await api('finals/'+encodeURIComponent(project.project_id)+'/integrity');detail.querySelector('[data-integrity-result]')?.remove();const panel=node('div','');panel.dataset.integrityResult='true';panel.setAttribute('role','status');panel.append(node('p','Integridad comprobada: '+(result.all_files_match?'archivos coinciden':'revisar archivos')+' · verificación vigente: '+(result.verification_current?'sí':'no')+' · copia vigente: '+(result.final_copy_current?'sí':'no')));if(!result.receipt_manifest_matches)panel.append(node('p','El recibo final contiene archivos distintos o repetidos.'));if(!result.outputs.length)panel.append(node('p','No hay salidas verificadas para comprobar.'));for(const file of result.outputs)panel.append(node('p',(file.source||'Origen inválido')+' · '+(integrityLabels[file.source_result]||file.source_result)+(file.final_result?' · copia: '+(integrityLabels[file.final_result]||file.final_result):'')));detail.append(panel);}catch(error){notice(error.message);}finally{check.disabled=false;check.textContent='Comprobar integridad ahora';}};const open=node('button','Abrir proyecto');open.onclick=()=>select(project.project_id);const sources=node('button','Ver fuentes del render');sources.type='button';sources.onclick=async()=>{sources.disabled=true;try{const result=await api('finals/'+encodeURIComponent(project.project_id)+'/sources');detail.querySelector('[data-source-trace]')?.remove();const panel=node('div','');panel.dataset.sourceTrace='true';panel.setAttribute('role','status');panel.append(node('p',result.note));for(const output of result.outputs){panel.append(node('p',output.output_path+' · '+(output.trace_complete?'Entradas enlazadas por recibos':'Trazabilidad incompleta: '+output.problem)));for(const input of output.inputs)panel.append(node('p',input.role+' · '+input.path+' · SHA-256 '+input.sha256+' · '+(input.registered?'procedencia registrada, uso comercial '+input.commercial_use:'sin registro de procedencia coincidente')));}detail.append(panel);}catch(error){notice(error.message);}finally{sources.disabled=false;}};detail.append(check,sources,open);box.append(detail);}for(const error of report.errors)box.append(node('p',error.project_id+': '+error.message));}catch(error){notice(error.message);}finally{button.disabled=false;}};

function renderVersions(report,selected){
 if(pid!==selected)return;const box=$('#versions-result');box.replaceChildren(node('p','Versiones guardadas; añadirlas a la cola no inicia generación.'));
 if(report.summary)box.append(node('p',report.summary.total+' versiones · '+report.summary.rendered+' terminadas · '+report.summary.awaiting_human+' requieren aprobación · '+report.summary.blocked+' bloqueadas · '+report.summary.unavailable+' no disponibles'));
 const selectedIds=new Set();
 for(const version of report.versions){const row=node('p',version.language+' · '+(version.status==='selection_changed'?'selección deportiva modificada':version.status)+' '+(version.message||''));
  if(version.source_football_selection)row.append(node('span',' · Selección deportiva original: '+version.source_football_selection.selection_id.slice(0,12)));
  if(version.job_status)row.append(node('span',' · Productor: '+version.job_status+' · Verificación: '+version.verification_status+' · '+(version.final_copy_registered?'copia final registrada':'sin copia final registrada')));
  if(version.project_id)row.append(link(' Abrir versión','/studio?project='+encodeURIComponent(version.project_id)));
  if(['created','existing'].includes(version.status)&&version.can_enqueue!==false){const check=document.createElement('input');check.type='checkbox';check.setAttribute('aria-label','Seleccionar '+version.language);check.onchange=()=>{if(check.checked)selectedIds.add(version.project_id);else selectedIds.delete(version.project_id);};row.prepend(check);}
  box.append(row);
 }
 if(!report.versions.length)box.append(node('p','Este proyecto no tiene versiones registradas.'));
 else{const enqueue=node('button','Añadir versiones seleccionadas a la cola');enqueue.onclick=async()=>{enqueue.disabled=true;try{if(pid!==selected)throw Error('Selecciona de nuevo el proyecto base.');if(!selectedIds.size)throw Error('Marca primero las versiones que quieras añadir.');const result=await api('queue/enqueue-batch',{project_ids:[...selectedIds]});notice(result.added.length+' añadidas · '+result.existing.length+' ya estaban en la cola. No se inició generación.');}catch(error){notice(error.message);}finally{enqueue.disabled=false;}};box.append(enqueue);
 const reuse=node('button','Compartir análisis base con las seleccionadas');reuse.onclick=async()=>{reuse.disabled=true;try{if(pid!==selected)throw Error('Selecciona de nuevo el proyecto base.');if(!selectedIds.size)throw Error('Marca primero las versiones.');const result=await api('reference-reuse/'+encodeURIComponent(selected),{project_ids:[...selectedIds]});notice(result.versions.map(item=>item.project_id+': '+item.status+(item.message?' · '+item.message:'')).join(' | '));}catch(error){notice(error.message);}finally{reuse.disabled=false;}};box.append(reuse);}
}
$('#versions-load').onclick=async()=>{if(!pid){notice('Selecciona primero un proyecto.');return;}const selected=pid;try{renderVersions(await api('language-versions/'+encodeURIComponent(selected)),selected);}catch(error){notice(error.message);}};
$('#versions-create').onclick=async()=>{if(!pid){notice('Selecciona primero un proyecto.');return;}const selected=pid,button=$('#versions-create');button.disabled=true;try{const languages=$('#version-languages').value.split(',').map(value=>value.trim()).filter(Boolean),report=await api('language-versions/'+encodeURIComponent(selected),{languages});await bootstrap();renderVersions(report,selected);}catch(error){notice(error.message);}finally{button.disabled=false;}};

$('#versions-requirements').onclick=async()=>{if(!pid){notice('Selecciona primero un proyecto.');return;}const selected=pid,button=$('#versions-requirements');button.disabled=true;try{const report=await api('language-requirements/'+encodeURIComponent(selected));if(pid!==selected)return;const box=$('#versions-requirements-result');box.replaceChildren(node('p',report.note));for(const item of report.candidates){const detail=document.createElement('details');detail.append(node('summary',item.family+' · '+item.capability+' · '+(item.files_configured?'archivos configurados':'revisar recursos')));if(item.model_dir)detail.append(node('p',item.model_dir));if(item.language_binding)detail.append(node('p','Correspondencia del adaptador: '+item.target_language+' → '+item.language_binding+' (sin prueba de voz)'));if(item.language_problem)detail.append(node('p',item.language_problem));if(item.family==='kokoro'&&item.language_binding)detail.append(node('p',item.matching_local_voices?.length?'Voces locales coincidentes: '+item.matching_local_voices.join(', '):'No hay voces locales coincidentes con el idioma objetivo.'));for(const problem of item.problems)detail.append(node('p',problem));if(item.required_modules?.length)detail.append(node('p','Dependencias por comprobar: '+item.required_modules.join(', ')));box.append(detail);}if(!report.candidates.length)box.append(node('p','Sin adaptadores de voz, traducción o transcripción registrados.'));}catch(error){notice(error.message);}finally{button.disabled=false;}};

$('#download-plan').onclick=async()=>{const button=$('#download-plan');button.disabled=true;try{const report=await api('download-plan'),box=$('#download-plan-result');box.replaceChildren(node('p',report.note),node('p',report.planned_files+' archivos no registrados. No se inició ninguna descarga.'),node('p','Inventarios usados: '+report.inventories.map(item=>item.Nombre+' · '+item.Serie+' · '+(item.Fecha||'sin fecha')).join(' / ')));if(report.filename_collisions_across_folders.length)box.append(node('p','Nombres repetidos entre carpetas: '+report.filename_collisions_across_folders.join(', ')));for(const folder of report.folders){const detail=document.createElement('details');detail.append(node('summary',folder.destination_folder+' · '+folder.files.length+' archivos'),node('p','Guardar en: '+folder.destination_folder));const urls=node('textarea','');urls.readOnly=true;urls.value=folder.files.map(item=>item.url).join('\n');urls.rows=Math.min(8,folder.files.length+1);urls.setAttribute('aria-label','Enlaces de '+folder.destination_folder);detail.append(urls);for(const item of folder.files)detail.append(node('p',item.filename+' · '+(item.size_bytes===null?'tamaño no verificado':item.size_bytes+' bytes')));box.append(detail);}if(report.without_download_url.length)box.append(node('p',report.without_download_url.length+' archivos requieren revisar su URL de descarga.'));}catch(error){notice(error.message);}finally{button.disabled=false;}};

async function loadProjectTranslation(selected){const report=await api('translation/'+encodeURIComponent(selected));if(pid!==selected)return;const box=$('#translation-result');box.replaceChildren(node('p','Traducción: '+report.status+' · '+(report.language||'')));if(report.message)box.append(node('p',report.message));if(report.status==='completed'){box.append(node('p','Revisa exactitud y naturalidad antes de usar el texto. Fragmentos recuperados: '+report.resumed_segments));const text=node('textarea','');text.readOnly=true;text.rows=8;text.value=report.text;text.setAttribute('aria-label','Guion traducido');box.append(text);}}
$('#translation-load').onclick=async()=>{if(!pid)return;try{await loadProjectTranslation(pid);}catch(error){notice(error.message);}};
$('#translation-start').onclick=async()=>{if(!pid){notice('Selecciona primero un proyecto.');return;}const selected=pid,button=$('#translation-start');button.disabled=true;try{await api('translation/'+encodeURIComponent(selected),{text:$('#translation-text').value});if(pid===selected)notice('Traducción local iniciada; consulta su estado. No se inició producción.');await loadProjectTranslation(selected);}catch(error){notice(error.message);}finally{button.disabled=false;}};

function renderSourceLanguage(report,selected){if(pid!==selected)return;$('#source-language-result').replaceChildren(node('p',report.note),node('p','Detectado: '+(report.detected_language||'sin datos')+' · Confirmado: '+(report.confirmed_language||'sin confirmar')));if(report.confirmation_outdated)$('#source-language-result').append(node('p','Cambió la referencia o el análisis; revisa de nuevo el idioma.'));$('#source-language').value=report.confirmed_language||report.detected_language||'';}
$('#source-language-load').onclick=async()=>{if(!pid)return;const selected=pid;try{renderSourceLanguage(await api('reference-language/'+encodeURIComponent(selected)),selected);}catch(error){notice(error.message);}};
$('#source-language-save').onclick=async()=>{if(!pid)return;const selected=pid;try{renderSourceLanguage(await api('reference-language/'+encodeURIComponent(selected),{language:$('#source-language').value.trim()}),selected);}catch(error){notice(error.message);}};

let footballSchema=null,footballDefinitions=null,footballQueryId=0;
const footballLabels={ranking:'Estadísticas por ranking',matches:'Partidos de una edición',match:'Ficha de un partido',player:'Jugador en una edición',player_history:'Historial de jugador',historical:'Ranking histórico',coaches:'Entrenadores por actas',coach_balance:'Balance de entrenador',teams:'Equipos de una edición',team:'Ficha de equipo',squad:'Inscripciones de un equipo',standings:'Clasificación oficial',head_to_head:'Enfrentamientos entre equipos',definitions:'Definiciones de métricas'};
const footballFieldLabels={edition:'Edición / temporada oficial',entity:'Entidad de la estadística',metrics:'Métricas oficiales, separadas por comas',metric:'Métrica oficial',phase:'Fase',team_id:'ID oficial del equipo',player_id:'ID oficial del jugador',coach_id:'ID oficial del entrenador',match_id:'ID oficial del partido',team1:'ID oficial del primer equipo',team2:'ID oficial del segundo equipo',order:'Orden',lineups:'Incluir alineaciones'};
function footballFields(){
 const action=footballSchema?.actions.find(item=>item.name===$('#football-action').value),box=$('#football-fields');box.replaceChildren();if(!action)return;
 for(const field of action.fields.filter(field=>field!=='competition')){const spec={...(footballSchema.parameters?.[field]||{type:'string'}),...(action.choices?.[field]?{enum:action.choices[field]}:{})},required=action.required.includes(field),label=node('label',(footballFieldLabels[field]||field)+(required?' · obligatorio':''));let input;
  if(spec.enum||spec.type==='boolean'){input=document.createElement('select');if(!required)input.append(new Option('Predeterminado: '+String(action.defaults?.[field]??'sin filtro'),''));for(const value of spec.enum||[true,false])input.append(new Option(String(value),String(value)));}
  else{input=document.createElement('input');input.type=spec.type==='integer'?'number':'text';if(spec.minimum!==undefined)input.min=spec.minimum;if(spec.type==='integer')input.step='1';if(spec.pattern)input.pattern=spec.pattern;}
  input.dataset.footballField=field;input.required=required;label.append(input);box.append(label);
  if(field==='entity')input.onchange=()=>{const metrics=box.querySelector('[data-football-field=metrics]');if(metrics)metrics.value='';syncFootballMetricPickers();};
  if(field==='metrics'&&footballDefinitions?.competition===$('#football-competition').value){const picker=document.createElement('select');picker.dataset.footballMetricPicker='true';picker.setAttribute('aria-label','Métrica de las definiciones oficiales');const add=node('button','Añadir métrica elegida');add.type='button';add.onclick=()=>{if(!picker.value)return;const values=input.value.split(',').map(item=>item.trim()).filter(Boolean);if(!values.includes(picker.value))values.push(picker.value);input.value=values.join(', ');};label.append(picker,add);}

 }
 syncFootballMetricPickers();
 box.append(node('p','Consulta primero las definiciones de métricas y utiliza IDs oficiales. No se completan identidades ni estadísticas por suposición.'));
}
function syncFootballMetricPickers(){const action=$('#football-action').value,entity=$('#football-fields').querySelector('[data-football-field=entity]')?.value,actor=action==='ranking'?(entity==='team'?'TEAM':'PLAYER'):'PLAYER';for(const picker of $('#football-fields').querySelectorAll('[data-football-metric-picker]')){const options=(footballDefinitions?.items||[]).filter(item=>item.actors.includes(actor));picker.replaceChildren(new Option(options.length?'Selecciona una métrica oficial':'Sin métricas para esta entidad',''),...options.map(item=>new Option(item.name,item.name)));}}
function footballTypedParameters(){const values={};for(const input of $('#football-fields').querySelectorAll('[data-football-field]')){if(!input.value.trim())continue;const field=input.dataset.footballField,spec=footballSchema.parameters?.[field]||{type:'string'};let value=input.value.trim();if(spec.type==='integer'){value=Number(value);if(!Number.isSafeInteger(value))throw Error('Indica un número entero para '+field);}else if(spec.type==='array')value=value.split(',').map(item=>item.trim()).filter(Boolean);else if(spec.type==='boolean')value=value==='true';values[field]=value;}return values;}
$('#football-action').onchange=()=>{footballQueryId++;footballFields();$('#football-parameters').value='';$('#football-result').replaceChildren(node('p','Consulta modificada; pulsa Consultar ahora para obtener datos.'));};
$('#football-competition').onchange=()=>{footballQueryId++;footballDefinitions=null;footballFields();$('#football-result').replaceChildren(node('p','Competición modificada; consulta de nuevo para obtener datos.'));};
$('#football-load').onclick=async()=>{footballQueryId++;footballDefinitions=null;try{footballSchema=await api('football/schema');$('#football-competition').replaceChildren(...footballSchema.competitions.map(name=>new Option(name,name)));$('#football-action').replaceChildren(...footballSchema.actions.map(item=>new Option(footballLabels[item.name]||item.name,item.name)));$('#football-action').value='definitions';footballFields();$('#football-form').hidden=false;$('#football-result').replaceChildren(node('p',footballSchema.coverage_note));}catch(error){notice(error.message);}};
function prepareFootballFollowup(suggestion){const query=suggestion.query;if(!footballSchema?.actions.some(item=>item.name===query.action)||!footballSchema.competitions.includes(query.competition))return;footballQueryId++;if($('#football-competition').value!==query.competition)footballDefinitions=null;$('#football-competition').value=query.competition;$('#football-action').value=query.action;$('#football-parameters').value='';footballFields();for(const input of $('#football-fields').querySelectorAll('[data-football-field]')){const value=query[input.dataset.footballField];if(value!==undefined&&value!==null)input.value=Array.isArray(value)?value.join(', '):String(value);}$('#football-result').replaceChildren(node('p','Consulta preparada con el ID oficial. Revisa los campos y pulsa Consultar ahora; todavía no se enviaron peticiones.'));$('#football-form').scrollIntoView({block:'start'});}
function renderFootballResult(report,box){
 box.replaceChildren(node('p',report.note));if(!report.success){box.append(node('p',report.error||'No se pudo completar la consulta; no hay respaldo antiguo.'));return;}
 const data=report.data||{};box.append(node('h3','Resultado de '+(data.fuente||'conector UEFA')));
 if(data.advertencia)box.append(node('p','Advertencia de la fuente: '+data.advertencia));
 if(data.alcance)box.append(node('pre','Alcance: '+JSON.stringify(data.alcance,null,2)));
 const sources=[...(data.url?[{url:data.url,consultado_utc:data.consultado_utc}]:[]),...(Array.isArray(data.consultas)?data.consultas:[])];
 for(const source of sources){let url;try{url=new URL(source.url);}catch{continue;}if(url.protocol!=='https:'||!(url.hostname==='uefa.com'||url.hostname.endsWith('.uefa.com')))continue;const row=node('p','Consulta: '+(source.consultado_utc||'fecha no indicada')+' · '),a=link('Fuente oficial',url.href);a.target='_blank';a.rel='noopener noreferrer';row.append(a);box.append(row);}
 const collection=['registros','definiciones','inscripciones','grupos','equipos'].find(key=>Array.isArray(data[key])&&data[key].every(item=>item&&typeof item==='object'&&!Array.isArray(item)));
 if(collection){const records=data[collection],flat=records.slice(0,100).map(record=>{const row={};for(const [key,value] of Object.entries(record)){if(key==='estadisticas'&&value&&typeof value==='object'&&!Array.isArray(value))for(const [metric,number] of Object.entries(value))row['estadisticas.'+metric]=number;else row[key]=value;}return row;}),allColumns=[...new Set(flat.flatMap(row=>Object.keys(row)))],columns=allColumns.slice(0,24);
  box.append(node('p',records.length+' registros devueltos por la fuente. Los datos no disponibles no se convierten en cero.'));
  if(flat.length&&columns.length){const scroll=document.createElement('div');scroll.className='football-table-wrap';const table=document.createElement('table'),head=document.createElement('thead'),header=document.createElement('tr');for(const column of columns){const cell=node('th',column);cell.scope='col';header.append(cell);}if(report.followups?.length)header.append(node('th','Consultar por ID oficial'));head.append(header);table.append(head);const body=document.createElement('tbody');for(const record of flat){const row=document.createElement('tr');for(const column of columns){const value=record[column];row.append(node('td',value===null||value===undefined?'Dato no disponible':typeof value==='object'?JSON.stringify(value):String(value)));}if(report.followups?.length){const cell=document.createElement('td');for(const suggestion of report.followups.filter(item=>item.row_index===flat.indexOf(record))){const button=node('button',suggestion.label);button.type='button';button.onclick=()=>prepareFootballFollowup(suggestion);cell.append(button);}row.append(cell);}body.append(row);}table.append(body);scroll.append(table);box.append(scroll);}
  if(records.length>100||allColumns.length>24)box.append(node('p','Tabla parcial: máximo 100 filas y 24 columnas. El resultado completo está en los datos originales.'));
 }
 const raw=document.createElement('details');raw.append(node('summary','Ver datos originales completos'),node('pre',JSON.stringify(data,null,2)));box.append(raw);
}
$('#football-form').onsubmit=async event=>{event.preventDefault();const queryId=++footballQueryId;const selectedAction=$('#football-action').value,selectedCompetition=$('#football-competition').value;if(selectedAction==='definitions')footballDefinitions=null;const button=$('#football-query'),box=$('#football-result');box.replaceChildren(node('p','Consultando fuente oficial; no se muestran resultados anteriores.'));button.disabled=true;try{const extra=JSON.parse($('#football-parameters').value.trim()||'{}');if(!extra||Array.isArray(extra)||typeof extra!=='object'||'action'in extra||'competition'in extra)throw Error('Indica solo parámetros adicionales como objeto JSON.');const typed=footballTypedParameters();if(Object.keys(extra).some(field=>field in typed))throw Error('No repitas el mismo campo en el formulario y en JSON.');const report=await api('football/query',{...extra,...typed,action:$('#football-action').value,competition:$('#football-competition').value});if(queryId!==footballQueryId)return;if(report.success&&selectedAction==='definitions'&&Array.isArray(report.data?.definiciones))footballDefinitions={competition:selectedCompetition,items:report.data.definiciones.filter(item=>item&&typeof item.name==='string'&&/^[a-z][a-z0-9_]*$/.test(item.name)&&Array.isArray(item.actors)).map(item=>({name:item.name,actors:item.actors}))};renderFootballResult(report,box);}catch(error){if(queryId===footballQueryId)box.replaceChildren(node('p','Consulta no completada: '+error.message));}finally{button.disabled=false;}};

const roundForm = $('#football-round-form');
const roundResult = $('#football-round-result');
const roundTeams = {'Argentina':'Argentina','Australia':'Australia','Belgium':'Bélgica','Brazil':'Brasil','Cameroon':'Camerún','Canada':'Canadá','Costa Rica':'Costa Rica','Croatia':'Croacia','Denmark':'Dinamarca','Ecuador':'Ecuador','England':'Inglaterra','France':'Francia','Germany':'Alemania','Ghana':'Ghana','Iran':'Irán','Japan':'Japón','Mexico':'México','Morocco':'Marruecos','Netherlands':'Países Bajos','Poland':'Polonia','Portugal':'Portugal','Qatar':'Qatar','Saudi Arabia':'Arabia Saudita','Senegal':'Senegal','Serbia':'Serbia','South Korea':'Corea del Sur','Spain':'España','Switzerland':'Suiza','Tunisia':'Túnez','Uruguay':'Uruguay','USA':'Estados Unidos','Wales':'Gales'};
const orderedTeams = Object.entries(roundTeams).sort((a, b) => a[1].localeCompare(b[1], 'es'));
for (const field of ['first_team', 'second_team']) {
 for (const [id, label] of orderedTeams) roundForm.elements[field].add(new Option(label, id));
}
const editionPicker = roundForm.elements.edition;
const qatarEdition = editionPicker.value;
const editionTeamFilters = new Map();
api('football/desk-editions').then(({editions}) => {
 const current = editionPicker.value;
 for (const item of editions) editionTeamFilters.set(item.id, item.team_filter);
 editionPicker.replaceChildren(...editions.map(item => new Option(item.label, item.id)));
 editionPicker.value = current;
}).catch(error => notice(error.message));
editionPicker.addEventListener('change', () => {
 const qatar = editionPicker.value === qatarEdition;
 const round = roundForm.elements.round;
 round.value = 'edition';
 round.disabled = !qatar;
 for (const key of ['first', 'second']) {
  const team = roundForm.elements[key + '_team'];
  const club = roundForm.elements[key + '_club'];
  team.disabled = !qatar;
  team.closest('label').hidden = !qatar;
  club.disabled = qatar || editionTeamFilters.get(editionPicker.value) === false;
  club.closest('label').hidden = club.disabled;
 }
});
let roundPreviewUrl = null;
function clearRoundResult(message) {
 if (roundPreviewUrl) URL.revokeObjectURL(roundPreviewUrl);
 roundPreviewUrl = null;
 roundResult.replaceChildren(message ? node('p', message) : document.createTextNode(''));
}
let roundRequest = 0;
roundForm.addEventListener('input', () => {
 roundRequest++;
 clearRoundResult('Consulta de nuevo para actualizar las cifras.');
});
roundForm.addEventListener('submit', async event => {
 event.preventDefault();
 const request = ++roundRequest;
 const form = new FormData(roundForm);
 const value = key => (form.get(key) || '').trim();
 const edition = value('edition');
 const players = ['first', 'second'].map(key => {
  const team = value(key + (edition === qatarEdition ? '_team' : '_club'));
  return {...(team ? {team} : {}), name: value(key + '_name')};
 });
 const button = roundForm.querySelector('button[type=submit]');
 clearRoundResult('Consultando la fuente de estadísticas…');
 button.disabled = true;
 try {
  const {report, preview_svg, export_token, metric_matrix, display_metrics, errors, failed_metrics, phase_note, coverage_note} = await api('football/round-goals', {round: form.get('round') || 'edition', edition, players});
  if (request !== roundRequest) return;
  clearRoundResult('');
  if (!report) {
   roundResult.append(node('p', 'No se verificaron los dos jugadores. Usa el nombre que publica la fuente.'));
   for (const error of errors || []) roundResult.append(node('p', error));
   if (metric_matrix?.length) {
    const details = document.createElement('details');
    details.append(node('summary', 'Ver ' + metric_matrix.length + ' métricas comunes sin cifra verificada'));
    const table = document.createElement('table');
    const heading = table.createTHead().insertRow();
    for (const label of ['Métrica', 'Jugador 1', 'Jugador 2', 'Estado']) {
     const cell = node('th', label); cell.scope = 'col'; heading.append(cell);
    }
    const rows = table.createTBody();
    for (const metric of metric_matrix) {
     const row = rows.insertRow();
     row.append(node('td', metric.label || metric.metric));
     for (const fact of metric.values) row.append(node('td', fact?.value ?? 'Sin dato'));
     row.append(node('td', 'Sin cifra verificada'));
    }
    const wrap = node('div', ''); wrap.className = 'football-table-wrap';
    wrap.append(table); details.append(wrap); roundResult.append(details);
   }
   return;
  }
  if (coverage_note) roundResult.append(node('p', coverage_note));
  if (phase_note) roundResult.append(node('p', phase_note));
  const supported = new Set(display_metrics);
  const choices = [];
  if (metric_matrix) {
   const states = {both_players:'Dos jugadores', one_player:'Un jugador', not_observed:'Sin cifra'};
   const totals = {both_players:0, one_player:0, not_observed:0};
   for (const metric of metric_matrix) if (metric.standard && metric.availability in totals) totals[metric.availability]++;
   roundResult.append(node('p', 'Métricas comunes verificadas en esta consulta: '
    + totals.both_players + ' para ambos, ' + totals.one_player + ' para uno, '
    + totals.not_observed + ' sin cifra. Las métricas propias de la fuente aparecen al final.'));
   const wrap = node('div', '');
   wrap.className = 'football-table-wrap';
   const table = document.createElement('table');
   const header = document.createElement('tr');
   for (const label of ['Métrica', ...report.records.map(row => row.identity.name), 'Estado', 'Mostrar']) {
    const cell = node('th', label); cell.scope = 'col'; header.append(cell);
   }
   table.createTHead().append(header);
   const rows = table.createTBody();
   const groupLabels = {participation:'Participación', attack:'Ataque',
    creation_and_passing:'Creación y pases', defence_and_duels:'Defensa y duelos',
    goalkeeping:'Portería', discipline:'Disciplina', physical:'Físico', other:'Otras métricas de la fuente'};
   let currentGroup = null;
   for (const metric of metric_matrix) {
    const group = metric.group || 'other';
    if (group !== currentGroup) {
     const heading = rows.insertRow();
     const cell = node('th', groupLabels[group] || group);
     cell.colSpan = 5;
     cell.scope = 'rowgroup';
     heading.append(cell);
     currentGroup = group;
    }
    const row = rows.insertRow();
    const label = metric.label || metric.metric.replaceAll('_', ' ');
    row.append(node('td', label));
    for (const fact of metric.values) {
     const cell = row.insertCell();
     cell.textContent = fact?.value ?? 'Sin dato';
     if (fact?.source_url) cell.append(' · ', link('Fuente', fact.source_url));
    }
    row.append(node('td', states[metric.availability] || 'Sin verificar'));
    const cell = row.insertCell();
    if (supported.has(metric.display_metric)) {
     const checkbox = document.createElement('input');
     checkbox.type = 'checkbox';
     checkbox.value = metric.display_metric;
     checkbox.setAttribute('aria-label', 'Mostrar ' + label);
     choices.push(checkbox);
     cell.append(checkbox);
    }
   }
   wrap.append(table);
   roundResult.append(wrap);
  } else {
   for (const record of report.records) {
    roundResult.append(node('p', record.identity.name + ' · ' + (roundTeams[record.team] || record.team) + ' · Goles: ' + record.statistics.goals));
   }
  }
  for (const player of report.unresolved || []) {
   roundResult.append(node('p', (typeof player === 'string' ? player : player.name) + ' · Dato sin verificar para este alcance'));
  }
  if (errors?.length || Object.keys(failed_metrics || {}).length) {
   roundResult.append(node('p', 'Hay rankings que no se pudieron consultar. Revisa las cifras disponibles.'));
   const detail = document.createElement('details');
   detail.append(node('summary', 'Ver fallos de consulta'), node('pre', JSON.stringify({errors, failed_metrics}, null, 2)));
   roundResult.append(detail);
  }
  if (!metric_matrix) for (const query of report.queries) roundResult.append(link('Fuente: OpenFootball', query.url));
  if (export_token && supported.size) {
   const preview = node('button', metric_matrix ? 'Ver postal con la selección' : 'Seleccionar goles y ver postal');
   preview.type = 'button';
   const selectionStatus = node('p', '');
   selectionStatus.setAttribute('role', 'status');
   const exports = node('div', '');
   let previewRevision = 0;
   function resetPreview() {
    previewRevision++;
    if (roundPreviewUrl) URL.revokeObjectURL(roundPreviewUrl);
    roundPreviewUrl = null;
    exports.replaceChildren();
    selectionStatus.textContent = '';
   }
   for (const checkbox of choices) checkbox.onchange = resetPreview;
   preview.onclick = async () => {
    resetPreview();
    const metrics = metric_matrix ? choices.filter(choice => choice.checked).map(choice => choice.value) : ['goals'];
    if (metrics.length < 1 || metrics.length > 6) {
     selectionStatus.textContent = 'Elige entre una y seis métricas.';
     return;
    }
    const revision = previewRevision;
    const selection = {report, export_token, metrics};
    preview.disabled = true;
    for (const checkbox of choices) checkbox.disabled = true;
    let svg;
    try {
     svg = preview_svg || (await api('football/round-goals/preview', selection)).preview_svg;
     if (request !== roundRequest) return;
    } catch (error) {
     selectionStatus.textContent = error.message;
     return;
    } finally {
     preview.disabled = false;
     for (const checkbox of choices) checkbox.disabled = false;
    }
    roundPreviewUrl = URL.createObjectURL(new Blob([svg], {type:'image/svg+xml'}));
    const image = document.createElement('img');
    image.src = roundPreviewUrl;
    image.alt = 'Postal de comparativa de goles';
    image.className = 'football-round-preview';
    const download = link('Descargar postal SVG', roundPreviewUrl);
    const scope = report.scope;
    const basename = report.source === 'FIFA'
     ? ['fifa', scope.competition_id, scope.season_id].join('-')
     : [scope.competition || report.competition || 'uefa', scope.season || scope.seasonYear,
        scope.round || scope.phase].join('-');
    download.download = basename + '.svg';
    const dossier = node('button', 'Descargar expediente JSON');
    dossier.type = 'button';
    const saveProject = node('button', 'Guardar selección en proyecto');
    saveProject.type = 'button';
    const video = node('button', 'Descargar clip MP4');
    video.type = 'button';
    const status = node('p', '');
    status.setAttribute('role', 'status');
    dossier.onclick = async () => {
     dossier.disabled = true;
     status.textContent = 'Preparando expediente de cifras y fuentes…';
     try {
      const record = await api('football/round-goals/dossier', selection);
      if (request !== roundRequest || revision !== previewRevision) return;
      const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], {type:'application/json'}));
      const file = link('Expediente JSON', url);
      file.download = basename + '-expediente.json';
      document.body.append(file);
      file.click();
      file.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = 'Expediente listo para descargar.';
     } catch (error) {
      status.textContent = error.message;
     } finally {
      dossier.disabled = false;
     }
    };
    saveProject.onclick = async () => {
     if (!pid) {status.textContent = 'Selecciona o crea un proyecto antes de guardar la selección.';return;}
     const selectedProject = pid;
     saveProject.disabled = true;
     status.textContent = 'Guardando el expediente en el proyecto…';
     try {
      const saved = await api('football/round-goals/projects/' + encodeURIComponent(selectedProject), selection);
      if (request !== roundRequest || revision !== previewRevision) return;
      status.textContent = (saved.duplicate ? 'Selección ya guardada' : 'Selección guardada')
       + ' en ' + selectedProject + '. El agente puede leerla desde los artefactos.';
     } catch (error) {
      status.textContent = error.message;
     } finally {
      saveProject.disabled = false;
     }
    };
    video.onclick = async () => {
     video.disabled = true;
     status.textContent = 'Generando clip vertical…';
     try {
      const response = await fetch('/api/studio/football/round-goals/video', {
       method: 'POST', headers: {'Content-Type':'application/json'},
       body: JSON.stringify(selection),
      });
      if (!response.ok) throw Error((await response.json()).detail);
      const blob = await response.blob();
      if (request !== roundRequest || revision !== previewRevision) return;
      const url = URL.createObjectURL(blob);
      const file = link('Clip MP4', url);
      file.download = basename + '.mp4';
      document.body.append(file);
      file.click();
      file.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = 'Clip listo para descargar.';
     } catch (error) {
      status.textContent = error.message;
     } finally {
      video.disabled = false;
     }
    };
    exports.replaceChildren(image, download, dossier, saveProject, video, status);
   };
   roundResult.append(preview, selectionStatus, exports);
  }
 } catch (error) {
  if (request === roundRequest) clearRoundResult(error.message);
 } finally {
  button.disabled = false;
 }
});

let scenePlan=null,scenePlanProject=null;
$('#scene-subtitle-inspect').onclick=async()=>{
 const box=$('#scene-subtitle-result');box.replaceChildren();if(!pid)return;
 try{const selected=pid,path=$('#scene-subtitle-form').elements.namedItem('srt_path').value.trim();
  const result=await api('scene-subtitles-inspect/'+encodeURIComponent(selected),{srt_path:path});if(pid!==selected)return;
  box.append(node('p',result.cue_count+' subtítulos · '+(result.partial?'se muestran los primeros 100':'lista completa')+' · SHA-256 '+result.sha256));
  for(const cue of result.cues)box.append(node('p',cue.start_seconds.toFixed(2)+'–'+cue.end_seconds.toFixed(2)+' s · '+cue.text));
 }catch(error){box.append(node('p',error.message));}
};
$('#scene-subtitle-form').onsubmit=async event=>{
 event.preventDefault();if(!pid){notice('Selecciona primero una producción.');return;}
 const selected=pid,form=event.target;
 try{const result=await api('scene-subtitles/'+encodeURIComponent(selected),{
  srt_path:form.elements.namedItem('srt_path').value.trim(),language:form.elements.namedItem('language').value});
  if(pid===selected)$('#scene-subtitle-result').replaceChildren(node('p','Video con subtítulos iniciado: '+result.attempt+' · '+result.cue_count+' segmentos.'));
 }catch(error){notice(error.message);}
};
$('#scene-subtitle-status').onclick=async()=>{
 const box=$('#scene-subtitle-result');box.replaceChildren();if(!pid)return;
 try{const selected=pid,result=await api('scene-subtitles/'+encodeURIComponent(selected));if(pid!==selected)return;
  box.append(node('p','Estado: '+result.status));if(result.error)box.append(node('p',result.error));
  if(result.output)box.append(link('Descargar MP4 con pista de subtítulos',result.output.url),
   link('Descargar SRT editable',result.srt_url),node('p','SHA-256 '+result.output.sha256));
 }catch(error){box.append(node('p',error.message));}
};
$('#scene-burn-start').onclick=async()=>{
 if(!pid){notice('Selecciona primero una producción.');return;}
 const selected=pid,box=$('#scene-burn-result');box.replaceChildren();
 try{const result=await api('scene-burned-subtitles/'+encodeURIComponent(selected),{});
  if(pid===selected)box.append(node('p','Exportación visible iniciada: '+result.attempt+' · '+result.cue_count+' segmentos.'));
 }catch(error){box.append(node('p',error.message));}
};
$('#scene-burn-status').onclick=async()=>{
 const box=$('#scene-burn-result');box.replaceChildren();if(!pid)return;
 try{const selected=pid,result=await api('scene-burned-subtitles/'+encodeURIComponent(selected));if(pid!==selected)return;
  box.append(node('p','Estado: '+result.status));if(result.error)box.append(node('p',result.error));
  if(result.output)box.append(link('Descargar MP4 con subtítulos visibles',result.output.url),
   node('p','Resolución '+result.resolution.join(' × ')+' · SHA-256 '+result.output.sha256));
 }catch(error){box.append(node('p',error.message));}
};
$('#scene-audio-form').onsubmit=async event=>{
 event.preventDefault();if(!pid){notice('Selecciona primero una producción.');return;}
 const selected=pid,form=event.target;
 try{const result=await api('scene-audio-preview/'+encodeURIComponent(selected),{
  narration_path:form.elements.namedItem('narration_path').value.trim(),music_path:form.elements.namedItem('music_path').value.trim(),
  narration_db:Number(form.elements.namedItem('narration_db').value),music_db:Number(form.elements.namedItem('music_db').value)});
  if(pid===selected)$('#scene-audio-result').replaceChildren(node('p','Mezcla iniciada: '+result.attempt+'. Consulta su estado aquí.'));
 }catch(error){notice(error.message);}
};
$('#scene-audio-status').onclick=async()=>{
 const box=$('#scene-audio-result');box.replaceChildren();if(!pid)return;
 try{const selected=pid,result=await api('scene-audio-preview/'+encodeURIComponent(selected));if(pid!==selected)return;
  box.append(node('p','Estado: '+result.status));if(result.error)box.append(node('p',result.error));
  if(result.output)box.append(link('Escuchar montaje de revisión',result.output.url),node('p','SHA-256 '+result.output.sha256));
 }catch(error){box.append(node('p',error.message));}
};
$('#scene-preview-form').onsubmit=async event=>{
 event.preventDefault();if(!pid){notice('Selecciona primero una producción.');return;}
 const selected=pid,policy=event.target.elements.namedItem('fit_policy').value;
 try{const result=await api('scene-edit-preview/'+encodeURIComponent(selected),{fit_policy:policy});if(pid===selected)$('#scene-preview-result').replaceChildren(node('p','Montaje iniciado: '+result.attempt+'. Consulta su estado aquí.'));}
 catch(error){notice(error.message);}
};
$('#scene-preview-status').onclick=async()=>{
 const box=$('#scene-preview-result');box.replaceChildren();if(!pid)return;
 try{const selected=pid,result=await api('scene-edit-preview/'+encodeURIComponent(selected));if(pid!==selected)return;
  box.append(node('p','Estado: '+result.status+(result.fit_policy?' · '+result.fit_policy:'')));
  if(result.error)box.append(node('p',result.error));
  if(result.output){box.append(link('Ver montaje sin audio',result.output.url),node('p','SHA-256 '+result.output.sha256));}
 }catch(error){box.append(node('p',error.message));}
};
$('#scene-edit-check').onclick=async()=>{
 const box=$('#scene-edit-result');box.replaceChildren();if(!pid){box.append(node('p','Selecciona primero una producción.'));return;}
 try{const selected=pid,report=await api('scene-edit-readiness/'+encodeURIComponent(selected));if(pid!==selected)return;
  box.append(node('p',report.ready?'Todas las tomas están listas para preparar el montaje.':'El montaje aún tiene pendientes.'));
  for(const message of report.problems)box.append(node('p',message));
  for(const scene of report.scenes){const detail=document.createElement('details');detail.append(node('summary',scene.scene_id+' · '+(scene.ready?'Lista':'Pendiente')));if(scene.approved_take)detail.append(node('p',scene.approved_take));for(const problem of scene.problems)detail.append(node('p',problem));box.append(detail);}
 }catch(error){box.append(node('p',error.message));}
};
function showSceneManifest(manifest){
 const box=$('#scene-batch-result'),form=$('#scene-media-form');box.replaceChildren();
 box.append(node('p','Manifiesto guardado: '+manifest.scene_count+' escenas · '+manifest.aspect_ratio+' · generación '+(manifest.generation_started?'iniciada':'sin iniciar')+'.'));
 if(manifest.scene_plan_sha256!==scenePlan.scene_plan_sha256){box.append(node('p','El plan aprobado cambió después del manifiesto. Revisa la versión antes de generar.'));form.hidden=true;return;}
 form.hidden=false;form.elements.namedItem('scene_id').replaceChildren(...manifest.scenes.map(s=>new Option(s.scene_id,s.scene_id)));
 for(const scene of manifest.scenes){
  const d=document.createElement('details');d.append(node('summary',scene.scene_id+' · '+scene.status));
  d.append(node('p','Imagen: '+scene.image_prompt),node('p','Movimiento: '+scene.motion_prompt));
  if(scene.image)d.append(node('p','Imagen registrada: '+scene.image.path+' · SHA-256 '+scene.image.sha256));
  if(scene.last_error)d.append(node('p','Último intento: '+scene.last_error));
  if(scene.image&&!scene.approved_take_id&&scene.takes.length<8){
   const generate=node('button','Generar vista previa I2V local');generate.type='button';
   generate.onclick=async()=>{if(pid!==scenePlanProject)return;try{const response=await api('scene-batch-preview/'+encodeURIComponent(pid),{scene_id:scene.scene_id});notice('Iniciada la escena '+response.scene_id+'. Consulta de nuevo la mesa para ver el resultado.');generate.disabled=true;}catch(error){notice(error.message);}};
   d.append(generate);
  }
  for(const take of scene.takes){
   const row=document.createElement('div');row.append(link(take.path,take.url),node('p','SHA-256 '+take.sha256+' · '+take.duration_seconds+' s'+(scene.approved_take_id===take.sha256?' · aprobada':'')));
   if(scene.approved_take_id!==take.sha256){const label=node('label','He revisado visualmente la identidad de los personajes');const check=document.createElement('input');check.type='checkbox';label.prepend(check);const button=node('button','Aprobar esta toma');button.type='button';button.onclick=async()=>{if(pid!==scenePlanProject)return;if(!check.checked){notice('Confirma la revisión visual de identidad antes de aprobar.');return;}try{await api('scene-batch-approve/'+encodeURIComponent(pid),{scene_id:scene.scene_id,sha256:take.sha256,identity_reviewed:true});showSceneManifest(await api('scene-batch/'+encodeURIComponent(pid)));}catch(error){notice(error.message);}};row.append(label,button);}
   d.append(row);
  }
  box.append(d);
 }
}
function sceneField(labelText,kind,id,value,maxLength){
 const label=node('label',labelText),area=document.createElement('textarea');
 area.dataset.kind=kind;area.dataset.id=id;area.maxLength=maxLength;area.required=true;area.rows=3;area.value=value||'';
 label.append(area);return label;
}
$('#scene-plan-load').onclick=async()=>{
 const box=$('#scene-batch-result'),form=$('#scene-batch-form');form.hidden=true;$('#scene-media-form').hidden=true;box.replaceChildren();scenePlan=null;scenePlanProject=null;
 if(!pid){box.append(node('p','Selecciona primero una producción.'));return;}
 try{
  const selected=pid;
  const [plan,saved]=await Promise.all([api('scene-batch-plan/'+encodeURIComponent(selected)),api('scene-batch/'+encodeURIComponent(selected))]);
  if(pid!==selected)return;
  scenePlan=plan;scenePlanProject=selected;
  if(saved.scenes){showSceneManifest(saved);return;}
  const fields=$('#scene-batch-fields');fields.replaceChildren();
  const characters=[...new Set(plan.scenes.flatMap(scene=>scene.character_ids))];
  if(characters.length){fields.append(node('h3','Anclas visuales de personajes'));for(const id of characters)fields.append(sceneField('Personaje '+id,'anchor',id,'',2000));}
  fields.append(node('h3','Prompts por escena'));
  for(const scene of plan.scenes){const section=document.createElement('section');section.append(node('h3',scene.id+' · '+scene.start_seconds+'–'+scene.end_seconds+' s'),node('p',scene.description),sceneField('Prompt de imagen','image',scene.id,'',5000),sceneField('Prompt de movimiento','motion',scene.id,'',5000));fields.append(section);}
  form.hidden=false;box.append(node('p',plan.scenes.length+' escenas del plan aprobado. Completa los campos y revisa antes de guardar.'));
 }catch(error){box.append(node('p',error.message));}
};
$('#scene-batch-form').onsubmit=async event=>{
 event.preventDefault();if(!pid||!scenePlan||scenePlanProject!==pid){$('#scene-batch-result').replaceChildren(node('p','Vuelve a cargar el plan del proyecto seleccionado.'));event.target.hidden=true;return;}
 const form=event.target,box=$('#scene-batch-result'),data={aspect_ratio:form.elements.namedItem('aspect_ratio').value,image_prompts:{},motion_prompts:{},character_anchors:{}};
 for(const area of form.querySelectorAll('textarea[data-kind]')){
  const dest=area.dataset.kind==='anchor'?data.character_anchors:area.dataset.kind==='image'?data.image_prompts:data.motion_prompts;
  dest[area.dataset.id]=area.value.trim();
 }
 try{const result=await api('scene-batch/'+encodeURIComponent(pid),data);form.hidden=true;showSceneManifest(result.manifest);}
 catch(error){box.replaceChildren(node('p',error.message));}
};
$('#scene-media-form').onsubmit=async event=>{
 event.preventDefault();if(!pid||scenePlanProject!==pid)return;
 const form=event.target;
 try{await api('scene-batch-media/'+encodeURIComponent(pid),{scene_id:form.elements.namedItem('scene_id').value,kind:form.elements.namedItem('kind').value,relative_path:form.elements.namedItem('relative_path').value.trim()});form.elements.namedItem('relative_path').value='';showSceneManifest(await api('scene-batch/'+encodeURIComponent(pid)));notice('Archivo local comprobado y registrado.');}
 catch(error){notice(error.message);}
};

$('#script-diagnostic').onclick=async()=>{if(!pid)return;const box=$('#script-diagnostic-result');try{const pace=Number($('#script-pace').value);if(!Number.isInteger(pace)||pace<80||pace>220)throw Error('Usa de 80 a 220 palabras por minuto');const result=await api('script-diagnostic/'+encodeURIComponent(pid)+'?words_per_minute='+pace);box.replaceChildren();if(result.status==='missing'){box.append(node('p',result.message));return;}box.append(node('h3',result.title),node('p',result.word_count+' palabras · '+result.estimated_speech_seconds+' s de voz estimada · '+result.total_duration_seconds+' s de video'),node('p',result.source_ref_missing+' secciones sin referencia · '+result.voice_directions_missing+' sin indicaciones de voz · '+result.visual_cues_missing+' sin indicaciones visuales'));for(const row of result.sections)box.append(node('p',row.label+' · '+row.word_count+' palabras · '+row.estimated_speech_seconds+' s de voz / '+row.allocated_seconds+' s asignados · desfase '+row.speech_overrun_seconds+' s · hueco previo '+row.gap_before_seconds+' s · fuente '+(row.has_source_ref?'indicada':'pendiente')));box.append(node('p',result.limits));}catch(error){box.replaceChildren(node('p',error.message));}};

let scriptOutlineRevision=null,scriptOutlineProject=null;
const scriptOutlineLabels={apertura:'Apertura',contexto:'Contexto',desarrollo:'Desarrollo',resolucion:'Resolución',cierre:'Cierre'};
$('#script-outline-load').onclick=async()=>{if(!pid)return;const selected=pid,box=$('#script-outline-result');try{const result=await api('script-outline/'+encodeURIComponent(pid));if(pid!==selected)return;scriptOutlineProject=pid;scriptOutlineRevision=result.revision;const form=$('#script-outline-form');form.hidden=false;form.elements.namedItem('title').value=result.title;form.elements.namedItem('target_seconds').value=result.target_seconds;const container=$('#script-outline-blocks');container.replaceChildren();for(const block of result.blocks){const section=document.createElement('fieldset');section.dataset.kind=block.kind;section.append(node('legend',scriptOutlineLabels[block.kind]||block.kind));for(const [name,label,max] of [['narration','Narración',4000],['voice_direction','Indicación de voz',500],['visual_direction','Indicación visual',500],['source_ref','Fuente o verificación pendiente',1000]]){const field=node('label',label),input=document.createElement('textarea');input.name=name;input.maxLength=max;input.value=block[name];input.rows=name==='narration'?3:2;field.append(input);section.append(field);}container.append(section);}box.replaceChildren(node('p',result.status==='draft'?'Borrador guardado · '+result.updated_at_utc:'Plantilla vacía.'));if(result.analysis)box.append(node('p',result.analysis.word_count+' palabras · '+result.analysis.estimated_speech_seconds+' s estimados a 150 palabras/minuto. '+result.analysis.limits));}catch(error){box.replaceChildren(node('p',error.message));}};
$('#script-outline-form').onsubmit=async event=>{event.preventDefault();const box=$('#script-outline-result');try{if(!pid||pid!==scriptOutlineProject)throw Error('Carga el borrador del proyecto seleccionado');const form=event.target,blocks=[...$('#script-outline-blocks').querySelectorAll('fieldset')].map(section=>({kind:section.dataset.kind,...Object.fromEntries(['narration','voice_direction','visual_direction','source_ref'].map(name=>[name,section.querySelector('[name="'+name+'"]').value]))}));const result=await api('script-outline/'+encodeURIComponent(pid),{title:form.elements.namedItem('title').value,target_seconds:Number(form.elements.namedItem('target_seconds').value),blocks,expected_revision:scriptOutlineRevision});scriptOutlineRevision=result.revision;box.replaceChildren(node('p','Borrador guardado · '+result.updated_at_utc),node('p',result.analysis.word_count+' palabras · '+result.analysis.estimated_speech_seconds+' s de voz estimada / '+result.target_seconds+' s objetivo'),node('p','Sin fuente: '+(result.analysis.without_source.join(', ')||'ninguno')+' · sin voz: '+(result.analysis.without_voice.join(', ')||'ninguno')+' · sin visual: '+(result.analysis.without_visual.join(', ')||'ninguno')),node('p',result.analysis.limits));}catch(error){box.replaceChildren(node('p',error.message));}};

let packagingRevision=null,packagingProject=null;
function packagingValues(){return [...$('#packaging-fields').querySelectorAll('fieldset')].map((field,index)=>({id:String(index+1),...Object.fromEntries(['title','overlay','visual_concept','source_note'].map(name=>[name,field.querySelector('[name="'+name+'"]').value]))}));}
function packagingPreview(){const box=$('#packaging-preview'),select=$('#packaging-form').elements.namedItem('selected_id'),chosen=select.value;box.replaceChildren();for(const option of packagingValues()){const card=node('div','');card.className='packaging-card';const image=node('div',option.overlay||'Texto de la miniatura');image.className='packaging-image';card.append(image,node('h3',option.title||'Título del video'),node('p',option.visual_concept||'Describe la imagen por crear'),node('p','Fuente / revisión: '+(option.source_note||'pendiente')));if(chosen===option.id)card.append(node('strong','Selección editorial'));box.append(card);}box.append(node('p','Vista de texto a 320 px; no representa una imagen final ni mide clics.'));}
function packagingField(option){const field=document.createElement('fieldset');field.append(node('legend','Variante '+option.id));for(const [name,label,max] of [['title','Título del video',100],['overlay','Texto sobre la miniatura',45],['visual_concept','Concepto visual',500],['source_note','Fuente o hecho por revisar',500]]){const row=node('label',label),input=document.createElement(name==='title'||name==='overlay'?'input':'textarea');input.name=name;input.maxLength=max;input.value=option[name];if(name==='title'||name==='visual_concept')input.required=true;row.append(input);field.append(row);}field.oninput=packagingPreview;return field;}
function packagingSelect(selected){const select=$('#packaging-form').elements.namedItem('selected_id');select.replaceChildren(new Option('Aún sin elegir',''));for(const option of packagingValues())select.append(new Option('Variante '+option.id,option.id));select.value=selected||'';}
$('#packaging-load').onclick=async()=>{if(!pid)return;const selected=pid,box=$('#packaging-preview');try{const data=await api('packaging-options/'+encodeURIComponent(pid));if(pid!==selected)return;packagingProject=pid;packagingRevision=data.revision;$('#packaging-form').hidden=false;const options=data.options.length?data.options:[1,2].map(id=>({id:String(id),title:'',overlay:'',visual_concept:'',source_note:''}));$('#packaging-fields').replaceChildren(...options.map(packagingField));packagingSelect(data.selected_id);packagingPreview();}catch(error){box.replaceChildren(node('p',error.message));}};
$('#packaging-add').onclick=()=>{const count=$('#packaging-fields').querySelectorAll('fieldset').length;if(count>=5){notice('Máximo cinco variantes');return;}$('#packaging-fields').append(packagingField({id:String(count+1),title:'',overlay:'',visual_concept:'',source_note:''}));packagingSelect($('#packaging-form').elements.namedItem('selected_id').value);packagingPreview();};
$('#packaging-form').elements.namedItem('selected_id').onchange=packagingPreview;
$('#packaging-form').onsubmit=async event=>{event.preventDefault();const box=$('#packaging-preview');try{if(!pid||pid!==packagingProject)throw Error('Carga las variantes del proyecto seleccionado');const selected=$('#packaging-form').elements.namedItem('selected_id').value;const result=await api('packaging-options/'+encodeURIComponent(pid),{options:packagingValues(),selected_id:selected||null,expected_revision:packagingRevision});packagingRevision=result.revision;packagingPreview();box.prepend(node('p','Variantes guardadas · '+result.updated_at_utc));}catch(error){box.prepend(node('p',error.message));}};

function showProjectThumbnail(data){const box=$('#thumbnail-result');box.replaceChildren();if(data.status==='missing'){box.append(node('p',data.message));return;}const preview=document.createElement('img');preview.src=data.url+'?rev='+encodeURIComponent(data.revision);preview.alt='Miniatura local asociada a la variante '+data.selected_id;preview.style.width='min(100%,320px)';preview.style.aspectRatio='16 / 9';preview.style.objectFit='contain';box.append(preview,node('p',data.width+' × '+data.height+' · '+data.bytes+' bytes · variante '+data.selected_id+' · pendiente de revisión visual'),node('p',data.limits));}
$('#thumbnail-load').onclick=async()=>{if(!pid)return;try{showProjectThumbnail(await api('project-thumbnail/'+encodeURIComponent(pid)));}catch(error){$('#thumbnail-result').replaceChildren(node('p',error.message));}};
$('#thumbnail-file').onchange=async event=>{const file=event.target.files[0];if(!file||!pid)return;try{if(pid!==packagingProject||!packagingRevision)throw Error('Carga y guarda primero una variante seleccionada');if(file.size>8000000)throw Error('Imagen superior a 8 MB');const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(Error('No se pudo leer la imagen'));reader.readAsDataURL(file);});showProjectThumbnail(await api('project-thumbnail/'+encodeURIComponent(pid),{image_base64:encoded,expected_packaging_revision:packagingRevision}));}catch(error){$('#thumbnail-result').replaceChildren(node('p',error.message));}};

let assetSourcesRevision=null,assetSourcesProject=null;
function showAssetSources(result){const box=$('#asset-sources-result');box.replaceChildren(node('p',result.entries.length+' medios registrados · '+result.limits));for(const item of result.entries)box.append(node('p',item.path+' · '+item.source_kind+' · SHA-256 '+item.sha256+' · uso comercial '+item.commercial_use+' · modificaciones '+item.modifications+' · '+(item.license_name||'licencia sin nombre')));}
$('#asset-sources-load').onclick=async()=>{if(!pid)return;const selected=pid;try{const result=await api('asset-sources/'+encodeURIComponent(pid));if(pid!==selected)return;assetSourcesProject=pid;assetSourcesRevision=result.revision;showAssetSources(result);}catch(error){$('#asset-sources-result').replaceChildren(node('p',error.message));}};
$('#asset-sources-form').onsubmit=async event=>{event.preventDefault();const box=$('#asset-sources-result');try{if(!pid||pid!==assetSourcesProject)throw Error('Carga primero el registro del proyecto seleccionado');const f=event.target;const entry=Object.fromEntries(['path','source_kind','source_url','license_url','creator','license_name','commercial_use','modifications','notes'].map(name=>[name,f.elements.namedItem(name).value.trim()]));const result=await api('asset-sources/'+encodeURIComponent(pid),{entry,expected_revision:assetSourcesRevision});assetSourcesRevision=result.revision;showAssetSources(result);}catch(error){box.prepend(node('p',error.message));}};

async function showAssetCoverage(offset=0){if(!pid)return;const selected=pid,box=$('#asset-coverage-result');try{const data=await api('asset-coverage/'+encodeURIComponent(pid)+'?offset='+offset+'&limit=20');if(selected!==pid)return;box.replaceChildren(node('p',data.registered_total+' registrados · '+data.unregistered_total+' sin registro · '+(data.complete_scan?'inspección completa':'límite de inspección alcanzado')));for(const row of data.rows)box.append(node('p',row.path+' · '+row.bytes+' bytes · '+(row.status==='registered'?'registrado':'SIN PROCEDENCIA')));if(offset>0){const previous=node('button','Anterior');previous.type='button';previous.onclick=()=>showAssetCoverage(Math.max(0,offset-20));box.append(previous);}if(data.next_offset!==null){const next=node('button','Siguiente');next.type='button';next.onclick=()=>showAssetCoverage(data.next_offset);box.append(next);}box.append(node('p',data.limits));}catch(error){box.replaceChildren(node('p',error.message));}}
$('#asset-coverage-load').onclick=()=>showAssetCoverage();

async function showAssetUsage(offset=0){if(!pid)return;const selected=pid,box=$('#asset-usage-result');try{const data=await api('asset-usage/'+encodeURIComponent(pid)+'?offset='+offset+'&limit=20');if(selected!==pid)return;box.replaceChildren(node('p',data.total+' medios declarados · '+data.unregistered_total+' sin registro'));for(const row of data.rows)box.append(node('p',row.path+' · '+row.declared_in.join(', ')+' · '+(row.file_present?'archivo presente':'ARCHIVO AUSENTE')+' · '+(row.registered?'procedencia registrada · uso comercial '+row.commercial_use:'SIN PROCEDENCIA')));for(const problem of data.problems)box.append(node('p',problem));if(offset>0){const previous=node('button','Anterior');previous.type='button';previous.onclick=()=>showAssetUsage(Math.max(0,offset-20));box.append(previous);}if(data.next_offset!==null){const next=node('button','Siguiente');next.type='button';next.onclick=()=>showAssetUsage(data.next_offset);box.append(next);}box.append(node('p',data.limits));}catch(error){box.replaceChildren(node('p',error.message));}}
$('#asset-usage-load').onclick=()=>showAssetUsage();
