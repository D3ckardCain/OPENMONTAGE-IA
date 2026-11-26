// Profile selection changes one shared binding; it never launches Blender.
export async function appendBlenderProfiles({app,host,api,notice,refresh}){
 if(app.id!=='blender')return;
 const text=document.createElement('p');host.append(text);
 if(app.profile_contract!==1||!Array.isArray(app.profiles)){
  text.textContent=app.profile_error||'Selector de versiones pendiente de activación manual del backend. La ruta actual se conserva.';return;
 }
 if(!app.profiles.length){text.textContent='No hay perfiles Blender registrados; se conserva la ruta manual.';return;}
 const label=document.createElement('label'),select=document.createElement('select'),save=document.createElement('button');
 label.textContent='Versión de Blender';select.dataset.blenderProfile='';save.textContent='Usar esta versión';save.type='button';save.dataset.blenderProfileSave='';
 select.add(new Option('Selecciona explícitamente una versión',''));
 for(const p of app.profiles){
  const option=new Option(p.label+' · '+p.version+(!p.file_found||!p.profile_available?' · No disponible':''),p.id);option.disabled=!p.file_found||!p.profile_available;select.add(option);
  if(p.selected)select.value=p.id;
 }
 let backendReady=false,backendMessage='Comprobando el selector de versiones; la ruta actual se conserva.';
 const show=()=>{const p=app.profiles.find(p=>p.id===select.value);save.disabled=!backendReady||!p||!p.file_found||!p.profile_available;text.textContent=!backendReady?backendMessage:p?(p.user_resources?'Preferencias y complementos aislados: '+p.user_resources:'Preferencias y complementos existentes conservados.')+' No abre Blender ni valida renders.':'Selecciona un perfil disponible; no se cambia automáticamente de versión.';};
 select.onchange=show;show();label.append(select);host.append(label,save);
 select.disabled=true;
 try{
  const contract=await api('applications/blender/profiles',undefined,{timeoutMs:4000});
  backendReady=contract.profile_contract===1&&contract.selection_supported===true;
  if(!backendReady)backendMessage='Contrato del selector incompatible; la ruta actual se conserva.';
 }catch(error){backendMessage=error.status===404?'Selector pendiente de activación manual del backend. La ruta actual se conserva.':'No se pudo verificar el selector. Comprueba conexión y estado; no se cambió la versión.';}
 select.disabled=!backendReady;show();
 save.onclick=async()=>{
  const id=select.value;save.disabled=true;select.disabled=true;
  try{const result=await api('applications/blender/profile',{profile_id:id});if(result.saved!==true||result.profile_id!==id)throw Error('El backend no confirmó el perfil solicitado; comprueba su activación.');notice('Blender: perfil '+id+' guardado para Studio y agente; no se abrió la aplicación.');await refresh();}
  catch(error){notice(error.message);}
  finally{select.disabled=false;show();}
 };
}
