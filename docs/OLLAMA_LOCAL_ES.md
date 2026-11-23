# Ollama local sin inferencia

Preparación del issue #27, 2026-11-23. El servicio y los pesos son locales y no requieren una API de pago. No equivale a validar al director del agente.

Se conserva el ZIP oficial Ollama v0.40.17 Windows amd64, SHA256 `3dd80f6e3a9699f2eadf4ac418f00529cee594df9557541806eda1f1f3f5588a`, coincidente con el digest del [release oficial](https://github.com/ollama/ollama/releases/tag/v0.40.17).

El GGUF existente Qwen3-8B-Q4_K_M (5027783488 bytes) tiene SHA256 `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785`, coincidente con los metadatos LFS oficiales de [Qwen/Qwen3-8B-GGUF](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/7c41481f57cb95916b40956ab2f0b139b296d974). Licencia Apache-2.0. El original se conserva; no se descarga otra copia del modelo.

`scripts/start_local_ollama.py --executable <ruta-absoluta-ollama> --models-dir <almacén-absoluto>` arranca únicamente `serve`. Usa loopback 127.0.0.1, `OLLAMA_NO_CLOUD=1`, contexto 4096 y un modelo cargado como máximo. Variables limitadas al proceso hijo; no cambia PATH, Python ni preferencias de aplicaciones. Si ya responde un servidor, no lo reemplaza ni afirma conocer su configuración. Guarda un log nuevo y distingue solicitar nube desactivada de comprobarlo en el log.

El helper no importa ni ejecuta modelos. La importación independiente sigue el [Modelfile oficial](https://docs.ollama.com/import), con `FROM` apuntando al GGUF local y `ollama create`. No se usa `pull`, cuantización, chat ni generate. La copia operativa queda en un almacén separado del original. [Configuración oficial sin nube](https://docs.ollama.com/faq).

Pruebas sintéticas verifican conservación de servicio existente, entorno del hijo, rutas/puerto y error de arranque; no abren modelos. La validación nativa consulta versión, tags, show y ps. Un registro de modelo no acredita inferencia, uso de herramientas, ajuste RAM/VRAM ni calidad. No se ejecuta producción, benchmark ni publicación de contenido.

## Resultado nativo

Importación oficial terminada correctamente como `openmontage-qwen3-8b:q4_k_m-local`. Tags/show identifican Qwen3 8.2B Q4_K_M, contexto operativo `num_ctx 4096` y capacidades declaradas `tools`, `thinking`, `completion`. El digest del manifiesto de Ollama es `62baa8d58c698816ef8571a2856edfed6e48372d0af5bbe85d5bb7ae328dbdeb`; es distinto de la huella del GGUF porque identifica otro objeto.

Studio devuelve `ollama_ready: true` e `inference_verified: false`. Tras comprobar cola vacía e inactiva, se respaldó settings y se añadió únicamente el modelo al campo antes vacío usando la API existente. Las demás opciones se compararon y conservaron; applications.json sigue idéntico. `/api/ps` devuelve `models: []`: ningún modelo cargado. La nube desactivada se comprobó en el log del servicio. No se ejecutaron chat, generate, tool calling ni evaluaciones de rendimiento. No se afirma comprobación visual nueva del panel.
