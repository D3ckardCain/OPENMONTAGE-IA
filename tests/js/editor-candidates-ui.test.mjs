import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initializeCandidatesUI } from '../../backlot/ui/editor-candidates-ui.js';
class Element {
  constructor(tag='div',text=''){this.tag=tag;this.textContent=text;this.children=[];this.value='';this.type='';this.hidden=false;this.checked=false;}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=[...nodes];if(this.tag==='select')this.value=nodes[0]?.value||'';}
}
test('ASR import submits exact words/reason/coverage, failure preserves draft, source review and acceptance are explicit',async()=>{
  const ids=['edit-candidate-form','edit-candidate-json','edit-candidate-message','edit-candidate-list','edit-candidates-panel','edit-candidate-words'];
  const nodes=new Map(ids.map(id=>[id,new Element()]));
  const fields=Object.fromEntries(['set_id','source_id','first_word','last_word','reason','coverage_start','coverage_end','time_offset'].map(id=>[id,new Element(['set_id','source_id'].includes(id)?'select':'input')]));
  nodes.get('edit-candidate-form').elements=fields;
  fields.coverage_start.value=0;fields.time_offset.value=0;
  globalThis.document={createElement:tag=>new Element(tag)};
  globalThis.Option=class extends Element{constructor(text,value){super('option',text);this.value=value;}};
  const transcript={duration_seconds:3,word_timestamps:[{word:'No',start:0,end:.2},{word:'cambiar.',start:.3,end:.9}]};
  const edl={sources:{s:{kind:'video',original_name:'synthetic metadata'}},candidate_sets:[]},calls=[];let fail=true;
  try{
    const ui=initializeCandidatesUI({q:id=>nodes.get(id),getEdl:()=>edl,getProject:()=> 'test',has:()=>true,
      run:async(op,data)=>{calls.push([op,data]);if(fail)throw Error('stale revision');},reviewSource(){}});
    ui.draw();fields.reason.value='Conservar advertencia';
    await nodes.get('edit-candidate-json').onchange({target:{files:[{size:100,text:async()=>JSON.stringify(transcript)}]}});
    const wordButtons=nodes.get('edit-candidate-words').children;
    wordButtons[0].onclick({shiftKey:false});wordButtons[1].onclick({shiftKey:true});
    await nodes.get('edit-candidate-form').onsubmit({preventDefault(){}});
    assert.match(nodes.get('edit-candidate-message').textContent,/stale/);
    fail=false;await nodes.get('edit-candidate-form').onsubmit({preventDefault(){}});
    assert.equal(calls.length,2);assert.equal(calls[1][0],'candidate_import');
    assert.deepEqual(calls[1][1].transcript,transcript);
    assert.deepEqual(calls[1][1].processed_ranges,[[0,3]]);
    assert.deepEqual(calls[1][1].proposals,[{first_word:0,last_word:1,reason:'Conservar advertencia'}]);
  }finally{delete globalThis.document;delete globalThis.Option;}
});
