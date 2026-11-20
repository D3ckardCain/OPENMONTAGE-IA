# Buscador de canales: YouTube Data API

La búsqueda utiliza el cliente oficial de YouTube Data API v3, sin scraping ni servicio de pago alternativo. La clave se introduce desde «Configurar YouTube Data API» en /channels. Se conserva en memoria hasta cerrar el servidor; no se devuelve al navegador ni se escribe en disco. También se admite YOUTUBE_API_KEY para configuraciones locales existentes. Olvidar la clave de sesión no borra la variable del entorno. Guardar una clave no acredita su validez: se comprueba al consultar.

La selección inicial descubre canales a partir de publicaciones de los últimos 30 días y conserva suscriptores como criterio secundario. Las vistas son acumuladas de publicaciones recientes, no necesariamente vistas ganadas durante esos 30 días. El filtro de creación del canal sigue siendo independiente. Se conservan consultas directas por ID, usuario y enlace, consultas de hasta cinco temas y filtros sobre la muestra reciente. No existe cobertura global de todos los canales.

«Prever solicitudes sin buscar» valida los temas y filtros aplicados y calcula límites superiores de solicitudes a search, channels, playlistItems y videos, sin clave ni tráfico a YouTube. No mide el saldo de la cuota del proyecto. El límite de solicitudes del lote solo aplica al endpoint de varios temas. La previsión se borra al cambiar tema o aplicar filtros para evitar mostrarla como si correspondiera a otra consulta.

Referencia oficial de cuotas, consultada el 19 de noviembre de 2026: https://developers.google.com/youtube/data/determine_quota_cost . La documentación vigente distingue el bucket de Search Queries de las unidades de otras lecturas. Los límites del proyecto real deben consultarse en su consola; la app no promete un número fijo de búsquedas restantes ni aumenta cuota con otras claves.

No se presentan RPM, ingresos o monetización real de canales ajenos. Vistas por día sería una métrica derivada propia, no un campo oficial: no se añade en esta fase. Los agregados de muestra ya existentes tampoco equivalen a medidas oficiales de crecimiento. La implementación de nuevas métricas derivadas debe revisar el permiso aplicable del proyecto, sin afirmar que ya existe aprobación: https://developers.google.com/youtube/terms/developer-policies-guide y https://developers.google.com/youtube/terms/derived-metrics-policy .

Las comprobaciones usan transportes simulados. No se suministró ni utilizó una clave real durante el desarrollo de esta fase, y no se guardan resultados anteriores como alternativa cuando falla la API.
