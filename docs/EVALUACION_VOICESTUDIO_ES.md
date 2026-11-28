# VoiceStudio: evaluación #63

24-11-2026 UTC. `debpalash/VoiceStudio@202e2139814897a438541c707668e6ae90c159d2`,
manifiestos0.5.9-beta.9. Sin instalar backend/UI, aceptar licencias ni generar voz.

## Decisión y existente

Gestión de perfiles y narración/doblaje largo merecen contrato neutral, no otra UI
ni copias de pesos. OPENMONTAGE ya tiene adaptadores Kokoro/Qwen3-TTS, ASR, pruebas
de voz, timestamps, audio_mixer y recibos. Voz localizada o un WAV válido no prueban
identidad, pronunciación española, diarización o doblaje sincronizado aprobados.
Priorizar perfil de voz versionado, segmentos/lotes y reloj de doblaje sobre esos
recursos; backend externo solo si añade función medida. Comparar ASR con #68.

## Fuentes y requisitos

[README](https://github.com/debpalash/VoiceStudio/blob/202e2139814897a438541c707668e6ae90c159d2/README.md),
[pyproject](https://github.com/debpalash/VoiceStudio/blob/202e2139814897a438541c707668e6ae90c159d2/pyproject.toml):
Python>=3.11, backend FastAPI/MCP, muchos motores con dependencias y rutas específicas;
default group CUDA y PyTorch cu128 en configuración uv. Windows10/11x64 NVIDIA/CPU
anunciados, no benchmark aquí; GGUF/Vulkan/ROCm son perfiles distintos y no
certifican todos los motores. No contaminar .venv o ComfyUI con ese entorno amplio.
[Catálogo](https://github.com/debpalash/VoiceStudio/blob/202e2139814897a438541c707668e6ae90c159d2/docs/engines/README.md)
distingue MLX Apple Silicon de Qwen3-TTS CUDA adapter, que exige checkpoint local,
variable y faster-qwen3-tts. Tener pesos Qwen actuales no garantiza ese loader.

[MCP](https://github.com/debpalash/VoiceStudio/blob/202e2139814897a438541c707668e6ae90c159d2/docs/mcp.md)
está montado en /mcp/ del backend; base_path confina archivos y sin él rechaza paths.
Consumption tools locales incluyen creación de perfiles: no son todo lectura.
files/both evita WAV base64 masivo en contexto; conservar namespace de ruta backend
vs agente. Timeout de espera MCP no demuestra cancelación GPU/cola. Futuro puente
restringe herramientas, permisos y procesos propios antes de escritura.

## Licencia, $0 y offline

[LICENSE](https://github.com/debpalash/VoiceStudio/blob/202e2139814897a438541c707668e6ae90c159d2/LICENSE)
y [NOTICE](https://github.com/debpalash/VoiceStudio/blob/202e2139814897a438541c707668e6ae90c159d2/LICENSE-NOTICE.md):
app AGPL3-only, permite uso comercial bajo sus obligaciones; no exige Pro por el mero
uso comercial. Distribución/modificaciones y servicio de versión modificada deben
respetar fuente/avisos aplicables. OmniVoice code embebido Apache2 separado.
Pro/Cloud no necesarios ni activados; licencia comercial de app no licencia pesos.
Default OmniVoice CC-BY-NC advertido; tokenizer tiene términos Boson/Meta propios.
Los registros upstream reconocen gaps: no dar clearance global a motores por una
casilla ni trasladar evidencia entre conversiones/revisiones. Excluir default de
canales monetizados mientras no se resuelva artefacto/uso exacto; no aceptar términos.

[Descargas](https://github.com/debpalash/VoiceStudio/blob/202e2139814897a438541c707668e6ae90c159d2/docs/downloading-models.md)
documenta primer uso con Hub, acelerador segmentado y selección de mirror tras
fallos de red. MCP generate_speech puede descargar ~2.3GB default: no invocarlo
como prueba inocua. Offline condicionado a runtime/modelos/tokenizer/fuentes presentes,
perfil elegible y egreso bloqueado. Reusar almacenamiento verificado sin duplicarlo,
pero no montar sobre rutas originales con permisos de actualización. Ningún audio real
procesado; “646 idiomas” no certifica calidad española ni derechos de voces.

## Tareas con aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P0 | Perfil de voz y derechos | Motor/variante/loader/revisión/hashes, idioma y referencia autorizada separados; evidencia de licencia por pesos/tokenizer/voz; NC o unknown bloquea uso monetizado |
| P1 | Narración/lotes E04/E05 | Segmentos estables, pausa/timestamp, cancel y error parcial; mocks demuestran resume sin repetir audio completado y sin crear otra voz |
| P1 | Puente local E01/E10 | Solo métodos elegidos, paths confinados, salida por archivo/recibo en vez de base64 enorme; modelo ausente falla sin descargar y localhost obligatorio |
| P1 | Doblaje/ASR compartido con #68 | Texto fuente/traducción/voz/duración separados; no truncar o acelerar silenciosamente; error por speaker/timing explícito en fixtures españoles |
| P2 | Calidad futura | Plan WER/tiempos/inteligibilidad/identidad/autorización con revisión humana; no ejecutar clonación ni audio en evaluación |

Bloqueos: default NC y términos de tokenizer, compatibilidad efectiva de loader y
recursos/memoria no validados. Contratos sobre motores actuales pueden avanzar;
no instalar VoiceStudio para completar la evaluación. Configuraciones conservadas.
