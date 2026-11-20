# Conector FIFA para agentes

Herramienta: `official_fifa_live`, descubrible mediante `list_tools` con capacidad `football_statistics`. No necesita pesos, suscripción ni clave. Lee servicios públicos de FIFA en el momento; son servicios web no documentados, no una API contractual con disponibilidad garantizada.

## Consultas implementadas

- `seasons`: `competition_id`. Descubre IDs oficiales y fechas de las ediciones. Rechaza paginación no agotada en lugar de presentar un catálogo parcial como completo.
- `teams`: `competition_id`, `season_id`. Verifica que la edición pertenece a la competición antes de listar sus equipos.
- `player_statistics`: `competition_id`, `season_id`; opcionalmente `player_ids` (1–10 IDs FDH) y `metrics` (1–30 nombres originales). Verifica el ID de la edición y usa su propiedad oficial `IdIFES` para el feed estadístico. No equipara automáticamente namespaces.

El agente descubre la edición consultando `seasons`, no adivinando el ID a partir del año. Para el Mundial masculino, el ID de competición comprobado es `17`. Otros torneos necesitan validación específica; el conector no afirma cobertura universal FIFA.

- `squad`: `competition_id`, `season_id`, `team_id`. Consulta la plantilla de esa edición, nombres, alias, posición y vínculo oficial FDH.
- `resolve_players`: `competition_id`, `season_id`, `subjects` con `name` y opcional `team_name` (nombre oficial o abreviatura). Sin equipo examina todas las plantillas (máximo 64 equipos, cuatro consultas concurrentes). No utiliza aproximación difusa: coincide por nombre o secuencia completa de palabras, sin distinguir acentos y mayúsculas. Devuelve resuelto, ambiguo o no encontrado.
- `compare_players`: dos sujetos por nombre y las métricas solicitadas. Resuelve ambos jugadores, verifica vínculos FDH y consulta cifras de la edición. Si la identidad es ambigua no consulta ni atribuye estadísticas. Las métricas ausentes conservan `null` y bloquean el indicador de datos listos para guion.

## Evidencia y límites

Comprobación HTTPS real realizada el 20 de noviembre de 2026, desde el entorno de desarrollo:

- Listado de ediciones del Mundial masculino: 23 registros.
- Mundial 2022, edición `255711`: 32 equipos.
- Estadísticas de esa edición: consulta selectiva de un ID FDH y tres métricas respondió con el formato esperado.

La prueba verifica acceso y estructura, no audita todas las cifras ni acredita disponibilidad de todas las ediciones. No se guardó una base estadística para consultas futuras.

**Identificación por nombres incorporada:** la plantilla requiere ambos parámetros `idCompetition` e `idSeason`; la ruta incompleta utilizada en la primera comprobación no funcionaba. Se comprobó la comparativa por nombres de Messi (ARG) y Mbappé (FRA), Mundial 2022, con goles, asistencias y partidos. Los nombres y los vínculos FDH se obtienen de FIFA, no de una tabla manual. Esto verifica la adquisición de datos para esa comparativa; todavía no constituye una prueba de render del video ni acredita cobertura de todas las competiciones.

No se infiere el equipo a partir del conocimiento del modelo. El agente puede obtenerlo del usuario o de evidencia oficial; si no lo conoce, el conector consulta todas las plantillas y detecta homónimos. Un fallo de una plantilla invalida la resolución completa en lugar de declarar que el jugador no existe.

Las unidades permanecen sin especificar hasta comprobar la definición oficial. Se conserva el indicador booleano del feed sin atribuirle un significado desconocido. Un valor ausente es `null`; un cero publicado sigue siendo cero. Errores de red, IDs inconsistentes, métricas duplicadas o valores no finitos producen fallo explícito, sin respaldo antiguo. No se calculan carreras completas, rankings propios ni palmarés a partir del agregado de una edición.

Cada resultado contiene URLs, hora UTC, alcance y advertencias. Un expediente guardado del video constituye evidencia histórica de esa producción; nunca se ofrece como la estadística actual de una producción posterior.

## Fuentes primarias

- https://api.fifa.com/api/v3/seasons?IdCompetition=17&count=100
- https://api.fifa.com/api/v3/seasons/255711
- https://api.fifa.com/api/v3/competitions/teams/255711
- https://fdh-api.fifa.com/v1/stats/season/255711/players.json

41 pruebas locales pasaron al incorporar identificación y comparativas, cubriendo también el directorio deportivo, UEFA y su capa de consulta. El workflow de conectores incluye ahora las nuevas pruebas para Windows y Linux.


## Postales coleccionables

`collectible_card` acepta un sujeto por nombre y las métricas de una edición. Ejecuta consultas nuevas y devuelve biografía de plantilla y hechos con URL, fecha de consulta, ID y alcance por cifra. No calcula edades actuales a partir de datos históricos ni atribuye récords completos, trofeos o puntuaciones de habilidad. Imagen y derechos permanecen pendientes. Es un insumo para guion/diseño, no una imagen renderizada.
