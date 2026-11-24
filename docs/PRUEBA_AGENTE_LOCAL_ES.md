# Prueba sintética del protocolo de herramientas local

Seguimiento #32/#2/#27. Esta prueba demuestra una llamada acotada de Ollama al puente real `LocalAgent.dispatch`, no un director autónomo de producción.

Studio expone `POST /api/studio/agent/probe-tools` con `{}`. Es una acción explícita que **ejecuta inferencia textual sintética local**: pide únicamente una llamada `execute_tool` para convertir 1 pulgada a milímetros mediante FreeCAD. No admite prompts, rutas, modelos o herramientas arbitrarios. No se ejecuta desde GET, bootstrap o diagnóstico pasivo. Las pruebas de CI simulan el modelo y la herramienta; no llaman a Ollama ni GPU.

Usa el modelo ya seleccionado en Studio y HTTP loopback, verifica modelo local instalado/capacidad tools y rechaza modelos remotos/cloud. Rechaza tareas activas y modelos ya cargados. Reserva la tarea local para evitar que producción, análisis o ajustes compitan durante la prueba. No cambia el modelo, sus pesos ni las opciones persistidas. La solicitud tiene contexto 4096, máximo 128 tokens, keep_alive=0 y pensamiento desactivado si el modelo lo admite. Los valores de producción existentes se conservan; estas opciones afectan solo la petición de diagnóstico.

Solo se acepta una llamada con nombre y argumentos idénticos a la fixture. Se valida antes del despacho; cualquier desviación termina sin ejecutar herramientas. La conversión nativa usa el FreeCAD registrado, sin GUI/documentos/geometría. La fixture temporal vive en una carpeta UUID propia dentro de projects y se elimina al finalizar; no se borran proyectos existentes. La liberación del modelo se consulta con `/api/ps` y se informa aparte: no se presume de keep_alive.

La respuesta contiene resultado, unidades, digest del manifiesto local, hashes del probe y conversión, fecha UTC, límites de contexto/salida y descarga verificada. La documentación de [chat y herramientas de Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md) define tool_calls, think y keep_alive. No se envían datos reales o privados a un proveedor externo ni se usa alternativa de pago.

## Resultado físico observado

Qwen3-8B-Q4_K_M local devolvió una llamada válida al descriptor fijo y el puente ejecutó FreeCAD.Units: 1in → 25.4mm. El digest del manifiesto es `62baa8d58c698816ef8571a2856edfed6e48372d0af5bbe85d5bb7ae328dbdeb`; versión FreeCAD 1.1.4. `/api/ps` confirmó models=[] al terminar. La prueba inicial de protocolo usó 201 tokens de entrada y 28 de salida; es una observación única, no un benchmark. Los archivos de configuración de Studio permanecieron idénticos.

Quedan sin acreditar el catálogo completo de herramientas, contexto largo, planificación multietapa, recuperación editorial, calidad creativa y rendimiento sostenido RAM/VRAM. El transporte de producción conserva su contexto previo; una prueba con 4096 tokens no demuestra que una petición de 32768 se ajuste al equipo. No se ejecutó audio, imagen, vídeo, render o publicación de contenido.
