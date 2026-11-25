# Chatterbox y español regional — evaluación #96

25-11-2026 UTC. Código [ab55923c27757c90cfcc407baa57dc25a7d25217](https://github.com/resemble-ai/chatterbox/tree/ab55923c27757c90cfcc407baa57dc25a7d25217),
manifiesto 0.1.7. Reutiliza inspección de `mtl_tts.py` en #96/7146443057.

## Decisión y comparación

Ya existe adaptador `chatterbox` en `model_adapters.py`; el worker llama
`ChatterboxMultilingualTTS.from_local`, pasando idioma y referencia local.
No crear otro TTS ni instalar un estudio. La mejora pendiente es identificar
explícitamente variante/loader V2/V3/regional y exponer solo parámetros soportados;
el worker actual no acredita carga regional V3, ni controles exaggeration/cfg.
Comparar después con Kokoro/Qwen preparados y con E16 de #63/#104, no repetir
generación o benchmarks ya aprobados.

El [README fijado](https://github.com/resemble-ai/chatterbox/blob/ab55923c27757c90cfcc407baa57dc25a7d25217/README.md)
anuncia retiro/no mantenimiento desde agosto2026, mientras conserva novedades V3
y promoción comercial contradictoria. Decisión prudente: tratar el soporte como
incierto y no prometer mantenimiento. Turbo350M/Nano110M se anuncian en inglés;
no heredar sus etiquetas expresivas ni cifras CPU al español multilingüe.

## Recursos y licencias

[Código MIT](https://github.com/resemble-ai/chatterbox/blob/ab55923c27757c90cfcc407baa57dc25a7d25217/LICENSE).
Modelo regional [27e595bf2fe7be0533ca299d9afafcde08b7cca7](https://huggingface.co/ResembleAI/Chatterbox-Multilingual-es-mx-latam/blob/27e595bf2fe7be0533ca299d9afafcde08b7cca7/README.md):
ficha MIT, es-419/es-MX, language_id `es`; incluye T3, decoder S3Gen V3 y tokenizer.
El T3 declarado ocupa 2.143.990.280 bytes, no el pipeline entero. Base compartida
[5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18](https://huggingface.co/ResembleAI/chatterbox/tree/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18),
también ficha MIT, conserva auxiliares propios. Es metadata, no descarga ni
verificación de pesos locales. La revisión del modelo no equivale a un loader
Windows compatible. Perth, tokenizer/decoder y referencias de voz requieren
procedencia/avisos separados; no eliminar la marca de agua del resultado.

`from_pretrained` usa snapshot `main`, no selecciona por sí solo la variante
regional. Exigir inventario/cache fijado y ruta local sin descargas implícitas.
`punc_norm` modifica el texto y puede sustituir vacío por frase inglesa: rechazar
vacío y conservar texto original/hablado con mapa de normalización.

## Windows, offline y costo

Upstream validó Python3.11/Debian11. [pyproject](https://github.com/resemble-ai/chatterbox/blob/ab55923c27757c90cfcc407baa57dc25a7d25217/pyproject.toml)
fija Torch/torchaudio2.6 para Python<3.14, Transformers5.2 y Perth desde master;
no modificar .venv/ComfyUI para acomodarlo. Windows/CUDA/CPU, memoria pico,
compatibilidad regional y calidad mexicana no medidos. Offline/$0 es posible
solo con stack y recursos elegibles preparados; hosted/demos no son dependencias.

| Prioridad / ID | Aceptación futura |
|---|---|
| P0 E01/E16 | Perfil incluye variante, locale, revisión/hash y companions; un T3 aislado o `es` no se acepta como pipeline regional completo |
| P1 E04/E05/E16 | Texto original/hablado, referencias autorizadas y marca Perth trazables; parámetros por variante, lotes/pausas y cancel/resume sin repetir tomas válidas |
| P1 E02/#92 | Selector de motor/variante/voz y versiones de toma sobre proyecto común; español no soportado se rechaza, sin fallback a inglés |
| B08/B06 | Confirmar compatibilidad/licencias de componentes y luego prueba auditiva autorizada de cifras, nombres, expresividad y continuidad; no inferir calidad del listado de idiomas |

Evaluación concluida; integración regional y calidad pendientes. No instalaciones,
pesos nuevos, carga de modelos o audio generado.
