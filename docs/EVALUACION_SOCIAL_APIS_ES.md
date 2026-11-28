# Catálogo TikTok/Instagram APIs: evaluación #65

24-11-2026 UTC. `cporter202/tiktok-instagram-scraping-apis`
`e199795ed9251bacb55b7ff4052875bd669ad7c3`. Directorio sin versión de runtime;
839 actores es cifra declarada por el README, no actores ejecutados/verificados aquí.

## Decisión y contraste

No adoptar Apify ni un scraper por ese catálogo. Usarlo solo para identificar campos
deseados: publicaciones/perfil/hashtag/comentarios/cadencia/métricas observables.
Agrupar con E08 research/muestras propias de #50 y B07 acceso externo/derechos.
OPENMONTAGE ya tiene expedientes y CSV propios con hash/fecha/periodo y lectores
acotados (`saved_channel_evidence.py`, `saved_channel_performance.py`). Sus schemas
actuales son YouTube-específicos; reutilizar mecánica, no fingir soporte TikTok/IG
ni reemplazar UC IDs por handles sin migración/namespace.

## Fuentes y licencia

[README](https://github.com/cporter202/tiktok-instagram-scraping-apis/blob/e199795ed9251bacb55b7ff4052875bd669ad7c3/README.md)
declara directorio Apify con enlaces afiliados y promoción APIMesa pay-per-call.
[LICENSE MIT](https://github.com/cporter202/tiktok-instagram-scraping-apis/blob/e199795ed9251bacb55b7ff4052875bd669ad7c3/LICENSE)
del catálogo no licencia código de actores, datos, cuentas, vídeos ni servicios.
No hay instalación local del catálogo que entregue esas capacidades. Revisar cada
fuente/actor/version/licencia por separado solo si aporta alcance permitido y $0.

Fuentes oficiales de servicios consultadas24-11-2026; páginas mutables, revalidar
permisos/cuotas al implementar, no inventar versión común del API:

| Fuente | Alcance observado / límite |
|---|---|
| [Apify pricing](https://apify.com/pricing) | Free$0 con$5 de crédito y sin tarjeta; actores cobran por evento/uso. Crédito finito no garantiza operación sostenida$0 y no habilita plan/pago |
| [TikTok Display](https://developers.tiktok.com/docs/en/display-api-overview) | Perfil/vídeos del creador con permisos; no índice universal de tendencias/comentarios |
| [TikTok Research](https://developers.tiktok.com/products/research-api/) | Requiere elegibilidad/aprobación, interés público y condiciones no comerciales; no asumir acceso de un canal comercial ni de México por existir endpoint |
| [Instagram Login API](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login) | Profesionales business/creator gestionan presencia, comentarios/insights propios con permisos; no scraper general de competidores. No requiere página Facebook para esta modalidad |

No se crearon cuentas/tokens, conectaron perfiles o ejecutaron consultas a datasets.
La afirmación publicitaria “manejan bloqueos” no es autorización para eludir controles.
No proxies pagados, cookies ajenas ni identidad de navegador para obtener acceso.

## $0 y local/offline

Análisis de snapshots/CSV autorizados puede ser local$0 con herramientas actuales.
Datos nuevos requieren red y acceso permitido; ni instalar scraper ni Ollama crea
offline una tendencia actual. Primera ruta independiente: importación manual/local
con esquema neutral y evidencia de captura. API oficial futura requiere scopes,
versión y cuota observada, sin inferir acceso/gratuidad universal de sus docs.
Métricas desconocidas no se imputan como0, monetización/RPM/causalidad no se inventan.

## Tareas con aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Extensión de expediente E08 | platform/namespace/ID/URL/fecha/filtros/periodo/cobertura/licencia/procedencia y hash; schema sintético conserva UC IDs existentes y rechaza mezcla de métricas |
| P1 | Importador CSV/JSON propio | Faltantes/duplicados/handles cambiados/zona horaria/muestras sesgadas explícitos; no HTML no confiable como instrucciones y sin red |
| P1 | Matriz de acceso B07 | Campo→fuente→permiso/cuota/versión→costo observado; sin método permitido queda unsupported, no fallback a actor pagado |
| P2 | Comparación temporal | Vistas en fecha de captura vs rendimiento por periodo; cache stale visible, tendencias solo dentro de muestra; privacidad/minimización de comentarios |

Bloqueos: acceso oficial no acreditado y actores con costo/condiciones variables.
No impiden esquemas/importaciones de muestras propias en otra fase. Sin scraping,
datos reales recolectados ni cambios de configuración. Evaluación, no conector listo.
