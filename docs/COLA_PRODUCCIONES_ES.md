# Cola de producciones locales

La sección **Cola de trabajos** organiza proyectos existentes en orden de llegada. Selecciona un proyecto en Producción y pulsa **Añadir proyecto seleccionado**. Añadirlo solamente guarda el registro; no ejecuta modelos.

**Ejecutar cola local** utiliza el productor existente, de uno en uno. Antes de activar el controlador revisa todos los registros pendientes: disco original, proyecto disponible, aprobación pendiente, almacenamiento y modelo seleccionado en Ollama cuando se necesita generar. Si alguno falla, muestra la causa y no procesa parcialmente el lote. Conserva las aprobaciones por etapa y no autoriza publicaciones.

Cuando un proyecto queda bloqueado, necesita información o requiere aprobación, la cola se pausa antes del siguiente. Abre el proyecto, resuelve la causa y utiliza **Volver a poner pendiente**. Este botón no aprueba etapas. Si el productor ya terminó, la cola reconoce el resultado sin generar otra vez solo cuando conserva una verificación técnica vigente y completa; una selección deportiva nueva o revisión editorial posterior obliga a revisar el render.

**Pausar después del trabajo activo** permite que termine el trabajo actual e impide iniciar otro. Para detener la generación actual utiliza el control del productor.

Los registros persisten en `production_queue.json` junto a la configuración. Cerrar la app interrumpe su controlador: al abrirla, los trabajos activos aparecen interrumpidos y requieren revisión y reintento explícitos. Nunca se reinicia una generación automáticamente.

Cada registro conserva la raíz original de proyectos. Para trabajos en otro disco, vuelve a seleccionar esa raíz y reinicia la app. El sistema no interpreta un proyecto del mismo nombre en otro disco como el original. La cola admite hasta 100 registros.

## Validación

Pruebas sintéticas de persistencia, ejecución secuencial, pausa, recuperación, aprobaciones y API. No certifican los modelos, los discos físicos ni la calidad de los videos. Las pruebas con los modelos reales permanecen pendientes.

## Orden y limpieza

Con la cola detenida, **Subir** y **Bajar** cambian la prioridad de un trabajo pendiente. **Retirar de la cola** elimina únicamente su registro: conserva el proyecto, checkpoints y resultados. Puedes retirar registros terminados para liberar espacio en la lista de 100. Ninguno de estos controles inicia producción. Mientras el controlador está activo, espera a que termine después de solicitar pausa.

## Comprobación previa

**Comprobar cola sin ejecutar** consulta la disponibilidad de los discos, la raíz y existencia de cada proyecto, sus aprobaciones y el nombre exacto del modelo seleccionado en el Ollama local. Espera hasta tres segundos la respuesta de Ollama. No ejecuta inferencia ni descarga pesos. Que aparezca instalado no acredita compatibilidad con llamadas de herramientas, workflows de ComfyUI, permisos de escritura ni espacio suficiente para el render. Los controles se repiten al iniciar la cola.

## Seguimiento

La cola muestra el estado y mensaje guardados por el productor, la última actualización y los checkpoints por etapa (excluye publicación). Se actualiza cada cinco segundos mientras la sección está visible y conserva los detalles abiertos. El recuento de etapas no representa porcentaje del tiempo ni estima cuánto falta. Un proyecto inaccesible muestra su propio error sin impedir consultar los demás.

La comprobación previa también detecta producciones, análisis de referencia y entregas locales activas. En ese caso indica que hay que esperar aunque la cola esté detenida. Es una consulta puntual; el control se vuelve a aplicar al iniciar.

## Reintentos y piloto de diez piezas

**Ver tiempos de producción** separa duración de cola y actividad por etapa. Al usar **Volver a poner pendiente**, conserva hasta veinte causas, fechas, tiempos por etapa y muestras RAM/VRAM de los intentos previos. La RAM corresponde a todo el equipo y la VRAM a la GPU NVIDIA más ocupada en intervalos aproximados de cinco segundos; no son consumo aislado del proyecto. Un dato ausente aparece «sin medir».

Cuando tengas diez proyectos distintos en los primeros diez lugares, pulsa **Fijar los primeros diez proyectos como piloto**. Guarda sus IDs y disco, sin iniciar generación. Reordenar la cola no cambia el grupo fijado. El informe muestra terminados, bloqueos, duración y cobertura de mediciones, decisiones editoriales, verificación de render y copia final registrada. Un proyecto retirado aparece como faltante. Las tasas se calculan solo con decisiones editoriales explícitas guardadas; los proyectos antiguos no tienen historial retroactivo. Los recibos de render y entrega no se recalculan al abrir este informe.

El piloto no estima por sí solo 48 videos semanales. La calidad visual, la exactitud del contenido y el funcionamiento de los modelos se validan con piezas reales en el equipo de producción.
