# Alternativas locales para OPENMONTAGE-IA

Revisión de fuentes: 6 de noviembre de 2026. Complementa
[Licencias y pagos](LICENCIAS_Y_PAGOS.md). Alcance: panorama amplio de familias
relevantes para producción audiovisual local, no inventario exhaustivo de cada
checkpoint, fork o LoRA publicado. Los proyectos cambian y una licencia de código
no prueba por sí sola la licencia de todos los pesos o dependencias.

## Resultado y correcciones respecto de las primeras recomendaciones

Hay muchas alternativas además de Wan2.2. La selección inicial fue demasiado
estrecha y los LTX v0.9.x indicados anteriormente son una familia heredada:
Lightricks recomienda ahora LTX-2.5 para nuevos proyectos. Los v0.9.x conservan
valor de comparación y perfiles pequeños; no son equivalentes a los actuales.
No cancelar o borrar automáticamente archivos existentes por esta revisión.

El criterio costo cero no excluye una licencia condicionada si el usuario
cumple sus condiciones. Sí impide presentarla como gratuita para toda escala,
todo territorio y cualquier cliente. No conocemos los ingresos de la empresa
ni se presume que supere ningún umbral. Descargar no contrata una API; aceptar
licencias o usar modelos con condiciones sigue siendo una decisión del usuario.

Las prioridades siguientes son decisiones de investigación, no resultados de
benchmarks propios. Solo Wan14B tiene hoy un adaptador específico en el fork;
ninguno de estos modelos tiene inferencia real certificada en la PC del dueño.

## Vídeo: generación, extensión y control

T2V = texto a vídeo; I2V = imagen a vídeo. "ComfyUI" significa que hay ejemplos,
soporte del proyecto o integración citada, no que se haya probado en la versión
portable instalada ni que esté conectado a OPENMONTAGE-IA.

| Familia exacta | Función complementaria | Licencia/pago observado | Integración y decisión |
|---|---|---|---|
| Wan2.2 T2V/I2V 14B | Generación general desde texto o imagen; LoRAs aceleradoras separadas | Apache-2.0 en modelos y LightX2V seleccionados | Flujos ComfyUI y adaptador restringido ya preparados; terminar prueba activa. |
| Wan2.2 TI2V 5B | Un motor para texto/imagen, variante de menos parámetros | Apache-2.0 | ComfyUI nativo; comparar con 14B, no inferir velocidad solo por tamaño. |
| Wan2.1 | Alternativa anterior, incluyendo 1.3B para T2V | Apache-2.0 de los modelos oficiales citados | Reserva de compatibilidad/recursos; no afirmar calidad equivalente a Wan2.2. |
| Mochi 1 Preview | Alternativa T2V centrada en movimiento | Apache-2.0 en ficha de pesos | Ejemplo ComfyUI nativo, reutiliza t5xxl descargado; candidato para PC potente. |
| CogVideoX 2B | Alternativa T2V de menos parámetros | Apache-2.0 | Referencia Diffusers; ComfyUI puede requerir nodos comunitarios. Candidato de comparación en laptop con ajustes. |
| CogVideoX 5B | Otra variante de generación | Licencia CogVideoX: registro comercial y licencia básica gratuita; más de un millón de visitas/mes requiere contactar al autor | No extrapolar Apache de 2B. Opcional condicionado, no prioridad frente a alternativas permisivas. |
| Kandinsky 5.0 T2V Lite SFT 5s | T2V de 2B parámetros; variantes SFT/distil para comparación | MIT en checkpoint exacto consultado | Autor publica instrucciones ComfyUI. Candidato prioritario; revisar aparte encoders y variante descargada. |
| LongCat-Video | T2V, I2V y continuación de vídeo | MIT en los pesos | Código/ejemplos oficiales y soporte anunciado por WanGP; candidato prioritario para extensión. No se confirmó plantilla nativa ComfyUI en esta revisión. |
| LongCat-Video-Avatar | Personaje guiado por audio, uno o varios interlocutores y continuación | MIT en pesos | Ejemplos oficiales single/multi; candidato para módulo de presentadores, preferentemente PC potente. |
| daVinci-MagiHuman | Generación conjunta de persona, vídeo y voz; base/distilled/superresolución | Apache-2.0 en ficha oficial | Código oficial y soporte anunciado por WanGP. Candidato prioritario para vídeo con audio; perfiles reales pendientes. |
| LTX-Video v0.9.8 2B/13B | Vídeo con variantes distilled, referencias y controles | LTXV Open Weights License 0.X; condición comercial desde USD 10 millones/año | Mantener descargados como comparación si se desea. Familia heredada, no prioridad para demostrar funciones actuales de LTX. |
| LTX-2 / LTX-2.3 | Vídeo y audio; en 2.3 seis flujos: T2V, I2V, primer/último fotograma, imagen+audio, IC-LoRA, ID-LoRA | Licencia propia de los pesos, condiciones económicas; no deducir Apache de la del código | 2.3 tiene seis flujos nativos documentados. Candidato fuerte condicionado; validar licencia exacta de cada versión. |
| LTX-2.5 | Familia actual recomendada por Lightricks; vídeo/audio sincronizados | LTX-2.x Community License, enmendada 29-oct-2026: límite USD 10 millones, entidades vinculadas y condiciones de transferencia de derivados | Candidato para PC potente. La app LTX Desktop requiere al menos 16 GB VRAM para modo local Windows/Linux; ese umbral es de ESA APP, no mínimo universal de ComfyUI. Fast local y Pro API no son lo mismo. |
| HunyuanVideo 1 / 1.5 | T2V/I2V; variantes y aceleraciones | Tencent Community: territorio excluye UE, Reino Unido y Corea del Sur; autorización especial bajo condición de más de 100 millones de usuarios activos mensuales en fecha definida | Disponible con flujos/integraciones. México no es territorio excluido en el texto consultado. Candidato condicionado, no descartado por ser Tencent. |
| FramePack I2V / F1 | Generación progresiva de vídeo, memoria de contexto constante | Código Apache-2.0; ficha FramePackI2V_HY no muestra una licencia suficiente para certificar todos los pesos; origen Hunyuan requiere revisión | Autor declara mínimo 6 GB VRAM y Windows/Linux; candidato técnico para laptop, aprobación de pesos pendiente. No es un nuevo permiso sobre Hunyuan. |
| Cosmos 1.0 Video2World | Continuación guiada por imágenes/fotogramas y transiciones | NVIDIA Open Model License sin cargo; atribución y condiciones. Conversiones aún requieren trazabilidad | Ejemplo ComfyUI. Pesos en cola; reservar prueba pesada para equipo adecuado. |
| Cosmos Predict2 | Familia posterior, texto a imagen e imagen a vídeo | Revisar versión original NVIDIA y conversión elegida | Ejemplo ComfyUI; reutiliza oldt5 y Wan2.1 VAE según ejemplo. No reutiliza necesariamente todo el stack Cosmos1. |
| SkyReels V2 DF | Generación autoregresiva/continuación para vídeos largos | Skywork Community License: uso comercial declarado, acuerdo completo adicional | Ejemplos oficiales; candidato condicionado. No aprobado como Apache ni para distribución comercial hasta cerrar acuerdo enlazado. |
| Open-Sora v2 | Generación abierta e infraestructura de investigación | Apache-2.0 en ficha de pesos | Menor prioridad por complejidad y recursos; no confundir con OpenAI Sora. Revisar encoders/dependencias del pipeline exacto. |
| Ovi 1.1 | Generación simultánea de vídeo y sonido | Código y checkpoint Ovi declaran Apache; instalador descarga además archivos de MMAudio, cuyo repo de pesos declara CC-BY-NC | Pendiente analizar qué pesos MMAudio usa exactamente y sus permisos. No dar aprobación comercial del conjunto solo por Apache de Ovi. |
| MiniMax H3 FL2VA / Ref2VA | Vídeo+audio; primer/último fotograma o referencias múltiples de imagen/vídeo/audio | Community License: México dentro de territorio; excluye UE/UK/Corea del Sur/EE.UU.; autorización previa sobre USD 20 millones/año y atribución visible | Pesos locales de H3-Base a 768p. Context-IR y regeneración 2K oficiales no están publicados como el mismo pipeline local: no prometer las prestaciones hosted sin sustituto local medido. Candidato avanzado condicionado. |
| Stable Video Diffusion XT | Animar imagen con un motor anterior | Archivo de licencia actual consultado: Stability Community, uso comercial gratuito bajo USD 1 millón/año; otras condiciones | ComfyUI dispone de ejemplos. Reserva histórica; no clasificarlo genéricamente como imposible de usar comercialmente ni como Apache. |

Fuentes primarias para vídeo:

- https://comfyanonymous.github.io/ComfyUI_examples/
- https://huggingface.co/Wan-AI/Wan2.2-T2V-A14B
- https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B
- https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B
- https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B
- https://huggingface.co/lightx2v/Wan2.2-Lightning
- https://huggingface.co/genmo/mochi-1-preview
- https://comfyanonymous.github.io/ComfyUI_examples/mochi/
- https://huggingface.co/zai-org/CogVideoX-2b
- https://huggingface.co/zai-org/CogVideoX-5b/raw/main/LICENSE
- https://huggingface.co/kandinskylab/Kandinsky-5.0-T2V-Lite-sft-5s
- https://huggingface.co/meituan-longcat/LongCat-Video
- https://huggingface.co/meituan-longcat/LongCat-Video-Avatar
- https://huggingface.co/GAIR/daVinci-MagiHuman
- https://github.com/Lightricks/LTX-Video/blob/main/README.md
- https://huggingface.co/Lightricks/LTX-Video/raw/main/LTX-Video-Open-Weights-License-0.X.txt
- https://huggingface.co/Lightricks/LTX-2.3
- https://docs.comfy.org/tutorials/video/ltx/ltx-2-3
- https://huggingface.co/Lightricks/LTX-2.5
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/LICENSE-2_x
- https://github.com/Lightricks/ltx-desktop/
- https://huggingface.co/tencent/HunyuanVideo-1.5
- https://huggingface.co/tencent/HunyuanVideo-1.5/raw/main/LICENSE
- https://github.com/lllyasviel/FramePack
- https://huggingface.co/lllyasviel/FramePackI2V_HY
- https://huggingface.co/nvidia/Cosmos-1.0-Diffusion-7B-Video2World
- https://comfyanonymous.github.io/ComfyUI_examples/cosmos_predict2/
- https://huggingface.co/Skywork/SkyReels-V2-DF-14B-720P/raw/main/LICENSE
- https://huggingface.co/hpcai-tech/Open-Sora-v2
- https://github.com/character-ai/Ovi
- https://github.com/character-ai/Ovi/blob/main/download_weights.py
- https://huggingface.co/chetwinlow1/Ovi
- https://huggingface.co/hkchengrex/MMAudio
- https://huggingface.co/MiniMaxAI/MiniMax-H3
- https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/LICENSE
- https://design.minimax.io/h3
- https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt/raw/main/LICENSE.md

## Imágenes y edición

Estas capacidades complementan la generación de vídeo: fotogramas de entrada,
productos, fondos, carteles, retoque y consistencia de referencias.

| Modelo | Función | Licencia y decisión |
|---|---|---|
| Qwen-Image | Imagen y texto en imagen | Apache-2.0 en ficha; candidato prioritario, consumo alto por medir. |
| Qwen-Image-Edit | Edición por instrucciones | Apache-2.0 en ficha; complementar con versión exacta de editor y encoder, no mezclar archivos. |
| FLUX.1 schnell | Imagen con pocos pasos | Apache-2.0; candidato de comparación. |
| FLUX.2 klein 4B | Generación y edición de imagen | Apache-2.0; candidato prioritario. No extrapolar a klein 9B, que tiene licencia no comercial según el autor. |
| Z-Image-Turbo | Imagen con variante acelerada | Apache-2.0 en ficha; candidato prioritario para pruebas de velocidad. |
| HiDream-I1-Full | Generación de imagen | MIT del modelo; revisar también sus encoders y licencias independientes antes de aprobar el stack completo. |
| SDXL Base1.0 | Imagen, img2img, inpainting y ecosistema de controles/LoRAs | OpenRAIL++-M: no canon obligatorio en licencia base, pero restricciones de uso. Cada derivado y ControlNet necesita licencia propia. |
| SD3.5 Large | Imagen | Stability Community: condicionado; revisar elegibilidad del modelo y umbral económico. No necesario como primera opción si hay alternativas Apache/MIT. |
| FLUX.1 dev | Imagen | Pesos no comerciales; su permiso de ciertas salidas comerciales no concede permiso general de despliegue comercial del modelo. No base de nuestra app comercial gratuita. |
| Krea2 Raw/Turbo | Imagen | Community License, en Raw uso comercial bajo USD 1 millón/año de ingresos totales agregados y obligaciones adicionales. Opcional condicionado; no Apache de pesos. |

Fuentes:
https://huggingface.co/Qwen/Qwen-Image ;
https://huggingface.co/Qwen/Qwen-Image-Edit ;
https://huggingface.co/black-forest-labs/FLUX.1-schnell ;
https://huggingface.co/black-forest-labs/FLUX.2-klein-4B ;
https://huggingface.co/Tongyi-MAI/Z-Image-Turbo ;
https://huggingface.co/HiDream-ai/HiDream-I1-Full ;
https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 ;
https://huggingface.co/stabilityai/stable-diffusion-3.5-large ;
https://huggingface.co/black-forest-labs/FLUX.1-dev ;
https://huggingface.co/krea/Krea-2-Raw ;
https://cdn.jsdelivr.net/gh/krea-ai/krea-2@db3984fbc6e13b34c0064990fc2d95ac64d00058/assets/hf_samples/LICENSE.pdf

## Voz, música, subtítulos y presentadores

| Modelo/herramienta | Función | Resultado de revisión |
|---|---|---|
| Kokoro82M | TTS compacto | Pesos Apache-2.0; candidato prioritario. Revisar voces y pronunciación española concretas. |
| Qwen3-TTS 12Hz0.6B Base | Clonación de voz desde referencia | Apache-2.0; candidato. CustomVoice y VoiceDesign son otros checkpoints, no asumir esas funciones de Base. |
| Chatterbox | TTS, variantes multilingües/clonación | MIT en ficha; candidato. Fijar checkpoint y evaluar español. |
| Fun-CosyVoice3 0.5B2512 | TTS multilingüe | Apache-2.0 en ficha; candidato de comparación. |
| Piper | TTS offline CPU | Motor actual GPL3; aprobar cada voz por separado, sin deducir derechos por licencia del ejecutable. |
| F5-TTS oficial | Clonación/TTS | Checkpoint SWivid declara CC-BY-NC4.0; no usarlo como solución comercial sin permiso adicional. |
| ACE-Step v1 3.5B | Música | Pesos Apache-2.0; candidato. |
| ACE-Step1.5 | Música | Ficha oficial Ace-Step1.5 declara MIT; candidato más reciente, revisar componentes exactos. |
| MusicGen de Meta | Música | Pesos CC-BY-NC; no seleccionado para uso comercial cero costo. Distinto del adaptador ElevenLabs del mismo nombre funcional. |
| MMAudio | Sonido condicionado por vídeo | Pesos CC-BY-NC; no aprobado comercialmente. Afecta la revisión de pipelines que los descargan indirectamente. |
| Stable Audio Open1.0 | Efectos/sonido | Stability Community; condicionado, no un permiso Apache universal. |
| Whisper / faster-whisper | Transcripción y subtítulos | Whisper código/pesos MIT; faster-whisper ejecución local con CTranslate2. Elegir tamaño/idioma por benchmark y auditar dependencias. |
| MuseTalk | Sincronización labial | Autor permite uso comercial de código MIT y modelo; dependencias y datos de prueba separados. Candidato. |
| LivePortrait | Animación de retrato por movimiento | Código y dependencias faciales separados; no aprobar stack que incluya pesos de InsightFace sin licencia comercial compatible. Existen integraciones MediaPipe, pendientes de validar. |
| Wav2Lip original | Sincronización labial | Autor prohíbe uso comercial de la versión abierta. No seleccionar para nuestra ruta comercial gratuita. |

Fuentes:
https://huggingface.co/hexgrad/Kokoro-82M ;
https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base ;
https://huggingface.co/ResembleAI/chatterbox ;
https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512 ;
https://github.com/OHF-Voice/piper1-gpl ;
https://huggingface.co/SWivid/F5-TTS ;
https://huggingface.co/ACE-Step/ACE-Step-v1-3.5B ;
https://huggingface.co/ACE-Step/Ace-Step1.5 ;
https://huggingface.co/facebook/musicgen-small ;
https://huggingface.co/hkchengrex/MMAudio ;
https://huggingface.co/stabilityai/stable-audio-open-1.0 ;
https://github.com/openai/whisper ;
https://github.com/SYSTRAN/faster-whisper ;
https://github.com/TMElyralab/MuseTalk ;
https://github.com/KlingAIResearch/LivePortrait ;
https://github.com/Rudrabha/Wav2Lip

## Mejora y composición

- Real-ESRGAN: repositorio BSD3; restauración/escalado de imágenes y fotogramas.
  Verificar checkpoint oficial específico; no prometer recuperar detalles reales
  inexistentes o resolución nativa del motor generador.
- RIFE: implementación ECCV2022 MIT para interpolar fotogramas; auditar pesos
  elegidos. Interpolar no sustituye movimiento correcto del vídeo generado.
- FFmpeg: montaje, audio, subtítulos y codificación locales; LGPL/GPL según build,
  no redistribuir un binario marcado nonfree sin resolver su condición.
- HyperFrames: licencia raíz Apache2.0, composición HTML local; dependencias,
  fuentes y assets conservan sus licencias. No activar sus rutas cloud.
- Blender: composición/animación/3D mediante aplicación libre; validar licencia
  de la versión y plugins/activos que se empaqueten. No confundir licencia del
  programa con derechos de modelos 3D descargados.
- Remotion: útil si se cumple su licencia gratuita, pero no dependencia esencial
  universal por sus condiciones empresariales y restricciones de derivados.

Fuentes:
https://github.com/xinntao/Real-ESRGAN ;
https://github.com/hzwer/ECCV2022-RIFE ;
https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/LICENSE.md ;
https://raw.githubusercontent.com/heygen-com/hyperframes/main/LICENSE ;
https://github.com/blender/blender/blob/main/COPYING ;
https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md

## Ejecutores alternativos y director local

ComfyUI sigue siendo el ejecutor ya instalado. WanGP es otro ejecutor, no un
modelo ni un requisito para usar los pesos. Su README anuncia soporte de muchos
modelos y optimización de VRAM, pero su licencia actual distingue uso interno
gratuito de comercialización restringida (incluyendo paquetes OEM/reseller y
producto de pago). Puede servir para comparación interna; no asumir que podemos
integrarlo o revenderlo sin licencia adicional. Que un ejecutor soporte H3 o
LTX no elimina la licencia de esos pesos.

Para sustituir la dirección externa puede evaluarse Qwen2.5-7B-Instruct local,
cuya ficha declara Apache2.0, mediante servidor local. Esto no implementa aún el
agente: hay que probar seguimiento de pipeline, llamadas de herramientas y
revisión de artefactos. Elegir el LLM definitivo requiere otra comparación, no
asumir equivalencia con un asistente comercial por el nombre o los parámetros.

Fuentes:
https://github.com/deepbeepmeep/WanGP ;
https://github.com/deepbeepmeep/WanGP/blob/main/LICENSE.txt ;
https://huggingface.co/Qwen/Qwen2.5-7B-Instruct

## Orden concreto de validación

1. Finalizar Wan14B T2V/I2V activo. Revisar los diez archivos distintos de los
   dos flujos y sus LoRAs correctas. La cola original puede omitir las dos I2V:
   `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` y
   `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors`.
2. Comparar Wan5B y candidatos pequeños como CogVideoX2B/Kandinsky Lite.
   FramePack tiene mínimo declarado de6GB, pero revisión de pesos pendiente.
3. Añadir funciones nuevas con LongCat/Avatar y MagiHuman en PC adecuada.
4. Comparar LTX2.3/2.5 y H3 solo bajo elegibilidad, junto a Mochi como
   alternativa Apache, sin depender de APIs oficiales de pago para terminar.
5. Cerrar imagen, TTS y música con candidatos permisivos, uno por módulo.
6. Integrar solo stacks verificados y medir extremo a extremo contra una
   referencia comercial concreta: calidad, consistencia, resolución efectiva,
   audio, tiempo, RAM/VRAM y reproducibilidad.

La RTX4060 Laptop8GB/16GB RAM es el equipo de prueba actual, no una limitación
al diseño final. No trasladar cifras de H100/4090 al equipo del propietario.
No se ha ejecutado inferencia de estos candidatos en esta revisión documental.
El objetivo de calidad/velocidad permanece; no se declara conseguido.
