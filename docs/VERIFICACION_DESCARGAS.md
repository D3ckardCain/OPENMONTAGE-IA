# Comprobar las descargas locales

> **Actualización 12/11/2026:** [estado e inventario histórico de ADATA y Seagate](ESTADO_PROYECTO.md). El catálogo original encontró 367 de 375 por ruta/tamaño; ocho ausencias se comunicaron para descarga, sin nueva verificación. Los [archivos adicionales](DESCARGAS_ADICIONALES.md) tienen [manifiesto separado](model_download_manifest_additional.json). No confundir descarga declarada, tamaño coincidente, SHA verificado e inferencia correcta.

Estado: 6 de noviembre de 2026. Comprobador nuevo:
`scripts/verify_model_downloads.py`. Solo usa biblioteca estándar Python 3.10+,
compatible con el Python embebido de ComfyUI. El código del fork y su manifiesto
deben estar descargados en la PC; instalar ComfyUI solo no instala este script.

## Dos comprobaciones diferentes

| Comprobación | Qué demuestra | Qué falta |
|---|---|---|
| `check_local_models.py` | Estructura safetensors legible de los flujos Wan 14B revisados; HTML, offsets o truncación inválidos | No compara identidad ni contenido contra un hash oficial |
| `verify_model_downloads.py` sin opciones | Presencia y tamaño exacto del grupo Wan del manifiesto (14B y 5B; 12 archivos) | Un archivo equivocado del mismo tamaño puede pasar |
| `verify_model_downloads.py --sha256` | SHA256 de archivos completos coincide con el registrado en el manifiesto, donde está disponible | No demuestra licencia, compatibilidad, calidad ni seguridad del contenido |

El manifiesto fija revisiones remotas y registra tamaños/SHA256 publicados para
los pesos grandes. Estos hashes son evidencia de correspondencia con ese
inventario, no una firma independiente del fabricante. Para entradas pequeñas
sin SHA256, el programa informa `HASH_UNAVAILABLE`, nunca `SHA256_OK`.

## Uso preparado para Windows

Desde la raíz del repositorio, para una revisión rápida del grupo Wan:

```powershell
& "C:\OPENMONTAJE-IA\ComfyUI_windows_portable\python_embeded\python.exe" scripts/verify_model_downloads.py
```

Para verificación de contenido del mismo grupo, cuando terminen las descargas:

```powershell
& "C:\OPENMONTAJE-IA\ComfyUI_windows_portable\python_embeded\python.exe" scripts/verify_model_downloads.py --sha256
```

Son ejemplos alternativos, no instrucciones para ejecutarlos todos ahora.

- `--groups mochi` selecciona otro grupo; `--groups wan mochi` combina y elimina
  destinos repetidos. `--groups all` revisa todos los grupos.
- `--root "D:\OPENMONTAJE-IA"` permite revisar la misma estructura movida a otra
  unidad o PC, conservando las subcarpetas.
- Hashear toda la lista lee más de 1 TB; empezar por el grupo que se vaya a probar.
- El script no descarga, no instala, no cambia nombres y no borra archivos.
- Nunca abre `.pt`, `.pth`, `.bin` o `.ckpt` con torch/pickle: solo lee bytes para
  el hash. No ejecuta pesos ni conecta con Hugging Face o proveedores.

Grupos definidos: `wan`, `cosmos`, `ltx-legacy`, `mochi`, `cogvideo`, `kandinsky`,
`longcat`, `longcat-avatar`, `magihuman`, `ltx23`, `ltx25`, `hunyuan15`,
`framepack`, `h3`, `qwen-image`, `flux-klein`, `z-image`, `kokoro`, `qwen-tts`,
`acestep`.

## Estados y código de salida

- `SIZE_OK`: tamaño correcto, contenido sin verificar.
- `SHA256_OK`: coincide con el hash esperado.
- `MISSING`, `SIZE_MISMATCH`, `HASH_MISMATCH`, `INVALID`, `UNREADABLE`: error.
- `CHANGED`: archivo cambió durante lectura; revisar después de acabar descarga.
- `HASH_UNAVAILABLE`: tamaño correcto, sin hash registrado.

Salida 0: la comprobación solicitada terminó sin fallos. Salida 1: hay errores.
Salida 2: argumentos/manifiesto inválidos. Salida 3: se pidió SHA256 y quedaron
archivos sin verificación de contenido por falta de hash. Un cero en modo tamaño
no equivale a aprobación de contenido.

## Estado de integración

Solo el adaptador `comfyui_wan_local` y sus dos grafos Wan 14B tienen actualmente
una ruta restringida en el fork. Descargar los otros grupos y verificar sus
hashes no añade automáticamente sus plantillas ni su integración en la app.

El requisito de calidad y velocidad se cerrará por motor: prueba real T2V/I2V,
semilla, resolución, fotogramas, clip guardado, RAM/VRAM, tiempo y evaluación
contra la referencia acordada. Los tests unitarios y las simulaciones HTTP no
sustituyen esa prueba.

## Verificación del comprobador

Pruebas reproducibles:

```text
python -m pytest tests/tools/test_verify_model_downloads.py tests/tools/test_local_model_downloads.py -q
```

Los casos usan archivos sintéticos pequeños e incluyen contenido equivocado del
mismo tamaño, truncación, rutas Windows reubicadas, hash ausente, cambio durante
lectura, índices de grupos y deduplicación. No se han leído los modelos del
propietario ni se han probado en su PC.

La batería enfocada ampliada terminó con **650 pruebas aprobadas, 1 omitida y
14 subpruebas aprobadas** en 12,84 s. Son comprobaciones locales sintéticas, no
inferencia con pesos reales ni aprobación de toda la suite heredada.


## Validación del manifiesto antes de revisar archivos

Actualización del 7 de noviembre de 2026: el comprobador rechaza inventarios o grupos vacíos, IDs de grupo repetidos o reservados, referencias a destinos inexistentes (incluso en grupos no seleccionados) y entradas con estructura inválida. También rechaza destinos duplicados que solo difieren en mayúsculas o barras, para no tratar como distintos dos nombres del mismo archivo en Windows. Los archivos compartidos por grupos válidos siguen comprobándose una sola vez.

Un manifiesto vacío o ambiguo termina con código 2; no puede producir una aprobación de cero archivos. Esto valida la estructura del inventario, no demuestra que una lista editada conserve todos los componentes del motor: debe mantenerse el manifiesto revisado del repositorio.

Validación de esta actualización: **49 pruebas aprobadas** entre ambos comprobadores, incluyendo 13 casos nuevos. Se usaron archivos sintéticos pequeños y el inventario real de 375 destinos; no se han inspeccionado los pesos de tu PC ni realizado inferencia.

## Manifiesto adicional de noviembre

Preparado para la fase posterior de verificación (no ejecutado en los discos):

```powershell
python scripts/verify_model_downloads.py --manifest docs/model_download_manifest_additional.json --groups all --root "D:\OPENMONTAJE-IA" --sha256
```

El manifiesto conserva el prefijo lógico C:/OPENMONTAJE-IA del comprobador; `--root`
lo redirige al disco elegido. Identificar antes ADATA o Seagate por nombre y serie,
no solo por D:. Cada disco contiene una parte del conjunto: un resultado MISSING
no demuestra que falte en ambos. Hay que combinar inventarios y resolver fuentes
compartidas antes del dictamen final. Las entradas sin SHA256 autorizado producen
HASH_UNAVAILABLE cuando se solicita hash; Git blob SHA1 no reemplaza ese SHA256.
El manifiesto adicional registra archivos HF seleccionados y reutilizaciones, no
los grupos de GitHub ni todos los auxiliares omitidos: no es un instalador completo.
