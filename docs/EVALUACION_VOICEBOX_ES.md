# #104 — Voicebox

Evaluación documental, 25-11-2026 UTC; comentario7146236065 reutilizado.
[Fuente fijada](https://github.com/jamiepine/voicebox/tree/8dc2a5bfe0f783edd53f8a346a22dcad9c1fb793),
package0.6.0, código MIT. No se instala, genera voz ni activa micrófono/hotkeys.

## Qué aporta y qué ya existe

Studio dispone de adaptadores Kokoro, Qwen y Chatterbox; mantener sus perfiles y
recursos inventariados. Útil: tomas/versiones y edición de historias, no otro
estudio TTS. `backend/routes/stories.py` documenta agregar/mover/recortar/dividir,
duplicar, volumen, orden, versiones y mezcla exportada. Tiempos en milisegundos
deben convertirse al contrato temporal del montaje con origen y redondeo.

`backend/routes/generations.py` tiene generate/retry/version/cancel y estados.
“Cancellation requested” durante ejecución no demuestra interrupción del cálculo
GPU. Reutilizar la distinción cancelación solicitada/transporte/cómputo/parcial.
El registro MCP inspeccionado tiene **cuatro herramientas**: voicebox_speak,
transcribe, list_captures y list_profiles; no expone toda la edición de stories.
REST existente no demuestra paridad MCP ni control del mismo documento de Studio.

## Licencias de variantes, no del nombre comercial

Metadatos oficiales HF consultados sin descargar pesos. Estos pins sirven para
evaluación y no sustituyen revisiones/huellas del inventario previo.

| Recurso oficial / revisión | Condición declarada y español |
|---|---|
| Qwen/Qwen3-TTS-12Hz-1.7B-Base `fd4b254389122332181a7c3db7f27e918eec64e3` | Apache2; español; Base distinto de CustomVoice/VoiceDesign |
| Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice `0c0e3051f131929182e2c023b9537f8b1c68adfe` | Apache2; no sustituir voces por equivalencia de familia |
| Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign `5ecdb67327fd37bb2e042aab12ff7391903235d3` | Apache2; diseño distinto de clonación |
| hexgrad/Kokoro-82M `f3ff3571791e39611d31c381e3a41a3af07b4987` | Apache2; reutilizar es→e, catálogo y prefijos de lengua existentes |
| ResembleAI/chatterbox `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18` | MIT; Multilingual incluye español; V3 regional requiere compatibilidad #96 |
| ResembleAI/chatterbox-turbo `749d1c1a46eb10492095d68fbcf55691ccf137cd` | MIT; inglés, tags expresivos no universales |
| YatharthS/LuxTTS `527f245a276a0eb42ea103a7a512bcfd771eb9b6` | Apache2; inglés, no calidad española acreditada |
| HumeAI/tada-1b `39a987c813d70bc70587757c3ed82c6e9853077d` | Llama3.2; inglés |
| HumeAI/tada-3b-ml `713298b823669995b71fdd76ce7826eac90d81da` | Llama3.2; multilingüe incluye español |
| HumeAI/tada-codec `4413b57a1f223c6f1530a8579c24af4238718c83` | MIT del codec no elimina condiciones del modelo/tokenizer Llama |

Fuentes: [Qwen](https://huggingface.co/Qwen), [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M),
[ResembleAI](https://huggingface.co/ResembleAI),
[LuxTTS](https://huggingface.co/YatharthS/LuxTTS), [HumeAI](https://huggingface.co/HumeAI).
La licencia declarada no resuelve todos los companions ni derechos de voz de
referencia. Mirror unsloth de Llama no elimina términos originales.

Las revisiones de la tabla identifican los repositorios completos, no tags
móviles. Ejemplos directos: [Base fijado](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base/tree/fd4b254389122332181a7c3db7f27e918eec64e3),
[Lux fijado](https://huggingface.co/YatharthS/LuxTTS/tree/527f245a276a0eb42ea103a7a512bcfd771eb9b6),
[TADA multilingüe fijado](https://huggingface.co/HumeAI/tada-3b-ml/tree/713298b823669995b71fdd76ce7826eac90d81da).

## Windows, offline y aceptación

Tauri/Bun/FastAPI, Torch/MLX; Python3.12, Bun1.3.8 y toolchain Rust/WebView2
documentados. CUDA/DirectML en Windows anunciados, no probados aquí ni trasladables
al Python3.11 actual. MLX no es backend Windows. Descarga automática de binarios
CUDA/compañeros al primer uso y VOICEBOX_MODELS_DIR no garantizan offline completo.
Sin costes de API con recursos elegibles preparados; no ejecutar personalidad o
refinado LLM, dictado o nuevas inferencias. No modificar entornos existentes.

| Familia | Hardware/CPU: evidencia y límite |
|---|---|
| Qwen Base/CustomVoice/VoiceDesign | Rutas Torch CPU/CUDA documentadas; tamaño0.6B/1.7B no equivale a memoria total ni controles idénticos; no consumo/latencia Windows observados |
| Kokoro | README anuncia CPU rápido para82M; conservar backend/perfil existentes, no convertir esa descripción en benchmark local |
| Chatterbox Multilingual/Turbo | Backend y compatibilidad por loader; CPU/GPU no acreditan misma velocidad, V3 regional requiere prueba específica |
| LuxTTS | README anuncia~1GBVRAM/150x realtime CPU; cifras upstream, no mediciones en este equipo; Whisper de referencia añade dependencias |
| TADA1B/3B | Torch y companions/codec/tokenizer; tamaño3B, contexto largo y GPU no garantizan8GB; elegibilidad Llama y presupuesto de memoria pendientes |

El selector global DirectML/CPU anunciado no demuestra que todos los operadores
y motores funcionen allí. No se presupone soporte uniforme ni memoria mínima.

| ID / prioridad | Aceptación futura |
|---|---|
| E16/E01 P1 | Perfil motor/variante/voz/lengua/licencia/recursos; errores de tags no soportados, sin fallback oculto ni descargas |
| E05 P0 | Versiones y parciales con propietario, cancelación honesta y reanudación sin repetir herramientas completadas |
| E04/E06 P1 | Spans, pausas, crossfades y duración real convertidos a tiempo común; undo/reopen y mismo proyecto para agente/usuario |
| E10/E02 P1 | Capabilities reales de REST/MCP y controles operativos del Audio actual; no otra UI ni paridad inventada |
| B08/B06 | Licencias Llama/companions, memoria y escucha española/resultado real pendientes |

Evaluación concluida; ningún motor nuevo queda instalado o validado por este informe.
