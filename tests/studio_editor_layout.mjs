import assert from 'node:assert/strict';
import { editorPanelBudget } from '../backlot/ui/editor-layout.js';

for (const [viewport, gridHeight] of [[1920, 930], [1280, 570]]) {
  for (const workspace of ['video', 'audio', 'subtitles']) {
    const budget = editorPanelBudget(gridHeight, 3, workspace);
    assert.ok(budget.minTracks >= 0, `${viewport}px ${workspace}: timeline has a non-negative minimum`);
    assert.ok(budget.maxTracks + budget.minTop + 10 <= gridHeight + 1,
      `${viewport}px ${workspace}: upper workspace, separator, and timeline fit the editor grid`);
    assert.ok(budget.defaultTrackShare >= .44 && budget.defaultTrackShare <= .47);
  }
}

const wideVideo = editorPanelBudget(930, 3, 'video');
const wideAudio = editorPanelBudget(930, 3, 'audio');
const wideSubtitles = editorPanelBudget(930, 3, 'subtitles');
assert.ok(wideVideo.minTracks >= 360, 'legacy short timeline layouts migrate to enough room for three base tracks');
assert.ok(wideAudio.minTracks > wideVideo.minTracks, 'audio workspace allocates more room to its timeline');
assert.ok(wideSubtitles.minTracks > wideVideo.minTracks, 'subtitle workspace allocates more room to cue editing');
assert.ok(wideAudio.defaultTrackShare > wideVideo.defaultTrackShare);

console.log('studio editor layout budget: 1920x1080 and 1280x720; video/audio/subtitles fit and focus budgets pass');
