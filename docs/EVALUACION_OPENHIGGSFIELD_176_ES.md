# Evaluación de OpenHiggsfield #176

Fecha: 2026-11-27. Revisión documental estática de dos proyectos distintos, fijada a [`thehiggsfieldai/OpenHiggsfield@a9507962df442b72c84f01d27565108b6724cc83`](https://github.com/thehiggsfieldai/OpenHiggsfield/tree/a9507962df442b72c84f01d27565108b6724cc83) y [`wide-trace/open-higgsfield@b16a0efe4d7e2707b56f8ccb02387fd2a9d2eddf`](https://github.com/wide-trace/open-higgsfield/tree/b16a0efe4d7e2707b56f8ccb02387fd2a9d2eddf). No se instalaron, ejecutaron ni copiaron.

## Decisión

No incorporar un segundo editor, catálogo de generación, cuenta o servicio de medios. Reutilizar únicamente patrones funcionales compatibles con el proyecto compartido de #158/#159/#164/#168/#174: borradores por proyecto, storyboard revisable, progreso por escena, selección de opciones que el backend realmente soporte, historial y atribución. Mantener Ollama y los motores locales ya conectados; ningún flujo puede afirmar costo $0 si envía peticiones a proveedores alojados.

La carencia útil es un contrato editorial compacto y agnóstico del proveedor: escenas referenciadas al mismo proyecto/EDL y medios, alternativas A/B/C explícitas, estado pendiente/aprobado/rechazado, revisión de cambios y procedencia por recurso. No implica generación automática, un catálogo de 50 personajes ni un segundo historial. El contrato debe compartir revisiones y permisos entre agente y usuario.

## Fuentes, versiones, licencias y requisitos

| Proyecto y evidencia fijada | Hallazgo | Consecuencia para OPENMONTAGE |
|---|---|---|
| [Story Studio README](https://github.com/thehiggsfieldai/OpenHiggsfield/blob/a9507962df442b72c84f01d27565108b6724cc83/README.md), [LICENSE](https://github.com/thehiggsfieldai/OpenHiggsfield/blob/a9507962df442b72c84f01d27565108b6724cc83/apps/story-studio/LICENSE), [`apps/story-studio/package.json`](https://github.com/thehiggsfieldai/OpenHiggsfield/blob/a9507962df442b72c84f01d27565108b6724cc83/apps/story-studio/package.json) | Código MIT, con avisos de terceros que conservar. Node **24+**, FFmpeg/ffprobe para ensamblar; frontend React **19.2**, Vite **8.3**, TypeScript **6.0** y cliente `@fal-ai/client` **1.10.1**. README anuncia personaje → historia → seis escenas revisables → estimación → render por escena. Requiere configuración de autenticación/correo para despliegue y credenciales propias para fal/Higgsfield. El README declara que no está afiliado a Higgsfield.ai. | MIT no concede derechos sobre nombres, marcas, semejanzas ni arte incluido. No copiar ilustraciones, personajes, marca ni textos de términos. No es operación de generación offline; credenciales autorizan proveedores externos y sus costos/retención dependen de cada uno. La estimación de la interfaz no es factura. Runtime y dependencias duplicarían el stack local. |
| [wide-trace README](https://github.com/wide-trace/open-higgsfield/blob/b16a0efe4d7e2707b56f8ccb02387fd2a9d2eddf/README.md), [`package.json`](https://github.com/wide-trace/open-higgsfield/blob/b16a0efe4d7e2707b56f8ccb02387fd2a9d2eddf/package.json), [árbol fijado](https://api.github.com/repos/wide-trace/open-higgsfield/git/trees/b16a0efe4d7e2707b56f8ccb02387fd2a9d2eddf?recursive=1) | Interfaz Next.js **16** (rango `^16.0.0`), React **19.2**, Zustand **5**, `@vercel/blob` **2.8**; catálogo dinámico de modelos, controles por rol/capacidad, historial IndexedDB y ciclo de solicitud. Subida directa de archivos a Vercel Blob y llamadas autenticadas a una API externa de generación. | El árbol fijado no contiene `LICENSE`/`COPYING`/`NOTICE`; consulta oficial de `LICENSE` devuelve 404. Tratar el código como **sin licencia identificada**: no copiar, adaptar ni distribuirlo hasta que el titular conceda permiso. “Gratis” describe la interfaz, no el costo de la API, almacenamiento ni operación; no funciona offline como generación local. |

## Comparación con lo existente y brechas sin duplicados

- OPENMONTAGE ya tiene edición compartida y EDL en #92/#174; audio, subtítulos y cambios reversibles en #107/#115/#129/#130; puente de composición HyperFrames offline en #132; perfiles/capacidades reales en adaptadores y proyectos/cuentas en #168. No hace falta crear un timeline, galería global, cola de generación ni historial paralelo.
- Reutilizable como requisito de diseño: parámetros expuestos solo cuando estén declarados por la capacidad del motor; progreso/estado por trabajo; seleccionar recurso previo desde biblioteca; revisar cambios por escena y conservar borradores privados.
- No adoptar el envío masivo de escenas ni galerías públicas. Una herramienta local debe fallar claramente si falta un motor/recurso, sin cambiar a API remota o CDN.
- El catálogo de personajes/imágenes del primer proyecto no es un paquete de assets con permiso universal. Registrar procedencia/licencia por archivo aportado por el usuario; prohibido incorporar esos assets a la app o usarlos para ejemplos sin autorización comprobada.

## Tareas concretas y aceptación si se prioriza implementación

1. Extender el contrato del proyecto existente (sin nueva base de datos): `project_revision`, referencias a medios/EDL y rangos temporales, escena, opciones A/B/C, estado de revisión, cambios propuestos, autor y procedencia/licencia. El agente lee y escribe el mismo contrato que la UI.
2. Renderizar solamente controles declarados por el adaptador local seleccionado; solicitudes inválidas/motor ausente producen error visible y no llaman a un proveedor alternativo.
3. En copia sintética offline, guardar/reabrir dos escenas, aceptar/rechazar una opción, deshacer/reaplicar, comprobar aislamiento por cuenta/proyecto y mantener trazabilidad de cada recurso. La copia no altera el montaje original.
4. La prueba de operación offline debe demostrar que no hubo tráfico externo; documentación/UI distingue planificación local de inferencia y render local. Para cualquier capacidad alojada futura, costo, proveedor, datos transmitidos y consentimiento deben aparecer antes de enviar.

## Verificación y límites

- Leídos README, manifest, LICENSE/sub-LICENSE, árbol y fuente oficial fijados de Story Studio; README, manifest y árbol recursivo del segundo proyecto. Verificado que el segundo no tiene archivo de licencia en esa revisión y que la ruta oficial `LICENSE` responde 404.
- Comprobación documental focalizada: commits y versiones fijados, runtime, dependencias, flujos de datos, proveedores y persistencia, licencias de código frente a derechos de assets, compatibilidad $0/offline y solapamientos con issues existentes.
- No se instaló, descargó ni ejecutó ninguno; no hubo llamadas a proveedores, cuentas, cargas, inferencias ni generación de contenido. Esto no certifica rendimiento, seguridad de despliegue ni compatibilidad real con Windows.
- No se implementó el contrato propuesto: queda como tarea futura sujeta a priorización en los issues existentes, no se presenta como una capacidad lista.

## Resultado de la evaluación

- [x] Revisiones upstream fijadas y fuentes consultadas.
- [x] Versiones, licencias, requisitos, costo/offline y límites de assets documentados.
- [x] Solapamientos contrastados y trabajo útil definido sin duplicar editor ni proveedor.
- [x] Pruebas focalizadas de consistencia documental; sin instalaciones ni contenido generado.
- [ ] Implementar contrato editorial: pertenece a los issues de editor/proyecto y requiere una entrega funcional separada.
