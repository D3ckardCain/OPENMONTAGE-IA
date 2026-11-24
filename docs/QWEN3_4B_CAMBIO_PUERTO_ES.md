# Qwen3_4B tras cambiar de puerto: misma discrepancia, sin sustitución

Seguimiento #82. Se ejecutó **una sola lectura completa** con
`Get-FileHash -LiteralPath <candidato exacto de E:> -Algorithm SHA256`.
El primer chequeo de destino se detuvo antes de calcular ningún hash al no
encontrar D:. La lectura de E: se realizó después como tarea independiente.

```text
E:\OPENMONTAJE-IA\ComfyUI_windows_portable\ComfyUI\models\text_encoders\candidates\qwen_3_4b-5b3abca5-6c671498.safetensors\qwen_3_4b.safetensors
```

| Campo | Resultado |
|---|---|
| Intervalo UTC | 2026-11-24 22:00:17–22:09:50 |
| Get-FileHash | Completado sin excepción |
| Tamaño | 8044982048 bytes |
| Identidad/metadatos | Tamaño,mtime,ctime,dispositivo,inode sin cambios |
| Cabecera anterior | Sigue siendo reutilizable: 398 tensores BF16,formas/bytes/offsets válidos |
| Hash oficial esperado | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` |
| Hash obtenido | `6cbad3f9d28e15e86d3ddb1842cd51653ad236c92e9a2204bd4415241af22f53` |
| Comparación con lectura anterior | Exactamente el mismo hash observado |
| Nuevos eventos de almacenamiento consultados durante la lectura | 0 |
| Sustituciones/borrados/movimientos | Ninguno |

## Conexión y eventos

E: continúa identificado como Seagate Basic USB,disco1. La cadena PnP actual es
Seagate Basic → UASPStor → concentrador raíz USB3.0 → controlador Intel xHCI.
El concentrador USB genérico intermedio de la consulta anterior ya no aparece.
Esto confirma el cambio de ruta observado; no acredita por sí solo salud completa.

Se guardó un RecordId de referencia y se consultó System para el intervalo del
hash, antes de comparar los eventos. Comprobación posterior independiente:
`queried_no_matching_events`. IDs consultados:7,11,15,51,55,98,129,153,154,157;
proveedores disk/NTFS/Storport y almacenamiento relacionados. No se afirma que
la ausencia de estos eventos sea una prueba de superficie o descarte todo fallo.

La discrepancia se reproduce incluso en esta pasada sin nuevos avisos de E/S.
Es evidencia de una huella observada consistente y distinta de la referencia;
no identifica si el origen fue descarga,variante,alteración persistente u otra
causa. No se atribuye causalidad exclusivamente al hub: también D: no estaba
montado durante esta prueba.

## Destino y conservación

Antes y después de la lectura, `Get-Partition -DriveLetter D` devuelve
`CmdletizationQuery_NotFound_DriveLetter`; las unidades de sistema de archivos
visibles son C: y E:. **D: no está identificado/montado.** No se interpreta esto
como eliminación del archivo antiguo ni se intenta montar/asignar letras.

No se modificó ningún archivo de modelo: falla la condición obligatoria de SHA256
y además no se pudo confirmar el destino D:. No hay temporal de transferencia,
respaldo nuevo ni ejecución del script de sustitución. No se borraron archivos,
descargaron pesos, hicieron inferencias ni cambiaron ComfyUI,controladores o
configuraciones. Solo se escribieron recibos de auditoría en el proyecto y se
publicaron resultados. PR#2 permanece en borrador,costo operativo$0.

Evidencia: `QWEN3_4B_CAMBIO_PUERTO_20261124.json`. Los informes anteriores se
conservan; no se ocultan el fallo Python ni los eventos de E/S de la ruta previa.
