// Review a server-built candidate; never manufacture word timings in the browser.
export function appendSubtitleDraft({parent,dataset,getProject,getRevision,loadDraft,run}){
  const make=(tag,text)=>{const el=document.createElement(tag);el.textContent=text;return el;};
  const button=make('button','Preparar borrador de subtítulos desde palabras guardadas');button.type='button';
  const box=make('div','');box.setAttribute('aria-live','polite');parent.append(button,box);
  button.onclick=async()=>{
    const pid=getProject();button.disabled=true;
    try{
      box.replaceChildren(make('p','Preparando borrador sin ASR ni modificar subtítulos…'));
      const draft=await loadDraft(dataset.id);
      if(pid!==getProject()||!box.isConnected)return;
      if(draft.revision!==getRevision())throw Error('Cambió el montaje; prepara de nuevo el borrador.');
      box.replaceChildren(make('p',`${draft.cues.length} subtítulos candidatos · revisión ${draft.revision}. No aplicados.`));
      for(const warning of [...draft.blockers,...draft.warnings])box.append(make('p',warning));
      if(!draft.ready)return;
      const preview=make('div','');preview.className='editor-word-clock';
      for(const cue of draft.cues.slice(0,100))preview.append(make('p',`${cue.start_seconds.toFixed(3)}–${cue.end_seconds.toFixed(3)} s · ${cue.text}`));
      box.append(preview);
      if(draft.cues.length>100)box.append(make('p','Vista limitada a100; revisa el JSON completo mediante API/agente antes de confirmar.'));
      const reviewed=make('input','');reviewed.type='checkbox';const reviewLabel=make('label','Revisé texto, contexto y tiempos del borrador completo ');reviewLabel.append(reviewed);
      const replace=make('input','');replace.type='checkbox';const replaceLabel=make('label','Autorizo reemplazar los subtítulos existentes (Deshacer los recupera) ');replaceLabel.append(replace);
      const apply=make('button','Aplicar borrador revisado');apply.type='button';apply.disabled=true;reviewed.onchange=()=>{apply.disabled=!reviewed.checked;};
      apply.onclick=async()=>{
        apply.disabled=true;
        try{
          if(pid!==getProject()||draft.revision!==getRevision())throw Error('Cambió el proyecto; prepara de nuevo el borrador.');
          await run('subtitle_from_words',{set_id:dataset.id,input_edl_sha256:draft.input_edl_sha256,word_data_sha256:draft.word_data_sha256,reviewed:reviewed.checked,replace_existing:replace.checked});
          box.replaceChildren(make('p','Borrador aplicado al proyecto compartido. Puedes deshacerlo; comprueba la vista previa antes de exportar.'));
        }catch(error){box.append(make('p',error.message));apply.disabled=!reviewed.checked;}
      };
      box.append(reviewLabel,replaceLabel,apply);
    }catch(error){if(pid===getProject())box.replaceChildren(make('p',error.message));}
    finally{button.disabled=false;}
  };
}
