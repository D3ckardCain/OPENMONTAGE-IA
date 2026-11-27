# Banco inicial de evaluación real del agente (ES/EN)

Issue #160. Este paquete separa definiciones de casos y recibos de evaluación de los unit tests y de los fixtures de implementación.

## Estado

El banco define 3 casos de smoke y 5 hold-out en español e inglés. Los casos contienen objetivos y comprobaciones deterministas; no incorporan medios reales, prompts de producción, datos personales ni resultados inventados. `scripts/agent_eval.py` valida el contrato de un recibo y resume resultados observados. No llama Ollama, herramientas, renderizadores ni endpoints.

Un recibo `real_model` exige nombre de modelo, cuantización, runtime y versión del prompt. Los resultados `synthetic_transport` y `fixture` se reportan separados y nunca cuentan como éxito real. El resumen calcula tokens, latencia p50/p95 por muestra medida, RAM/VRAM máximas, llamadas redundantes y efectos duplicados identificables por idempotency key; valores desconocidos permanecen nulos.

## Ejecución

Validar el catálogo sin ejecutar el modelo:

```powershell
.\.venv\Scripts\python.exe -B scripts\agent_eval.py
```

Tras una ejecución autorizada del agente, guardar cada recibo JSON fuera del repositorio de código y pasar sus rutas:

```powershell
.\.venv\Scripts\python.exe -B scripts\agent_eval.py .\run-es.json .\run-en.json
```

`passed` en un recibo `real_model` requiere que todos los checks del caso estén presentes como booleanos. La CLI valida y resume el registro; no certifica por sí sola la veracidad de artefactos. Cada checker debe contrastarse con el estado/recibo o artefacto local indicado, y la muestra humana queda separada. No incluir brief, transcripción, prompt completo, cookies, tokens ni rutas personales en el registro publicado.

## Casos

La fase `smoke` son candidatos para la primera línea base (selección segura de herramienta, recurso ausente, no afirmar escucha/render). `held_out` se conserva para validar generalización, sin ajustar prompts a sus contenidos. Las descripciones son esquemáticas, no autorizan una llamada real.

## Límites actuales

No hay inferencias reales ejecutadas: la última consulta local a Ollama agotó el timeout. No se registran calidad creativa, naturalidad, escucha o render sin pruebas propias. El esquema no crea evidencia ni mide RAM/VRAM automáticamente; esos valores los debe aportar instrumentación observada. #160 sigue abierto hasta capturar tres casos de smoke con modelo/runtime/prompt y artefactos verificados, y después expandir la muestra en ES/EN.
