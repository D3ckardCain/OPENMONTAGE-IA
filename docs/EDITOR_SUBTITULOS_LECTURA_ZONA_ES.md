# Límites de lectura y zona segura — #174/#129

Primera ampliación sobre el editor de cues y palabras ya existente. No repite ASR, inspección de palabras ni muestra portuguesa. Cuenta: todavía no implementada (#168); estos ajustes pertenecen al proyecto, no a una biblioteca de estilos por cuenta.

En **Lectura y zona segura de subtítulos**, guardar máximo de líneas1–4, caracteres por línea10–80 y CPS5–40. Revisar consulta avisos por cue y propone saltos de línea; pulsar un cue usa el inspector/cursor existentes. Aplicar requiere confirmación y hash vigente. No cambia tiempos, elimina negaciones ni divide palabras largas; agrupa espacios explícitamente como formato, conservando la secuencia de tokens. Deshacer/rehacer y reapertura comparten EDL con el agente.

Avisos no equivalen a comprensión medida ni bloquean la exportación. CPS cuenta espacios/puntuación y omite saltos; longitudes cuentan caracteres Unicode, no anchura tipográfica. La propuesta puede seguir excediendo líneas/CPS: revisar/retimar, nunca truncar texto para cumplir un número. No se promete cabida pixel-perfect de cualquier palabra o tamaño de fuente.

Zona segura configurable left/right/top/bottom0–0,4 del lienzo. ASS/quemado usa márgenes y ancla de posición dentro de ese rectángulo; se conservan los controles de tamaño/posición existentes. No hay una zona universal para todas las apps/redes.

**Seleccionable:** MP4 mov_text/SRT conserva texto y milisegundos; no garantiza márgenes, tipografía, colores o karaoke. **Quemado:** ASS se rasteriza en el vídeo y ya no es una pista editable; sus tiempos se redondean a centésimas. Cambiar límites sin modificar cues no requiere render. Cambiar zona solo invalida el render quemado, porque el seleccionable no incorpora esa geometría.

## Contratos

`subtitle_layout` con `layout:{max_lines,max_chars_per_line,max_cps,safe_area:{left,right,top,bottom}}`; `layout:null` quita ajustes explícitos. `GET /api/studio/editor/{pid}/subtitles/quality` / acción `subtitle_quality` del puente3.8.0 entrega informe y hash. `subtitle_reflow` requiere `reviewed:true` e `input_edl_sha256` del informe vigente. Revisión optimista e historial normales; recuperar estado antes de repetir escrituras inciertas.

## Validación

9 casos nuevos focalizados aprobados: política/errores atómicos, propuesta sin perder tokens/tiempos, historial/reapertura, hash obsoleto, identidad soft/burn, ASS seguro y puente. Panel/API reales en copia aislada4778: guardar, revisar, aplicar, undo/redo/reapertura; cero erroresJS.

Dos exportaciones **nuevas necesarias para este formato** de4s con los mismos medios propios/impactos existentes: seleccionable tras reflow y quemado con zona nueva. Cues técnicos explícitamente QA, no una transcripción inventada. `mov_text` extraído coincide exactamente; quemado no contiene stream de subtítulos y el texto es visible. En fotograma1,25s, diferencia visible del texto en caja(233,211)–(372,269), dentro de zona configurada. Frame inspeccionado. Payload AAC de ambas salidas idéntico, sin repetir medición de audio. No se acredita escucha humana ni todos los tamaños/fuentes a partir de esta muestra.

[Evidencia](EDITOR_SUBTITULOS_LECTURA_EVIDENCIA_20261126.json). QA4778 cerrado. Pendientes: karaoke con tiempos reales, estilos por cuenta dependientes168, activación agrupada4750 y valoración humana. La cola continúa; no se cierran107/115/129 por esta ampliación. PR2 en borrador, originales/configuración/.venv/ComfyUI intactos.
