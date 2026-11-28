# PeakCut frente a OPENMONTAGE: evaluación #44

Fecha: 24-11-2026 UTC. Revisión documental/estática; sin instalar, importar ni ejecutar
PeakCut, descargar pesos, capturar directos, inferir o generar medios. Snapshot oficial
`haziqahmedqasmi/PeakCut@39c32a878648619e981b57af608ba4571a82247f`, también HEAD main
en la consulta. OPENMONTAGE comparado con `d401390` y los archivos locales correspondientes.
No se modifican GitHub Dark, aplicaciones, entornos, configuraciones o PR #2 borrador.

## Decisión

Reutilizar OPENMONTAGE como sistema principal. Tomar ideas y, si se implementan,
funciones pequeñas con atribución: ajuste temporal a frases, layouts ASS y gestión
de segmentos de directo. No incorporar el servidor PeakCut ni su orquestador completo.
Prioridad: español original, Ollama ya conectado y ASR multilingüe local existente.
Una función presente en código no equivale a rendimiento o calidad audiovisual probados.

## Comparación concreta

| Área | PeakCut revisado | OPENMONTAGE existente | Carencia útil y decisión |
|---|---|---|---|
| Momentos | `brain.find_clips`: ventanas solapadas, candidatos puntuados por LLM, ajuste a palabras/frases y descarte de solapamientos; alternativa por volumen declarada | `pipeline_defs/clip-factory.yaml` y sus directores ya piden candidatos, clasificación, contexto suficiente y cortes por frase; `scene_detect`, transcripción y Qwen/Ollama están conectados | Falta un contrato único de candidatos trazables y validación mecánica de límites/solapamientos, con API de revisión. La valoración editorial debe seguir en el agente, no en un orquestador Python nuevo |
| Subtítulos por palabra | `render.build_ass`: eventos ASS, palabra activa, estilos, medidas de fuente y título | `subtitle_gen` produce SRT/VTT/JSON por palabra y karaoke; `remotion_caption_burn` y CaptionOverlay ya animan palabras | No reconstruir ASR/subtitulador. Evaluar un adaptador ASS/FFmpeg opcional y zonas seguras; resolver disparidad con HyperFrames. SRT con negrita no garantiza el aspecto de un render ASS |
| Vertical | Layouts fill/fit/blur, recortes laterales, dos mitades apiladas y gameplay/facecam | `auto_reframe` incluye 9:16,1:1,16:9,4:5,21:9 y trayectoria de rostro; `video_stitch` ya tiene PiP y apilado | Falta una interfaz de presets que comparta geometría, subtítulos y preview/export. No copiar otro reencuadrador. Distinguir detección de caja facecam de seguimiento temporal de sujetos |
| Directos | `live.Session`: yt-dlp resuelve URL; FFmpeg guarda segmentos TS nominales de6s; CSV aporta reloj, retención, reinicios y márgenes de recorte | `video_downloader` ingiere URL bajo límite; no se halló controlador persistente de captura continua con buffer circular en tools/lib revisados | Es la ampliación funcional más diferenciada, después del contrato de clips: captura separada, acotada y cancelable, con índice durable. Descargar un vídeo o resolver un HLS no acredita capturar un directo con recuperación |
| Cola | Cuentas/creadores, sesiones y publicación | `production_queue`, checkpoints, recibos, parada y recuperación existentes | Reutilizar cola/recibos. No importar otra base de cuentas ni habilitar publicación automática |

Fuentes upstream: [selección](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/studio/brain.py),
[ASS/layouts](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/studio/render.py),
[directos](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/studio/live.py),
[facecam](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/studio/facecam.py).
La retención upstream borra segmentos viejos y usa procesos propios: adaptar el diseño,
sin copiar borrados sobre rutas existentes ni reutilizar su carpeta de datos.

## Español, Ollama y ASR: diferencias que impiden adoptar sin adaptación

- `fetch_model.MODELS` solo tiene en/ar. Inglés puede descargarse automáticamente;
  su SHA256 esperado está vacío en esa tabla. No es soporte integrado de español.
- `brain.KEEP_LANGS=(en,hi,ur)` y `english_captions` orientan la salida al inglés.
  Traducir español y repartir las palabras traducidas uniformemente en una frase
  no produce alineación acústica española. Mantener lengua original y separar una
  traducción opcional con procedencia y tiempos de alineación propios.
- PeakCut admite Ollama sin clave por `/v1/chat/completions`; su configuración por
  defecto selecciona Gemini y admite varios proveedores/modelos. No importar ese
  selector. Usar `LocalAgent.chat`, validación local, cancelación y sesiones actuales.
  Volumen solo es una señal heurística, no selección semántica ni promesa de viralidad.
- OPENMONTAGE tiene `transcriber` con Faster-Whisper, palabras y `language`, pero su
  carga por nombre puede descargar un modelo ausente. El adaptador preparado
  `model_faster_whisper`/`model_adapter_worker.py` usa rutas locales y
  `local_files_only=True`; priorizarlo. Verificar qué salida expone palabras y pasar
  `es` explícito cuando corresponda; no instalar otro ASR ni asumir que presencia
  del adaptador acredita precisión en español. WhisperX/diarización no son requisito.

Fuentes: [modelos](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/studio/fetch_model.py),
[idiomas/captions](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/studio/brain.py#L543),
[proveedores](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/studio/ai.py),
[configuración](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/studio/config.py).

## Licencias y dependencias

Código PeakCut: [MIT, copyright2026contributors](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/LICENSE).
Si se copia/adapta código, conservar licencia y avisos en THIRD_PARTY_NOTICES con
archivo, commit y cambios. OPENMONTAGE conserva su AGPLv3; no se relicencia el producto
completo a MIT. Las fuentes Poppins/Anton/Archivo Black incluyen OFL propios en
`studio/fonts`; conservarlos si se incorporan fuentes. El texto upstream atribuye
los pesos Parakeet/FastConformer a CC-BY-4.0, pero no se auditó cada archivo/model card;
licencia MIT del servidor no cubre pesos ni contenido capturado. No se necesitan esos
pesos para la propuesta española. Revisar FFmpeg según build y codecs, y cada paquete
si se redistribuye; esta evaluación no incorpora binarios o código externo.

[requirements](https://github.com/haziqahmedqasmi/PeakCut/blob/39c32a878648619e981b57af608ba4571a82247f/requirements.txt)
fija FastAPI0.162.5, httpx0.28.1, NumPy2.2.6, sherpa-onnx2.0.1,
soundfile0.14.0, SQLAlchemy2.0.57, psycopg/psycopg-binary3.3.9,
uvicorn0.54.0, yt-dlp2026.10.21 y Pillow11.3.0. README pide Python3.10+ y FFmpeg;
SQLite local, PostgreSQL/despliegue remoto opcionales. No son dependencias nuevas
recomendadas para OPENMONTAGE: componentes concretos pueden usar el FFmpeg, yt-dlp,
ASR y Ollama existentes. Evitar colisión del paquete `studio`; si se evalúa una copia
ejecutable en el futuro, entorno/proceso separado y API acotada. El comprobador de
actualizaciones tiene `PEAKCUT_UPDATE_CHECK=0`; no añadir consultas automáticas.

## Tareas de implementación propuestas, aún no ejecutadas

| Prioridad | Entrega futura | Reutilización y criterios de aceptación |
|---|---|---|
| P0 | Contrato `clip_candidates` y revisión Studio | Fuente/sha, lengua, transcripción/hash, inicio/fin, motivo y modelo reales; normalizador valida finitos, duración, reloj y duplicados. Agente ordena y justifica en español; aprobación conserva candidatos rechazados. Fixtures sin LLM y transporte Ollama simulado; no afirmar viralidad por puntuación |
| P0 | Puente ASR local→palabras→candidato | Reusar worker preparado; rutas existentes, sin descarga; `es`, signos ¿¡, tildes, pausas, entrada sin voz, idioma incierto, offsets absolutos/relativos y cancelación. Validación de calidad con audio autorizado queda para otra fase |
| P1 | ASS y presets de encuadre opcionales | Reusar JSON de palabras, FFmpeg y componentes de composición; pruebas textuales de escape ASS/rutas, Unicode, redondeo, zonas seguras, dimensiones/SAR y layout. Inspección visual/exports solo en fase autorizada; no degradar karaoke a SRT sin declararlo |
| P1 | Captura de directo con buffer acotado | Reusar ejecutables existentes; índice de segmentos finalizados, reloj real y discontinuidades, cuotas bytes/tiempo, pines de clips, stop/reanudación, URL expirada, falta de audio, disco lleno y limpieza solo de su UUID. Primero mocks y listas sintéticas offline; no conectar un directo en esta evaluación |
| P2 | Señales de chat y cola por creador | Optativas, separadas de selección editorial; procedencia, privacidad, límites y sesiones no automáticas. Captura real requiere red y permiso sobre el contenido; funcionamiento offline significa procesar material ya local, no obtener un directo sin red |

## Verificación de esta evaluación

Se leyeron código y licencias del commit fijado y fuentes locales enumeradas; búsqueda
de captura persistente acotada a tools/lib/tests, sin afirmar ausencia universal.
Pruebas existentes identificadas: `test_transcriber_device_selection`,
`test_subtitle_timestamps`, `test_remotion_caption_burn`,
`test_auto_reframe_display_geometry`. No se ejecutaron porque esta entrega solo añade
documentación; tampoco se probaron rendimiento, ASR, seguimiento o directos. Próximo
paso autorizado en otra tarea: implementar el contrato P0, no instalar PeakCut entero.
