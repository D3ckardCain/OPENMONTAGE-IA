# Activación agrupada pendiente de Studio

Petición del usuario: agrupar45b8609 con los demás cambios, evitando reinicios
repetidos. Esta entrega **no reinicia Studio ni activa herramientas**. La muestra
portuguesa de #107 está validada por el usuario; la española sigue pendiente.

| Seguimiento | Cambio preparado | Comprobación nueva tras una sola activación |
|---|---|---|
| #108 / f9e52a2 | Diagnóstico de unidad/ruta/permiso/E/S | Versión/fuentes cargadas; no desconectar discos o cambiar settings para forzar fallos |
| #109 / 45b8609 | Idioma declarado de subtítulos | Identidad coherente y capability subtitle_language; contrato de nueva instancia, sin repetir muestra portuguesa |
| #110 / entrega actual | BgRemove0.2.0 local explícito | Metadata de herramienta y campos requeridos; sin ejecutar segmentación, descargar pesos o aprobar licencias por el check |

Cuando se active el lote, comprobar primero trabajos activos e identificar
exactamente el proceso propietario de4750. Un solo reinicio controlado de Studio
desde C:/OPENMONTAGE-IA con su `.venv`; conservar proyectos/configuraciones y no
detener ComfyUI/Ollama/otras aplicaciones. No iniciar jobs al arrancar.

Después: salud/identidad/capacidades y metadata de herramientas. Comparar fuentes
publicadas y advertir si sigue backend anterior, sin reinicios automáticos.
La identidad #105 tiene alcance limitado; no atesta por sí sola BgRemove o
reference_analysis: comprobar también su versión/fuentes/importación residente.
No tomar solo la presencia de archivos nuevos en disco como activación probada.

Si falta un paquete/artefacto/revisión de licencia para BgRemove, ese estado
permanece explícito: no instala/descarga/procesa contenido en esta comprobación.
No se repiten ASR, exportación, escucha o pruebas portuguesas aceptadas. #107
continúa abierto con la validación española pendiente.
