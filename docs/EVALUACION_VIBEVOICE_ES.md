# VibeVoice: evaluación #68

24-11-2026 UTC. `microsoft/VibeVoice@16fb2cb1217c9934a886e1948ffb06120caa2df5`,
pyproject1.0.0. Runtime CPU separado
`microsoft/VibeASR.cpp@c4334009c88060f86cdbbd684b62662f710b6c20`.
Sin instalar, descargar pesos, transcribir audio ni generar voz.

## Decisión y variantes

Prioridad a una mejora medible de diarización/timestamps/audio largo en español,
no reemplazar Whisper, Kokoro o Qwen3-TTS preparados. Unificar perfil de voz/doblaje
con #63 y transcript/segmentos con E04. Búsqueda acotada en lib/tools/docs no halló
VibeVoice por nombre en el código/configuración revisados: no equivale a barrido
de todos los discos ni prueba de ausencia de pesos. Antes de aprovisionar, cotejar
inventario existente, hashes y loader; en esta fase no descargar nada.

| Variante | Aporte declarado | Límite para adoptar |
|---|---|---|
| ASR7B | Who/When/What, hotwords y hasta60min/64K tokens | No significa que una hora quepa en laptop ni speaker IDs sean identidades verificadas |
| ASR Streaming7B | Segmentos mientras llega audio;10idiomas declarados | Chunk provisional/final y continuidad de hablantes necesitan contrato propio |
| ASR BitNet | Runtime CPU con VAE/LM cuantizados, LM1.5B distinto del7B | No mismo modelo con idéntica precisión; cifras upstream excluyen carga y usan clip~20s |
| Realtime0.5B | TTS streaming de un hablante; ES experimental | Docs todavía priorizan inglés/no extensamente probado; no calidad española uniforme |
| TTS original1.5B | Anuncio histórico multihablante/largo | Código retirado del repositorio oficial; no instalar fork como equivalente Microsoft |

## Fuentes, licencias y requisitos

[README](https://github.com/microsoft/VibeVoice/blob/16fb2cb1217c9934a886e1948ffb06120caa2df5/README.md),
[ASR](https://github.com/microsoft/VibeVoice/blob/16fb2cb1217c9934a886e1948ffb06120caa2df5/docs/vibevoice-asr.md),
[Streaming](https://github.com/microsoft/VibeVoice/blob/16fb2cb1217c9934a886e1948ffb06120caa2df5/docs/vibevoice-asr-streaming.md),
[Realtime](https://github.com/microsoft/VibeVoice/blob/16fb2cb1217c9934a886e1948ffb06120caa2df5/docs/vibevoice-realtime-0.5b.md)
y [pyproject](https://github.com/microsoft/VibeVoice/blob/16fb2cb1217c9934a886e1948ffb06120caa2df5/pyproject.toml):
Python>=3.10, torch, Transformers>=4.51.3,<5; extra streamingtts fija4.51.3.
Demos recomiendan contenedores CUDA/FlashAttention y FFmpeg; comandos privileged/
net=host/--share no se ejecutan ni se trasladan a la instalación. Windows nativo
de esa ruta no certificado por contenedores Linux. Latencia200/300ms difiere entre
documentos y es dependiente de hardware, no SLA medido aquí.

[VibeASR.cpp README](https://github.com/microsoft/VibeASR.cpp/blob/c4334009c88060f86cdbbd684b62662f710b6c20/README.md)
requiere Python>=3.9, CMake>=3.14 y GCC/Clang; Windows MSVC rechazado, MinGW recomendado.
Tamaño total anunciado1.58GB no es pico RAM. Benchmarks incluyen i7-13700/32GB y
acentos estándar; no extrapolar a nuestra laptop ni todo español.

[Código MIT](https://github.com/microsoft/VibeVoice/blob/16fb2cb1217c9934a886e1948ffb06120caa2df5/LICENSE)
y runtime CPU MIT: conservar avisos. Metadata oficial Hub consultada por HTTPS API
solo texto, sin pesos; fija las revisiones siguientes y declara license=mit:

| Artefacto oficial | Revisión de metadata |
|---|---|
| [ASR](https://huggingface.co/microsoft/VibeVoice-ASR/tree/d0c9efdb8d614685062c04425d91e01b6f37d944) | d0c9efdb8d614685062c04425d91e01b6f37d944 |
| [Streaming7B](https://huggingface.co/microsoft/VibeVoice-ASR-Streaming-7B/tree/60d858b518b4e19d404af3737f848fc185b30177) |60d858b518b4e19d404af3737f848fc185b30177|
| [BitNet](https://huggingface.co/microsoft/VibeVoice-ASR-BitNet/tree/66e78021ab8f5f06133d1ab421ba4d348bda97c9) |66e78021ab8f5f06133d1ab421ba4d348bda97c9|
| [Realtime0.5B](https://huggingface.co/microsoft/VibeVoice-Realtime-0.5B/tree/6bce5f06044837fe6d2c5d7a71a84f0416bd57e4) |6bce5f06044837fe6d2c5d7a71a84f0416bd57e4|

Metadata MIT no inventaría todos los derechos de tokenizer/voces/dependencias o
conversiones. Revisar textos/avisos de archivos exactos y referencias autorizadas
antes de uso. Recomendación upstream de pruebas adicionales antes de uso comercial
no se convierte por sí sola en prohibición NC del código MIT.

## $0, offline y tareas

Inferencia local puede evitar cargos con runtime/pesos/recursos presentes y egreso
bloqueado; from_pretrained/model_path remoto y descarga de voces experimentales
requieren red. No usar Playground/Azure/Colab para acreditar local$0. ASR y TTS son
jobs distintos; stop de Qwen no cancela estos procesos automáticamente.

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Transcript/speaker neutral E04 | Segmentos/span/tiempos/lengua/confianza opcional/speaker local con procedencia; fixtures de solapes, cambio de IDs, silencios, idioma mixto y tiempos inválidos |
| P1 | Streaming E05 | Parcial vs final, secuencia de chunk/reintento/cancel y estado persistente; reconectar no duplica palabras ni finaliza contenido provisional |
| P1 | Inventario/doctor E01 | Variante/loader/commit/tamaños/hashes/licencias y recursos; sin auto-download; modelo ya presente se reutiliza solo si compatible |
| P2 | Benchmark futuro | WER/CER, DER/tolerancia de timestamps, hotwords, RAM/VRAM/RTF/carga y estabilidad frente ASR existente; corpus español autorizado, no audio en esta fase |

Bloqueos de ejecución: cierre de artefactos/derechos, runtime y memoria/calidad no
validados. Contratos/mocks son independientes; no instalar otro TTS por anuncio.
