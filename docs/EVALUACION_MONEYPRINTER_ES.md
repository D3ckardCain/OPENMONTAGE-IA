# MoneyPrinterTurbo: evaluación #62

24-11-2026 UTC. Fuente oficial `harry0703/MoneyPrinterTurbo`
`dabfd3f8548d30ed0eea8759decbdead9626e0e6`, pyproject1.3.11/Python>=3.11.
Revisión estática sin instalar aplicación, importar servicios ni generar contenido.

## Decisión y solapamientos

No añadir otro director/Streamlit/API. Tema→guion→assets→voz→subtítulos→montaje ya
existe en pipeline_defs, checkpoints y herramientas locales. Ollama, Kokoro/Qwen,
ASR, presets verticales y ffprobe tampoco son novedades. Aporte para estudiar:
proyecto editable y reutilización/invalidation de etapas, lote parcialmente exitoso
y asociación de recursos a fragmentos. Un proyecto editable no implica que todo se
pueda reanudar sin repetir generación o conservar calidad al cambiar formato.

Fuentes locales contrastadas: `lib/checkpoint.py`, `lib/agent_conversation.py`,
`lib/scene_audio_preview.py`, `tools/audio/audio_mixer.py`, transcriber y subtitle_gen;
evaluaciones #44/#54. Reutilizar E03/E04/E05/E06/E08, no duplicar guion/TTS/montaje.

## Fuentes, licencia y requisitos

[README-en](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/README-en.md),
[pyproject](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/pyproject.toml),
[config](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/config.example.toml):
FFmpeg y Python; dependencias elegidas incluyen MoviePy2.2.1, edge-tts7.3.1,
faster-whisper1.1.0, FastAPI0.136.3. No deben instalarse sobre Studio por coincidir
el floor de Python. Config se copia al primer arranque, por lo que tampoco se
arrancó como diagnóstico. API tiene clave opcional, no publicar servicio sin scope.
[MIT](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/LICENSE)
del código exige avisos; stock/música/voces/pesos/FFmpeg mantienen condiciones propias.
Nombre del proyecto o muestras no acreditan ingresos, monetización o derechos.

[Proyectos](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/docs/video-projects.md)
y [task](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/app/services/task.py)
permiten estudiar persistencia, medios por escena y snapshots de resultados parciales.
La lectura de esas rutas no prueba crash-safety de toda la aplicación ni cancelación
del encoder real. Reconciliar input/artefacto/recibo, nunca éxito por archivo presente.

## $0 y offline por función

Config `script_generation_backend=local` conserva workflow LLM, no garantiza que el
proveedor sea Ollama: [llm.py](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/app/services/llm.py)
incluye rutas externas. Seleccionar endpoint/modelo local explícito y negar fallback.
Edge TTS es red aunque no pida clave. Proveedores comerciales, planes de agentes y
créditos promocionales no son ruta $0 independiente. No conectar cuentas ni stock.

[subtitle.py](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/app/services/subtitle.py)
busca modelo local pero puede pasar nombre de modelo a WhisperModel si no existe;
riesgo de descarga implícita. Reusar worker/pesos preparados, no esta inicialización.
[voice.py](https://github.com/harry0703/MoneyPrinterTurbo/blob/dabfd3f8548d30ed0eea8759decbdead9626e0e6/app/services/voice.py)
ofrece múltiples dispatches: tener Kokoro en un menú no acredita compatibilidad con
nuestros pesos ni español probado. Offline posible por perfil cerrado de archivos,
TTS/ASR/modelos/fuentes locales; no verificado ejecutando upstream.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Invalidación por dependencias E05/E06 | Proyecto sintético: cambio de guion/voz/asset/fuente/ratio invalida solo etapas afectadas; hash/revisión y motivo visibles; no perder originales |
| P1 | Lote con resultados parciales E05 | Error en variante2 conserva variante1 verificada y su recibo; resume no repite ni declara lote completo; stop distingue etapa/proceso |
| P1 | Asociación guion→recursos E03/E08 | Referencias/fechas/licencias/intervalos guardados; muestras propias y faltantes explícitos, no búsquedas de pago ni material inventado |
| P1 | Perfil cerrado local E01/E04 | Mocks rechazan endpoint cloud, modelo ausente y descargas; español/pausas/fin real del audio y palabras con timestamps; no corregir texto perdiendo verdad de ASR |

Bloqueos de ejecutar upstream: cierre de recursos, dependencias y backend efectivo
no verificado. Los contratos anteriores son independientes; no instalar aplicación
completa. Sin audio/vídeo, APIs pagadas ni cambios en configuraciones/ComfyUI.
