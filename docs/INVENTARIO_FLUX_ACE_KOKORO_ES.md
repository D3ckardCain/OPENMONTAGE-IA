# Inventario físico: FLUX.2/klein, ACE-Step1.5 y Kokoro

24-11-2026 UTC. Seguimiento #3/#82/#83/#86. **Los87 archivos del catálogo tienen alternativa presente con nombre/ruta relativa y tamaño coincidente. Lista mínima de pesos a descargar: vacía,0archivos/0bytes.** No instalar, copiar ni redescargar por las rutas antiguas de C:.

[Detalle verificable JSON](INVENTARIO_FLUX_ACE_KOKORO_20261124.json):114 archivos encontrados,87 comparaciones de catálogo, tamaños oficiales y rutas, revisiones esperadas, raíces recorridas y limitaciones. No contiene pesos, configuraciones personales ni credenciales.

## Método y alcance

Primero se consultó `docs/models/base.json`, inventarios adicionales/documentación de adaptadores y almacenamiento, y rutas guardadas de Studio. El catálogo usa `C:/OPENMONTAJE-IA/…`; la aplicación actual está en `C:/OPENMONTAGE-IA`, nombres distintos. Después se enumeraron por nombre las carpetas DESCARGAS_MODELOS, models de ComfyUI y descargas de D:/E:, Descargas del usuario y cachés HF/Torch en C:. El JSON registra cada raíz; la cuenta Windows se expresa como `%USERPROFILE%`.

Se usó enumeración y stat, sin importar runtimes, abrir/deserializar pesos ni inferencia. Consulta remota limitada a JSON de metadatos y textos de licencia/model card; ningún peso o recurso se guardó.87 tamaños del catálogo contrastados con API oficial HF en su revisión fijada. **Nombre+tamaño no prueban identidad SHA256, integridad, revisión real del contenido, compatibilidad ni carga funcional.** Los hashes del JSON son referencias esperadas del catálogo/metadatos, no hashes locales recalculados.

## Discos y rutas ausentes

| Volumen | Observación |
|---|---|
| C: Windows | Conectado y raíz enumerada. Las carpetas antiguas C:/OPENMONTAJE-IA/DESCARGAS_MODELOS y ComfyUI/models no existen allí. No es disco desconectado. |
| D: ADATA | Conectado, carpetas de modelos accesibles. Encoder/VAE de FLUX, ACE-Step y Kokoro encontrados. |
| E: Seagate Basic | Conectado, modelos accesibles. Transformer klein encontrado; carpetas alternativas ACE-Step y Kokoro existentes pero vacías de archivos. |

No hubo errores de acceso/I/O en las raíces recorridas ni volumen desconectado observado. No es búsqueda forense de todos los directorios del sistema: no se recorrieron Windows/Program Files, papelera o carpetas privadas ajenas al alcance. En otro momento, un volumen no disponible debe marcarse `volume_unavailable`, nunca como descarga pendiente. Un acceso denegado tampoco demuestra ausencia.

## Ubicaciones y tamaños exactos

| Recurso | Ruta encontrada | Bytes |
|---|---|---:|
| klein4B distilled FP8 | E:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models/flux-2-klein-4b-fp8.safetensors | 4070624520 |
| Encoder compartido Qwen3_4B | D:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders/qwen_3_4b.safetensors | 8044982048 |
| VAE FLUX.2 | D:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae/flux2-vae.safetensors | 336213556 |
| ACE turbo | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-v15-turbo/model.safetensors | 4787825604 |
| ACE LM1.7B | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B/model.safetensors | 3708521528 |
| ACE encoder0.6B | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B/model.safetensors | 1191586416 |
| ACE VAE | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/vae/diffusion_pytorch_model.safetensors | 337431388 |
| Kokoro v1.0 | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/kokoro-v1_0.pth | 327212226 |
| Voz española ef_dora | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices/ef_dora.pt | 523420 |
| Voz española em_alex | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices/em_alex.pt | 523420 |
| Voz española em_santa | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices/em_santa.pt | 523430 |

FLUX suma12451820124bytes en3 archivos repartidos entre discos. No completar cada disco descargando los archivos que están en el otro; no se comprobó resolución de rutas del grafo activo ni se modificó extra_model_paths.

ACE tiene **27/27** archivos (10092100853bytes por conjunto), incluyendo configuración/tokenizers/código auxiliar y silence_latent. Existe además `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step-1.5` con los mismos27 nombres relativos y tamaños: posible duplicación, sin igualdad criptográfica acreditada. No borrar, mover ni consolidar. `E:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5` contiene4 directorios y0 archivos: ausencia verificable en esa carpeta, no en todo el equipo.

Kokoro tiene **57/57** archivos (355485634bytes): README, config, peso y54 voces, incluidas las3 españolas. En E: su carpeta alternativa contiene1 directorio y0 archivos. No descargar otra copia para llenarla.

## Versiones esperadas y licencias por componente

Estas revisiones son la procedencia esperada del catálogo/servidor, **no revisión local demostrada por hash**.

| Componente | Fuente/revisión fijada | Licencia / límite |
|---|---|---|
| klein4B FP8 | [BFL](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8/tree/5b4408e59397a4a37ccb46afe426d8ed86379441) | Apache-2.0; LICENSE.md contrastado. No9B/dev. |
| Qwen3_4B split Comfy | [Comfy-Org](https://huggingface.co/Comfy-Org/flux2-klein-4B/tree/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965) | Metadata Apache-2.0; no confundir con layout Qwen3-4B-FP8 Transformers. |
| VAE split encontrado | [Comfy-Org/flux2-dev](https://huggingface.co/Comfy-Org/flux2-dev/tree/9630c1b4b6e690497ae0c19bb6b1b35d4ebedcb7) | Repo declara `other` y enlaza licencia dev; BFL declara autoencoder Apache por recurso. Alcance del split exacto debe quedar documentado antes de redistribución, no heredar licencia del repo completo ni declarar VAE NC sin más. |
| ACE1.5 turbo/LM/encoder/VAE | [ACE-Step](https://huggingface.co/ACE-Step/Ace-Step1.5/tree/19671f406d603126926c1b7e2adc169acbcade22) | Model card MIT principal; recursos/LoRA externos independientes. No sustituir1.7B por0.6B oXL. |
| Kokoro82M v1.0 y voces | [hexgrad](https://huggingface.co/hexgrad/Kokoro-82M/tree/f3ff3571791e39611d31c381e3a41a3af07b4987) | Apache-2.0 declarado; conservar VOICES.md/atribuciones específicas y derechos de referencias separados. |

Hay **dos VAE con el mismo nombre en repos distintos**: split klein oficial Comfy mide336211292bytes y el split dev encontrado336213556. No son intercambiables por nombre/tamaño ni se propone bajar otro VAE. Tampoco se propone el modelo4B BF16 de otra evaluación cuando ya hay4B FP8 catalogado.

## Lista mínima de descargas oficiales preparada, no ejecutada

**Pesos/config/tokenizers del alcance catalogado: ninguno falta tras localizar alternativas.0descargas.** No se incluyen paquetes runtime, modelos nuevos, otras voces, XL/9B ni copias para cada disco. Presencia no resuelve dependencias fonéticas de Kokoro, loaders/nodos ni memoria de ACE/FLUX; quedan fuera de este inventario de archivos.

Solo quedan dos candidatos documentales pequeños para acompañar la copia existente; son documentación, no requisitos para afirmar pesos presentes. No se descargaron. No confundirlos con licencia completa de todos los componentes ni autorización de distribución.

| Documento oficial | Versión/revisión | Licencia | Bytes | Destino propuesto, sin crearlo |
|---|---|---|---:|---|
| [LICENSE.md klein](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8/resolve/5b4408e59397a4a37ccb46afe426d8ed86379441/LICENSE.md) | 4B FP8 /5b4408e59397a4a37ccb46afe426d8ed86379441 | Apache-2.0 | 9584 | E:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models/flux-klein-4b-LICENSE.md |
| [VOICES.md Kokoro](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/VOICES.md) | v1.0 /f3ff3571791e39611d31c381e3a41a3af07b4987 | Repo Apache-2.0; avisos individuales aplicables | 7625 | D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/VOICES.md |

VOICES.md no existe en la carpeta encontrada; LICENSE klein no existe en el destino propuesto. No se afirma que no pueda existir otra copia documental fuera del alcance. Tamaños de API oficial en revisión fija; total documental17209bytes. Antes de cualquier futura descarga revalidar presencia, destino y necesidad; no activar herramientas de descarga por este informe.

## Conservación y resultado

Únicas escrituras: informes de esta tarea dentro del proyecto para publicación. Datos/modelos examinados solo en lectura. No se descargó/instaló/movió/cargó ningún modelo, no se cambió catálogo, rutas guardadas, .venv, ComfyUI o configuración. Settings SHA256497DDCD071B06F9AD4109E3123CDB36EBC6BB5A1F33AB53E556FE931B09AD952 y applications SHA25633073A45E5D34775AAE08CEF0557BCE23B59DDEAF0699BE26B70909DCE4CCF7B permanecen intactos. Costo$0, PR#2 en borrador.
