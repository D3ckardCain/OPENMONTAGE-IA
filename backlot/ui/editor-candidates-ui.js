// Existing ASR JSON and revisioned EDL commands only. No model calls.
export function initializeCandidatesUI({q,getEdl,getProject,run,has,reviewSource,getRevision=()=>null,inspectWords}){
  let imported=null,key=null;
  const make=(tag,text)=>{const node=document.createElement(tag);node.textContent=text;return node;};
  const form=q('edit-candidate-form'),field=name=>form.elements[name];
  const set=()=>getEdl().candidate_sets?.find(s=>s.id===field('set_id').value);
  function words(){return imported?.word_timestamps||set()?.words||[];}
  function wordList(){
    const list=q('edit-candidate-words');list.replaceChildren();
    words().forEach((word,index)=>{
      const button=make('button',`${index} · ${word.word} [${word.start}–${word.end}s]`);button.type='button';
      button.title='Clic: inicio; Mayús + clic: final de selección';
      button.onclick=event=>{field(event.shiftKey?'last_word':'first_word').value=index;};list.append(button);
    });
  }
  q('edit-candidate-json').onchange=async event=>{
    try{
      const file=event.target.files[0];if(!file)return;
      if(file.size>450000)throw Error('JSON ASR superior a450KB; usa un fragmento con cobertura explícita.');
      const value=JSON.parse(await file.text());if(!Array.isArray(value.word_timestamps)||!value.word_timestamps.length||value.word_timestamps.length>5000)throw Error('El ASR debe incluir entre1 y5000 word_timestamps; no se inventan tiempos.');
      imported=value;field('first_word').value=0;field('last_word').value=value.word_timestamps.length-1;
      if(Number.isFinite(value.duration_seconds))field('coverage_end').value=value.duration_seconds;
      wordList();q('edit-candidate-message').textContent='Transcripción preparada, no guardada. Confirma fuente y cobertura ASR declarada; no se ha ejecutado reconocimiento.';
    }catch(error){imported=null;q('edit-candidate-message').textContent=error.message;}
  };
  field('set_id').onchange=()=>{imported=null;q('edit-candidate-json').value='';wordList();};
  form.onsubmit=async event=>{
    event.preventDefault();
    try{
      const proposal={first_word:Number(field('first_word').value),last_word:Number(field('last_word').value),reason:field('reason').value};
      if(imported){await run('candidate_import',{source_id:field('source_id').value,transcript:imported,
        processed_ranges:[[Number(field('coverage_start').value),Number(field('coverage_end').value)]],
        time_offset:Number(field('time_offset').value),proposals:[proposal]});imported=null;q('edit-candidate-json').value='';}
      else{if(!set())throw Error('Importa un JSON ASR existente o selecciona un conjunto guardado.');await run('candidate_propose',{set_id:set().id,...proposal});}
      key=null;draw();
    }catch(error){q('edit-candidate-message').textContent=error.message;}
  };
  function draw(){
    q('edit-candidates-panel').hidden=!has('clip_candidates');
    const edl=getEdl(),next=JSON.stringify([getProject(),edl.sources,edl.candidate_sets]);if(key===next)return;key=next;
    const old=field('set_id').value,oldSource=field('source_id').value;
    field('source_id').replaceChildren(...Object.entries(edl.sources).filter(([,s])=>s.kind==='video').map(([id,s])=>new Option(s.original_name||s.path,id)));
    if(edl.sources[oldSource])field('source_id').value=oldSource;
    field('set_id').replaceChildren(new Option('Nueva transcripción',''),...(edl.candidate_sets||[]).map(s=>new Option(`${s.id.slice(0,8)} · ${edl.sources[s.source_id]?.original_name||s.source_id}`,s.id)));
    field('set_id').value=edl.candidate_sets?.some(s=>s.id===old)?old:(edl.candidate_sets?.at(-1)?.id||'');
    if(!imported)wordList();
    const list=q('edit-candidate-list');list.replaceChildren();
    for(const dataset of edl.candidate_sets||[]){
      const coverage=dataset.coverage;
      list.append(make('p',`Cobertura ASR declarada: ${coverage.processed_seconds.toFixed(3)} / ${coverage.source_seconds.toFixed(3)}s (${(coverage.fraction*100).toFixed(1)}%) · ${coverage.word_count} palabras · ${coverage.complete?'completa declarada':'PARCIAL'} · no verificada independientemente`));
      list.append(make('p','Procesado declarado: '+coverage.processed_ranges.map(([a,b])=>`${a}–${b}s`).join(', ')+'. No procesado: '+(coverage.unprocessed_ranges?.map(([a,b])=>`${a}–${b}s`).join(', ')||'sin huecos declarados')+'. Selección editorial limitada a propuestas; no se revisó automáticamente toda la fuente.'));
      if(has('subtitle_words')&&inspectWords){
        const reportBox=make('div',''),button=make('button','Inspeccionar palabras en el reloj del montaje');button.type='button';
        button.onclick=async()=>{
          const pid=getProject();button.disabled=true;
          try{
            const loading=make('p','Consultando tiempos guardados, sin ASR ni cambios del montaje…');loading.setAttribute('role','status');reportBox.replaceChildren(loading);
            const report=await inspectWords(dataset.id);
            if(pid!==getProject()||!reportBox.isConnected)return;
            if(getRevision()!==null&&report.revision!==getRevision())throw Error('El montaje cambió; vuelve a consultar sus tiempos.');
            const summary=make('p',`${report.words.length} ocurrencias · ${report.excluded_word_occurrences} exclusiones · revisión ${report.revision}. Solo lectura, sin crear subtítulos.`);summary.setAttribute('role','status');reportBox.replaceChildren(summary);
            const wrap=make('div','');wrap.className='editor-word-clock';const table=make('table','');
            table.append(make('caption','Palabras guardadas: tiempos de fuente y de montaje'));
            const header=make('tr','');for(const name of ['Clip','Palabra / índice','Fuente (s)','Montaje (s)','Tiempos declarados']){const cell=make('th',name);cell.scope='col';header.append(cell);}table.append(header);
            const timingLabels={measured:'medido declarado',estimated:'estimado declarado',imputed:'imputado declarado',unknown:'origen no declarado'};
            for(const word of report.words.slice(0,100)){
              const row=make('tr','');for(const value of [word.clip_id.slice(0,8),`${word.text} / ${word.word_index}`,
                `${word.source.start_seconds.toFixed(3)}–${word.source.end_seconds.toFixed(3)}`,
                `${word.timeline.start_seconds.toFixed(3)}–${word.timeline.end_seconds.toFixed(3)}`,
                `${timingLabels[word.timing_status]||'origen no declarado'} · ${word.language||'idioma no declarado'} · ${word.speaker===null?'hablante sin declarar':'hablante declarado '+JSON.stringify(word.speaker)}`])row.append(make('td',value));table.append(row);
            }
            wrap.append(table);reportBox.append(wrap);
            if(report.words.length>100)reportBox.append(make('p','Se muestran100ocurrencias; el informe JSON de API/agente conserva todas.'));
            const reasons={zero_duration:'duración cero, sin intervalo que mostrar',partial_source_word:'palabra cortada por el límite del clip',partial_frame_quantization:'palabra cortada por la duración en fotogramas'};
            let shown=0;for(const clip of report.clips){
              for(const word of clip.excluded_words||[])if(shown++<20)reportBox.append(make('p',`Excluida: ${word.text} / ${word.word_index} · ${reasons[word.reason]||word.reason}. Revisa el límite del corte.`));
              if(clip.source_inspected&&!clip.coverage_complete_declared)reportBox.append(make('p','Cobertura ASR parcial en clip '+clip.clip_id+'; ausencia de palabras no prueba silencio.'));
            }
            for(const warning of report.warnings)reportBox.append(make('p',warning));
          }catch(error){if(pid===getProject()){const errorLine=make('p',error.message);errorLine.setAttribute('role','status');reportBox.replaceChildren(errorLine);}}
          finally{button.disabled=false;}
        };
        list.append(button,reportBox);
      }
      for(const item of dataset.candidates){
        const card=make('article',''),details=make('details','');details.append(make('summary',`${item.status} · ${item.start_seconds.toFixed(3)}–${item.end_seconds.toFixed(3)}s · ${item.text}`));
        details.append(make('p','Motivo: '+item.reason),make('p','Antes: '+item.context_before),make('p','Selección exacta: '+item.text),make('p','Después: '+item.context_after),make('p',item.warnings.join(' ')));
        const timed=dataset.words.slice(item.word_span[0],item.word_span[1]+1).map(w=>`${w.index}:${w.word} [${w.start}–${w.end}]`).join(' ');details.append(make('p',timed));
        const reviewed=make('input','');reviewed.type='checkbox';reviewed.checked=item.context_confirmed;const label=make('label','Revisé negaciones, antecedentes y final de la idea ');label.append(reviewed);details.append(label);
        const action=(text,fn)=>{const button=make('button',text);button.type='button';button.onclick=async()=>{try{await fn();}catch(error){q('edit-candidate-message').textContent=error.message;}};details.append(button);};
        action('Escuchar/ver fuente',()=>reviewSource(dataset.source_id,{in_seconds:item.start_seconds,speed:1}));
        action('Aceptar',()=>run('candidate_review',{set_id:dataset.id,id:item.id,status:'accepted',context_confirmed:reviewed.checked}));
        action('Rechazar',()=>run('candidate_review',{set_id:dataset.id,id:item.id,status:'rejected'}));
        action('Corregir límites con selección de palabras',()=>{if(imported||field('set_id').value!==dataset.id)throw Error('Selecciona el conjunto guardado de este candidato antes de corregir sus palabras.');return run('candidate_review',{set_id:dataset.id,id:item.id,status:'pending',first_word:Number(field('first_word').value),last_word:Number(field('last_word').value)});});
        action('Añadir aceptado al montaje',()=>run('candidate_insert',{set_id:dataset.id,id:item.id}));
        card.append(details);list.append(card);
      }
    }
  }
  return {draw,reset(){imported=null;key=null;q('edit-candidate-json').value='';}};
}
