"""Safe, bounded diagnostics. Never retain provider messages, URLs or keys."""
import json

MESSAGES = {
    'REQUEST_BUDGET_EXCEEDED': ('Se alcanzó el límite de solicitudes del lote. Revisa los temas pendientes antes de continuar.', False),
    'MISSING_KEY': ('Falta configurar la clave local de YouTube API.', False),
    'INVALID_KEY': ('YouTube rechazó la clave. Revisa la clave local configurada.', False),
    'API_DISABLED': ('La API de YouTube no está habilitada para esta clave. Revisa su proyecto de Google.', False),
    'QUOTA_EXCEEDED': ('La cuota de YouTube se agotó. Espera a que se restablezca antes de repetir la búsqueda.', False),
    'RATE_LIMITED': ('YouTube limitó temporalmente las solicitudes. Espera antes de volver a intentar.', True),
    'ACCESS_DENIED': ('YouTube denegó el acceso. Revisa las restricciones y permisos de la clave.', False),
    'NETWORK_ERROR': ('No se pudo conectar con YouTube. Comprueba la conexión a Internet.', True),
    'TIMEOUT': ('YouTube tardó demasiado en responder. Intenta más tarde o reduce la búsqueda.', True),
    'SEARCH_TOO_BROAD': ('La búsqueda superó su tiempo disponible. Reduce páginas o filtros.', False),
    'UPSTREAM_ERROR': ('YouTube tiene un fallo temporal. Intenta más tarde.', True),
    'UPSTREAM_REQUEST_INVALID': ('YouTube rechazó los parámetros de la consulta. Revisa los filtros.', False),
    'RESOURCE_UNAVAILABLE': ('El canal o recurso solicitado no está disponible en YouTube.', False),
    'INVALID_RESPONSE': ('YouTube devolvió una respuesta no válida. No se usan resultados anteriores.', True),
    'UNKNOWN_ERROR': ('No se pudo completar la consulta. No se usan resultados anteriores.', False),
}


def classify_http_error(status, payload):
    """Only exact allowlisted reason tokens influence public diagnostics."""
    reasons = set()
    if isinstance(payload,dict):
        error = payload.get('error',{})
        if isinstance(error,dict):
            for group in ('errors','details'):
                items=error.get(group,[])
                if isinstance(items,list):
                    for item in items:
                        if isinstance(item,dict) and isinstance(item.get('reason'),str):
                            reasons.add(item['reason'])
    if reasons & {'quotaExceeded','dailyLimitExceeded','dailyLimitExceededUnreg'}:
        return 'QUOTA_EXCEEDED'
    if status==429 or reasons & {'rateLimitExceeded','userRateLimitExceeded'}:
        return 'RATE_LIMITED'
    if reasons & {'keyInvalid','API_KEY_INVALID','API_KEY_EXPIRED'}:
        return 'INVALID_KEY'
    if reasons & {'accessNotConfigured','SERVICE_DISABLED'}:
        return 'API_DISABLED'
    if status in (401,403):return 'ACCESS_DENIED'
    if status==404:return 'RESOURCE_UNAVAILABLE'
    if status>=500:return 'UPSTREAM_ERROR'
    return 'UPSTREAM_REQUEST_INVALID'


def read_http_error(error):
    try:
        raw=error.read(65537)
        payload=json.loads(raw) if len(raw)<=65536 else {}
    except Exception:
        payload={}
    finally:
        error.close()
    return classify_http_error(error.code,payload)
