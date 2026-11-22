const $ = id => document.getElementById(id);
const dialog = $('filters'), form = $('filter-form');
let applied = {pages:1,max_requests:300,filters:{sample_size:10,published_within:'month',discovery_mode:'recent_publications',sort_by:'matching_publication_views'}};
let snapshot = [];
const numeric = ['min_views','max_views','max_channel_age_days','min_subscribers','max_subscribers','min_minutes','max_minutes','min_publication_views','min_matching_publications','pages','sample_size','max_requests'];
const format = value => value === null || value === undefined ? 'No disponible' : new Intl.NumberFormat('es-MX').format(value);
function element(tag,text,cls){const node=document.createElement(tag);node.textContent=text;if(cls)node.className=cls;return node;}
function restore(values){for(const [name,value] of values)form.elements.namedItem(name).value=value;}
function readFilters(){
  const filters={};let pages=1,max_requests=300;
  for(const [name,raw] of new FormData(form)){
    if(raw==='')continue;
    let value=raw;
    if(numeric.includes(name)){value=Number(raw);if(!Number.isSafeInteger(value)||value<0)throw Error('Usa números enteros no negativos.');}
    if(name==='max_requests')max_requests=value;else if(name==='pages')pages=value;else filters[name]=name==='country'?value.toUpperCase():value;
  }
  for(const [low,high] of [['min_views','max_views'],['min_subscribers','max_subscribers'],['min_minutes','max_minutes']]){
    if(filters[low]!==undefined && filters[high]!==undefined && filters[low]>filters[high])throw Error('El mínimo no puede superar al máximo.');
  }
  if(filters.min_matching_publications<1 || filters.min_matching_publications>filters.sample_size)throw Error('Las coincidencias mínimas deben estar entre 1 y el tamaño de la muestra.');
  if(filters.discovery_mode==='recent_publications'&&filters.published_within==='any')throw Error('Selecciona una fecha reciente para descubrir canales por publicaciones.');
  if(filters.sort_by==='matching_publication_views'&&filters.published_within==='any')throw Error('Selecciona una fecha reciente para ordenar por publicaciones coincidentes.');
  return {pages,filters,max_requests};
}
$('open-filters').onclick=()=>{snapshot=[...new FormData(form)];$('filter-error').textContent='';dialog.showModal();};
function cancel(){restore(snapshot);dialog.close();}
$('close-filters').onclick=cancel;$('cancel-filters').onclick=cancel;
dialog.addEventListener('cancel',event=>{event.preventDefault();cancel();});
$('reset-filters').onclick=()=>form.reset();
$('recent-preset').onclick=()=>{
  for(const name of ['min_views','max_views','max_channel_age_days'])form.elements.namedItem(name).value='';
  restore([['published_within','month'],['min_publication_views','100000'],['min_matching_publications','3'],['sample_size','20'],['sort_by','matching_publication_views'],['discovery_mode','recent_publications']]);
};
$('young-preset').onclick=()=>{
  form.elements.namedItem('min_views').value='1000000';
  form.elements.namedItem('max_views').value='';
  form.elements.namedItem('max_channel_age_days').value='90';
};
form.onsubmit=event=>{
  event.preventDefault();try{applied=readFilters();dialog.close();
    const n=Object.entries(applied.filters).filter(([key,value])=>key!=='sample_size' && key!=='sort_by' && key!=='discovery_mode' && value!=='any' && !(key==='min_matching_publications'&&value===1) && !(['min_views','min_minutes','min_publication_views'].includes(key)&&value===0)).length;
    $('filter-count').textContent=n?`(${n})`:'';
    // Old results must not appear as if the new filters have been searched.
    $('results').replaceChildren();$('scope').textContent='';$('query-plan-result').replaceChildren();$('status').textContent='Filtros aplicados. Pulsa Buscar canales para consultar.';
  }catch(error){$('filter-error').textContent=error.message;}
};
function productionLink(channel,video=null){
 const reference=video?'https://www.youtube.com/watch?v='+encodeURIComponent(video.id):'https://www.youtube.com/channel/'+encodeURIComponent(channel.id);
 const brief=[video?'Referencia de video para analizar localmente: '+reference:'Canal de inspiración: '+reference+'. Seleccionar primero una publicación concreta antes de analizar video.',
  'Canal: '+(channel.title||channel.id),
  video?'Tema de referencia: '+(video.title||video.id):'Investigar temas de sus publicaciones recientes y proponer un enfoque propio.',
  video?'Vistas públicas acumuladas observadas en la búsqueda: '+format(video.viewCount)+'. No representan crecimiento medido ni garantizan viralidad.':'',
  video?.audio_language_declared?'Idioma de audio declarado: '+video.audio_language_declared+'. Confirmarlo al analizar y proponer idiomas de destino distintos.':'Confirmar el idioma original antes de elegir idiomas de destino.',
  'Crear un guion original con investigación adicional y fuentes verificables. Proponer estructura, ejemplos y material visual propios o autorizado para reutilizar.',
  'Adaptar narración, subtítulos, títulos, miniaturas, música y referencias culturales a cada idioma. Comprobar licencias de los recursos.',
  'No se han verificado ingresos, monetización ni RPM. Este encargo no inicia descargas, generación ni publicación.'
 ].filter(Boolean).join('\n');
 const query=new URLSearchParams({reference,title:('Nuevo enfoque: '+(video?.title||channel.title||channel.id)).slice(0,150),brief});
 return '/studio?'+query.toString();
}
function showChannel(ch,index){
  const card=element('article','','channel');card.append(element('span',`CANAL ${index+1}`,'rank'));
  const h=element('h2',''),a=element('a',ch.title||ch.id);a.href=`https://www.youtube.com/channel/${encodeURIComponent(ch.id)}`;a.target='_blank';a.rel='noopener noreferrer';h.append(a);card.append(h);
  const produce=element('a','Crear video a partir de este canal','chip');produce.href=productionLink(ch);card.append(produce);
  const periodButton=element('button','Auditar publicaciones de 30 días','secondary');periodButton.type='button';
  const historyButton=element('button','Ver auditorías guardadas','secondary');historyButton.type='button';
  const periodBox=element('div','','scope');card.append(periodButton,historyButton,periodBox);
  function showPeriod(data){
    periodBox.replaceChildren(element('p',`${data.publications.length} publicaciones visibles · ${data.pages_read} páginas de ${data.max_pages} permitidas · ${data.complete_period?'Periodo cubierto en la lista pública':'Cobertura incompleta'}. Consultado: ${new Date(data.retrieved_at_utc).toLocaleString('es-MX')}.`),
      element('p',`Mediana de vistas acumuladas: ${format(data.analysis.median_views)}. Sin cifra: ${data.analysis.views_unknown}. ${data.note}`));
    if(data.saved_snapshot)periodBox.append(element('p',`Expediente local ${data.saved_snapshot.id} · SHA-256 ${data.saved_snapshot.report_sha256}`));
    if(data.save_error)periodBox.append(element('p',`No se guardó el expediente: ${data.save_error}`));
    if(data.analysis.top_publication_share!==null)periodBox.append(element('p',`La publicación más vista aporta ${(data.analysis.top_publication_share*100).toFixed(1)} % de las vistas observadas.`));
    const details=element('details',''),summary=element('summary','Ver todas las publicaciones consultadas'),list=element('ul','');details.append(summary);
    for(const video of data.publications){const item=element('li',''),a=element('a',video.title||video.id);a.href=video.url;a.target='_blank';a.rel='noopener noreferrer';item.append(a,element('span',` · ${format(video.viewCount)} vistas · ${video.published_at||'fecha desconocida'}`));list.append(item);}
    details.append(list);periodBox.append(details);
  }
  periodButton.onclick=async()=>{
    periodButton.disabled=true;periodBox.textContent='Consultando páginas del canal por partes…';
    try{
      const response=await fetch('/api/research/channels/period',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({channel_id:ch.id,days:30,max_pages:10})});
      const data=await response.json();if(!response.ok)throw Error(data.detail||'No se pudo auditar el canal');
      showPeriod(data);
    }catch(error){periodBox.textContent=error.message;}finally{periodButton.disabled=false;}
  };
  historyButton.onclick=async()=>{
    historyButton.disabled=true;periodBox.textContent='Leyendo expedientes locales…';
    try{const response=await fetch('/api/research/channels/period/history/'+encodeURIComponent(ch.id));const data=await response.json();if(!response.ok)throw Error(data.detail||'No se pudo leer el historial');
      periodBox.replaceChildren(element('p',`${data.snapshots.length} auditorías guardadas. Cada una conserva la fecha y cifras de su consulta.`));
      for(const row of data.snapshots){const button=element('button',`${new Date(row.retrieved_at_utc).toLocaleString('es-MX')} · ${row.publication_count} videos · ${row.complete_period?'periodo cubierto':'incompleto'}`,'secondary');button.type='button';
        button.onclick=async()=>{try{const response=await fetch('/api/research/channels/period/history/'+encodeURIComponent(ch.id)+'/'+encodeURIComponent(row.id));const saved=await response.json();if(!response.ok)throw Error(saved.detail||'No se pudo abrir el expediente');showPeriod({...saved.report,saved_snapshot:saved});}catch(error){periodBox.textContent=error.message;}};
        periodBox.append(button);
      }
    }catch(error){periodBox.textContent=error.message;}finally{historyButton.disabled=false;}
  };
  const metrics=element('div','','metrics');for(const [title,value] of [['Vistas totales',ch.viewCount],['Suscriptores',ch.subscriberCount_public_rounded]]){const metric=element('div','','metric');metric.append(element('strong',format(value)),element('span',title));metrics.append(metric);}card.append(metrics);
  const created=ch.created_at?new Date(ch.created_at):null;
  card.append(element('p',`Creado: ${created&&!Number.isNaN(created.getTime())?created.toLocaleDateString('es-MX'):'fecha no disponible'}`));
  card.append(element('p',`${format(ch.videoCount)} publicaciones públicas · País: ${ch.country_declared||'no declarado'}`));
  if(ch.matched_queries)card.append(element('p',`Temas: ${ch.matched_queries.join(' · ')}`));
  if(ch.content_review){
    const r=ch.content_review;
    if('matching_publication_views_sum' in r)card.append(element('p',`Vistas de publicaciones coincidentes: ${format(r.matching_publication_views_sum)} · suma de la muestra revisada.`));
    card.append(element('p',`${r.matched} coincidencias entre ${r.inspected} publicaciones revisadas (muestra de ${r.sample_requested}).`));
    if(r.sample_analysis){
      const a=r.sample_analysis;
      const box=element('details',''),heading=element('summary','Analizar toda la muestra revisada');box.append(heading);
      box.append(element('p',`${a.sample_returned} publicaciones devueltas de ${a.sample_requested} solicitadas · ${a.views_known} con vistas conocidas · ${a.views_unknown} sin cifra. Mediana de vistas acumuladas: ${format(a.median_views)}.`));
      if(a.top_publication_share!==null)box.append(element('p',`El video más visto reúne ${(a.top_publication_share*100).toFixed(1)} % de las vistas conocidas en esta muestra. Relación con la mediana de los demás: ${format(a.top_to_other_median_ratio)}×.`));
      box.append(element('p','Muestra limitada a las publicaciones solicitadas. No cubre necesariamente todos los videos del periodo ni mide vistas ganadas durante él.'));
      const list=element('ul','');for(const video of r.sample_publications||[]){
        if(!/^[A-Za-z0-9_-]{11}$/.test(video.id))continue;
        const item=element('li',''),link=element('a',video.title||video.id);
        link.href=`https://www.youtube.com/watch?v=${encodeURIComponent(video.id)}`;link.target='_blank';link.rel='noopener noreferrer';
        item.append(link,element('span',` · ${format(video.viewCount)} vistas acumuladas · ${video.published_at||'fecha desconocida'} · ${video.matches_filters?'Cumple los filtros':'Fuera de los filtros'}`));list.append(item);
      }box.append(list);card.append(box);
    }
    if(r.matching_publications?.length){
      const details=element('details',''),summary=element('summary','Ver publicaciones coincidentes');details.append(summary);
      const list=element('ul','');
      for(const video of r.matching_publications){
        if(!/^[A-Za-z0-9_-]{11}$/.test(video.id))continue;
        const item=element('li',''),link=element('a',video.title||video.id);
        link.href=`https://www.youtube.com/watch?v=${encodeURIComponent(video.id)}`;link.target='_blank';link.rel='noopener noreferrer';
        const date=video.published_at?new Date(video.published_at):null;
        const create=element('a','Crear producción con esta referencia','chip');
        create.href=productionLink(ch,video);
        item.append(create,element('br',''));
        item.append(link,element('p',`${format(video.viewCount)} vistas acumuladas · Publicado: ${date&&!Number.isNaN(date.getTime())?date.toLocaleDateString('es-MX'):'fecha no disponible'} · Duración: ${video.duration_iso8601||'no disponible'} · Audio declarado: ${video.audio_language_declared||'no disponible'}`));list.append(item);
      }
      details.append(list,element('small','Vistas acumuladas de estas publicaciones; no vistas ganadas por el canal durante el periodo.'));card.append(details);
    }
  }
  return card;
}
$('search').onsubmit=async event=>{
  event.preventDefault();
  const queries=[...new Set($('query').value.split(/\r?\n/).map(q=>q.trim()).filter(Boolean))];
  if(!queries.length||queries.length>5||queries.some(q=>q.length>200)){
    $('status').textContent='Escribe entre 1 y 5 temas, uno por línea, de hasta 200 caracteres.';return;
  }
  $('submit').disabled=true;$('open-filters').disabled=true;
  $('results').replaceChildren();$('scope').textContent='';$('status').textContent='Buscando canales y comprobando filtros… Puede tardar unos minutos.';
  try{
    const isBatch=queries.length>1;
    const payload=isBatch?{queries,...applied}:{query:queries[0],pages:applied.pages,filters:applied.filters};
    const response=await fetch(isBatch?'/api/research/channels/batch':'/api/research/channels',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const data=await response.json();
    $('result-order').textContent=data.order?.[0]==='matching_publication_views_sum_desc'?'Orden: vistas de publicaciones coincidentes ↓ · suscriptores ↓':'Orden: vistas totales ↓ · suscriptores ↓';
    if(!response.ok){
      if(['MISSING_KEY','INVALID_KEY','API_DISABLED','ACCESS_DENIED'].includes(data.error_code))$('configuration').textContent=data.error;
      if(isBatch && data.result_type==='channels'){
        data.results.forEach((ch,index)=>$('results').append(showChannel(ch,index)));
        $('scope').textContent=`LOTE INCOMPLETO · ${data.completed_queries.length} de ${data.queries.length} temas completados. Pendientes: ${data.pending_queries.join(' · ')}. Los resultados visibles proceden solo de temas completados en esta ejecución.`;
      }
      throw Error(data.error||data.detail||'No se pudo completar la búsqueda.');
    }
    $('configuration').textContent='YouTube respondió a esta consulta · datos consultados ahora';
    data.results.forEach((ch,index)=>$('results').append(showChannel(ch,index)));
    $('status').textContent=data.results.length?`${data.results.length} canales encontrados.`:'Ningún canal coincide en los candidatos y la muestra revisados. Prueba otros filtros.';
    if(isBatch){
      $('scope').textContent=`Lote completado · ${data.completed_queries.length} temas · canales sin duplicados.\n${Object.values(data.requests).reduce((a,b)=>a+b,0)} solicitudes API de un límite de ${data.max_requests}.\nConsultado: ${new Date(data.retrieved_at_utc).toLocaleString('es-MX')}. No es una clasificación global ni certificación de viralidad.`;
      return;
    }
    const excluded=Object.values(data.excluded).reduce((sum,n)=>sum+n,0);
    const mode=data.scope.candidate_discovery==='recent_publications'?'Canales descubiertos desde publicaciones recientes del índice de videos.':(!data.scope.lookup_mode||data.scope.lookup_mode==='keywords'?'Muestra del índice de canales.':'Canal identificado directamente; los filtros siguen aplicándose.');
    $('scope').textContent=`${mode}\nConsultado: ${new Date(data.retrieved_at_utc).toLocaleString('es-MX')} · ${data.scope.candidate_channels} canales candidatos · ${excluded} excluidos.\nAlcance limitado a los resultados consultados; no es una clasificación global. Suscriptores redondeados.\n${data.scope.content_filter_scope==='recent_upload_sample'?'Los filtros de contenido revisan publicaciones recientes; no todo el historial.':''}`;
  }catch(error){$('status').textContent=error.message;}
  finally{$('submit').disabled=false;$('open-filters').disabled=false;}
};
fetch('/api/research/channels/status').then(r=>r.json()).then(data=>{$('configuration').textContent=data.configured?'Clave local presente · se comprobará al buscar':'Pendiente: configurar la clave local de YouTube API. No se muestran datos de ejemplo.';}).catch(()=>{$('configuration').textContent='No se pudo comprobar la configuración.';});

async function configureYouTubeKey(value){
 const response=await fetch('/api/research/channels/configuration',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:value})});
 const result=await response.json();if(!response.ok)throw Error(result.detail||'No se pudo configurar la clave');
 $('youtube-api-key').value='';
 $('youtube-key-status').textContent=result.configured?(result.source==='session'?'Clave configurada para esta sesión; todavía sin verificar.':'Se utiliza la clave del entorno local; todavía sin verificar.'):'No hay una clave configurada.';
 $('configuration').textContent=result.configured?'Clave presente · se comprobará al buscar':'Pendiente: configurar YouTube API.';
}
$('youtube-key-form').onsubmit=async event=>{event.preventDefault();try{await configureYouTubeKey($('youtube-api-key').value);}catch(error){$('youtube-key-status').textContent=error.message;}};
$('youtube-key-clear').onclick=async()=>{try{await configureYouTubeKey('');}catch(error){$('youtube-key-status').textContent=error.message;}};
$('query-plan').onclick=async()=>{
 try{
  const queries=$('query').value.split(/\r?\n/).map(value=>value.trim()).filter(Boolean);
  if(!queries.length)throw Error('Escribe al menos un tema o canal.');
  const response=await fetch('/api/research/channels/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({queries,...applied})});
  const result=await response.json();if(!response.ok)throw Error(result.detail||'No se pudo preparar la consulta');
  const box=$('query-plan-result');box.replaceChildren(element('p','Previsión sin consultar YouTube · cuota restante del proyecto desconocida'));
  for(const [name,value] of Object.entries(result.maximum_requests_before_budget))box.append(element('p',name+': hasta '+value+' solicitudes'));
  box.append(element('p',result.batch_request_limit===null?'Consulta individual: límite por páginas y tiempo de búsqueda.':'Límite del lote: '+result.batch_request_limit+' solicitudes. El consumo puede ser menor.'),element('p',result.notes.join(' ')));
 }catch(error){$('query-plan-result').textContent=error.message;}
};

$('query').addEventListener('input',()=>$('query-plan-result').replaceChildren());

function observationId(value){const url=new URL(value);if(url.protocol!=='https:'||!['www.youtube.com','youtube.com'].includes(url.hostname)||url.pathname!=='/watch')throw Error('Usa un enlace HTTPS de YouTube');const id=url.searchParams.get('v');if(!/^[A-Za-z0-9_-]{11}$/.test(id||''))throw Error('ID de video inválido');return id;}
const observationForm=$('observation-form'),observationBox=$('observation-result');
function showObservations(rows){observationBox.replaceChildren(element('p',`${rows.length} observaciones guardadas para este video.`));for(const row of rows.slice().reverse())observationBox.append(element('p',`${new Date(row.observed_at_utc).toLocaleString('es-MX')} · ${row.source} · vistas ${format(row.views)} · VPH ${format(row.vph)} · engagement ${format(row.engagement_percent)} % · outlier ${format(row.outlier_ratio)}× · SEO ${format(row.seo_score)}/100${row.notes?' · '+row.notes:''}`));}
$('observation-load').onclick=async()=>{
 try{const id=observationId(observationForm.elements.namedItem('video_url').value.trim());
  const response=await fetch('/api/research/video-observations/'+encodeURIComponent(id));const result=await response.json();if(!response.ok)throw Error(result.detail||'No se pudo leer el historial');showObservations(result.observations);
 }catch(error){observationBox.textContent=error.message;}
};
observationForm.onsubmit=async event=>{
 event.preventDefault();const fields=observationForm.elements;
 const data={video_url:fields.namedItem('video_url').value.trim(),notes:fields.namedItem('notes').value.trim()};
 for(const name of ['views','vph','engagement_percent','outlier_ratio','seo_score']){const value=fields.namedItem(name).value;data[name]=value===''?null:Number(value);}
 try{const response=await fetch('/api/research/video-observations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const result=await response.json();if(!response.ok)throw Error(result.detail||'No se pudo guardar');
  $('observation-load').click();
 }catch(error){observationBox.textContent=error.message;}
};
