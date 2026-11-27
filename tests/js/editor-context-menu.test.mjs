import { test } from 'node:test';
import assert from 'node:assert/strict';
import { clampMenuPosition,contextMenuItems,describeEditorContext,initializeEditorContextMenu } from '../../backlot/ui/editor-context-menu.js';

class Element {
  constructor(){this.children=[];this.attributes={};this.dataset={};this.style={};this.listeners={};this.disabled=false;this.isConnected=true;this.parent=null;this.textContent='';}
  setAttribute(k,v){this.attributes[k]=v;}
  append(child){child.parent=this;this.children.push(child);}
  remove(){if(this.parent)this.parent.children=this.parent.children.filter(x=>x!==this);this.isConnected=false;}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
  dispatch(type,event={}){event.type=type;event.target??=this;event.preventDefault??=()=>{event.defaultPrevented=true;};for(const fn of this.listeners[type]||[])fn(event);}
  closest(selector){return selector==='[data-editor-context]'&&this.dataset.editorContext?this:null;}
  querySelectorAll(selector){return selector==='[role="menuitem"]'?this.children.filter(x=>x.attributes.role==='menuitem'):[];}
  contains(node){for(let item=node;item;item=item.parent)if(item===this)return true;return false;}
  focus(){globalThis.document.activeElement=this;}
  getBoundingClientRect(){return {left:0,bottom:0,width:200,height:this.className==='editor-context-menu'?this.children.length*32:24};}
}

function fixture(){
  const root=new Element(),documentListeners={};
  globalThis.document={activeElement:null,createElement:()=>new Element(),addEventListener(type,fn){(documentListeners[type]??=[]).push(fn);}};
  globalThis.window={innerWidth:1000,innerHeight:700};
  const activated=[],prepared=[];
  const ui=initializeEditorContextMenu({root,describe:target=>target.dataset.editorContext?({type:target.dataset.editorContext,track:target.dataset.track||'video'}):null,
    prepare:ctx=>prepared.push(ctx.type),items:contextMenuItems,state:()=>({canSplit:false,splitReason:'El cursor está fuera del clip.',canMute:true,muted:false,canRemove:true}),
    activate:(id,ctx)=>activated.push([id,ctx.type])});
  return {root,documentListeners,activated,prepared,ui};
}

test('context menu exposes only contextual operations and disables invalid commands with a reason',()=>{
  const audio=contextMenuItems({type:'clip',track:'audio'},{canSplit:false,splitReason:'Fuera del clip',canMute:true,muted:false,canRemove:true,canDuplicate:true,selectedCount:2});
  assert.deepEqual(audio.map(x=>x.id),['properties','split-cursor','mute','duplicate','remove-audio']);
  assert.equal(audio[1].enabled,false);assert.equal(audio[1].reason,'Fuera del clip');
  assert.match(audio[3].label,/\(2\)/);
  const locked=contextMenuItems({type:'clip',track:'video'},{canEdit:false,editReason:'La pista está bloqueada.',canSplit:false,splitReason:'Bloqueada',canRemove:false,canKeepGap:false,keepGapReason:'Bloqueada'});
  assert.equal(locked[0].enabled,false);assert.equal(locked[0].reason,'La pista está bloqueada.');
  const video=contextMenuItems({type:'clip',track:'video'},{canSplit:true,canDuplicate:false,canKeepGap:true,canRippleDelete:false,rippleReason:'Bloqueado'});
  assert.deepEqual(video.map(x=>x.id),['properties','split-cursor','keep-gap','ripple-delete']);
  assert.equal(video.at(-1).enabled,false);assert.equal(video.at(-1).reason,'Bloqueado');
  assert.deepEqual(contextMenuItems({type:'cue'}).map(x=>x.id),['edit-cue','seek-cue']);
  assert.deepEqual(contextMenuItems({type:'source'}).map(x=>x.id),['view-source','add-source']);
  assert.deepEqual(contextMenuItems({type:'library'}).map(x=>x.id),['import-media']);
  const monitor=contextMenuItems({type:'monitor'},{playable:false,hasProject:false});
  assert.deepEqual(monitor.map(x=>x.id),['toggle-play','prepare-preview']);assert.ok(monitor.every(x=>!x.enabled&&x.reason));
});

test('right-click opens without editing, arrows navigate, Escape restores focus and actions run only on activation',()=>{
  const f=fixture(),clip=new Element();clip.dataset.editorContext='clip';clip.dataset.track='audio';
  const event={target:clip,clientX:990,clientY:690};f.root.dispatch('contextmenu',event);
  assert.equal(event.defaultPrevented,true);assert.equal(f.ui.isOpen(),true);assert.deepEqual(f.activated,[]);
  assert.deepEqual(f.prepared,['clip']);
  const menu=f.root.children[0];assert.equal(menu.attributes.role,'menu');assert.equal(menu.style.left,'792px');assert.equal(menu.style.top,'564px');
  assert.equal(document.activeElement.textContent,'Propiedades del clip');
  menu.dispatch('keydown',{target:menu.children[0],key:'ArrowDown'});assert.equal(document.activeElement.textContent,'Silenciar audio');
  menu.dispatch('keydown',{target:menu.children[1],key:'Escape'});assert.equal(f.ui.isOpen(),false);assert.equal(document.activeElement,clip);
  f.root.dispatch('contextmenu',{target:clip,clientX:30,clientY:40});
  f.root.children[0].children[2].dispatch('click');
  assert.deepEqual(f.activated,[['mute','clip']]);assert.equal(f.ui.isOpen(),false);
});

test('Shift+F10 uses the focused editor item and outside pointer closes without capturing unrelated context menus',()=>{
  const f=fixture(),item=new Element();item.dataset.editorContext='source';item.focus();f.root.append(item);
  const key={target:f.root,key:'F10',shiftKey:true};f.root.dispatch('keydown',key);
  assert.equal(key.defaultPrevented,true);assert.equal(f.ui.isOpen(),true);
  const outside=new Element();for(const fn of f.documentListeners.pointerdown||[])fn({target:outside});
  assert.equal(f.ui.isOpen(),false);
  const unmanaged=new Element();unmanaged.closest=()=>null;const context={target:unmanaged,clientX:5,clientY:5};f.root.dispatch('contextmenu',context);
  assert.equal(context.defaultPrevented,undefined);assert.equal(f.ui.isOpen(),false);
});

test('menu coordinates remain within small and widescreen viewports',()=>{
  assert.deepEqual(clampMenuPosition(1200,1000,300,300,1280,720),{left:972,top:412});
  assert.deepEqual(clampMenuPosition(0,0,500,400,3440,1440),{left:8,top:8});
});

test('context resolution distinguishes managed editor areas from native library controls',()=>{
  const clip={dataset:{editorContext:'clip',contextId:'c1',contextTrack:'audio'}};
  const inClip={closest:selector=>selector==='[data-editor-context]'?clip:null};
  assert.deepEqual(describeEditorContext(inClip),{type:'clip',id:'c1',track:'audio',node:clip});
  const monitor={closest:selector=>selector==='#editor-monitor .editor-screen'?{}:null};
  assert.deepEqual(describeEditorContext(monitor),{type:'monitor'});
  const input={closest:selector=>selector==='.editor-library'?{}:selector==='button,input,select,textarea,a,summary,[contenteditable="true"]'?{}:null};
  assert.equal(describeEditorContext(input),null);
  const blankLibrary={closest:selector=>selector==='.editor-library'?{}:null};
  assert.deepEqual(describeEditorContext(blankLibrary),{type:'library'});
  const tracks={closest:selector=>selector==='#edit-tracks'?{}:null};
  assert.equal(describeEditorContext(tracks).type,'empty');
  assert.equal(describeEditorContext({closest:()=>null}),null);
});
