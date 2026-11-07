# Licencias y pagos de OPENMONTAGE-IA

Revisión: 6 de noviembre de 2026. Código revisado: rama
`feat/zero-cost-local-policy`, commit `cf6a6b24bbed43ba837195caf4de5681a0d3b26c`.

## Dictamen

Se puede construir una ruta local sin regalías de software con Wan y motores
libres de composición. No se puede certificar todavía que TODA la aplicación,
sus dependencias transitivas y la instalación Windows sean distribuibles a
cualquier cliente sin condiciones. LTX y Remotion tienen condiciones económicas;
Cosmos tiene condiciones adicionales y su reempaquetado requiere trazabilidad.
No se han contratado servicios, aceptado términos en nombre del propietario ni
activado tarjetas, suscripciones o APIs durante esta revisión.

La licencia del código, la de los pesos, las voces, los materiales de entrada
y los derechos sobre salidas son asuntos diferentes. Instalar un SDK no es
contratar una API, y ejecutar en GPU local no elimina condiciones de licencia.

## Motores y archivos seleccionados

| Componente / archivos de la lista | Evidencia de licencia | Resultado económico y condición |
|---|---|---|
| Wan2.2 T2V 14B: `wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors`, `wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors` | Wan-AI T2V y Comfy-Org declaran Apache-2.0 | Sin regalías de licencia; conservar licencia/avisos y cambios al redistribuir. |
| Wan2.2 I2V 14B: `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`, `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | Wan-AI I2V y Comfy-Org declaran Apache-2.0 | Igual; no mezclar parejas T2V/I2V. |
| Wan2.2 5B: `wan2.2_ti2v_5B_fp16.safetensors`, `wan2.2_vae.safetensors` | Wan-AI TI2V-5B y conversión Comfy-Org: Apache-2.0 | Sin canon por generación local. |
| VAE 14B: `wan_2.1_vae.safetensors` | Familia Wan2.1 y distribución Comfy-Org: Apache-2.0 | Conservar procedencia del archivo exacto. |
| LightX2V: LoRAs T2V v1.1 high/low e I2V v1 high/low | Páginas de archivo Comfy-Org y repositorio LightX2V Wan2.2-Lightning: Apache-2.0 | Sin regalías según publicaciones; fijar revisiones y hashes antes del paquete distribuible. |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | Google UMT5-XXL: Apache-2.0; distribuido por Comfy-Org | Sin dependencia de Google Cloud para usar pesos locales. |
| `t5xxl_fp16.safetensors` para LTX | Google T5 v1.1 XXL y Comfy-Org/Mochi-Preview: Apache-2.0 | Sin API de Google; codificador distinto de oldt5. |
| LTX `ltxv-2b-0.9.8-distilled.safetensors`, `ltxv-13b-0.9.8-dev-fp8.safetensors`, `ltxv-13b-0.9.8-distilled-fp8.safetensors` | LTXV Open Weights License 0.X | Gratuito sujeto a condiciones; uso comercial de entidades con ingresos anuales desde USD 10 millones requiere acuerdo de pago. No aprobar como dependencia esencial de costo cero a cualquier escala. |
| `Cosmos-1_0-Diffusion-7B-Video2World.safetensors` | Modelo original NVIDIA: NVIDIA Open Model License; conversión mcmonkey sin metadatos completos de licencia | Original permite uso comercial sin cargo; conversión pendiente de trazabilidad documental para redistribución. No asumir licencia nueva por estar en Hugging Face. |
| `cosmos_cv8x8x8_1.0.safetensors` | Tokenizador original NVIDIA CV8x8x8: NVIDIA Open Model License; repo de conversión sin metadatos completos | Pendiente documentar correspondencia exacta. Misma cautela al distribuir. |
| `oldt5_xxl_fp8_e4m3fn_scaled.safetensors` | Familia T5 original: Apache-2.0; repo de conversión sin metadatos completos | Procedencia exacta y avisos pendientes de consolidar. No certificar el reempaquetado solo por la familia. |

NVIDIA exige conservar su licencia y avisos al distribuir, e identificación
`Built on NVIDIA Cosmos` en los supuestos previstos por su licencia. También
impone condiciones de uso y prohíbe eludir salvaguardas. No hay aquí un umbral de
facturación como el de LTX; eso no convierte su licencia en Apache/MIT ni elimina
las obligaciones de uso. Descargar o convertir a safetensors no las suprime.

## Aplicación y composición

| Componente | Resultado |
|---|---|
| OpenMontage / fork: AGPLv3 | Se puede usar, modificar y cobrar por distribución/soporte. Conservar licencia y avisos; entregar fuente correspondiente al distribuir en las condiciones de la AGPL. La versión modificada con interacción remota debe ofrecer su fuente a esos usuarios conforme a sección 13. No plantear el fork como derivado privativo cerrado. |
| ComfyUI: GPLv3 | Ejecución local sin suscripción obligatoria. Distribuir la carpeta con PCs requiere cumplir las obligaciones del código y binarios que se entregan; la licencia del núcleo no cubre automáticamente nodos adicionales ni pesos. |
| Remotion 4.0.484 en lockfile | Licencia propia. Uso gratuito para particulares, entidades sin fines de lucro y empresas lucrativas de hasta tres empleados según licencia publicada; fuera de elegibilidad requiere licencia empresarial. También restringe vender/alquilar/licenciar derivados de Remotion. No aprobar como componente incondicional para reventa del producto. La página anuncia términos diferentes para v5: no aplicarlos retroactivamente a v4. |
| HyperFrames, licencia raíz Apache-2.0 | Candidato de composición local sin canon por render. Auditar versión empacada, dependencias, fuentes, plugins y recursos; no confundir con la API comercial de HeyGen ni habilitar AWS/GCP por usar su CLI. |
| FFmpeg | Licencia depende de compilación (LGPL/GPL y librerías). `--enable-nonfree` puede producir binario no redistribuible. Antes de copiar a PCs de clientes, registrar `-version`, `-buildconf` y `-L` del binario real; evaluar aparte licencias/patentes de codecs según distribución y jurisdicción. No afirmar que el binario Windows fue revisado desde este entorno. |

La base propuesta para evitar umbrales económicos es Wan + composición local
con FFmpeg/HyperFrames. Es una dirección de arquitectura: no se afirma que ya
sustituya todas las composiciones Remotion con igual resultado y velocidad.

## Voces, música y material adicional

Piper actual OHF-Voice usa GPL-3.0; el Piper histórico tenía otra licencia.
`pip install piper-tts` sin versión fijada no determina qué edición se empaqueta.
Cada voz tiene su propia ficha. La voz por defecto del adaptador,
`en_US-lessac-medium`, remite a un dataset Lessac/Blizzard con licencia de
investigación. Esto no prueba por sí solo que cada salida del modelo esté
prohibida comercialmente, pero impide aprobar esa voz para nuestro paquete
comercial sin aclaración o permiso específico. Mantenerla fuera de una selección
comercial aprobada y elegir después una voz con derechos documentados.

Meta MusicGen-small declara CC-BY-NC-4.0: no elegirlo para uso comercial cero
costo. No se confunde con `tools/audio/music_gen.py`: ese adaptador del fork
utiliza ElevenLabs, está clasificado API y queda bloqueado por la política.
Las bibliotecas de música, imágenes, fuentes y clips externos necesitan sus
licencias individuales; la del motor no otorga derechos sobre esos materiales.

## Pagos y rutas técnicas comprobadas

- `config.yaml` y `lib/config_model.py` conservan `llm.provider=anthropic` como
  configuración heredada. No se ejecutó ninguna llamada LLM en esta auditoría.
  El agente director local está pendiente; el bloqueo BaseTool no cubre un
  cliente LLM externo ni el costo del asistente usado para dirigir producción.
- APIs/híbridos se bloquean en BaseTool y los selectores filtran proveedores.
  ComfyUI genérico también se bloquea por admitir nodos con créditos.
- `comfyui_wan_local` acepta solo grafos Wan revisados, vía HTTP loopback,
  sin credenciales de nube, proxies del entorno ni redirecciones. LTX y Cosmos
  todavía no están integrados en este adaptador.
- ComfyUI Partner Nodes consumen servicios externos/créditos. Comfy Cloud,
  Hugging Face Inference/Endpoints y render cloud no son descargas de pesos ni
  motores locales y no deben activarse como requisitos.
- Descargar pesos públicos y ejecutar los archivos locales no activa por sí
  solo facturación por inferencia. Un login/aceptación de licencia no equivale
  a necesitar tarjeta. No se contrataron planes Hugging Face de pago.
- El presupuesto USD 0 y el bloqueo de APIs no comprueban elegibilidad de
  licencias ni protegen contra todo script o proceso externo. Una herramienta
  marcada local puede tener restricciones económicas o de redistribución.

## Cobertura de dependencias y límites de la verificación

Se inspeccionaron requirements de Python, configuración, adaptadores y
`remotion-composer/package-lock.json`. El lockfile contiene 244 entradas de
paquetes, con estas declaraciones: MIT 179; MPL-2.0 4; SEE LICENSE IN LICENSE.md 6;
Remotion License 1; UNDECLARED 8; Remotion License con URL 1; UNLICENSED 2;
Apache-2.0 5; BSD-3-Clause 6; CC-BY-4.0 1; ISC 19; BSD-2-Clause 9;
Unlicense 2; 0BSD 1. Declaraciones no son una auditoría del texto de cada paquete;
`UNLICENSED` no significa automáticamente que se haya detectado un cobro.

Python usa rangos abiertos y HyperFrames se obtiene sin versión fija en el
instalador. No existe todavía un inventario reproducible de TODOS los paquetes
y binarios de la PC Windows. No se declara aprobada la redistribución íntegra
de la carpeta portable, los paquetes de ComfyUI o todas las skills heredadas.
Windows y el controlador/CUDA conservan además sus condiciones independientes;
no se compra ni concede una licencia Windows por copiar ComfyUI.

Para cerrar la distribución comercial falta fijar versiones/hashes, completar
avisos y licencias de terceros con las fuentes que correspondan, resolver las
conversiones Cosmos y la voz, y revisar el inventario de la instalación real.
No hace falta pagar una API para realizar estas comprobaciones.

## Fuentes primarias consultadas

- OpenMontage: https://raw.githubusercontent.com/calesthio/OpenMontage/main/LICENSE
- ComfyUI: https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/LICENSE
- Wan T2V: https://huggingface.co/Wan-AI/Wan2.2-T2V-A14B
- Wan I2V: https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B
- Wan 5B: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B
- Wan2.1: https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B
- Conversión Wan: https://huggingface.co/Comfy-Org/Wan-2.2
- LoRAs originales: https://huggingface.co/lightx2v/Wan2.2-Lightning
- UMT5: https://huggingface.co/google/umt5-xxl
- T5 v1.1: https://huggingface.co/google/t5-v1_1-xxl
- T5 original: https://huggingface.co/google-t5/t5-11b
- Codificador convertido: https://huggingface.co/Comfy-Org/Mochi-Preview
- LTX: https://huggingface.co/Lightricks/LTX-Video/raw/main/LTX-Video-Open-Weights-License-0.X.txt
- Cosmos original: https://huggingface.co/nvidia/Cosmos-1.0-Diffusion-7B-Video2World
- Tokenizador Cosmos: https://huggingface.co/nvidia/Cosmos-0.1-Tokenizer-CV8x8x8
- Conversión Cosmos: https://huggingface.co/mcmonkey/cosmos-1.0
- VAE/codificador Cosmos: https://huggingface.co/comfyanonymous/cosmos_1.0_text_encoder_and_VAE_ComfyUI
- Remotion: https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md
- Remotion precios: https://www.remotion.dev/docs/license/pricing
- Remotion términos v4: https://www.remotion.pro/terms-4-0
- HyperFrames: https://raw.githubusercontent.com/heygen-com/hyperframes/main/LICENSE
- FFmpeg: https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/LICENSE.md
- Piper actual: https://github.com/OHF-Voice/piper1-gpl
- Voz Lessac: https://huggingface.co/rhasspy/piper-voices/raw/main/en/en_US/lessac/medium/MODEL_CARD
- Dataset citado por esa voz: https://www.cstr.ed.ac.uk/projects/blizzard/2013/lessac_blizzard2013/license.html
- Meta MusicGen: https://huggingface.co/facebook/musicgen-small
- Nodos con créditos: https://docs.comfy.org/tutorials/partner-nodes/overview
