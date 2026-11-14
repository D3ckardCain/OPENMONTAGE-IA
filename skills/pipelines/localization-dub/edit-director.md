# Edit Director - Localization Dub Pipeline

## When To Use

Translate the scene plan and localized asset kit into concrete timeline decisions for each language output. The goal is to preserve the source structure where possible without pretending all languages land on the same timing.

## Process

### 1. Preserve Structure By Default

Keep the original scene order and major timing unless the translated audio clearly requires extension, compression, or coverage.

### 2. Apply The Chosen Dub Mode

Per deliverable, decide where to:

- keep original picture with new subtitles,
- replace only the audio,
- use lip-sync output,
- cover mismatch with graphics or B-roll.

### 3. Keep Language Variants Organized

Separate timeline decisions by locale so versioning stays clear all the way into compose and publish.

### 4. Use Metadata For Variant Control

Recommended metadata keys:

- `locale_timeline_map`
- `timing_adjustments`
- `coverage_sections`
- `subtitle_strategy_by_locale`

### 5. Quality Gate

- language variants are explicit,
- timing changes are recorded,
- coverage decisions are deliberate,
- the original structure is only changed where necessary.

## Common Pitfalls

- Forcing every language to match source timing exactly.
- Mixing locale-specific notes into one ambiguous edit list.
- Hiding sections where the dub treatment is visually weak.


### Cultural audio evidence (required)
Carry `cultural_audio_audit` in the checkpoint artifacts. For every target locale,
review the entire source soundtrack, including incidental voices, lyrics, music,
ambience and silence. Record time ranges, evidence, language, rights and an explicit
retain/dub/replace/remove decision with a cultural rationale. Unknown or unresolved
items block completion. Use `lib.cultural_audio.validate_cultural_audio` before
completing the stage. This validator checks evidence structure, not the media itself.
For multiple locales use separate locale project runs; each audit covers one locale.
Do not assume English songs can remain merely because narration was translated.
Neutral ambience may remain when appropriate. Inspect the final mix for residual
source speech and verify replacements and rights before marking resolved.
No paid provider fallback is authorized; missing local runtime blocks the stage.
