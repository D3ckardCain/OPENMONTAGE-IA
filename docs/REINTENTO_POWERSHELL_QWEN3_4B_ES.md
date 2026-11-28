# Qwen3_4B: SHA256 PowerShell distinto del oficial; sin sustitución

Seguimiento #82,24-11-2026. Se ejecutó **un solo reintento completo**, exactamente
con `Get-FileHash -LiteralPath ... -Algorithm SHA256`, de
`Microsoft.PowerShell.Utility`. No se buscó otro candidato ni se descargó nada.

```text
E:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\text_encoders\candidates\qwen_3_4b-5b3abca5-6c671498.safetensors\qwen_3_4b.safetensors
```

| Comprobación | Resultado |
|---|---|
| Tamaño | 8044982048 bytes: coincide |
| Identidad/metadatos antes y después | Tamaño,mtime,ctime,dispositivo,inode sin cambios |
| Cabecera anterior | Reutilizable:45848 bytes,398 tensores BF16,formas/bytes/offsets válidos,sin huecos/solapamientos |
| SHA256 PowerShell | Lectura completa terminada sin excepción, pero **no coincide** |
| Sustitución/borrados | **No realizados** |

Esperado:
`6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a`

Obtenido:
`6cbad3f9d28e15e86d3ddb1842cd51653ad236c92e9a2204bd4415241af22f53`

Este resultado sustituye la incertidumbre de hash **de este reintento** por una
discrepancia observada. No borra el fallo de lectura Python anterior. Un hash
completo observado y una cabecera válida no acreditan identidad oficial ni
compatibilidad de ejecución. La discrepancia no identifica por sí sola corrupción,
variante, descarga incorrecta ni origen físico del problema.

## Diagnóstico no destructivo

- E: sigue accesible; NTFS,Seagate Basic USB,disco1,Online,no marcado solo lectura.
  Windows informa Healthy/OK; ese resumen no descarta los avisos de E/S observados.
- Archivo Archive/SparseFile, no marcado solo lectura, sin enlace simbólico.
  `fsutil sparse queryrange` informa asignación del intervalo lógico completo
  [0,8044982048): la marca sparse no demuestra una descarga incompleta.
- Cuatro puntos de4096 bytes, dos lecturas cada uno: cabecera,primer tensor,
  último avance registrado anterior y cola. Todos devuelven4096 bytes iguales
  entre ambas lecturas. Son muestras lógicas que pueden usar caché Windows;
  no son una prueba de superficie ni de estabilidad íntegra de los8GB.
- Registro System, ventana consultada de2h: **12 eventos disk153** en disco1.
  Un mapa NTFS leído mediante `fsutil file queryextents`, geometría de partición
  y sectores relaciona10 direcciones con extensiones actuales del candidato.
  Incluye offset0 y la zona6528040960–6528434176. Correlación de direcciones;
  no se afirma que el último progreso Python fuera el offset exacto del fallo.
- Contadores Windows consultados:37°C,2851h,ReadErrorsTotal0,
  ReadErrorsUncorrected0,latencia máxima de lectura **42171ms (42.171s)**.
  Contadores de escritura no disponibles. No se han restablecido contadores.

[Microsoft explica el evento153 como timeout/reintento de una petición de
almacenamiento](https://learn.microsoft.com/en-us/troubleshoot/windows-server/backup-and-storage/troubleshoot-data-corruption-and-disk-errors#event-id-153-the-io-operation-at-logical-block-address-123456-for-disk-2-was-retried).
[La clase de contadores documenta ReadLatencyMax en milisegundos](https://learn.microsoft.com/en-us/windows-hardware/drivers/storage/msft-storagereliabilitycounter).
Estos datos respaldan problemas de latencia/reintentos en la ruta de E/S de E:;
no distinguen por sí solos medio,puerto/cable USB,controlador/driver o carga.
Tampoco prueban que esos reintentos expliquen la huella distinta.

El archivo tiene47315 extensiones según la consulta NTFS. No se desfragmentó,
reparó ni modificó la asignación. No había recibos locales Hugging Face en el
directorio del candidato; no se ha identificado el origen de la discrepancia.

## Estado conservado

El original inválido de D: y el candidato de E: permanecen en sus rutas, con
las mismas identidades/metadatos comprobados. No se ejecutó el script preparado
de transferencia, no hay temporal nuevo ni respaldo. Sin borrados,movimientos,
reparaciones,descargas,instalaciones,inferencia ni cambios de ComfyUI/configuración.
El hash observado queda en este informe, no se promueve a una caché de modelos
verificados. No se lanzó un tercer hash completo ni un bucle de reintentos.

La sustitución continúa bloqueada porque falla el SHA256 esperado. La causa
física exacta y el motivo de la discrepancia siguen sin aislar. Evidencia:
`REINTENTO_POWERSHELL_QWEN3_4B_20261124.json`. PR#2 en borrador,costo$0.
