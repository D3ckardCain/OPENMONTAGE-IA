# Activación agrupada pendiente de Studio

Actualización: el lote #111 se verificó directamente en4750/PID125660,
resident=disk=e68adc7a05b647f5d49b31b293b2d093a2c024d06ce5ee51b5e7d2c72fecc647,
restart_required=false; subtitle_language presente,109 hablantes VCTK y
preescucha real2.147846s reproducida. El agente no reinició el servidor.
La tabla conserva el plan de ese lote; la ampliación posterior **#112/E05 de
recuperación Piper** está preparada pero aún no activada en4750. Su siguiente
activación será manual y agrupada con futuros cambios, sin repetir pruebas
españolas. [Contrato/pruebas/límites](PIPER_RECUPERACION_ES.md).

Petición del usuario: agrupar45b8609 con los demás cambios, evitando reinicios
repetidos. Esta entrega **no reinicia Studio ni activa herramientas**. La muestra
portuguesa de #107 está validada por el usuario; la española sigue pendiente.

| Seguimiento | Cambio preparado | Comprobación nueva tras una sola activación |
|---|---|---|
| #108 / f9e52a2 | Diagnóstico de unidad/ruta/permiso/E/S | Versión/fuentes cargadas; no desconectar discos o cambiar settings para forzar fallos |
| #109 / 45b8609 | Idioma declarado de subtítulos | Identidad coherente y capability subtitle_language; contrato de nueva instancia, sin repetir muestra portuguesa |
| #110 / entrega actual | BgRemove0.2.0 local explícito | Metadata de herramienta y campos requeridos; sin ejecutar segmentación, descargar pesos o aprobar licencias por el check |
| #111 / Piper + VCTK reentrenado | Catálogo, hablantes y preescucha local en Audio; conjunto VCTK fijado a 5ec43b186ef915a195d3ddbcfd9916e76c503c3f | Tras activación, comprobar API/panel de la instancia 4750 y versión Piper aislada; reutilizar pruebas españolas ya aprobadas, no repetirlas |

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

## Único reinicio manual, después de resolver VCTK

No ejecutar durante la sustitución. La última instancia comprobada es PID89172,
salud correcta y `restart_required=true`; cola pausada/vacía sin worker activo.
Antes de hacerlo, volver a comprobar que no hayan empezado trabajos.
En la consola de Studio: Ctrl+C y esperar salida. Si no termina, cerrar solamente
esa consola. Después, desde PowerShell:

```powershell
Set-Location -LiteralPath C:\OPENMONTAGE-IA
& .\.venv\Scripts\python.exe -B -m backlot serve --port 4750
```

Recargar el panel y exigir identidad residente/disco coherente, no solo salud.
No repetir ASR, exportación portuguesa ni pruebas de las cuatro combinaciones
españolas. La escucha humana de Piper sigue pendiente. BgRemove mantiene su
validación real de proveedor/peso/licencia como pendiente independiente; el
reinicio no acredita segmentación ni calidad. No se modifica ComfyUI ni settings.
