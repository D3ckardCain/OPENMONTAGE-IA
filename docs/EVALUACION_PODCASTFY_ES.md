# Podcastfy — evaluación #86

24-11-2026, #3. [Fuente oficial](https://github.com/souzatharsis/podcastfy/tree/053b54a0917e35edb2808049499292361ccaae7b), pyproject **0.4.3**. README, LICENSE, manifiesto/requirements, usage/local_llm.md, tts/factory.py y conversation_config.yaml revisados; ejemplos no ejecutados.

Apache-2.0 código con avisos; modelos, voces, documentos, imágenes y paquetes tienen términos propios. No concede licencia a fuentes ni voces por transformarlas. Python^3.11, dependencias LangChain/LiteLLM, ingesta y audio; README menciona pip ffmpeg, pero paquete Python no sustituye ejecutable FFmpeg/ffprobe. En Windows deben localizarse binarios/codecs y wheels efectivos, permisos/temp paths; no acreditado por instalación Python. RAM/VRAM/disco dependen del LLM, TTS y longitud, sin medición local. No instalar requirements extensos en .venv.

## Local no equivale a todo offline

`is_local`/llamafile documenta **generación de guion**, con modelo local preparado; primera preparación de llamafile/modelo puede necesitar red. TTS factory lista OpenAI/Google/ElevenLabs/Edge y variantes Gemini, no Kokoro local. Edge es online; claves/servicios comerciales no cumplen operación$0 garantizada. URL/YouTube/imágenes externas requieren red/derechos. Documentos propios y motores locales preparados permiten diseñar flujo offline, pero no se valida Podcastfy de extremo a extremo aquí. No se exponen APIs ni crean cuentas.

## Reutilización y carencia

OpenMontage ya tiene lectores aislados, Ollama, pipeline podcast-repurpose, mezcla/subtítulos y perfil E16. **Kokoro ya implementa** idioma `es→e`, verificación de prefijo de voz, carga de voz local y salida24kHz (`lib/model_languages.py`, `lib/model_adapter_worker.py`). Reutilizar ese perfil/validación, no descargar voces ni crear otro catálogo. Qwen existente es alternativa elegible según sus recursos; no suponer que un filename acredita calidad o derechos.

Lo útil es un contrato de conversación **fuente→afirmación→turno→voz**, separado de la generación. No adoptar otro agente, motor de voz ni UI.

| Grupo | Aceptación futura con texto/metadatos/mocks |
|---|---|
| E06/E08 | Turnos con speaker_id, texto, pasaje/fuente/hash y estatus de evidencia; cita inventada o contradicción queda señalada, no corregida con hechos nuevos. Lengua española y nombres/cifras/negación preservados. |
| E16/E04 | Speaker estable→perfil de voz/idioma autorizado; incompatibilidad Kokoro es/e o referencia ausente devuelve error antes de job. Texto hablado/original y pausas/timing separado de duración estimada. No voz nueva por cambiar de turno. |
| E05 | Segmentos/turnos con IDs y recibos; fallo en uno conserva los demás, cambio de fuente/voz invalida dependientes. Mock de diálogo largo respeta límite y no trunca una afirmación ni declara audio generado. |
| B07/B08 | Fuentes, licencias y modelos/voz/recursos Windows completos pendientes antes de cualquier adopción; no fallback online. |

Multilingüe declarado no prueba español factual ni naturalidad. Evaluación completa sin reescritura de documentos del usuario, modelos, inferencia, instalación o audio.
