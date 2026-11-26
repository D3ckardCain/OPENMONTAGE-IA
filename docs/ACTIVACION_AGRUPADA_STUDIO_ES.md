# Activación agrupada de Studio

## Estado vigente: lote #117/#129 activado

[Resultados reales de la activación única](ACTIVACION_117_129_ES.md): PID130700,
identidad residente=disco y restart_required=false. #129 revisión/aplicación,
undo/redo/save/reopen pasaron en copia portuguesa con106ocurrencias/19cues;
selector Blender habilitado,4.5 predeterminado conservado. No nuevo reinicio
necesario por ese lote. Sin repetir ASR/síntesis/piloto ni afirmar exportación AV.
#112 sin recibo elegible y acciones ocultas #113 siguen pendientes.

## Historial del lote #117/#129 antes de activar

[Preparación única comprobada y prueba portuguesa lista](ACTIVACION_117_129_ES.md):
cola vacía/sin trabajos activos a01:12UTC, PID123920 todavía antiguo. Copia QA
separada lista; **reinicio manual y validación del lote aún pendientes**.

#112–#115 ya se activaron tras el reinicio manual; consultar
[resultados de esa activación](ACTIVACION_112_115_RESULTADOS_ES.md).
Siguen pendientes únicamente la recuperación con recibo elegible de #112 y
las acciones ocultas del agente de #113; no repetir síntesis ni pruebas aprobadas.

El próximo lote incorpora el selector/API de perfiles Blender y el descubrimiento
de `blender_skills_pilot`, junto con el borrador compartido de subtítulos #129.
**No reiniciar ahora.**
4.5.15 continúa como predeterminado; el piloto usó 5.3 expresamente y de forma
aislada mediante el agente, no mediante el servidor residente.

Antes de la futura activación manual única: comprobar que no haya trabajos
activos y confirmar la copia de C:\OPENMONTAGE-IA y su Python .venv.
Después: identidad compatible, contrato GET de perfiles, selector disponible,
4.5 todavía seleccionado y nueva herramienta descubierta. No repetir el render
ni las comprobaciones de provisión aprobadas. No cambiar perfiles automáticamente.
[Piloto y límites](BLENDER_117_PILOTO_ES.md).

Para #129, comprobar tras ese mismo reinicio la capacidad `subtitle_from_words`,
GET `subtitle-draft` y el control de revisión/aplicación en una copia de prueba.
No aplicar sobre originales ni repetir ASR/síntesis/renders. Usar palabras ya
guardadas; si su cobertura/límites no permiten un borrador, registrar el bloqueo
sin reconstruir palabras. [Contrato y pruebas](SUBTITULOS_DESDE_PALABRAS_ES.md).
Ruido y borde del suelo del piloto quedan documentados como mejoras de acabado;
no son una nueva tarea de render ni motivo para repetirlo.

## Historial de preparación anterior (no es el estado vigente)

Actualización: el lote #111 se verificó directamente en4750/PID125660,
resident=disk=e68adc7a05b647f5d49b31b293b2d093a2c024d06ce5ee51b5e7d2c72fecc647,
restart_required=false; subtitle_language presente,109 hablantes VCTK y
preescucha real2.147846s reproducida. El agente no reinició el servidor.
La tabla conserva el plan de ese lote; las ampliaciones posteriores **#112/E05 de
recuperación Piper**, **#113/E02 de contraste/foco** y **#114/E02 de errores HTTP**
están preparadas pero aún no validadas en4750. Su siguiente
activación será manual y agrupada con futuros cambios, sin repetir pruebas
españolas. [Contrato/pruebas/límites #112](PIPER_RECUPERACION_ES.md) y
[contraste/foco #113](STUDIO_CONTRASTE_FOCO_ES.md).

## Próximo lote pendiente: #112 + #113 + #114 + #115 y próximas entregas

[Comprobación conjunta breve preparada](COMPROBACION_CONJUNTA_112_114_ES.md):
criterios pendientes revisados, una sola activación, recuperación por recibo
existente, contraste/foco y un400 interceptado sin mutaciones reales. Si no hay
recibo elegible de #112, ese paso queda explícitamente pendiente; no repetir
síntesis ni fabricar evidencia. No se ejecuta todavía.

No ejecutar todavía. Un único reinicio manual de4750 cargará la recuperación de
Piper preparada en #112; recargar después aplicará los tokens/estilos de #113
y los errores/formularios de #114 ([contrato y pruebas](STUDIO_ERRORES_HTTP_ES.md)).
Antes, comprobar trabajos activos. Después, verificar identidad coherente y el
contrato nuevo, sin repetir síntesis ni comprobaciones ya aprobadas de #111.
Mantener la valoración natural/robótica aplazada. El agente no reinicia Studio.

#115 añade capability/GET de inspección de palabras en reloj del montaje y su
control de lectura ([manual](PALABRAS_RELOJ_MONTAJE_ES.md)). Se incorpora al mismo
reinicio, no requiere otro. Su comprobación posterior no llama ASR ni exporta;
la comprobación breve de #112–#114 conserva su alcance y resultados previos.

Para #114, validar mensajes/foco sin enviar creaciones o settings reales como
mero diagnóstico; las pruebas offline ya cubren los fallos sintéticos. No repetir
#111/#112/#113 aprobados ni lanzar modelos para probar una alerta de la interfaz.

## Historial del lote anterior

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
