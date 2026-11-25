import {runFormRequest} from './studio-form-request.js';

// These are local metadata forms, not inference endpoints. Other calls keep their budgets.
export function initializeProductionForms({root=document,api,bootstrap,select,notice,timeoutMs=30000}){
  const create=root.querySelector('#create'),settings=root.querySelector('#settings');
  create.onsubmit=event=>{
    event.preventDefault();const f=event.target;
    return runFormRequest(f,async()=>{
      const query=new URLSearchParams(location.search);
      const research=query.has('channel_id')&&query.has('snapshot_id')&&query.has('idea_id')?
        {channel_id:query.get('channel_id'),snapshot_id:query.get('snapshot_id'),idea_id:query.get('idea_id')}:null;
      const performance=f.elements.namedItem('performance_import_id').value.trim();
      const result=await api('projects',{title:f.elements.namedItem('title').value,brief:f.brief.value,
        pipeline:f.pipeline.value,language:f.language.value,reference:f.reference.value,automatic:f.automatic.checked,
        ...(research?{research_idea:research}:{}),...(performance?{performance_import_id:performance}:{})},{timeoutMs});
      if(typeof result?.project_id!=='string'||!result.project_id){
        throw Error('Studio respondió, pero falta el identificador del proyecto. Consulta Proyectos antes de repetir la creación.');
      }
      try{await bootstrap();await select(result.project_id);}
      catch(error){throw Error('Proyecto creado ('+result.project_id+'). Falló la actualización de la vista: '+error.message+' No repitas la creación; consulta Proyectos.');}
      notice('Proyecto creado. Inicia los agentes cuando el modelo local esté configurado.');
    },error=>notice(error.message));
  };
  settings.onsubmit=event=>{
    event.preventDefault();const f=event.target;
    return runFormRequest(f,async()=>{
      await api('settings',{yt_dlp_path:f.yt_dlp_path.value,deno_path:f.deno_path.value,
        ffmpeg_path:f.ffmpeg_path.value,ffprobe_path:f.ffprobe_path.value,ollama_url:f.ollama_url.value,
        comfyui_url:f.comfyui_url.value,model:f.model.value,
        resource_roots:f.roots.value.split('\n').map(line=>line.trim()).filter(Boolean)},{timeoutMs});
      notice('Configuración guardada.');
    },error=>notice(error.message));
  };
}
