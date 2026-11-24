# Distribución del editor (#92)

El editor de `/studio?edit=<proyecto>#video` ocupa la ventana. La biblioteca,
el visor y el inspector comparten la zona superior; las pistas aparecen
inmediatamente debajo, seguidas de sus herramientas. Cada panel tiene desplazamiento interno. El vídeo se encaja
sin deformar y su tamaño original no empuja la línea de tiempo fuera de pantalla.

Arrastra los dos separadores verticales para ajustar biblioteca, visor e inspector.
Arrastra el separador horizontal para repartir altura entre visor y timeline.
También puedes enfocar los separadores con Tab: flechas ajustan 16 px;
Mayús + flechas, 64 px; Inicio/Fin llevan a los límites admitidos.
En el separador horizontal usa arriba/abajo. El menú **Distribución** ofrece
los mismos ajustes y permite ocultar los paneles laterales.

Las dimensiones y paneles ocultos se guardan en el almacenamiento local del
navegador, reutilizando las claves anteriores. Una ventana menor limita los tamaños
para conservar espacio útil; no sobrescribe la preferencia hasta que se ajusta
manualmente. La distribución se comparte entre Vídeo, Audio y Subtítulos y no
modifica el proyecto, su revisión, los medios ni la vista previa existente.

La primera apertura sin preferencias reserva aproximadamente el 35% del espacio
útil para pistas y herramientas; los tamaños anteriores se respetan. La regla
de segundos, vídeo, audio y subtítulos comparten escala y desplazamiento horizontal.
Los bloques de subtítulos abren su edición debajo de las pistas y seleccionan
el cue. Seleccionar un clip habilita las acciones directas de división,
reordenación y eliminación; el formulario de recorte, ganancia, fades y velocidad
se despliega debajo. El botón **Ver montaje guardado** vuelve desde una fuente
al render existente sin generar otro. Preparación y exportación están en la
barra del proyecto. Se conserva un solo proyecto y la misma revisión.

Referencias de interacción aprobadas en el comentario 7140938058 de #92:
estructura Kdenlive, especialización de audio Fairlight y controles/subtítulos
Shotcut. No se copia código ni recursos. El motor continúa con cortes de vídeo
secuenciales y pistas de audio independientes; los bloques de subtítulos no
añaden capas de vídeo. Waveforms por pista, mezclador/medidores, doble visor,
karaoke y herramientas avanzadas siguen pendientes. La forma de onda existente
del audio seleccionado se conserva; no es un medidor ni la mezcla renderizada.

## Alcance de verificación

La regresión de navegador usa el EDL real del proyecto `edit-827337e03f38`,
revisión 27, capturado de disco en solo lectura. Contiene dos cortes, una pista
de audio y un cue manual. Se omite su historial; no se incluyen medios en CI.
Los transportes se interceptan: las capturas acreditan geometría, controles y
persistencia, **no reproducción audiovisual real ni la ventana Windows abierta**.
Se comprueban 1920×1080 y 3440×1440, arrastre, teclado, reapertura, ocultación,
cambio de espacio y límites de preferencias extremas, sin comandos de edición.
La validación audiovisual previa sigue en `VALIDACION_EDITOR_HTTP_ACTIVO_ES.md`.

El servidor local no se reinició. En esta sesión el PID 73536 continuaba
escuchando en 4750, pero una consulta del editor agotó 15 s sin respuesta;
esto no demuestra que el servidor haya cerrado. La observación de esa ventana
requiere las herramientas de escritorio autorizadas, no disponibles en esta sesión.

Diagnóstico posterior: el hilo principal está bloqueado dentro de la escritura
síncrona de un log (`logging.StreamHandler.emit`, CALL a `stream.write`, línea1113).
El registro informa un `ConnectionResetError [WinError 10054]` en
`_ProactorBasePipeTransport._call_connection_lost`. Esto explica que incluso
`/api/health` no responda; no demuestra por sí solo por qué se bloqueó el destino
del log. Se pidió comprobar selección en la consola y pulsar Esc si existe,
sin reiniciar. No se inyectó código, suspendió el proceso ni modificó su memoria.
La recuperación y la apariencia/interacción de la ventana real siguen pendientes
hasta verificarlas; CI no las sustituye. Evidencia: `EVIDENCIA_BLOQUEO_HTTP_20261124.json`.
