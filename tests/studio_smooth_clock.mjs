// Run with the prepared Node runtime; no npm/npx/packages/network required.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {forwardClock,inverseClock} from '../backlot/ui/editor-smooth-clock.js';
const fixture=JSON.parse(fs.readFileSync(new URL('./fixtures/smooth_clock_vectors_v1.json',import.meta.url),'utf8'));
let max=0;
for(const r of fixture.vectors)max=Math.max(max,Math.abs(forwardClock(fixture.map,r.time)-r.forward),Math.abs(inverseClock(fixture.map,r.time)-r.inverse));
assert(max<1e-10,'Frontend/backend clock drift: '+max);
console.log(JSON.stringify({vectors:fixture.vectors.length,max_error_seconds:max}));
