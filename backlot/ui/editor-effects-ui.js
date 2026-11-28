// Forms persist only through the same revisioned commands as the agent.
import {videoDuration} from './editor-time.js';
import {initializeAudioBalance} from './editor-audio-balance.js';
import {initializeAudioProcessing} from './editor-audio-processing.js';
import {initializeTrackMixer} from './editor-track-mixer.js';
import {initializeDucking} from './editor-ducking.js';
import {initializeColor} from './editor-color.js';
import {initializeColorCurves} from './editor-color-curves.js';
import {initializeSpeedRamp} from './editor-speed-ramp.js';
import {initializeSmoothSpeed} from './editor-smooth-speed.js';
export function initializeEffectsUI({q,getEdl,getProject,getSelection,run,runBalance=run,has,cursor}){
  const colorUI=initializeColor({host:q('edit-transform-panel'),getEdl,getProject,getSelection,run:runBalance,has,cursor});
  const curvesUI=initializeColorCurves({host:q('edit-transform-panel'),getProject,getSelection,run:runBalance,has});
  const speedUI=initializeSpeedRamp({host:q('edit-transform-panel'),getProject,getEdl,getSelection,run:runBalance,has,cursor});
  const smoothUI=initializeSmoothSpeed({host:q('edit-transform-panel'),getProject,getEdl,getSelection,run:runBalance,has});
  const mixerUI=initializeTrackMixer({host:q('edit-mix-panel'),getEdl,getProject,run:runBalance,has});
  const duckingUI=initializeDucking({host:q('edit-mix-panel'),getEdl,getProject,run:runBalance,has});
  const balanceUI=initializeAudioBalance({host:q('edit-mix-panel'),getEdl,getProject,getSelection,run:runBalance,has});
  const processingUI=initializeAudioProcessing({host:q('edit-mix-panel'),getEdl,getProject,getSelection,run:runBalance,has});
  const anchorLabel=document.createElement('label');anchorLabel.textContent='Ancla horizontal del componente (0–1) ';
  const anchor=document.createElement('input');anchor.name='anchor_x';anchor.type='number';anchor.min='0';anchor.max='1';anchor.step='.01';anchor.value='.5';anchorLabel.append(anchor);anchorLabel.hidden=true;q('edit-title-form').append(anchorLabel);
  let transformKey=null,titleKey=null,outputKey=null,mixKey=null;
  const defaults={fit:'pad',rotation:0,zoom:1,focus_x:.5,focus_y:.5,flip_h:false,flip_v:false};
  const values=(form,data)=>{for(const [key,value] of Object.entries(data)){const field=form.elements[key];if(field)field.type==='checkbox'?field.checked=Boolean(value):field.value=value;}};
  const numeric=(form,key)=>Number(form.elements[key].value);
  function syncCrop(){const f=q('edit-transform-form');for(const key of ['zoom','focus_x','focus_y'])f.elements[key].disabled=f.elements.fit.value!=='crop';}
  function drawSelection(){
    colorUI.draw();
    curvesUI.draw();
    speedUI.draw();
    smoothUI.draw();
    let item;try{item=getSelection();}catch{/* no clip */}
    balanceUI.draw(item);
    processingUI.draw();
    const enabled=has('transform')&&item?.track==='video'&&item.clip.kind!=='gap';q('edit-transform-panel').hidden=!enabled;
    const form=q('edit-transform-form');form.querySelector('fieldset').disabled=!enabled||Boolean(item?.clip.locked);
    const key=JSON.stringify([getProject(),item?.id,item?.clip.transform,item?.clip.locked]);
    if(key!==transformKey){values(form,{...defaults,...(item?.clip.transform||{})});transformKey=key;syncCrop();}
  }
  function drawTitle(force=false){
    const titles=getEdl().titles||[],id=q('edit-title-select').value,title=titles.find(t=>t.id===id),end=duration();
    anchorLabel.hidden=!title?.component_layout;
    const key=JSON.stringify([getProject(),title||null,end]);
    if(force||key!==titleKey){values(q('edit-title-form'),title||{text:'',start_seconds:Math.min(cursor(),Math.max(0,end-.001)),end_seconds:Math.min(end,cursor()+2),size:64,position:'center'});anchor.value=title?.component_layout?.anchor_x??.5;titleKey=key;}
    q('edit-title-remove').disabled=!title;q('edit-title-form').querySelector('button[type=submit]').disabled=end<=0;
  }
  function duration(){return videoDuration(getEdl());}
  function draw(){
    mixerUI.draw();
    duckingUI.draw();
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
  q('edit-title-form').onsubmit=async event=>{event.preventDefault();const f=event.target,id=q('edit-title-select').value,old=new Set((getEdl().titles||[]).map(t=>t.id)),data={text:f.elements.text.value,position:f.elements.position.value};for(const k of ['start_seconds','end_seconds','size'])data[k]=numeric(f,k);if(id){data.id=id;if(getEdl().titles.find(t=>t.id===id)?.component_layout)data.anchor_x=Number(anchor.value);}await run(id?'title_update':'title_add',data);if(!id){const title=(getEdl().titles||[]).find(t=>!old.has(t.id));if(title){q('edit-title-select').value=title.id;drawTitle(true);}}};
  q('edit-title-remove').onclick=()=>run('title_remove',{id:q('edit-title-select').value});
  q('edit-output-custom-form').onsubmit=event=>{event.preventDefault();const f=event.target;run('output_custom',{width:numeric(f,'width'),height:numeric(f,'height'),fps:numeric(f,'fps'),platform:f.elements.platform.value,preset_name:f.elements.preset_name.value});};
  q('edit-mix-form').onsubmit=event=>{event.preventDefault();const f=event.target;run('audio_mix',{normalize:f.elements.normalize.checked,target_lufs:numeric(f,'target_lufs'),gain:numeric(f,'gain')});};
  return {draw,drawSelection,selectTitle(id){q('edit-title-panel').open=true;q('edit-title-select').value=id;drawTitle(true);q('edit-title-form').elements.text.focus();},reset(){mixerUI.reset();duckingUI.reset();balanceUI.reset();processingUI.reset();transformKey=titleKey=outputKey=mixKey=null;}};
}
