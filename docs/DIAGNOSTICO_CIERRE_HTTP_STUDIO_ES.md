# Studio: cierre con SSE y lecturas HTTP incompletas (#92)

24 de noviembre de 2026, hora de Cancún; pruebas hasta 25-11-2026 UTC.
Base: `badfae3cf567ebb964607aaf19f0db79cdd8916b`.

## Resultado y alcance

Se corrigió una causa reproducible de cierre retenido: Uvicorn espera que
terminen las conexiones antes de enviar el evento de cierre del lifespan.
Los streams SSE de biblioteca y proyecto seguían esperando notificaciones
indefinidamente mientras el navegador permanecía conectado. Cancelar el watcher
en el lifespan no podía resolver esa espera anterior.

`StudioServer.shutdown` avisa primero al `ChangeHub` y después delega el drenaje
normal a Uvicorn. El hub despierta también colas llenas y suscripciones tardías;
ambos generadores terminan y liberan la suscripción. No se fuerza la salida,
no se mata ningún trabajo y no se cambia ningún timeout. El comando conserva
el tratamiento normal de SIGINT y los códigos de error de inicio.

Esto no demuestra que todo bloqueo histórico de Ctrl+C tuviera esa causa.
No se reprodujo selección de texto/QuickEdit ni una tecla física en PowerShell.

**Los cortes HTTP siguen sin causa raíz confirmada y no se declaran corregidos.**
Una respuesta con cabeceras 200 puede quedarse en 65.280 de 91.055 bytes y
terminar en timeout del cliente; la evidencia previa también contenía WinError
10054. No son códigos de error idénticos. Los controles acotan el problema,
pero no identifican todavía si el origen es transporte, runtime o entorno.

## Evidencia focalizada

Entorno reutilizado: Python 3.11.9, Uvicorn 0.54.0, FastAPI 0.165.0,
Starlette 1.10.0, AnyIO 4.16.0, h11 0.16.0. Sin instalaciones.
Cada servidor empleó proyectos/configuración vacíos y JSON textual sintético
en `.runtime/qa`, puerto efímero diferente de 4750 y procesos propios.
No se llamó `configured_environment`, no se buscaron ejecutables ni se accedió
a D:. Ningún medio, modelo, inferencia o render intervino.

| Control | Observación |
|---|---|
| Uvicorn anterior, dos SSE abiertos y SIGINT | Inicia cierre y espera conexiones; al cerrar clientes termina |
| Evento nativo Windows Ctrl+C, servidor anterior | Sigue vivo después de 2,016 s; clientes cerrados después para limpieza |
| Evento nativo Windows Ctrl+C, servidor corregido | Clientes aún abiertos; proceso termina normalmente, código 0, lifespan completo |
| Última prueba nativa corregida | Puerto 64682; 36 lecturas completas, cierre observado en 0,047 s después de volver del emisor del evento |
| Sin SSE | Un fallo HTTP entre 34 lecturas: SSE no es requisito para el corte |
| Sin middleware BaseHTTP de caché | Tres fallos entre 16 lecturas: no justifica cambiar caché/middleware |
| Respuesta JSON ASGI mínima fuera de rutas del editor | Dos fallos entre 24 lecturas: no requiere leer ni editar un proyecto real |
| Selector explícito en Uvicorn, solo diagnóstico | 36 lecturas completas; una muestra no acredita solución ni permite cambiar el runtime |
| Traza de envíos Proactor en servidor aislado | Fallos de cliente pese a que las operaciones WSASend observadas notificaron los bytes completos |
| `http.server` y streams asyncio independientes | 12 lecturas completas por control; no permite atribuir el problema a toda la red o a Python en general |

Los fallos son intermitentes: también hubo ejecuciones Proactor sin fallos.
`Connection: close` explícito **no es una corrección**: vuelve a fallar en los
controles. urllib ya fuerza ese valor en el transporte, incluso si el llamador
solicita keep-alive. Las etiquetas de cabecera del informe describen la solicitud
del llamador, no prueban conexiones persistentes reales. No se probó una sesión
HTTP/1.1 reutilizada mediante un cliente que la soporte.

Un primer intento de comparar Selector cambiando solo la política global no
cambió el bucle que Uvicorn crea explícitamente. Solo el caso
`http-actual-selector` fuerza `asyncio:SelectorEventLoop`; los anteriores no se
usan como evidencia de Selector. No se cambió el bucle del producto.

37 pruebas focalizadas: `test_studio_shutdown.py` y `test_server.py`, 3,23 s.
Comprueban cierre de colas y generadores reales, suscriptores llenos/tardíos,
orden aviso→drenaje, error de inicio y regresiones HTTP existentes.
Se reutilizó pytest de `.runtime/qa/venv` con las dependencias de Studio desde
`.venv`, mediante `sys.path` solo en el proceso de prueba; ningún entorno cambió.
Aviso previo de pytest-asyncio sobre configuración de loop pendiente, sin fallo.
No se ejecutó una suite completa local.

Informe resumido: [JSON de evidencia](EVIDENCIA_CIERRE_HTTP_STUDIO_20261124.json).
Logs y cuerpos detallados permanecen en `.runtime/qa/http-*`, sin publicar
rutas personales ni archivos de configuración.

## Reproducción optativa, aislada

El script crea un directorio nuevo bajo `.runtime/qa`; no reutilizar una ruta.
El modo normal emplea el servidor corregido; `--baseline` usa Uvicorn sin el
aviso previo. Configuración, proyectos y endpoints `__qa` son exclusivos del
proceso de diagnóstico: no se añaden al servidor de Studio normal.

```powershell
$env:QA_CONSOLE_SIGINT = '1'
.venv\Scripts\python.exe -B scripts/validate_studio_transport.py probe C:\OPENMONTAGE-IA\.runtime\qa\http-caso-nuevo
$probeExitCode = $LASTEXITCODE
Remove-Item Env:QA_CONSOLE_SIGINT
exit $probeExitCode
```

Windows: crea consola NUEVA y oculta. El emisor se conecta solo a esa consola,
comprueba sus procesos y envía `CTRL_C_EVENT`; no se conecta a la consola de
4750 ni emite una señal global de la sesión. Sin esa variable usa SIGINT real
inyectado por `signal.raise_signal` en el loop del hijo, claramente etiquetado.
El emisor desasocia únicamente su propia consola antes de `AttachConsole`:
Microsoft documenta que ERROR_ACCESS_DENIED también significa «ya asociado»,
no demuestra una denegación de permisos sobre el servidor.

El código de salida del script es distinto de cero si alguna lectura HTTP
falla o si el servidor no termina con los clientes abiertos. El código del
proceso servidor se informa aparte. Un cierre correcto no oculta un corte HTTP.
La limpieza se limita a los procesos propios registrados por la prueba.
Variables `QA_NO_BASE_MIDDLEWARE`, `QA_RAW_ASGI`, `QA_SELECTOR` y `QA_TRACE_SEND`
son controles experimentales del script, nunca opciones de configuración del
producto; la última observa métodos internos de Proactor solo en el hijo.

## Límites y siguiente diagnóstico

PID 78256 y su fecha de creación se conservaron. **No carga esta nueva
corrección mientras siga ejecutándose**; no se reinició ni se recargó.
Proyecto original y settings/applications mantienen SHA256 de la evidencia
anterior. No se afirma validación visual, escucha ni exportación.

El siguiente paso HTTP mínimo es capturar una lectura incompleta con trazas
del protocolo/cierre y un cliente persistente real, comparando un único
parámetro por vez. Mantener fixture textual y servidor aislado. No aumentar
timeouts, añadir reintentos automáticos a escrituras ni cambiar Selector,
dependencias o configuración sin identificar la causa. Una recepción parcial
no demuestra pérdida/corrupción del proyecto guardado.

Fuentes primarias de interpretación:
[Uvicorn: bucles](https://github.com/Kludex/uvicorn/blob/main/docs/concepts/event-loop.md),
[Uvicorn: cierre](https://github.com/Kludex/uvicorn/blob/main/docs/server-behavior.md),
[Microsoft AttachConsole](https://learn.microsoft.com/en-us/windows/console/attachconsole).
El código instalado y las pruebas anteriores fijan las versiones y el
comportamiento realmente observado; la documentación web no sustituye esa prueba.
