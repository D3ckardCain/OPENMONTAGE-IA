# MLB para los agentes

Herramienta `official_mlb_live`, sin clave y sin proveedor de pago. Lee el servicio público `https://statsapi.mlb.com/api/v1/` durante cada consulta. No guarda una base reutilizable ni devuelve estadísticas antiguas cuando falla Internet. El acceso público no supone licencia de uso para retratos, logos o videos ni un contrato de disponibilidad del servicio.

## Uso

- `resolve_player`: `name`. Conserva la identidad oficial; no selecciona un candidato ambiguo.
- `player_statistics`: `player_id` oficial, `season`, `group` (`hitting` o `pitching`) y `metrics`.
- `compare_players`: dos `names`, `season`, `group` y `metrics`. Resuelve IDs internamente y consulta las estadísticas de ambos jugadores.

Ejemplo: nombres `Shohei Ohtani` y `Aaron Judge`, temporada `2024`, grupo `hitting`, métricas `homeRuns`, `avg`, `rbi`.

Cada respuesta incluye URL y fecha, grupo, año y tipo de partido. Un valor ausente sigue siendo null; cero sigue siendo cero. Las tasas publicadas como texto conservan su precisión. `inningsPitched` se conserva literalmente: su decimal representa outs, no una fracción decimal común.

## Cobertura inicial

Solo MLB y temporada regular (`gameType=R`). No promete carreras completas, postemporada, Statcast, boxeo ni otras ligas de béisbol. Si una respuesta contiene varios desgloses por equipos, bloquea la consulta agregada hasta validar el total oficial. No suma tasas ni innings. Si un jugador no tiene cifras en ese grupo/año, informa indisponibilidad; no lo transforma en una temporada con cero.

El resultado está listo para investigación y guion cuando las identidades y métricas están presentes. La plantilla gráfica admite ahora informes MLB en SVG/PNG y como clips MP4, con audio local opcional. La acción `collectible_card` resuelve un nombre y prepara hechos con procedencia individual. Las comparativas usan la fuente estadística propia de cada jugador. Los textos conservan tasas e innings sin convertirlos a números decimales. Las pruebas usan datos sintéticos para verificar el flujo visual; no constituyen validación con los modelos TTS ni retratos reales.

## Comprobación

El 20 de noviembre de 2026 respondió la búsqueda oficial de Ohtani y su estadística de bateo 2024. También se ejecutó una comparativa por nombres Ohtani–Judge. No se guardaron esas cifras como base actualizable. Las pruebas simuladas cubren homónimos, alcance incorrecto, múltiples desgloses, ausencia de métricas, cero, tasas e innings conservados y exclusión de parámetros no aplicables.
