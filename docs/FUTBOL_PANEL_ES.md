# Consultas oficiales de fútbol desde el estudio

La sección «Fútbol · fuentes oficiales» permite consultar el conector UEFA existente. «Cargar opciones del conector» solo muestra acciones y competiciones, sin consultar estadísticas. La consulta inicial «definitions» permite revisar las definiciones antes de elegir métricas.

Selecciona una competición y una acción. El formulario muestra campos separados para los parámetros admitidos, incluidos edición, fase e IDs. Las métricas se introducen separadas por comas. Los campos obligatorios están señalados y los opcionales pueden mantener el valor predeterminado del conector. Hay una sección JSON avanzada para parámetros adicionales; no debe repetir campos ya introducidos. Los IDs deben ser los oficiales y la edición y fase deben corresponder al alcance que quieras consultar. No se infieren identidades de jugador, equipo o entrenador a partir de nombres ambiguos.

«Consultar ahora en UEFA» ejecuta la consulta en un hilo separado del servidor. Solo permite una consulta de panel a la vez. Cada consulta limpia el resultado anterior; si falla no usa un respaldo antiguo. Los resultados permanecen únicamente en la página mientras se revisan: no se guardan como una base de estadísticas reutilizable.

Conserva las fechas, URLs, advertencias y alcance devueltos. Los servicios públicos del sitio UEFA no son una API contractual y pueden cambiar. No se considera completa la cobertura de FIFA, CONMEBOL, ligas nacionales ni toda la carrera de un jugador o entrenador.

El productor ya dispone de `official_uefa_live` como herramienta de investigación. Esta sección añade la consulta directa; no genera ni publica videos. Las pruebas usan transportes y resultados simulados; no certifican disponibilidad actual de los endpoints.

Al cambiar la acción se retiran los campos y parámetros anteriores. Al cambiar la competición se retira el resultado. Una respuesta que llegue después del cambio de selección no se presenta como si correspondiera a la nueva consulta.

## Leer el resultado

Cuando la fuente devuelve registros, el panel ofrece una tabla con los valores originales y nombres de métricas sin recalcularlos. Los valores nulos o ausentes se muestran como «Dato no disponible»; el cero se conserva como cero. El alcance, las advertencias y los enlaces oficiales de las consultas permanecen visibles.

La tabla muestra hasta 100 filas y 24 columnas y avisa si es parcial. «Ver datos originales completos» conserva la respuesta íntegra para revisar otras estructuras o campos. Mostrar una tabla no amplía la cobertura del servicio ni acredita exactitud de carrera completa.

## Elegir métricas de la fuente

Después de consultar «Definiciones de métricas», las consultas con varias métricas ofrecen un selector con los nombres devueltos por UEFA para la entidad correspondiente (jugador o equipo). «Añadir métrica elegida» completa el campo sin duplicarla. No inventa traducciones de nombres técnicos. La selección de entidad distingue el contrato de ranking (`player/team`) del histórico (`players/teams`).

Las definiciones permanecen solo en memoria de la página para esa competición. Cambiar competición las retira y limpia los campos; consultar de nuevo las definiciones invalida la lista anterior. Los rankings históricos de una sola métrica no usan estas sugerencias porque su ruta tiene otro contrato. La validación del servidor sigue comprobando las métricas antes de devolver estadísticas.

## Consultas enlazadas por ID

Las tablas de equipos, rankings y partidos pueden ofrecer «Preparar consulta» usando únicamente el ID que devolvió la fuente. Para jugadores mantiene la edición, métricas y fase del ranking; la ficha de equipo se señala como actual, no histórica. El botón rellena el formulario y no consulta automáticamente. Revisa los campos y pulsa «Consultar ahora». Si el tipo o la identidad son ambiguos, no se ofrece el enlace.
