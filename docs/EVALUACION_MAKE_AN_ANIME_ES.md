# Claude Make an Anime: evaluación #61

24-11-2026 UTC. Fuente oficial `makevoid/claude-make-an-anime`
`adc1a76eb4e77df47f42160c2c166350a76ad849`. No versión semántica declarada en el
package de herramientas revisado; commit como identidad. Evaluación estática,
sin instalar skill, adoptar instrucciones externas, delegar agentes o ejecutar setup.

## Decisión y contraste

Reutilizar tres métodos: biblia visual con identidades/versiones, voz antes de
cerrar duración de plano y retomas limitadas al ámbito invalidado. No introducir
Ruby ni otro director. OPENMONTAGE ya tiene character_design/scene_plan, checkpoints,
decision_log, recibos persistentes y pistas de audio. `lib/scene_audio_preview.py`
verifica duración/hash y mezcla narración/música; `lib/agent_conversation.py` evita
repetir una herramienta sin recibo verificable. No confundir esa infraestructura
existente con calidad de actuación, continuidad o lip-sync aprobados.

Agrupar con #55/E11 eventos semánticos, E04 palabras/timing, E05 jobs/recuperación
y E06 intercambio. Extensión concreta: dependencia de cada toma de versiones de
personaje, escenario, voz y diálogo; cambiar voz invalida timing y planos afectados,
no todo el proyecto. Reusar una toma exige compatibilidad y evidencia, no solo nombre.

## Fuentes, licencia y requisitos

[README](https://github.com/makevoid/claude-make-an-anime/blob/adc1a76eb4e77df47f42160c2c166350a76ad849/README.md),
[SKILL](https://github.com/makevoid/claude-make-an-anime/blob/adc1a76eb4e77df47f42160c2c166350a76ad849/skills/make-an-anime/SKILL.md):
generación pagada Fal, GPT Image, H3/Seedance y ElevenLabs voz/música/SFX. Sus gates,
defaults de proveedor e instrucciones de subagentes no se incorporan a esta sesión.
Su setup instala paquetes por proyecto. Ruby>=3.2/Bundler, FFmpeg/ImageMagick,
Python3, Node>=22.12 y Chrome; VFX opcional Swift5.9/macOS14 no aplica a Windows.

[Gemfile](https://github.com/makevoid/claude-make-an-anime/blob/adc1a76eb4e77df47f42160c2c166350a76ad849/skills/make-an-anime/scripts/Gemfile)
incluye excon~1.7/json~3/rake~13.4;
[package](https://github.com/makevoid/claude-make-an-anime/blob/adc1a76eb4e77df47f42160c2c166350a76ad849/skills/make-an-anime/scripts/package.json)
p5^2.3.3/puppeteer-core^25.16.0 y requirements NumPy2/Pillow11–12.
Rangos no prueban una instalación reproducible o compatibilidad efectiva Windows.
[LICENSE MIT](https://github.com/makevoid/claude-make-an-anime/blob/adc1a76eb4e77df47f42160c2c166350a76ad849/LICENSE):
conservar avisos al adaptar código; no otorga derechos sobre modelos/voces/fuentes,
personajes reales ni ejemplos. No copiar historias, identidades o aprobaciones.

## $0 y local/offline

Flujo original no cumple costo$0 integral: incluso review:dialogue usa Whisper
pagado según README. No cuenta/crédito/Fal ni referencias subidas. Los métodos
se pueden especificar sobre Ollama, TTS español y ASR preparados y compositor local;
no se verificó equivalencia a demos al sustituir proveedores. Cache de requests
pagados no convierte un endpoint externo en offline. Acabado Windows puede usar
herramientas existentes; no migrar plataforma para Swift. Recursos/fuentes/modelos
deben estar presentes y licenciados antes de pruebas con egreso bloqueado.

## Tareas con aceptación

| Prioridad | Entrega | Aceptación y vínculo consolidado |
|---|---|---|
| P1 | Dependencias de toma/biblia | E06/E11: IDs y hash/versiones de cast/location/voz; cambio de personaje/voz invalida solo dependientes, conserva rechazados/originales |
| P1 | Diálogo→timing | E04: fixture español con pausas/solapes/retomas y fps racional; plano no trunca voz; conversión absoluta/relativa inequívoca |
| P1 | Reutilización trazable | E05: recibo con inputs/seed/proveedor real y motivo de reutilización; no tratar FORCE o archivo presente como nueva generación ni aprobación |
| P2 | Revisión diferenciada | E11: continuidad/cámara/contacto/audio con evidencia futura por plano, separada de schema/ffprobe; cero certificados derivados de ejemplos |

Bloqueo de ejecutar upstream: proveedores pagados y VFX macOS. No bloquea contratos
neutrales. Sin inferencia, voz, imágenes, render o modificaciones de configuración.
