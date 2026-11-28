import { test } from 'node:test';
import assert from 'node:assert/strict';
import {makePeaks,paintPeaks,signalLevel} from '../../backlot/ui/editor-waveform.js';
test('peaks retain signed extremes of decoded samples and partial last block',()=>{
  const p=makePeaks(new Float32Array([-.5,.25,.75,-1,.1]),2,2);
  assert.equal(p.duration,2.5);assert.deepEqual(Array.from(p.low).slice(0,2),[-.5,-1]);
  assert.deepEqual(Array.from(p.high).slice(0,2),[.25,.75]);assert.equal(p.low.length,3);
});
test('drawing a source interval excludes samples outside the actual trim',()=>{
  const p=makePeaks(new Float32Array([-1,1,.25,-.5]),1,1),lines=[];
  const context={clearRect(){},beginPath(){},moveTo(x,y){lines.push([x,y]);},lineTo(x,y){lines.push([x,y]);},stroke(){}};
  paintPeaks({width:2,height:100,getContext(){return context;}},p,2,4);
  assert.deepEqual(lines,[[0,50],[0,62.5],[1,25],[1,50]]);
});
test('meter reports real RMS, sample peak and silence floor without claiming LUFS',()=>{
  const value=signalLevel(new Float32Array([-1,1,0,0]));
  assert.equal(value.peak,1);assert.equal(value.rms,Math.sqrt(.5));assert.ok(Math.abs(value.dbfs+3.0102999566)<1e-8);
  assert.equal(signalLevel(new Float32Array(10)).dbfs,-96);
});
