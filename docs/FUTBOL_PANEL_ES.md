# Consultas oficiales de fútbol desde el estudio

La sección «Fútbol · fuentes oficiales» permite consultar el conector UEFA existente. «Cargar opciones del conector» solo muestra acciones y competiciones, sin consultar estadísticas. La consulta inicial «definitions» permite revisar las definiciones antes de elegir métricas.

Selecciona una competición y una acción; indica en JSON los parámetros adicionales admitidos que muestra el formulario. Los IDs deben ser los oficiales y la edición y fase deben corresponder al alcance que quieras consultar. No se infieren identidades de jugador, equipo o entrenador a partir de nombres ambiguos.

«Consultar ahora en UEFA» ejecuta la consulta en un hilo separado del servidor. Solo permite una consulta de panel a la vez. Cada consulta limpia el resultado anterior; si falla no usa un respaldo antiguo. Los resultados permanecen únicamente en la página mientras se revisan: no se guardan como una base de estadísticas reutilizable.

Conserva las fechas, URLs, advertencias y alcance devueltos. Los servicios públicos del sitio UEFA no son una API contractual y pueden cambiar. No se considera completa la cobertura de FIFA, CONMEBOL, ligas nacionales ni toda la carrera de un jugador o entrenador.

El productor ya dispone de `official_uefa_live` como herramienta de investigación. Esta sección añade la consulta directa; no genera ni publica videos. Las pruebas usan transportes y resultados simulados; no certifican disponibilidad actual de los endpoints.
