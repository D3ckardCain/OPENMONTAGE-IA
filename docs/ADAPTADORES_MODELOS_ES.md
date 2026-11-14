# Adaptadores de modelos descargados

Los adaptadores se descubren en el registro normal, como `model_kokoro`,
`model_faster_whisper`, `model_wan` y `model_grounding_dino`. El productor puede
usarlos con `execute_tool`, presupuesto cero y salidas dentro del proyecto.
No se instalan pesos ni dependencias automáticamente, no se sustituye la familia
seleccionada y no se cambia de GPU a CPU de forma silenciosa.

## Estado de integración

El catálogo completo tiene 46 familias: 21 rutas nativas implementadas y 25
conectores para workflows API de ComfyUI. **Un conector no demuestra que exista un
workflow compatible, que todos los nodos estén instalados ni que una GPU pueda
cargar el modelo.** WAN incluye el workflow T2V de cuatro pasos ya existente;
los demás conectores requieren un grafo compatible explícito. No se convierte
ACE-Step 1.5 en ACE-Step 1 ni un modelo de video en imágenes estáticas.

Las pruebas utilizan dependencias y salidas controladas, sin bajar modelos. No
certifican inferencia ni calidad de las 46 familias en el equipo del usuario.

## Configuración desde el estudio

En `/studio`, dentro de «Modelos y discos», pulsa «Detectar adaptadores y
dependencias». El diagnóstico busca en las carpetas de recursos configuradas:
`<raíz>/DESCARGAS_MODELOS/<repositorio>`, `<raíz>/OPENMONTAJE-IA/DESCARGAS_MODELOS/…`
o directamente la carpeta del repositorio. También puedes indicar una carpeta
movida sin reorganizar ni copiar pesos.

Cada adaptador nativo permite elegir un ejecutable Python absoluto. Esto separa
las dependencias de voz, visión y traducción del servidor web. `source_dir`
permite usar un checkout local del runtime oficial cuando no es una librería
instalada, por ejemplo CosyVoice o Depth Anything V2. No es una carpeta de pesos.

Se comprueban archivos del catálogo, índices y shards de la variante elegida.
Una coincidencia de ruta o tamaño del inventario no se usa como prueba de que
un archivo siga conectado. Los pesos se buscan de nuevo en el sistema local.

## Rutas nativas

| Familia / herramienta | Uso | Dependencias del Python elegido |
|---|---|---|
| `model_kokoro` | Voz con modelo, configuración y voz `.pt` locales | torch, kokoro, soundfile y recursos fonéticos del idioma |
| `model_qwen_tts` | Voz a partir de audio y transcripción de referencia | torch, qwen-tts, soundfile |
| `model_voice_design` | Diseño de voz por instrucción | torch, qwen-tts, soundfile |
| `model_chatterbox` | Voz multilingüe desde `from_local` | torch, chatterbox-tts, soundfile |
| `model_cosyvoice` | Voz zero-shot con recursos locales | runtime oficial CosyVoice y sus dependencias, torch, torchaudio |
| `model_faster_whisper` | Transcripción y tiempos por palabra | faster-whisper |
| `model_parakeet` | Transcripción con modelo TDT | torch, transformers con AutoModelForTDT, soundfile |
| `model_aligner` | Alineación texto/audio | torch, qwen-asr |
| `model_m2m100` | Traducción con idiomas origen/destino | torch, transformers, sentencepiece |
| `model_minilm` | Embeddings multilingües normalizados | sentence-transformers |
| `model_qwen3` | Texto local con formato de conversación | torch, transformers compatible con Qwen3, accelerate |
| `model_qwen_vl`, `model_smolvlm` | Consulta sobre una imagen real | torch, transformers con AutoModelForImageTextToText, Pillow; accelerate para Qwen |
| `model_florence` | Descripción, OCR o detección por token de tarea | torch, transformers compatible con código local Florence, Pillow y dependencias del repositorio |
| `model_grounding_dino` | Detección de objetos indicados en texto | torch, transformers, Pillow |
| `model_siglip` | Comparación imagen/etiquetas | torch, transformers, Pillow |
| `model_birefnet` | Recorte de fondo con transparencia | torch, torchvision, transformers, Pillow y dependencias del repositorio |
| `model_depth` | Profundidad relativa ViT-S, PNG 16 bits y NPY | torch, código oficial depth_anything_v2, opencv-python |
| `model_silero` | Probabilidad de voz por ventanas | onnxruntime, numpy, soundfile |
| `model_ocr_latin`, `model_ocr_det` | Reconocimiento latino / detección de texto | paddleocr y PaddlePaddle compatible |

La detección de imports es una comprobación preliminar: versiones incompatibles,
recursos fonéticos, paquetes auxiliares o nodos de terceros pueden faltar aunque
el módulo principal exista. El error real del runtime se conserva y bloquea esa
ruta. No se afirma que una lista genérica de paquetes sea un entorno validado.
No instales todas estas librerías en el mismo entorno: algunas requieren
versiones diferentes de torch y transformers.

### Entradas y resultados

Todos los adaptadores exigen `output_dir`. La ejecución de agentes lo restringe
al proyecto activo. Parámetros relevantes:

- Voz: `text`, `language`, `voice` para Kokoro, `reference_audio` y
  `reference_text` para Qwen Base/CosyVoice; `instruction` para VoiceDesign.
  Las referencias deben ser archivos locales. El resultado es `voice.wav`.
- Traducción: `text`, `source_language`, `language` de destino. Para M2M100,
  usa códigos del tokenizer, por ejemplo `es` y `en`.
- Transcripción/alineación: `input_path` local; alineación también necesita
  `text` y `language`. Parakeet y Silero requieren audio mono a 16 kHz.
- Visión: `input_path` de imagen; Qwen/SmolVLM necesitan `text` como pregunta,
  DINO necesita la lista de objetos como texto, SigLIP necesita `labels`.
- Florence: `instruction` es un token de tarea, por defecto `<DETAILED_CAPTION>`.
- Embeddings: `texts` o un `text` individual.
- `device` vale `cpu` por defecto. `cuda` es una elección explícita y falla si
  CUDA no está disponible. El worker CPU oculta CUDA para evitar una selección
  automática contraria a la solicitud.

Se guardan solicitud, respuesta y resultados dentro de la carpeta de salida.
Cada inferencia nativa ocurre en un proceso separado con timeout. Hub y
Transformers están offline; el worker bloquea conexiones TCP y datagramas para
impedir descargas ocultas de otros runtimes. Si falta un recurso local se
informa como dependencia. No se acredita calidad solo porque existe un archivo.

Kokoro necesita una voz local, por ejemplo `ef_dora` para español cuando ese
archivo esté instalado. No se descargan voces por nombre. Los recursos
fonéticos del idioma también deben estar instalados previamente.

## Las 25 conexiones ComfyUI

Video: wan, cosmos, ltx-legacy, mochi, cogvideo, kandinsky, longcat,
longcat-avatar, magihuman, ltx23, ltx25, hunyuan15, framepack, h3, wan-vace,
wan-camera, wan-control y wan-s2v.

Imagen/edición: qwen-image, flux-klein, z-image, qwen-edit y lama.
Audio: acestep. Pose: dwpose.

Configura `workflow_path` (JSON exportado en formato API) y `output_node`.
`bindings` cambia campos concretos que ya existan en el grafo. El adaptador
comprueba que el workflow referencia pesos de la familia, que los nodos están
registrados, que las opciones/modelos seleccionados existen y que el nodo de
salida sea realmente un nodo de salida. Esto valida estructura y registro, no
la compatibilidad matemática ni el resultado artístico de un grafo.

El productor puede consultar `comfy_nodes` para leer contratos reales de hasta
12 clases por llamada, escribir un grafo con `write_project_file` y usar
`bind_workflow` para vincularlo después de validarlo. Esa acción solo admite
archivos de trabajo del proyecto; no modifica el Python ni mueve pesos.
`adapter_status` explica qué le falta a una familia antes de ejecutarla.

La ejecución persiste `prompt_id` y hash del grafo **antes** de esperar. Si
ComfyUI sigue trabajando después de un timeout, se puede usar
`resume_prompt_id` con el mismo grafo y carpeta; no se vuelve a enviar el trabajo.
Los medios se descargan con su extensión real. No se cancela silenciosamente
una tarea de ComfyUI ni se declara éxito sin archivos no vacíos.

Los grafos con nodos de terceros conservan el comportamiento de esos nodos.
El bloqueo de red del worker nativo no se aplica al proceso externo de ComfyUI;
usa nodos locales y revisa sus dependencias/servicios antes de aprobar el grafo.

## Fuentes de implementación

- [Kokoro: modelo](https://github.com/hexgrad/kokoro/blob/main/kokoro/model.py) y [pipeline](https://github.com/hexgrad/kokoro/blob/main/kokoro/pipeline.py).
- [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base).
- [Chatterbox multilingual](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/mtl_tts.py).
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice).
- [Qwen3 ForcedAligner](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B).
- [Parakeet](https://huggingface.co/docs/transformers/model_doc/parakeet).
- [Grounding DINO](https://huggingface.co/docs/transformers/model_doc/grounding-dino).
- [Florence-2](https://huggingface.co/microsoft/Florence-2-large-ft).

Los archivos de código propios del modelo se ejecutan solo desde la carpeta
local ya instalada (`local_files_only=True`); no se obtiene código remoto durante
la inferencia. Conserva las licencias de cada modelo y recurso de audio.
