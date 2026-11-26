# Conjuntos de la lista completa — avance provisional

Corte: 527/651 rutas iniciales comprobadas; los dos auxiliares nuevos se registran aparte.

Localizado ≠ verificado ≠ operativo. Los grupos comparten recursos. No se repiten pruebas aprobadas.

| Catálogo / conjunto | Referencias localizadas | Verificadas | Estado funcional |
|---|---:|---:|---|
| additional.json / qwen-edit | 1/1 | 0/1 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| additional.json / faster-whisper | 5/5 | 5/5 | Previously approved Portuguese ASR; do not repeat |
| additional.json / chatterbox | 6/6 | 6/6 | Regional samples active; generic model distinct. Turbo awaits authorized reference>5s |
| additional.json / cosyvoice | 19/19 | 19/19 | Resources deferred by user; not loaded |
| additional.json / depth | 2/2 | 2/2 | Código depth_anything_v2 no preparado en el entorno aislado; no carga |
| additional.json / qwen3 | 14/14 | 14/14 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| additional.json / qwen-vl | 15/15 | 14/15 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| additional.json / wan-vace | 11/11 | 9/11 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| additional.json / wan-camera | 5/5 | 3/5 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| additional.json / aligner | 9/9 | 9/9 | Modelo1,84GB: margen CPU2×peso+1GiB≈4,74GB supera4,13GB libres; falta qwen_asr |
| additional.json / birefnet | 6/6 | 6/6 | Código local usa eval para backbones; revisión específica y torchvision/timm compatibles pendientes antes de ejecutar |
| additional.json / grounding-dino | 8/8 | 8/8 | Ensayo CPU offline acotado90s agotado dentro de forward; sin respuesta; no operativo acreditado |
| additional.json / florence | 12/12 | 12/12 | Modelo1,55GB: margen CPU conservador2×peso+1GiB≈4,18GB supera4,13GB libres observados; no cargar |
| additional.json / siglip | 7/7 | 7/7 | CPU forward exceeded90s twice with watchdog; no further retries |
| additional.json / m2m100 | 8/8 | 8/8 | Modelo1,94GB: margen CPU2×peso+1GiB≈4,95GB supera4,13GB libres; falta sentencepiece |
| additional.json / parakeet | 7/7 | 7/7 | Modelo2,51GB: margen CPU2×peso+1GiB≈6,09GB supera4,13GB libres; no cargar |
| additional.json / smolvlm | 15/15 | 14/15 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| additional.json / wan-control | 3/3 | 1/3 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| additional.json / wan-s2v | 14/14 | 11/14 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| additional.json / voice-design | 3/3 | 3/3 | Previously approved C:VoiceDesign sample; do not repeat; old D:variant differs |
| additional.json / dwpose | 2/2 | 2/2 | No se localizaron onnxdet.py/onnxpose.py en custom_nodes revisados; no carga |
| additional.json / lama | 1/1 | 1/1 | Falta entorno/fuentes saicinpainting; no carga |
| additional.json / silero | 2/2 | 2/2 | Actual ONNX CPU offline smoke passed once; registered Studio adapter |
| additional.json / minilm | 10/10 | 10/10 | Actual CPU offline inference passed once; registered Studio adapter |
| additional.json / ocr-latin | 4/4 | 4/4 | Falta stack PaddleOCR/PaddlePaddle compatible Windows; no está operativo |
| additional.json / ocr-det | 4/4 | 4/4 | Mismo entorno Paddle pendiente; no duplicarlo |
| base.json / wan | 12/12 | 6/12 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / cosmos | 3/3 | 1/3 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / ltx-legacy | 4/4 | 0/4 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / mochi | 3/3 | 1/3 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / cogvideo | 16/16 | 14/16 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / kandinsky | 29/29 | 28/29 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / longcat | 28/28 | 18/28 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / longcat-avatar | 28/28 | 16/28 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / magihuman | 93/93 | 45/93 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / ltx23 | 9/9 | 6/9 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / ltx25 | 11/11 | 7/11 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / hunyuan15 | 7/7 | 4/7 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / framepack | 26/26 | 20/26 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / h3 | 5/5 | 1/5 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / qwen-image | 4/4 | 1/4 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / flux-klein | 3/3 | 2/3 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / z-image | 3/3 | 1/3 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / kokoro | 57/57 | 57/57 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| base.json / qwen-tts | 12/12 | 12/12 | Conjunto0.6B distinto de1.7B; recursos presentes, prueba propia pendiente; no repetir las aprobadas1.7B |
| base.json / acestep | 27/27 | 27/27 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| madlad.json / madlad | 7/7 | 6/7 | No functional claim; finish verification, review actual runtime dependencies/memory/license before one bounded load |
| qwen17.json / voice-design | 12/12 | 12/12 | Previously approved C:VoiceDesign sample; do not repeat; old D:variant differs |
| qwen17.json / qwen-tts-17b-base | 12/12 | 12/12 | Previously approved Base1.7B sample; do not repeat |

Los márgenes CPU son filtros conservadores previos, no picos medidos ni una afirmación de incompatibilidad absoluta. No se intentó descargar un stack redundante ni cargar dos familias a la vez. La memoria libre varía.

Las familias generativas pendientes necesitan además grafo/runtime compatible, licencia y presupuesto antes de cargar. La presencia del ZIP/peso no acredita esas condiciones. CosyVoice sigue aplazado por recursos; Audio8 se documenta por separado en #175.

La columna SHA256 oficial del CSV queda vacía si upstream publica únicamente Git blob SHA1. Un SHA256 local no se convierte en oficial por haber sido calculado. La inspección de cabecera no certifica compatibilidad.
