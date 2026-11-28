// Shared proposal/command API only. Never analyze audio or infer silence from words.
export function appendSilenceReview({parent,dataset,getEdl,getProject,getRevision,inspectWords,loadProposal,run,reviewSource}){
  const make=(tag,text='')=>{const el=document.createElement(tag);el.textContent=text;return el;};
  const details=make('details'),summary=make('summary','Revisar propuestas de silencio');details.append(summary);
  const note=make('p','Importa intervalos de fuente existentes. No inicia análisis ni ASR. Los datos sintéticos se identifican como tales.');
  const file=make('input');file.type='file';file.accept='.json,application/json';const fileLabel=make('label','JSON de análisis existente ');fileLabel.append(file);
  const raw=make('textarea');raw.rows=4;raw.setAttribute('aria-label','Análisis de silencios JSON');
  const fields={};for(const [name,label,value] of [['padding_seconds','Margen de silencio (s)',.1],['word_padding_seconds','Protección de palabras (s)',.08],['min_cut_seconds','Corte mínimo final (s)',.1]]){
    const input=make('input');input.type='number';input.min='0';input.max=name==='min_cut_seconds'?'10':'2';input.step='.001';input.value=value;input.setAttribute('aria-label',label);fields[name]=input;const row=make('label',label+' ');row.append(input);details.append(row);
  }
  const prepare=make('button','Preparar propuesta sin modificar el montaje');prepare.type='button';
  const box=make('div');box.setAttribute('aria-live','polite');let busy=false;
  file.onchange=async()=>{try{const f=file.files[0];if(!f)return;if(f.size>120000)throw Error('JSON superior a120KB');raw.value=await f.text();}catch(e){box.textContent=e.message;}};
  prepare.onclick=async()=>{
    if(busy)return;busy=true;prepare.disabled=true;const pid=getProject(),revision=getRevision();
    try{
      const parsed=JSON.parse(raw.value),analysis=parsed.analysis||parsed;
      const words=await inspectWords(dataset.id);
      if(pid!==getProject()||revision!==getRevision()||!box.isConnected)throw Error('Cambió el montaje; vuelve a preparar la propuesta.');
      const proposal={revision,set_id:dataset.id,input_edl_sha256:words.input_edl_sha256,word_data_sha256:words.word_data_sha256,analysis};
      for(const [name,input] of Object.entries(fields))proposal[name]=Number(input.value);
      const report=await loadProposal(proposal);
      if(pid!==getProject()||revision!==getRevision()||!box.isConnected)return;
      box.replaceChildren(make('p',`${report.candidates.length} candidatos · revisión ${report.revision} · ${report.analysis_provenance.evidence}. No aplicados.`));
      for(const text of [...report.blockers,...report.warnings])box.append(make('p',text));
      if(!report.ready_for_review)return;
      if(report.candidates.length>100){box.append(make('p','Más de100candidatos: acota el análisis o revisa mediante API; aplicación deshabilitada en esta vista.'));return;}
      const checks=[];
      for(const candidate of report.candidates){
        const row=make('div'),check=make('input');check.type='checkbox';const label=make('label',`${candidate.timeline.start_seconds.toFixed(3)}–${candidate.timeline.end_seconds.toFixed(3)} s · ${candidate.frames[1]-candidate.frames[0]} fotogramas `);label.append(check);row.append(label);checks.push([candidate,check]);
        for(const [text,at] of [['Ver inicio en fuente',candidate.source.start_seconds],['Ver final en fuente',candidate.source.end_seconds]]){const button=make('button',text);button.type='button';button.onclick=()=>reviewSource(candidate.source_id,{in_seconds:at,speed:1});row.append(button);}box.append(row);
      }
      const audio=[];for(const track of getEdl().audio_tracks){const check=make('input');check.type='checkbox';const label=make('label','Revisé el audio independiente '+track.id+' (solo si falta cobertura ASR) ');label.append(check);box.append(label);audio.push([track.id,check]);}
      const reviewed=make('input');reviewed.type='checkbox';const label=make('label','Revisé palabras, límites y pistas de los candidatos seleccionados ');label.append(reviewed);
      const apply=make('button','Aplicar silencios seleccionados');apply.type='button';apply.disabled=true;
      const update=()=>{apply.disabled=busy||!reviewed.checked||!checks.some(([,c])=>c.checked);};reviewed.onchange=update;checks.forEach(([,c])=>{c.onchange=update;});
      apply.onclick=async()=>{
        if(busy)return;busy=true;apply.disabled=true;prepare.disabled=true;
        try{
          if(pid!==getProject()||revision!==getRevision())throw Error('Propuesta obsoleta; prepara de nuevo.');
          await run('silence_apply',{proposal,proposal_sha256:report.proposal_sha256,selected_ids:checks.filter(([,c])=>c.checked).map(([c])=>c.id),reviewed:reviewed.checked,reviewed_audio_ids:audio.filter(([,c])=>c.checked).map(([id])=>id)});
          box.replaceChildren(make('p','Cortes aplicados al proyecto compartido. Deshacer recupera todas las pistas. Comprueba la reproducción antes de exportar.'));
        }catch(e){box.append(make('p',e.message));}
        finally{busy=false;prepare.disabled=false;update();}
      };
      box.append(label,apply);busy=false;update();
    }catch(e){if(pid===getProject())box.textContent=e.message;}
    finally{busy=false;prepare.disabled=false;}
  };
  details.append(note,fileLabel,raw,prepare,box);parent.append(details);
}
