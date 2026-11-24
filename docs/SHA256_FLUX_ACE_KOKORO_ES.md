# SHA256 físico: FLUX/klein, ACE-Step1.5 y Kokoro

2026-11-24T15:00:21.185191+00:00; seguimiento #3/#82/#83/#86.

**Hay una diferencia real de SHA256 en el encoder Qwen3_4B de FLUX.** No se movió, borró, sustituyó o descargó nada. Los resultados por ruta constan en [JSON completo](SHA256_FLUX_ACE_KOKORO_20261124.json). Este informe amplía el [inventario de presencia/tamaños](INVENTARIO_FLUX_ACE_KOKORO_ES.md): tamaño coincidente nunca acreditó integridad.

## Documentos guardados

Ambos documentos están presentes como archivos, pero un nivel por debajo de los destinos propuestos: esos destinos son **directorios con nombre terminado en .md**, no archivos. Se conservó esa estructura.

| Archivo real | Bytes | SHA256 calculado | Referencia oficial |
|---|---:|---|---|
| E:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models/flux-klein-4b-LICENSE.md/LICENSE.md | 9584 | `ca02bc51900ab07789d1b70283329e7137f5af98f5161c23a1c81fc38a4af1fe` | SHA256 reference_unavailable; Git blob SHA1 match |
| D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/VOICES.md/VOICES.md | 7625 | `ec7e4941ad7e194af61e3455928528a9ff5360c7c505e412efab27d6a69ea106` | SHA256 reference_unavailable; Git blob SHA1 match |

Licencia klein: Apache-2.0; VOICES pertenece al repo Kokoro declarado Apache-2.0 y conserva sus avisos por voz. Se contrastaron los metadatos de las mismas revisiones fijadas, sin descargar contenidos/modelos.

## Cobertura y método

Se calcularon SHA256 de los **87 archivos catalogados**, sus alternativas de ACE y los2 documentos: **116 rutas únicas**, 32991524673bytes leídos. Los dos conjuntos ACE tienen rutas distintas y se leyeron una vez cada uno. No se suman dos veces los archivos de una misma ruta. No existían resultados locales previos válidos en la caché de esta tarea; cada resultado se guardó tras terminar el archivo. Las referencias esperadas del catálogo no se usaron como si fueran hashes locales.

Lectura secuencial en bloques8MiB con biblioteca estándar; SHA256 y Git blob SHA1 se calcularon en **la misma pasada**, sin deserializar ni importar modelos. Antes/después de cada lectura se compararon tamaño, mtime/ctime, volumen e identidad del archivo; al final se revalidaron metadatos de todas las rutas sin releer contenido. Ninguna cambió. La caché local permite reutilizar resultados si esa identidad/metadatos siguen iguales; no se publicó configuración ni la caché operativa.

Las referencias HF se consultaron mediante API JSON `revision/<SHA>?blobs=true`, verificando el commit. Para LFS, `lfs.sha256` es la referencia de contenido. Para archivos normales, HF publica Git blob SHA1 y tamaño: **no se inventó un SHA256 oficial**. El blobId de una entrada LFS identifica su puntero y no se compara con los bytes del peso. SHA1 se informa separado, con su algoritmo y alcance.

| Cobertura | Resultado |
|---|---|
| Archivos catalogados con SHA256 oficial | 66 de87 |
| Archivos catalogados sin SHA256 oficial | 21 de87; SHA256 local calculado y Git blob contrastado por separado |
| Comparaciones SHA256 por ruta, incluyendo segundo conjunto ACE | 73 coincidencias; 1 diferencias |
| Git blob de archivos normales, incluidos documentos y segundo conjunto ACE | 42 coincidencias; 0 diferencias |
| Errores de lectura / rutas cambiadas | 0 / 0 |

Las comparaciones por ruta incluyen copias necesarias para contrastar ambos conjuntos; no son el recuento de87 entradas del catálogo. Referencia no disponible no significa diferencia ni archivo correcto por defecto. No se acredita que un modelo cargue o sea compatible por coincidir su hash.

## Diferencias

Para asociar resultados se exigió la ruta relativa exacta dentro de cada raíz ACE. Los candidatos por basename del inventario de búsqueda no bastan: el config.json raíz, el del encoder, el del LM y el del VAE son archivos distintos. Sus hashes se calcularon una vez por ruta y se reutilizaron en la comparación correcta.

- Ruta: `D:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders/qwen_3_4b.safetensors`.
  SHA256 local: `a5e1c4ed3f2d45531da55eaa977e44e40b8cfde7c2ebc53a5288b9573c3f45bc`.
  SHA256 oficial: `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a`.
  Fuente: `Comfy-Org/flux2-klein-4B@5b3abca5c0dc1ecd4eaf3340868d09063fc1c965`, archivo `split_files/text_encoders/qwen_3_4b.safetensors`.

El encoder conserva el tamaño8044982048bytes y sus metadatos permanecieron estables. Catálogo y API oficial fijada coinciden en la referencia esperada. No se repitió una lectura de8GB para obtener el mismo dato ni se diagnosticó la causa sin evidencia: puede ser contenido de otra revisión o alterado; no se afirma cuál. **No certificar este archivo como idéntico a la referencia fijada.** No se cambia configuración ni se ejecuta reparación.

## Referencias SHA256 no disponibles

Estos21 archivos normales del catálogo no publican SHA256 LFS en la revisión consultada. El SHA256 local está en el JSON; el estado de Git blob siguiente solo acredita la comparación con ese identificador oficial, no una referencia SHA256 que no existe.

| Familia / archivo remoto | Git blob oficial | Resultado |
|---|---|---|
| kokoro / README.md | `d6dc124205ad567631d14cd8700f1af77a861c3f` | match |
| kokoro / config.json | `14a726edd3718279eac426630879ff743955b16a` | match |
| acestep / Qwen3-Embedding-0.6B/added_tokens.json | `b54f9135e44c1e81047e8d05cb027af8bc039eed` | match |
| acestep / Qwen3-Embedding-0.6B/chat_template.jinja | `699ff8df401fe4788525e9c1f9b86a99eadd6230` | match |
| acestep / Qwen3-Embedding-0.6B/config.json | `21bd712c76114dc22587c6eeb84ab64186c9d245` | match |
| acestep / Qwen3-Embedding-0.6B/merges.txt | `31349551d90c7606f325fe0f11bbb8bd5fa0d7c7` | match |
| acestep / Qwen3-Embedding-0.6B/special_tokens_map.json | `ac23c0aaa2434523c494330aeb79c58395378103` | match |
| acestep / Qwen3-Embedding-0.6B/tokenizer_config.json | `ddaf69808214a44fdd26d3785b66c1367c78277a` | match |
| acestep / Qwen3-Embedding-0.6B/vocab.json | `4783fe10ac3adce15ac8f358ef5462739852c569` | match |
| acestep / README.md | `a3115cec283fbdc2d500aa50fdffac3c87e6689a` | match |
| acestep / acestep-5Hz-lm-1.7B/added_tokens.json | `584075018edeacd6dcc031b3e2cbbf90836eba41` | match |
| acestep / acestep-5Hz-lm-1.7B/chat_template.jinja | `01be9b307daa2d425f7c168c9fb145a286e0afb4` | match |
| acestep / acestep-5Hz-lm-1.7B/config.json | `1325891e0f2cb06ea22906f9c89047d09d0dac1f` | match |
| acestep / acestep-5Hz-lm-1.7B/merges.txt | `31349551d90c7606f325fe0f11bbb8bd5fa0d7c7` | match |
| acestep / acestep-5Hz-lm-1.7B/special_tokens_map.json | `aa26266349a0f38be608e07138c9047356309551` | match |
| acestep / acestep-5Hz-lm-1.7B/vocab.json | `4783fe10ac3adce15ac8f358ef5462739852c569` | match |
| acestep / acestep-v15-turbo/config.json | `6a0b5c09a654614302947fd1d7041f7ed0764d8c` | match |
| acestep / acestep-v15-turbo/configuration_acestep_v15.py | `965a1b73afb1c89d0959c7d80691e487fdfde505` | match |
| acestep / acestep-v15-turbo/modeling_acestep_v15_turbo.py | `fa1162a5a01cc45c7959f3c531e2a8272ca05104` | match |
| acestep / config.json | `6a0b5c09a654614302947fd1d7041f7ed0764d8c` | match |
| acestep / vae/config.json | `f49eb7b261dde15ed29c0fa1e790251dcecbd280` | match |

Los2 documentos tampoco tienen SHA256 LFS publicado: sus SHA256 se calcularon localmente y sus Git blob SHA1 se contrastaron con la revisión. Es una limitación de referencia, no un fallo de lectura.

## Ambos conjuntos ACE-Step conservados

**27/27 pares tienen SHA256 idéntico**, comparando la misma ruta relativa en `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5` y `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step-1.5`. El JSON incluye los27 pares y sus hashes. No se eliminó ni consolidó ninguno. Igualdad entre copias se distingue de comparación oficial: LFS por SHA256 y archivos normales por Git blob SHA1 cuando no hay SHA256 publicado.

## Fuentes fijadas

- [ACE-Step/Ace-Step1.5@19671f406d603126926c1b7e2adc169acbcade22](https://huggingface.co/ACE-Step/Ace-Step1.5/tree/19671f406d603126926c1b7e2adc169acbcade22).
- [Comfy-Org/flux2-dev@9630c1b4b6e690497ae0c19bb6b1b35d4ebedcb7](https://huggingface.co/Comfy-Org/flux2-dev/tree/9630c1b4b6e690497ae0c19bb6b1b35d4ebedcb7).
- [Comfy-Org/flux2-klein-4B@5b3abca5c0dc1ecd4eaf3340868d09063fc1c965](https://huggingface.co/Comfy-Org/flux2-klein-4B/tree/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965).
- [black-forest-labs/FLUX.2-klein-4b-fp8@5b4408e59397a4a37ccb46afe426d8ed86379441](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8/tree/5b4408e59397a4a37ccb46afe426d8ed86379441).
- [hexgrad/Kokoro-82M@f3ff3571791e39611d31c381e3a41a3af07b4987](https://huggingface.co/hexgrad/Kokoro-82M/tree/f3ff3571791e39611d31c381e3a41a3af07b4987).

Solo se escribieron informes y caché de resultados dentro del proyecto. Modelos/documentos originales y ambos conjuntos ACE permanecen intactos. Sin descargas, instalaciones, movimiento, borrado, carga/inferencia ni cambios de configuraciones/ComfyUI. Costo$0; PR#2 permanece en borrador. La CI verifica el repositorio, no sustituye estos hashes ni prueba inferencia.
