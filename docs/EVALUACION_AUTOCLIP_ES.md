# #103 — Dos proyectos AutoClip

Evaluación documental, 25-11-2026 UTC. Reutiliza comentario7146274272; sin
instalaciones, inferencias, descargas o publicación de clips.

## Identidades y fuentes

| Proyecto fijado | Versión / licencia / requisitos documentados |
|---|---|
| [artbyjazi/autoclip](https://github.com/artbyjazi/autoclip/tree/5d0eac36fa615b79dd2104083bf273a96f8d68bb) | 0.1.0.dev0; MIT; Python>=3.11,<3.13; fuentes Anton/Inter OFL |
| [zhouxiaoka/autoclip](https://github.com/zhouxiaoka/autoclip/tree/9e62c07c5770b1206bbd5ecea8304e82e8bb1c5c) | 1.6.0; MIT; Python>=3.10; escritorio Windows10/11 x64 documentado con Python/FFmpeg empaquetados |

No mezclar capacidades ni versiones. MIT del código no licencia vídeos, voces,
modelos de diarización, fuentes o servicios. Reutilizar ASR/Ollama/FFmpeg,
`auto_reframe.py`, selección de clips y `source_media_review` existentes.

## Aportes verificables y límites offline

Art describe ingestión→candidatos→revisión→exportación y Whisper/Ollama local.
Elegir índices de palabras y resolver tiempos medidos evita inventar timestamps
con el LLM. Esto no demuestra calidad española ni predice viralidad. Inspección
previa de crop_path/speaker: actividad de boca y turnos son heurísticas, no
identidad segura; fuera de plano, reacción y solapamiento requieren fallback
ancho y corrección manual. WhisperX/pyannote opcionales pueden necesitar modelos
gated, token y licencia propia. Texto enviado a proveedores cloud deja de ser
offline aunque ASR sea local.

Zhou anuncia Ollama/LMStudio y Whisper/SenseVoice locales, pero la inspección
registrada de llm_providers/configuración no prueba todo el flujo sin red.
Documentar esa diferencia: base_url local no certifica ASR/exportación offline.
API cloud de ASR/caratulas, APIMart, UploadPost y publicación Bilibili requieren
red/cuentas y pueden tener coste. MCP/CLI anunciados no demuestran paridad total.
No cambiar telemetría/configuración existente en esta evaluación.

FFmpeg “full” frente a “Essentials” es una recomendación upstream: comprobar
capacidades reales libass/encoders/filtros solo cuando falten; no reemplazar la
instalación aprobada por una etiqueta. Windows empaquetado no fue ejecutado aquí.
Coste$0 viable con motores y recursos locales elegibles ya preparados; no asumir
que modelos opcionales estén presentes ni que no descarguen al primer uso.

## Carencias útiles, agrupadas

| ID / prioridad | Aceptación futura |
|---|---|
| E03 P0 | Candidatos por spans de palabra con fuente, tiempo medido y contexto; aceptar/rechazar manual, sin sobrescribir original ni puntuación de viralidad ficticia |
| E04 P0 | Crop editable por keyframes/PTS, confianza/fallback ancho y zonas seguras para palabras; cambios de plano y hablante incierto explícitos |
| E05/E06 P1 | Jobs y artefactos trazables, mismo EDL de agente/usuario, undo/reopen; no otro pipeline/downloader |
| B07/B08/B06 | Derechos y red, recursos gated y prueba española con silencios/dos hablantes/fuera de plano pendientes; 9:16 no acredita publicación social |

Evaluación concluida; no adopción automática de ninguno de los dos proyectos.
