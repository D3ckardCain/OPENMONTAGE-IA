# Medición persistente de la mezcla final — #174

La revisión encontró un medidor ya existente en `editor.js`: `AudioContext`/`AnalyserNode` muestra RMS y pico mono de una ventana de 2048 muestras del reproductor. Puede estar reproduciendo una fuente o un montaje. Se conserva: no acredita sonoridad integrada ni máximos del render completo, no distingue por sí solo render vigente y no entrega un recibo al agente.

La ampliación **Medir mezcla final guardada** analiza bajo demanda el audio codificado de un render completado que coincida con el montaje actual. Incluye EQ, compresor, mezclador, ducking y limitador ya aplicados, y las variaciones del códec. No analiza la fuente original, no vuelve a renderizar, no normaliza ni modifica la EDL, originales o configuración.

## Controles y límites

En Audio, abrir el panel, indicar inicio y opcionalmente duración. Se mide un máximo de **120 s** por consulta, con timeout de proceso de **60 s**. Por defecto se mide todo si cabe, o los primeros120s marcados **PARCIAL**. Cobertura en reloj del render codificado, no del archivo fuente. No se extrapolan LUFS de una selección al vídeo completo.

Muestra RMS global y pico de muestra en dBFS, true peak en dBTP, sonoridad integrada en LUFS y rango de sonoridad en LU. Se utilizan `astats` y `ebur128=peak=true` del FFmpeg existente. Las precisiones de resumen de FFmpeg limitan la de true peak/LUFS; una muestra de4s y su LRA no representan un programa largo. Silencio se registra como `null` para −∞ y sonoridad bajo puerta se identifica expresamente, sin NaN/Infinity en JSON. No impone una norma LUFS universal por red; el objetivo de normalización configurable existente no se cambia.

Una preview ya codificada también puede medirse, identificada como **Preview**; una exportación figura como **Exportación**. No es un medidor en directo. Cambiar la EDL vuelve histórica la medición: el panel exige preparar y medir el render actualizado.

La operación ocupa temporalmente el proyecto con el mecanismo existente de tareas de exportación para que las comprobaciones de trabajos activos/runtime la detecten; la lectura no altera el proyecto editable. **Cancelar medición** detiene únicamente el decodificador propio mediante la terminación acotada ya utilizada por el renderer. No se publica resultado parcial. Si no se confirma el cierre del proceso, conserva el bloqueo y comunica el fallo; no finge cancelación correcta. Un reinicio deja recibos incompletos como interrumpidos, sin reintento automático.

La caché incluye contrato de medición, SHA declarado por el exportador, identidad física/bytes/mtime del render, intervalo, y ruta/identidad del ejecutable FFmpeg. No vuelve a hashear modelos ni el ejecutable. Estos metadatos son un criterio de reutilización local, no una verificación criptográfica independiente del MP4 frente a manipulación externa. Un cambio durante la lectura invalida el resultado.

## API y agente

Capability `mix_meter`. El puente `studio_project_edit`3.7.0 comparte el mismo servicio, sin inferencias:

```json
{"project_id":"ID","action":"mix_meter_start","request_id":"UUID_UNICO","revision":12,"meter":{"start_seconds":0,"duration_seconds":30}}
```

Después, acciones `mix_meter_status` y `mix_meter_cancel` con proyecto/request_id. API: `POST /api/studio/editor/{pid}/mix-meter`, `GET .../mix-meter/requests/{request_id}` y `POST .../mix-meter/requests/{request_id}/cancel`; inicio de agente mediante `agent-mix-meter`. Un mismo ID con otra solicitud se rechaza. Respuesta incierta: **recuperar recibo por GET**, nunca repetir automáticamente el POST. El panel guarda el ID en la sesión para **Recuperar medición** tras recargar. Los informes persisten en `artifacts/mix_meter/` y llevan origen, cobertura e identidad.

## Validación nueva

- **16 casos focalizados acreditados**: caché/idempotencia sin modificar EDL, procedencia, intervalo parcial, límites/revisión, render antiguo/alterado, fallo de decoder/lectura corta sin caché, silencio/parser, recibos de interrupción, cancelación antes/durante el decoder simulado, fallo de inicio, cierre no confirmado conservando recurso y puente agente/API. Las simulaciones no se presentan como una cancelación real nueva de FFmpeg.
- Una lectura real del MP4 activo de ducking: **192.000 muestras/canal /4s**, RMS **−36,540406dBFS**, pico de muestra **−20,925137dBFS**, true peak **−20,9dBTP**, integrada **−33,7LUFS**, LRA **0,4LU**. RMS y pico se contrastaron independientemente con los arrays decodificados ya guardados, error inferior a0,001dB, sin volver a decodificar.
- Panel/API reales en copia aislada4774: medir reutilizando esa caché, perder deliberadamente la respuesta y recuperar por GET con **un solo POST**, reabrir recibo y señalar render antiguo al editar; se deshizo la edición QA al acabar. Cero erroresJS. No se volvió a medir audio para probar la UI. QA4774 cerrado; guardas de error de arranque/limpieza posteriores a esa UI se verificaron con los casos focalizados correspondientes.

[Evidencia](EDITOR_MEDICION_MEZCLA_EVIDENCIA_20261126.json). Pendientes: activación conjunta en4750 tras confirmación manual y escucha humana; no se repitieron suites, renders del mezclador ni CI. Se mantiene la única escucha A/B existente.

Documentación oficial: [astats](https://ffmpeg.org/ffmpeg-filters.html#astats-1) y [ebur128](https://ffmpeg.org/ffmpeg-filters.html#ebur128-1). Entrega local con costo0, sin dependencias nuevas. PR#2 en borrador.
