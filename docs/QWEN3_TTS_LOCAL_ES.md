# Qwen3-TTS local: preparación y límites

Seguimiento #149/#3, 26-11-2026. VoiceDesign **1.7B** diseña por descripción;
Base **1.7B** clona únicamente una referencia autorizada. No sustituirlos por
CustomVoice ni Base0.6B. Código nuevo propio; tarjetas oficiales Apache-2.0,
derechos de la voz de referencia separados.

Fuentes fijadas:

- [VoiceDesign](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/tree/5ecdb67327fd37bb2e042aab12ff7391903235d3).
- [Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base/tree/fd4b254389122332181a7c3db7f27e918eec64e3).
- [Runtime oficial 0.1.1](https://pypi.org/project/qwen-tts/0.1.1/).

Ambos modelos están preparados en `C:/OPENMONTAJE-IA/DESCARGAS_MODELOS`, cada uno
en su subcarpeta. Los principales nuevos coinciden con tamaño/SHA256 oficiales:

| Variante | Bytes | SHA256 |
|---|---:|---|
| VoiceDesign | 3833402552 | `391e8db219f292c515297cdceeb43e4eae67cdde35fa57e79a6a8a532fca0522` |
| Base | 3857413744 | `38fc7fc51c5e776e840414b6fd443962e9411b9654888fd7913e4da643cb857c` |
| Tokenizer común | 682293092 | `836b7b357f5ea43e889936a3709af68dfe3751881acefe4ecf0dbd30ba571258` |

FDM confirmó finalización antes de leer. Cada peso nuevo completo se verificó
una vez; la caché exige volumen/inodo/tamaño/mtime/ctime coincidentes. Los dos
tokenizers canónicos de C: son enlaces duros al mismo contenido verificado.
El tokenizer adicional descargado por FDM fue identificado y su alias redundante
eliminado. No se repitió su descarga ni se tocaron los originales D:.

Había un config VoiceDesign en la carpeta Base y auxiliares dentro de un
directorio llamado model.safetensors. Se identificaron por Git blob oficial,
se conservaron auxiliares mal ubicados en `identified-download-layout`, y los
pesos terminados `(1)` pasaron a sus nombres canónicos sin sobrescribir.
`speech_tokenizer/config.json` y `configuration.json` siguen siendo archivos
distintos. El anterior peso D: etiquetado VoiceDesign coincide exactamente con
CustomVoice oficial; es otra variante, no evidencia de corrupción.

Runtime específico `.runtime/qwen-tts/venv`, Python3.11.9. Instalados únicamente
allí: qwen-tts0.1.1, torch/torchaudio2.6.0+cpu, Transformers4.57.3,
Accelerate1.12.0; `pip check` e importación reales aprobados, sin cargar modelos.
[Versiones instaladas](QWEN149_RUNTIME_VERSIONES.txt). Hub offline; no descarga
automática de pesos. SoX ejecutable no se encontró durante la importación y
flash-attn es opcional ausente; no se afirma síntesis por superar importación.

La ruta CPU actual selecciona FP32: presupuesto conservador de pesos expandidos
más1GiB, aproximadamente10,1GB; RAM libre observada3,4–3,8GB. Diagnóstico y worker
rechazan la carga antes de leer tensores. Es una estimación, no pico medido.
Este Torch no ofrece CUDA. No se ha validado otro runtime CUDA ni ajuste real
en los8GB de la RTX4060 Laptop. No hay muestra española nueva ni naturalidad,
latencia o cancelación de inferencia acreditadas.

## Studio y agente

Tras activar el backend, Audio → «Qwen3-TTS local · perfiles y preparación» →
consultar perfiles. GET `/api/studio/editor/qwen/profiles` es diagnóstico sin
carga. Se permite guardar un **plan editable**, no una preescucha ficticia:
VoiceDesign pide texto/idioma/descripción; Base exige WAV/FLAC registrado,
transcripción y autorización explícita. Diez idiomas oficiales; español incluido.
El plan admite deshacer/rehacer/reapertura, sin iniciar síntesis.

El agente usa `studio_project_edit(action=qwen_profiles)` y comando compartido
`qwen_tts_plan` con revisión. Los adaptadores registrados son `model_voice_design`
y `model_qwen_tts_17b_base`; el perfil0.6B existente permanece separado.
Verificación persistente local: `.runtime/qwen-tts/verified-models.json`.
No copiar una huella a un archivo con identidad diferente ni rehash automático
en consultas de disponibilidad. La identidad de Studio incluye los nuevos
helpers/worker/catálogo para detectar backend antiguo.

Pruebas:14 casos nuevos de perfiles, variantes, memoria, errores JSON,
autorización, plan/persistencia e identidad. Chrome/API reales en instancia QA:
consulta, plan y persistencia;500 explícitamente simulado conserva el error
visible, sin habilitar guardado. No equivale a cancelar una inferencia real.
