# EvaluaciÃ³n de Cal.diy #181

Fecha: 2026-11-27. Repositorio/fuente fijados a [`calcom/cal.diy@ae027bb70e694e2d2c44569f398d6cbcee0389b1`](https://github.com/calcom/cal.diy/tree/ae027bb70e694e2d2c44569f398d6cbcee0389b1). No se instalÃ³ ni ejecutÃ³.

## DecisiÃ³n

No integrar Cal.diy ni reemplazar las colas/calendario editorial previstos en #169. Cal.diy resuelve reserva de citas y disponibilidad para reuniones; no publica videos ni sincroniza envÃ­os con redes. Reutilizar como referencia UX solo selector de intervalos, zona horaria, disponibilidad y conflictos si OPENMONTAGE necesita reservar entrevistas/grabaciones. #169 ya define el calendario editorial, publicaciones vencidas, recibos, fallos por destino y reconciliaciÃ³n; #168 ya define aislamiento por cuenta. No abrir otro issue ni agregar scheduler/DB.

## Fuentes y compatibilidad

| Tema | Fuente oficial fijada | ConclusiÃ³n |
|---|---|---|
| CÃ³digo/licencia | [README](https://github.com/calcom/cal.diy/blob/ae027bb70e694e2d2c44569f398d6cbcee0389b1/README.md) y [LICENSE](https://github.com/calcom/cal.diy/blob/ae027bb70e694e2d2c44569f398d6cbcee0389b1/LICENSE) en commit anterior. README declara Cal.diy MIT, sin licencia de Cal.com requerida, con mÃ³dulos Enterprise/Teams/Organizations/Insights/Workflows/SSO eliminados. | MIT permite uso segÃºn sus tÃ©rminos, pero el README **recomienda estrictamente solo uso personal/no producciÃ³n**. Es recomendaciÃ³n operativa explÃ­cita; no la presento como clÃ¡usula NC inventada de la licencia MIT. Respetar avisos y licencias de dependencias.
| AplicaciÃ³n/arquitectura | README y `package.json`: monorepo `calcom-monorepo` privado, Next/tRPC/React/Prisma/PostgreSQL, Daily.co, Yarn 4.12.0. Requiere PostgreSQL >=13 segÃºn guÃ­a. Se puede alojar localmente, pero el flujo completo exige servicios/configuraciÃ³n administrativa. | Coste de licencia $0 no significa preparaciÃ³n/operaciÃ³n sin mantenimiento. No introducir el monorepo completo por un calendario editorial sencillo.
| Requisitos de Node | README dice Node >=18. El paquete oficial `apps/web` en la revisiÃ³n tiene Next.js 16.4.3; su [`package.json`](https://github.com/vercel/next.js/blob/v16.4.3/packages/next/package.json) declara Node >=20.9.0. El root fija Yarn 4.12.0. | La versiÃ³n mÃ­nima `>=18` del README estÃ¡ desfasada para el paquete web actual. Antes de cualquier preparaciÃ³n habrÃ­a que seguir el engine de la dependencia/versiones fijadas, no solo el texto de README. No se ejecutÃ³ en Windows.
| Servicios/conectores | README describe SMTP/correos, videollamada Daily y calendarios/integraciones opcionales con credenciales externas; el proyecto se documenta como autohospedado, sin versiÃ³n hosted/managed. | Calendario local bÃ¡sico puede servir sin publicaciÃ³n social; sincronizaciÃ³n externa, correo y reuniones necesitan conectividad/credenciales y pueden tener condiciones/costos propios. No prometer modo completamente offline ni todas las integraciones por $0.

## Diferencia de dominio y comparaciÃ³n

- **Cal.diy:** participantes reservan citas; disponibilidad del anfitriÃ³n, zonas horarias, pÃ¡gina de reservas, invitaciones y proveedores de calendario/videollamada.
- **#169:** el agente programa una salida audiovisual final a uno o mÃ¡s destinos sociales; requiere cuenta propietaria, versiÃ³n exacta, archivo final, consentimiento, estado de publicaciÃ³n remoto, recibo y reconciliaciÃ³n anti-duplicados. Booking no implementa estos contratos ni publica a TikTok/YouTube/Meta.
- **#168:** el workspace local por cuenta separa proyectos y memoria, con cola/biblioteca global deliberada. No se debe usar un nombre de perfil del scheduler para decidir propietario ni cruzar secretos.
- **DecisiÃ³n de implementaciÃ³n:** no usar Cal.diy como scheduler oculto; cualquier futura reserva de invitados debe ser una funciÃ³n opcional aparte, con disponibilidad IANA/UTC/DST probada, propietario estable por cuenta y almacenamiento local controlado. No requiere adoptar su stack.

## ReutilizaciÃ³n mÃ­nima y criterios de aceptaciÃ³n

No se justifica un cambio de producto en esta evaluaciÃ³n. Si aparece la necesidad de booking, tomar Ãºnicamente estas pruebas UX/datos:

1. Resolver zona IANA y convertir UTC sin cambiar la hora civil; cubrir transiciÃ³n DST que crea hora inexistente y hora ambigua.
2. Guardar dueÃ±o inmutable por cuenta/canal y conservar el espacio de trabajo al cambiar de cuenta; verificar con #168.
3. Mostrar conflictos y disponibilidad como propuesta; no reservar ni publicar por inferencia del agente.
4. Guardar/reabrir configuraciÃ³n local; exportar invitaciÃ³n o crear cita solo cuando se seleccione un conector y estÃ© listo. Su disponibilidad externa requiere red.
5. Mantener separadas reservas, cola de producciÃ³n y cola de publicaciÃ³n de #169.

La Ãºltima marca de actividad de Cal.diy en la revisiÃ³n es 2026-11-13; no se atribuye un release/tag versionado. No se descargaron sus dependencias ni se inspeccionaron instaladores. Estado de dependencia Windows sin confirmar.

## VerificaciÃ³n y lÃ­mites

- Revisados issue #181, README, licencia raÃ­z, package manifest, configuraciÃ³n Yarn, `apps/web/package.json`, `packages/prisma/package.json`, requisitos oficiales del paquete Next.js 16.4.3 y requerimientos actuales de #168/#169.
- VerificaciÃ³n documental focalizada: identidad de repositorio, licencia vs recomendaciÃ³n no-producciÃ³n, engine real de Node, stack, costo, integraciones, distinciÃ³n booking/publicaciÃ³n y duplicaciÃ³n.
- Sin instalaciÃ³n, base de datos, SMTP, conexiÃ³n de calendario, pruebas de Windows, consultas a cuentas ni creaciÃ³n/publicaciÃ³n de eventos.
- El engine Node se infiriÃ³ de `next@16.4.3` requerido por el paquete `apps/web`, no de un engine Node raÃ­z declarado por Cal.diy. La elegibilidad comercial o de servicios externos no es una evaluaciÃ³n legal.

## AceptaciÃ³n de la evaluaciÃ³n

- [x] Commit y fuentes oficiales fijados.
- [x] MIT, recomendaciÃ³n upstream personal/no-producciÃ³n y dependencias separadas.
- [x] Node/Postgres y requisitos externos comprobados o limitaciÃ³n identificada.
- [x] Solapamiento con #168/#169 resuelto sin backlog duplicado.
- [x] Sin instalaciÃ³n ni operaciones externas.
- [ ] ValidaciÃ³n de DST/booking: fuera de alcance hasta que exista necesidad concreta.

