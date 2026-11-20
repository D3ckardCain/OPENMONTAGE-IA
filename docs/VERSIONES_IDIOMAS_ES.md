# Preparar versiones por idioma

Abre un proyecto y despliega «Preparar versiones en otros idiomas». Indica entre uno y diez códigos separados por comas, por ejemplo `en, ko, de, pt-BR`. Pulsa «Crear proyectos por idioma».

Cada versión recibe el encargo base y las instrucciones de localización. Conserva el pipeline y la URL de referencia, utiliza su propio espacio de trabajo y exige aprobación por etapas aunque el proyecto base sea automático. No copia medios, artefactos, aclaraciones posteriores ni resultados del proyecto base; no ejecuta traducción o modelos al crearla. Después abre cada versión, revisa el encargo y utiliza el productor habitual o la cola.

Las instrucciones requieren adaptar narración, subtítulos, títulos, miniaturas, música y referencias culturales. El análisis debe confirmar el idioma de los diálogos y canciones y la autorización de sus recursos. No existe todavía una comprobación automática que certifique esa adaptación cultural.

No acepta el mismo idioma objetivo del proyecto base ni códigos repetidos. Eso no confirma el idioma original del video de referencia, que puede ser diferente. Repetir la solicitud reutiliza las versiones registradas para ese mismo encargo. Si falta una versión, se informa para evitar crear otra sin revisar. Los fallos parciales muestran qué idiomas se prepararon; no eliminan proyectos.

Las pruebas usan creadores simulados y no validan narración, traducción ni render con modelos reales.

## Organizar la producción

«Consultar versiones guardadas» recupera los proyectos registrados incluso después de cerrar la app. Marca los idiomas deseados y pulsa «Añadir versiones seleccionadas a la cola». Admite hasta diez por lote. Valida todos los proyectos y la capacidad antes de guardar. Las versiones que ya estén en la cola se conservan sin duplicarlas ni reactivar bloqueos. Los registros no disponibles no pueden seleccionarse. Luego revisa la cola e inicia su ejecución expresamente; siguen aplicándose las aprobaciones por etapa.

## Recursos locales

«Revisar recursos de voz y traducción» consulta los adaptadores registrados de voz, traducción y transcripción. Revisa archivos y configuración sin ejecutar Python auxiliar, hacer peticiones a servidores ni cargar modelos. Muestra requisitos ausentes y módulos pendientes. «Archivos configurados» no certifica dependencias instaladas ni soporte de un idioma: habrá que comprobar voz, pronunciación y calidad con los modelos reales.

La prueba de integración crea proyectos reales en carpetas temporales, comprueba checkpoints guiados, idiomas independientes, ausencia de renders y reutilización al repetir. No ejecuta inferencia.

## Estado de las versiones

La consulta de versiones guardadas muestra el estado del productor, su último mensaje, la verificación técnica guardada y si existe una copia final registrada. Resume las terminadas, bloqueadas, pendientes de aprobación y no disponibles. Una versión con el productor en estado `rendered` no se ofrece para añadir otra vez a la cola. Una copia registrada no confirma que su disco siga conectado; consulta «Videos finales» para comprobar disponibilidad. Los datos se actualizan al pulsar «Consultar versiones guardadas».

## Compartir análisis de referencia

Primero termina el análisis local en el proyecto base. Consulta sus versiones, marca las deseadas y pulsa «Compartir análisis base con las seleccionadas». Se guarda una instantánea JSON del informe: transcripción, observaciones, lagunas y procedencia. No copia el video ni fotogramas. Las rutas del informe siguen apuntando al proyecto original; consérvalo conectado si necesitas abrir esos recursos.

Solo admite versiones registradas con la misma referencia. Exige que no haya una tarea local activa. Conserva los análisis distintos ya existentes. Un informe parcial continúa siendo parcial: compartirlo no completa sus lagunas, traduce su contenido ni verifica sus afirmaciones. El productor puede consultar el informe guardado mediante su herramienta de análisis de referencia; solicitar expresamente un nuevo análisis seguirá ejecutándolo.

El productor reutiliza la instantánea compartida cuando llama a su acción de análisis sin parámetros. Antes comprueba la huella del contenido y que la referencia del proyecto siga coincidiendo. No descarga ni carga modelos en ese caso. Con opciones de análisis explícitas solicita una ejecución nueva. Se mantienen los controles de tarea activa y parada. El panel de referencias muestra la procedencia y un enlace al proyecto base.
