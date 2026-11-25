// Local form ownership only; does not retry, reset values or disable the workspace.
const active=new WeakSet();
export async function runFormRequest(form,action,onError){
  if(active.has(form))return {ignored:true};
  active.add(form);
  const focus=document.activeElement,busy=form.getAttribute('aria-busy');
  const buttons=[...form.querySelectorAll('button:not([type]),button[type=submit],input[type=submit]')].map(button=>[button,button.disabled]);
  form.setAttribute('aria-busy','true');for(const [button]of buttons)button.disabled=true;
  let failed=false;
  try{return await action();}
  catch(error){failed=true;onError(error);return {failed:true};}
  finally{
    for(const [button,disabled]of buttons)if(button.isConnected)button.disabled=disabled;
    if(busy===null)form.removeAttribute('aria-busy');else form.setAttribute('aria-busy',busy);
    active.delete(form);
    if(failed&&focus?.isConnected&&form.contains(focus)&&
      (document.activeElement===document.body||form.contains(document.activeElement)))focus.focus({preventScroll:true});
  }
}
