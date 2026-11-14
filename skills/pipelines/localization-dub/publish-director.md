# Publish Director - Localization Dub Pipeline

## When To Use

Package the completed localization outputs so downstream teams can find the right video, subtitle, and metadata bundle for each language without manual cleanup.

## Process

### 1. Package By Locale

Each language package should clearly separate:

- video output,
- subtitle files,
- transcript or approved script copy,
- review notes,
- metadata.

### 2. Keep Naming Precise

Recommended metadata keys:

- `locale`
- `language_name`
- `deliverable_mode`
- `subtitle_included`
- `review_owner`

### 3. Preserve Review Context

If a language output has pronunciation caveats, timing warnings, or missing lip sync, keep that note in the published package.

### 4. Quality Gate

- locale packages are clearly labeled,
- metadata matches the actual treatment,
- supporting text assets are present,
- warnings and review notes are not lost.

## Common Pitfalls

- Shipping localized videos without the matching subtitle or transcript files.
- Mixing audio-dub and subtitle-only variants under the same generic filename.
- Removing the QA notes that explain known issues.

---

## Gate Reminder (Binding)

This stage gates on human approval (`human_approval_default: true`). After review passes:
checkpoint with `status="awaiting_human"`, present the summary (the Backlot board renders
the artifact), and **END YOUR TURN**. Do not start the next stage in the same response.
Approval is per-gate — an earlier "go ahead" does not cover this gate.


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
