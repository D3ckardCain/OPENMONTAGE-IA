# OpenReel como editor local y puente de agente: evaluación #46

Fecha:24-11-2026 UTC. Snapshot oficial `Augani/openreel-video@b358fabb45ed3e3c19a4d518b09b61660dff6bed`,
también HEAD consultado. Lectura estática de fuentes, licencias y metadatos npm;
sin clonar/instalar, ejecutar build, conectar MCP, cargar modelos o generar medios.
OPENMONTAGE base funcional `d401390`; GitHub Dark y configuraciones permanecen intactos.

## Decisión

El valor nuevo es un editor multipista con acciones reversibles y puente MCP, no otro
selector de highlights ni otro agente de producción. Evaluar primero un contrato de
intercambio de proyecto y un adaptador MCP pequeño, conservando el agente Ollama actual.
No integrar el monorepo ni su chat/ASR por defecto. La incorporación del bundle completo
queda condicionada a licencias de dependencias, export y compatibilidad Windows.
Esta evaluación termina con tareas concretas, no con una instalación aprobada.

## Comparación y reutilización

| Área | OpenReel revisado | OPENMONTAGE actual | Decisión |
|---|---|---|---|
| Edición | Timeline de pistas, clips, subtítulos, transformaciones, keyframes y transiciones en el modelo Project y acciones del editor | `scene_plan`, `edit_decisions` con cortes/audio/overlays/subtítulos; trimmer/stitch/composición y storyboard | El editor gráfico multipista reversible es una ampliación. No sustituir los contratos existentes ni confundir ver el storyboard con editar un NLE completo |
| Agente | MCP desktop autenticado y registro de herramientas, chat BYOK web/desktop y runner headless | LocalAgent/Ollama, validación de herramientas, presupuesto0, recibos, checkpoints y cancelación | Reusar el agente actual; exponer un subconjunto MCP explícito. No ejecutar dos directores de producción ni delegar aprobación/publicación a defaults externos |
| Persistencia | StorageEngine IndexedDB; serializador JSON y rutas de archivo desktop; historial/undo de turno | JSON atómico en proyectos, historial de checkpoints, hashes y procedencia | Fuente de verdad y respaldo en proyectos OPENMONTAGE. IndexedDB es caché/estado de editor, no respaldo único ni vínculo automático a archivos originales |
| Subtítulos/audio | Edición de subtítulos y audio en el editor; worker Whisper de navegador separado | ASR multilingüe local preparado, palabras/subtitle_gen y audio/composición existentes | Importar transcript/words en español con offsets declarados; no descargar otro Whisper ni usar cloud. Preservar correcciones y procedencia al volver |
| Export | Motores web y desktop, cola y sidecars FFmpeg; capacidades dependen de backend/codec | FFmpeg/ffprobe, Remotion/HyperFrames y recibos de render/entrega | Mantener export existente primero. Un JSON editado o preview correcto no es vídeo exportado ni entrega verificada |
| Apariencia | Editor React propio y otra jerarquía visual | Studio GitHub Dark de operación y aprobación | Editor opcional separado/aislado, no migrar ni repintar Studio. Embebido/iframe no se decide sin revisar CSP/CORS/atajos/foco |

Fuentes locales revisadas: `schemas/artifacts/edit_decisions.schema.json`,
`lib/scene_edit.py`, `scene_batch.py`, `production_agent.py`, `agent_conversation.py`,
`render_verification.py`, `final_delivery.py`, herramientas trimmer/stitch y UI Studio.
La búsqueda no encontró un NLE multipista completo con undo en ese panel; no declara
ausencia de toda experimentación de timeline en el repositorio.

## Diferencia decisiva: Ollama web/MCP no equivale a CLI local listo

[Guía de agente](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/docs/AGENT-GUIDE.md)
y [transporte renderer](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/apps/web/src/services/agent/direct-llm-transport.ts)
admiten endpoint compatible con OpenAI, HTTP localhost, clave opcional y tool calling.
El renderer hace la petición y requiere CORS del endpoint; no cambiar OLLAMA_ORIGINS
ni ampliar acceso global durante la evaluación. MCP permite que el agente de Studio
llame al editor sin habilitar otro cliente LLM en el navegador.

En cambio, [node-llm.ts](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/packages/agent-runner/src/node-llm.ts)
solo enumera anthropic/openai, exige clave y fija endpoints externos.
El ejemplo CLI no es una ruta Ollama sin cambios. La API programática
[run.ts](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/packages/agent-runner/src/run.ts)
permite inyectar `llm`, útil para fixtures o transporte propio, pero no justifica
instalar otro bucle cuando OPENMONTAGE ya lo tiene. El headless usa un Host/serializador
y runner de jobs inyectable: no incluye por sí mismo el motor de export web/desktop.

## MCP, archivos, undo y cancelación

- [http-server.ts](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/apps/desktop/src/main/mcp/http-server.ts)
  usa host127.0.0.1 por defecto, bearer validado y límite4MiB. El llamador desktop
  revisado genera token aleatorio y escribe endpoint local. No publicar token ni
  copiarlo a artefactos/JS del panel. Descubrir herramientas con tools/list, sin
  afirmar que el catálogo entero funciona por existir.
- La guía indica permisos destructivos/export MCP habilitados por defecto. El puente
  propio debe negar esas acciones inicialmente y limitar capabilities; no heredar
  auto-approve ni los escape hatches execute_action/batch_actions indiscriminadamente.
- [policy.ts](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/apps/desktop/src/main/mcp/policy.ts)
  permite por defecto varias carpetas del usuario, y añade carpeta del proyecto y
  watch folders a effectiveRoots. No basta con estrechar una lista: comprobar raíces
  efectivas y path-guard, rutas reales/symlinks, escrituras y medios importados. Usar
  copias de proyecto y salidas nuevas bajo su workspace, sin ampliar raíces existentes.
- [loop.ts](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/packages/agent/src/loop.ts)
  abre transacción, comprueba AbortSignal y revierte por error. Undo de estado de
  editor no garantiza deshacer copias de archivos o exports externos. No confundir
  cancelar chat, cerrar transporte MCP, revertir edición y cancelar un job de render.
- [project-io.ts](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/packages/agent-runner/src/project-io.ts)
  guarda JSON con writeFile y el runner puede escribir in-place por defecto. El
  adaptador futuro debe guardar candidato separado, temporal+replace y backup/hash;
  validar schema/revisión antes de aceptar. No apuntarlo al original aprobado.
- La [cola de export](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/docs/export-queue.md)
  guarda un snapshot y recupera jobs interrumpidos en pausa, pero documenta que una
  modificación de efectos/overlays durante un render puede afectar fotogramas
  pendientes. No prometer aislamiento total: el puente deberá congelar revisiones
  o bloquear esas mutaciones mientras exporta y comprobar el recibo al reanudar.

## Dependencias, idiomas y requisitos efectivos

El [package.json raíz](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/package.json)
declara Node>=18 y pnpm>=8, pero fija packageManager=pnpm11.7.0.
Los [metadatos oficiales de pnpm11.7.0](https://registry.npmjs.org/pnpm/11.7.0)
exigen Node>=22.13; CI upstream usa Node22. El Node22.23.5 ya registrado en OPENMONTAGE
satisface ese mínimo declarado, sin repetir su instalación ni acreditar el build.
No recomendar Node18 por copiar README. pnpm no fue instalado.

La web usa React19.2.7, TypeScript/Vite, Zustand, Mediabunny, WebCodecs y rutas
WebGPU/WebGL/Canvas; core incluye ffmpeg.wasm, ONNX Runtime Web, Three y GSAP.
El build raíz compila WASM con AssemblyScript; no inferir requisito Rust de la palabra
WASM. Desktop1.1.0 añade Electron, sidecars y scripts nativos; el host Audio Units
revisado se salta fuera de macOS. No se certifican plugins nativos Windows por el
build del editor. `pack/dist` llaman fetch:ffmpeg: no ejecutarlos en esta evaluación.

El [worker Whisper](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/apps/web/src/workers/whisper-worker.ts)
activa modelos remotos y desactiva modelos locales; usa media.openreel.video y caché
del navegador. Su [tabla](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/apps/web/src/workers/whisper-models.ts)
ofrece Large-v3-turbo/tiny, anunciados≈760/100MB. Tener WASM empaquetado no elimina
esa descarga inicial. Evitar este duplicado y transportar palabras del ASR preparado
de OPENMONTAGE. Verificar español/¿¡/ñ/acentos en controles y captions: no se ha
acreditado traducción completa de la UI. `posthog-js` aparece en dependencias; no se
auditó su activación y no se presume tráfico por solo verlo en package.json. La
validación offline futura debe inspeccionar/bloquear red real y recursos remotos.

## Licencias: no es un bundle íntegramente MIT

| Componente revisado | Evidencia y consecuencia para la propuesta |
|---|---|
| Código OpenReel | [LICENSE MIT](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/LICENSE). Conservar avisos/commit si se adapta código. OPENMONTAGE mantiene AGPLv3 |
| Mediabunny1.25.3 | [Registro oficial: MPL-2.0](https://registry.npmjs.org/mediabunny/1.25.3), no MIT. Revisar fuente y obligaciones de distribución de archivos modificados; [FAQ de Mozilla](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) describe copyleft por archivo |
| GSAP3.14.2 | [Metadatos](https://registry.npmjs.org/gsap/3.14.2) remiten a licencia Standard sin cargo. [Texto oficial](https://gsap.com/community/standard-license/) restringe ciertos usos en creadores visuales de animación competidores. No asumir que gratuito=MIT o permiso automático para un editor visual. Resolver encaje antes de adoptar ese componente; si requiere autorización/costo no disponible, excluirlo o usar alternativa compatible |
| Paper shaders0.0.76 | [Metadatos](https://registry.npmjs.org/@paper-design%2fshaders/0.0.76) remiten a LICENSE externo; el [main consultado](https://github.com/paper-design/shaders/blob/main/LICENSE) es Apache2.0, pero eso no fija por sí solo el archivo de la versión0.0.76. Verificar paquete/avisos antes de redistribuir |
| Transformers.js3.8.1 | [Apache2.0 declarada](https://registry.npmjs.org/@huggingface%2ftransformers/3.8.1); los pesos ASR tienen licencias aparte. No se descargan ni adoptan aquí |
| FFmpeg nativo desktop | [Avisos upstream](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/apps/desktop/LICENSES/FFMPEG.md) declaran builds GPL y Windows GPL3+. Verificar manifest/configuración/fuente correspondiente si se distribuye; no copiar ofertas de fuente con contacto de ejemplo. Preferir el FFmpeg existente con procedencia conservada |
| ffmpeg.wasm | El campo npm del paquete no basta: [FAQ oficial](https://ffmpegwasm.netlify.app/docs/faq/) distingue wrapper MIT del core y bibliotecas con licencias FFmpeg respectivas. Auditar el artefacto real antes de empaquetar |
| Blender opcional | [Aviso propio](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/apps/desktop/LICENSES/BLENDER.md): GPL y proceso aparte. No instalar otro Blender ni asumir exención por distribución gratuita |

Esto identifica condiciones concretas de adopción, no certifica toda la cadena de
licencias, recursos o codecs. No se incorpora código/binario externo en esta entrega.

## Tareas propuestas y aceptación

| Prioridad | Tarea futura | Entrega verificable sin contenido real al comenzar |
|---|---|---|
| P0 | Especificación de intercambio | Mapa explícito edit_decisions↔Project con versión, IDs, hashes, segundos/frames, fps fraccional, pistas, offsets y rutas. Lo no soportado se informa, no se pierde silenciosamente. Round-trip con JSON sintético; export distinto de aprobación |
| P0 | Doctor MCP y puente mínimo | Endpoint loopback+token privado, versión/tools/list, proyecto correcto, whitelist de lectura/dry-run y errores de ruta/autorización. Tests con servidor MCP falso, timeout/desconexión y herramientas desconocidas; ninguna instalación o conexión a editor real hasta superar requisitos |
| P0 | Condiciones de licencia/paquete | Inventario exacto de dependencias resueltas y notices; resolver GSAP/artefactos multimedia antes de empaquetar. Documentar alternativa sin cargo si se excluye algo; no comprar licencia ni asumir permiso por MIT raíz |
| P1 | Mutaciones reversibles y recuperación | Copia candidata, diff y revisión; transacción/undo/redo, fallo de guardado, revisión obsoleta, permisos y disco lleno. Separar cancelación de LLM/transporte/job y conservar recibos sin duplicar export al reanudar |
| P1 | Texto español y persistencia | Importar words/subtítulos locales sin otro ASR; acentos, signos y fuentes, tiempos absolutos/relativos. JSON portable/backup y relink con IndexedDB ausente, cuota agotada, cierre y recarga |
| P2 | Validar motor Windows/Edge y export | Plan de fixtures para codecs/capabilities, rutas largas, color/SAR/fps, transparencia, audio/latencia, preview/export y memoria. Futura fase autorizada con medios sintéticos; ffprobe/decodificación/recibos del motor elegido, sin sustituir render_runtime aprobado |

## Límites de la evaluación

[known-limitations.md](https://github.com/Augani/openreel-video/blob/b358fabb45ed3e3c19a4d518b09b61660dff6bed/docs/known-limitations.md)
avisa de apartados históricos superados: por ejemplo estimaciones antiguas de memoria,
LUTs y keyframes tienen correcciones posteriores. Se priorizó su estado/resumen y el
código seleccionado, sin presentar números viejos como rendimiento vigente. Varias
mediciones upstream se hicieron en macOS; no acreditan Windows, GPU local ni paridad
con editores comerciales. WebCodecs/WebGPU/codec real se consultarán en ejecución,
no se deducen de tener Edge o de un catálogo de funciones.

No se verificaron build, IndexedDB real, import/export, MCP físico, precisión ASR,
GPU/memoria o calidad audiovisual. Los defaults cloud del CLI y la revisión de
licencias son condiciones pendientes de una implementación, no bloqueos para terminar
esta evaluación. Priorizar contrato+MCP y conservar el director/ASR actuales, en vez
de instalar el editor completo. Costo$0; PR#2 permanece en borrador.
