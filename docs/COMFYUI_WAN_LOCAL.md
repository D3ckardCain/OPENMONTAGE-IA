# Sustitución de video de pago: Wan 2.2 local

## Alcance actual

Objetivo activo: sustituir la generación de video mediante nodos ComfyUI con
créditos por ejecución local, sin perder la meta de calidad y velocidad.
No se considera terminado hasta producir y evaluar video real en GPU.

Equipo comprobado mediante salidas de Windows del propietario:

| Componente | Confirmado |
|---|---|
| CPU | Intel Core i7-12650H, 12.ª generación |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| VRAM | 8188 MiB |
| RAM | 16 GB |
| Controlador NVIDIA | 610.78 |
| ComfyUI | 0.44.0, portable para Windows |
| PyTorch | 2.14.1+cu130 |
| Python embebido | 3.13.14 |

La mención inicial de RTX 4080 quedó corregida por el diagnóstico real. ComfyUI
arranca y reconoce CUDA. Los pesos están en proceso de descarga; aún no se ha generado video.
Cada flujo revisado requiere seis archivos: T2V e I2V comparten codificador y
VAE, pero usan modelos de difusión y LoRAs distintos (diez archivos en total).
Ruta indicada: `C:\OPENMONTAJE-IA\ComfyUI_windows_portable`.
No se reutilizan especificaciones de otros proyectos.

## Sustituto incorporado

Herramienta: `comfyui_wan_local`. Hereda los constructores de los flujos Wan 2.2
14B FP8 de OpenMontage, con las LoRAs LightX2V de cuatro pasos. Admite texto a
video e imagen local a video. Mantiene la semilla cero como valor válido.

La licencia del repositorio oficial Wan 2.2 es Apache 2.0:
https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt
Antes del despliegue se verificarán también las licencias y versiones de los
pesos y LoRAs exactos descargados; no se deducen solo de la licencia del código.

## Reglas de ejecución

- ComfyUI debe estar en la misma PC mediante HTTP en una dirección loopback.
  `localhost` se normaliza a `127.0.0.1` sin resolver DNS.
- Se respetan `COMFYUI_VIDEO_SERVER_URL` y `COMFYUI_SERVER_URL`, pero se rechazan
  servidores públicos y LAN en este adaptador. No se usan proxies del entorno
  ni se siguen redirecciones.
- Solo se aceptan `wan22-t2v-4step.json` y `wan22-i2v-4step.json`. Se fija su
  contenido revisado mediante huellas de JSON canónico, compatibles con CRLF.
- Se pueden variar texto, dimensiones, cantidad de fotogramas, semilla y nombres
  de entrada/salida. Modelos, LoRAs, nodos, enlaces e instrucciones extra se
  rechazan si difieren de las plantillas revisadas.
- Dimensiones en múltiplos de 16 y cantidad de fotogramas `4n+1`.
- La referencia de imagen debe ser un archivo local. Salida MP4.
- No acepta flujos personalizados, familias con créditos, URLs de referencia
  ni reanudación de trabajos cuya procedencia no se ha verificado.
- Si faltan modelos, devuelve el error y las instrucciones existentes; no
  sustituye automáticamente el video por imágenes ni cambia de proveedor.

La herramienta se descubre mediante el registro normal. Las producciones reales
deben seguir un manifiesto de `pipeline_defs/`, sus etapas y sus aprobaciones;
estas pruebas no constituyen una producción ni autorización para omitirlas.

La conexión mediante `video_selector`, incluida la adaptación de duración,
proporción y controles de selección, se describe en
[Selección de proveedores locales](SELECCION_LOCAL.md).

## Pruebas reproducibles

```bash
python -m pytest tests/tools/test_zero_cost_policy.py tests/tools/test_comfyui_wan_local.py tests/tools/test_base_tool_dependencies.py -q
```

Las pruebas de integración levantan un servidor HTTP **emulado** en loopback:
comprueban consulta de modelos, envío del grafo, consulta de estado, subida de
imagen y descarga de un archivo de prueba. Ese archivo es un marcador binario
explícito, no un video generado por IA. También se prueban rechazo de nodos y
modelos alterados, servidores externos, redirecciones y entradas no permitidas.

## Qué falta para cerrar este objetivo

1. Completar la descarga de los modelos en la PC comprobada.
2. Instalar y verificar las versiones de ComfyUI, modelos y LoRAs locales.
3. Producir muestras reales T2V e I2V a través del pipeline, registrando semilla,
   dimensiones, fotogramas, duración, pico de VRAM y tiempo de extremo a extremo.
4. Comparar esas muestras con una demostración comercial concreta y la misma
   promesa de entrega. Calidad de movimiento, coherencia y velocidad siguen
   pendientes de medición; los tests HTTP no prueban esas propiedades.

El perfil de recursos procede de los flujos originales y es orientativo, no
una medición en la RTX 4060 Laptop del propietario. El cliente no puede garantizar que
un servidor ComfyUI modificado maliciosamente ejecute lo que declara: se requiere
una instalación local confiable. Esta barrera tampoco aísla código externo al
adaptador ni supervisa el tráfico del proceso ComfyUI en el sistema operativo.

## Comprobación de descargas antes de generar

Desde la raíz de este repositorio, con Python 3.10+ (sin dependencias externas):

```powershell
& "C:\OPENMONTAJE-IA\ComfyUI_windows_portable\python_embeded\python.exe" scripts/check_local_models.py --models-dir "C:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models" --operation all
```

Este comando se prepara para cuando el código del fork esté descargado en la PC;
instalar ComfyUI por sí solo no instala este script. Puede usarse `--operation
t2v` o `--operation i2v` para revisar solo el flujo que se probará primero.

- Lee nombres y carpetas directamente de las dos plantillas revisadas.
- Detecta archivos ausentes, HTML disfrazado de `.safetensors`, punteros Git LFS,
  cabeceras inválidas, datos truncados y offsets inconsistentes.
- `HEADER_OK` significa estructura legible, no identidad ni integridad
  criptográfica verificadas. Un modelo equivocado renombrado o una alteración de
  los datos puede superar esta comprobación; faltan hashes oficiales para ello.
- No usa GPU, no descarga y no cambia archivos. Salida 1 si falta un archivo o
  falla la comprobación; 0 si todas las estructuras son legibles. Mientras una
  descarga siga activa puede aparecer truncada; revisar otra vez al terminar.
- Las LoRAs I2V del flujo son `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors`
  y `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors`. Las T2V v1.1 no las
  reemplazan; tampoco deben renombrarse para aparentar que son I2V.

LTX, Cosmos y Wan 5B son candidatos descargables pendientes de integración y
prueba; el adaptador `comfyui_wan_local` actual solo ejecuta los dos flujos Wan
14B revisados. Tener sus pesos descargados no los habilita automáticamente aquí.

## Referencias de imagen y recuperación de trabajos

La llamada directa debe indicar `operation=image_to_video` cuando se envía
`reference_image_path`. Si se omite la operación o se elige `text_to_video`,
la herramienta devuelve un error antes de conectarse. No descarta silenciosamente
la imagen ni cambia de operación. I2V sigue exigiendo un archivo local existente.
Los prompts formados solo por espacios o saltos de línea también se rechazan.

Si falla la espera después de recibir un `prompt_id`, se conserva ese identificador
para revisar la cola/historial local. El error no recomienda `resume_prompt_id`:
este adaptador no admite reanudar trabajos cuya procedencia no ha verificado.
Devuelve `resume_supported=false`, `resubmit_requires_job_check=true` y
`job_state=unknown_check_local_queue`. Ese estado no prueba si el trabajo terminó,
falló o sigue en curso. No se reenvía automáticamente ni se cambia de proveedor.

La revisión se comprueba con archivos sintéticos y servidor HTTP emulado. No
se han generado vídeos ni medido rendimiento en GPU con estas pruebas.

Validación de esta revisión: **655 pruebas aprobadas, 1 omitida y 14 subpruebas
aprobadas** en la batería enfocada (12,57 s). El grupo específico Wan/selectores
pasó 68 pruebas. No se declara aprobada toda la suite heredada.


### Comprobación previa sin generación

El adaptador local valida los mismos parámetros en `dry_run` y en `execute`. El modo de prueba solo indica `would_execute=true` si el servidor responde y aparecen los modelos y las clases de nodos del flujo correspondiente. Un servidor desconectado se informa como `unavailable`; modelos o nodos ausentes, como `degraded`. Los requisitos de texto a vídeo e imagen a vídeo se comprueban por separado. La ejecución también rechaza nodos ausentes antes de subir imágenes o encolar trabajos.

Esta comprobación consulta metadatos locales: no genera, no sube imágenes ni escribe vídeos. La presencia de nombres no certifica integridad de pesos, compatibilidad completa de las firmas de nodos, memoria suficiente ni calidad. Para integridad se usa el verificador de descargas; para rendimiento hace falta una generación real. `estimated_runtime_seconds=null` y `runtime_status=unmeasured_on_target_gpu` evitan presentar como medición un tiempo heredado.

Validación: pruebas con servidor HTTP local simulado cubren servidor desconectado, entradas inválidas, modelos y nodos ausentes, diferencias entre operaciones y modo de prueba disponible sin envíos ni archivos. Estos ensayos no son inferencia de IA.


### Recuperación de resultados y escritura del vídeo

Actualización del 7 de noviembre de 2026: una vez que ComfyUI devuelve el identificador de un trabajo Wan local, los fallos posteriores al esperar, buscar resultados o descargar/guardar el archivo conservan ese identificador en el error. El adaptador indica revisar la cola e historial locales antes de volver a enviar; no reintenta la generación automáticamente ni habilita la reanudación de trabajos no verificados. Así también se puede localizar un vídeo ya generado cuando lo que falló fue su recuperación.

La descarga local escribe primero un archivo temporal en la carpeta de destino y solo reemplaza el vídeo anterior al terminar la escritura. Si el reemplazo falla (por ejemplo, archivo bloqueado), conserva el destino anterior y elimina el temporal. Esto protege frente a los fallos de escritura comprobados; no certifica que los bytes descargados constituyan un MP4 válido ni garantiza durabilidad ante corte eléctrico. La validación real del vídeo sigue pendiente.

Tres pruebas nuevas cubren desconexión al descargar, reemplazo fallido y reemplazo correcto. La batería enfocada termina con **679 pruebas aprobadas, 1 omitida y 14 subpruebas aprobadas**. Usa resultados sintéticos; no mide calidad ni rendimiento de inferencia.
