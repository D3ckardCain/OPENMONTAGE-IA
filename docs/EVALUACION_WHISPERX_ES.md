# WhisperX: evaluación #72

24-11-2026 UTC. Main `8d8e43bf3698dd1df4b011c0f1a8dd1d468ae365` declara3.8.7rc1;
release estable v3.8.6 fijada a `3ccc17b8de34f305300f8a3fd3c9f76ba820c0d0`.
No confundir desarrollo/estable ni instalar por nombre sin lock. Solo lectura.

## Decisión y existente

No otro transcriptor. `tools/analysis/transcriber.py` ya usa faster-whisper con
word_timestamps=True y tiene paso opcional WhisperX de alineación/diarización.
Actualmente su helper carga alineador CPU con language_code=en y vuelve a segmentos
originales ante excepción; word_timestamps se obtiene antes de ese paso. No se
acredita alineación española ni ausencia de degradación silenciosa por esa presencia.
La API de diarización usada por ese código debe contrastarse con upstream actual.
E04/E16 y #68 ya cubren speakers, tiempos, perfiles y procedencia: ampliar esas
tareas con alineación forzada independiente de diarización y estado explícito.

## Fuentes/requisitos/licencias

[README main](https://github.com/m-bain/whisperX/blob/8d8e43bf3698dd1df4b011c0f1a8dd1d468ae365/README.md),
[estable pyproject](https://github.com/m-bain/whisperX/blob/3ccc17b8de34f305300f8a3fd3c9f76ba820c0d0/pyproject.toml):
Python>=3.10,<3.14, Torch/torchaudio~2.8, CTranslate2>=4.5, faster-whisper>=1.2,
NumPy>=2.1, pyannote>=4 y torchcodec0.6–<0.8 para Windows entre otros. Main hace
torchaudio opcional y tiene fallback HF: no trasladarlo sin más a estable. README
recomienda CUDA12.8 Windows para GPU y permite CPU. Driver/cuDNN/CTranslate2,
torchcodec/FFmpeg y wheels efectivos requieren prueba aislada, no modificar .venv
ni Python ComfyUI. Cifras70x o VRAM de ASR no son memoria/velocidad del pipeline entero.

[LICENSE BSD2](https://github.com/m-bain/whisperX/blob/8d8e43bf3698dd1df4b011c0f1a8dd1d468ae365/LICENSE)
con avisos; modelos/tokenizers/VAD/pyannote tienen términos propios. En
[alignment.py main](https://github.com/m-bain/whisperX/blob/8d8e43bf3698dd1df4b011c0f1a8dd1d468ae365/whisperx/alignment.py)
es→VOXPOPULI_ASR_BASE_10K_ES, fallback facebook/wav2vec2-base-10k-voxpopuli-es.
Fijar licencia/revisión de ese artefacto antes de aprovisionar, no hereda BSD2.
[diarize.py](https://github.com/m-bain/whisperX/blob/8d8e43bf3698dd1df4b011c0f1a8dd1d468ae365/whisperx/diarize.py)
usa speaker-diarization-community-1 y token/aceptación de términos para obtenerlo;
no crear cuenta, aceptar condiciones ni descargar en esta fase. Speaker label no
identifica a una persona ni elimina errores en solapes.

## Offline/$0 y carencias

Sin API pagada necesaria, anuncios cloud no usados. Offline exige ASR, alineador
español, VAD, diarizador opcional y recursos NLTK presentes. Main muestra
model_cache_only en ruta HF, pero la alineación también intenta nltk.download
punkt_tab si falta: no basta local_files_only para declarar toda la cadena sin red.
La ruta torchaudio de pesos necesita inventario separado. No llamar load_model,
load_align_model o diarize como doctor inocuo. Originales y resultados ASR previos
deben conservarse al fallar alineación; timestamp inferido/interpolado no es medido.

## Tareas propuestas

| Prioridad | Entrega / grupo | Aceptación |
|---|---|---|
| P1 | Alineación española opcional E04 | Separar ASR/alineación/speaker; lengua seleccionada vs detectada, sin hardcode en; conservar palabra sin timestamp y su estado/reason, cifras/acentos/code-switch y spans originales |
| P1 | Contrato no degradado E04/E05 | Mock de error/token ausente/modelo faltante devuelve aligned=false/diarized=false, nunca éxito completo; palabras alineadas corresponden al mismo texto/hash/offset |
| P1 | Inventario offline E01/E16 | ASR/alineador/VAD/diarizador/NLTK y revisiones/avisos; cero descargas implícitas; diarización desactivada sin términos/recursos elegibles |
| P2 | Validación futura | WER y error de alineación/DER separados de pruebas de schema; corpus español autorizado y memoria/RTF medidos frente a ASR actual, sin audio aquí |

Bloqueos de ejecución: recursos/licencias/token y compatibilidad aislada pendientes.
Contratos/mocks no requieren instalar WhisperX. No se probaron audio, calidad o GPU.
