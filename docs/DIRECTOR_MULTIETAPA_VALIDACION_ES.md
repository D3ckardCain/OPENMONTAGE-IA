# Validación sintética del transporte multietapa

Seguimiento #41 y #3; rama `feat/local-agent-research-foundation`, PR #2 en borrador.
Se reutilizan `LocalAgent.chat`, `LocalAgent.dispatch`, checkpoints, instrucciones y
FreeCAD.Units existentes. No hay un guion creativo ni decisiones de etapas en Python.

## Persistencia y recuperación

`lib/agent_conversation.py` guarda `agent_session.json` versión 2 mediante el escritor
atómico existente de Studio: conversación, lote pendiente, índice de siguiente llamada,
instrucciones leídas y SHA256 de la solicitud. Guarda intención antes de despachar y
recibo antes de la siguiente acción. El resultado JSON completo, incluida procedencia,
llega como mensaje `tool` al siguiente turno; conserva `tool_call_id` cuando existe.

Al reanudar desde Studio, una instancia nueva recupera los recibos y ejecuta solamente
las llamadas pendientes. Relee las instrucciones guardadas por el validador existente
y comunica el estado/clarificaciones actuales después de completar el lote. No repite
las llamadas terminadas. Solicitud modificada bloquea la recuperación para revisión.
Sesiones antiguas se conservan en `agent_session_legacy.json`; no tenían recibos por
llamada y se vuelve a consultar el estado/checkpoints, sin reproducir sus llamadas.

Una intención sin recibo provoca `AGENT_SESSION_UNCERTAIN`. Puede haber ocurrido un
efecto externo antes de la interrupción: no se promete ejecución exactamente una vez.
Revisar artefactos, cola y recibos del motor antes de reconciliar manualmente esa sesión;
no borrar ni reintentar automáticamente. Un fallo al guardar tras ejecutar también
conserva esa intención incierta. Los errores de herramientas se transmiten al modelo
como errores; no se convierten en éxito ni disparan una alternativa automática.

La cancelación conserva el trabajo completado y se comprueba antes del modelo y entre
acciones. La continuación #42 añade cierre del transporte Ollama durante la petición;
véase [cancelación de inferencia local](CANCELACION_INFERENCIA_LOCAL_ES.md), que separa
cierre del cliente y evidencia del servidor. No cancela procesos externos o renders.
Una pausa de checkpoint
se registra como recibo y descarta las llamadas restantes del lote, con respuestas
explícitas de no ejecución. La aprobación humana sigue pasando por el control existente;
ninguna sesión guardada autoriza saltarse una etapa.

## Sonda disponible por Studio

`POST /api/studio/agent/probe-multistep` con `{}` ejecuta **dos inferencias textuales
sintéticas locales**. GET, parámetros libres y orígenes externos se rechazan. No es una
sonda pasiva ni se ejecuta desde bootstrap. Reservará la tarea local y rechazará trabajos
activos/modelos cargados. Reutiliza el modelo seleccionado, comprobado local y con tools;
no descarga pesos ni admite cloud/fallback. Contexto 4096, salida máxima 256 tokens por
petición, pensamiento desactivado cuando se admite, `keep_alive=0`.

Solo permite `execute_tool/freecad_units`: primero [1] in→mm, después los valores realmente
devueltos mm→cm. El segundo argumento se contrasta contra el primer recibo antes de
despachar. No puede elegir otra herramienta, proyecto, magnitud, ruta o generación.
El informe incluye digest del modelo, hashes de entradas/worker/transcripción, procedencia,
fecha, conteos separados de modelo y herramientas y descarga consultada en `/api/ps`.
La carpeta UUID diagnóstica se oculta de proyectos de producción y se elimina al finalizar;
el cliente debe conservar el informe, no se guardan transcripciones privadas en GitHub.
La sonda anterior `/agent/probe-tools` conserva su contrato de una sola llamada.

## Evidencias y alcance

- **Modelo y SDK reales:** Qwen3 `openmontage-qwen3-8b:q4_k_m-local`, digest
  `62baa8d58c698816ef8571a2856edfed6e48372d0af5bbe85d5bb7ae328dbdeb`, dos peticiones
  Ollama y dos ejecuciones FreeCAD 1.1.4: 1in→25.4mm→2.54cm. Observación local del
  24-11-2026 UTC, descarga verificada. SHA256 transcripción
  `abf3fa643e5a9cfee7157d8463ab2cce1155a476a1b7b5020c8a4d62e746c405`.
- **SDK real/modelo simulado:** cancelación después de la primera conversión y nueva
  instancia recuperando la segunda, conservando procedencia y sin nueva llamada al modelo.
- **Modelo simulado/persistencia y checkpoints reales:** avance de etapa, artefacto
  conservado, pausa guiada y aprobación explícita de la fixture; sin medios ni render.
- **Simulaciones de fallos:** timeout del modelo/worker, argumentos JSON inválidos,
  lotes malformados/excesivos, error de validación, cancelación antes del modelo,
  interrupción tras intención y rechazo de repetición incierta.

Pruebas: `tests/tools/test_agent_conversation.py`, `test_local_agent_probe.py` y
`tests/backlot/test_production_studio.py`. CI no ejecuta Ollama. La prueba nativa opcional
se omite si falta FreeCAD preparado; no lo instala. Regresión local: 71 aprobadas,
1 omitida (contrato de exportación que requiere FFmpeg en PATH de ese proceso).

Esta evidencia valida transporte y recuperación acotados. No acredita dirección creativa,
planificación libre de muchas etapas por el modelo real, revisión editorial real, contexto
32768, rendimiento sostenido ni calidad de audio/vídeo. La continuación #42 documenta
la prueba posterior de cancelación durante inferencia textual real y sus límites.
Costo $0; sin mapas, geometría, animación ni contenido
real. Originales, configuraciones, `.venv` y Python de ComfyUI conservados.
