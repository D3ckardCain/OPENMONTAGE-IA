# youtube-research-skills — evaluación #50

24-11-2026 UTC. [TubeLabHQ a8a67468](https://github.com/TubeLabHQ/youtube-research-skills/tree/a8a674681e5297ce700ba9393e11cff451f2768a),
HEAD consultado. Paquete privado0.1.0, capa tubelab-mcp3.1; no confundir versiones
de paquete/skills. Lectura estática, sin conectar TubeLab, usar credenciales, investigar
canales reales o producir títulos/guiones/medios.

## Decisión y comparación

Reutilizar métodos, no su backend pagado ni sus inferencias comerciales. Priorizar
español, muestras guardadas y el agente local; una cobertura menor debe declararse.

| Método | OPENMONTAGE existente | Aporte justificado |
|---|---|---|
| Buscar canales/nichos | `tools/research/youtube_*`: consultas, filtros, periodos/lotes; dossiers y fuentes fechadas | Contrato de hipótesis de nicho y comparación reproducible, no nuevo buscador equivalente a índice TubeLab |
| Outliers | `youtube_channels.py` ya calcula median_views y top_to_other_median_ratio; observaciones vidIQ manuales separadas | Cohortes por edad/formato/periodo y ratios con denominador/n explícitos. No duplicar mediana ni mezclar dato manual con cálculo propio |
| Títulos/miniaturas | `packaging_options`, thumbnail y selección editorial/procedencia existentes | Extraer patrones sustentados en muestra y distinguir hipótesis de éxito causal. No copiar títulos ni inferir CTR por vistas |
| Comentarios | El cliente devuelve commentCount, no se halló lectura de hilos en su superficie revisada | Adaptador paginado optativo y análisis de temas sobre comentarios guardados; cantidad no equivale a corpus ni sentimiento |
| Transcripción | Descarga/análisis de referencia y ASR local preparado | Analizar material autorizado ya local; no prometer captions oficiales de cualquier vídeo público |
| Monetización | Cliente conserva monetized/revenue/rpm=None y CSV de rendimiento aportado | Mantener desconocidos. Ofertas/patrocinios observados pueden tener fuente; ingresos, audiencia inferida o pérdida de anuncios no se inventan |

Fuentes upstream seleccionadas: [niche-validator](https://github.com/TubeLabHQ/youtube-research-skills/blob/a8a674681e5297ce700ba9393e11cff451f2768a/skills/niche-validator/SKILL.md),
[title-formulas](https://github.com/TubeLabHQ/youtube-research-skills/blob/a8a674681e5297ce700ba9393e11cff451f2768a/skills/title-formulas/SKILL.md),
[comment-mining](https://github.com/TubeLabHQ/youtube-research-skills/blob/a8a674681e5297ce700ba9393e11cff451f2768a/skills/comment-mining/SKILL.md),
[revenue-maxxing](https://github.com/TubeLabHQ/youtube-research-skills/blob/a8a674681e5297ce700ba9393e11cff451f2768a/skills/revenue-maxxing/SKILL.md).
Locales: `youtube_client.py`, `youtube_channels.py`, `lib/channel_dossiers.py`,
`channel_performance.py`, `video_observations.py`, `packaging_options.py`.

## Costo, acceso y offline

[Capa TubeLab](https://github.com/TubeLabHQ/youtube-research-skills/blob/a8a674681e5297ce700ba9393e11cff451f2768a/skills/tubelab-mcp/SKILL.md)
describe planes/créditos; búsquedas y ciertos clientes/API tienen condiciones de plan.
No activar Starter/Pro/Team, trial, clave o conexión MCP pagada. Instrucciones abiertas
no hacen gratuito el servicio. No adoptar afirmaciones del proveedor de que sin su
índice todo cálculo es imposible: sí podemos calcular sobre nuestra muestra, sin
afirmar cobertura, freshness o campos equivalentes a su base propietaria.

YouTube Data API existente puede usarse dentro de acceso/cuota autorizados, sin
activar facturación. No se comprobó cuota efectiva del proyecto ni se pidió otra clave.
[Tabla oficial consultada](https://developers.google.com/youtube/v3/determine_quota_cost)
distingue actualmente buckets de search.list/videos.insert y unidades del resto;
no fijar de memoria reglas antiguas o asumir cuota ilimitada/gratuita para todo.
Paginación y consultas fallidas también consumen cuota; guardar conteo, caché,
filtros y cobertura parcial, sin reemplazar error por un resultado viejo silencioso.

[commentThreads.list](https://developers.google.com/youtube/v3/docs/commentThreads/list)
cuesta1unidad según documentación consultada; un hilo no garantiza todas sus respuestas.
Considerar paginación, desactivados, borrados y sesgo de ordenar por relevancia.
[captions.download](https://developers.google.com/youtube/v3/docs/captions/download)
requiere autorización y permiso de editar el vídeo; no es una API abierta de
transcripciones de cualquier canal. Alternativas: textos aportados o ASR sobre medios
obtenidos legítimamente, conservando su procedencia. No eludir restricciones de acceso.

Offline solo para analizar snapshots/transcripciones/CSV ya locales. Recolectar datos
frescos requiere red; la interfaz debe mostrar fecha, origen, n, faltantes y modo
cache/offline. No llamar a fuentes externas para evaluar aquí ni usar un modelo para
rellenar métricas faltantes.

## Licencia y dependencias

[MIT](https://github.com/TubeLabHQ/youtube-research-skills/blob/a8a674681e5297ce700ba9393e11cff451f2768a/LICENSE)
para instrucciones; mantener atribución si se adaptan. No cubre datos del servicio,
vídeos, comentarios, miniaturas o marcas; respetar condiciones de API y derechos del
contenido. El [paquete](https://github.com/TubeLabHQ/youtube-research-skills/blob/a8a674681e5297ce700ba9393e11cff451f2768a/package.json)
declara Node>=20 para su validador de skills, no un motor local de investigación.
La adaptación puede usar los lectores/Python/agente ya presentes sin instalarlo.

## Tareas futuras con aceptación

| Prioridad | Tarea | Aceptación |
|---|---|---|
| P0 | Informe de muestra y baseline | URLs/fecha/filtros/n/periodo/edad/formato y fórmulas; mediana0, muestra pequeña, vistas ocultas, duplicados y periodos diferentes dan resultados explícitos o desconocido |
| P0 | Mapear capacidades gratuitas | Separar metadatos observados, CSV del propietario, vidIQ manual y campos no disponibles; tests de faltantes sin inventar RPM/ingresos/monetización |
| P1 | Lectura de comentarios | Mocks de hilos/respuestas/páginas, cuota/error/desactivados y IDs duplicados; textos no confiables tratados como datos, muestreo trazable, privacidad y sin publicar respuestas |
| P1 | Patrones de títulos/miniaturas | Referencias y muestra guardadas, revisión del agente en español y evidencia visual separada; no atribuir rendimiento causal ni generar miniaturas en el diagnóstico |
| P2 | Watchlist offline | Snapshots versionados, vencimiento visible, comparación reproducible y consultas frescas solo explícitas; presupuesto de llamadas sin pagos/fallback TubeLab |

La evaluación no calcula ingresos, evalúa canales reales o acredita precisión de las
heurísticas upstream. No se importaron instrucciones como reglas de sesión. Se
completa el análisis; las adaptaciones y fuentes nuevas siguen pendientes.
