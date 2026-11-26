# Chatterbox regional: muestras locales y límites

Seguimiento #96/#3, 26 noviembre 2026; continuación de e7df084.

## Recursos y entorno

Los T3 es-MX/LatAm y es-ES de las revisiones oficiales
`27e595bf2fe7be0533ca299d9afafcde08b7cca7` y
`7262b364e3222ba9446c9289e7485eadc47ed902` están completos y verificados.
Comparten `s3gen_v3.safetensors` y
`grapheme_mtl_merged_expanded_v1.json` ya disponibles en C:; el encoder
`ve.pt` verificado se usa desde D:. No se copiaron esos recursos a cada perfil.
El inventario JSON de esta entrega contiene tamaños, SHA256 y estados por ruta.

Python3.11.9 en `.runtime/chatterbox/venv`, separado de `.venv`, ComfyUI y Qwen.
Torch/torchaudio2.6.0+cu124 se instalaron desde wheels existentes en caché;
los enlaces duros al wheelhouse no duplican su contenido. Transformers5.2.0,
Diffusers0.29.0, s3tokenizer0.3.0, safetensors0.5.3, NumPy1.26.4,
librosa0.11.0 y Perth1.0.1 de distribución importan offline.
`perth.__version__` informa1.0.0 aunque sus metadatos de distribución son1.0.1;
se conservan ambas observaciones, sin ocultar la diferencia.

El código MIT upstream está fijado en
[`ab55923`](https://github.com/resemble-ai/chatterbox/tree/ab55923c27757c90cfcc407baa57dc25a7d25217).
No se instaló el fork del Space. Se conservan atribuciones del paquete upstream,
incluidos sus componentes Apache2; los pesos regionales declaran MIT.
Perth conserva su marca de agua. No se usaron voces de demostración del Space.

Es un runtime español acotado: `pip check` aún señala Gradio y spacy-pkuseg
ausentes. Gradio pertenece a la interfaz de demostración alternativa y pkuseg
a la segmentación china. No se presenta como instalación completa de todas
las funciones e idiomas del paquete upstream.

## Loader y puente compartido

`lib/chatterbox_regional_runtime.py` utiliza las clases upstream. La comparación
con constructores reales en dispositivo meta acredita292 tensores T3 y2488 del
decoder; faltan únicamente los buffers deterministas `tokenizer._mel_filters`
y `tokenizer.window`. Se reconstruyen a través del propio constructor y después
se aplica **strict=True**. Claves inesperadas, parámetros ausentes y formas
distintas fallan antes de aceptar el estado. No se usa strict=False.

`model_chatterbox` acepta selección explícita `regional_profile`:
`chatterbox-es-mx-latam` o `chatterbox-es-es`, `language="es"`,
`device="cuda"`, referencia local y `reference_authorized=true`.
Usa el Python regional, sin reescribir configuración ni ruta del adaptador
heredado. Las peticiones sin perfil conservan su ruta anterior; no son un
fallback de una petición regional.

Contrato actual: texto1–240 caracteres, presupuesto32–512 tokens (160 por
defecto), referencia autorizada y margen CUDA libre mínimo6GiB. No cambia a
CPU automáticamente. El límite se aplica a la llamada interna de upstream,
que originalmente fija1000 tokens; se restaura el método al terminar o fallar.
El worker comprueba identidad de la referencia antes/después y devuelve
procedencia, perfil, revisión del código, límite y estado del watermark.
Reutiliza el transporte/proceso controlado ya existente para cancelación;
no se creó otra cola. No se ejecutó una nueva prueba real de cancelación.

Para una petición nueva autorizada, el agente reutiliza el registro:

```python
from tools.tool_registry import registry
registry.discover()
tool = registry.get("model_chatterbox")
# No volver a ejecutar las muestras ya aprobadas para comprobar disponibilidad.
# Una ejecución nueva requiere todos estos campos:
params = {
    "regional_profile": "chatterbox-es-es", "language": "es", "device": "cuda",
    "reference_audio": "RUTA_LOCAL_AUTORIZADA", "reference_authorized": True,
    "text": "TEXTO_NUEVO_AUTORIZADO", "max_new_tokens": 160,
    "output_dir": "projects/PROYECTO/assets/audio/TRABAJO_NUEVO", "timeout": 180,
}
# result = tool.execute(params, control=control_existente)
```

Las cualificaciones privadas en `.runtime/chatterbox/qualifications.json`
ligan las dos muestras reales a identidades de recursos, código instalado,
loader, Python, versiones y WAV resultante. Consultar perfiles solo lee
metadatos/recibos: no importa Torch, calcula hashes grandes ni sintetiza.
Si cambian las identidades, deja de acreditar la muestra. No se publican
entornos, configuraciones ni ese archivo privado.

## Pruebas funcionales realizadas

Texto fijo: «Esta es una prueba local de voz.» Referencia sintética QA de
Qwen VoiceDesign ya existente, cuya instrucción excluye imitar a una persona.
No se repitió su síntesis. Semilla42, tope160 tokens, conexiones bloqueadas.

| Perfil | Duración | Frecuencia | Inferencia medida | Pico CUDA asignado |
|---|---:|---:|---:|---:|
| es-MX/LatAm | 2,32s | 24kHz | 15,97s | 4.337.787.392bytes |
| es-ES | 2,20s | 24kHz | 4,34s | 4.337.787.392bytes |

WAV PCM16 mono, datos finitos y señal no nula, watermark aplicado. Cada proceso
terminó y liberó su modelo antes de iniciar el siguiente. La diferencia de
tiempo no es un benchmark comparable: la primera ejecución puede calentar
cachés. No acredita naturalidad, acento percibido, comprensión exacta ni
compatibilidad general de cualquier trabajo con8GB.

Se reabrieron los WAV nuevos con el lector PCM existente:52.800 y55.680
muestras, mono/16bits/24kHz, decodificación válida y fracción de clipping0.
Esta comprobación de persistencia no repitió ninguna síntesis ni ASR.

Muestras y recibos se conservan, sin sobrescribir:
`projects/qa96-chatterbox-regional/assets/audio/<regional_profile>/`.
No se suben WAV ni pesos a GitHub. Escucha humana pendiente.

Las muestras son ejecuciones reales del loader/generador. El enrutado nuevo
del adaptador tiene pruebas unitarias con transporte explícitamente simulado;
no se repitieron las síntesis para afirmar un segundo recorrido extremo a
extremo. La API/panel reales de Studio aislado4766 muestran ambos perfiles con
muestra comprobada y **preescucha regional de Audio pendiente**. No equivalen
a activación en4750, que no se reinició. El botón del panel solo consulta;
no se añadió un control de síntesis que el panel aún no ejecute.

## CosyVoice y descargas que continúan

El conjunto estándar D: de CosyVoice tiene seis pesos verificados y ocho
auxiliares con Git blobs oficiales. Los dos ONNX pasan checker1.23.2 sin
inferencia; BlankEN tiene290 tensores safetensors válidos; PT se inspecciona
como ZIP sin ejecutar pickle. Los pesos nuevos terminados en C: también se
verificaron una vez. La validación ONNX se reutiliza por SHA256 idéntico; no se
repitió el parser sobre la segunda copia. En C: falta
`CosyVoice-BlankEN/model.safetensors`; ya existe verificado en el conjunto D:.
No se descarga otra copia ni se mezclan configuraciones entre carpetas.

Una comprobación posterior de metadatos PT usó Torch2.6
`weights_only=True`, `mmap=True` y `FakeTensorMode`: llm293, flow330 e hift328
tensores FP32, sin materializar pesos ni construir el modelo. BlankEN también
pasó el parser safetensors0.5.3 en modo metadatos, sin `get_tensor`.
No se convirtió esto en acreditación del ABI ni del runtime CosyVoice.

Python Cosy3.11.9 separado y código Apache2 fijado en
`074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc`; Matcha-TTS en
`dd9105b34bf2be2230f4aa1e4769fb586a3c824e`. Solo se preparó código Python y
documentación; no se ejecutó YAML ni se compiló infraestructura.
Requisitos oficiales incluyen Torch/torchaudio2.3.1,
Transformers4.51.3 y ONNXRuntimeCPU1.18 en Windows. La resolución offline se
detiene en Torch2.3.1 ausente en caché; no se mezcló con Chatterbox5.2.

Se consideró el wheel CPU oficial Torch2.3.1 de159.781.829bytes, SHA256
`5802530783bd465fe66c2df99123c9a54be06da118fbd785a25ab0a88123758a`.
La petición propia se detuvo con temporal de0bytes al comprobar insuficiencia
de RAM: disponible aproximadamente5,4GB frente a estimación conservadora
9.933.571.152bytes (no pico medido). No se reintentó ni se tocó FDM.
No se carga CosyVoice ni se declara su voz operativa.

Código/ficha declaran Apache2; el alcance comercial del disclaimer de ejemplos
sigue sin respuesta visible en la
[discusión19](https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512/discussions/19).
No se infiere NC de los pesos ni autorización comercial integral. Evaluación
interna y derechos de cada referencia son cuestiones separadas.

### Turbo terminó durante la comprobación

Una nueva pareja de snapshots encontró los nueve archivos de Turbo terminados
y estables. Se verificaron una vez los nuevos T3, meanflow y auxiliares frente
a `749d1c1a46eb10492095d68fbcf55691ccf137cd`; los archivos anteriores reutilizan
su caché. Es un perfil inglés distinto y no sustituye a los regionales.

Se reutilizó el mismo entorno, clases upstream y carga estricta, con T3/decoder
en CUDA para limitar duplicación temporal en RAM. El intento llegó a la
preparación de referencia, que rechazó el audio sintético de1,92s:
`Audio prompt must be longer than 5 seconds!`. No produjo WAV. La revisión de
cabeceras WAV de proyectos y recursos QA Qwen/Piper no encontró una referencia
sintética autorizada >5s. No se usaron voces reales/demo ni se repitió o rellenó
el audio para eludir la condición. Carga comprobada **no** es síntesis operativa.
El snapshot de memoria del informe del fallo precede al fin del proceso;
tras terminar se comprobó que no quedaban procesos de cómputo CUDA activos.

No se descargaron variantes RL, batch o TensorRT. HTTP10054 mantiene la regla:
recuperar estado antes de repetir una escritura incierta, sin cambios de red.
