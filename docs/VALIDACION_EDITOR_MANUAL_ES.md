# Evidencia y pendientes del editor (#92)

Fecha: 2026-11-24. Base remota comparada antes de editar: `d9c3573307c34002ac49368e4140826133ff4e00`, rama `feat/local-agent-research-foundation`. El workspace procede de ZIP y no contiene `.git`; publicación mediante árboles/commits GitHub conservando árbol base y verificación de HEAD, sin force push. PR #2 continúa en borrador.

## Implementación y alcance probado

| Fase | Código disponible | Evidencia y límite |
|---|---|---|
| Espacio widescreen | Menú principal, biblioteca, monitor real HTML5, inspector, pistas, tamaños/ocultación persistidos | HTML servido comprobado por HTTP; controles/anchos se prueban en CI con estado JSON sintético. No hay inspección visual local acreditada. |
| Vídeo manual | Importar/registrar, fuente individual, añadir, entrada/salida, dividir, reordenar por arrastre/botones, quitar, zoom, guardar/reabrir, undo/redo, presets, vista previa/exportación FFmpeg | Pruebas de contrato/API y del proceso de render con probe/encoder simulados explícitamente. No se ejecutó una edición/exportación audiovisual real. |
| Audio | Importación, recorte/división, desplazamiento temporal, ganancia, silencio, velocidad, fundidos, mezcla FFmpeg; waveform Web Audio del primer canal | Grafo, tiempos y mezcla comprobados offline; decodificación de archivo real y escucha pendientes. No se generó audio. |
| Subtítulos | SRT, tiempos/texto, dividir/unir/desplazar, CPS, SRT/ASS de salida, estilo ASS y modos mov_text/quemado | Lector existente, serialización y controles probados con texto; mux/burn y sincronía audiovisual real pendientes. |
| Agente | Herramienta HTTP `studio_project_edit`, misma revisión/funciones y procedencia que la UI | Transporte local simulado mediante TestClient, conflictos 409 y exclusión de escrituras durante render. No se llamó a Ollama ni se atribuye decisión de IA a fixtures. |

`tests/backlot/test_studio_editor.py` cubre el ciclo persistente con archivos de **texto** y probe/encoder sustituidos. Los nombres `.mp4` de sus archivos temporales no implican medios reales: contienen un marcador textual. No son prueba de codecs ni de reproducción. Incluye dos escritores concurrentes con revisión igual, rutas fuera del proyecto, fuentes modificadas, entradas NaN/Infinity, límites de recorte/división, procedencia, original conservado, lectura parcial HTTP, modos de subtítulos, errores de render y estado interrumpido tras reinicio.

La previsualización y la exportación ejecutables comparten `studio_editor_render.plan`; reusan descubrimiento/configuración multimedia, cadena `atempo` existente, lector SRT y generador ASS. La extensión manual no sustituye decisiones de producción ni presume compatibilidad total con todos los compositores. Ver [manual](EDITOR_MANUAL_STUDIO_ES.md).

## Resultados locales

- Primera entrega local: **81 passed / 1 skipped en 9.04 s**: editor (32 casos) + producción Studio + contrato de E/S UTF-8. Se reutilizó Python 3.11.9 de `.venv`, añadiendo al proceso de pruebas el `site-packages` del entorno QA ya preparado para disponer de pytest. No se instalaron paquetes ni se cambió ningún entorno.
- 312 passed: editor + punteros de skills + contratos phase0 (69.38 s).
- Regresión ampliada con escenas: 92 passed / 1 skipped / **1 failed**. El test antiguo `test_preview_uses_registered_image_and_does_not_advance` falló al leer `scene_batch.json` durante escritura concurrente en Windows (`PermissionError`). La ejecución aislada volvió a fallar. Otra ejecución anterior de editor/escenas/política local había aprobado 41 pruebas. No se oculta el fallo, no se deshabilita el test ni se cambia su timeout. La ampliación opcional de `_ass` mantiene por defecto su salida anterior; el lector de escenas no se modificó. CI Linux y contratos Windows deben evaluarse por separado.
- `node --check`: módulos de Studio/editor sin errores de sintaxis. No equivale a prueba DOM ni visual.
- FFmpeg configurado conserva filtros `ass`, `concat`, `amix`, `alimiter`, `tpad`; inspección de capacidades, sin procesar medios ni inferencias.

## Bloqueos de la instalación activa

Se comprobó Studio en loopback: servidor de `C:\OPENMONTAGE-IA`, Python 3.11.9, puerto 4750. Cola pausada/vacía, `worker_active=false` y `local_task_active=false`; sin procesos FFmpeg/FFprobe activos.

El intento de reiniciar **solo Studio** fue **rechazado por la revisión automática de aprobación, `blocked by policy`**, sin motivo más específico. No se intentó eludirlo con otro lanzador, shell o herramienta. El proceso original permanece activo. El HTML se sirve de disco y ya contiene el monitor/menú/accesos anteriores; `/api/studio/editor/projects` devuelve **404** en ese proceso, por lo que la UI explica la necesidad de reinicio y deshabilita el editor. No se declara desplegada la API ni validado el ciclo en el panel activo.

La página queda en ASCII con entidades HTML para preservar caracteres españoles y símbolos incluso en el lector antiguo dependiente de la codificación de Windows. El handler actualizado fija UTF-8. Una comprobación HTTP confirmó `edit-player`, `legacy-studio` y `data-section="video"` después de esta compatibilidad; no es una captura visual.

La sesión carece del runtime `node_repl` requerido por la skill [computer-use](C:/Users/sando/.codex/plugins/cache/openai-bundled/computer-use/26.1117.31558/skills/computer-use/SKILL.md): «Run this once per fresh `node_repl` JavaScript session». Se revisó la guía de esa skill y no se construyó un cliente alternativo. Existe además una restricción previa de la sesión contra abrir otro navegador. La CI usa el job de navegador ya existente; no se lanzó uno local para sortear restricciones.

No se encontraron medios de validación existentes en `projects/`, `.runtime/qa/` y `tests/qa/` mediante búsqueda por extensión. No se ampliaron búsquedas a vídeos personales ajenos a esos directorios ni se generaron fixtures audiovisuales nuevos. Por tanto, reproducción/exportación con medios autorizados y escucha/sincronía permanecen sin comprobar.

## CI y evidencia visual automatizada

El job existente `browser-regressions` incorpora cinco casos para 1280×720, 1920×1080, 2560×1440, 3440×1440 y 640×720. El último comprueba reflujo con espacio equivalente al de una ventana 1280 a zoom 200%; **no acredita un ensayo del zoom nativo del navegador**. Cambios de pestaña conservan proyecto, comandos envían revisión exacta, no hay overflow horizontal ni errores JS. Sus datos son JSON sintético, sin medios ni inferencia.

Capturas/JSON se guardan como artifact `studio-editor-layout-<run_id>`. La CI conserva lint, suite completa, contratos Windows/Linux y pruebas de navegador sin red externa; solo se añadió preservación de evidencia, sin quitar checks, ampliar timeouts ni reintentar fallos. Los enlaces y resultados del commit se registran en #92/#3 y PR #2 después de finalizar.

### Primera CI y correcciones derivadas

Commit inicial `16bb3467c8b7b85f3994211e03e75c1f4776a3e6`: [CI completa45442696155](https://github.com/D3ckardCain/OPENMONTAGE-IA/actions/runs/45442696155) aprobada, **3438 passed / 44 skipped / 3 xfailed / 40 subtests passed, 127.04 s**, intento1. Instalación y contratos Windows/Linux aprobados. [Navegador PR45442696241](https://github.com/D3ckardCain/OPENMONTAGE-IA/actions/runs/45442696241) y push45442680676 fallaron: **3 failed / 28 passed**. Los cinco casos nuevos del editor pasaron; fallaron tres regresiones de los flujos existentes. No se declara verde esa entrega.

Causas de esas regresiones: el nuevo inicio Vídeo ocultaba formularios cuando un enlace de canal llevaba `reference/title/brief`; y la regla específica `#legacy-studio` mantenía dos columnas a390px, anulando el reflujo anterior. Se corrige el código para respetar enlaces de preparación de producción y restaurar una columna móvil; **las tres pruebas fallidas se conservan sin cambios**. No hay ampliación de timeout ni reintento de la misma revisión para ocultarlo.

[Artifact inicial14943817081](https://github.com/D3ckardCain/OPENMONTAGE-IA/actions/runs/45442696241/artifacts/14943817081): cinco PNG/cinco JSON, SHA256 ZIP `b2c282dfe6c187fd71b3a88b026884638ed3b2ef2310bdae3e9a7293161fb1d5`. Recuperado mediante GitHub; cinco informes sin overflow horizontal ni errores JS, comandos `output/save` con revisiones0/1. Se inspeccionaron las capturas1920×1080 y640×720: biblioteca, monitor, inspector y pistas presentes con GitHub Dark, sin medios. Eso acredita únicamente la UI sintética de CI, no el panel de Windows ni playback real.

La corrección también hace proporcional la anchura de clips, representa los inicios independientes de audio, añade miniaturas/cursor temporal y reserva estado/importaciones/snapshots frente a escrituras genéricas del agente. El diagnóstico de la herramienta exige una API de editor accesible. Se añaden pruebas de esas reservas y del diagnóstico. El resultado final de la nueva revisión se registra en el issue; no se confunde con el resultado de `16bb3467`.

Regresión local de la corrección: **86 passed / 1 skipped, 11.13 s** (33 casos del editor más producción/UTF-8). Se retienen las verificaciones de error, concurrencia, restricciones de rutas y costo cero; la CI final debe confirmar además los navegadores y todos los contratos.

La revisión `3fbf57b83ed7dbca8b7f31735be2212451299ef8` quedó aprobada en intento1: [CI45444307267](https://github.com/D3ckardCain/OPENMONTAGE-IA/actions/runs/45444307267), **3443 passed / 44 skipped / 3 xfailed / 40 subtests passed, 103.01 s**; [contratos PR45444307274](https://github.com/D3ckardCain/OPENMONTAGE-IA/actions/runs/45444307274) y [push45444290361](https://github.com/D3ckardCain/OPENMONTAGE-IA/actions/runs/45444290361), incluidos navegador e instalación/contratos Windows/Linux. Las tres regresiones anteriores están resueltas sin modificar sus pruebas.

Revisión posterior de procedencia: se separa importar SRT original (bytes exactos, BOM/CRLF y hash conservados) de aplicar cambios al texto. Antes, editar el campo antes de aplicar podía guardar una copia modificada bajo el nombre de origen. Un test HTTP conserva los bytes originales tras editar cues, rechaza revisiones anteriores y valida entradas inválidas sin mutar el proyecto. Las lecturas SHA256 quedan acotadas al tamaño inicial y rechazan crecimiento/truncado durante la lectura, sin perseguir un archivo en expansión. **Regresión local posterior: 89 passed / 1 skipped, 12.47 s**. Los resultados CI de esta última revisión se publican en #92; no se atribuyen a la revisión anterior.

## Conservación y trabajo restante

SHA256 de configuraciones conservadas:

```text
settings.json     497DDCD071B06F9AD4109E3123CDB36EBC6BB5A1F33AB53E556FE931B09AD952
applications.json 33073A45E5D34775AAE08CEF0557BCE23B59DDEAF0699BE26B70909DCE4CCF7B
```

Sin instalaciones, descargas, inferencias, carga de modelos ni contenido real generado. ComfyUI y originales intactos; costo $0. No se publican configuraciones, medios, `.runtime`, `.venv` ni aplicaciones.

Pendiente de aceptación #92: activar las rutas en la instancia permitida; inspeccionar el panel local y las capturas CI; realizar el ciclo con medios autorizados existentes; validar waveform/escucha/subtítulos reales y zoom 200% nativo. Funcionalidad restante explícita en UI/manual: importación del montaje de producción al editor, intercambio editorial completo, títulos/transiciones, reencuadre focal, solo/bloqueo, pistas voz/música/FX, selección avanzada de waveform, A/B, ASS de entrada, karaoke y traducciones separadas. No se cierra #92 por esta primera entrega.
