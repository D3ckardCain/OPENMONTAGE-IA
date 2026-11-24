# Code-Graph-RAG: evaluación #53

24-11-2026 UTC. Revisión estática de `vitali87/code-graph-rag` en
`112cb76e037566a4433b3fb2a1a818f1a08c4ece`, versión de pyproject 0.7.107.
El README distingue tags por merge de releases/PyPI menos frecuentes: este commit
no acredita que ese número tenga wheel publicado. No se instaló ni indexó código.

## Decisión y contraste

Conservar `rg`, lectura de archivos, tests y GitHub como base. Probar posteriormente
un grafo auxiliar de desarrollo, no incorporarlo al director audiovisual ni darle
edición por MCP. El registro `tools/tool_registry.py` describe capacidades y
`lib/production_agent.py` coordina herramientas de producción: no son un índice de
llamadas del código. Un grafo sí puede aportar callers/importers/tests_reaching y
contexto acotado con motivos y localizaciones; no sustituye verificar el archivo.
La carga dinámica del registry y dispatch por nombres pueden quedar incompletos.
Una arista ausente no prueba código muerto ni autoriza borrarlo.

## Fuentes, licencia y requisitos

- [README](https://github.com/vitali87/code-graph-rag/blob/112cb76e037566a4433b3fb2a1a818f1a08c4ece/README.md): Tree-sitter, frontends opcionales y SQLite embebido; no necesita Docker para el alcance básico.
- [pyproject](https://github.com/vitali87/code-graph-rag/blob/112cb76e037566a4433b3fb2a1a818f1a08c4ece/pyproject.toml): Python>=3.12, cgr-graph-rs>=0.1.8,<0.2, Tree-sitter0.26.0, MCP>=2.3,<3, pydantic-ai-slim y extras opcionales. Windows x64 requiere wheel nativo compatible. Studio3.11 no cumple; futuro entorno aislado, sin tocar .venv/ComfyUI.
- [LICENSE](https://github.com/vitali87/code-graph-rag/blob/112cb76e037566a4433b3fb2a1a818f1a08c4ece/LICENSE): MIT, conservar aviso. Revisar avisos del componente Rust, parsers y modelos opcionales por separado; no se copió código.
- [Configuración](https://github.com/vitali87/code-graph-rag/blob/112cb76e037566a4433b3fb2a1a818f1a08c4ece/docs/getting-started/configuration.md): roles orchestrator y Cypher deben configurar proveedor/modelo juntos. Usar solo Ollama existente y modelo preparado explícito, no descargar el ejemplo qwen2.5-coder. El default llama3.2 no acredita presencia local.
- [MCP](https://github.com/vitali87/code-graph-rag/blob/112cb76e037566a4433b3fb2a1a818f1a08c4ece/docs/guide/mcp-server.md) y [registro](https://github.com/vitali87/code-graph-rag/blob/112cb76e037566a4433b3fb2a1a818f1a08c4ece/codebase_rag/mcp/tools.py): existen consultas deterministas sin LLM y modo `--read-only`; excluye escrituras e indexación. Preparar el índice por separado, no exponer todos los métodos por defecto.

## Costo, offline y procedencia

Consultas estructurales pueden ser $0/offline tras aprovisionar runtime e índice.
Preguntas naturales requieren inferencia local; calidad de Cypher de Qwen no probada.
La CLI registra búsqueda web DuckDuckGo por defecto incluso sin clave. El registro
MCP revisado indica que no expone esa herramienta web: no confundir sus dos rutas.
Exigir lista permitida de métodos y bloqueo de egreso en pruebas; no basta cambiar
proveedor a Ollama. Embeddings semánticos son opcionales y pueden requerir pesos;
empezar sin ellos. No servicios de pago ni envío de código externo.

El SQLite por defecto es compartido en ~/.cgr. Usar futuro índice exclusivo con raíz,
revisión, hashes/archivos, versión del parser, exclusiones y fecha. `--clean` borra
todos los proyectos del índice compartido; no utilizarlo. Excluir .venv, ComfyUI,
node_modules, .backlot, .runtime, secretos, pesos, binarios, proyectos y salidas.
Incremental/reingest no actualiza todos los análisis globales: indicar frescura y
rechazar resultados incompatibles con revisión actual, sin mutar fuentes.

## Tareas propuestas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Contrato de consulta y corpus sintético | Casos Python/JS de importación, herencia, dispatch dinámico y borrado; respuesta distingue resuelto/heurístico/desconocido, con archivo/línea/revisión |
| P1 | Benchmark contra rg | Mismas preguntas conocidas, recall/precisión, tokens, tiempo, disco/RAM y frescura medidos; adoptar solo si mejora contexto sin ocultar omisiones |
| P1 | Perfil aislado y exclusiones | Inventario sin instalar; luego wheel/huella/licencias y Python compatible; ningún acceso a secretos, configuraciones o entornos protegidos |
| P2 | MCP de solo lectura | Lista de métodos comprobada, escrituras/indexación/web rechazadas; índice externo exclusivo, cancelación/timeouts y errores estructurados |
| P2 | Incremental y recuperación | Cambio/renombre/borrado sintéticos actualizan localizaciones; crash no presenta índice parcial como completo; no repetir consultas completadas innecesariamente |

Bloqueos de adopción: runtime>=3.12/wheel aún no validados, beneficio no medido y
egreso/allowlist pendientes. No impiden especificar contratos. Esta evaluación no
certifica compatibilidad Windows, precisión de grafo ni mejora de productividad.
