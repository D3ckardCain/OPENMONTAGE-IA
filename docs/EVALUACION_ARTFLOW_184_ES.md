# EvaluaciÃ³n de Artflow #184

Fecha de consulta: 2026-11-27. EvaluaciÃ³n documental; no se creÃ³ una cuenta, no se subieron imÃ¡genes, no se compraron crÃ©ditos y no se generÃ³ contenido.

## DecisiÃ³n

No adoptar Artflow.ai como motor de OPENMONTAGE. Es un servicio alojado de pago/crÃ©ditos; sus Actor dependen de subir referencias y mantener un actor en la plataforma. No ofrece la operaciÃ³n offline ni el costo $0 requeridos. Tampoco copiar el homÃ³nimo `ShayLiu/artflow`: aunque su README declara MIT, la app depende de APIs de Zhipu con paquete de recursos pagado y de `tldraw` cuyo SDK de producciÃ³n requiere licencia. No aporta una ruta local autorizada sin resolver esos costos y tÃ©rminos.

Reutilizar la lista de requisitos ya expresada en **#158** (biblioteca local de avatares, ID/versiones/referencias/procedencia, editor y agente compartidos) y la separaciÃ³n por cuenta de **#168**. No crear otro backlog ni confundir un perfil guardado con generaciÃ³n persistente, rig, animaciÃ³n facial o lipsync.

## Fuentes y condiciones actuales

| Fuente fijada | ObservaciÃ³n verificable | Impacto para OPENMONTAGE |
|---|---|---|
| [Artflow.ai, pÃ¡gina de producto/pricing](https://app.artflow.ai/products), consulta 2026-11-27; documentaciÃ³n de actores y precios dinÃ¡micos, sin nÃºmero de release pÃºblico | Actor se entrena con 10â€“20 fotos y el proceso anunciado tarda 10â€“30 minutos. Artflow anuncia plan de entrada pagado desde US$7.50/mes con facturaciÃ³n anual (US$6.25/mes equivalente), crÃ©ditos por mes y cargo para actores adicionales. El nivel Basic limita contenido a uso personal; Creator permite comercial con atribuciÃ³n; Pro/Ultra indican permiso comercial sin atribuciÃ³n. Los tÃ©rminos prevalecen sobre el resumen de marketing. | No satisface dependencia $0. Los actores, crÃ©ditos y derechos dependen de suscripciÃ³n activa; no descargar ni integrar el servicio en el flujo local.
| [TÃ©rminos oficiales de Artflow](https://app.artflow.ai/about), vigentes desde 2026-08-28 | El contenido generado estÃ¡ sujeto al plan y a restricciones sobre likeness; los permisos no transfieren derechos de autor. TÃ©rminos requieren que el usuario tenga derechos/consentimiento para cargar likeness. Exigen marcar claramente contenido fotorrealista sintÃ©tico y prohÃ­ben retirar marcas/metadata de origen. | No cargar fotos reales de usuarios ni reutilizar likeness sin autorizaciÃ³n explÃ­cita. Una futura integraciÃ³n necesitarÃ­a mostrar plan/derechos/procedencia y disclosure; no se justifica bajo esta solicitud.
| [PolÃ­tica de privacidad oficial](https://app.artflow.ai/privacy-policy), consulta 2026-11-27 | Los archivos cargados (incluyendo fotos/audio/video) se usan para el servicio Actor y para entrenar el modelo personalizado. Los tÃ©rminos afirman conservar material mientras la cuenta y el Actor/contenido asociado existan; permiten procesamiento por proveedores del servicio. | El usuario pidiÃ³ mantener recursos y configuraciones locales y no autorizÃ³ subir medios. Excluir la ruta remota.
| [HomÃ³nimo `ShayLiu/artflow` @ `2a00ac4f72936c8f1f03d1eb77d7b32f634bc724`](https://github.com/ShayLiu/artflow/tree/2a00ac4f72936c8f1f03d1eb77d7b32f634bc724), `package.json` v0.1.0 | Es un lienzo Next.js/tldraw con CogView-4 y GLM-4-Flash vÃ­a ZhipuAI; README pide API key y paquete de recursos (~Â¥0.1/imagen en el README). Declara MIT, pero el Ã¡rbol de esa revisiÃ³n no incluye archivo raÃ­z `LICENSE`. | No es Artflow.ai ni un motor local/offline; las llamadas de IA cuestan y quedan fuera del objetivo. No reutilizar cÃ³digo sin aclarar concesiÃ³n MIT y avisos/dependencias.
| [Licencia oficial de tldraw SDK](https://github.com/tldraw/tldraw/blob/main/apps/docs/content/community/license.mdx), lectura 2026-11-27 | Los paquetes SDK publicados requieren licencia vÃ¡lida de prueba, hobby o comercial para uso de producciÃ³n; el SDK no se vuelve MIT porque el proyecto consumidor declare MIT. | El homÃ³nimo agrega una licencia/posible costo que impide usarlo como base $0 de producciÃ³n sin revisar elegibilidad. No instalarlo.

Los precios/planes de Artflow pueden cambiar y estÃ¡n sujetos a regiÃ³n, impuestos, facturaciÃ³n y tÃ©rminos de cuenta. No se inicia trial ni se usa el plan gratuito para eludir la condiciÃ³n de no usar servicios externos obligatorios.

## ComparaciÃ³n con lo existente

- En el Ã¡rbol remoto actual existen rutas de avatar/hablante de terceros (`tools/avatar/heygen_avatar.py`, `kling_avatar.py`, `kling_lip_sync.py`, `lip_sync.py`, `talking_head.py`) y guÃ­as de uso, pero no equivalen a una biblioteca local de perfiles persistentes offline.
- #158 ya exige ID estable, miniatura, nombres/renombrado, referencias autorizadas y versionadas, asignaciÃ³n explÃ­cita a proyectos, revisiÃ³n/undo y las mismas operaciones en Studio/agente. Acepta crear o importar recursos solo segÃºn los motores locales disponibles; mantiene biblioteca y generaciÃ³n como capacidades separadas.
- #168 requiere `account_id`, proyectos/recientes/memorias aislados y biblioteca global explÃ­cita. Los perfiles visuales por cuenta deben heredar esa separaciÃ³n; los modelos/paquetes tÃ©cnicos comunes no se duplican por cuenta.
- Las capacidades HeyGen/Kling presentes son rutas de proveedor, no disponibilidad local ni permiso automÃ¡tico para usar fotos. No se les atribuye operaciÃ³n offline ni $0.

## Tareas concretas sin duplicar #158/#168

1. Al implementar #158, persistir `avatar_id`, versiÃ³n, cuenta propietaria, referencias con procedencia/hash y derechos declarados; el proyecto fija una versiÃ³n, no el nombre mutable.
2. Rechazar selecciÃ³n cruzada de perfiles por cuenta salvo acciÃ³n explÃ­cita de compartir; un cambio de voz opcional nunca muta el perfil visual.
3. Mostrar separado: biblioteca/importaciÃ³n manual lista; generaciÃ³n local no disponible hasta que un perfil de soporte confirme modelo/licencia/VRAM; proveedor cloud restringido y nunca auto-elegido.
4. Aceptar #158 solo despuÃ©s de reabrir, renombrar sin romper IDs, seleccionar manualmente y vÃ­a agente en copia de prueba, probar dos cuentas y demostrar que cambiar una versiÃ³n no altera proyectos fijados a otra. La generaciÃ³n/lipsync requiere su propia prueba local y autorizaciÃ³n de recursos.

## ValidaciÃ³n documental y lÃ­mites

- Revisados pÃ¡gina del producto, precios, tÃ©rminos, privacidad y release notes de Artflow.ai; README/manifest/Ã¡rbol de archivos del homÃ³nimo; licencia oficial de tldraw; issues abiertos #158 y #168 y Ã¡rbol de adaptadores del repositorio.
- ComprobaciÃ³n focalizada: identidad de ambos Artflow, fuentes oficiales, costo, uso de datos, licencia, duplicaciÃ³n y enlaces a los issues existentes; sin cambiar cÃ³digo del producto.
- No se comprobÃ³ una cuenta ni accesibilidad desde MÃ©xico, no se verificÃ³ una cotizaciÃ³n/checkout ni validez jurÃ­dica de tÃ©rminos; no hubo consulta de licencia legal. Los precios pueden cambiar.
- No instalaciÃ³n, descarga, entrenamiento, carga de referencia, generaciÃ³n, ni inferencia local/remota.

## AceptaciÃ³n

- [x] Servicio y homÃ³nimo diferenciados.
- [x] Licencias, costo, privacidad, consentimiento y condiciones de uso documentados.
- [x] Solapamiento consolidado en #158/#168, sin tarea duplicada.
- [x] Alcance sin instalaciÃ³n, descarga ni contenido generado.
- [ ] Prueba de persistencia/aislamiento: pertenece a la implementaciÃ³n pendiente de #158/#168, no a esta evaluaciÃ³n.

