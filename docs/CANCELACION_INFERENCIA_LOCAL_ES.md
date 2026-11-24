# Cancelación de inferencia local desde Studio

Seguimiento #42, vinculado a #3 y continuación de #41. Prueba textual sintética;
no certifica dirección creativa ni genera contenido audiovisual.

## Qué se corrigió

Antes, `stop` marcaba un Event que se comprobaba entre acciones. Una petición
Ollama en curso podía seguir esperando hasta su timeout180s. Ahora `LocalAgent.chat`
usa el mismo HTTP local con una extensión cancelable: un vigilante del Event hace
`shutdown` del socket propio; el hilo de la petición termina la lectura y cierra
respuesta/conexión. No queda un trabajador HTTP separado inferiendo en segundo plano
del cliente. El vigilante se termina al cerrar la petición. No se mata Ollama, su
runner, procesos del usuario ni renders previamente enviados.
Antes de disponer de un socket, la resolución/conexión puede seguir dependiendo del
timeout; las pruebas cubren espera de cabeceras y lectura durante inferencia.

Se mantiene `stream:false` para producción, sus opciones32768/8192 y keep_alive0.
La ruta de diagnóstico utiliza streaming textual sin herramientas para observar
fragmentos antes de cancelar. Tiene límites de línea64KiB, respuesta16MB y timeout;
no sigue redirecciones ni proxies, y solo permite los hosts loopback existentes.
Streaming no admite herramientas ni fragmentos de llamadas a funciones.

`agent_session.json` conserva intentos de modelo con estado running/completed/
cancelled/error e indicios de transporte. Una interrupción del proceso deja un
intento `interrupted_unknown` al recuperar: no se presume cancelación del servidor.
Un resultado parcial cancelado no se agrega como respuesta válida ni se despacha.
Los recibos de herramientas anteriores permanecen y no se vuelven a ejecutar.
Se corrigió además la mutación del contexto inicial que podía duplicar mensajes al
reutilizarlo para recuperar. Las fixtures se rechazan en el inicio de producción
normal; solo pueden seguir por su diagnóstico acotado.

## Tres evidencias distintas

1. `stop` devuelve requested: se ha solicitado la parada; todavía no es un resultado.
2. `transport_closed` y `socket_shutdown_requested`: el cliente cerró su conexión.
   Por sí solos **no** acreditan que el backend dejó de inferir.
3. La sonda consulta `/api/ps` después, durante hasta15s y con una reserva exclusiva
   de Studio. `model_unloaded_verified` acredita ausencia de modelos cargados en
   esa consulta. La evidencia se etiqueta `no_models_loaded_after_exclusive_request`.
   Si falta, se informa `not_verified`, y la sonda no autoriza su recuperación.

La evidencia de transporte siempre mantiene `server_inference_stopped:not_verified`:
no contiene un acuse explícito del servidor. La descarga observada se registra aparte.
No se afirma un instante exacto del último token/kernel ni una garantía universal de
cancelación por desconexión. El código oficial de [Ollama0.40.17](https://github.com/ollama/ollama/blob/v0.40.17/server/routes.go)
propaga el contexto HTTP a Completion/Chat; eso fundamenta el mecanismo esperado,
pero no sustituye la observación del backend instalado. `/api/ps` no es un contador
universal de solicitudes activas. Un cliente externo podría competir fuera de Studio.

## Uso explícito y recuperación

- `POST /api/studio/agent/probe-cancellation` con `{}` devuelve project_id, status_url
  y stop_url. No acepta prompts/modelos/rutas arbitrarios; rechaza origen externo.
- `GET status_url` permite observar estado y `transport.content_chunks` sin ejecutar
  inferencia. Esperar fragmentos y `done_received:false` distingue inferencia textual
  observada de una mera carga. `bootstrap` sigue disponible y oculta esta fixture.
- `POST stop_url` con `{}` usa el control normal de Studio
  `/api/studio/projects/{pid}/stop`. Cerrar la pestaña o dejar de consultar no equivale
  a esa acción ni garantiza cancelar el backend.
- Esperar `status:stopped`, `active:false`, recibos intactos y descarga verificada.
- `POST status_url/resume` con `{}` recupera la sesión y hace una petición sintética
  de hasta16 tokens. No vuelve a ejecutar la herramienta completada. Rechaza otros
  proyectos, estados no reanudables, recibos modificados y tareas concurrentes.

Se reutiliza la preparación de modelo del probe existente: local instalado,
digest/capacidad tools, sin modelos cargados ni tareas activas; cloud/fallback se
rechazan. La sonda primero conserva un recibo FreeCAD.Units real1in→25.4mm usando
un mensaje de modelo **simulado** explícito. Después ejecuta Qwen real, contexto4096,
máximo512 tokens y pensamiento desactivado si lo admite. No existe generación de
geometría. La recuperación usa Qwen real, máximo16 tokens. No cambia configuración,
pesos, entornos ni versiones. Conserva JSON de diagnóstico bajo un proyecto UUID
oculto; esos archivos, los entornos y las configuraciones no se publican en GitHub.

Las evidencias del intento anterior se guardan en previous_result; una petición nueva
reinicia los indicadores de descarga/transporte para evitar mostrar resultados
anteriores como comprobaciones actuales. Una herramienta con intención sin recibo
sigue bloqueada por `AGENT_SESSION_UNCERTAIN`; no se repite automáticamente.

## Resultado local observado

24-11-2026 UTC, Ollama0.40.17 y Qwen
`openmontage-qwen3-8b:q4_k_m-local`, digest
`62baa8d58c698816ef8571a2856edfed6e48372d0af5bbe85d5bb7ae328dbdeb`.
Se observaron5 fragmentos reales antes de stop. Respuesta al stop≈0.015s; estado
terminal y descarga consultada≈0.125s después de solicitarlo. Son mediciones de
una ejecución, no un benchmark ni un SLA. Socket cerrado, done:false, sesión stopped
y recibo intacto. La recuperación real terminó y conservó exactamente una llamada
nativa; hash de recibos antes/después
`2759f1546c0cebe377bc7a869ee2506e3b7d74cfa79897b0f90bcf430ef135e9`.
Ollama siguió sirviendo y quedó sin modelos cargados al terminar. No hubo cancelación
por matar el servicio. Las correcciones de campos de estado se verifican aparte con
la fixture offline; el informe físico original conserva el hash de la sonda usada.

Pruebas offline: sockets reales contra servidor HTTP simulado (antes de cabeceras,
durante stream, timeout, JSON normal, truncamiento, tamaño excesivo, redirección,
cancelación previa); ciclo API de Studio con modelo/SDK simulados; persistencia y
recuperación sin repetir recibos. CI no ejecuta Qwen. Archivos:
`tests/tools/test_cancellable_http.py`, `test_local_inference_probe.py`,
`test_agent_conversation.py` y regresiones existentes.

No se acredita la cancelación de render, procesos CAD, herramientas externas o llamadas
remotas. Una parada sin descarga comprobada requiere revisar el servidor, sin matar
procesos ni repetir herramientas a ciegas. Costo$0; originales, configuraciones,
`.venv` y Python de ComfyUI conservados. PR#2 sigue en borrador y no se fusiona.
