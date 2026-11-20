# Cola de producciones locales

La sección **Cola de trabajos** organiza proyectos existentes en orden de llegada. Selecciona un proyecto en Producción y pulsa **Añadir proyecto seleccionado**. Añadirlo solamente guarda el registro; no ejecuta modelos.

**Ejecutar cola local** utiliza el productor existente, de uno en uno. Conserva sus permisos, comprobaciones de recursos y aprobaciones por etapa. No autoriza publicaciones. Si hay otra tarea local activa, no inicia.

Cuando un proyecto queda bloqueado, necesita información o requiere aprobación, la cola se pausa antes del siguiente. Abre el proyecto, resuelve la causa y utiliza **Volver a poner pendiente**. Este botón no aprueba etapas. Si el productor ya terminó, la cola reconoce el resultado y no lo genera otra vez.

**Pausar después del activo** permite que termine el trabajo actual e impide iniciar otro. Para detener la generación actual utiliza el control del productor.

Los registros persisten en `production_queue.json` junto a la configuración. Cerrar la app interrumpe su controlador: al abrirla, los trabajos activos aparecen interrumpidos y requieren revisión y reintento explícitos. Nunca se reinicia una generación automáticamente.

Cada registro conserva la raíz original de proyectos. Para trabajos en otro disco, vuelve a seleccionar esa raíz y reinicia la app. El sistema no interpreta un proyecto del mismo nombre en otro disco como el original. La cola admite hasta 100 registros.

## Validación

Pruebas sintéticas de persistencia, ejecución secuencial, pausa, recuperación, aprobaciones y API. No certifican los modelos, los discos físicos ni la calidad de los videos. Las pruebas con los modelos reales permanecen pendientes.
