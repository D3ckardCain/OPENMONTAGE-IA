# Investigación de la diferencia Qwen3_4B

24-11-2026 UTC; seguimiento #3/#82. Alcance exclusivo: `qwen_3_4b.safetensors`. [Evidencia JSON](INVESTIGACION_QWEN3_4B_20261124.json), ampliación del [informe SHA256](SHA256_FLUX_ACE_KOKORO_ES.md). No se ha identificado el hash local con una revisión oficial en las fuentes consultadas. **No hay evidencia suficiente para afirmar corrupción ni atribuir una causa.**

## Estado del disco y reutilización de resultados

C: y E: (Seagate Basic) están conectados y sus raíces se enumeran. **D: ya no aparece como volumen disponible**; no se puede buscar allí ni revalidar el original en esta sesión. Se clasifica como volumen no disponible, no como archivo ausente ni acceso denegado. No se monta ni modifica el disco.

Se conserva como evidencia histórica el resultado anterior de esta ruta:

`D:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders/qwen_3_4b.safetensors`

| Dato | Resultado guardado |
|---|---|
| Tamaño | 8044982048bytes |
| SHA256 local | `a5e1c4ed3f2d45531da55eaa977e44e40b8cfde7c2ebc53a5288b9573c3f45bc` |
| Cálculo anterior UTC | 2026-11-24T14:51:25.271601+00:00 |
| Estado de caché ahora | Histórica; identidad/metadatos no revalidables con D: desconectado. No se presenta como observación actual. |

No se repitió la lectura de8GB. No aparecieron otras rutas candidatas accesibles que necesitaran hashing: **0bytes nuevos de contenido leídos,0nuevos hashes y0resultados de rutas accesibles reutilizables**. El hash histórico sí se reutilizó como dato para consultar referencias oficiales, con esa limitación explícita.

## Búsqueda de otras copias

Primero se consultaron catálogo, inventario y caché anteriores. Después se buscaron nombres Qwen3_4B, variantes con separadores y extensiones de pesos, además de los nombres blob iguales al SHA256 local/esperado, en:

- `E:/OPENMONTAJE-IA`: incluye DESCARGAS_MODELOS y ambas zonas models/descargas presentes en ese árbol;1645 archivos enumerados.
- `C:/OPENMONTAGE-IA`:15866 archivos enumerados, excluyendo .git, .venv/venv, node_modules, __pycache__ y python_embeded.
- `%USERPROFILE%/Downloads`:606 archivos y caché Hugging Face:2 archivos.
- Las rutas antiguas `C:/OPENMONTAJE-IA`, caché Torch y modelos LM Studio no existen en ese volumen conectado.

**Ninguna copia candidata encontrada en ese alcance**, sin errores de enumeración. No se afirma una búsqueda exhaustiva de Windows/Program Files, papelera, archivos renombrados arbitrariamente, modelos dentro de archivos comprimidos ni discos no disponibles. No se identificó una copia con el SHA256 esperado. La búsqueda adicional en D: queda bloqueada hasta que el volumen esté disponible; no impide preparar el plan reversible.

## Contraste con revisiones oficiales

Se consultó exclusivamente metadato JSON público de Hugging Face: listas de commits y entradas de árbol LFS de `split_files/text_encoders/qwen_3_4b.safetensors`. No se descargaron pesos ni se compararon formatos distintos como si fueran equivalentes.

| Repositorio oficial del empaquetado | Head fijado / revisiones devueltas y comprobadas |
|---|---|
| [Comfy-Org/flux2-klein-4B](https://huggingface.co/Comfy-Org/flux2-klein-4B/tree/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965) | `5b3abca5c0dc1ecd4eaf3340868d09063fc1c965` /14 |
| [Comfy-Org/z_image_turbo](https://huggingface.co/Comfy-Org/z_image_turbo/tree/6fc90a3b1b653e935a0d175e260736de25b84df5) | `6fc90a3b1b653e935a0d175e260736de25b84df5` /16 |
| [Comfy-Org/z_image](https://huggingface.co/Comfy-Org/z_image/tree/94d47a468ec820d29a5dc09d4642539d76d49542) | `94d47a468ec820d29a5dc09d4642539d76d49542` /14 |

En las **44 revisiones comprobadas**, las entradas donde el archivo existe publican el mismo SHA256 esperado:

`6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a`

Las revisiones anteriores a su subida o sin esa ruta se registran como no presente; no como hash diferente. La subida identificable de ese nombre en flux2-klein-4B es `8556e4d870cda7c53c7942b190bfeea5be9bd411` (15-01-2026), con el hash esperado. El JSON conserva cada commit/fecha/ruta/hash/URL consultado.

El hash local histórico **no coincide con ninguna de estas entradas**. Esto no descarta revisiones de otros repositorios/ramas, conversiones o cambios locales; tampoco identifica una de esas causas. La búsqueda web por hash exacto no devolvió resultados, lo cual no es una prueba global de inexistencia. No se comparan directamente shards Transformers/Qwen o formatos FP4/FP8 distintos con este archivo unificado.

## Plan oficial preparado, sin descargar

No hay copia esperada localizable en los volúmenes accesibles. Plan de una sola descarga futura, evitando el destino original y sin crear carpetas:

| Campo | Valor |
|---|---|
| Fuente | Comfy-Org/flux2-klein-4B, empaquetado oficial Comfy |
| Revisión | `5b3abca5c0dc1ecd4eaf3340868d09063fc1c965` |
| Archivo remoto | `split_files/text_encoders/qwen_3_4b.safetensors` |
| Enlace fijado | [Descarga oficial en revisión fija](https://huggingface.co/Comfy-Org/flux2-klein-4B/resolve/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965/split_files/text_encoders/qwen_3_4b.safetensors) |
| Tamaño | **8044982048bytes**, aproximadamente7.492GiB |
| SHA256 esperado | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` |
| Licencia declarada en revisión | Apache-2.0; conservar avisos y términos del recurso |
| Destino nuevo propuesto | `E:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders/candidates/qwen_3_4b-5b3abca5-6c671498.safetensors` |
| Estado | Destino comprobado inexistente; no se creó ni descargó. E: tiene unos20.57GB libres observados, no reserva ni garantía de espacio futuro. |

Antes de ejecutar una futura descarga: volver a comprobar disponibilidad y otras copias si D: regresa; revalidar espacio/destino, no sobrescribir, verificar el candidato contra el hash fijado y mantenerlo separado del original. Ese plan **no autoriza ni realiza** activación, movimiento, sustitución de rutas o carga. La existencia de un archivo nuevo no resolvería por sí sola compatibilidad del grafo.

## Conservación y publicación

Solo se escribieron informes/metadatos de investigación dentro del proyecto. Sin cargar/deserializar modelos, lectura nueva de pesos, descargas, instalaciones, movimientos, borrados o cambios de configuración/ComfyUI. Se conserva evidencia histórica y no se altera ningún conjunto ACE/Kokoro ni otros modelos. PR#2 permanece en borrador y costo$0.
