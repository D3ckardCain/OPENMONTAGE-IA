# Stickman Video Director: evaluación #55

24-11-2026 UTC. Snapshot `kaomei/stickman-video-director`
`8394bec0148fa281ea59171d90fddc13afb80c4e`; runtime privado 1.0.0.
No se instalaron skills ni se ejecutaron init/doctor/render. Las instrucciones
upstream son objeto de comparación, no autorizaciones de producción.

## Decisión: reutilizar planificación, conservar motores

La aportación útil es relacionar cada movimiento con narración, objetos y cambios
observables. El borrado hipotético de una animación debería perder información,
causalidad o emoción pertinente; píxeles cambiantes no prueban actuación útil.
Adoptar un contrato opcional de eventos semánticos, no quince estilos de muestra
ni un segundo director. No trasladar sus reglas de duración o apariencia a Studio.

OPENMONTAGE ya tiene `pipeline_defs/character-animation.yaml`, herramientas
`tools/character/character_animation.py`, schemas character_design/rig_plan/
pose_library/character_qa_report, Rhubarb y el director con checkpoints. Ink Theater
y su Ink Puppet ya ofrecen trazos, poses y coreografías de mocap con tiempo seek-safe;
Remotion/HyperFrames y Blender cubren composición/3D. No presentar stick figures,
sincronía o continuidad como capacidades enteramente ausentes.
Falta justificar semántica de acciones y anclajes a narración de forma comprobable
entre esos artefactos. Un JSON válido no acredita revisión visual/auditiva.

## Fuentes y requisitos

- [README.en](https://github.com/kaomei/stickman-video-director/blob/8394bec0148fa281ea59171d90fddc13afb80c4e/README.en.md) y [SKILL](https://github.com/kaomei/stickman-video-director/blob/8394bec0148fa281ea59171d90fddc13afb80c4e/skills/directing-stickman-videos/SKILL.md): Model Engine A genera clips con modelos; Code Engine B anima capas y compone localmente. Código local no elimina costos de preparar imágenes, voces o del agente.
- [package](https://github.com/kaomei/stickman-video-director/blob/8394bec0148fa281ea59171d90fddc13afb80c4e/skills/directing-stickman-videos/package.json): Node>=20, @napi-rs/canvas0.1.100 y sharp0.35.5; FFmpeg/ffprobe externos. Binarios nativos por plataforma aún no validados en Windows.
- [runtime](https://github.com/kaomei/stickman-video-director/blob/8394bec0148fa281ea59171d90fddc13afb80c4e/skills/directing-stickman-videos/references/autopilot-runtime.md): B1–B4 usan manifestv1, B6 despacha a runtime propio y código trusted-code. No existe un único contrato intercambiable con nuestros renderers. Init copia material/proyectos; no es operación inocua de consulta.
- [semántica B3](https://github.com/kaomei/stickman-video-director/blob/8394bec0148fa281ea59171d90fddc13afb80c4e/skills/directing-stickman-videos/references/b3-semantic-motion.md): eventos con antes/después, tiempos, capas y propósito; conectores con objeto/ancla. Su validación geométrica explícitamente no acredita significado, oclusión o legibilidad final.

## Licencia, costo y offline

[LICENSE](https://github.com/kaomei/stickman-video-director/blob/8394bec0148fa281ea59171d90fddc13afb80c4e/LICENSE)
MIT del proyecto con avisos. Recursos, audio, identidades de referencia y fuentes
requieren cadena propia. El [archivo de licencias de audio](https://github.com/kaomei/stickman-video-director/blob/8394bec0148fa281ea59171d90fddc13afb80c4e/docs/audio-license-archive/README.md)
documenta capturas y manifiestos, no una autorización universal sobre cualquier demo.
El [registro de fuentes](https://github.com/kaomei/stickman-video-director/blob/8394bec0148fa281ea59171d90fddc13afb80c4e/skills/directing-stickman-videos/assets/fonts/README.md)
separa Nunito/Anton/Archivo Black OFL de Arial Rounded Bold propietario no redistribuido.
Conservar huellas y avisos del asset seleccionado; no copiar muestras como originales.

Las demos A usan Flow y varias rutas hacen referencia a Gemini/voces/servicios y
suscripciones de agentes: no cumplen por sí mismas costo operativo $0 ni offline.
Para una adaptación futura: Ollama/imagen/vídeo/TTS/ASR locales ya preparados,
fuentes locales con ñ/acentos/¿¡ y render existente. No prometer equivalencia a demos
al sustituir modelos; cualquier producción futura conserva gates y elección del
usuario. Runtime local con archivos presentes puede funcionar offline; generación
integral y cobertura española no se probaron. No descargar recursos implícitos.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Eventos semánticos opcionales en scene_plan | Datos sintéticos con cue, actor/objeto, antes/después, tiempo y propósito; referencias rotas, final fuera de frames y decoración mal clasificada detectados |
| P1 | Continuidad y anclajes | IDs estables entre planos/ratios, conectores unen objetos correctos; estado no se pierde al recortar/reordenar; originales preservados |
| P1 | Español y audio | Contrato reutiliza ASR/TTS/subtítulos preparados, acentos y puntuación; alineación por timestamps, no duración inferida de número de palabras |
| P2 | Intercambio sobre motores actuales | Traducción limitada y explícita a rig/poses/edit_decisions; no ejecutar expresiones o código externo del manifest; unsupported se informa, no fallback oculto |
| P2 | QA diferenciada | Validación schema/tiempo/geométrica separada de revisión audiovisual futura con evidencia por evento; no marcar aprobado por plantilla o preview técnico |

Bloqueos: derechos de assets elegidos, memoria/calidad de modelos y validación
perceptual pendientes. Contratos/test fixtures son independientes. No hubo voz,
imagen, geometría ni animación generada; motores y configuraciones intactos.
