// Forms persist only through the same revisioned commands as the agent.
import {videoDuration} from './editor-time.js';
export function initializeEffectsUI({q,getEdl,getProject,getSelection,run,has,cursor}){
  let transformKey=null,titleKey=null,outputKey=null,mixKey=null;
  const defaults={fit:'pad',rotation:0,zoom:1,focus_x:.5,focus_y:.5,flip_h:false,flip_v:false};
  const values=(form,data)=>{for(const [key,value] of Object.entries(data)){const field=form.elements[key];if(field)field.type==='checkbox'?field.checked=Boolean(value):field.value=value;}};
  const numeric=(form,key)=>Number(form.elements[key].value);
  function syncCrop(){const f=q('edit-transform-form');for(const key of ['zoom','focus_x','focus_y'])f.elements[key].disabled=f.elements.fit.value!=='crop';}
  function drawSelection(){
    let item;try{item=getSelection();}catch{/* no clip */}
    const enabled=has('transform')&&item?.track==='video'&&item.clip.kind!=='gap';q('edit-transform-panel').hidden=!enabled;
    const form=q('edit-transform-form');form.querySelector('fieldset').disabled=!enabled||Boolean(item?.clip.locked);
    const key=JSON.stringify([getProject(),item?.id,item?.clip.transform,item?.clip.locked]);
    if(key!==transformKey){values(form,{...defaults,...(item?.clip.transform||{})});transformKey=key;syncCrop();}
  }
  function drawTitle(force=false){
    const titles=getEdl().titles||[],id=q('edit-title-select').value,title=titles.find(t=>t.id===id),end=duration();
    const key=JSON.stringify([getProject(),title||null,end]);
    if(force||key!==titleKey){values(q('edit-title-form'),title||{text:'',start_seconds:Math.min(cursor(),Math.max(0,end-.001)),end_seconds:Math.min(end,cursor()+2),size:64,position:'center'});titleKey=key;}
    q('edit-title-remove').disabled=!title;q('edit-title-form').querySelector('button[type=submit]').disabled=end<=0;
  }
  function duration(){return videoDuration(getEdl());}
  function draw(){
    drawSelection();q('edit-title-panel').hidden=!has('titles');q('edit-output-custom-panel').hidden=!has('output_custom');q('edit-mix-panel').hidden=!has('audio_mix');
    const selected=q('edit-title-select').value;
    q('edit-title-select').replaceChildren(new Option('Nuevo título',''),...(getEdl().titles||[]).map(t=>new Option(t.start_seconds.toFixed(3)+' s · '+t.text.slice(0,50),t.id)));
    q('edit-title-select').value=selected;drawTitle();
    const out=getEdl().output,key=JSON.stringify([getProject(),out]);
    if(key!==outputKey){const sizes={'16:9':[1920,1080],'9:16':[1080,1920],'1:1':[1080,1080],'4:5':[1080,1350]},[width,height]=out.ratio==='custom'?[out.width,out.height]:sizes[out.ratio];values(q('edit-output-custom-form'),{width,height,fps:out.fps,platform:out.platform||'local',preset_name:out.preset_name||''});outputKey=key;}
    const mix=getEdl().audio_mix||{},mk=JSON.stringify([getProject(),mix]);if(mk!==mixKey){values(q('edit-mix-form'),{gain:1,normalize:false,target_lufs:-16,...mix});mixKey=mk;}
  }
  q('edit-transform-form').elements.fit.onchange=()=>{const f=q('edit-transform-form');if(f.elements.fit.value==='pad')values(f,{zoom:1,focus_x:.5,focus_y:.5});syncCrop();};
  q('edit-transform-form').onsubmit=event=>{event.preventDefault();const f=event.target,item=getSelection(),data={id:item.id,fit:f.elements.fit.value,rotation:numeric(f,'rotation'),flip_h:f.elements.flip_h.checked,flip_v:f.elements.flip_v.checked};for(const k of ['zoom','focus_x','focus_y'])data[k]=numeric(f,k);run('transform',data);};
  q('edit-transform-reset').onclick=()=>run('transform',{id:getSelection().id,...defaults});
  q('edit-title-select').onchange=()=>drawTitle(true);
  q('edit-title-cursor').onclick=()=>values(q('edit-title-form'),{start_seconds:Math.min(cursor(),Math.max(0,duration()-.001)),end_seconds:Math.min(duration(),cursor()+2)});
  q('edit-title-form').onsubmit=async event=>{event.preventDefault();const f=event.target,id=q('edit-title-select').value,old=new Set((getEdl().titles||[]).map(t=>t.id)),data={text:f.elements.text.value,position:f.elements.position.value};for(const k of ['start_seconds','end_seconds','size'])data[k]=numeric(f,k);if(id)data.id=id;await run(id?'title_update':'title_add',data);if(!id){const title=(getEdl().titles||[]).find(t=>!old.has(t.id));if(title){q('edit-title-select').value=title.id;drawTitle(true);}}};
  q('edit-title-remove').onclick=()=>run('title_remove',{id:q('edit-title-select').value});
  q('edit-output-custom-form').onsubmit=event=>{event.preventDefault();const f=event.target;run('output_custom',{width:numeric(f,'width'),height:numeric(f,'height'),fps:numeric(f,'fps'),platform:f.elements.platform.value,preset_name:f.elements.preset_name.value});};
  q('edit-mix-form').onsubmit=event=>{event.preventDefault();const f=event.target;run('audio_mix',{normalize:f.elements.normalize.checked,target_lufs:numeric(f,'target_lufs'),gain:numeric(f,'gain')});};
  return {draw,drawSelection,selectTitle(id){q('edit-title-panel').open=true;q('edit-title-select').value=id;drawTitle(true);q('edit-title-form').elements.text.focus();},reset(){transformKey=titleKey=outputKey=mixKey=null;}};
}
