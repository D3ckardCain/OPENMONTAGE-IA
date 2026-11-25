import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cropGeometry,initializeCropPreview } from '../../backlot/ui/editor-crop-preview.js';
test('manual crop and wide fallback share the existing scale/crop geometry',()=>{
  const base={fit:'crop',zoom:1,rotation:0,focus_x:0,focus_y:.5};
  const left=cropGeometry(1920,1080,1080,1920,base),right=cropGeometry(1920,1080,1080,1920,{...base,focus_x:1});
  assert.equal(Math.abs(left.x),0);assert.equal(Math.abs(left.y),0);assert.ok(right.x<-2000);
  const padded=cropGeometry(1920,1080,1080,1920,{...base,fit:'pad'});
  assert.equal(padded.x,0);assert.ok(padded.y>600);
});
test('rotation and zoom use output geometry, not unscaled source coordinates',()=>{
  const rotated=cropGeometry(1920,1080,1080,1920,{fit:'crop',zoom:1,rotation:90,focus_x:.5,focus_y:.5});
  assert.equal(rotated.rw,1080);assert.equal(rotated.rh,1920);assert.equal(rotated.scale,1);
  const zoom=cropGeometry(1920,1080,1920,1080,{fit:'crop',zoom:2,rotation:0,focus_x:.5,focus_y:.5});
  assert.equal(zoom.scale,2);assert.equal(zoom.x,-960);assert.equal(zoom.y,-540);
});
test('invalid focus/zoom is an error, not silently accepted framing',()=>{
  for(const changed of [{zoom:5},{focus_x:NaN},{focus_y:-1},{rotation:45}])
    assert.throws(()=>cropGeometry(1920,1080,1080,1920,{fit:'crop',zoom:1,rotation:0,focus_x:.5,focus_y:.5,...changed}),/límites/);
});
test('real preview handlers seek selected source and redraw draft focus, stopping on selection change (synthetic DOM)',()=>{
  const calls=[],handlers={};
  const video={controls:false,readyState:2,videoWidth:1920,videoHeight:1080,currentTime:0,paused:true,
    setAttribute(){},addEventListener(name,fn){handlers[name]=fn;},pause(){this.paused=true;},removeAttribute(){delete this.src;},load(){}};
  const context=Object.fromEntries(['fillRect','save','restore','scale','rotate','drawImage','translate'].map(name=>[name,(...args)=>calls.push([name,...args])]));
  const canvas={hidden:true,getContext:()=>context},form={elements:Object.fromEntries(Object.entries({fit:'crop',zoom:1,rotation:0,focus_x:.5,focus_y:.5,flip_h:false,flip_v:false}).map(([name,value])=>[name,{value,checked:value===true}])),addEventListener(name,fn){this[name]=fn;}};
  const nodes={'edit-transform-form':form,'edit-crop-canvas':canvas,'edit-crop-message':{},'edit-crop-source':{append(){}},'edit-crop-open':{}};
  globalThis.document={createElement:()=>video};globalThis.cancelAnimationFrame=()=>{};globalThis.requestAnimationFrame=()=>1;
  let selection={id:'clip',track:'video',clip:{source_id:'s',in_seconds:2,out_seconds:5}};
  try{
    const ui=initializeCropPreview({q:id=>nodes[id],getEdl:()=>({output:{ratio:'9:16'}}),getSelection:()=>selection,sourceUrl:()=>'/api/studio/editor/test/source/s'});
    nodes['edit-crop-open'].onclick();assert.equal(video.src,'/api/studio/editor/test/source/s');
    video.onloadedmetadata();assert.equal(video.currentTime,2);handlers.seeked();
    assert.equal(canvas.hidden,false);assert.ok(calls.some(([name])=>name==='drawImage'));
    const before=calls.filter(([name])=>name==='translate').at(-1);
    form.elements.focus_x.value=.9;form.input();
    assert.notDeepEqual(calls.filter(([name])=>name==='translate').at(-1),before);
    assert.match(nodes['edit-crop-message'].textContent,/borrador/);
    selection=null;ui.selectionChanged();assert.equal(canvas.hidden,true);assert.equal(video.src,undefined);
  }finally{delete globalThis.document;delete globalThis.cancelAnimationFrame;delete globalThis.requestAnimationFrame;}
});
