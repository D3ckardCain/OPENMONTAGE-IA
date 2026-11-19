# Análisis de referencias dentro de OPENMONTAGE-IA

El análisis se ejecuta en el ordenador donde corre el Estudio. No necesita
ChatGPT, una suscripción, claves API ni servicios de pago. El agente recibe los
resultados locales al iniciar y puede consultarlos con `reference_analysis`.

## Uso del módulo

En la configuración local del Estudio se indican las rutas completas a
`ffmpeg.exe` y `ffprobe.exe`, o se dejan vacías si están disponibles en PATH.
En «Análisis local de video de referencia», se selecciona un proyecto y un
archivo de video. La carga admite hasta 500 MB; no inicia análisis por sí sola.
«Analizar con modelos locales» inicia una tarea en segundo plano, en CPU.
El informe se conserva por proyecto y puede recuperarse con «Ver análisis guardado».

Las rutas observadas del equipo de desarrollo del usuario son:

```
C:\OPENMONTAJE-IA\HERRAMIENTAS\FFmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe
C:\OPENMONTAJE-IA\HERRAMIENTAS\FFmpeg\ffmpeg-9.0.2-essentials_build\bin\ffprobe.exe
```

## Qué hace

1. Lee duración, resolución y presencia de audio con FFprobe; acepta hasta
   30 minutos por referencia.
2. Detecta cambios de plano con FFmpeg (umbral 0,3, aproximado) y extrae
   cuatro fotogramas repartidos por el video.
3. Describe los fotogramas con el adaptador local SmolVLM. La API permite
   seleccionar Qwen-VL explícitamente o desactivar visión; no cambia de modelo
   por su cuenta.
4. Extrae audio mono a 16 kHz, lo transcribe con Faster-Whisper local y permite
   descargar la transcripción en SRT con sus tiempos.
5. Usa Qwen3 local para sintetizar tema, estructura, gancho, recursos, mejoras
   originales y cuestiones que requieren investigación externa.
6. Guarda fotogramas, transcripción, observaciones, informe y carencias.

Los tres adaptadores utilizan los pesos previamente configurados y su Python
aislado, con las descargas de Hugging Face desactivadas. La tarea fuerza CPU.
Si falta un modelo o una dependencia, se devuelve un informe parcial con el
motivo. FFmpeg/FFprobe ausentes o video ilegible producen un fallo explícito.
No se usa la GPU ni se contacta ComfyUI desde este módulo. CPU y RAM sí se usan:
en equipos modestos, los modelos grandes pueden tardar o agotar memoria.

## Alcance y límites actuales

La visión analiza imágenes muestreadas, no todo el movimiento del video.
La detección de cortes utiliza un umbral heurístico; puede omitir transiciones
suaves o confundir destellos. No existe todavía análisis de música ni medición
de retención real. El campo `external_fact_check: not_performed` distingue este
análisis de una investigación de hechos con fuentes externas. Las inferencias
del modelo requieren revisión y no garantizan calidad, originalidad o monetización.

La entrada admite archivo local o enlace individual de YouTube. Las versiones
multilingües de producción todavía no están conectadas a este módulo. El análisis no inicia automáticamente un video nuevo ni publica contenido.
Las pruebas de integración usan un video sintético y respuestas simuladas de los
modelos; no constituyen validación de inferencia sobre el video del usuario.

## API

- `POST /api/studio/reference-video/{pid}/upload`: cuerpo binario, guarda fuente.
- `POST /api/studio/reference-video/{pid}/analyze`: inicia tarea; opciones
  `frames` (1–12), `vision`, `transcribe`, `summary`, `vision_model`.
- `GET /api/studio/reference-video/{pid}`: informe guardado y progreso parcial.

Solo una tarea de análisis o producción de agentes puede estar activa a la vez.
Si se reinicia el proceso, los informes pendientes aparecen como interrumpidos.
Los resultados de cada intento se conservan en su carpeta de ejecución.

## Descarga desde el formulario

El enlace se valida y normaliza a un video individual de YouTube, sin listas.
«Descargar enlace y analizar localmente» ejecuta yt-dlp con Deno y FFmpeg locales,
sin cargar configuraciones externas de yt-dlp. Limita la selección a 1080p y
comprueba que el resultado no supere 500 MB. La descarga queda en la carpeta de
su ejecución y conserva metadata de yt-dlp y un registro local `download.log`.
Una descarga rechazada o fallida no activa servicios alternativos.

En la configuración se pueden guardar `yt_dlp_path` y `deno_path`, además de
FFmpeg y FFprobe. «Detectar herramientas de referencia» consulta archivos locales,
sin ejecutarlos. Si no hay ruta configurada ni herramienta en PATH, busca en
HERRAMIENTAS bajo el repositorio y las raíces de recursos configuradas; en Windows
también comprueba C:/OPENMONTAJE-IA y D:/OPENMONTAJE-IA. Una ruta configurada inválida
se informa, no se sustituye silenciosamente. Las ubicaciones verificadas del
usuario para yt-dlp.exe y deno.exe están en C:/OPENMONTAJE-IA/HERRAMIENTAS/yt-dlp/.

El panel permite elegir SmolVLM o Qwen-VL y desactivar visión, transcripción o
síntesis. No cambia de modelo cuando falta uno. Los informes de otro proyecto se
limpian del panel al cambiar la selección para evitar confundir resultados.

## Verificación de este bloque

95 pruebas de contratos, integración y extracción con video sintético pasaron
localmente. La descarga se simuló y no se descargó el video del usuario aquí.
Los modelos siguieron simulados. Las dos pruebas de navegador se prepararon,
pero no pudieron ejecutarse localmente por restricciones de sockets de Chromium;
no se presentan como aprobadas. El workflow de GitHub añade los contratos nuevos
y conserva la prueba de interfaz para ejecutarla en un runner compatible.

La fuente seleccionada se registra por proyecto. Repetir el análisis utiliza el
video descargado o cargado más recientemente, sin volver a descargarlo ni usar
por accidente una referencia anterior. Se rechazan rutas fuera del proyecto.
