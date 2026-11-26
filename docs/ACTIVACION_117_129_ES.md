# Activación única #117/#129 — resultados 26-11-2026

## Estado actual: activado y comprobado en4750

Tras el reinicio manual confirmado por el usuario, PID130700 carga identidad
residente=disco `5876fee6a176112ac9f4c20192d34ee16b692d6d1a999d53a5c5bb54f63e4bcf`,
`restart_required=false`, API protocolo1 y `subtitle_from_words` presente.
UI `50f751ebab4ede241ed5d9228d2356132c2b61dcceef6719e2f3315cb849e169`.

Validación en Chrome headless contra servidor real y proyecto QA separado:
borrador portugués19cues/106ocurrencias de116palabras guardadas, revisión de todos
los textos/tiempos con negaciones conservadas. Aplicar→revisión1; deshacer→2
recupera exactamente EDL previo/24cues; rehacer→3 restaura19; guardar→4 y
reabrir→4 conservan exactamente EDL/procedencia. Los cuatro POST se limitaron a
esa copia. Texto SRT portugués y19cues visibles en timeline, captura inspeccionada.
No nueva transcripción, traducción, síntesis, render, reproducción/escucha AV ni piloto.
El visor sin render se presenta explícitamente así; no acredita resultado AV final.

Selector Blender/API contrato1 habilitado:4.5.15 marcado como seleccionado,
5.3.0 disponible. Se eligió5.3 únicamente en el desplegable, se comprobó botón
habilitado y se volvió a4.5 sin guardar preferencia global ni abrir Blender.
Se reutiliza prueba persistente aislada anterior; no se repitió. Captura del
selector visible inspeccionada. Proyecto original, settings, applications y
blender_profiles conservaron exactamente sus SHA256.

El guion inicial completó todas las operaciones de subtítulos, pero agotó su
espera de selector al omitir «Ver aplicaciones integrables». Se terminó solo
esa parte con el control de carga correcto y cero POST; no fue fallo de Studio
ni se repitieron ediciones. Cero errores JavaScript observados. Dos capturas y
el informe completo permanecen locales; se publica únicamente
[evidencia numérica](ACTIVACION_117_129_RESULTADOS.json), sin medios/transcripción.

La comprobación cubre el ciclo manual pedido y activación del selector; no
certifica las28skills, calidad artística, guardado global5.3 en esta sesión,
exportación AV de nuevos cues ni escucha. #107 español, #112 sin recibo elegible
y acciones ocultas #113 conservan sus pendientes. Agente:0reinicios, costo$0,
sin instalar ni tocar ComfyUI; PR#2 borrador.

## Historial: preparación anterior al reinicio

Estado: **preparada, pendiente del reinicio manual**. No declarar panel/API
activados por la presencia del código. Salud de4750 responde, pero PID123920
mantiene identidad residente `7e9611ee0cbccc15d321f87f71027990e07c68f44d46f170cea48392910085c9`,
anterior al disco `5876fee6a176112ac9f4c20192d34ee16b692d6d1a999d53a5c5bb54f63e4bcf`;
`restart_required=true` y capacidad `subtitle_from_words` ausente.

## Comprobación previa real,01:12UTC

Cola paused, lista vacía, worker_active=false y local_task_active=false.
Cuatro registros persistentes de render/preescucha revisados sin estados activos.
La inspección de cola declara storage/model-status, no inferencia nueva ni
certificación de todos los procesos externos. Se identificó el cwd por lectura
del proceso: `C:\OPENMONTAGE-IA\`; proceso servidor Python311, comando
`-B -m backlot serve --port 4750`. No se detuvo ni se lanzó otro servidor.
Revalidar trabajos justo antes de la futura parada si ha transcurrido tiempo.

La activación se reservó manual en el plan vigente; única acción pendiente:
Ctrl+C en su consola, esperar que termine y arrancar desde C:\OPENMONTAGE-IA:

```powershell
.\.venv\Scripts\python.exe -B -m backlot serve --port 4750
```

Si Ctrl+C no termina, informar ese estado; no lanzar otro proceso sobre el puerto
ocupado ni reutilizar la autorización para matar otros servicios. No ComfyUI.

## Copia y prueba preparada

`projects/edit-qa129-pt-activation`: copia separada del proyecto portugués
`edit-qa107-pt-5f4e1409`, revisión inicial0,24cues previos,116palabras guardadas.
Se reutilizó el vídeo existente mediante una copia de prueba20MB conservando
sus metadatos; no hubo ASR/síntesis/render/piloto ni descarga de medios/modelos.
El diario original conservó SHA256:
`30085c28db90f096ec36e0615f35106f2a698c41a23bd62b3c85926d64cd62ca`.

Prelectura local (aún no API/panel activado): borrador listo,19cues que conservan
106ocurrencias dentro del montaje22.72s, sin palabras cortadas/cero excluidas.
Las otras10palabras del ASR25s están fuera de la selección, no se reconstruyen.
Las19agrupaciones son mecánicas; conservar texto portugués, incluyendo negaciones,
y revisar en el panel antes de confirmar. No se valida español ni escucha por ello.

Tras el reinicio, una única comprobación disponible:

1. Salud, identidad residente/disco/UI coherentes y capacidad `subtitle_from_words`.
2. En la copia, preparar/revisar19cues, marcar revisión y reemplazo explícitos;
   aplicar. Deshacer recupera exactamente EDL previo/24cues; rehacer restaura19;
   guardar/reabrir conserva contenido y procedencia. Solo cuatro POST de edición,
   sin ASR/render/síntesis. Captura de panel y respuestas reales conservadas localmente.
3. GET de perfiles contrato1 y selector habilitado con4.5 seleccionado. Seleccionar
   5.3 únicamente en el control, comprobar disponibilidad y volver a4.5 sin guardar
   cambio global ni abrir Blender. Reutilizar prueba persistente aislada ya aprobada.
4. Verificar hashes de proyecto original, settings, aplicaciones y perfiles
   sin cambios; no repetir piloto ni otras baterías aprobadas.

El guion local `.runtime/qa/activation117_129_live.cjs` limita escrituras al
proyecto QA y sus cuatro operaciones; rechaza cualquier otro POST. **No ejecutado
contra4750 en esta preparación.** Las pruebas aisladas aprobadas de #129 permanecen
como evidencia previa, sin contarlas como una nueva validación local.

#112 sin recibo elegible y acciones ocultas #113 pendientes; selector/#129
pendientes de activar y probar.4.5 predeterminado, PR#2 borrador y costo$0.
Ruido/borde del suelo del piloto quedan como acabado, sin regenerarlo.
