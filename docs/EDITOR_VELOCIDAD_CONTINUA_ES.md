# Rampas continuas de velocidad

Entrega P1 de #174 desde113e632. El clip permanece entero: velocidad continua **lineal entre puntos en reloj fuente**, con aceleración y desaceleración, no una sucesión de cortes constantes. No es interpolación de imagen/optical flow, Bézier ni garantía de conservar tono.

Seleccionar vídeo → **Rampa continua · aceleración y desaceleración**.2–8 puntos incluyendo entrada/salida, separados≥1ms, velocidades0,25–4. El gráfico muestra la velocidad solicitada; **Revisar** calcula sin escribir, informa duración cuantizada y límites. Confirmar explícitamente el modo de audio y aplicar realiza una operación reversible. Undo/redo, guardar/reabrir conservan todos los puntos/mapa. Fuente original reproduce la fuente; usar vista previa preparada/exportación para ver y oír la rampa.

## Un contrato temporal

`continuous-source-speed-linear-v1`, compartido por API/Studio/agente y todos los recursos vinculados. Integración analítica `∫ds/v(s)` —logaritmo por tramo lineal— e inversa con exponencial. Se ajusta uniformemente al número entero de fotogramas final, sin truncar intervalos fuente. La velocidad efectiva puede diferir ligeramente de la solicitada por esa cuantización. Previsualización y exportación usan la misma función `setpts`, no dos relojes.

Audio usa la inversa del mismo mapa por muestra48kHz, interpolación PCM continua en bloques8192 y filtro previo de paso bajo según aceleración máxima. **Este modo cambia el tono.** Se denomina `continuous_resample_pitch_changes`: no se presenta como Rubber Band, WSOLA ni preservación de formantes/tono. El renderer preparado ya dispone de NumPy/FFmpeg; no se instala nada. Decodifica solo los intervalos necesarios, con el Control cancelable existente, y procesa una muestra acotada en memoria por bloque; elimina sus PCM propios al terminar. Procedencia de fuentes, modo, muestras/canales y filtro quedan en el recibo.

Vídeo, audio nativo y adicional y capas estáticas comparten exactamente el objeto de mapa. No se dividen pistas ni se reinician compresores por cambios internos de velocidad. Títulos, cues y marcadores pasan al nuevo reloj; texto/fuentes/ASR originales se conservan. Reloj de palabras usa el mapa solo en clips nuevos con `time_warp`; el camino constante previo permanece igual. Comparar Color y navegación fuente↔montaje también lo usan.181vectores Python/JS dan error máximo8,88e−16s; pruebas de impulsos PCM comprueban anclajes con la inversa analítica. Esto es precisión numérica, no medición acústica nueva.

API POST `/{pid}/smooth-speed-plan` (solo lectura); agente `studio_project_edit`3.12 acción `smooth_speed_plan`, payload `ramp:{id,points,audio_mode}`. Escritura compartida:

```json
{"operation":"clip_smooth_speed","revision":12,"id":"ID_CLIP","points":[{"source_seconds":0,"speed":0.75},{"source_seconds":2,"speed":1.5},{"source_seconds":4,"speed":0.75}],"audio_mode":"continuous_resample_pitch_changes","reviewed":true,"input_edl_sha256":"HASH_PROPUESTA"}
```

Revisión/huella obligatorias, sin reenvío automático tras error incierto. Usar GET para recuperar estado antes de repetir una escritura. No hay una copia editable distinta para el agente.

## Límites explícitos de esta entrega

Un mapa continuo activo, máximo30s de fuente/120s de salida; audio vinculado afectado≤60s. Volumen conserva sus tiempos absolutos. Capas animadas afectadas, fundidos o transiciones requieren remapeo específico y se rechazan; no se eliminan. El audio remuestreado tiene límites de interpolación/filtro y puede cambiar timbre: no se promete naturalidad ni calidad de mastering. Conservar tono requiere otro modo validado, no activar un flag sin evidencia.

Después de aplicar, cambiar la curva/duración/orden/FPS o añadir recursos que alteren el mapa exige deshacer primero. No se declara edición arbitraria posterior del mapa. Color, mezcla, texto y estilos siguen editables; una capa estática puede cambiar geometría conservando su reloj. Operaciones incompatibles fallan con un mensaje, no invalidan silenciosamente las referencias. La curva escalonada anterior se conserva como función distinta y su evidencia no se repite.

## Prueba real única

Copia portuguesa aislada, mismos recursos/116palabras guardadas, capa y título/marcador de QA y WAV propio ya sintetizado. UI/API4788: revisar/aplicar, undo/redo, guardar/reabrir. Un único MP4 nuevo para ambos tramos, intento `6eea986c1ab04988a78b8d74d726c2b9`:92fotogramas/25fps,3,68s; audio3,68s/176640muestras48kHz no nulas.16palabras completas conservadas y1parcial previa sigue excluida. Textos/tiempos seleccionables extraídos coinciden con EDL≤1ms. Capas y audio comparten mapa; no se atribuye alineación acústica independiente a esos datos.

Anclajes de vídeo en0,88/1,84/2,8s cotejados con fuente según inversa. Diferencia RGB media2,50–2,57/255 en ROI sin overlays; coincidencia dentro de1fotograma de fuente(1/24s), compatible con muestreo de fuente/salida y compresión, no identidad de píxeles ni optical flow. Fotogramas inspeccionados con título/capa.

Reproducción en **Studio QA4789**:92frames/0descartes hasta el final, búsqueda0–3,68s, subtítulo portugués visible. El primer arranque de QA solo cambiaba `studio.PROJECTS_DIR` y dejaba `/media` en otro root; se corrigió el **harness** fijando `OPENMONTAGE_PROJECTS_DIR` antes de importar. Se reutilizó el MP4, sin nuevo render ni cambios de configuración de Studio normal. No se confunde ese ajuste QA con activación4750.

13casos nuevos focalizados pasan,181vectores de conformidad y esta prueba AV. No se repiten las36pruebas anteriores ni las de velocidad escalonada/CI. Sin ASR, síntesis, inferencias, modelos ni descargas. Recibos `.runtime/qa/smooth174/`, evidencia `EDITOR_VELOCIDAD_CONTINUA_EVIDENCIA_20261126.json`. Escucha humana sigue pendiente; A/B anterior intacta. #186 conserva72frames y bloqueo intermitente abierto, sin nuevas ejecuciones.
