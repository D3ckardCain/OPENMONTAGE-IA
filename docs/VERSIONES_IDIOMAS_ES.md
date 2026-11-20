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
