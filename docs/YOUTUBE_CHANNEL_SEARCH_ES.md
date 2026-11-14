# Buscador de canales

En el panel de producciones, abrir **Buscador de canales** (`/channels`). Escribir
un tema, configurar filtros y pulsar **Buscar canales**. La clave de YouTube Data
API se configura en el entorno local del servidor; no se pide ni se envía desde
el formulario. Sin clave no se inventan resultados. Cada búsqueda consulta datos
actuales; no se almacena un inventario de estadísticas ni se recuperan resultados
anteriores cuando falla la consulta.

## Orden y filtros
El orden es fijo: vistas totales del canal descendentes; suscriptores públicos
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
- Vistas mínimas de una publicación de la muestra: distinto de vistas totales.
- Profundidad: 1–3 páginas de candidatos y 5, 10 o 20 publicaciones recientes.

Los filtros de contenido se evalúan **juntos en una misma publicación**. Basta
una coincidencia en la muestra para incluir al canal; no se afirma que todo el
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
