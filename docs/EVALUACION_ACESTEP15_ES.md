# ACE-Step 1.5 — evaluación #83

24-11-2026, #3. [Código oficial fijado](https://github.com/ace-step/ACE-Step-1.5/tree/ca1e85fe9430179831e6bc6be790c332190a3866), pyproject **1.5.0**; README, LICENSE y manifiesto revisados. [Model card principal](https://huggingface.co/ACE-Step/Ace-Step1.5/tree/19671f406d603126926c1b7e2adc169acbcade22) fijada por API y lectura de texto; sin pesos descargados.

## Inventario y licencias

`docs/models/base.json` ya registra familia **acestep**, turbo, LM1.7B, Qwen3-Embedding0.6B y VAE en la misma revisión HF. `lib/model_adapters.py` ya la enruta a music_generation con grafo ComfyUI explícito; hay workflows/reference_templates existentes. Un registro no prueba que estén instalados nodos compatibles ni automatización validada; no duplicar adaptador ni confundir ACE-Step v1 con1.5. Se inspeccionó presencia/tamaño de archivos catalogados sin cargarlos ni rehash masivo; resultado numérico en issue.

Código MIT con avisos y tarjeta principal MIT. No extrapolar esa etiqueta a cualquier XL, LoRA de terceros, encoder/tokenizer o muestra. Antes de adoptar una variante: inventario por archivo/revisión/hash/bytes/licencia y avisos, incluyendo LM/encoder/VAE. `nano-vllm` tiene LICENSE propio; paquetes/voz y recursos de referencia conservan términos independientes. Permiso del modelo no garantiza originalidad/exclusividad de una salida musical ni derechos sobre grabaciones de referencia. No se aprueban todos los checkpoints por el badge principal.

## Windows, recursos, offline y costo

Lectura de presencia del catálogo:0/27 archivos ACE-Step en las rutas allí guardadas,0bytes observados; no se concluye que falten en todos los discos ni se reaprovisiona. Ninguna configuración específica de estas familias en `adapter_settings` del archivo leído. Es un límite de inventario/ruta, no autorización para duplicar descargas. Se conserva el catálogo y la configuración.

Python **>=3.11,<3.13**, rutas Windows CUDA y portátil según README; PyTorch Windows con CUDA12.8 en manifiesto. ROCm Windows exige3.12 según upstream; no actualizar Python de Studio/ComfyUI ni instalar portátil. MPS/CPU/XPU son rutas con requisitos distintos, no rendimiento equivalente.

**2B y XL4B separados**: README propone turbo2B y LM0.6B para6–8GB, pero inventario actual incluye LM1.7B. No sustituir ni descargar0.6B automáticamente. La frase <4GB exige offload/quantización/LM desactivado según perfil; no representa todos los modos. XL requiere>=12GB con offload/quantización, >=20GB sin offload según upstream: no elegible para nuestra GPU8GB. Memoria RAM/disco y activaciones/duración/lotes deben medirse, no solo sumar pesos. A100/3090 no predicen latencia local.

Arranque documentado descarga modelos al primer uso; no lanzar UI/API ni doctor que aprovisione. Offline requiere todos los recursos/rutas/loader preparados, sin descargas implícitas. Código/pesos principales no exigen API pagada; servicios cloud/créditos excluidos. Español entre50+ idiomas declarado no acredita pronunciación/letras/calidad. Instrumental, voz, repaint, cover y vocal2BGM tienen entradas/efectos diferentes.

## Carencias y aceptación sin generación

| Grupo | Aceptación futura |
|---|---|
| E01 | Perfil variante/DiT/LM/encoder/VAE/backend/precisión/offload y recursos reales; mocks diferencian2B deXL y LM ausente/insuficiente sin descargar ni invocar modelo. Inventario aprobado reutilizado. |
| E05/E06 | Solicitud musical estructurada: instrumental/letras/idioma/duración/semilla/tempo/compás/modo y referencias con derechos. Repaint registra intervalo/contexto protegido; NaN/rango fuera de fuente/variante incompatible es error. Datos JSON, ningún audio. |
| E05 | IDs/recibos por variante/segmento y dependencias; cancelación/archivo parcial no se declara final. Cambiar letras no invalida todo recurso independiente, no repetir resultados válidos. |
| B04/B06 | Grafo/nodos efectivos, licencias completas de variantes y recursos/medición/escucha pendientes. No instalar XL ni otros motores para resolver la evaluación. |

Se amplían contratos existentes, no otra UI/motor musical. Evaluación completada sin inferencia, audio, modelos, instalaciones o cambios de configuración.
