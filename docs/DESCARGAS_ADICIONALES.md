# Ampliación de descargas y candidatos locales

Actualizado: 12 de noviembre de 2026. Registro de lo comunicado después del
[catálogo original de 375 archivos](DESCARGAS_CANDIDATOS.md); **no es una nueva orden
de volver a descargarlo todo**. «Ya/listo» en el chat se interpreta como comunicado
por el usuario, no como verificación física. No se ha probado inferencia.

## Lectura del registro

Los enlaces HF se fijan a revisiones concretas. El
[manifiesto adicional](model_download_manifest_additional.json) registra tamaños,
SHA256 de archivos LFS y Git blob SHA1 de archivos pequeños (no confundir ambos).
Se compararon identidades de contenido con el manifiesto original y entre las nuevas
entradas. Esto no sustituye comparar los archivos locales con esos hashes.
Los componentes idénticos pueden figurar como reutilización, con un destino futuro
que aún debe copiarse/enlazarse. Los destinos actuales son ADATA, D:, salvo indicación
de reutilizar el otro disco. No borrar extras del usuario.

La revisión legal es por candidato y fuente: no certifica todos los auxiliares,
ejecutores, datos ni derechos de contenido. Código descargado y conversiones de
terceros requieren revisión antes de ejecutarse. Licencias permisivas no garantizan
compatibilidad con Python 3.13, Windows ni RTX 4060 de 8 GB.

## Índice y licencias

| Candidato | Uso | Licencia documentada | Estado |
|---|---|---|---|
| [Comfy-Org/Qwen-Image-Edit](https://huggingface.co/Comfy-Org/Qwen-Image-Edit/tree/f68ace85e60b4a02a323e394253731947657b7d2) | Edición de imágenes | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3/tree/edaa852ec7e145841d8ffdb056a99866b5f0a478) | Transcripción multilingüe | MIT | Comunicado; integridad e integración pendientes |
| [ResembleAI/chatterbox](https://huggingface.co/ResembleAI/chatterbox/tree/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18) | Voz multilingüe, incluido español | MIT | Comunicado; integridad e integración pendientes |
| [FunAudioLLM/Fun-CosyVoice3-0.5B-2512](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/tree/29e01c4e8d000f4bcd70751be16fa94bf3d85a18) | Voz multilingüe, incluido español | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [depth-anything/Depth-Anything-V2-Small](https://huggingface.co/depth-anything/Depth-Anything-V2-Small/tree/03876f8651c73a60fe4c2c48294e09fcb6838fcf) | Mapas de profundidad | Apache-2.0 (solo Small) | Comunicado; integridad e integración pendientes |
| [Qwen/Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/tree/b968826d9c46dd6066d109eabc6255188de91218) | Director y guiones locales; español prioritario | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [Qwen/Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/tree/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b) | Comprensión visual y revisión | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [alibaba-pai/Wan2.2-VACE-Fun-A14B](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/tree/4438caabbfdd7437bbb0283d86cb200d1b7223ba) | Edición y control de vídeo | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [alibaba-pai/Wan2.2-Fun-A14B-Control-Camera](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control-Camera/tree/da1f119dcf5626b2fa41219ce42ac175752f3892) | Control de cámara | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [Qwen/Qwen3-ForcedAligner-0.6B](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/tree/c7cbfc2048c462b0d63a45797104fc9db3ad62b7) | Tiempos por palabra para subtítulos | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [ZhengPeng7/BiRefNet](https://huggingface.co/ZhengPeng7/BiRefNet/tree/e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4) | Separación de fondo | MIT declarada; revisión del código pendiente | Comunicado; integridad e integración pendientes |
| [IDEA-Research/grounding-dino-base](https://huggingface.co/IDEA-Research/grounding-dino-base/tree/12bdfa3120f3e7ec7b434d90674b3396eccf88eb) | Detección guiada por texto | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [microsoft/Florence-2-large](https://huggingface.co/microsoft/Florence-2-large/tree/21a599d414c4d928c9032694c424fb94458e3594) | OCR y descripciones de imágenes | MIT | Comunicado; integridad e integración pendientes |
| [google/siglip2-base-patch16-224](https://huggingface.co/google/siglip2-base-patch16-224/tree/75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2) | Correspondencia texto-imagen | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [facebook/m2m100_418M](https://huggingface.co/facebook/m2m100_418M/tree/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636) | Traducción, incluido español | MIT | Comunicado; integridad e integración pendientes |
| [nvidia/parakeet-tdt-0.6b-v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3/tree/541d1f99c6b0c3cd0b11a95167540bb8edefd82b) | Transcripción alternativa multilingüe | CC-BY-4.0; requiere atribución | Comunicado; integridad e integración pendientes |
| [HuggingFaceTB/SmolVLM2-2.2B-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/tree/be92141c8d0ceb98596a923c308ac2bbb4a7c466) | Comprensión visual alternativa | Apache-2.0; inglés prioritario | Comunicado; integridad e integración pendientes |
| [alibaba-pai/Wan2.2-Fun-A14B-Control](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control/tree/297be6d520f54908e124be0298e2317ee50ffdf4) | Control por pose, contorno y profundidad | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [Wan-AI/Wan2.2-S2V-14B](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/tree/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b) | Imagen y audio a vídeo; ejemplo oficial de 80 GB VRAM | Apache-2.0; auxiliar wav2vec2 también Apache-2.0 | Comunicado; integridad e integración pendientes |
| [Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/tree/5ecdb67327fd37bb2e042aab12ff7391903235d3) | Diseño de voces por descripción; español e inglés | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [yzd-v/DWPose](https://huggingface.co/yzd-v/DWPose/tree/1a7144101628d69ee7a3768d1ee3a094070dc388) | Poses de cuerpo, manos y rostro | Apache-2.0 declarada | Comunicado; integridad e integración pendientes |
| [smartywu/big-lama](https://huggingface.co/smartywu/big-lama/tree/05cb2be7f8dbe6ca7c6e78f4fc827a4b2baaa4a9) | Borrado de objetos y relleno de imágenes | Apache-2.0 declarada; espejo de tercero | Comunicado; integridad e integración pendientes |
| [onnx-community/silero-vad](https://huggingface.co/onnx-community/silero-vad/tree/e71cae966052b992a7eca6b17738916ce0eca4ec) | Detección de voz y silencios | MIT; conversión de terceros | Comunicado; integridad e integración pendientes |
| [sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/tree/e8f8c211226b894fcb81acc59f3b34ba3efd5f42) | Búsqueda semántica y comparación de textos multilingües | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [PaddlePaddle/latin_PP-OCRv5_mobile_rec](https://huggingface.co/PaddlePaddle/latin_PP-OCRv5_mobile_rec/tree/ab2cd5cc5fa6309be2e5acdfe66eca2c2c127d57) | Reconocimiento OCR latino, incluido español | Apache-2.0 | Comunicado; integridad e integración pendientes |
| [PaddlePaddle/PP-OCRv5_mobile_det](https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_det/tree/0d63e78e2b680928f6b1747d76a08db6e645efb7) | Detección de zonas con texto | Apache-2.0 | Comunicado; integridad e integración pendientes |

Además se comunicaron cuatro grupos de utilidades desde sus repositorios originales:

| Grupo | Licencia | Uso | Fuente |
|---|---|---|---|
| Real-ESRGAN | BSD-3-Clause | Escalado/restauración | [Proyecto](https://github.com/xinntao/Real-ESRGAN) |
| Demucs v4 | MIT | Separación de pistas | [Proyecto archivado](https://github.com/facebookresearch/demucs) |
| SAM 2.1 | Apache-2.0 para pesos | Máscaras y seguimiento | [Proyecto](https://github.com/facebookresearch/sam2) |
| DeepFilterNet3 | MIT o Apache-2.0 | Reducción de ruido de voz | [Proyecto](https://github.com/Rikorose/DeepFilterNet) |

Parakeet requiere conservar atribución CC-BY-4.0. Depth Anything V2 solo se aprobó
como candidato **Small** Apache-2.0; no extenderlo a sus pesos mayores no comerciales.
LaMa y Silero aquí enlazados son espejos/conversiones de terceros, no publicaciones
originales de los autores. SmolVLM2 prioriza inglés; no sustituye la prioridad español.
Wan S2V se reserva para hardware apropiado: su ejemplo oficial utiliza 80 GB de VRAM;
no se ha demostrado en esta laptop.

## Dependencias compartidas y duplicados detectados

- Qwen Image Edit: reutilizar el encoder y VAE de Qwen Image del catálogo original.
- SigLIP2: `tokenizer.model` se omitió por identidad con el tokenizer Gemma/T5 ya
  registrado (SHA256 `61a7b147390c64585d6c3543dd6fc636906c9af3865a5548f27f31aee1d4c8e2`).
- Qwen VoiceDesign: generation config, merges, preprocessor, tokenizer config,
  vocab y los cuatro archivos de `speech_tokenizer/` son compartidos con Qwen3-TTS
  0.6B Base. Se comunicaron solo modelo, configuración y README nuevos.
- Wan VACE/Camera/Control/S2V: reutilizar los auxiliares T5, VAE y tokenizer que
  coincidan por hash. El T5 BF16 nativo de 11.361.920.418 bytes del segundo disco
  todavía requiere comprobación local de identidad.
- Control-Camera: high y low tienen idéntico tamaño, pero SHA256 distintos:
  `b242a310d161460d3ecf8430d4f8ee01398bebc3925a479c267b71318e8e30ad`
  y `277a7b0374f9d0d5ba0e769fa9648687301cfff8b32d32c9b57d122dbea24c02`.
  Sus dos configs sí son idénticos; copiar uno al otro destino cuando se integre.
- Control sin Camera tiene pesos diferentes de Camera y VACE. Sus high/low también
  son distintos entre sí, aunque comparten nombre y tamaño:
  `e4be07ca25d67aaf3461ef87fbb5ad8762f602a5efa620aea9dc250ac2747a9d`
  y `d82bc21cd703e089eee4f6fabc25e90ebbd00965623fdc5e83d46d01dbeac2c3`.
  Los configs high/low se reutilizan entre sí, pero no son el config de Camera.
- DWPose necesita **ambos** ONNX: detector de personas y estimador de poses.
- PaddleOCR necesita detector y reconocedor; ambos repiten nombres de archivo,
  pero pesos y configuraciones son diferentes. Mantener carpetas separadas.
- Silero: se seleccionó solo `onnx/model.onnx`; se omiten formatos/cuantizaciones
  alternativas. MiniLM: solo pesos safetensors, sin PyTorch/TF/ONNX/OpenVINO duplicados.

Las reutilizaciones automáticas adicionales figuran al final y en el manifiesto.
El manifiesto adicional cubre archivos HF explícitamente seleccionados, **no todos
los auxiliares omitidos por reutilización ni las fuentes externas**. No debe utilizarse
como certificado de que un grupo está listo para funcionar sin conexión.

## Archivos de Hugging Face ya comunicados

Las tablas preservan los destinos de la conversación. Si una entrada se identifica
como compartida, consultar el mapa de reutilización antes de descargar otra copia.

### Comfy-Org/Qwen-Image-Edit

Revisión `f68ace85e60b4a02a323e394253731947657b7d2`. Edición de imágenes.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [split_files/diffusion_models/qwen_image_edit_2511_fp8mixed.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image-Edit/resolve/f68ace85e60b4a02a323e394253731947657b7d2/split_files/diffusion_models/qwen_image_edit_2511_fp8mixed.safetensors?download=true) | `D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\diffusion_models\` |

### Systran/faster-whisper-large-v3

Revisión `edaa852ec7e145841d8ffdb056a99866b5f0a478`. Transcripción multilingüe.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.bin](https://huggingface.co/Systran/faster-whisper-large-v3/resolve/edaa852ec7e145841d8ffdb056a99866b5f0a478/model.bin?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Systran--faster-whisper-large-v3\` |
| [config.json](https://huggingface.co/Systran/faster-whisper-large-v3/resolve/edaa852ec7e145841d8ffdb056a99866b5f0a478/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Systran--faster-whisper-large-v3\` |
| [preprocessor_config.json](https://huggingface.co/Systran/faster-whisper-large-v3/resolve/edaa852ec7e145841d8ffdb056a99866b5f0a478/preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Systran--faster-whisper-large-v3\` |
| [tokenizer.json](https://huggingface.co/Systran/faster-whisper-large-v3/resolve/edaa852ec7e145841d8ffdb056a99866b5f0a478/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Systran--faster-whisper-large-v3\` |
| [vocabulary.json](https://huggingface.co/Systran/faster-whisper-large-v3/resolve/edaa852ec7e145841d8ffdb056a99866b5f0a478/vocabulary.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Systran--faster-whisper-large-v3\` |

### ResembleAI/chatterbox

Revisión `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`. Voz multilingüe, incluido español.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [t3_mtl23ls_v2.safetensors](https://huggingface.co/ResembleAI/chatterbox/resolve/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18/t3_mtl23ls_v2.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ResembleAI--chatterbox\` |
| [s3gen.pt](https://huggingface.co/ResembleAI/chatterbox/resolve/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18/s3gen.pt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ResembleAI--chatterbox\` |
| [ve.pt](https://huggingface.co/ResembleAI/chatterbox/resolve/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18/ve.pt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ResembleAI--chatterbox\` |
| [grapheme_mtl_merged_expanded_v1.json](https://huggingface.co/ResembleAI/chatterbox/resolve/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18/grapheme_mtl_merged_expanded_v1.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ResembleAI--chatterbox\` |
| [conds.pt](https://huggingface.co/ResembleAI/chatterbox/resolve/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18/conds.pt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ResembleAI--chatterbox\` |
| [Cangjie5_TC.json](https://huggingface.co/ResembleAI/chatterbox/resolve/5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18/Cangjie5_TC.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ResembleAI--chatterbox\` |

### FunAudioLLM/Fun-CosyVoice3-0.5B-2512

Revisión `29e01c4e8d000f4bcd70751be16fa94bf3d85a18`. Voz multilingüe, incluido español.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [CosyVoice-BlankEN/config.json](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/CosyVoice-BlankEN/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\CosyVoice-BlankEN\` |
| [CosyVoice-BlankEN/generation_config.json](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/CosyVoice-BlankEN/generation_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\CosyVoice-BlankEN\` |
| [CosyVoice-BlankEN/merges.txt](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/CosyVoice-BlankEN/merges.txt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\CosyVoice-BlankEN\` |
| [CosyVoice-BlankEN/model.safetensors](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/CosyVoice-BlankEN/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\CosyVoice-BlankEN\` |
| [CosyVoice-BlankEN/tokenizer_config.json](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/CosyVoice-BlankEN/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\CosyVoice-BlankEN\` |
| [CosyVoice-BlankEN/vocab.json](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/CosyVoice-BlankEN/vocab.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\CosyVoice-BlankEN\` |
| [README.md](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [asset/dingding.png](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/asset/dingding.png?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\asset\` |
| [campplus.onnx](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/campplus.onnx?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [config.json](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [configuration.json](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/configuration.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [cosyvoice3.yaml](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/cosyvoice3.yaml?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [flow.decoder.estimator.fp32.onnx](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/flow.decoder.estimator.fp32.onnx?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [flow.pt](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/flow.pt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [hift.pt](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/hift.pt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [llm.pt](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/llm.pt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [llm.rl.pt](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/llm.rl.pt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [speech_tokenizer_v3.batch.onnx](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/speech_tokenizer_v3.batch.onnx?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |
| [speech_tokenizer_v3.onnx](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/resolve/29e01c4e8d000f4bcd70751be16fa94bf3d85a18/speech_tokenizer_v3.onnx?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\FunAudioLLM--Fun-CosyVoice3-0.5B-2512\` |

### depth-anything/Depth-Anything-V2-Small

Revisión `03876f8651c73a60fe4c2c48294e09fcb6838fcf`. Mapas de profundidad.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [depth_anything_v2_vits.pth](https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/03876f8651c73a60fe4c2c48294e09fcb6838fcf/depth_anything_v2_vits.pth?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\depth-anything--Depth-Anything-V2-Small\checkpoints\` |
| [README.md](https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/03876f8651c73a60fe4c2c48294e09fcb6838fcf/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\depth-anything--Depth-Anything-V2-Small\` |

### Qwen/Qwen3-8B

Revisión `b968826d9c46dd6066d109eabc6255188de91218`. Director y guiones locales; español prioritario.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [LICENSE](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/LICENSE?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [README.md](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [generation_config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/generation_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [merges.txt](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/merges.txt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [model-00001-of-00005.safetensors](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model-00001-of-00005.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [model-00002-of-00005.safetensors](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model-00002-of-00005.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [model-00003-of-00005.safetensors](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model-00003-of-00005.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [model-00004-of-00005.safetensors](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model-00004-of-00005.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [model-00005-of-00005.safetensors](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model-00005-of-00005.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [tokenizer.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |
| [vocab.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/vocab.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-8B\` |

### Qwen/Qwen3-VL-8B-Instruct

Revisión `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`. Comprensión visual y revisión.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [README.md](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [chat_template.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/chat_template.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [config.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [generation_config.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/generation_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [merges.txt](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/merges.txt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [model-00001-of-00004.safetensors](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/model-00001-of-00004.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [model-00002-of-00004.safetensors](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/model-00002-of-00004.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [model-00003-of-00004.safetensors](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/model-00003-of-00004.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [model-00004-of-00004.safetensors](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/model-00004-of-00004.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/model.safetensors.index.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [preprocessor_config.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [tokenizer.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [video_preprocessor_config.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/video_preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |
| [vocab.json](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct/resolve/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b/vocab.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-VL-8B-Instruct\` |

### alibaba-pai/Wan2.2-VACE-Fun-A14B

Revisión `4438caabbfdd7437bbb0283d86cb200d1b7223ba`. Edición y control de vídeo.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [high_noise_model/diffusion_pytorch_model.safetensors](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/high_noise_model/diffusion_pytorch_model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\high_noise_model\` |
| [high_noise_model/config.json](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/high_noise_model/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\high_noise_model\` |
| [low_noise_model/diffusion_pytorch_model.safetensors](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/low_noise_model/diffusion_pytorch_model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\low_noise_model\` |
| [low_noise_model/config.json](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/low_noise_model/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\low_noise_model\` |
| [Wan2.1_VAE.pth](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/Wan2.1_VAE.pth?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\` |
| [configuration.json](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/configuration.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\` |
| [google/umt5-xxl/special_tokens_map.json](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/google/umt5-xxl/special_tokens_map.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\google\umt5-xxl\` |
| [google/umt5-xxl/spiece.model](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/google/umt5-xxl/spiece.model?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\google\umt5-xxl\` |
| [google/umt5-xxl/tokenizer.json](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/google/umt5-xxl/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\google\umt5-xxl\` |
| [google/umt5-xxl/tokenizer_config.json](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/google/umt5-xxl/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\google\umt5-xxl\` |
| [README.md](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\` |
| [README_en.md](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B/resolve/4438caabbfdd7437bbb0283d86cb200d1b7223ba/README_en.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-VACE-Fun-A14B\` |

### alibaba-pai/Wan2.2-Fun-A14B-Control-Camera

Revisión `da1f119dcf5626b2fa41219ce42ac175752f3892`. Control de cámara.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [high_noise_model/diffusion_pytorch_model.safetensors](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control-Camera/resolve/da1f119dcf5626b2fa41219ce42ac175752f3892/high_noise_model/diffusion_pytorch_model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control-Camera\high_noise_model\` |
| [high_noise_model/config.json](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control-Camera/resolve/da1f119dcf5626b2fa41219ce42ac175752f3892/high_noise_model/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control-Camera\high_noise_model\` |
| [low_noise_model/diffusion_pytorch_model.safetensors](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control-Camera/resolve/da1f119dcf5626b2fa41219ce42ac175752f3892/low_noise_model/diffusion_pytorch_model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control-Camera\low_noise_model\` |
| [low_noise_model/config.json](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control-Camera/resolve/da1f119dcf5626b2fa41219ce42ac175752f3892/low_noise_model/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control-Camera\low_noise_model\` |
| [configuration.json](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control-Camera/resolve/da1f119dcf5626b2fa41219ce42ac175752f3892/configuration.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control-Camera\` |
| [README_en.md](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control-Camera/resolve/da1f119dcf5626b2fa41219ce42ac175752f3892/README_en.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control-Camera\` |

### Qwen/Qwen3-ForcedAligner-0.6B

Revisión `c7cbfc2048c462b0d63a45797104fc9db3ad62b7`. Tiempos por palabra para subtítulos.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.safetensors](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |
| [config.json](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |
| [generation_config.json](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/generation_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |
| [preprocessor_config.json](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |
| [chat_template.json](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/chat_template.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |
| [tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |
| [merges.txt](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/merges.txt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |
| [vocab.json](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/vocab.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |
| [README.md](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B/resolve/c7cbfc2048c462b0d63a45797104fc9db3ad62b7/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-ForcedAligner-0.6B\` |

### ZhengPeng7/BiRefNet

Revisión `e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4`. Separación de fondo.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.safetensors](https://huggingface.co/ZhengPeng7/BiRefNet/resolve/e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ZhengPeng7--BiRefNet\` |
| [config.json](https://huggingface.co/ZhengPeng7/BiRefNet/resolve/e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ZhengPeng7--BiRefNet\` |
| [BiRefNet_config.py](https://huggingface.co/ZhengPeng7/BiRefNet/resolve/e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4/BiRefNet_config.py?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ZhengPeng7--BiRefNet\` |
| [birefnet.py](https://huggingface.co/ZhengPeng7/BiRefNet/resolve/e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4/birefnet.py?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ZhengPeng7--BiRefNet\` |
| [requirements.txt](https://huggingface.co/ZhengPeng7/BiRefNet/resolve/e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4/requirements.txt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ZhengPeng7--BiRefNet\` |
| [README.md](https://huggingface.co/ZhengPeng7/BiRefNet/resolve/e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\ZhengPeng7--BiRefNet\` |

### IDEA-Research/grounding-dino-base

Revisión `12bdfa3120f3e7ec7b434d90674b3396eccf88eb`. Detección guiada por texto.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.safetensors](https://huggingface.co/IDEA-Research/grounding-dino-base/resolve/12bdfa3120f3e7ec7b434d90674b3396eccf88eb/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\IDEA-Research--grounding-dino-base\` |
| [config.json](https://huggingface.co/IDEA-Research/grounding-dino-base/resolve/12bdfa3120f3e7ec7b434d90674b3396eccf88eb/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\IDEA-Research--grounding-dino-base\` |
| [preprocessor_config.json](https://huggingface.co/IDEA-Research/grounding-dino-base/resolve/12bdfa3120f3e7ec7b434d90674b3396eccf88eb/preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\IDEA-Research--grounding-dino-base\` |
| [special_tokens_map.json](https://huggingface.co/IDEA-Research/grounding-dino-base/resolve/12bdfa3120f3e7ec7b434d90674b3396eccf88eb/special_tokens_map.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\IDEA-Research--grounding-dino-base\` |
| [tokenizer.json](https://huggingface.co/IDEA-Research/grounding-dino-base/resolve/12bdfa3120f3e7ec7b434d90674b3396eccf88eb/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\IDEA-Research--grounding-dino-base\` |
| [tokenizer_config.json](https://huggingface.co/IDEA-Research/grounding-dino-base/resolve/12bdfa3120f3e7ec7b434d90674b3396eccf88eb/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\IDEA-Research--grounding-dino-base\` |
| [vocab.txt](https://huggingface.co/IDEA-Research/grounding-dino-base/resolve/12bdfa3120f3e7ec7b434d90674b3396eccf88eb/vocab.txt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\IDEA-Research--grounding-dino-base\` |
| [README.md](https://huggingface.co/IDEA-Research/grounding-dino-base/resolve/12bdfa3120f3e7ec7b434d90674b3396eccf88eb/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\IDEA-Research--grounding-dino-base\` |

### microsoft/Florence-2-large

Revisión `21a599d414c4d928c9032694c424fb94458e3594`. OCR y descripciones de imágenes.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.safetensors](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [config.json](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [generation_config.json](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/generation_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [preprocessor_config.json](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [tokenizer.json](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [tokenizer_config.json](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [vocab.json](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/vocab.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [configuration_florence2.py](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/configuration_florence2.py?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [modeling_florence2.py](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/modeling_florence2.py?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [processing_florence2.py](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/processing_florence2.py?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [LICENSE](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/LICENSE?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |
| [README.md](https://huggingface.co/microsoft/Florence-2-large/resolve/21a599d414c4d928c9032694c424fb94458e3594/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\microsoft--Florence-2-large\` |

### google/siglip2-base-patch16-224

Revisión `75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2`. Correspondencia texto-imagen.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.safetensors](https://huggingface.co/google/siglip2-base-patch16-224/resolve/75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\google--siglip2-base-patch16-224\` |
| [config.json](https://huggingface.co/google/siglip2-base-patch16-224/resolve/75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\google--siglip2-base-patch16-224\` |
| [preprocessor_config.json](https://huggingface.co/google/siglip2-base-patch16-224/resolve/75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2/preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\google--siglip2-base-patch16-224\` |
| [special_tokens_map.json](https://huggingface.co/google/siglip2-base-patch16-224/resolve/75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2/special_tokens_map.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\google--siglip2-base-patch16-224\` |
| [tokenizer.json](https://huggingface.co/google/siglip2-base-patch16-224/resolve/75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\google--siglip2-base-patch16-224\` |
| [tokenizer_config.json](https://huggingface.co/google/siglip2-base-patch16-224/resolve/75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\google--siglip2-base-patch16-224\` |
| [README.md](https://huggingface.co/google/siglip2-base-patch16-224/resolve/75de2d55ec2d0b4efc50b3e9ad70dba96a7b2fa2/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\google--siglip2-base-patch16-224\` |

### facebook/m2m100_418M

Revisión `55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636`. Traducción, incluido español.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [pytorch_model.bin](https://huggingface.co/facebook/m2m100_418M/resolve/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636/pytorch_model.bin?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebook--m2m100_418M\` |
| [config.json](https://huggingface.co/facebook/m2m100_418M/resolve/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebook--m2m100_418M\` |
| [generation_config.json](https://huggingface.co/facebook/m2m100_418M/resolve/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636/generation_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebook--m2m100_418M\` |
| [sentencepiece.bpe.model](https://huggingface.co/facebook/m2m100_418M/resolve/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636/sentencepiece.bpe.model?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebook--m2m100_418M\` |
| [special_tokens_map.json](https://huggingface.co/facebook/m2m100_418M/resolve/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636/special_tokens_map.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebook--m2m100_418M\` |
| [tokenizer_config.json](https://huggingface.co/facebook/m2m100_418M/resolve/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebook--m2m100_418M\` |
| [vocab.json](https://huggingface.co/facebook/m2m100_418M/resolve/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636/vocab.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebook--m2m100_418M\` |
| [README.md](https://huggingface.co/facebook/m2m100_418M/resolve/55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebook--m2m100_418M\` |

### nvidia/parakeet-tdt-0.6b-v3

Revisión `541d1f99c6b0c3cd0b11a95167540bb8edefd82b`. Transcripción alternativa multilingüe.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.safetensors](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3/resolve/541d1f99c6b0c3cd0b11a95167540bb8edefd82b/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\nvidia--parakeet-tdt-0.6b-v3\` |
| [config.json](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3/resolve/541d1f99c6b0c3cd0b11a95167540bb8edefd82b/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\nvidia--parakeet-tdt-0.6b-v3\` |
| [generation_config.json](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3/resolve/541d1f99c6b0c3cd0b11a95167540bb8edefd82b/generation_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\nvidia--parakeet-tdt-0.6b-v3\` |
| [processor_config.json](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3/resolve/541d1f99c6b0c3cd0b11a95167540bb8edefd82b/processor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\nvidia--parakeet-tdt-0.6b-v3\` |
| [tokenizer.json](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3/resolve/541d1f99c6b0c3cd0b11a95167540bb8edefd82b/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\nvidia--parakeet-tdt-0.6b-v3\` |
| [tokenizer_config.json](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3/resolve/541d1f99c6b0c3cd0b11a95167540bb8edefd82b/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\nvidia--parakeet-tdt-0.6b-v3\` |
| [README.md](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3/resolve/541d1f99c6b0c3cd0b11a95167540bb8edefd82b/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\nvidia--parakeet-tdt-0.6b-v3\` |

### HuggingFaceTB/SmolVLM2-2.2B-Instruct

Revisión `be92141c8d0ceb98596a923c308ac2bbb4a7c466`. Comprensión visual alternativa.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [README.md](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [added_tokens.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/added_tokens.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [chat_template.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/chat_template.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [config.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [generation_config.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/generation_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [merges.txt](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/merges.txt?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [model-00001-of-00002.safetensors](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/model-00001-of-00002.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [model-00002-of-00002.safetensors](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/model-00002-of-00002.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [model.safetensors.index.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/model.safetensors.index.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [preprocessor_config.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [processor_config.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/processor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [special_tokens_map.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/special_tokens_map.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [tokenizer.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [tokenizer_config.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |
| [vocab.json](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct/resolve/be92141c8d0ceb98596a923c308ac2bbb4a7c466/vocab.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\HuggingFaceTB--SmolVLM2-2.2B-Instruct\` |

### alibaba-pai/Wan2.2-Fun-A14B-Control

Revisión `297be6d520f54908e124be0298e2317ee50ffdf4`. Control por pose, contorno y profundidad.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [high_noise_model/diffusion_pytorch_model.safetensors](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control/resolve/297be6d520f54908e124be0298e2317ee50ffdf4/high_noise_model/diffusion_pytorch_model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control\high_noise_model\` |
| [low_noise_model/diffusion_pytorch_model.safetensors](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control/resolve/297be6d520f54908e124be0298e2317ee50ffdf4/low_noise_model/diffusion_pytorch_model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control\low_noise_model\` |
| [high_noise_model/config.json](https://huggingface.co/alibaba-pai/Wan2.2-Fun-A14B-Control/resolve/297be6d520f54908e124be0298e2317ee50ffdf4/high_noise_model/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\alibaba-pai--Wan2.2-Fun-A14B-Control\high_noise_model\` |

### Wan-AI/Wan2.2-S2V-14B

Revisión `dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b`. Imagen y audio a vídeo; ejemplo oficial de 80 GB VRAM.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [README.md](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\` |
| [config.json](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\` |
| [configuration.json](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/configuration.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\` |
| [diffusion_pytorch_model-00001-of-00004.safetensors](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/diffusion_pytorch_model-00001-of-00004.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\` |
| [diffusion_pytorch_model-00002-of-00004.safetensors](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/diffusion_pytorch_model-00002-of-00004.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\` |
| [diffusion_pytorch_model-00003-of-00004.safetensors](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/diffusion_pytorch_model-00003-of-00004.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\` |
| [diffusion_pytorch_model-00004-of-00004.safetensors](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/diffusion_pytorch_model-00004-of-00004.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\` |
| [diffusion_pytorch_model.safetensors.index.json](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/diffusion_pytorch_model.safetensors.index.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\` |
| [wav2vec2-large-xlsr-53-english/README.md](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/wav2vec2-large-xlsr-53-english/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\wav2vec2-large-xlsr-53-english\` |
| [wav2vec2-large-xlsr-53-english/config.json](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/wav2vec2-large-xlsr-53-english/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\wav2vec2-large-xlsr-53-english\` |
| [wav2vec2-large-xlsr-53-english/model.safetensors](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/wav2vec2-large-xlsr-53-english/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\wav2vec2-large-xlsr-53-english\` |
| [wav2vec2-large-xlsr-53-english/preprocessor_config.json](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/wav2vec2-large-xlsr-53-english/preprocessor_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\wav2vec2-large-xlsr-53-english\` |
| [wav2vec2-large-xlsr-53-english/special_tokens_map.json](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/wav2vec2-large-xlsr-53-english/special_tokens_map.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\wav2vec2-large-xlsr-53-english\` |
| [wav2vec2-large-xlsr-53-english/vocab.json](https://huggingface.co/Wan-AI/Wan2.2-S2V-14B/resolve/dab4e9c55bbe4c8c4d03db1c2c98c7f0ac9c454b/wav2vec2-large-xlsr-53-english/vocab.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Wan-AI--Wan2.2-S2V-14B\wav2vec2-large-xlsr-53-english\` |

### Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign

Revisión `5ecdb67327fd37bb2e042aab12ff7391903235d3`. Diseño de voces por descripción; español e inglés.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.safetensors](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/resolve/5ecdb67327fd37bb2e042aab12ff7391903235d3/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-TTS-12Hz-1.7B-VoiceDesign\` |
| [config.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/resolve/5ecdb67327fd37bb2e042aab12ff7391903235d3/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-TTS-12Hz-1.7B-VoiceDesign\` |
| [README.md](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/resolve/5ecdb67327fd37bb2e042aab12ff7391903235d3/README.md?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Qwen--Qwen3-TTS-12Hz-1.7B-VoiceDesign\` |

### yzd-v/DWPose

Revisión `1a7144101628d69ee7a3768d1ee3a094070dc388`. Poses de cuerpo, manos y rostro.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [dw-ll_ucoco_384.onnx](https://huggingface.co/yzd-v/DWPose/resolve/1a7144101628d69ee7a3768d1ee3a094070dc388/dw-ll_ucoco_384.onnx?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\yzd-v--DWPose\` |
| [yolox_l.onnx](https://huggingface.co/yzd-v/DWPose/resolve/1a7144101628d69ee7a3768d1ee3a094070dc388/yolox_l.onnx?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\yzd-v--DWPose\` |

### smartywu/big-lama

Revisión `05cb2be7f8dbe6ca7c6e78f4fc827a4b2baaa4a9`. Borrado de objetos y relleno de imágenes.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [big-lama.zip](https://huggingface.co/smartywu/big-lama/resolve/05cb2be7f8dbe6ca7c6e78f4fc827a4b2baaa4a9/big-lama.zip?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\smartywu--big-lama\` |

### onnx-community/silero-vad

Revisión `e71cae966052b992a7eca6b17738916ce0eca4ec`. Detección de voz y silencios.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [onnx/model.onnx](https://huggingface.co/onnx-community/silero-vad/resolve/e71cae966052b992a7eca6b17738916ce0eca4ec/onnx/model.onnx?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\onnx-community--silero-vad\onnx\` |
| [LICENSE](https://huggingface.co/onnx-community/silero-vad/resolve/e71cae966052b992a7eca6b17738916ce0eca4ec/LICENSE?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\onnx-community--silero-vad\` |

### sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Revisión `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Búsqueda semántica y comparación de textos multilingües.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [model.safetensors](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/model.safetensors?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [config.json](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [modules.json](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/modules.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [config_sentence_transformers.json](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/config_sentence_transformers.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [sentence_bert_config.json](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/sentence_bert_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [tokenizer.json](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/tokenizer.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [tokenizer_config.json](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/tokenizer_config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [special_tokens_map.json](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/special_tokens_map.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [sentencepiece.bpe.model](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/sentencepiece.bpe.model?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\` |
| [1_Pooling/config.json](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/e8f8c211226b894fcb81acc59f3b34ba3efd5f42/1_Pooling/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\1_Pooling\` |

### PaddlePaddle/latin_PP-OCRv5_mobile_rec

Revisión `ab2cd5cc5fa6309be2e5acdfe66eca2c2c127d57`. Reconocimiento OCR latino, incluido español.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [inference.pdiparams](https://huggingface.co/PaddlePaddle/latin_PP-OCRv5_mobile_rec/resolve/ab2cd5cc5fa6309be2e5acdfe66eca2c2c127d57/inference.pdiparams?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\PaddlePaddle--latin_PP-OCRv5_mobile_rec\` |
| [inference.json](https://huggingface.co/PaddlePaddle/latin_PP-OCRv5_mobile_rec/resolve/ab2cd5cc5fa6309be2e5acdfe66eca2c2c127d57/inference.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\PaddlePaddle--latin_PP-OCRv5_mobile_rec\` |
| [inference.yml](https://huggingface.co/PaddlePaddle/latin_PP-OCRv5_mobile_rec/resolve/ab2cd5cc5fa6309be2e5acdfe66eca2c2c127d57/inference.yml?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\PaddlePaddle--latin_PP-OCRv5_mobile_rec\` |
| [config.json](https://huggingface.co/PaddlePaddle/latin_PP-OCRv5_mobile_rec/resolve/ab2cd5cc5fa6309be2e5acdfe66eca2c2c127d57/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\PaddlePaddle--latin_PP-OCRv5_mobile_rec\` |

### PaddlePaddle/PP-OCRv5_mobile_det

Revisión `0d63e78e2b680928f6b1747d76a08db6e645efb7`. Detección de zonas con texto.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [inference.pdiparams](https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_det/resolve/0d63e78e2b680928f6b1747d76a08db6e645efb7/inference.pdiparams?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\PaddlePaddle--PP-OCRv5_mobile_det\` |
| [inference.json](https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_det/resolve/0d63e78e2b680928f6b1747d76a08db6e645efb7/inference.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\PaddlePaddle--PP-OCRv5_mobile_det\` |
| [inference.yml](https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_det/resolve/0d63e78e2b680928f6b1747d76a08db6e645efb7/inference.yml?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\PaddlePaddle--PP-OCRv5_mobile_det\` |
| [config.json](https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_det/resolve/0d63e78e2b680928f6b1747d76a08db6e645efb7/config.json?download=true) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\PaddlePaddle--PP-OCRv5_mobile_det\` |

## Fuentes externas ya comunicadas

No se han vuelto a descargar estos pesos al preparar la documentación. Estas fuentes
no están incluidas en el manifiesto HF; sus hashes se comprobarán por separado.

| Fichero — descarga | Carpeta de destino |
|---|---|
| [RealESRGAN_x4plus.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth) | `D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\upscale_models\` |
| [RealESRGAN_x2plus.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth) | `D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\upscale_models\` |
| [RealESRNet_x4plus.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth) | `D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\upscale_models\` |
| [RealESRGAN_x4plus_anime_6B.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth) | `D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\upscale_models\` |
| [realesr-animevideov3.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth) | `D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\upscale_models\` |
| [realesr-general-x4v3.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth) | `D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\upscale_models\` |
| [realesr-general-wdn-x4v3.pth](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth) | `D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\upscale_models\` |
| [955717e8-8726e21a.th](https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [f7e0c4bc-ba3fe64a.th](https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/f7e0c4bc-ba3fe64a.th) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [d12395a8-e57c48e6.th](https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/d12395a8-e57c48e6.th) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [92cfc3b6-ef3bcb9c.th](https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/92cfc3b6-ef3bcb9c.th) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [04573f0d-f3cf25b2.th](https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/04573f0d-f3cf25b2.th) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [5c90dfd2-34c22ccb.th](https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/5c90dfd2-34c22ccb.th) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [htdemucs.yaml](https://raw.githubusercontent.com/facebookresearch/demucs/main/demucs/remote/htdemucs.yaml) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [htdemucs_ft.yaml](https://raw.githubusercontent.com/facebookresearch/demucs/main/demucs/remote/htdemucs_ft.yaml) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [htdemucs_6s.yaml](https://raw.githubusercontent.com/facebookresearch/demucs/main/demucs/remote/htdemucs_6s.yaml) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [LICENSE](https://raw.githubusercontent.com/facebookresearch/demucs/main/LICENSE) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--demucs\` |
| [sam2.1_hiera_tiny.pt](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--sam2\checkpoints\` |
| [sam2.1_hiera_t.yaml](https://raw.githubusercontent.com/facebookresearch/sam2/main/sam2/configs/sam2.1/sam2.1_hiera_t.yaml) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--sam2\sam2\configs\sam2.1\` |
| [sam2.1_hiera_small.pt](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--sam2\checkpoints\` |
| [sam2.1_hiera_s.yaml](https://raw.githubusercontent.com/facebookresearch/sam2/main/sam2/configs/sam2.1/sam2.1_hiera_s.yaml) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--sam2\sam2\configs\sam2.1\` |
| [sam2.1_hiera_base_plus.pt](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--sam2\checkpoints\` |
| [sam2.1_hiera_b+.yaml](https://raw.githubusercontent.com/facebookresearch/sam2/main/sam2/configs/sam2.1/sam2.1_hiera_b+.yaml) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--sam2\sam2\configs\sam2.1\` |
| [sam2.1_hiera_large.pt](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--sam2\checkpoints\` |
| [sam2.1_hiera_l.yaml](https://raw.githubusercontent.com/facebookresearch/sam2/main/sam2/configs/sam2.1/sam2.1_hiera_l.yaml) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\facebookresearch--sam2\sam2\configs\sam2.1\` |
| [DeepFilterNet3.zip](https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/models/DeepFilterNet3.zip) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Rikorose--DeepFilterNet\` |
| [DeepFilterNet3_onnx.tar.gz](https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/models/DeepFilterNet3_onnx.tar.gz) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Rikorose--DeepFilterNet\` |
| [DeepFilterNet3_ll_onnx.tar.gz](https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/models/DeepFilterNet3_ll_onnx.tar.gz) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Rikorose--DeepFilterNet\` |
| [LICENSE](https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/LICENSE) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Rikorose--DeepFilterNet\` |
| [LICENSE-MIT](https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/LICENSE-MIT) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Rikorose--DeepFilterNet\` |
| [LICENSE-APACHE](https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/LICENSE-APACHE) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\Rikorose--DeepFilterNet\` |
| [LICENSE — Depth Anything V2](https://raw.githubusercontent.com/DepthAnything/Depth-Anything-V2/main/LICENSE) | `D:\OPENMONTAJE-IA\DESCARGAS_MODELOS\depth-anything--Depth-Anything-V2-Small\` |

Real-ESRGAN general y WDN son una pareja para ajustar reducción de ruido. Demucs FT
usa cuatro pesos como conjunto; el modelo de seis fuentes tiene limitaciones
experimentales, especialmente piano. Los cuatro tamaños SAM son alternativas y no
se cargan juntos. DeepFilterNet conserva formatos ya comunicados para comparación;
no es necesario instalarlos todos. Los enlaces externos a `main` no son inmutables;
su procedencia y contenido deben fijarse antes de automatizar instalaciones.

## Mapa de reutilización por identidad de contenido

Estos archivos ya se habían comunicado, pero no deben descargarse dos veces. La
copia/enlace al destino de cada motor se hará al integrar, no en esta actualización.

| Destino solicitado | Archivo idéntico de referencia |
|---|---|
| `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-8B/vocab.json` | `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/FunAudioLLM--Fun-CosyVoice3-0.5B-2512/CosyVoice-BlankEN/vocab.json` |
| `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-VL-8B-Instruct/vocab.json` | `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/FunAudioLLM--Fun-CosyVoice3-0.5B-2512/CosyVoice-BlankEN/vocab.json` |
| `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/alibaba-pai--Wan2.2-VACE-Fun-A14B/low_noise_model/config.json` | `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/alibaba-pai--Wan2.2-VACE-Fun-A14B/high_noise_model/config.json` |
| `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/alibaba-pai--Wan2.2-VACE-Fun-A14B/google/umt5-xxl/spiece.model` | `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/tokenizer/spiece.model` |
| `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/alibaba-pai--Wan2.2-Fun-A14B-Control-Camera/low_noise_model/config.json` | `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/alibaba-pai--Wan2.2-Fun-A14B-Control-Camera/high_noise_model/config.json` |
| `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-ForcedAligner-0.6B/merges.txt` | `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-8B/merges.txt` |
| `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-ForcedAligner-0.6B/vocab.json` | `D:/OPENMONTAJE-IA/DESCARGAS_MODELOS/FunAudioLLM--Fun-CosyVoice3-0.5B-2512/CosyVoice-BlankEN/vocab.json` |

Resumen técnico: 26 grupos HF, 195 entradas comunicadas, 189 destinos canónicos en el manifiesto adicional y 7 reutilizaciones detectadas. Los cuatro grupos externos se documentan aparte.
