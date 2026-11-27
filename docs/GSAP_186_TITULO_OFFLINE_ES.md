# GSAP Core/Timeline: título técnico local

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
