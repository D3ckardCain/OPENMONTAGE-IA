# Aplicación, discos de trabajo y videos finales

La aplicación y su configuración pueden residir en el M.2. Las carpetas de pesos
se configuran como recursos y adaptadores; no necesitan compartir disco con la app.

En Modelos y discos se registran hasta 16 carpetas de proyectos, cada una con un
nombre. Se muestra disponibilidad y espacio del volumen. Esta primera versión
mantiene un disco de proyectos activo por sesión; cambiarlo requiere reiniciar.
No combina todavía en un listado único proyectos de todos los discos simultáneamente.
Las carpetas deben existir: guardar la configuración no mueve ni borra trabajos.
Si el disco activo se desconecta, no se cambia silenciosamente al M.2.

El destino de videos finales se configura por separado. Puede ser una carpeta en
el disco de modelos o en otro disco dedicado. Dejarlo vacío conserva el comportamiento
de guardar renders en el proyecto. Al finalizar una producción, después de verificar
los renders, el agente copia los archivos al destino configurado dentro de una
carpeta del proyecto. El nombre incorpora parte del hash para conservar versiones.
Se verifica SHA-256 de cada copia y se registra su ubicación en final_delivery.json.
El panel muestra esas rutas; los originales permanecen en el disco de trabajo.

Si falta el disco de finales, falla la copia o no hay espacio, no se declara una
entrega exitosa. Los archivos de trabajo no se eliminan. Los pesos existentes en
ese disco no se mueven ni se modifican. No se realizó ninguna migración sobre los
discos del usuario; las pruebas utilizan archivos pequeños en carpetas temporales.

La configuración de almacenamiento permanece en .backlot/storage.json junto a la
app. OPENMONTAGE_PROJECTS_DIR, cuando existe, tiene prioridad para el disco de
trabajo y se informa en el diagnóstico. La guía general se completará al validar
el flujo completo y estabilizar todas las opciones del panel.

## Comprobación antes de producir

El panel permite consultar si las carpetas de trabajo y de finales están
disponibles y cuánto espacio libre reporta el sistema. Iniciar agentes se
rechaza si falta uno de esos destinos o el espacio es cero. El análisis de
referencias verifica únicamente su disco de trabajo. La comprobación no escribe
archivos, no predice el tamaño del render ni certifica permisos o velocidad.
