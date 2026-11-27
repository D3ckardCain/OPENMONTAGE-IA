// Viewport-only preferences. This module never edits the media project.
export function editorPanelBudget(height, rows=3, workspace='video') {
  const viewport=Math.max(1,Number(height)||1), trackRows=Math.max(3,Number(rows)||3);
  const taskExtra=workspace==='audio'?44:workspace==='subtitles'?36:0;
  const minTop=Math.min(220,Math.max(0,(viewport-8)*.36));
  const available=Math.max(0,viewport-8-minTop);
  const minTracks=Math.min(400+Math.max(0,trackRows-3)*48+taskExtra,viewport*.65,available);
  return {minTop,minTracks,maxTracks:Math.max(minTracks,available),defaultTrackShare:(workspace==='audio'||workspace==='subtitles') ? .47 : .44};
}

export function initializeEditorLayout() {
  const q=id=>document.getElementById(id), root=q('manual-editor'), grid=q('editor-grid');
  const keys={library:'edit-library-size',inspector:'edit-inspector-size',tracks:'edit-track-size'};
  const defaults={library:320,inspector:280,tracks:null}, prefs={};
  let migrate=false;try{migrate=localStorage.getItem('edit-layout-version')!=='4';}catch{/* storage is optional */}
  for(const [key,id] of Object.entries(keys)){
    let raw;try{raw=localStorage.getItem(id);}catch{/* storage is optional */}
    const n=raw===null||raw===undefined?NaN:Number(raw);
    prefs[key]=Number.isFinite(n)&&n>0?Math.min(n,10000):defaults[key];
  }
  for(const [id,cls] of [['edit-hide-library','library-hidden'],['edit-hide-inspector','inspector-hidden']]){
    try{q(id).checked=localStorage.getItem(id)==='true';}catch{/* storage is optional */}
    q(id).onchange=()=>{root.classList.toggle(cls,q(id).checked);save(id,String(q(id).checked));apply();};
    root.classList.toggle(cls,q(id).checked);
  }
  let effective={...prefs}, limits={}, drag=null, scheduled=false;
  const clamp=(n,min,max)=>Math.max(min,Math.min(max,n));
  function save(key,value){try{localStorage.setItem(key,value);}catch{/* keep in memory */}}
  function apply(){
    if(root.hidden||grid.clientWidth<=0||grid.clientHeight<=0)return;
    const showLibrary=!q('edit-hide-library').checked, showInspector=!q('edit-hide-inspector').checked;
    const minLibrary=showLibrary?(grid.clientWidth>=1000?260:160):0, minInspector=showInspector?180:0;
    const gutters=(Number(showLibrary)+Number(showInspector))*10;
    const sideBudget=Math.max(minLibrary+minInspector,grid.clientWidth-240-gutters);
    const height=grid.clientHeight, workspace=document.body.dataset.editorWorkspace||'video';
    const budget=editorPanelBudget(height,root.dataset.timelineRows||3,workspace),{minTop,minTracks,maxTracks,defaultTrackShare}=budget;
    if(migrate){
      // Pre-v4 layouts could leave the library too narrow to identify media.
      // Normalize only during migration; preserve widths saved by current layouts.
      if(prefs.library<defaults.library)prefs.library=defaults.library;
      if(prefs.tracks!==null&&(prefs.tracks<minTracks||prefs.tracks>height*.65)){
        prefs.tracks=null;try{localStorage.removeItem(keys.tracks);}catch{/* storage is optional */}
      }
      save(keys.library,String(prefs.library));save('edit-layout-version','4');migrate=false;
    }
    let library=showLibrary?Math.max(minLibrary,prefs.library):0;
    let inspector=showInspector?Math.max(minInspector,prefs.inspector):0;
    if(library+inspector>sideBudget){
      const extra=library+inspector-minLibrary-minInspector;
      const factor=extra?Math.max(0,(sideBudget-minLibrary-minInspector)/extra):0;
      library=minLibrary+(library-minLibrary)*factor;inspector=minInspector+(inspector-minInspector)*factor;
    }
    effective={library:Math.round(library),inspector:Math.round(inspector),tracks:Math.round(clamp(prefs.tracks??height*defaultTrackShare,minTracks,maxTracks))};
    limits={library:[minLibrary||160,Math.max(minLibrary||160,Math.floor(sideBudget-inspector))],inspector:[180,Math.max(180,Math.floor(sideBudget-library))],tracks:[Math.round(minTracks),Math.floor(maxTracks)]};
    for(const [key,id] of Object.entries(keys)){
      root.style.setProperty('--'+key,effective[key]+'px');
      const input=q(id);input.min=limits[key][0];input.max=limits[key][1];input.value=Math.max(limits[key][0],effective[key]);
      if(key==='library'||key==='inspector')input.disabled=key==='library'?!showLibrary:!showInspector;
      const handle=q('edit-split-'+(key==='tracks'?'timeline':key));
      handle.setAttribute('aria-valuemin',String(limits[key][0]));handle.setAttribute('aria-valuemax',String(limits[key][1]));handle.setAttribute('aria-valuenow',String(effective[key]));
    }
    q('edit-split-library').hidden=!showLibrary;q('edit-split-inspector').hidden=!showInspector;
  }
  function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;apply();});}
  function commit(key){apply();prefs[key]=effective[key];save(keys[key],String(prefs[key]));}
  q('edit-layout-reset').onclick=()=>{
    Object.assign(prefs,defaults);
    for(const key of Object.values(keys))try{localStorage.removeItem(key);}catch{/* storage is optional */}
    for(const [id,cls] of [['edit-hide-library','library-hidden'],['edit-hide-inspector','inspector-hidden']]){
      q(id).checked=false;root.classList.remove(cls);save(id,'false');
    }
    save('edit-layout-version','4');migrate=false;apply();
  };
  for(const [key,id] of Object.entries(keys))q(id).oninput=()=>{prefs[key]=Number(q(id).value);commit(key);};
  for(const key of Object.keys(keys)){
    const handle=q('edit-split-'+(key==='tracks'?'timeline':key));
    handle.addEventListener('keydown',event=>{
      if(!limits[key])return;
      const delta=event.shiftKey?64:16;let next=effective[key];
      if(event.key==='Home')next=limits[key][0];else if(event.key==='End')next=limits[key][1];
      else if(key==='tracks'&&event.key==='ArrowUp')next+=delta;
      else if(key==='tracks'&&event.key==='ArrowDown')next-=delta;
      else if(key!=='tracks'&&event.key==='ArrowRight')next+=key==='inspector'?-delta:delta;
      else if(key!=='tracks'&&event.key==='ArrowLeft')next+=key==='inspector'?delta:-delta;
      else return;
      event.preventDefault();prefs[key]=clamp(next,...limits[key]);commit(key);
    });
    handle.addEventListener('pointerdown',event=>{
      if(event.button!==0)return;event.preventDefault();apply();
      drag={key,id:event.pointerId,x:event.clientX,y:event.clientY,base:effective[key]};
      handle.setPointerCapture(event.pointerId);
      document.documentElement.classList.add('editor-resizing',key==='tracks'?'editor-resizing-rows':'editor-resizing-columns');
    });
    handle.addEventListener('pointermove',event=>{
      if(!drag||drag.key!==key||drag.id!==event.pointerId)return;
      const delta=key==='tracks'?drag.y-event.clientY:(event.clientX-drag.x)*(key==='inspector'?-1:1);
      prefs[key]=clamp(drag.base+delta,...limits[key]);apply();
    });
    const finish=()=>{if(!drag||drag.key!==key)return;commit(key);drag=null;document.documentElement.classList.remove('editor-resizing','editor-resizing-rows','editor-resizing-columns');};
    handle.addEventListener('pointerup',finish);handle.addEventListener('pointercancel',finish);handle.addEventListener('lostpointercapture',finish);
  }
  q('edit-layout-options').addEventListener('keydown',event=>{if(event.key==='Escape'){q('edit-layout-options').open=false;q('edit-layout-options').querySelector('summary').focus();}});
  new ResizeObserver(schedule).observe(grid);
  window.addEventListener('resize',schedule);window.addEventListener('studio-workspace',event=>{document.body.dataset.editorWorkspace=event.detail;schedule();});
  window.addEventListener('studio-tracks-layout',schedule);
  apply();
}
