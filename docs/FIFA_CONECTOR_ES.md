# Conector FIFA para agentes

Herramienta: `official_fifa_live`, descubrible mediante `list_tools` con capacidad `football_statistics`. No necesita pesos, suscripción ni clave. Lee servicios públicos de FIFA en el momento; son servicios web no documentados, no una API contractual con disponibilidad garantizada.

## Consultas implementadas

- `seasons`: `competition_id`. Descubre IDs oficiales y fechas de las ediciones. Rechaza paginación no agotada en lugar de presentar un catálogo parcial como completo.
- `teams`: `competition_id`, `season_id`. Verifica que la edición pertenece a la competición antes de listar sus equipos.
- `player_statistics`: `competition_id`, `season_id`; opcionalmente `player_ids` (1–10 IDs FDH) y `metrics` (1–30 nombres originales). Verifica el ID de la edición y usa su propiedad oficial `IdIFES` para el feed estadístico. No equipara automáticamente namespaces.

El agente descubre la edición consultando `seasons`, no adivinando el ID a partir del año. Para el Mundial masculino, el ID de competición comprobado es `17`. Otros torneos necesitan validación específica; el conector no afirma cobertura universal FIFA.

## Evidencia y límites

Comprobación HTTPS real realizada el 20 de noviembre de 2026, desde el entorno de desarrollo:

- Listado de ediciones del Mundial masculino: 23 registros.
- Mundial 2022, edición `255711`: 32 equipos.
- Estadísticas de esa edición: consulta selectiva de un ID FDH y tres métricas respondió con el formato esperado.

La prueba verifica acceso y estructura, no audita todas las cifras ni acredita disponibilidad de todas las ediciones. No se guardó una base estadística para consultas futuras.

**Pendiente:** resolver nombres de jugadores automáticamente con evidencia oficial. El feed estadístico devuelve IDs y valores, no nombres. La ruta de plantilla probada devolvió HTTP 405; no se ha reemplazado por asociaciones supuestas. Esto impide considerar terminado el flujo «dos nombres → video» para FIFA.

Las unidades permanecen sin especificar hasta comprobar la definición oficial. Se conserva el indicador booleano del feed sin atribuirle un significado desconocido. Un valor ausente es `null`; un cero publicado sigue siendo cero. Errores de red, IDs inconsistentes, métricas duplicadas o valores no finitos producen fallo explícito, sin respaldo antiguo. No se calculan carreras completas, rankings propios ni palmarés a partir del agregado de una edición.

Cada resultado contiene URLs, hora UTC, alcance y advertencias. Un expediente guardado del video constituye evidencia histórica de esa producción; nunca se ofrece como la estadística actual de una producción posterior.

## Fuentes primarias

- https://api.fifa.com/api/v3/seasons?IdCompetition=17&count=100
- https://api.fifa.com/api/v3/seasons/255711
- https://api.fifa.com/api/v3/competitions/teams/255711
- https://fdh-api.fifa.com/v1/stats/season/255711/players.json

33 pruebas locales pasaron al incorporar el conector, cubriendo también el directorio deportivo, UEFA y su capa de consulta. El workflow de conectores incluye ahora las nuevas pruebas para Windows y Linux.
