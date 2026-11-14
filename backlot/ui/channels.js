const $ = id => document.getElementById(id);
const dialog = $('filters'), form = $('filter-form');
let applied = {pages:1,filters:{sample_size:10}};
let snapshot = [];
const numeric = ['min_views','max_views','min_subscribers','max_subscribers','min_minutes','max_minutes','min_publication_views','pages','sample_size'];
const format = value => value === null || value === undefined ? 'No disponible' : new Intl.NumberFormat('es-MX').format(value);
function element(tag,text,cls){const node=document.createElement(tag);node.textContent=text;if(cls)node.className=cls;return node;}
function restore(values){for(const [name,value] of values)form.elements.namedItem(name).value=value;}
function readFilters(){
  const filters={};let pages=1;
  for(const [name,raw] of new FormData(form)){
    if(raw==='')continue;
    let value=raw;
    if(numeric.includes(name)){value=Number(raw);if(!Number.isSafeInteger(value)||value<0)throw Error('Usa números enteros no negativos.');}
    if(name==='pages')pages=value;else filters[name]=name==='country'?value.toUpperCase():value;
  }
  for(const [low,high] of [['min_views','max_views'],['min_subscribers','max_subscribers'],['min_minutes','max_minutes']]){
    if(filters[low]!==undefined && filters[high]!==undefined && filters[low]>filters[high])throw Error('El mínimo no puede superar al máximo.');
  }
  return {pages,filters};
}
$('open-filters').onclick=()=>{snapshot=[...new FormData(form)];$('filter-error').textContent='';dialog.showModal();};
function cancel(){restore(snapshot);dialog.close();}
$('close-filters').onclick=cancel;$('cancel-filters').onclick=cancel;
dialog.addEventListener('cancel',event=>{event.preventDefault();cancel();});
$('reset-filters').onclick=()=>form.reset();
form.onsubmit=event=>{
  event.preventDefault();try{applied=readFilters();dialog.close();
    const n=Object.entries(applied.filters).filter(([key,value])=>key!=='sample_size' && value!==0 && value!=='any').length;
    $('filter-count').textContent=n?`(${n})`:'';
    // Old results must not appear as if the new filters have been searched.
    $('results').replaceChildren();$('scope').textContent='';$('status').textContent='Filtros aplicados. Pulsa Buscar canales para consultar.';
  }catch(error){$('filter-error').textContent=error.message;}
};
function showChannel(ch,index){
  const card=element('article','','channel');card.append(element('span',`CANAL ${index+1}`,'rank'));
  const h=element('h2',''),a=element('a',ch.title||ch.id);a.href=`https://www.youtube.com/channel/${encodeURIComponent(ch.id)}`;a.target='_blank';a.rel='noopener noreferrer';h.append(a);card.append(h);
  const metrics=element('div','','metrics');for(const [title,value] of [['Vistas totales',ch.viewCount],['Suscriptores',ch.subscriberCount_public_rounded]]){const metric=element('div','','metric');metric.append(element('strong',format(value)),element('span',title));metrics.append(metric);}card.append(metrics);
  card.append(element('p',`${format(ch.videoCount)} publicaciones públicas · País: ${ch.country_declared||'no declarado'}`));
  if(ch.content_review){const r=ch.content_review;card.append(element('p',`${r.matched} coincidencias entre ${r.inspected} publicaciones revisadas (muestra de ${r.sample_requested}).`));}
  return card;
}
$('search').onsubmit=async event=>{
  event.preventDefault();$('submit').disabled=true;$('open-filters').disabled=true;
  $('results').replaceChildren();$('scope').textContent='';$('status').textContent='Buscando canales y comprobando filtros… Puede tardar unos minutos.';
  try{
    const response=await fetch('/api/research/channels',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:$('query').value,...applied})});
    const data=await response.json();if(!response.ok)throw Error(data.error||data.detail||'No se pudo completar la búsqueda.');
    data.results.forEach((ch,index)=>$('results').append(showChannel(ch,index)));
    $('status').textContent=data.results.length?`${data.results.length} canales encontrados.`:'Ningún canal coincide en los candidatos y la muestra revisados. Prueba otros filtros.';
    const excluded=Object.values(data.excluded).reduce((sum,n)=>sum+n,0);
    $('scope').textContent=`Consultado: ${new Date(data.retrieved_at_utc).toLocaleString('es-MX')} · ${data.scope.candidate_channels} canales candidatos · ${excluded} excluidos.\nMuestra de búsqueda, no clasificación global de YouTube. Suscriptores redondeados.\n${data.scope.content_filter_scope==='recent_upload_sample'?'Los filtros de contenido revisan publicaciones recientes; no todo el historial.':''}`;
  }catch(error){$('status').textContent=error.message;}
  finally{$('submit').disabled=false;$('open-filters').disabled=false;}
};
fetch('/api/research/channels/status').then(r=>r.json()).then(data=>{$('configuration').textContent=data.configured?'YouTube API configurada · consultas al buscar':'Pendiente: configurar la clave local de YouTube API. No se muestran datos de ejemplo.';}).catch(()=>{$('configuration').textContent='No se pudo comprobar la configuración.';});
