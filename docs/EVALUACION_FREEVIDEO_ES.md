# FreeVideo / VDN-H3 — evaluación #47

24-11-2026 UTC. Revisión estática, sin instalación, importación del runtime,
descargas de pesos ni generación. Fuente oficial fijada:
[FreeVideo046bc4b](https://github.com/FlashML-org/FreeVideo/tree/046bc4be5de896aa02974ae8355cdd12a5ca9f80),
HEAD consultado, release0.6.9. `pyproject.toml` declara versión de paquete
2026.9.16.41444: son identificadores distintos, no intercambiables. Base local f2ff424.

## Decisión y comparación

Mantener WAN/LTX y los adaptadores actuales como primera opción. FreeVideo aporta
un runtime VDN-H3 con streaming/prefetch de pesos y estimación por hardware que merece
una evaluación posterior aislada; no sustituir familia ni instalarlo dentro de ComfyUI.
La adopción queda condicionada a licencia de pesos, perfil exacto, almacenamiento y
compatibilidad del equipo. No se acredita aquí calidad, velocidad ni uso comercial.

| Función | OPENMONTAGE existente | Aporte / carencia justificada |
|---|---|---|
| Generación local | `model_adapters`, `wan_presets`, WAN5B/14B, adaptador LTX y plantilla H3 de referencia | VDN-H3 es otra arquitectura/runtime. Una plantilla H3 no acredita que FreeVideo esté preparado; pesos WAN/LTX no son reutilizables como H3 |
| Pocos recursos y dos pasos | Perfiles y límites del trabajo, selección explícita de modelos | Streaming/prefetch y preview/acabado son candidatos específicos; no prometer el mínimo anunciado para cualquier resolución o referencia |
| Control por agente | LocalAgent, recibos, cola, cancelación/recuperación y almacenamiento por proyecto | CLI upstream expone status/schema/plan/submit/job/cancel/resume y OpenAPI. Evaluar un adaptador a esa superficie; no importar su agente ni ejecutar install-skill |
| ComfyUI | Servidor y Python actuales, grafos/bindings y prompt_id persistente | Upstream puede instalar entorno, modelos y nodos. Solo instancia separada si pasa requisitos; no modificar el ComfyUI del usuario |

Fuentes: [README](https://github.com/FlashML-org/FreeVideo/blob/046bc4be5de896aa02974ae8355cdd12a5ca9f80/README.md),
[CLI agente](https://github.com/FlashML-org/FreeVideo/blob/046bc4be5de896aa02974ae8355cdd12a5ca9f80/freevideo_engine/agent/cli.py).
Locales: `lib/model_adapters.py`, `lib/wan_presets.py`, `lib/comfy_job_records.py`,
`tools/video/ltx_video_local.py`, `tools/_comfyui/reference_templates/h3.ui.json`.
Presencia de código/receta no significa inferencia de esas familias validada en este equipo.

## Licencia y costo $0

Código [Apache2.0](https://github.com/FlashML-org/FreeVideo/blob/046bc4be5de896aa02974ae8355cdd12a5ca9f80/LICENSE);
conservar avisos/atribución y revisar componentes incluidos. Los pesos no heredan esa
licencia. Se leyó [MiniMax H3 Community fijada en2283779e](https://huggingface.co/OpenVDN/vdn-minimax-h3-edge/blob/2283779e4cd6bd4724f200c152977fce58216da3/LICENSE).
Excluye UE, Reino Unido, República de Corea y Estados Unidos, e impone restricciones
también sobre uso/distribución/exhibición de resultados fuera del territorio aplicable.
Incluye política de uso, avisos y condiciones comerciales; ingresos comerciales anuales
superiores a USD20millones requieren autorización previa, y hay identificación de marca.
No inferir permiso por ubicación del equipo ni por no cobrar una API. Resolver alcance,
usuarios y distribución antes de adoptar; si exige pago/autorización no disponible,
excluir esa ruta y conservar motores elegibles. No se contactó al proveedor ni se aceptaron términos.

## Dependencias, inventario y offline

[pyproject](https://github.com/FlashML-org/FreeVideo/blob/046bc4be5de896aa02974ae8355cdd12a5ca9f80/pyproject.toml)
exige Python>=3.12,<3.13; Studio actual3.11 no debe alterarse. Runtime incluye
Triton3.7.1 Linux/triton-windows3.7.1.post27 Windows, Transformers5.15,
Accelerate1.14, PEFT0.20, NumPy2.5.2, PyAV18.1 y componentes de descarga. Torch/CUDA
también dependen del instalador/perfil, no solo de esa lista. README anuncia NVIDIA
CC>=8.0 y mínimo8GBVRAM/16GBRAM; son requisitos declarados, no un diagnóstico local.

El [manifest model_files.json](https://github.com/FlashML-org/FreeVideo/blob/046bc4be5de896aa02974ae8355cdd12a5ca9f80/freevideo_engine/model_files.json)
contiene40entradas que suman99,144,407,906bytes declarados. Incluye encoder de
15,687,142,551bytes y shards de varios GB, con revisiones y huellas. Es un catálogo,
no el mínimo instalable ni tamaño final de una variante. No incluye toda la expansión
de entorno, variantes preparadas, temporales, cachés o salidas; el total real queda
pendiente del perfil elegido. No se leyeron pesos ni recalcularon hashes del inventario.

README describe paquetes offline para modelo, encoder, decoders y sampling caches,
más entorno nuevo; referencia de audio opcional. Offline es viable solo con conjunto
completo, versiones/huellas verificadas y sin rutas de descarga/actualización pendientes.
El arranque puede obtener recursos automáticamente y el instalador ejecuta pip/uv;
por eso no se ejecutó. La cifra comunitaria0.3.23 del issue no representa0.6.9 ni un
benchmark local. Se conserva su valor histórico sin extrapolar tiempo/VRAM.

## Tareas futuras con aceptación

| Prioridad | Tarea | Aceptación |
|---|---|---|
| P0 | Elegibilidad y perfil | Licencia exacta de cada recurso, destinos permitidos y decisión trazable; si hay incompatibilidad/pago, ruta deshabilitada sin fallback |
| P0 | Plan de preparación, sin descargar | Variante y cierre de dependencias con bytes/sha/revisión, temporales y espacio; reutilización solo de coincidencias verificadas; no usar catálogo como inventario físico |
| P1 | Doctor aislado | Python3.12 separado, CUDA/Triton/CC y nodos reportados; pruebas con fixtures sin GPU/instalación, sin escribir en .venv o ComfyUI existentes |
| P1 | Contrato CLI/API | Mocks de status/plan/job/cancel/resume, IDs, errores, recibos y reanudación sin duplicados. Solo después preparar ejecución física autorizada |
| P2 | Comparación con WAN/LTX | Plan de muestras sintéticas iguales, fases preview/final, calidad y picos RAM/VRAM/disco medidos; no ejecutar en esta evaluación |

Bloqueos de adopción documentados, no de esta revisión: elegibilidad territorial,
footprint de variante y hardware efectivo. Evaluación completada; implementación pendiente.
