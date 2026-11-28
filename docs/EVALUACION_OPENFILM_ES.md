# OpenFilm — evaluación #52

24-11-2026 UTC. [327ef4c8](https://github.com/openfilm/openfilm/tree/327ef4c86ceab07122a145c0d6d984045af7c295),
HEAD consultado; paquete openfilm0.4.1, SPEC protocolo0.1 draft. Evaluación estática:
sin instalar, lanzar CLI/Studio, descargar Chromium/modelos ni crear HTML audiovisual.

## Decisión y comparación

No añadir otro compositor/editor completo de inmediato. Evaluar interoperabilidad
de film.html y overrides sobre un proyecto candidato, manteniendo agente y pipelines.

| Área | OPENMONTAGE existente | Diferencia útil |
|---|---|---|
| HTML por tiempo | HyperFrames_compose posee materialización, lint/check/render y atelier HTML; Remotion compone por frames | `frame(t)` y film.html son otro protocolo, no un archivo HyperFrames compatible automáticamente. Interesa un traductor limitado con pérdidas declaradas |
| Montaje | edit_decisions, cortes/audio/subtítulos y composición aprobada | film.html declara clips/pistas y páginas iframe; posible formato de intercambio, no reemplazo del schema ni de render_runtime |
| Edición manual/agente | Storyboard/checkpoints; OpenReel #46 evaluado como editor multipista | Overrides como JSON separados de páginas fuente pueden conservar cambios humanos; evaluar conflictos/selectores y round-trip antes de incorporar otro editor |
| Recuperación | Recibos/hashes/jobs y salidas dentro del proyecto | Render upstream por chunks de10s, settings y firmas; estudiar invalidación/cache, no asumir que todo archivo grande se hashea íntegramente |
| Generación | ASR/Ollama/ComfyUI y motores existentes | Proveedores externos del nuevo Studio no acreditan costo0. No conectar sus cuentas, generación o publicación |

Locales: `tools/video/hyperframes_compose.py`, `video_compose.py`,
`lib/hyperframes_style_bridge.py`, `lib/agent_conversation.py` y esquemas de edición.
Fuentes upstream: [SPEC](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/packages/openfilm/SPEC.md),
[render](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/packages/openfilm/src/render.mjs),
[overrides](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/packages/openfilm/src/overrides.mjs),
[resume](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/packages/openfilm/src/render-resume.mjs).

## Contrato y límites observados

La página expone `frame(t)` y ready; sonido pertenece a clips audio/video y palabras
pueden venir de WebVTT. La imagen debe ser función de t, no de tiempo de pared o
historia de llamadas. El host debe esperar recursos y seeks; no deducir sincronía
de tener un timeline visual. Conservar fps racional, fuente/trim, speed y offsets.

Overrides referencian selectores: renombrar DOM o reescribir una escena puede dejar
cambios manuales sin destino. Se necesita versión/base hash y conflicto explícito,
no fusión silenciosa. HTML ejecuta scripts: un archivo de proyecto no es solo JSON.
La futura previsualización requiere aislamiento, límites de rutas y red denegada;
no abrir material externo dentro del Studio real ni permitir acceso a secretos.

Render recibe AbortSignal y limpia recursos/procesos; hay caché de chunks y control
de trabajos concurrentes. Eso es evidencia de diseño, no prueba física de cancelación.
La firma upstream usa hash de contenido para archivos pequeños y metadatos de
tamaño/tiempo para grandes: no equivale a SHA256 integral de cada medio. Conectar la
procedencia propia y probar invalidación tras modificar un asset manteniendo metadatos.
No confundir pausar espera, detener proceso y reanudar desde chunks válidos.

## Licencia, requisitos y offline

[MIT](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/LICENSE)
para código; preservar avisos y marcas. [Biblioteca](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/packages/openfilm/library/LICENSE.md)
declara CC0 para contenido propio y MIT para FluentEmoji con su aviso. No extrapolar
eso a cualquier plugin, fuente, medio importado o modelo. Los
[avisos de terceros](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/packages/openfilm/THIRD_PARTY_NOTICES.md)
separan InterOFL, ReactMIT, iconosISC/CC0 y otros paquetes; revisar artefactos exactos
si se distribuyen. OPENMONTAGE mantiene AGPLv3, sin copiar componentes aquí.

[package.json](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/packages/openfilm/package.json)
exige Node>=22.2 y fija playwright-core1.61.1, MediaPipe1.2.2 y ONNX Runtime Web1.31.1.
FFmpeg/ffprobe son herramientas externas; git sirve a versiones guardadas. El
[CLI](https://github.com/openfilm/openfilm/blob/327ef4c86ceab07122a145c0d6d984045af7c295/packages/openfilm/bin/openfilm.mjs)
puede instalar chromium-headless-shell en primer uso. No ejecutarlo ni su prepare/build
como una mera sonda; no se demuestra compatibilidad con el navegador ya presente.

Composición/render sobre recursos completos puede ser local sin API de pago; offline
requiere navegador/binarios y recursos ya presentes, URLs y fuentes locales, y modelos
opcionales preparados. Proveedores de voz/música/imagen/vídeo y publicar son funciones
distintas: deshabilitarlas o mapear explícitamente a motores elegibles existentes,
sin claves o fallback cloud. No se comprobó un puente directo listo para nuestro agente.
Un README traducido al español no certifica toda la UI ni captions en español.

## Tareas futuras con aceptación

| Prioridad | Tarea | Aceptación |
|---|---|---|
| P0 | Subconjunto de intercambio | Mapa versionado edit_decisions↔film.html, pérdida/unsupported explícitos y recursos con hash; parser de fixtures sin ejecutar scripts |
| P0 | Doctor local y elegibilidad | Dependencias/binarios/licencias reportados sin descargas; estado missing distinto de offline-ready; no instalar otro Node/Chromium por defecto |
| P1 | Round-trip humano/agente | Overrides y fuente/base guardados por separado; conflictos tras renombrar selectores, undo/revisión y protección del original probados con datos sintéticos |
| P1 | Determinismo y sonido | Plan de pruebas t repetido/desordenado, ready, fps fraccional, seeks, silencios, offsets y palabras españolas; sin ejecutar render en esta evaluación |
| P1 | Job/cancel/resume | Mocks de AbortSignal/procesos, manifiesto de chunks y corrupción; reconciliar sin duplicar, invalidar por cambios reales y separar recibo de presencia de salida |
| P2 | Sandbox/offline | Fixtures locales, red/proveedores denegados, rutas confinadas y recursos completos; preview/export físico y mediciones solo en fase autorizada |

No sustituye Remotion por una llamada de API ni añade automáticamente un editor
equivalente a OpenReel. Evaluación completa; integración, offline físico, calidad y
rendimiento quedan pendientes. Configuraciones/GitHub Dark conservados, costo$0.
