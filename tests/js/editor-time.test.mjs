import { test } from 'node:test';
import assert from 'node:assert/strict';
import { timelineEnd,videoDuration,fitZoom,tickStep,splitAtCursor,snapTime,editPoints,trimByDelta,moveCue } from '../../backlot/ui/editor-time.js';
const first={id:'first',in_seconds:40,out_seconds:42,speed:1};
const second={id:'second',in_seconds:10.5,out_seconds:12,speed:1};
const edl={output:{fps:24},cuts:[first,second],audio_tracks:[],cues:[]};
test('fit a 3.5 second montage without the former 160 px/s ceiling',()=>{
  assert.equal(videoDuration(edl),3.5);
  for(const width of [1900,3420]){
    const scale=fitZoom(edl,width);assert.ok(scale>160);
    assert.equal(scale*3.5+50,width);
    assert.ok(tickStep(scale,24)<1);
  }
});
test('include independent audio tails and subtitle end in fit',()=>{
  const withTail={...edl,audio_tracks:[{start_seconds:12,in_seconds:0,out_seconds:4,speed:2}],cues:[{end_seconds:15}]};
  assert.equal(timelineEnd(withTail),15);
  assert.equal(fitZoom(withTail,1550),100);
  assert.equal(videoDuration(withTail),3.5);
});
test('long timelines and an empty project have finite usable scales',()=>{
  const long={...edl,cuts:[{...first,in_seconds:0,out_seconds:7200}]};
  const scale=fitZoom(long,3440);assert.ok(scale<1&&scale>0);
  assert.ok(tickStep(scale,24)>=100);
  assert.ok(Number.isFinite(fitZoom({...edl,cuts:[]},640)));
});
test('cursor split converts montage time into source time including speed',()=>{
  assert.deepEqual(splitAtCursor(edl,second,'video',2.5),{id:'second',track:'video',at:11});
  const fast={...first,speed:2};
  assert.equal(splitAtCursor({...edl,cuts:[fast]},fast,'video',.5).at,41);
  const audio={...second,start_seconds:10,speed:2};
  assert.equal(splitAtCursor({...edl,audio_tracks:[audio]},audio,'audio',10.5).at,11.5);
});
test('reject boundaries and cuts shorter than an output frame',()=>{
  for(const t of [0,.001,2,2.5])assert.throws(()=>splitAtCursor(edl,first,'video',t));
  assert.equal(splitAtCursor(edl,first,'video',1/24).at,40+1/24);
});
test('edge trim stays inside source and leaves one output frame at any speed',()=>{
  const clip={...first,speed:2,source_id:'s'};
  const e={...edl,sources:{s:{duration:76}},cuts:[clip]};
  assert.deepEqual(trimByDelta(e,clip,'video','in',.5),{id:'first',track:'video',in_seconds:41,out_seconds:42});
  assert.equal(trimByDelta(e,clip,'video','in',100).in_seconds,42-2/24);
  assert.equal(trimByDelta(e,clip,'video','out',100).out_seconds,76);
  assert.equal(trimByDelta(e,clip,'video','out',-100).out_seconds,40+2/24);
  assert.throws(()=>trimByDelta(e,clip,'audio','in',.5));
});
test('snap uses a pixel threshold and can be explicitly disabled',()=>{
  assert.equal(snapTime(1.96,[1,2,3],100,true),2);
  assert.equal(snapTime(1.8,[1,2,3],100,true),1.8);
  assert.equal(snapTime(1.96,[1,2,3],100,false),1.96);
  assert.ok(editPoints({...edl,audio_tracks:[],cues:[{start_seconds:.75,end_seconds:1.75}]},1).includes(.75));
});
test('moving a cue preserves text and length, clamps to actual video output',()=>{
  const cue={start_seconds:.75,end_seconds:1.75,text:'Line one\nLine two'};
  assert.deepEqual(moveCue(edl,cue,-10),{start_seconds:0,end_seconds:1,text:cue.text});
  assert.deepEqual(moveCue(edl,cue,100),{start_seconds:2.5,end_seconds:3.5,text:cue.text});
});
