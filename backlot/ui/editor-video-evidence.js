const el=(tag,text='')=>{const node=document.createElement(tag);node.textContent=String(text);return node;};
const time=value=>Number.isFinite(value)?`${Math.floor(value/60).toString().padStart(2,'0')}:${(value%60).toFixed(3).padStart(6,'0')}`:'--:--.---';

export function initializeVideoEvidence({getProject,getEdl,sourceToTimeline,jump}){
  const refreshButton=document.getElementById('edit-video-evidence-refresh');
  const status=document.getElementById('edit-video-evidence-status');
  const list=document.getElementById('edit-video-evidence-list');
  if(!refreshButton||!status||!list)return null;
  let request=0,loading=false;

  function jumpButton(label,sourceSha,sourceTime){
    const button=el('button',label);button.type='button';
    const edl=getEdl(),sources=edl?.sources||{};
    const sourceId=Object.keys(sources).find(id=>sources[id]?.sha256===sourceSha);
    const clip=sourceId?(edl.cuts||[]).find(item=>item.source_id===sourceId&&Number.isFinite(item.in_seconds)&&Number.isFinite(item.out_seconds)&&sourceTime>=item.in_seconds&&sourceTime<=item.out_seconds):null;
    let target=null;
    if(clip)try{target=sourceToTimeline(edl,clip,'video',sourceTime);}catch{/* source is no longer mappable */}
    if(!Number.isFinite(target)){
      button.disabled=true;button.title='No hay un clip de esta fuente exacta en el montaje abierto.';
    }else button.addEventListener('click',()=>jump(target));
    return button;
  }

  function render(item){
    const card=el('article');card.className='video-evidence-card';card.dataset.evidenceId=item.id;
    const heading=el('h3',`Muestreo ${time(item.requested_range?.[0])}–${time(item.requested_range?.[1])} · ${item.frame_count} fotogramas`);
    const meta=el('p',`Fuente SHA-256 ${item.source_sha256.slice(0,12)}… · reloj PTS de fuente · cobertura parcial`);
    card.append(heading,meta);
    if(item.contact_sheet_url){const figure=el('figure'),image=document.createElement('img');image.src=item.contact_sheet_url;image.alt='Hoja de contacto local de fotogramas muestreados; no representa el vídeo completo';image.loading='lazy';image.referrerPolicy='no-referrer';figure.append(image,el('figcaption',`Hoja verificada · SHA-256 ${item.contact_sheet_sha256.slice(0,12)}…`));card.append(figure);}
    const frameList=el('div');frameList.className='video-evidence-pts';
    for(const frame of item.frames||[])frameList.append(jumpButton(`Ir al PTS ${time(frame.pts_seconds)} de la fuente`,item.source_sha256,frame.pts_seconds));
    card.append(frameList);
    const transcript=item.transcript||{},words=transcript.words||[];
    if(words.length){const details=el('details'),summary=el('summary',`Transcripción guardada · ${transcript.word_count} palabras · ASR en esta consulta: no ejecutado`),ordered=el('ol');
      for(const word of words){const row=el('li'),button=jumpButton(`${word.text} · ${time(word.start_seconds)}–${time(word.end_seconds)}`,item.source_sha256,word.start_seconds);row.append(button);ordered.append(row);}
      details.append(summary,el('p',`Procedencia declarada: ${transcript.status}; cobertura ${transcript.coverage}.`));
      const provenance=transcript.provenance||{};const fields=Object.entries(provenance).map(([key,value])=>`${key}: ${value}`);
      if(transcript.transcript_sha256)fields.push(`transcript_sha256: ${transcript.transcript_sha256}`);
      if(fields.length)details.append(el('p',fields.join(' · ')));
      details.append(ordered);if(transcript.truncated)details.append(el('p','Lista parcial: hay más palabras guardadas que las mostradas.'));card.append(details);
    }else card.append(el('p','Este recibo no incluye palabras temporizadas guardadas.'));
    card.append(el('p',item.gaps||'Las imágenes muestreadas no evalúan movimiento ni audio.'));
    return card;
  }

  async function load(){
    const project=getProject();
    if(!project){status.textContent='Abre un proyecto editable para consultar sus recibos guardados.';return;}
    if(loading)return;
    loading=true;const sequence=++request;refreshButton.disabled=true;status.textContent='Leyendo solo recibos guardados del proyecto…';list.replaceChildren();
    try{
      const response=await fetch(`/api/studio/editor/${encodeURIComponent(project)}/video-evidence`,{cache:'no-store',headers:{Accept:'application/json'}});
      if(!response.ok)throw new Error(`HTTP ${response.status}`);
      const value=await response.json();
      if(sequence!==request||project!==getProject())return;
      if(value.contract!=='local-video-evidence-gallery-v1'||value.read_only!==true||value.asr_executed!==false)throw new Error('Contrato de lectura no verificable');
      list.replaceChildren(...(value.items||[]).map(render));
      const warning=(value.warnings||[]).length?' Algunos recibos se omitieron por falta de verificación.':'';
      status.textContent=value.items?.length?`${value.items.length} recibo(s) verificado(s). Cobertura parcial de imágenes; no se ejecutaron extracción ni ASR.${warning}`:`No hay recibos de evidencia verificables guardados en este proyecto.${warning}`;
    }catch(error){if(sequence===request)status.textContent=`No se pudo consultar la evidencia guardada (${error.message}). No se inició extracción ni ASR.`;}
    finally{if(sequence===request){loading=false;refreshButton.disabled=false;}}
  }
  function reset(){request++;loading=false;refreshButton.disabled=false;list.replaceChildren();status.textContent='Solo se consulta al pulsar el botón.';}
  refreshButton.addEventListener('click',load);
  return {reset,refresh:load};
}
