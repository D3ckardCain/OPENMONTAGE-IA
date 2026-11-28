import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initializeCandidatesUI } from '../../backlot/ui/editor-candidates-ui.js';
class Node {
  constructor(text=''){this.textContent=text;this.children=[];this.value='';}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
}
test('candidate review exposes exact negation/context/coverage and submits explicit accept/reject/insert (synthetic DOM)',async()=>{
  const ids=['edit-candidate-form','edit-candidate-json','edit-candidate-message','edit-candidate-list','edit-candidates-panel','edit-candidate-words'];
  const nodes=new Map(ids.map(id=>[id,new Node()]));
  const fields=Object.fromEntries(['set_id','source_id','first_word','last_word','reason','coverage_start','coverage_end','time_offset'].map(id=>[id,new Node()]));
  nodes.get('edit-candidate-form').elements=fields;
  globalThis.document={createElement:()=>new Node()};globalThis.Option=class extends Node{constructor(text,value){super(text);this.value=value;}};
  const item={id:'c',status:'pending',context_confirmed:false,start_seconds:0,end_seconds:1,word_span:[0,1],text:'No cambiar.',reason:'Advertencia',context_before:'Contexto anterior.',context_after:'Consecuencia.',warnings:['Revisión necesaria']};
  const edl={sources:{s:{kind:'video',original_name:'synthetic'}},candidate_sets:[{id:'set',source_id:'s',words:[{index:0,word:'No',start:0,end:.2},{index:1,word:'cambiar.',start:.3,end:1}],candidates:[item],coverage:{processed_seconds:2,source_seconds:10,fraction:.2,word_count:2,complete:false,processed_ranges:[[0,2]],unprocessed_ranges:[[2,10]]}}]};
  const calls=[];
  try{
    const ui=initializeCandidatesUI({q:id=>nodes.get(id),getEdl:()=>edl,getProject:()=> 'test',has:()=>true,run:async(...args)=>calls.push(args),reviewSource:(...args)=>calls.push(['source',...args])});
    ui.draw();
    function flatten(node){return [node,...node.children.flatMap(flatten)];}
    const all=flatten(nodes.get('edit-candidate-list'));
    assert.ok(all.some(n=>n.textContent==='Selección exacta: No cambiar.'));
    assert.ok(all.some(n=>n.textContent.includes('2 / 10')||n.textContent.includes('2.000 / 10.000')));
    const button=text=>all.find(n=>n.textContent===text);
    const checkbox=all.find(n=>n.type==='checkbox');checkbox.checked=true;
    await button('Aceptar').onclick();await button('Rechazar').onclick();await button('Añadir aceptado al montaje').onclick();
    assert.deepEqual(calls[0],['candidate_review',{set_id:'set',id:'c',status:'accepted',context_confirmed:true}]);
    assert.equal(calls[1][1].status,'rejected');assert.equal(calls[2][0],'candidate_insert');
    await button('Escuchar/ver fuente').onclick();assert.deepEqual(calls[3],['source','s',{in_seconds:0,speed:1}]);
  }finally{delete globalThis.document;delete globalThis.Option;}
});
