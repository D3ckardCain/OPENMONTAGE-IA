# Descubrimiento dirigido de herramientas

Seguimiento #33/#3. `GET /api/studio/tools` conserva su respuesta original: herramientas locales permitidas y su estado. Para consultar una conexión concreta sin sondear el resto del catálogo:

- `/api/studio/tools?name=freecad_units`
- `/api/studio/tools?capability=geographic_coordinate_analysis`

Los filtros son opcionales, exactos y combinables (intersección), con longitud máxima 100 caracteres. Un nombre/capacidad desconocido devuelve lista vacía. La restricción a herramientas locales y no publicadoras se mantiene. No introduce activación, descarga, ejecución, caché de disponibilidad o autorización de contenido.

El filtro se aplica antes de `get_status`: las herramientas excluidas no consultan sus runtimes. La carga inicial de módulos del registro aún existe; no se promete latencia máxima para el primer descubrimiento ni que el estado de una herramienta seleccionada sea siempre instantáneo. La operación seleccionada conserva su diagnóstico real; no se reemplaza por un estado optimista.

El agente ya dispone de `list_tools` por capacidad y `tool_info` para leer el contrato de una herramienta. Este cambio extiende esa selección dirigida a clientes HTTP de Studio. Las pruebas de API comprueban que el estado de herramientas excluidas y proveedores remotos no se consulta, que el formato por defecto se conserva y que filtros cruzados desconocidos devuelven vacío.
