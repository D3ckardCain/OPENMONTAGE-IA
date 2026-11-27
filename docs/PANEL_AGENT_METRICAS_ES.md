# Métricas de uso del agente en Producción

Los intentos de Ollama pueden emitir un evento `model_usage` en el registro del
trabajo. El panel existente muestra contadores de prompt/respuesta y duraciones
solo cuando llegan en la respuesta local `/api/chat`. El evento conserva esos
valores estructurados bajo `ollama_usage`; no guarda el prompt ni su contenido.

Los tiempos se convierten de nanosegundos reportados por Ollama a milisegundos
para la etiqueta visible. Si el endpoint no incluye uso, no se muestra una
estimación basada en caracteres. Esto no mide RAM/VRAM, calidad ni comprensión,
y no completa el panel general de #167.


## Evitar doble envío de aprobación · #167

El panel desactiva temporalmente la acción mientras la solicitud está pendiente y descarta eventos de clic duplicados. El backend serializa la transición del checkpoint de aprobación y el inicio del trabajo, de modo que varias aprobaciones concurrentes producen una sola decisión y un solo inicio. La protección no afirma entrega exactamente-una-vez ante caídas del proceso: para una respuesta HTTP incierta se debe recuperar estado antes de reintentar.
