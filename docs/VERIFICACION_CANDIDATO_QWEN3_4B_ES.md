# Candidato nuevo Qwen3_4B: identidad no verificada por fallo de lectura

Seguimiento #82. El usuario autorizó sustituir únicamente el archivo antiguo
de D: y eliminarlo sin respaldo **solo si tamaño, SHA256 y estructura pasan**.
En esta ejecución esa condición no se cumple. **No se sustituyó, movió ni
eliminó ningún modelo; tampoco se creó el archivo temporal de transferencia.**

Primero se consultaron inventarios/caché anteriores y se buscaron nombres en
las carpetas conocidas de modelos y descargas de D:/E:, ambos disponibles.
Dos archivos encontrados: el antiguo de D: y el candidato nuevo:

```text
E:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\text_encoders\candidates\qwen_3_4b-5b3abca5-6c671498.safetensors\qwen_3_4b.safetensors
```

| Comprobación del candidato | Resultado |
|---|---|
| Tamaño | 8044982048 bytes: coincide |
| Prefijo de8 bytes / longitud little-endian | Cabecera45848 bytes; dentro del archivo y del límite16MiB |
| JSON/metadatos | Válido; sin claves duplicadas; metadatos vacíos |
| Tensores | 398, todos BF16 |
| Formas/tipos/extensiones | Bytes por tensor coherentes |
| Offsets | Contiguos, sin huecos/solapamientos; payload completo8044936192 bytes |
| SHA256 completo | **No obtenido: error de lectura** |
| Compatibilidad/inferencia | No probadas; no se cargó modelo ni importó Torch/ComfyUI |

SHA256 esperado:
`6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a`.
Referencia previamente fijada: [Comfy-Org/flux2-klein-4B, revisión5b3abca5](https://huggingface.co/Comfy-Org/flux2-klein-4B/tree/5b3abca5c0dc1ecd4eaf3340868d09063fc1c965/split_files/text_encoders).
No se descargaron pesos ni otra copia.

La lectura secuencial para SHA256 terminó con **OSError: [Errno22] Invalid argument**.
Último avance registrado:6450839552 bytes (~80%). No se dispone del offset exacto
del error. No se presenta un hash parcial como SHA256 válido, ni se clasifica
el resultado como discrepancia de hash. El fallo no identifica por sí solo una
causa de disco, conexión, sistema de archivos o contenido; no se declara corrupción.

Tras el fallo D:/E: siguen accesibles por metadatos, y ambos archivos conservan
tamaño/mtime/ctime/dispositivo/inode anteriores. Eso no demuestra lectura íntegra.
El resultado antiguo de D: se reutiliza solo por identidad/metadatos coincidentes:
hash históricoa5e1c4ed… y cabecera previamente inválida; no se releyeron sus8GB.
El original inválido permanece, ya que falló una condición de sustitución.

Se comprobaron además7 casos sintéticos pequeños del validador: caso válido,
extensión fuera de archivo, tamaño incompatible, hueco, solapamiento, clave JSON
duplicada y longitud excesiva antes de leer JSON. Esto valida el rechazo del
lector, no sustituye el hash del candidato real.

Evidencia: `VERIFICACION_CANDIDATO_QWEN3_4B_20261124.json`; manifiesto local de
tensores y logs en `.runtime/qa/qwen-replacement-20261124/`. El script preparado
para transferencia/reemplazo **no se ejecutó**. Sin reintentos automáticos,
inferencias, instalaciones, movimientos ni cambios de configuración de ComfyUI.
No se eliminaron otros modelos. PR#2 sigue en borrador y costo operativo$0.
