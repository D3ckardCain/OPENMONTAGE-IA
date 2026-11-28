# AI YouTube Shorts Generator — evaluación #85

24-11-2026, #3. Nombre genérico: identificación candidata de la captura, no certificada. [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator/tree/4cfa5f00d65b4dca05bec92c67bfeb3af66cdfb3). README, LICENSE, requirements y `shorts_generator/local/clipper.py` revisados. Sin manifiesto semántico de release en los archivos revisados: commit es versión reproducible; no inventar número.

MIT del código con avisos; vídeos, ASR, cascadas/paquetes y servicios tienen licencias/derechos propios. Python3.10+, FFmpeg para modo local, requirements-local: yt-dlp>=2024.1.1, faster-whisper>=1.0, OpenCV>=4.8, SDK OpenAI/Gemini. Windows requiere ejecutables/wheels/codecs compatibles; ejemplos source/xargs son Unix, no prueba Windows. GPU opcional para ASR, RAM/disco dependen de fuente/caché; no mínimo medido para laptop.

README titula local/offline, pero **ranking local usa OpenAI o Gemini remotos**; modo predeterminado usa MuAPI. También reconoce pago por API. No cumple cadena$0/offline tal cual, incluso con archivo local. Reutilizar Ollama existente solo como diseño futuro, no compatibilidad upstream probada. Descargar YouTube necesita red/derechos; se excluye. ASR puede descargar modelo si falta; no ejecutarlo.

## Código y contraste

Local crop usa Haar sin modelo adicional, toma cara más grande, suaviza con0.15 y conserva último centro cuando no detecta. Eso no identifica al hablante ni resuelve multihablantes/deportes. Usa fps de captura (fallback30), no garantiza PTS VFR. Cache de transcripción por basename/mtime y de vídeo por ID no demuestra identidad por contenido/parámetros; puede quedar obsoleta.

**OpenMontage ya tiene** `tools/analysis/face_tracker.py` (MediaPipe/Haar, JSON) y `tools/video/auto_reframe.py` (trayectoria suavizada/padding/centro), además ASR/FFmpeg/Ollama y E03/E04. No añadir tracking ni crop como carencia nueva; evaluar errores y calidad por separado. PeakCut#44, WhisperX#72 y PySceneDetect#73 ya cubren candidatos/alineación/límites.

| Grupo | Aceptación futura útil |
|---|---|
| E04 | Datos de cajas/tiempos sintéticos: cara ausente/múltiple/cambio de plano no producen salto injustificado ni crop fuera de límites; método/fallback e incertidumbre explícitos. Mantener PTS/fps racional y política de selección del sujeto; no declarar seguimiento perfecto por pasar esquema. |
| E03 | Candidato con fuente/hash/intervalo/motivo/modelo; deduplicación preserva rechazados y frases completas. Score0–100 no predice viralidad. Llamada Ollama real y mock etiquetados. |
| E05 | Caché por hash de fuente+modelo+idioma+parámetros/revisión, no solo nombre/mtime. Dos archivos homónimos y transcripción obsoleta no reutilizan recibo equivocado; error por clip no marca lote completo. |
| B06/B07 | Calidad de encuadre/selección y fuentes reales requieren fase posterior; APIs de pago excluidas, sin nuevo downloader/ASR. |

Evaluación completa; no adopción integral. Sin instalar, generar clips, cargar modelos ni modificar configuraciones.
