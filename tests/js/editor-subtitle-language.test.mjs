import { test } from 'node:test';
import assert from 'node:assert/strict';
import { languageSelection,languageParams } from '../../backlot/ui/editor-subtitle-language.js';
test('legacy UI explicitly represents an undeclared value, never silently writes Spanish',()=>{
  assert.equal(languageSelection({}), 'legacy');
  assert.deepEqual(languageParams('legacy'),{});
});
test('declared language is preserved and unsupported backend receives no new parameter',()=>{
  assert.equal(languageSelection({language:'por'}),'por');
  assert.deepEqual(languageParams('por'),{language:'por'});
  assert.deepEqual(languageParams('und'),{language:'und'});
  assert.deepEqual(languageParams('por',false),{});
});
