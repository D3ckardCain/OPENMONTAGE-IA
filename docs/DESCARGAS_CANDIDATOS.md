# Lista verificada de descargas para candidatos locales

> **Actualización 12/11/2026:** esta es la referencia original de 375 archivos, no el catálogo completo actual. Consultar [ampliación y reutilizaciones](DESCARGAS_ADICIONALES.md), [manifiesto adicional](model_download_manifest_additional.json) y [estado de los dos discos](ESTADO_PROYECTO.md). No repetir descargas ya comunicadas. Los conteos originales no incluyen los candidatos añadidos después.

Verificada: 6 de noviembre de2026. Enlaces fijados a la revisión consultada,
tamaños en GB decimales y SHA256 de archivos grandes registrados en el manifiesto.
Se consultó el inventario remoto; no se descargaron pesos ni se aceptaron licencias.

## Cómo guardar

- Enlaces individuales: clic directo. No usar Guardar página como.
- Mantener nombres, extensiones y carpetas. Una pieza de un modelo dividido no
  funciona sola: descargar también índices, configuraciones y tokenizer.
- Archivos ComfyUI van a la ruta indicada de models. Las carpetas originales
  van a DESCARGAS_MODELOS como almacén; luego se conectarán al motor apropiado.
- No sobrescribir un archivo ya completo ni duplicar un destino compartido.
- GATED significa que debes aceptar personalmente la licencia en Hugging Face;
  un enlace no evita ese requisito. No se requieren APIs de inferencia de pago.
- La lista prepara pesos, no instala software ni garantiza funcionamiento offline
  completo: faltan ejecutores, paquetes y pruebas de cada integración.
- Un modelo permisivo puede depender de pesos con otra licencia. Los grupos
  condicionados se preparan para evaluación; no se aprueba su uso comercial.

## Resumen

| Grupo | Archivos listados | GB del grupo, contando compartidos |
|---|---:|---:|
| [Wan2.2 14B T2V/I2V y 5B](#wan) | 12 | 80.48 |
| [Cosmos 1.0 Video2World](#cosmos) | 3 | 19.58 |
| [LTX-Video 0.9.8 y T5 compartido](#ltx-legacy) | 4 | 47.52 |
| [Mochi 1 Preview](#mochi) | 3 | 30.76 |
| [CogVideoX 2B](#cogvideo) | 16 | 13.78 |
| [Kandinsky 5 Lite SFT 5s](#kandinsky) | 29 | 25.58 |
| [LongCat-Video](#longcat) | 28 | 83.31 |
| [LongCat-Video-Avatar](#longcat-avatar) | 28 | 128.56 |
| [daVinci-MagiHuman](#magihuman) | 93 | 275.26 |
| [LTX-2.3, seis flujos nativos](#ltx23) | 9 | 74.96 |
| [LTX-2.5 T2V/I2V/FLF y preparación DFR](#ltx25) | 11 | 68.46 |
| [HunyuanVideo 1.5, preparación480p](#hunyuan15) | 7 | 30.21 |
| [FramePack I2V](#framepack) | 26 | 42.87 |
| [MiniMax H3 FL2VA y Ref2VA](#h3) | 5 | 63.44 |
| [Qwen-Image y Qwen-Image-Edit](#qwen-image) | 4 | 50.50 |
| [FLUX.2 klein4B distilled](#flux-klein) | 3 | 12.45 |
| [Z-Image-Turbo](#z-image) | 3 | 20.69 |
| [Kokoro82M, voces incluidas](#kokoro) | 57 | 0.36 |
| [Qwen3-TTS0.6B Base](#qwen-tts) | 12 | 2.52 |
| [ACE-Step1.5](#acestep) | 27 | 10.09 |

**Total único: 375 archivos, 1053.17 GB.**
Este total incluye archivos que ya puedes tener; no es el espacio adicional
necesario ni un requisito para comenzar las pruebas. No incluye runtimes.

[Manifiesto con tamaños exactos, hashes y destinos](model_download_manifest.json)

<a id="wan"></a>
## Wan2.2 14B T2V/I2V y 5B

Incluye ambos pares de difusión, cuatro LoRAs correctas, dos VAEs y el encoder compartido. No repetir archivos ya completos.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors?download=true) | 14.294 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors?download=true) | 14.294 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors?download=true) | 14.295 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors?download=true) | 14.295 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors?download=true) | 1.227 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |
| [split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors?download=true) | 1.227 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |
| [split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors?download=true) | 1.227 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |
| [split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors?download=true) | 1.227 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |
| [split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors?download=true) | 10.000 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/vae/wan2.2_vae.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/vae/wan2.2_vae.safetensors?download=true) | 1.409 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [split_files/vae/wan_2.1_vae.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/vae/wan_2.1_vae.safetensors?download=true) | 0.254 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors](https://huggingface.co/Comfy-Org/Wan-2.2/resolve/ee6f4a40737a995bf5818954cfce6d59443b0f04/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors?download=true) | 6.736 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |

<a id="cosmos"></a>
## Cosmos 1.0 Video2World

Mantener la descarga anterior. Conversión pendiente de trazabilidad documental; no confundir con Predict2.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [Cosmos-1_0-Diffusion-7B-Video2World.safetensors](https://huggingface.co/mcmonkey/cosmos-1.0/resolve/5506accba041d4ae2cc65bea7db9cb4bd3dfeb8c/Cosmos-1_0-Diffusion-7B-Video2World.safetensors?download=true) | 14.473 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [text_encoders/oldt5_xxl_fp8_e4m3fn_scaled.safetensors](https://huggingface.co/comfyanonymous/cosmos_1.0_text_encoder_and_VAE_ComfyUI/resolve/bbdb80af1f09226fca13a1c4cfe13db7b5bc9033/text_encoders/oldt5_xxl_fp8_e4m3fn_scaled.safetensors?download=true) | 4.898 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [vae/cosmos_cv8x8x8_1.0.safetensors](https://huggingface.co/comfyanonymous/cosmos_1.0_text_encoder_and_VAE_ComfyUI/resolve/bbdb80af1f09226fca13a1c4cfe13db7b5bc9033/vae/cosmos_cv8x8x8_1.0.safetensors?download=true) | 0.211 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |

<a id="ltx-legacy"></a>
## LTX-Video 0.9.8 y T5 compartido

Comparación de familia heredada. Condiciones económicas LTX. El T5 se reutiliza en Mochi; no lo borres.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [ltxv-2b-0.9.8-distilled.safetensors](https://huggingface.co/Lightricks/LTX-Video/resolve/8984fa25007f376c1a299016d0957a37a2f797bb/ltxv-2b-0.9.8-distilled.safetensors?download=true) | 6.341 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/checkpoints` |
| [ltxv-13b-0.9.8-dev-fp8.safetensors](https://huggingface.co/Lightricks/LTX-Video/resolve/8984fa25007f376c1a299016d0957a37a2f797bb/ltxv-13b-0.9.8-dev-fp8.safetensors?download=true) | 15.694 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/checkpoints` |
| [ltxv-13b-0.9.8-distilled-fp8.safetensors](https://huggingface.co/Lightricks/LTX-Video/resolve/8984fa25007f376c1a299016d0957a37a2f797bb/ltxv-13b-0.9.8-distilled-fp8.safetensors?download=true) | 15.694 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/checkpoints` |
| [split_files/text_encoders/t5xxl_fp16.safetensors](https://huggingface.co/Comfy-Org/Mochi-Preview/resolve/ed4b8585dc4d3204397291c35e100884686178d6/split_files/text_encoders/t5xxl_fp16.safetensors?download=true) | 9.788 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |

<a id="mochi"></a>
## Mochi 1 Preview

Seleccionada variante BF16 para evaluar calidad. Reutiliza el T5 del grupo anterior. Equipo potente; no certificado en laptop8GB.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [split_files/diffusion_models/mochi_preview_bf16.safetensors](https://huggingface.co/Comfy-Org/Mochi-Preview/resolve/ed4b8585dc4d3204397291c35e100884686178d6/split_files/diffusion_models/mochi_preview_bf16.safetensors?download=true) | 20.055 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/vae/mochi_vae.safetensors](https://huggingface.co/Comfy-Org/Mochi-Preview/resolve/ed4b8585dc4d3204397291c35e100884686178d6/split_files/vae/mochi_vae.safetensors?download=true) | 0.920 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [split_files/text_encoders/t5xxl_fp16.safetensors](https://huggingface.co/Comfy-Org/Mochi-Preview/resolve/ed4b8585dc4d3204397291c35e100884686178d6/split_files/text_encoders/t5xxl_fp16.safetensors?download=true) | 9.788 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |

<a id="cogvideo"></a>
## CogVideoX 2B

Conservar carpeta completa de este conjunto, índices y tokenizer. No colocar las piezas juntas en diffusion_models ni renombrarlas.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [LICENSE](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/LICENSE?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b` |
| [README.md](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b` |
| [model_index.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/model_index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b` |
| [scheduler/scheduler_config.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/scheduler/scheduler_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/scheduler` |
| [text_encoder/config.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/text_encoder/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/text_encoder` |
| [text_encoder/model-00001-of-00002.safetensors](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/text_encoder/model-00001-of-00002.safetensors?download=true) | 4.995 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/text_encoder` |
| [text_encoder/model-00002-of-00002.safetensors](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/text_encoder/model-00002-of-00002.safetensors?download=true) | 4.530 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/text_encoder` |
| [text_encoder/model.safetensors.index.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/text_encoder/model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/text_encoder` |
| [tokenizer/added_tokens.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/tokenizer/added_tokens.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/tokenizer` |
| [tokenizer/special_tokens_map.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/tokenizer/special_tokens_map.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/tokenizer` |
| [tokenizer/spiece.model](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/tokenizer/spiece.model?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/tokenizer` |
| [tokenizer/tokenizer_config.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/tokenizer/tokenizer_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/tokenizer` |
| [transformer/config.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/transformer/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/transformer` |
| [transformer/diffusion_pytorch_model.safetensors](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/transformer/diffusion_pytorch_model.safetensors?download=true) | 3.388 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/transformer` |
| [vae/config.json](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/vae/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/vae` |
| [vae/diffusion_pytorch_model.safetensors](https://huggingface.co/zai-org/CogVideoX-2b/resolve/1137dacfc2c9c012bed6a0793f4ecf2ca8e7ba01/vae/diffusion_pytorch_model.safetensors?download=true) | 0.862 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/zai-org--CogVideoX-2b/vae` |

<a id="kandinsky"></a>
## Kandinsky 5 Lite SFT 5s

El modelo MIT necesita además VAE Hunyuan, Qwen-VL y CLIP. Sus licencias se revisan aparte. Rutas originales conservadas para preparar el motor oficial.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [model/config.json](https://huggingface.co/kandinskylab/Kandinsky-5.0-T2V-Lite-sft-5s/resolve/0af037be85ccb8d24b7dbdcd612d3e0cc9e32cc2/model/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/kandinskylab--Kandinsky-5.0-T2V-Lite-sft-5s/model` |
| [model/kandinsky5lite_t2v_sft_5s.safetensors](https://huggingface.co/kandinskylab/Kandinsky-5.0-T2V-Lite-sft-5s/resolve/0af037be85ccb8d24b7dbdcd612d3e0cc9e32cc2/model/kandinsky5lite_t2v_sft_5s.safetensors?download=true) | 4.573 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/kandinskylab--Kandinsky-5.0-T2V-Lite-sft-5s/model` |
| [README.md](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [chat_template.json](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/chat_template.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [config.json](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [generation_config.json](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/generation_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [merges.txt](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/merges.txt?download=true) | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [model-00001-of-00005.safetensors](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/model-00001-of-00005.safetensors?download=true) | 3.900 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [model-00002-of-00005.safetensors](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/model-00002-of-00005.safetensors?download=true) | 3.865 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [model-00003-of-00005.safetensors](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/model-00003-of-00005.safetensors?download=true) | 3.865 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [model-00004-of-00005.safetensors](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/model-00004-of-00005.safetensors?download=true) | 3.865 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [model-00005-of-00005.safetensors](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/model-00005-of-00005.safetensors?download=true) | 1.090 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [model.safetensors.index.json](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [preprocessor_config.json](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/preprocessor_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [tokenizer.json](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/tokenizer.json?download=true) | 0.007 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [tokenizer_config.json](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/tokenizer_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [vocab.json](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/resolve/cc594898137f460bfe9f0759e9844b3ce807cfb5/vocab.json?download=true) | 0.003 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen2.5-VL-7B-Instruct` |
| [README.md](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [config.json](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [merges.txt](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/merges.txt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [model.safetensors](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/model.safetensors?download=true) | 1.711 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [preprocessor_config.json](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/preprocessor_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [pytorch_model.bin](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/pytorch_model.bin?download=true) | 1.711 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [special_tokens_map.json](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/special_tokens_map.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [tokenizer.json](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/tokenizer.json?download=true) | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [tokenizer_config.json](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/tokenizer_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [vocab.json](https://huggingface.co/openai/clip-vit-large-patch14/resolve/32bd64288804d66eefd0ccbe215aa642df71cc41/vocab.json?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/openai--clip-vit-large-patch14` |
| [vae/config.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/vae/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/vae` |
| [vae/diffusion_pytorch_model.safetensors](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/vae/diffusion_pytorch_model.safetensors?download=true) | 0.986 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/vae` |

<a id="longcat"></a>
## LongCat-Video

Base y sus dos LoRAs oficiales, encoder, tokenizer y VAE. Preservar toda la estructura.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [LICENSE](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/LICENSE?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video` |
| [README.md](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video` |
| [config.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video` |
| [dit/config.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/dit/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/dit` |
| [dit/diffusion_pytorch_model-00001-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/dit/diffusion_pytorch_model-00001-of-00006.safetensors?download=true) | 9.933 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/dit` |
| [dit/diffusion_pytorch_model-00002-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/dit/diffusion_pytorch_model-00002-of-00006.safetensors?download=true) | 9.976 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/dit` |
| [dit/diffusion_pytorch_model-00003-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/dit/diffusion_pytorch_model-00003-of-00006.safetensors?download=true) | 9.955 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/dit` |
| [dit/diffusion_pytorch_model-00004-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/dit/diffusion_pytorch_model-00004-of-00006.safetensors?download=true) | 9.821 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/dit` |
| [dit/diffusion_pytorch_model-00005-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/dit/diffusion_pytorch_model-00005-of-00006.safetensors?download=true) | 9.926 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/dit` |
| [dit/diffusion_pytorch_model-00006-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/dit/diffusion_pytorch_model-00006-of-00006.safetensors?download=true) | 4.712 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/dit` |
| [dit/diffusion_pytorch_model.safetensors.index.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/dit/diffusion_pytorch_model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/dit` |
| [lora/cfg_step_lora.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/lora/cfg_step_lora.safetensors?download=true) | 2.523 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/lora` |
| [lora/refinement_lora.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/lora/refinement_lora.safetensors?download=true) | 3.209 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/lora` |
| [model_index.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/model_index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video` |
| [scheduler/scheduler_config.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/scheduler/scheduler_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/scheduler` |
| [text_encoder/config.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/text_encoder/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/text_encoder` |
| [text_encoder/model-00001-of-00005.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/text_encoder/model-00001-of-00005.safetensors?download=true) | 4.972 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/text_encoder` |
| [text_encoder/model-00002-of-00005.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/text_encoder/model-00002-of-00005.safetensors?download=true) | 4.899 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/text_encoder` |
| [text_encoder/model-00003-of-00005.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/text_encoder/model-00003-of-00005.safetensors?download=true) | 4.966 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/text_encoder` |
| [text_encoder/model-00004-of-00005.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/text_encoder/model-00004-of-00005.safetensors?download=true) | 5.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/text_encoder` |
| [text_encoder/model-00005-of-00005.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/text_encoder/model-00005-of-00005.safetensors?download=true) | 2.886 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/text_encoder` |
| [text_encoder/model.safetensors.index.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/text_encoder/model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/text_encoder` |
| [tokenizer/special_tokens_map.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/tokenizer/special_tokens_map.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/tokenizer` |
| [tokenizer/spiece.model](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/tokenizer/spiece.model?download=true) | 0.005 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/tokenizer` |
| [tokenizer/tokenizer.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/tokenizer/tokenizer.json?download=true) | 0.017 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/tokenizer` |
| [tokenizer/tokenizer_config.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/tokenizer/tokenizer_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/tokenizer` |
| [vae/config.json](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/vae/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/vae` |
| [vae/diffusion_pytorch_model.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video/resolve/03b55529b1d1d4045f5fbe14d65c8c6e8116b278/vae/diffusion_pytorch_model.safetensors?download=true) | 0.508 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video/vae` |

<a id="longcat-avatar"></a>
## LongCat-Video-Avatar

Incluye variantes single/multi y auxiliares publicados en este repo. También requiere el grupo LongCat-Video base. No se ha aprobado toda dependencia para reventa.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [LICENSE](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/LICENSE?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar` |
| [README.md](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar` |
| [avatar_multi/config.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_multi/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_multi` |
| [avatar_multi/diffusion_pytorch_model-00001-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_multi/diffusion_pytorch_model-00001-of-00006.safetensors?download=true) | 10.718 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_multi` |
| [avatar_multi/diffusion_pytorch_model-00002-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_multi/diffusion_pytorch_model-00002-of-00006.safetensors?download=true) | 10.707 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_multi` |
| [avatar_multi/diffusion_pytorch_model-00003-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_multi/diffusion_pytorch_model-00003-of-00006.safetensors?download=true) | 10.640 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_multi` |
| [avatar_multi/diffusion_pytorch_model-00004-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_multi/diffusion_pytorch_model-00004-of-00006.safetensors?download=true) | 10.707 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_multi` |
| [avatar_multi/diffusion_pytorch_model-00005-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_multi/diffusion_pytorch_model-00005-of-00006.safetensors?download=true) | 10.665 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_multi` |
| [avatar_multi/diffusion_pytorch_model-00006-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_multi/diffusion_pytorch_model-00006-of-00006.safetensors?download=true) | 10.048 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_multi` |
| [avatar_multi/diffusion_pytorch_model.safetensors.index.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_multi/diffusion_pytorch_model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_multi` |
| [avatar_single/config.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_single/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_single` |
| [avatar_single/diffusion_pytorch_model-00001-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_single/diffusion_pytorch_model-00001-of-00006.safetensors?download=true) | 10.718 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_single` |
| [avatar_single/diffusion_pytorch_model-00002-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_single/diffusion_pytorch_model-00002-of-00006.safetensors?download=true) | 10.707 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_single` |
| [avatar_single/diffusion_pytorch_model-00003-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_single/diffusion_pytorch_model-00003-of-00006.safetensors?download=true) | 10.640 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_single` |
| [avatar_single/diffusion_pytorch_model-00004-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_single/diffusion_pytorch_model-00004-of-00006.safetensors?download=true) | 10.707 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_single` |
| [avatar_single/diffusion_pytorch_model-00005-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_single/diffusion_pytorch_model-00005-of-00006.safetensors?download=true) | 10.665 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_single` |
| [avatar_single/diffusion_pytorch_model-00006-of-00006.safetensors](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_single/diffusion_pytorch_model-00006-of-00006.safetensors?download=true) | 10.048 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_single` |
| [avatar_single/diffusion_pytorch_model.safetensors.index.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/avatar_single/diffusion_pytorch_model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/avatar_single` |
| [chinese-wav2vec2-base/chinese-wav2vec2-base-fairseq-ckpt.pt](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/chinese-wav2vec2-base/chinese-wav2vec2-base-fairseq-ckpt.pt?download=true) | 1.141 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/chinese-wav2vec2-base` |
| [chinese-wav2vec2-base/config.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/chinese-wav2vec2-base/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/chinese-wav2vec2-base` |
| [chinese-wav2vec2-base/preprocessor_config.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/chinese-wav2vec2-base/preprocessor_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/chinese-wav2vec2-base` |
| [chinese-wav2vec2-base/pytorch_model.bin](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/chinese-wav2vec2-base/pytorch_model.bin?download=true) | 0.380 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/chinese-wav2vec2-base` |
| [config.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar` |
| [model_index.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/model_index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar` |
| [vocal_separator/Kim_Vocal_2.onnx](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/vocal_separator/Kim_Vocal_2.onnx?download=true) | 0.067 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/vocal_separator` |
| [vocal_separator/download_checks.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/vocal_separator/download_checks.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/vocal_separator` |
| [vocal_separator/mdx_model_data.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/vocal_separator/mdx_model_data.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/vocal_separator` |
| [vocal_separator/vr_model_data.json](https://huggingface.co/meituan-longcat/LongCat-Video-Avatar/resolve/e25e0323d9956e1b03f033828314e7a9214d8fcb/vocal_separator/vr_model_data.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/meituan-longcat--LongCat-Video-Avatar/vocal_separator` |

<a id="magihuman"></a>
## daVinci-MagiHuman

Incluye base, distilled, superresolución540/1080 y TurboVAE. El config oficial exige además T5Gemma y Stable Audio Open: acceso/licencias condicionados. No es aún un stack comercial aprobado sin condiciones.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [1080p_sr/model-00001-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00001-of-00013.safetensors?download=true) | 4.874 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00002-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00002-of-00013.safetensors?download=true) | 4.870 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00003-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00003-of-00013.safetensors?download=true) | 4.940 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00004-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00004-of-00013.safetensors?download=true) | 4.679 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00005-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00005-of-00013.safetensors?download=true) | 4.482 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00006-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00006-of-00013.safetensors?download=true) | 4.986 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00007-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00007-of-00013.safetensors?download=true) | 4.450 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00008-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00008-of-00013.safetensors?download=true) | 4.688 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00009-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00009-of-00013.safetensors?download=true) | 4.964 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00010-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00010-of-00013.safetensors?download=true) | 4.870 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00011-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00011-of-00013.safetensors?download=true) | 4.264 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00012-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00012-of-00013.safetensors?download=true) | 4.975 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model-00013-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model-00013-of-00013.safetensors?download=true) | 4.155 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [1080p_sr/model.safetensors.index.json](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/1080p_sr/model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/1080p_sr` |
| [540p_sr/model-00001-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00001-of-00013.safetensors?download=true) | 4.921 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00002-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00002-of-00013.safetensors?download=true) | 4.521 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00003-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00003-of-00013.safetensors?download=true) | 4.924 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00004-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00004-of-00013.safetensors?download=true) | 4.897 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00005-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00005-of-00013.safetensors?download=true) | 4.924 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00006-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00006-of-00013.safetensors?download=true) | 3.507 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00007-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00007-of-00013.safetensors?download=true) | 4.543 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00008-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00008-of-00013.safetensors?download=true) | 4.680 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00009-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00009-of-00013.safetensors?download=true) | 4.924 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00010-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00010-of-00013.safetensors?download=true) | 4.897 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00011-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00011-of-00013.safetensors?download=true) | 4.924 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00012-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00012-of-00013.safetensors?download=true) | 4.583 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model-00013-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model-00013-of-00013.safetensors?download=true) | 4.951 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [540p_sr/model.safetensors.index.json](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/540p_sr/model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/540p_sr` |
| [README.md](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman` |
| [base/model-00001-of-00007.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model-00001-of-00007.safetensors?download=true) | 4.798 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/base` |
| [base/model-00002-of-00007.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model-00002-of-00007.safetensors?download=true) | 4.777 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/base` |
| [base/model-00003-of-00007.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model-00003-of-00007.safetensors?download=true) | 4.999 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/base` |
| [base/model-00004-of-00007.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model-00004-of-00007.safetensors?download=true) | 4.738 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/base` |
| [base/model-00005-of-00007.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model-00005-of-00007.safetensors?download=true) | 4.972 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/base` |
| [base/model-00006-of-00007.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model-00006-of-00007.safetensors?download=true) | 4.555 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/base` |
| [base/model-00007-of-00007.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model-00007-of-00007.safetensors?download=true) | 1.804 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/base` |
| [base/model.safetensors.index.json](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/base/model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/base` |
| [config.json](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman` |
| [distill/model-00001-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00001-of-00013.safetensors?download=true) | 4.110 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00002-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00002-of-00013.safetensors?download=true) | 4.532 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00003-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00003-of-00013.safetensors?download=true) | 4.785 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00004-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00004-of-00013.safetensors?download=true) | 4.924 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00005-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00005-of-00013.safetensors?download=true) | 4.897 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00006-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00006-of-00013.safetensors?download=true) | 4.924 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00007-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00007-of-00013.safetensors?download=true) | 4.897 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00008-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00008-of-00013.safetensors?download=true) | 4.924 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00009-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00009-of-00013.safetensors?download=true) | 4.897 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00010-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00010-of-00013.safetensors?download=true) | 4.924 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00011-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00011-of-00013.safetensors?download=true) | 4.311 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00012-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00012-of-00013.safetensors?download=true) | 4.951 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model-00013-of-00013.safetensors](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model-00013-of-00013.safetensors?download=true) | 4.118 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [distill/model.safetensors.index.json](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/distill/model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/distill` |
| [turbo_vae/TurboV3-Wan22-TinyShallow_7_7.json](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/turbo_vae/TurboV3-Wan22-TinyShallow_7_7.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/turbo_vae` |
| [turbo_vae/checkpoint-340000.ckpt](https://huggingface.co/GAIR/daVinci-MagiHuman/resolve/7fe95e50c11bd92bdadf94cd51dbec18427f8e0c/turbo_vae/checkpoint-340000.ckpt?download=true) | 1.870 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/GAIR--daVinci-MagiHuman/turbo_vae` |
| [README.md](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/README.md?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [config.json](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [generation_config.json](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/generation_config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00001-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00001-of-00009.safetensors?download=true) **GATED** | 4.903 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00002-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00002-of-00009.safetensors?download=true) **GATED** | 4.948 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00003-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00003-of-00009.safetensors?download=true) **GATED** | 4.962 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00004-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00004-of-00009.safetensors?download=true) **GATED** | 3.670 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00005-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00005-of-00009.safetensors?download=true) **GATED** | 4.933 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00006-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00006-of-00009.safetensors?download=true) **GATED** | 4.948 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00007-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00007-of-00009.safetensors?download=true) **GATED** | 4.992 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00008-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00008-of-00009.safetensors?download=true) **GATED** | 4.977 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model-00009-of-00009.safetensors](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model-00009-of-00009.safetensors?download=true) **GATED** | 2.334 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [model.safetensors.index.json](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/model.safetensors.index.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [special_tokens_map.json](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/special_tokens_map.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [tokenizer.json](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/tokenizer.json?download=true) **GATED** | 0.034 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [tokenizer.model](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/tokenizer.model?download=true) **GATED** | 0.004 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [tokenizer_config.json](https://huggingface.co/google/t5gemma-9b-9b-ul2/resolve/7071a2ace9c8353e12e723e5382cc7256ee41d9f/tokenizer_config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/google--t5gemma-9b-9b-ul2` |
| [LICENSE.md](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/LICENSE.md?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0` |
| [README.md](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/README.md?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0` |
| [model.ckpt](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/model.ckpt?download=true) **GATED** | 4.854 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0` |
| [model.safetensors](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/model.safetensors?download=true) **GATED** | 4.854 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0` |
| [model_config.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/model_config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0` |
| [model_index.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/model_index.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0` |
| [projection_model/config.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/projection_model/config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/projection_model` |
| [projection_model/diffusion_pytorch_model.safetensors](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/projection_model/diffusion_pytorch_model.safetensors?download=true) **GATED** | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/projection_model` |
| [scheduler/scheduler_config.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/scheduler/scheduler_config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/scheduler` |
| [text_encoder/config.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/text_encoder/config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/text_encoder` |
| [text_encoder/model.safetensors](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/text_encoder/model.safetensors?download=true) **GATED** | 0.439 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/text_encoder` |
| [tokenizer/special_tokens_map.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/tokenizer/special_tokens_map.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/tokenizer` |
| [tokenizer/spiece.model](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/tokenizer/spiece.model?download=true) **GATED** | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/tokenizer` |
| [tokenizer/tokenizer.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/tokenizer/tokenizer.json?download=true) **GATED** | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/tokenizer` |
| [tokenizer/tokenizer_config.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/tokenizer/tokenizer_config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/tokenizer` |
| [transformer/config.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/transformer/config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/transformer` |
| [transformer/diffusion_pytorch_model.safetensors](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/transformer/diffusion_pytorch_model.safetensors?download=true) **GATED** | 4.228 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/transformer` |
| [vae/config.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/vae/config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/vae` |
| [vae/diffusion_pytorch_model.safetensors](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/vae/diffusion_pytorch_model.safetensors?download=true) **GATED** | 0.624 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0/vae` |
| [vae_model.ckpt](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/vae_model.ckpt?download=true) **GATED** | 0.624 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0` |
| [vae_model_config.json](https://huggingface.co/stabilityai/stable-audio-open-1.0/resolve/f21265c1e2710b3bd2386596943f0007f55f802e/vae_model_config.json?download=true) **GATED** | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/stabilityai--stable-audio-open-1.0` |
| [Wan2.2_VAE.pth](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/resolve/921dbaf3f1674a56f47e83fb80a34bac8a8f203e/Wan2.2_VAE.pth?download=true) | 2.819 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Wan-AI--Wan2.2-TI2V-5B` |

<a id="ltx23"></a>
## LTX-2.3, seis flujos nativos

Checkpoint dev/distilled FP8, LoRAs de aceleración/control/identidad, encoder Gemma y geometría. Términos LTX, Gemma y modelos auxiliares independientes; no aceptar licencias automáticamente.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [ltx-2.3-22b-dev-fp8.safetensors](https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/91eda216f820e5ecb3d17dc9fe3b7cdaf56b587d/ltx-2.3-22b-dev-fp8.safetensors?download=true) | 29.145 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/checkpoints` |
| [ltx-2.3-22b-distilled-fp8.safetensors](https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/91eda216f820e5ecb3d17dc9fe3b7cdaf56b587d/ltx-2.3-22b-distilled-fp8.safetensors?download=true) | 29.532 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/checkpoints` |
| [split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors](https://huggingface.co/Comfy-Org/LTX-2/resolve/ccde4ba417d7900669fd56dd292a883cee11ff37/split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors?download=true) | 9.448 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [split_files/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors](https://huggingface.co/Comfy-Org/LTX-2/resolve/ccde4ba417d7900669fd56dd292a883cee11ff37/split_files/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors?download=true) | 0.628 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |
| [split_files/loras/ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16.safetensors](https://huggingface.co/Comfy-Org/LTX-2.3/resolve/f20f3a54378001e5e6d642acc84719cc78addf4b/split_files/loras/ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16.safetensors?download=true) | 2.741 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |
| [split_files/loras/ltx-2.3-id-lora-talkvid-3k.safetensors](https://huggingface.co/Comfy-Org/LTX-2.3/resolve/f20f3a54378001e5e6d642acc84719cc78addf4b/split_files/loras/ltx-2.3-id-lora-talkvid-3k.safetensors?download=true) | 1.158 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |
| [ltx-2.3-spatial-upscaler-x2-1.1.safetensors](https://huggingface.co/Lightricks/LTX-2.3/resolve/c1521179de480464f366a98a9d9b2acc4cc097b9/ltx-2.3-spatial-upscaler-x2-1.1.safetensors?download=true) | 0.996 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/latent_upscale_models` |
| [ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors](https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control/resolve/20a580c8606c06a0988d40375a61309e0fe5893d/ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors?download=true) | 0.654 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |
| [geometry_estimation/moge_2_vitl_normal_fp16.safetensors](https://huggingface.co/Comfy-Org/MoGe/resolve/1484985258ba7ef45c314144fcf0e90924ffbf44/geometry_estimation/moge_2_vitl_normal_fp16.safetensors?download=true) | 0.662 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/geometry_estimation` |

<a id="ltx25"></a>
## LTX-2.5 T2V/I2V/FLF y preparación DFR

Repositorio gated: iniciar sesión y aceptar personalmente la licencia. Incluye dos variantes int8 para comparación; encoder Gemma4, duración, VAEs y mejoras. DFR necesita un flujo específico; no basta cargar los pesos.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [diffusion_models/ltx-2.5-22b-dev-transformer-comfy-int8-convrot.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/diffusion_models/ltx-2.5-22b-dev-transformer-comfy-int8-convrot.safetensors?download=true) **GATED** | 21.504 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors?download=true) **GATED** | 21.504 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors?download=true) **GATED** | 15.373 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [vae/ltx-2.5-video-vae-bf16.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/vae/ltx-2.5-video-vae-bf16.safetensors?download=true) **GATED** | 1.472 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [vae/ltx-2.5-video-vae-conv-bf16.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/vae/ltx-2.5-video-vae-conv-bf16.safetensors?download=true) **GATED** | 1.452 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [vae/ltx-2.5-audio-vae-bf16.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/vae/ltx-2.5-audio-vae-bf16.safetensors?download=true) **GATED** | 0.365 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [model_patches/ltx-2.5-duration-head-bf16.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/model_patches/ltx-2.5-duration-head-bf16.safetensors?download=true) **GATED** | 0.004 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/model_patches` |
| [latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors?download=true) **GATED** | 0.996 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/latent_upscale_models` |
| [latent_upscale_models/ltx-2.5-latent-temporal-upscaler-x2-bf16-1.0.safetensors](https://huggingface.co/Lightricks/LTX-2.5/resolve/49b093a39c19169a8a81721dcc541e07e945232f/latent_upscale_models/ltx-2.5-latent-temporal-upscaler-x2-bf16-1.0.safetensors?download=true) **GATED** | 0.262 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/latent_upscale_models` |
| [text_encoders/gemma4_e2b_it_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/gemma-4/resolve/63d0f7c476756b88910170c1df75e2384ea1af31/text_encoders/gemma4_e2b_it_int8_convrot.safetensors?download=true) | 5.200 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors](https://huggingface.co/Lightricks/LTX-2.5-22b-IC-LoRA-Pixel-Spatial-Upscaler/resolve/59f26f1e0c11af42f1affa924b4ef231e9e98b2a/ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors?download=true) **GATED** | 0.327 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |

<a id="hunyuan15"></a>
## HunyuanVideo 1.5, preparación480p

Modelos distintos T2V e I2V y aceleración. Tencent Community, restricciones territoriales y otras condiciones. No garantiza rendimiento8GB.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [split_files/diffusion_models/hunyuanvideo1.5_480p_t2v_cfg_distilled_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/1405a2b738c29b890cf6d03fc038d8d3e92eeed7/split_files/diffusion_models/hunyuanvideo1.5_480p_t2v_cfg_distilled_fp8_scaled.safetensors?download=true) | 8.330 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/diffusion_models/hunyuanvideo1.5_480p_i2v_step_distilled_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/1405a2b738c29b890cf6d03fc038d8d3e92eeed7/split_files/diffusion_models/hunyuanvideo1.5_480p_i2v_step_distilled_fp8_scaled.safetensors?download=true) | 8.335 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/1405a2b738c29b890cf6d03fc038d8d3e92eeed7/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors?download=true) | 9.385 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [split_files/text_encoders/byt5_small_glyphxl_fp16.safetensors](https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/1405a2b738c29b890cf6d03fc038d8d3e92eeed7/split_files/text_encoders/byt5_small_glyphxl_fp16.safetensors?download=true) | 0.439 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [split_files/vae/hunyuanvideo15_vae_fp16.safetensors](https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/1405a2b738c29b890cf6d03fc038d8d3e92eeed7/split_files/vae/hunyuanvideo15_vae_fp16.safetensors?download=true) | 2.521 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [split_files/clip_vision/sigclip_vision_patch14_384.safetensors](https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/1405a2b738c29b890cf6d03fc038d8d3e92eeed7/split_files/clip_vision/sigclip_vision_patch14_384.safetensors?download=true) | 0.857 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/clip_vision` |
| [split_files/loras/hunyuanvideo1.5_t2v_480p_lightx2v_4step_lora_rank_32_bf16.safetensors](https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/1405a2b738c29b890cf6d03fc038d8d3e92eeed7/split_files/loras/hunyuanvideo1.5_t2v_480p_lightx2v_4step_lora_rank_32_bf16.safetensors?download=true) | 0.341 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/loras` |

<a id="framepack"></a>
## FramePack I2V

Preparar motor original:3piezas del modelo más encoders, tokenizers, VAE y visión. Pesos derivadosHunyuan/LLama y demás licencias pendientes de aprobación comercial. No descargar todo Hunyuan, solo auxiliares listados.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [README.md](https://huggingface.co/lllyasviel/FramePackI2V_HY/resolve/86cef4396041b6002c957852daac4c91aaa47c79/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--FramePackI2V_HY` |
| [config.json](https://huggingface.co/lllyasviel/FramePackI2V_HY/resolve/86cef4396041b6002c957852daac4c91aaa47c79/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--FramePackI2V_HY` |
| [diffusion_pytorch_model-00001-of-00003.safetensors](https://huggingface.co/lllyasviel/FramePackI2V_HY/resolve/86cef4396041b6002c957852daac4c91aaa47c79/diffusion_pytorch_model-00001-of-00003.safetensors?download=true) | 9.972 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--FramePackI2V_HY` |
| [diffusion_pytorch_model-00002-of-00003.safetensors](https://huggingface.co/lllyasviel/FramePackI2V_HY/resolve/86cef4396041b6002c957852daac4c91aaa47c79/diffusion_pytorch_model-00002-of-00003.safetensors?download=true) | 9.987 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--FramePackI2V_HY` |
| [diffusion_pytorch_model-00003-of-00003.safetensors](https://huggingface.co/lllyasviel/FramePackI2V_HY/resolve/86cef4396041b6002c957852daac4c91aaa47c79/diffusion_pytorch_model-00003-of-00003.safetensors?download=true) | 5.790 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--FramePackI2V_HY` |
| [diffusion_pytorch_model.safetensors.index.json](https://huggingface.co/lllyasviel/FramePackI2V_HY/resolve/86cef4396041b6002c957852daac4c91aaa47c79/diffusion_pytorch_model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--FramePackI2V_HY` |
| [text_encoder/config.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/text_encoder/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/text_encoder` |
| [text_encoder/model-00001-of-00004.safetensors](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/text_encoder/model-00001-of-00004.safetensors?download=true) | 4.977 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/text_encoder` |
| [text_encoder/model-00002-of-00004.safetensors](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/text_encoder/model-00002-of-00004.safetensors?download=true) | 5.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/text_encoder` |
| [text_encoder/model-00003-of-00004.safetensors](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/text_encoder/model-00003-of-00004.safetensors?download=true) | 4.916 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/text_encoder` |
| [text_encoder/model-00004-of-00004.safetensors](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/text_encoder/model-00004-of-00004.safetensors?download=true) | 0.117 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/text_encoder` |
| [text_encoder/model.safetensors.index.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/text_encoder/model.safetensors.index.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/text_encoder` |
| [text_encoder_2/config.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/text_encoder_2/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/text_encoder_2` |
| [text_encoder_2/model.safetensors](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/text_encoder_2/model.safetensors?download=true) | 0.246 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/text_encoder_2` |
| [tokenizer/special_tokens_map.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/tokenizer/special_tokens_map.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/tokenizer` |
| [tokenizer/tokenizer.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/tokenizer/tokenizer.json?download=true) | 0.017 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/tokenizer` |
| [tokenizer/tokenizer_config.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/tokenizer/tokenizer_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/tokenizer` |
| [tokenizer_2/merges.txt](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/tokenizer_2/merges.txt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/tokenizer_2` |
| [tokenizer_2/special_tokens_map.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/tokenizer_2/special_tokens_map.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/tokenizer_2` |
| [tokenizer_2/tokenizer_config.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/tokenizer_2/tokenizer_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/tokenizer_2` |
| [tokenizer_2/vocab.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/tokenizer_2/vocab.json?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/tokenizer_2` |
| [vae/config.json](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/vae/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/vae` |
| [vae/diffusion_pytorch_model.safetensors](https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/vae/diffusion_pytorch_model.safetensors?download=true) | 0.986 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hunyuanvideo-community--HunyuanVideo/vae` |
| [feature_extractor/preprocessor_config.json](https://huggingface.co/lllyasviel/flux_redux_bfl/resolve/45b801affc54ff2af4e5daf1b282e0921901db87/feature_extractor/preprocessor_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--flux_redux_bfl/feature_extractor` |
| [image_encoder/config.json](https://huggingface.co/lllyasviel/flux_redux_bfl/resolve/45b801affc54ff2af4e5daf1b282e0921901db87/image_encoder/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--flux_redux_bfl/image_encoder` |
| [image_encoder/model.safetensors](https://huggingface.co/lllyasviel/flux_redux_bfl/resolve/45b801affc54ff2af4e5daf1b282e0921901db87/image_encoder/model.safetensors?download=true) | 0.857 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/lllyasviel--flux_redux_bfl/image_encoder` |

<a id="h3"></a>
## MiniMax H3 FL2VA y Ref2VA

Condicionado por licenciaH3 y territorio; aquí México. INT8convrot compatible con ruta Comfy seleccionada; no se elige difusiónNVFP4 que exige otro perfil de GPU. Context-IR/2K oficial no está incluido localmente.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/54472221d27c695fca9621b0c3ed52f06c4af707/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors?download=true) | 20.970 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/54472221d27c695fca9621b0c3ed52f06c4af707/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors?download=true) | 20.970 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/54472221d27c695fca9621b0c3ed52f06c4af707/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors?download=true) | 15.687 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [vae/minimax_h3_video_vae_fp16.safetensors](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/54472221d27c695fca9621b0c3ed52f06c4af707/vae/minimax_h3_video_vae_fp16.safetensors?download=true) | 5.208 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [vae/minimax_h3_audio_vae_fp32.safetensors](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/54472221d27c695fca9621b0c3ed52f06c4af707/vae/minimax_h3_audio_vae_fp32.safetensors?download=true) | 0.605 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |

<a id="qwen-image"></a>
## Qwen-Image y Qwen-Image-Edit

Primeras versiones investigadas, FP8; encoder/VAE compartidos. No son archivos para versiones2512/2511; deben coincidir con las plantillas.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/1f12b17be14c89b026c51a91d67c32f84bb047bc/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors?download=true) | 20.431 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/1405a2b738c29b890cf6d03fc038d8d3e92eeed7/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors?download=true) | 9.385 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [split_files/vae/qwen_image_vae.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/1f12b17be14c89b026c51a91d67c32f84bb047bc/split_files/vae/qwen_image_vae.safetensors?download=true) | 0.254 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |
| [split_files/diffusion_models/qwen_image_edit_fp8_e4m3fn.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/f68ace85e60b4a02a323e394253731947657b7d2/split_files/diffusion_models/qwen_image_edit_fp8_e4m3fn.safetensors?download=true) | 20.431 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |

<a id="flux-klein"></a>
## FLUX.2 klein4B distilled

4B Apache; no9B niFLUXdev. Encoder qwen3_4b compartido con Z-Image; VAEflux2 distinto de ae.safetensors.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [flux-2-klein-4b-fp8.safetensors](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8/resolve/5b4408e59397a4a37ccb46afe426d8ed86379441/flux-2-klein-4b-fp8.safetensors?download=true) | 4.071 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/text_encoders/qwen_3_4b.safetensors](https://huggingface.co/Comfy-Org/flux2-klein-4B/resolve/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965/split_files/text_encoders/qwen_3_4b.safetensors?download=true) | 8.045 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [split_files/vae/flux2-vae.safetensors](https://huggingface.co/Comfy-Org/flux2-dev/resolve/9630c1b4b6e690497ae0c19bb6b1b35d4ebedcb7/split_files/vae/flux2-vae.safetensors?download=true) | 0.336 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |

<a id="z-image"></a>
## Z-Image-Turbo

ModeloBF16 del flujo nativo. Comparte el qwen3_4b de klein; el VAEae es diferente del VAEflux2.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [split_files/diffusion_models/z_image_turbo_bf16.safetensors](https://huggingface.co/Comfy-Org/z_image_turbo/resolve/6fc90a3b1b653e935a0d175e260736de25b84df5/split_files/diffusion_models/z_image_turbo_bf16.safetensors?download=true) | 12.310 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/diffusion_models` |
| [split_files/text_encoders/qwen_3_4b.safetensors](https://huggingface.co/Comfy-Org/flux2-klein-4B/resolve/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965/split_files/text_encoders/qwen_3_4b.safetensors?download=true) | 8.045 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/text_encoders` |
| [split_files/vae/ae.safetensors](https://huggingface.co/Comfy-Org/z_image_turbo/resolve/6fc90a3b1b653e935a0d175e260736de25b84df5/split_files/vae/ae.safetensors?download=true) | 0.335 | `C:/OPENMONTAJE-IA/ComfyUI_windows_portable/ComfyUI/models/vae` |

<a id="kokoro"></a>
## Kokoro82M, voces incluidas

Carpeta completa; incluye voces españolas ef_dora, em_alex y em_santa. Licencias de voces deben acompañar la instalación.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [README.md](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M` |
| [config.json](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M` |
| [kokoro-v1_0.pth](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/kokoro-v1_0.pth?download=true) | 0.327 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M` |
| [voices/af_alloy.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_alloy.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_aoede.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_aoede.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_bella.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_bella.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_heart.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_heart.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_jessica.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_jessica.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_kore.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_kore.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_nicole.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_nicole.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_nova.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_nova.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_river.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_river.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_sarah.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_sarah.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/af_sky.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/af_sky.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_adam.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_adam.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_echo.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_echo.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_eric.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_eric.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_fenrir.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_fenrir.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_liam.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_liam.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_michael.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_michael.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_onyx.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_onyx.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_puck.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_puck.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/am_santa.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/am_santa.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/bf_alice.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/bf_alice.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/bf_emma.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/bf_emma.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/bf_isabella.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/bf_isabella.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/bf_lily.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/bf_lily.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/bm_daniel.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/bm_daniel.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/bm_fable.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/bm_fable.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/bm_george.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/bm_george.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/bm_lewis.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/bm_lewis.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/ef_dora.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/ef_dora.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/em_alex.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/em_alex.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/em_santa.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/em_santa.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/ff_siwis.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/ff_siwis.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/hf_alpha.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/hf_alpha.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/hf_beta.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/hf_beta.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/hm_omega.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/hm_omega.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/hm_psi.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/hm_psi.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/if_sara.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/if_sara.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/im_nicola.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/im_nicola.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/jf_alpha.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/jf_alpha.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/jf_gongitsune.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/jf_gongitsune.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/jf_nezumi.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/jf_nezumi.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/jf_tebukuro.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/jf_tebukuro.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/jm_kumo.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/jm_kumo.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/pf_dora.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/pf_dora.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/pm_alex.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/pm_alex.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/pm_santa.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/pm_santa.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/zf_xiaobei.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/zf_xiaobei.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/zf_xiaoni.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/zf_xiaoni.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/zf_xiaoxiao.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/zf_xiaoxiao.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/zf_xiaoyi.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/zf_xiaoyi.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/zm_yunjian.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/zm_yunjian.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/zm_yunxi.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/zm_yunxi.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/zm_yunxia.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/zm_yunxia.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |
| [voices/zm_yunyang.pt](https://huggingface.co/hexgrad/Kokoro-82M/resolve/f3ff3571791e39611d31c381e3a41a3af07b4987/voices/zm_yunyang.pt?download=true) | 0.001 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/hexgrad--Kokoro-82M/voices` |

<a id="qwen-tts"></a>
## Qwen3-TTS0.6B Base

Conservar model.safetensors y speech_tokenizer/model.safetensors en sus carpetas distintas. No proporciona por sí solo la función VoiceDesign de otro checkpoint.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [README.md](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base` |
| [config.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base` |
| [generation_config.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/generation_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base` |
| [merges.txt](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/merges.txt?download=true) | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base` |
| [model.safetensors](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/model.safetensors?download=true) | 1.829 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base` |
| [preprocessor_config.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/preprocessor_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base` |
| [speech_tokenizer/config.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/speech_tokenizer/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base/speech_tokenizer` |
| [speech_tokenizer/configuration.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/speech_tokenizer/configuration.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base/speech_tokenizer` |
| [speech_tokenizer/model.safetensors](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/speech_tokenizer/model.safetensors?download=true) | 0.682 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base/speech_tokenizer` |
| [speech_tokenizer/preprocessor_config.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/speech_tokenizer/preprocessor_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base/speech_tokenizer` |
| [tokenizer_config.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/tokenizer_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base` |
| [vocab.json](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/resolve/5d83992436eae1d760afd27aff78a71d676296fc/vocab.json?download=true) | 0.003 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/Qwen--Qwen3-TTS-12Hz-0.6B-Base` |

<a id="acestep"></a>
## ACE-Step1.5

Conservar turbo, LM, encoder y VAE en sus respectivas carpetas; no mezclar con ACE-Step v1.

| Archivo — enlace directo | GB | Carpeta de destino |
|---|---:|---|
| [Qwen3-Embedding-0.6B/added_tokens.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/added_tokens.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [Qwen3-Embedding-0.6B/chat_template.jinja](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/chat_template.jinja?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [Qwen3-Embedding-0.6B/config.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [Qwen3-Embedding-0.6B/merges.txt](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/merges.txt?download=true) | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [Qwen3-Embedding-0.6B/model.safetensors](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/model.safetensors?download=true) | 1.192 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [Qwen3-Embedding-0.6B/special_tokens_map.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/special_tokens_map.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [Qwen3-Embedding-0.6B/tokenizer.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/tokenizer.json?download=true) | 0.011 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [Qwen3-Embedding-0.6B/tokenizer_config.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/tokenizer_config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [Qwen3-Embedding-0.6B/vocab.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/Qwen3-Embedding-0.6B/vocab.json?download=true) | 0.003 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/Qwen3-Embedding-0.6B` |
| [README.md](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/README.md?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5` |
| [acestep-5Hz-lm-1.7B/added_tokens.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/added_tokens.json?download=true) | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-5Hz-lm-1.7B/chat_template.jinja](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/chat_template.jinja?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-5Hz-lm-1.7B/config.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-5Hz-lm-1.7B/merges.txt](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/merges.txt?download=true) | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-5Hz-lm-1.7B/model.safetensors](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/model.safetensors?download=true) | 3.709 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-5Hz-lm-1.7B/special_tokens_map.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/special_tokens_map.json?download=true) | 0.002 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-5Hz-lm-1.7B/tokenizer.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/tokenizer.json?download=true) | 0.024 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-5Hz-lm-1.7B/tokenizer_config.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/tokenizer_config.json?download=true) | 0.014 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-5Hz-lm-1.7B/vocab.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-5Hz-lm-1.7B/vocab.json?download=true) | 0.003 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-5Hz-lm-1.7B` |
| [acestep-v15-turbo/config.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-v15-turbo/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-v15-turbo` |
| [acestep-v15-turbo/configuration_acestep_v15.py](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-v15-turbo/configuration_acestep_v15.py?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-v15-turbo` |
| [acestep-v15-turbo/model.safetensors](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-v15-turbo/model.safetensors?download=true) | 4.788 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-v15-turbo` |
| [acestep-v15-turbo/modeling_acestep_v15_turbo.py](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-v15-turbo/modeling_acestep_v15_turbo.py?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-v15-turbo` |
| [acestep-v15-turbo/silence_latent.pt](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/acestep-v15-turbo/silence_latent.pt?download=true) | 0.004 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/acestep-v15-turbo` |
| [config.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5` |
| [vae/config.json](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/vae/config.json?download=true) | 0.000 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/vae` |
| [vae/diffusion_pytorch_model.safetensors](https://huggingface.co/ACE-Step/Ace-Step1.5/resolve/19671f406d603126926c1b7e2adc169acbcade22/vae/diffusion_pytorch_model.safetensors?download=true) | 0.337 | `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS/ACE-Step--Ace-Step1.5/vae` |

## Lo que no se añade a esta cola

Ovi, SkyReels, Open-Sora, SVD, variantes de imagen/voz y otros modelos del estudio
no forman parte de los candidatos concretos priorizados en esta lista. Ovi
además descarga componentes MMAudio cuya licencia requiere aclaración. No se
descargan automáticamente familias rechazadas para uso comercial, como F5-TTS
oficial, MetaMusicGen o Wav2Lip original.

La lista no es una certificación de derechos para distribuir PCs: véanse
[la auditoría de licencias](LICENCIAS_Y_PAGOS.md) y [el estudio](ALTERNATIVAS_LOCALES.md).
La revisión de dependencias añade condiciones relevantes: Kandinsky usa VAEHunyuan;
MagiHuman requiere Stable Audio Open y T5Gemma; LTX usa Gemma. Sus licencias
no quedan sustituidas por MIT/Apache del modelo principal.

Fuentes de compatibilidad: documentación ComfyUI LTX2.3/LTX2.5/FLUX2Klein,
download_models.py oficial Kandinsky, demo_gradio.py oficial FramePack,
example/base/config.json oficial MagiHuman y fichas/repositorios de cada fila.
Todos los archivos se verificaron contra siblings de la API pública Hugging Face.

Validación adicional: se leyeron los índices públicos y se comprobaron todas sus
piezas referenciadas. El índice de T5Gemma exige acceso autorizado y no se pudo
leer sin aceptar la licencia: su inventario público sí fue listado, pero esa
comprobación concreta queda pendiente. No se intentó eludir el acceso.
