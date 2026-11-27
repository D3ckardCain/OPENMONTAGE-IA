# Métricas de uso real de Ollama

Cada intento local conserva, dentro de `model_attempts[].transport.ollama_usage`,
los campos que Ollama devuelve realmente en `/api/chat`: `prompt_eval_count`,
`eval_count` y las duraciones de carga, prompt, respuesta y total, cuando son
enteros no negativos dentro del límite de validación. No se estima el número de
tokens desde caracteres ni se inventan valores cuando la respuesta los omite.

La prueba usa una respuesta sintética interceptada; no conecta con Ollama ni
carga un modelo. Los contadores de Ollama describen ese intento y no equivalen a
una evaluación de calidad o comprensión del agente.
