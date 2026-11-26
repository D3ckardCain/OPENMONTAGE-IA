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

Runtime específico `.runtime/qwen-tts/venv`, Python3.11.9. Preparación inicial
CPU bloqueada por RAM; después se sustituyó solo Torch de este mismo entorno
por la distribución CUDA oficial. Versiones finales: qwen-tts0.1.1,
torch/torchaudio2.6.0+cu124, Transformers4.57.3, Accelerate1.12.0.
`pip check` e importación CUDA/BF16 reales aprobados.
[Versiones instaladas](QWEN149_RUNTIME_VERSIONES.txt). Hub offline; no descarga
automática de pesos. SoX ejecutable no se encontró durante la importación y
flash-attn es opcional ausente; no se afirma síntesis por superar importación.

La ruta CPU actual selecciona FP32: presupuesto conservador de pesos expandidos
más1GiB, aproximadamente10,1GB; RAM libre observada3,4–3,8GB. Diagnóstico y worker
rechazan la carga antes de leer tensores. Es una estimación, no pico medido.
El diagnóstico CPU sigue bloqueando esa ruta. La continuación CUDA utilizó
[PyTorch2.6/CUDA12.4 oficial](https://pytorch.org/get-started/previous-versions/)
en el mismo entorno, sin instalar drivers/toolchain ni tocar `.venv` o ComfyUI.
RTX4060 Laptop, driver610.78; importación BF16 sin pesos y presupuesto VRAM
antes de cada carga. La estimación no garantiza ajuste para cualquier texto.

## Muestras y cancelación reales

Pruebas técnicas propias en Studio aislado4764, proyecto
`edit-1f9afbe37f35`. Cada función ejecutó una sola muestra española terminada,
128tokens máximos/semilla42/CUDA BF16 eager, sin flash-attn ni descargas de pesos.

| Función | Solicitud | WAV | Pasadas | Pico GPU asignado/reservado, bytes |
|---|---|---|---:|---:|
| VoiceDesign | `681c005bf9184ba49594d6d398466dfd` | 1,92s/24kHz | 25 | 4243039232 / 4336910336 |
| Base1.7B | `8677f86b65724f399f2b2569c9d0cf8d` | 2,80s/24kHz | 36 | 4387419136 / 4435476480 |

Base utilizó exclusivamente la muestra VoiceDesign propia como referencia
sintética autorizada, con su texto, SHA256 y recibo. No se clonó una persona.
Las dos cargas reales aceptaron el tokenizer compartido por enlace duro.
WAV PCM16 mono, señal finita/no vacía y procedencia comprobadas. Chrome real:
recuperar recibo → cargar parámetros explícitamente → reproducir silenciado →
registrar sin duplicar → guardar plan → recargar/reabrir dos fuentes y plan.
Cambiar función invalida el reproductor anterior; recuperar no pisa formularios.
La reproducción silenciada no acredita escucha, pronunciación ni naturalidad.

Cancelación adicional `7b0ea5b4ee174870b054ede0a8c34843`: botón real pulsado
tras3pasadas de inferencia observadas, PID141272. Se confirmó cierre del worker,
liberación de GPU, estado cancelado persistido, ausencia de resultado publicado
y recuperación tras recargar sin repetir llamada; las dos fuentes previas intactas.
Se distingue solicitud de cancelación, salida del proceso y cierre de inferencia
observada. No se promete cancelación cooperativa por token ni continuación de
una síntesis parcial: otra toma exige una solicitud explícita nueva.

Durante la validación se detectó que el lanzador venv de Windows crea otro
Python hijo. El control Qwen ahora inicia el Python base identificado en
`pyvenv.cfg`, con `__PYVENV_LAUNCHER__` conservando el entorno aislado. No modifica
su configuración. La confirmación exige que el PID de las pasadas coincida
con el proceso poseído y terminado; cerrar solo el lanzador no cuenta.
Solo este worker propio se termina, nunca procesos encontrados por nombre.

## Studio y agente

Tras activar el backend, Audio → «Qwen3-TTS local · perfiles y preparación» →
consultar perfiles. GET `/api/studio/editor/qwen/profiles` es diagnóstico sin
carga. Guardar un **plan editable** no ejecuta síntesis. La preescucha real
requiere el botón separado, backend `qwen-preview-v1` y diagnóstico disponible:
VoiceDesign pide texto/idioma/descripción; Base exige WAV/FLAC registrado,
transcripción y autorización explícita. Diez idiomas oficiales; español incluido.
El plan admite deshacer/rehacer/reapertura, sin iniciar síntesis.

El agente usa `studio_project_edit(action=qwen_profiles)` y comando compartido
`qwen_tts_plan` con revisión. `qwen_start` recibe `qwen` con request_id hexadecimal
de32caracteres, revisión, perfil, idioma, texto, device, max_new_tokens8–256,
seed y descripción o referencia autorizada. `qwen_status`/`qwen_cancel` reciben
request_id. Usuario y agente llaman al mismo propietario Studio y recibos.
No reintentar POST tras respuesta incierta: consultar primero por ID. Mismo ID
con otros parámetros se rechaza; índice e historial no sintetizan.
Texto de preescucha hasta300caracteres, WAV hasta30s/10MB, timeout300s; Base
exige referencia registrada WAV/FLAC hasta30s/10MB sin cambios de SHA256.
Los adaptadores registrados son `model_voice_design`
y `model_qwen_tts_17b_base`; el perfil0.6B existente permanece separado.
Verificación persistente local: `.runtime/qwen-tts/verified-models.json`.
No copiar una huella a un archivo con identidad diferente ni rehash automático
en consultas de disponibilidad. La identidad de Studio incluye los nuevos
helpers/worker/catálogo para detectar backend antiguo.

Pruebas:14 casos nuevos de perfiles, variantes, memoria, errores JSON,
autorización, plan/persistencia e identidad. Chrome/API reales en instancia QA:
consulta, plan y persistencia;500 explícitamente simulado conserva el error
visible, sin habilitar guardado. Esa prueba simulada se mantiene separada de la
cancelación real posterior. Se añaden18casos nuevos offline:9solicitudes/recibos,
5preparación CUDA/comando Windows y4contratos de agente/worker. Fixtures no son
evidencia de síntesis. Las muestras y cancelación anteriores sí usan modelos reales.

Metadatos de recursos se revalidan sin releer pesos; recibos de runtime ligados
a identidad de Python y METADATA de Torch. No hay fallback CPU/modelo ni red
oculta. Si cambia el servidor con un worker sin reconciliar se informa
interrupción, sin relanzarlo ni afirmar cierre; requiere inspección propia.
La activación en Studio4750 sigue bloqueada por política de ejecución; las
comprobaciones anteriores pertenecen a la instancia aislada, no a la del usuario.

Código funcional publicado en `4242eca`. CI principal45773151291 aprobada:
3832passed/44skipped/3xfailed/40subtests,107,66s. Contratos e instalación Windows
y Linux del push45773142874 aprobados;43regresiones de navegador aprobadas.
El resultado del workflow PR paralelo se registra en el informe de CI.
