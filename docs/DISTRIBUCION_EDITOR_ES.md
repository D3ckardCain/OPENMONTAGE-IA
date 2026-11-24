# Distribución del editor (#92)

El editor de `/studio?edit=<proyecto>#video` ocupa la ventana. La biblioteca,
el visor y el inspector comparten la zona superior; la línea de tiempo ocupa
la zona inferior. Cada panel tiene desplazamiento interno. El vídeo se encaja
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
