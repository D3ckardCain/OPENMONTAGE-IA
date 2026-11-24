# Social Media Agent — evaluación #87

24-11-2026, #3. [langchain-ai/social-media-agent](https://github.com/langchain-ai/social-media-agent/tree/bc27973c9c11f5c4929d78f26cb9ed200ab017f2). README, LICENSE, package.json/pyproject y nodos shared generate-post human-node/schedule-post revisados. Ambos manifiestos declaran0.0.1; commit fija fuente, no certifica versión estable de despliegue.

MIT con avisos para código; marcas/datos/modelos y servicios tienen términos propios. Stack principal TypeScript/LangGraph, Yarn1.22.22, autenticación OAuth/Arcade; componente Python>=3.11. No piso Node inequívoco en campos revisados: tipos Node26 no prueban requisito runtime26. Windows necesitaría CLI/dependencias/comandos compatibles, almacenamiento y reloj/zona horaria correctos; no probado. Recursos RAM/disco dependen del servidor/estado y LLM; no benchmark local ni GPU obligatoria inferida de app.

## Offline/$0

Quickstart necesita Anthropic, Firecrawl y Arcade. Créditos promocionales no garantizan operación$0; README no prueba contratos/precios actuales de APIs sociales. LinkedIn/X publicación requiere red, permisos y condiciones vigentes por plataforma; autenticación vía tercero no elimina límites ni derechos. No cuentas/Apps, credenciales, cron ni publicaciones creadas. Dossier/borrador local con Trafilatura/Ollama existentes es adaptación conceptual; no afirmar que upstream está ya conectado a ellos o que publicar será gratuito.

## Comparación con lo existente

`schemas/artifacts/publish_log.schema.json` ya distingue published/exported/failed/draft/pending_review; `tools/publishers/export_bundle.py` ya exporta. Eso no acredita una cola social durable, idempotencia de envío o reconciliación de resultado incierto. El candidato tiene revisión/interrupción y programación; no se toma como prueba de exactly-once. No instalar LangGraph/Agent Inbox ni segundo agente/UI.

La carencia útil es especificar estados de publicación en **E05/E06**, con prioridad baja y ejecución futura limitada a mocks. Extiende jobs/artefactos, no nuevo grupo duplicado.

| Grupo | Aceptación futura |
|---|---|
| E05/E06 | Borrador versionado con fuente/hash/cuenta/plataforma, revisión y aprobación ligadas al hash. Editar después de aprobar invalida aprobación. Rechazo no envía ni programa; timezone/DST y fecha pasada explícitos. |
| E05 | Mock de timeout después de aceptar envío produce uncertain y reconciliación por ID remoto/idempotency key; no retry ciego ni marcar failed como seguro de no publicación. Token expirado,401/403/429 y cancelación tienen estados distintos, sin secretos en logs. |
| E08/E06 | Extraer afirmación→pasaje y procedencia con lectores existentes; mock fuente cambiada no usa borrador viejo como vigente. Español y longitud por plataforma son validaciones, no hechos inventados. |
| B07 | Publicación real bloqueada hasta permisos/derechos/términos/costo elegibles y autorización de acción concreta. Ningún mock activa red o cron. |

Evaluación completada. No se acredita publicación social funcional ni adopción integral; ninguna instalación, modelo, mensaje, contenido o configuración modificada.
