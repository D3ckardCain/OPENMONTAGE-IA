# Recursos de System Academy: adaptación para OPENMONTAGE‑IA

Revisión del catálogo de 26 recursos en [la biblioteca](https://biblioteca.systemacademy.es/recursos), sus fichas de producción, retención, nichos y herramientas, y los documentos enlazados de investigación de nichos, análisis de canales y guiones. Se revisó el contenido textual accesible de las fichas y esos tres prompts; no se validó el contenido completo de cada video ni sus promesas de resultados.

## Lista de desarrollo

| Orden | Aporte observado | Adaptación a nuestra app | Estado |
| --- | --- | --- | --- |
| 1 | Subtítulos y montaje para video corto | Exportación local con subtítulos visibles y márgenes para 9:16 y 16:9, además del MP4 con pista editable y SRT | En desarrollo |
| 2 | Nichos y canales: analizar muestra completa, consistencia, antigüedad y excepciones | El buscador audita ventanas de 7, 30, 90 o 365 días por páginas, conserva cada informe local con hash y compara dos expedientes elegidos solo por videos comunes. Permite guardar una propuesta original vinculada a un expediente; las observaciones manuales de vidIQ se guardan por video y fecha | Parcial |
| 3 | Filtrado de ideas y diagnóstico de alcance, clics y retención | Módulo editorial que compare propuestas y, cuando haya datos aportados, explique impresiones, CTR y retención por pieza y periodo | Pendiente |
| 4 | Guiones: título, apertura, bloques, voz, indicaciones visuales y revisión factual | Plantilla original de guion por escenas, duración estimada por palabras, marcas de verificación factual y aprobación antes de voz y video | Pendiente |
| 5 | Títulos y miniaturas | Variantes, vista previa legible en móvil y decisión editorial guardada; modelos locales ya registrados antes de añadir otros | Pendiente |
| 6 | Flujo de tareas y retroalimentación | Estado por etapa, trazabilidad del artefacto, medición de tiempos y revisión de calidad con datos reales del canal | Parcial |
| 7 | Stock externo | Evaluar licencia, procedencia y restricciones de uso de cada activo antes de admitirlo como fuente de una pieza | Pendiente |

Las cifras indicativas de RPM, visualizaciones, CTR o retención de los recursos no son garantías ni límites universales; se deberán mostrar como hipótesis configurables y con periodo y fuente. La originalidad de guion, imágenes, música y narración se comprueba en cada proyecto. La biblioteca menciona servicios como ElevenLabs, CapCut, Canva, Claude, vidIQ y NexLev: no se integran en la ruta principal mientras no se demuestre operación gratuita y compatible con el objetivo de costo cero. Usamos los conceptos del flujo y redactamos nuestros propios formularios y prompts; no copiamos materiales protegidos.

La búsqueda inicial consulta como máximo veinte publicaciones recientes por canal y las cifras son vistas acumuladas al momento de consulta. La ficha presenta las descartadas junto a las coincidentes y muestra la concentración en la publicación líder solo si conoce las vistas de al menos tres videos. La acción separada de auditoría acepta ventanas de 7, 30, 90 o 365 días y un límite de 2, 5 o 10 páginas de cincuenta elementos; muestra antes un máximo aproximado de solicitudes HTTP, que no son unidades de cuota. Obtiene los detalles en lotes y une los resultados por ID. Indica cobertura incompleta si llega al límite o faltan fechas o videos; la fecha de corte y las solicitudes realizadas figuran en el resultado. La lista de subidas puede cambiar durante la paginación, por lo que esta cobertura es una comprobación de la lista pública consultada, no una certificación histórica inmutable.

Cada auditoría exitosa genera un expediente local nuevo con SHA-256 del informe, fecha y alcance; «Ver auditorías guardadas» permite recuperarlo sin gastar solicitudes API. Se conservan hasta cincuenta expedientes por canal; al alcanzar el límite, la consulta sigue mostrando sus datos pero explica que no pudo guardarlos. El hash detecta cambios en el expediente guardado; no demuestra que YouTube mantenga esos valores posteriormente. El historial no realiza descargas de videos ni contiene métricas privadas de vidIQ.

La comparación de dos expedientes elegidos mide diferencias entre capturas solo para videos con ID común y cifras conocidas que no hayan disminuido. Enumera por separado nuevas publicaciones, ausentes, cifras desconocidas y cifras reducidas. Avisa cuando las dos ventanas tienen duraciones diferentes. La suma de diferencias y el promedio por hora se refieren únicamente a esos videos comparables y a ese intervalo entre consultas. No representan visitas totales del canal, CTR, retención, ingresos ni el rendimiento completo del periodo.

Desde un expediente guardado se pueden seleccionar de uno a cinco videos como referencias y redactar un título, enfoque y audiencia propios. La propuesta conserva el hash y fecha del informe, las cifras de esas referencias en ese momento y queda como **borrador** con revisión de hechos y derechos pendiente. Un enlace prepara un proyecto en el estudio con ese contexto; no aprueba el guion ni genera o publica el video. Los títulos idénticos al de una referencia seleccionada se rechazan, aunque la originalidad exige revisión editorial real.

El agente local dispone de `saved_channel_evidence` para leer ese expediente y, opcionalmente, la propuesta vinculada. La herramienta exige IDs exactos, comprueba integridad y devuelve las publicaciones en páginas de hasta 50 con `next_offset`. El encargo del estudio incluye los IDs para solicitarla. Es lectura local de costo cero: no consulta otra vez YouTube, no incorpora los cálculos de vidIQ y conserva la advertencia sobre cobertura, fecha y revisiones pendientes.

Al crear una producción desde una propuesta, el estudio valida de nuevo IDs, hash y referencia elegida, guarda el vínculo estructurado en la solicitud y copia la propuesta y el expediente íntegro como artefactos del proyecto. `project_channel_evidence` verifica el hash y los IDs de ambas copias y devuelve las publicaciones en páginas de hasta 50 con `next_offset`, incluso si el proyecto cambia de disco. Una copia alterada se rechaza. Crear el proyecto no aprueba las afirmaciones ni las licencias del material.

El estudio muestra fecha de consulta, cantidad de publicaciones, cobertura del periodo y SHA-256 de la copia. Si falta o cambia un artefacto, indica que se debe revisar el proyecto y rechaza el inicio o aprobación de etapas hasta restaurar evidencia íntegra; una captura histórica no demuestra cifras actuales ni derechos de uso.

Proyectos antiguos con la propuesta local conservada pueden recuperar un expediente faltante desde los registros locales mediante «Recuperar copia local». La operación comprueba IDs, referencia, hash cuando exista y contenido de cualquier copia superviviente; nunca sobrescribe una copia alterada. Si los registros originales ya no están disponibles o falta una referencia de integridad, la recuperación se rechaza.

Al crear un proyecto desde una propuesta, se copian únicamente las observaciones manuales ya guardadas para los videos de referencia elegidos. El agente las consulta con `project_vidiq_observations` en páginas de hasta 50, con fecha y atribución, separadas del expediente oficial. La copia tiene hash en la solicitud; una modificación posterior bloquea el inicio. Los proyectos antiguos sin copia muestran esa ausencia, sin inventar valores.

En el estudio, «Ver publicaciones» y «Ver observaciones vidIQ» muestran páginas de veinte registros de la copia verificada del proyecto. Se ven por separado la fecha, cobertura y vistas de YouTube, y la fecha y métricas manuales atribuidas a vidIQ. No se vuelve a consultar ninguna fuente ni se carga todo el expediente en una respuesta.

### Observación puntual con vidIQ en Edge

El 22 de noviembre de 2026 se revisó [este video de Edwin Arenas](https://www.youtube.com/watch?v=rd8TQwkQ4zs) con la extensión ya instalada. La ficha visible indicaba **80,1 mil vistas acumuladas**, **21 VPH**, **2,7 % Engagement**, **19,7× Outlier** y **40,3/100 puntuación SEO**. También mostraba etiquetas del video y canal y una gráfica histórica de vistas. Son valores mostrados por vidIQ en ese momento; VPH y puntuaciones son cálculos del proveedor y no equivalen a CTR, retención, ingresos ni crecimiento certificado del canal. La propia interfaz reservaba ciertas etiquetas y opciones para planes de pago.

La página «Canales» incluye un formulario para registrar vistas, VPH, engagement, outlier y SEO del video con fecha automática y fuente «vidIQ Edge (transcripción manual)». Cada observación se añade al historial local del ID del video; no sustituye registros anteriores ni se mezcla con la respuesta oficial de YouTube. El backend local no puede acceder a la extensión de Edge ni promete extracción automática de datos privados de vidIQ. El operador introduce solo cifras que ve; los análisis periódicos siguen usando la fuente pública disponible.

### Enlaces revisados

- [Catálogo de recursos](https://biblioteca.systemacademy.es/recursos)
- [Guía de investigación de nichos](https://docs.google.com/document/d/10fD6d4XAOdXnJ1HHlQNjtHLVOoky_KfwPyrCBusL0WE/edit)
- [Guía de análisis de canales e ideas](https://docs.google.com/document/d/1XubNFRSNKhCLGNzPSqYxBeVrFChLtSTVNcMbwbYH2IE/edit)
- [Guía de guiones](https://biblioteca.systemacademy.es/prompt-guiones)
