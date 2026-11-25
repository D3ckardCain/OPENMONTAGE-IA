import { test } from 'node:test';
import assert from 'node:assert/strict';
import { editPoints,snapTime } from '../../backlot/ui/editor-time.js';
const base={output:{fps:24},cuts:[],audio_tracks:[],cues:[]};
test('layers use montage start and scaled duration, titles have independent intervals',()=>{
  const edl={...base,layers:[{start_seconds:5,in_seconds:40,out_seconds:46,speed:2}],titles:[{start_seconds:9,end_seconds:10.5}]};
  const before=JSON.stringify(edl),points=editPoints(edl);
  for(const boundary of [5,8,9,10.5])assert.ok(points.includes(boundary));
  assert.ok(!points.includes(40)&&!points.includes(46));
  assert.equal(JSON.stringify(edl),before);
  assert.equal(snapTime(7.97,points,100),8);
  assert.equal(snapTime(10.54,points,100),10.5);
});
test('snap threshold and disabled mode unchanged, slow and locked layers remain temporal references',()=>{
  const points=editPoints({...base,layers:[{start_seconds:3,in_seconds:1,out_seconds:3,speed:.5,locked:true}]});
  assert.ok(points.includes(7));
  assert.equal(snapTime(6.93,points,100),7);
  assert.equal(snapTime(6.9,points,100),6.9);
  assert.equal(snapTime(6.93,points,100,false),6.93);
});
test('optional arrays and invalid composition metadata do not poison snapping',()=>{
  assert.deepEqual(editPoints(base),[0,0]);
  const points=editPoints({...base,layers:[{start_seconds:1,in_seconds:0,out_seconds:4,speed:0},{start_seconds:NaN,in_seconds:0,out_seconds:3,speed:1}],titles:[{start_seconds:4,end_seconds:2},{start_seconds:0,end_seconds:Infinity}]});
  assert.deepEqual(points,[0,0]);
});
