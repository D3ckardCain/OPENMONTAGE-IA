# Qwen3 4B: sustitución y limpieza verificadas (#82)

El25-11-2026 se verificó la descarga nueva ya existente, sin descargar otra
copia ni cargar el modelo. Tamaño **8044982048bytes** y SHA256:

```text
6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a
```

Coincide con los metadatos oficiales ya fijados de
Comfy-Org/flux2-klein-4B@5b3abca5c0dc1ecd4eaf3340868d09063fc1c965,
`split_files/text_encoders/qwen_3_4b.safetensors`.
Se reutilizó la referencia registrada; no se repitieron diagnósticos de disco.

## Verificación y transferencia

- Descarga localizada en
  `C:\Users\sando\Downloads\qwen_3_4b.safetensors\qwen_3_4b.safetensors`.
  Identidad/metadatos estables antes/después del SHA256 completo.
- Prefijo8bytes comprobado antes del JSON: cabecera45848bytes, dentro del
  archivo y del límite16MiB. JSON sin claves duplicadas, metadatos vacíos.
-398tensores BF16, nombres/formas/tipos/longitudes coherentes, offsets contiguos
  y sin huecos/solapamientos; payload8044936192bytes. Cabecera SHA256
  `4552846f1e705a23d7340bf1ffcc7251d9f742cd45e5029f80cc6694507a89ce`.
- D: comprobado como ADATA/NTFS, identificador de volumen2728866502;
  identidad del antiguo y de la otra copia defectuosa igual a la caché registrada.
  Solo comprobación de identidad de destino; sin SMART/eventos/pruebas de disco.
- Copia a temporal exclusivo en el directorio de destino. Hash simultáneo a
  la copia igual al oficial, flush/fsync y **SHA256 completo del archivo escrito
  en D:** también igual. Estructura de destino comprobada antes de sustituir.
- Sustitución por renombrado atómico del archivo verificado sobre el antiguo,
  sin respaldo. La identidad del archivo verificado se conserva tras el
  renombrado; tamaño y cabecera se volvieron a comprobar. No se repitió otro
  SHA256 completo tras renombrar el mismo archivo.

## Estado final y alcance de limpieza

Única copia válida entre las rutas conocidas examinadas:

```text
D:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\text_encoders\qwen_3_4b.safetensors
```

Eliminaciones autorizadas y comprobadas después de verificar la transferencia:

1. Antiguo inválido de la ruta activa D:, sustituido sin respaldo; huella previa
   cacheada `a5e1c4ed…`, identidad/metadata revalidadas sin releer sus8GB.
2. Segunda copia defectuosa, antes E: y ahora F:, retirada exclusivamente de
   `F:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\text_encoders\candidates\qwen_3_4b-5b3abca5-6c671498.safetensors\qwen_3_4b.safetensors`.
   Huella previa `6cbad3f9…`, device4101616990/inode2814749767109048 y tiempos
   idénticos a la evidencia anterior; no se volvió a calcular su hash.
3. Descarga temporal válida de C: indicada arriba, eliminada después de asegurar
   el destino; el temporal de transferencia D: dejó de existir al renombrarlo.

Solo archivos exactos identificados; no borrado recursivo ni eliminación de
carpetas/otros modelos. La afirmación de copia única se limita a las rutas
conocidas comprobadas, no a una búsqueda forense de todos los discos.

**Identidad y estructura acreditadas; compatibilidad funcional no probada.**
No Torch/ComfyUI importados, inferencia, reparación, nueva descarga, cambio de
configuración ni entorno. Se conservan otros modelos, originales de proyectos,
coste$0 y PR#2 en borrador. No se ejecutó suite/CI para una operación local de
archivos y documentación; la CI previa no se usa como evidencia de estos pesos.

Evidencia detallada: [JSON de verificación y limpieza](QWEN3_4B_SUSTITUCION_VERIFICADA_20261125.json).
