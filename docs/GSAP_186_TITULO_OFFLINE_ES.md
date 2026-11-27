# GSAP Core/Timeline: título técnico local

**Actualización:** el seguimiento posterior acredita un MP43s/72fotogramas con reproducción real. El bloqueo intermitente original **no tiene causa raíz confirmada**; no se declara corregido por el éxito de una ejecución con trazas. Véase `GSAP_186_DIAGNOSTICO_20261126.json` y el apartado final. El registro inicial se conserva abajo.

Guías oficiales fijadas a `greensock/gsap-skills@aed9cfd3277740755f6bfc1155c7aa645403b760`. Los archivos locales Core y Timeline coinciden normalizando CRLF a LF; blobs y SHA256 pequeños en `GSAP_SKILLS_REVISION_20261126.json`. Guías MIT con aviso conservado en `licenses/GSAP-SKILLS-MIT.txt`. El runtime GSAP3.14.2 tiene su licencia estándar independiente, **no MIT**. No se incorporan todos los plugins por usar dos guías.

Proyecto separado `projects/qa186-gsap-offline`, pipeline `hyperframes-offline-pilot`, herramienta existente ampliada con alcance explícito. Título propio,3s,640×360,24fps, sin audio, fuentes del sistema, GSAP preparado local. Timeline pausada y síncrona, estados `fromTo` explícitos, etiquetas y `immediateRender:false` en la salida. Usuario autorizó esta prueba técnica completa; la decisión y checkpoints se guardaron antes de los recursos.

Se usa el perfil persistente seleccionado, revisión1: paquete HyperFrames0.9.96, Node22.23.5, Chrome y GSAP existentes. Sin variables heredadas ni modificación de configuración. El hash de GSAP se reutilizó contra la identidad vigente del recibo anterior; no se repitió doctor, piloto132, cancelación ni hashes de modelos. Los paquetes/binarios no se publican.

## Resultado acreditado

-2 pruebas nuevas focalizadas: construcción con perfil/identidad, conservación del motor, rechazo de sobrescritura y contrato de template local/pausado.
-Chrome real servido por loopback4780: saltos1→0,25→2,75→1s y recarga→1s. PNG exactamente iguales al volver a1s: `0443c66867a8eb92267097cd41c12fc69c4f28db37e82c4ec13fd7ae7188aa1a`. Captura inspeccionada: título legible y completo. Sin errores JS ni peticiones externas de la escena. El primer script de QA devolvía una timeline entonces tratada como promesa; se corrigió retornando booleano/void, sin cambiar la animación.
-CLI `check` aprobado. Una única exportación nueva llegó a captura y quedó en0/72 fotogramas; el transporte propio la detuvo a180s, sin ampliar timeout ni reintentar. **Exportación offline de este título pendiente**, no se acredita por el render132 anterior.
-Guardia Node rechazó un intento del CLI a `fonts.googleapis.com`; la escena usa Arial y no lo solicitó. Offline significa ejecución bajo bloqueo aplicado, no ausencia de todo intento de red del CLI ni firewall del sistema. La identidad de esa petición y la causa del bloqueo de captura aún no están demostradas.

Recibos privados: `artifacts/pilot-build.json`, `seek.json`, `check.log`, `pilot-render.json`, `render.log`, `network.jsonl`. Se conservan el fallo y sus procesos propios; Studio4750 y descargas no se tocaron. No se promovió la salida incompleta como MP4 válido. No se cambia de motor para simular una exportación HyperFrames.

Pendiente: identificar el punto de espera en captura antes de repetir esta exportación. Las pruebas deterministas del HTML no equivalen a exportación aprobada. #186/#132 permanecen abiertos en sus criterios pendientes.

## Seguimiento solicitado: un fotograma y exportación completa

Pipeline/proyecto/título/perfil anteriores conservados. Fases explícitas nuevas del mismo `hyperframes_offline_pilot`1.2.0: `frame186` captura1s con `--start1 --end1.041666…`; `zero186` captura el límite0s. Ambos MP4 contienen exactamente1fotograma,640×360/24fps,0,041667s. No se repitieron las36 pruebas anteriores ni seek determinista.

Experimentos negativos conservados: desactivar streaming dejó la ruta completa en0/72 también en captura a disco; se retiró ese ajuste y **no se publica como solución**. El intento propio se detuvo tras identificar PID58412 y su árbol, a155,937s sin avance. Un tramo completo0–3s progresó por7chunks y agotó un presupuesto diagnóstico reducido90s: no demuestra que la ruta por tramos resuelva el bloqueo. No se prolonga ni reintenta indefinidamente.

Después se habilitó **solo en ese proceso QA** `scripts/hyperframes_capture_trace.cjs`: hook Node22 sobre las12asignaciones de `session.captureStep` del paquete ya instalado. Solo añade mensajes, sin modificar sus archivos, título, motores ni configuración persistente. La ruta completa normal con streaming completó72/72 en10,594s de proceso, salida `projects/qa186-gsap-offline/renders/trace186.mp4`,59221bytes. FFprobe decodificó72fotogramas,24fps/3s. Las trazas recorren seek→CSS→handlers→LUT→captura; el fallo previo no estaba instrumentado, de modo que **no sabemos en cuál de esos awaits se detenía**. Una carrera o efecto temporal de las trazas es hipótesis, no diagnóstico probado. No se introduce un sleep ni se fuerza esta instrumentación como arreglo del motor.

Chrome real reprodujo hasta el final:72fotogramas,0descartes,71callbacks de presentación. El título es intencionadamente mudo. Fotograma1s extraído con FFmpeg e inspeccionado: título legible, barra y colores presentes. El primer servidor QA `python -m http.server` devolvía intervalo buscable0–0; la búsqueda del navegador volvía a0 y daba un fotograma oscuro. Con servidor QA `FileResponse`, intervalo0–3, tiempo real1s y9942píxeles claros; canvas inspeccionado coincide visualmente con el título. Es una limitación del servidor **de QA**, no evidencia de fallo en Studio. No se repitió el render para resolverla.

Guardia Node bloqueó1petición del CLI a Google Fonts; recursos de la escena siguen locales. Sin instalaciones, paquetes nuevos, modelos, inferencias, CI ni consultas4750.3pruebas nuevas focalizadas de guardas/recibos/conteo pasan; el error de timeout del transporte ahora informa el presupuesto real, no180s fijo cuando se usaron45/90. Fases tienen recibo y no sobrescriben/reintentan salidas existentes.

Resultado: exportación y reproducción de **esta ejecución** acreditadas; reproducibilidad sin trazas/causa del bloqueo intermitente pendientes. #186 sigue abierto por ese límite. No se modifica el arranque normal ni se instala un supuesto workaround. Recibos privados `artifacts/{frame186,zero186,finish186,span186,trace186,playback186,browser-seek-range186}.json`; logs separados por fase conservados.
