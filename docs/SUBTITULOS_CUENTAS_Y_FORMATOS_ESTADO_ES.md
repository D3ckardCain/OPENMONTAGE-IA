# Subtítulos: cuentas y formatos — revisión desdeb2e69c5

Código contrastado: `studio_editor.py`, `studio_editor_render.py`, `studio_subtitle_layout.py`, `studio_subtitle_karaoke.py`, rutas del editor, puente y especificación completa #168. Sin modificar configuración ni asignar proyectos históricos.

| Salida actual | Acreditado y límite |
|---|---|
| MP4 seleccionable | `mov_text`, texto/tiempos/idioma; no garantiza colores, zona ni karaoke. Pruebas/evidencia5dfb85d/b24a65f ya aprobadas. |
| MP4 quemado | ASS rasterizado por FFmpeg, zona/estilo y palabras con tiempos guardados; no tiene pista seleccionable. Misma evidencia previa. |
| SRT | Texto/tiempos externos, sin estilos ni resaltado. No es un subtítulo quemado. |
| ASS | Estilo/zona y eventos por palabra; archivo externo no equivale por sí solo a exportación quemada ni a soporte universal del reproductor. |

No se ejecutan otra vez exports/ASR/CI por esta revisión. Ya se extrajeron cues seleccionables, se verificó ausencia de stream de subtítulos quemado, píxeles de palabra y payload AAC equivalente. Español representativo de #107 sigue pendiente; portugués no lo sustituye. El editor manual actual entrega MP4; otros contenedores no se declaran soportados por esta tabla.

**Pendiente real: estilos nombrados/versionados por cuenta.** La configuración actual es por proyecto; no existe propiedad `account_id` integrada en editor, rutas, listados y agente. #168 exige denegar cruces también en medios/búsquedas/SSE/recibos, contextos de trabajos capturados al encolar y migración reversible a sin-asignar. Un diccionario global de presets o un filtro de interfaz no satisface ese requisito. No se ha creado uno con etiqueta engañosa ni repartido históricos por tema/idioma.

Secuencia concreta de implementación: base de cuenta/propietario #168 → almacén privado con ID estable/nombre/revisión/estilo y procedencia de fuentes → proyecto fija versión y copia efectiva editable → comandos aplicar/undo/redo/reapertura compartidos con agente. Modo de exportación es selección explícita del proyecto, no efecto lateral oculto de aplicar un estilo. Al elegir mov_text/SRT se advierte que estilo/resaltado no se conserva; no se promete quemado sin exportar. Fuentes locales disponibles, sin descargas ocultas ni sustituciones silenciosas.

Aceptación pendiente: dos cuentas con estilos homónimos y proyectos distintos, listados y acceso cruzado rechazados por backend/agente, proyecto fijado a versión sin cambios retroactivos, aplicar/deshacer/reabrir, recuperar contexto al cambiar cuenta y comprobar ambos formatos reutilizando recursos. La migración no asigna ni mueve originales por conjetura. Dependencia técnica registrada en #168/#174; no implica permiso rutinario ni bloquea velocidad/otras mejoras independientes.
