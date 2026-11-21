# Buscador de canales

En el panel de producciones, abrir **Buscador de canales** (`/channels`). Escribir
un tema, configurar filtros y pulsar **Buscar canales**. La clave de YouTube Data
API se configura en el entorno local del servidor; no se pide ni se envía desde
el formulario. Sin clave no se inventan resultados. Cada búsqueda consulta datos
actuales; no se almacena un inventario de estadísticas ni se recuperan resultados
anteriores cuando falla la consulta.

## Orden y filtros
El orden predeterminado es vistas totales del canal descendentes; suscriptores públicos
como segundo criterio en empates. No prioriza suscriptores por encima de vistas.
Los contadores de suscriptores están redondeados por YouTube. Un valor oculto o
faltante se representa como desconocido, nunca como cero; si se exige un rango
de suscriptores, los canales sin esa información no pueden cumplirlo.

Filtros disponibles:
- Vistas totales del canal: mínimo y máximo, sin tope máximo artificial.
- Tamaño del canal: rango de suscriptores.
- País declarado por el canal: distinto del país del público.
- Idioma del audio declarado en una publicación de la muestra reciente.
- Duración mínima y máxima en minutos enteros.
- Tipo por duración: todos, hasta 3 minutos (candidatos a Shorts), más de 3
  minutos, 4–20 minutos inclusive y más de 20 minutos.
- Fecha de publicación: última hora, 24 horas, 7 días, 30 días o 365 días.
- Vistas mínimas por publicación coincidente: distinto de vistas totales.
- Cantidad mínima de publicaciones coincidentes: entre 1 y el tamaño de la muestra.
- Profundidad: 1–3 páginas de candidatos y 5, 10 o 20 publicaciones recientes.

Los filtros de contenido se evalúan **juntos en una misma publicación**. Basta
una coincidencia de forma predeterminada; el mínimo es configurable. No se afirma que todo el
canal tenga ese idioma, formato o volumen de vistas. Las emisiones en directo y
sus archivos quedan excluidos de esta revisión. Los elementos privados o borrados
pueden reducir la muestra efectivamente revisada. No se buscan publicaciones en
el historial completo ni se promete encontrar coincidencias antiguas.

## Alcance y límites
Los resultados son una muestra del índice de búsqueda, no un censo o clasificación
global. Un orden distinto de relevancia puede devolver menos resultados en la API;
se consultan después los contadores actuales de los canales y se ordena la muestra.
Vistas acumuladas altas no prueban crecimiento reciente, viralidad actual,
monetización ni RPM. Estas últimas métricas no se estiman ni puntúan. No se calcula
un índice propio de viralidad. Una publicación de menos de 3 minutos puede ser un
video normal: la duración no confirma su clasificación como Short.

La búsqueda de metadatos es más rápida; activar filtros de contenido requiere
consultar publicaciones por canal. Hay un presupuesto temporal de 120 segundos
antes de iniciar cada petición (cada petición conserva su timeout de 30 segundos)
y un máximo de dos consultas simultáneas desde el panel. Si falla, reducir páginas
o profundidad; no se muestran coincidencias parciales como una búsqueda completa.
Las acciones consumen cuota gratuita de Google, no cuota de GitHub Actions.

## Agentes
Para descubrir canales, buscar en el registro la capacidad
`youtube_channel_research` y usar `youtube_channel_search.execute`:

```json
{"query":"animales","pages":1,"filters":{"min_views":1000000,"min_subscribers":1000,"language":"es","content_type":"medium","published_within":"month","sample_size":10}}
```

Los modos de investigación de videos anteriores siguen disponibles como funciones
separadas; el nuevo panel y esta capacidad devuelven exclusivamente canales.
El agente conserva en su respuesta la fecha de consulta y el alcance de la muestra,
y separa descubrimiento de canales de la posterior investigación editorial de ideas.

Fuentes oficiales revisadas el 14 de noviembre de 2026:
- https://developers.google.com/youtube/v3/docs/search/list
- https://developers.google.com/youtube/v3/docs/channels
- https://developers.google.com/youtube/v3/docs/playlistItems/list


## Identificación directa de canales
El campo de búsqueda acepta temas, `@usuario`, ID `UC…` y enlaces de YouTube
`/@usuario` o `/channel/UC…`, incluso sus pestañas videos/shorts/about. También
acepta los enlaces históricos `/user/nombre` mediante la API oficial. Los enlaces
personalizados `/c/nombre` y enlaces de videos no se convierten en canales por
aproximación: se pide usar el @usuario. Se admiten handles con escritura Unicode.

Una identidad concreta se consulta con `channels.list` (id/forHandle/forUsername),
sin gastar una consulta de `search.list`. No se sigue el enlace pegado ni se visita
su dirección: solo se extrae el identificador y se envía al endpoint oficial.
Si no se encuentra, no se sustituyen resultados por nombres similares. Los filtros
se mantienen, por lo que un canal identificado puede quedar excluido por sus rangos.
La profundidad en páginas solo se aplica a temas; la muestra reciente se mantiene
cuando se activan filtros de contenido.

Referencia oficial: https://developers.google.com/youtube/v3/docs/channels/list


## Diagnóstico de fallos
La presencia de una clave local no certifica su validez: esta se comprueba durante
una consulta real. Los errores distinguen clave ausente/rechazada, API sin habilitar,
acceso denegado, cuota agotada, límite temporal, desconexión, timeout y respuesta
inválida. Se muestran mensajes propios y códigos estables; no se devuelven claves,
URLs de petición, mensajes originales del proveedor ni cuerpos HTTP de error.
La lectura del cuerpo de error está limitada a 64 KiB y su conexión se cierra.

Una consulta fallida no devuelve resultados anteriores ni se transforma en una lista
vacía satisfactoria. Se conservan el tema y los filtros en la pantalla para corregir
y reintentar. No hay reintentos automáticos: la cuota agotada necesita restablecerse;
los errores temporales se indican como tales a los agentes mediante `retryable`.
No se promete una hora de recuperación ni se deduce que toda respuesta 403 sea cuota.

Referencia: https://developers.google.com/youtube/v3/docs/errors


## Consultas automáticas de varios temas
Escribir hasta cinco temas, @usuarios o enlaces, uno por línea, y pulsar Buscar
canales. El servidor los consulta secuencialmente, elimina entradas equivalentes
y une canales por su ID. Se conservan los temas que coincidieron con cada canal,
y se ordena por vistas y después suscriptores. Si un contador cambia entre temas,
se conserva la respuesta más reciente; no se fabrica el mayor valor observado.

Se validan todos los temas y filtros antes de la primera consulta. Hay un límite
de 300 solicitudes API por lote de forma predeterminada (configurable entre 1 y
500 por los agentes, con opciones en la interfaz), y 180 segundos para iniciar
peticiones; una petición en curso mantiene su timeout de 30 segundos. El presupuesto
cuenta solicitudes, no unidades de cuota de Google ni dinero.

Ante cualquier fallo, el lote se detiene sin reintentar los temas restantes.
Si ya había temas completados, se muestran sus resultados actuales con el aviso
LOTE INCOMPLETO y la lista de pendientes. Un tema interrumpido no aporta resultados
parciales. Los resultados no se guardan ni se mezclan con ejecuciones anteriores.
Tras resolver el fallo, el agente puede consultar los temas pendientes en un lote
nuevo, con datos actualizados; no se programa una tarea recurrente ni se ejecuta
nada después de cerrar la aplicación.

Los agentes descubren `youtube_channel_batch_research` y llaman a
`youtube_channel_batch.execute` con `queries`, `filters`, `pages`, `max_requests`.
Es una herramienta de consulta determinista: el agente elige los temas y toma las
decisiones editoriales. No introduce un orquestador de agentes en Python ni inicia
producción o publicación de videos.

## Muchas vistas en un canal joven
`max_channel_age_days` limita la antigüedad desde `snippet.publishedAt`, la fecha
oficial de creación del canal. Por ejemplo, `min_views: 1000000` junto con
`max_channel_age_days: 90` exige un millón de vistas acumuladas y un canal creado
hace como máximo 90 días. Un canal con un millón de vistas en cinco años queda
fuera. Si la fecha falta, es inválida o futura, no cumple este filtro. No hace falta
consultar publicaciones para comprobar la antigüedad. Se aplica también a lotes e
identidades concretas. El orden sigue siendo vistas, después suscriptores.

La creación del canal no es la fecha del primer video ni el comienzo de una nueva
etapa del canal. Un canal antiguo que crece ahora puede quedar fuera de este modo.
La fecha de publicaciones sirve para otro caso: encontrar publicaciones recientes
con muchas vistas. No revela las vistas ganadas por todo el canal durante los
últimos 30 días. Para ese dato haría falta una fuente temporal autorizada; no se
inventa a partir del contador acumulado ni se guarda un histórico silenciosamente.

## Investigación editorial posterior
La detección de candidatos precede al análisis de sus publicaciones: tema, hechos,
fuentes, gancho, estructura, ritmo, tratamiento visual y audiencia. El análisis
permitirá proponer un guion y recursos propios para cada idioma, verificando hechos
y derechos de los materiales. No se implementan transformaciones para ocultar una
copia: cambios cosméticos o traducciones por sí solos no garantizan originalidad
ni monetización. La revisión editorial debe identificar aportaciones propias,
material autorizado y adaptación cultural, además de diferencias superficiales.

Fuentes oficiales:
- https://developers.google.com/youtube/v3/docs/channels
- https://support.google.com/youtube/answer/1311392?hl=es


## Éxitos repetidos en publicaciones recientes

El filtro `min_matching_publications` (predeterminado 1) exige entre 1 y
`sample_size` publicaciones **distintas** que cumplan cada una todos los filtros
de contenido. Se aplica igual a una consulta directa y a un lote. Por ejemplo:

```json
{"query":"animal behavior","filters":{"published_within":"month",
 "min_publication_views":100000,"min_matching_publications":3,"sample_size":20}}
```

Esto pide al menos tres publicaciones de los últimos 30 días con 100000 vistas
acumuladas cada una dentro de la muestra reciente. No mide vistas ganadas durante
el mes ni certifica monetización o viralidad. Un canal con una sola coincidencia
queda excluido como `insufficient_matching_publications`. Una muestra incompleta
no equivale al historial completo.

Cada ficha permite desplegar las publicaciones coincidentes: enlace, título,
fecha, vistas, duración ISO 8601 e idioma de audio declarado; los valores ausentes
se indican como no disponibles. Los datos se consultan de nuevo en cada búsqueda,
sin guardar estadísticas históricas. El orden sigue siendo vistas totales del
canal y después suscriptores por defecto; puede elegirse el orden por publicaciones
coincidentes descrito abajo. No hay una puntuación de crecimiento inventada.


## Priorizar publicaciones recientes

Seleccionar **Vistas de publicaciones coincidentes recientes** en Orden de los
canales (`sort_by: matching_publication_views`) y un periodo de publicación.
El botón **Ejemplo: 3 videos / 100 mil vistas / 30 días** configura últimos 30 días,
100000 vistas por publicación, mínimo tres coincidencias, muestra de 20 y
descubrimiento por publicaciones recientes; retira
los límites de vistas totales y antigüedad del canal, conservando los demás filtros.

La clasificación suma los contadores actuales de las publicaciones distintas que
cumplen todos los filtros. Una publicación anterior al periodo no aporta vistas a
esta suma. Después ordena por suscriptores en los empates, tanto para un tema como
para un lote. Se mantiene el último registro completo al deduplicar canales. Si
falta cualquier contador coincidente, la suma se marca desconocida y queda detrás
de las sumas conocidas; nunca se convierte en cero ni en una suma parcial.

Es una comparación de publicaciones de la muestra, no de todo el historial ni de
vistas ganadas durante el periodo. El descubrimiento de candidatos sigue usando
el índice seleccionado: cambiar solo el orden no amplía la cobertura ni demuestra que
se encontraron los canales con mayor crecimiento en YouTube. Se conserva el orden
por vistas totales como opción predeterminada (`sort_by: channel_views`).


## Descubrimiento desde publicaciones recientes

En **Descubrir canales a partir de**, elegir **Publicaciones recientes con muchas
vistas** (`discovery_mode: recent_publications`) junto con una fecha de publicación.
Para temas, se consulta `search.list` con `type=video`, `order=viewCount` y la ventana
RFC 3339. Se recuperan los metadatos reales de los videos y se verifican idioma,
fecha, vistas, duración y exclusión de directos. Sus canales se deduplican y pasan
por todos los filtros de canal y por la revisión de publicaciones recientes.

Los resultados siguen siendo canales. Un solo video descubierto no satisface un
mínimo de varias coincidencias: este mínimo se comprueba en la muestra de subidas.
Un video encontrado por el índice puede haber salido ya de esa muestra; no se
mezclan conjuntos para inflar las coincidencias. Las páginas limitan videos
candidatos (hasta 50 por página), de los que pueden salir menos canales distintos.
La fecha de búsqueda corresponde a publicaciones, no a creación del canal; el
filtro opcional de edad del canal se comprueba después con sus propios metadatos.

`discovery_mode: channels` conserva el comportamiento anterior. Para @usuarios,
IDs y enlaces concretos se mantiene la consulta directa, sin buscar videos para
identificar al propietario. El campo `scope.candidate_discovery` indica el método
real usado. Los lotes conservan ese alcance por tema completado.

El índice puede retrasarse, omitir coincidencias o devolver menos resultados con
orden y fecha. No hay una clasificación exhaustiva, una garantía de viralidad, ni
una certificación de ingresos. No se guardan estadísticas históricas ni se crean
tareas recurrentes.

Referencia oficial revisada el 14 de noviembre de 2026:
https://developers.google.com/youtube/v3/docs/search/list
