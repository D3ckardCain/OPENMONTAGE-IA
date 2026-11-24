# Multica: evaluación #57

24-11-2026 UTC. `multica-ai/multica@92a4e450fb5c7d1de40cd5656772f47a22c62096`.
package raíz0.2.0 es metadato de workspace, no se equipara a release de contenedores.
Revisión estática; no instalar daemon, escritorio, agentes ni servicios.

## Decisión y existente

Mantener GitHub issues/PR/CI y flujo actual como fuente de seguimiento. Multica es
coordinación interna de desarrollo para equipos, no otra función audiovisual.
Su propio README orienta al desarrollador individual hacia un gestor local más
simple. No añadir PostgreSQL y otro tablero sin beneficio de traspaso medido.

OPENMONTAGE ya conserva trabajos, decisiones, checkpoints, recibos y reanudación
del agente de producción (`lib/production_agent.py`, `lib/agent_conversation.py`).
Una llamada sin recibo no se reintenta a ciegas. Multica mantiene runs de CLIs y
puede reusar una sesión/directorio o crear otra tras un error; eso no prueba
exactly-once sobre herramientas externas ni recuperación de nuestro render.
No duplicar esos estados ni lanzar agentes concurrentes en el proyecto por esta revisión.

## Fuentes y requisitos

[README](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/README.md),
[SELF_HOSTING](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/SELF_HOSTING.md),
[Compose](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/docker-compose.selfhost.yml):
servidor Go, web, colaboración, PostgreSQL17/pgvector, daemon y CLI de agente propia.
[go.mod](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/server/go.mod)
fija Go1.26.9; [package](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/package.json)
Node>=22/pnpm10.28.2. Compose usa latest por defecto: futura prueba debe fijar
imágenes por digest y runtime/agente por versión, medir RAM/disco, respaldar
volúmenes y comprobar migraciones automáticas. No se verificó Docker/WSL disponible.

[Runtimes](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/apps/docs/content/docs/daemon-runtimes.mdx):
daemon exige CLI soportada detectada; no incluye modelo. Defaults de concurrencia
20 por daemon/6 por agente son inadecuados como promesa en laptop: futura prueba
aislada empezaría en1 con bloqueo por checkout. Autostart Windows usa registro
Run y actualizaciones gestionadas; no habilitarlos ni cambiar configuraciones.

[Runs](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/apps/docs/content/docs/tasks.mdx):
reintentos acotados de fallos transitorios, no servicio perpetuo ni solución de
cuotas/auth. Detener espera del cliente no prueba terminación de todos los procesos.
[GitHub](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/apps/docs/content/docs/github-integration.mdx)
lee PR/CI y conserva snapshot stale; no publica commits/comentarios por sí mismo.
Agentes con otros permisos sí pueden escribir. Autoalojado requiere GitHub App y
autorización; no sustituye el conector ya operativo ni se crean credenciales aquí.

## Licencia, $0 y offline

[Multica License](https://github.com/multica-ai/multica/blob/92a4e450fb5c7d1de40cd5656772f47a22c62096/LICENSE)
combina Apache2 con condiciones adicionales: no es Apache puro. Uso interno de una
organización sin licencia comercial; servicio alojado a terceros incluso gratuito
y componentes de ofertas comerciales requieren licencia. UI derivada conserva
marca/logo/nombre salvo dispensa expresa; backend/daemon/CLI tienen atribución en
documentación. `server/ee` y `packages/ee` tienen términos comerciales separados.
No copiar UI al Studio ni asumir permiso por AGPL/MIT de otras partes. Sin aceptar
términos, contactar ventas o cambiar marcas.

Desktop conecta a cloud por defecto: ejecución local no implica datos locales.
Servidor guarda mensajes/contexto/resultados y variables/configuración de agentes;
fragmentos de código pueden llegar allí. Solo autoalojamiento completo y modelos
locales elegibles pueden aspirar a $0/offline; GitHub y CLIs cloud necesitan red,
y sus planes no son modelo local gratuito. Ollama solo no acredita integración de
un CLI soportado. Telemetría propia diaria activa: DO_NOT_TRACK=1 en servidor;
PostHog usa control independiente ANALYTICS_DISABLED. Ninguno se modificó aquí.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P2 | Medir necesidad del coordinador | Flujo actual vs propuesta con mismos casos de asignar/revisar/reanudar; tiempos y pasos medidos, sin doble fuente de estado |
| P2 | Matriz de elegibilidad/localidad | Uso interno delimitado, sin ee, imágenes/digests/licencias y CLI/modelo local compatible; sin credenciales o red implícita |
| P2 | Contrato de runs, no otro director | IDs y recibos enlazan GitHub/checkout; retries no repiten efectos sin evidencia, snapshot stale explícito, stop no equivale a inferencia detenida |
| P3 | Plan aislado de fallos | Concurrencia1, locks por checkout, caída daemon/DB, timeout, cancel y restore de volúmenes; recuperar sin perder cambios ni fusionar PR |

Bloqueos de despliegue: elegibilidad/objetivo interno, infraestructura y runtime
local no acreditados; eventual GitHub App requiere autorización específica. No son
bloqueos para mejorar seguimiento actual sin adoptar Multica. Sin agentes iniciados,
servicios instalados ni cambios a entornos o configuración del usuario.
