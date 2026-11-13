# Selección orientada a campañas de vídeo de calidad

Revisión: 12 de noviembre de 2026. Investigación documental y metadatos remotos,
sin descarga de pesos en el entorno de investigación ni inferencia. Esta selección
propone candidatos; no acredita un ganador absoluto, calidad perfecta ni velocidad
igual a las demos comerciales.

## Encargo de referencia

Campaña de 48 vídeos sobre pasajes bíblicos, movimiento real, música, narración en
español e inglés, versiones para distintas redes y distribución semanal. Español
primero. No se limita la selección al hardware de la laptop: el equipo de producción
se definirá tras medir los motores. Se mantiene costo operativo objetivo USD 0,
sin tarjetas, pruebas temporales ni APIs comerciales.

## Selección por función

| Función | Candidatos a comparar | Decisión |
|---|---|---|
| Dirección, guion y revisión multimodal | Qwen3.6-35B-A3B y Qwen3.6-27B | Nuevos candidatos Apache-2.0; seleccionar una variante tras comparación, no descargar ambas por defecto |
| Referencias y fidelidad bíblica | Corpus local con texto, edición, libro, capítulo y versículo | Requisito de datos, no sustituible por la memoria de un LLM; permisos de cada edición pendientes |
| Imágenes y miniaturas | Qwen-Image-2512 frente a Qwen-Image anterior; FLUX.1-schnell y FLUX.2 klein 4B como alternativas | 2512 es candidato nuevo Apache-2.0; no confundir con 2.1 ni con Image Edit |
| Edición y continuidad visual | Qwen-Image-Edit-2511 y referencias de personajes/vestuario | Ya comunicado; probar coherencia antes de ampliar |
| Movimiento real y control de escena | Wan2.2 I2V/T2V, VACE/Control/Camera | Ya comunicado; candidato principal Apache-2.0, sin certificación física |
| Continuación de escenas | LongCat-Video | Ya comunicado, MIT; comparar continuidad y tiempo real |
| Narración | Qwen3-TTS-1.7B-CustomVoice y VoiceDesign; CosyVoice3/Chatterbox como alternativas | CustomVoice nuevo, Apache-2.0; español e inglés declarados |
| Música | ACE-Step1.5 | Ya comunicado, MIT; priorizar composición instrumental original bajo narración |
| Efectos y ambientes | MOSS-SoundEffect-v2.0 | Nuevo candidato Apache-2.0; cubrir viento, agua, pasos y ambientes, no reemplazar narración |
| Traducción y subtítulos | MADLAD/M2M100, Whisper/Parakeet y Qwen ForcedAligner | Ya comunicados; comparar transcripción con guion y comprobar sincronización |
| Revisión audiovisual | Qwen VL/Qwen3.6, DNSMOS, Silero y comprobaciones deterministas | DNSMOS solo puntúa sonido: no comprueba verdad, pronunciación ni derechos |
| Montaje y exportación | Herramientas locales de la app, FFmpeg y composición con licencias elegibles | No requieren otro modelo por cada red; auditar ejecutores antes de uso |

No repetir las descargas de los candidatos ya comunicados ni instalar todas las
alternativas. Los cuatro candidatos nuevos deben recibir listas curadas y destinos
antes de una orden de descarga. Los agentes y adaptadores aún no están implementados
de extremo a extremo. Ver [automatización](AUTOMATIZACION_AGENTES.md).

## Nuevos candidatos: procedencia y tamaño del repositorio

Los tamaños siguientes son el total del inventario remoto consultado; incluyen
auxiliares y no equivalen al espacio adicional que habrá que descargar, memoria RAM
ni VRAM necesaria. Todavía no son listas definitivas de archivos.

| Repositorio | Revisión consultada | Total remoto aproximado |
|---|---|---:|
| OpenMOSS-Team/MOSS-SoundEffect-v2.0 | e35df4d82fbe87fcd5d14e5d100e349c0c3c076d | 11,23 GB |
| Qwen/Qwen3.6-35B-A3B | 345d467b117d1fd5eda9b879a5988de9ae5f47a7 | 71,93 GB |
| Qwen/Qwen3.6-27B | 8f33b98937c6031bb49e713dee3e8e185aafd26f | 55,59 GB |
| Qwen/Qwen-Image-2512 | 25468b98e3276ca6700de15c6628e51b7de54a26 | 57,70 GB |
| Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice | 0c0e3051f131929182e2c023b9537f8b1c68adfe | 4,52 GB |

Qwen3.6 es candidato por su soporte multimodal y herramientas, no porque su ficha
demuestre mejor guion bíblico en español. No limitarse a Qwen3-32B por ser el primer
modelo mayor encontrado; comparar las variantes actuales con el Qwen3-8B ya reunido.
35B totales con 3B activos no significa que baste memoria para 3B.

MOSS genera efectos a 48 kHz de hasta 30 segundos según el autor y recibe instrucciones
en inglés/chino. El usuario podrá escribir en español y el director local preparará
el prompt en inglés. Su entorno recomendado Python 3.12 no coincide con el portable
ComfyUI Python 3.13: no modificar este último ni prometer compatibilidad directa.
Qwen CustomVoice tiene voces predefinidas y control de estilo; VoiceDesign crea voces
por descripción y Base permite clonación autorizada. No son funciones intercambiables.

## Reutilizaciones identificadas

Comparación contra SHA256 de los manifiestos anteriores:

- MOSS: tokenizer/tokenizer.json coincide con el tokenizer del Qwen3-8B ya comunicado.
  Otros auxiliares pequeños requieren comparación individual antes de listar descargas.
- CustomVoice: speech_tokenizer/model.safetensors coincide con el tokenizer de
  Qwen3-TTS-0.6B-Base. Verificar los archivos de configuración compartidos también.
- Qwen-Image-2512: no se halló coincidencia de pesos en los SHA del manifiesto actual.
  Esto no demuestra que no existan otros empaquetados compatibles de encoder/VAE.
- Ningún SHA remoto confirma por sí mismo la integridad de los archivos del usuario.

## Exclusiones y condiciones

- Qwen-Image-2.1: licencia Qwen Research, uso no comercial; requiere licencia separada
  para uso comercial. Excluir del flujo comercial de costo cero. 2512 sí declara
  Apache-2.0: no extender su permiso a versiones posteriores.
- TangoFlux: ficha y licencia indican investigación no comercial; excluir.
- SANA-Sprint: Apache declarada más condiciones Gemma y texto de investigación;
  dejar pendiente hasta resolver alcance, sin aprobación comercial general.
- LTX-2.x y modelos con licencias comunitarias/restricciones se mantienen separados
  de la base permisiva. Evaluar condiciones por versión y empresa antes de uso.
- El modelo generativo no asegura originalidad, ausencia de reclamaciones ni derechos
  sobre voces, traducciones, personas o material usado como referencia.

## Prueba de aceptación posterior

No iniciar estas pruebas mientras siga vigente la fase de descargas/documentación.

1. Fijar corpus y verificar cada cita literal contra una edición autorizada. Distinguir
   cita, explicación y dramatización, sin inventar versículos o atribuciones.
2. Preparar un único brief con tres escenas: narración reflexiva, personaje con
   movimiento/manos y escena ambiental compleja. Usar el mismo brief por candidato.
3. Comparar anatomía, coherencia de personaje/vestuario, movimiento, parpadeo temporal,
   fidelidad al encuadre y errores visuales; registrar rechazos y regeneraciones.
4. Comparar voces españolas e inglesas con nombres bíblicos, números, pausas y emoción.
   Medir transcripción frente al guion, cortes de palabras y mezcla con música.
5. Medir por versión y hardware: tiempo inicial y caliente, memoria máxima, porcentaje
   de escenas aceptadas y minutos de cómputo por minuto final útil. Incluir reintentos.
6. Exportar horizontal y vertical con encuadre y zonas de texto propios; reutilizar
   imágenes/escenas entre idiomas cuando sea adecuado, ajustando montaje a la voz.
   No quemar citas bíblicas dentro de imágenes generadas: componer texto verificado.
7. Probar reanudación de campaña y evitar publicaciones duplicadas antes de autorizar
   redes reales. Disponibilidad de publicación gratuita oficial sigue por comprobar.

Elegir el mejor conjunto por los resultados del encargo real; una puntuación del
autor o una demo aislada no decide la selección. No eliminar los modelos existentes
hasta terminar una comparación y contar con una decisión explícita.

## Fuentes primarias

- [MOSS-SoundEffect v2](https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0).
- [MOSS: descripción del equipo](https://www.moss.cn/en/models/moss-sound-effect).
- [Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B).
- [Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B).
- [Qwen-Image-2512](https://huggingface.co/Qwen/Qwen-Image-2512).
- [Licencia Qwen-Image-2.1](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE).
- [Qwen CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice).
- [Wan2.2 I2V](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B).
- [LongCat-Video](https://huggingface.co/meituan-longcat/LongCat-Video).
- [ACE-Step1.5](https://huggingface.co/ACE-Step/Ace-Step1.5).
- [TangoFlux](https://huggingface.co/declare-lab/TangoFlux).
