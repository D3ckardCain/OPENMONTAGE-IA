// Preview the existing FFmpeg static transform; no tracking/model invocation.
export function cropGeometry(sw,sh,ow,oh,values){
  if(![sw,sh,ow,oh].every(n=>Number.isFinite(n)&&n>0)||!['crop','pad'].includes(values.fit)||
    ![0,90,180,270].includes(Number(values.rotation))||!Number.isFinite(Number(values.zoom))||Number(values.zoom)<1||Number(values.zoom)>4||
    !['focus_x','focus_y'].every(k=>Number.isFinite(Number(values[k]))&&Number(values[k])>=0&&Number(values[k])<=1))throw Error('Encuadre fuera de límites; corrige foco/zoom antes de revisar.');
  const rotation=Number(values.rotation)||0;
  const rw=rotation===90||rotation===270?sh:sw,rh=rotation===90||rotation===270?sw:sh;
  const zoom=values.fit==='crop'?Number(values.zoom):1;
  const targetW=Math.max(ow,Math.round(ow*zoom/2)*2),targetH=Math.max(oh,Math.round(oh*zoom/2)*2);
  const scale=values.fit==='crop'?Math.max(targetW/rw,targetH/rh):Math.min(ow/rw,oh/rh);
  const width=rw*scale,height=rh*scale;
  return {rw,rh,scale,x:values.fit==='crop'?-(width-ow)*Number(values.focus_x):(ow-width)/2,
    y:values.fit==='crop'?-(height-oh)*Number(values.focus_y):(oh-height)/2};
}
export function initializeCropPreview({q,getEdl,getSelection,sourceUrl}){
  const video=document.createElement('video');video.controls=true;video.preload='metadata';video.muted=true;
  video.setAttribute('aria-label','Fuente para revisar encuadre, sin audio de mezcla');q('edit-crop-source').append(video);
  const form=q('edit-transform-form'),canvas=q('edit-crop-canvas'),message=q('edit-crop-message');
  let identity=null,frame=null,generation=0;
  function stop(){generation++;cancelAnimationFrame(frame);video.pause();video.removeAttribute('src');video.load();identity=null;canvas.hidden=true;}
  function draw(){
    if(!identity||video.readyState<2)return;
    let item;try{item=getSelection();}catch{stop();return;}
    if(!item||item.id!==identity.id||item.clip.source_id!==identity.source_id){stop();return;}
    if(video.currentTime>=item.clip.out_seconds)video.pause();
    const values=Object.fromEntries(['fit','rotation','zoom','focus_x','focus_y'].map(k=>[k,form.elements[k].value]));
    const output=getEdl().output,sizes={'16:9':[1920,1080],'9:16':[1080,1920],'1:1':[1080,1080],'4:5':[1080,1350]};
    const [ow,oh]=output.ratio==='custom'?[output.width,output.height]:sizes[output.ratio];
    let geometry;try{geometry=cropGeometry(video.videoWidth,video.videoHeight,ow,oh,values);}catch(error){message.textContent=error.message;return;}
    const reduction=Math.min(360/ow,360/oh);canvas.width=Math.max(1,Math.round(ow*reduction));canvas.height=Math.max(1,Math.round(oh*reduction));canvas.hidden=false;
    const ctx=canvas.getContext('2d'),factor=canvas.width/ow;
    ctx.fillStyle='#000';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.save();ctx.scale(factor,factor);
    ctx.translate(geometry.x+geometry.rw*geometry.scale/2,geometry.y+geometry.rh*geometry.scale/2);
    ctx.scale(geometry.scale,geometry.scale);ctx.scale(form.elements.flip_h.checked?-1:1,form.elements.flip_v.checked?-1:1);
    ctx.rotate(Number(values.rotation)*Math.PI/180);ctx.drawImage(video,-video.videoWidth/2,-video.videoHeight/2);ctx.restore();
    message.textContent='Previsualización local del encuadre · '+video.currentTime.toFixed(3)+'s de fuente · borrador hasta Aplicar encuadre. Sin títulos, subtítulos ni mezcla; comprueba el montaje antes de exportar.';
  }
  function loop(){draw();if(!video.paused)frame=requestAnimationFrame(loop);}
  video.addEventListener('play',()=>{if(identity&&video.currentTime>=identity.out_seconds)video.currentTime=identity.in_seconds;loop();});
  video.addEventListener('seeked',draw);video.addEventListener('loadeddata',draw);
  video.addEventListener('error',()=>{message.textContent='No se pudo decodificar la fuente en este navegador. No se ha validado el encuadre; usa la vista previa FFmpeg existente.';});
  form.addEventListener('input',draw);form.addEventListener('change',draw);
  q('edit-crop-open').onclick=()=>{
    try{
      const selected=getSelection();if(selected?.track!=='video'||selected.clip.kind==='gap')throw Error('Selecciona un clip de vídeo con fuente.');
      stop();identity={...selected.clip,id:selected.id};const token=generation;
      video.onloadedmetadata=()=>{if(token===generation)video.currentTime=identity.in_seconds;};
      video.src=sourceUrl(identity.source_id);video.load();message.textContent='Cargando fotograma de la fuente…';
    }catch(error){message.textContent=error.message;}
  };
  return {selectionChanged(){if(identity){let selected;try{selected=getSelection();}catch{}if(selected?.id!==identity.id)stop();else draw();}},reset:stop};
}
