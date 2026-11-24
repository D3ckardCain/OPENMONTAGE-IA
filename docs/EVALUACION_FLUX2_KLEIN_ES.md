# FLUX.2 klein 4B — evaluación #82

24-11-2026, #3. [Código oficial](https://github.com/black-forest-labs/flux2/tree/50fe5162777813d869182b139e83b10743caef15), paquete0.1.0; README, LICENSE.md, pyproject y utilidades revisados. [Model card 4B fijada](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/tree/e7b7dc27f91deacad38e78976d1f2b499d76a294): solo metadatos y texto, ningún peso.

## Licencias por recurso

Código y **klein4B/base4B** declarados Apache-2.0; cumplir avisos/modificaciones. **9B,9B KV y dev no son equivalentes: licencia no comercial**, no habilitados aquí. El autoencoder FLUX.2 se declara Apache aunque esté alojado en repo dev: fijar archivo/revisión y términos específicos, no extender la licencia de un recurso a todos. Encoder/tokenizer, filtros, adaptaciones cuantizadas y LoRA requieren inventario/licencia propios. No se acredita distribución cerrada de todos los recursos con solo el badge del modelo. Marcas no tienen permiso general por Apache.

## Windows, memoria y offline

Fuente de encoder exacta del código: `src/flux2/text_encoder.py` carga **Qwen/Qwen3-4B-FP8** para4B. [Metadatos oficiales fijados](https://huggingface.co/Qwen/Qwen3-4B-FP8/tree/96b30dc13593a244a5e59e84687309f53c375cfa) declaran Apache-2.0. No equivale sin contraste al artefacto qwen3_4b del catálogo/loader ComfyUI; layout, precisión y tokenizer deben identificarse por archivo antes de elegir ruta. Solo se consultó metadata, sin descargar encoder.

pyproject admite Python>=3.10,<3.13; upstream probó inferencia en GB200/CUDA12.9/Python3.12, no en nuestra laptop Windows. README dice ~8GB VRAM para4B y model card **~13GB**: discrepancia explícita, sin elegir la cifra conveniente. Se debe medir pipeline completo transformer+encoder+VAE+activaciones, resolución/referencias y offload/RAM; no prometer cabida en RTX4060Laptop8GB/16GBRAM. Espacio de descarga/caché/duplicados y tiempo de offload no medidos. No se instala ni modifica ComfyUI.

Model card muestra Diffusers desde Git con CPU offload; no ejecutar su actualización. Referencia a soporte ComfyUI no demuestra que la copia instalada tenga loaders compatibles. `from_pretrained` puede descargar recursos; offline requiere todos preparados/localizados y egreso deshabilitado. BFL API/OpenRouter/encoder remoto quedan fuera de costo$0. Con artefactos elegibles locales no exige una API de pago, pero aún no se acredita ejecución en este hardware.

Español y texto exacto en miniaturas no validados: la tarjeta declara `en` y advierte distorsión del texto. No usar generador para cifras/titulares factuales cuando compositor local puede escribir tipografía exacta.

## Comparación y aceptación

Contraste adicional del inventario: `docs/models/base.json` ya registra **flux-klein** y encoder Qwen3_4b compartido con Z-Image; `lib/model_adapters.py` ya enruta familia a image_generation/ComfyUI. En esta sesión0/3 archivos listados estaban presentes en **esas rutas de catálogo**; no demuestra inexistencia en otros discos/rutas. No repetir descarga, reinstalar ni afirmar que esos nodos están preparados. Reutilizar el adaptador existente; la carencia es su perfil de recursos/evidencia de compatibilidad, no otro conector.

Ya existen rutas ComfyUI/FLUX inventariadas (incluido FLUX.1-schnell) y E01/E05/E06; no volver a descargarlas ni otro adaptador por nombre. Aporte diferencial potencial: edición multirreferencia local de4B, condicionada a recursos/compatibilidad, sin desplazar motor aprobado.

| Destino | Criterio futuro |
|---|---|
| E01 | Perfil por artefacto/modelo/loader/hash/licencia, recursos presentes vs ausentes y estimación de memoria con alcance. Mocks rechazan confundir4B Apache con9B NC o tamaño de archivo con VRAM; sin descarga implícita. |
| E06/E05 | Referencias ordenadas por ID/hash/rol y parámetros/semilla/ratio; cambiar una referencia invalida derivados pertinentes. Error de recurso o memoria es explícito, no fallback a API ni otra variante. Fixtures JSON sin imágenes. |
| B04/B06 | Compatibilidad Windows/ComfyUI y prueba de memoria/calidad/texto español pendientes; ninguna instalación o inferencia autorizada en esta fase. |

No tarea independiente duplicada. Evaluación completa; solo propuesta de contrato y ruta condicionada. Sin modelos, contenido, paquetes ni configuraciones cambiadas.
