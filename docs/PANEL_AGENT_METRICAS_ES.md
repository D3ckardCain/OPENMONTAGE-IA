# Métricas de uso del agente en Producción

Los intentos de Ollama pueden emitir un evento `model_usage` en el registro del
trabajo. El panel existente muestra contadores de prompt/respuesta y duraciones
solo cuando llegan en la respuesta local `/api/chat`. El evento conserva esos
valores estructurados bajo `ollama_usage`; no guarda el prompt ni su contenido.

Los tiempos se convierten de nanosegundos reportados por Ollama a milisegundos
para la etiqueta visible. Si el endpoint no incluye uso, no se muestra una
estimación basada en caracteres. Esto no mide RAM/VRAM, calidad ni comprensión,
y no completa el panel general de #167.
