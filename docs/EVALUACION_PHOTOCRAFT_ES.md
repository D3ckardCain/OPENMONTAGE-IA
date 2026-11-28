# #101 — PhotoCraft

Evaluación documental, 25-11-2026 UTC. Sin instalación, ejecución ni medios.
Reutiliza el hallazgo del comentario 7146338257.

## Fuente y alcance

[Repositorio fijado](https://github.com/storytold/photocraft/tree/32f53c8fbbc7aacdb8f856a1fca024d804d02d50):
Cargo 0.23.1, Rust 1.95/edition2024. Se contrastan README, licencias,
NOTICE/ATTRIBUTION y documentos de automatización CLI/MCP/control-protocol.
MIT **o** Apache2 para el código no cubre todo: fuentes SIL OFL1.1, iconos
Lucide ISC/Feather MIT, diccionarios SCOWL y red libfacedetection BSD3 tienen
condiciones propias. Nombre/logos **ArtCraft** tienen restricciones de marca y
no se incorporan a OPENMONTAGE. Los formatos opcionales requieren revisar sus
dependencias antes de distribuir.

## Utilidad y límites

Editor Rust/wgpu con referencia CPU y backend DX12/Vulkan/Metal/WebGPU.
MSI y CLI Windows documentados; CLI fuera de PATH no equivale a instalación
rota. No se prueba aquí Windows, drivers ni paridad de formatos. Es alpha:
500 comandos de menú no demuestran 500 operaciones completas. KRA es lectura;
ORA lectura/escritura puede aplicar máscaras o perder estilos. No se promete
PSD editable sin pérdidas. Fuentes de sustitución cambian métricas; un LUT no
conserva máscaras ni efectos espaciales.

La edición clásica puede ser local sin tarifas después de preparar recursos;
esto no acredita funciones AI locales ni gratuitas. No activar servicios cloud.
Krita ya está registrado: su apertura no acredita automatización. El aporte
útil es `command_list/run/batch`, `doc_inspect` y `render_preview`, no otra tarjeta.
MCP headless, puente explícito de escritorio y autodetección optativa son modos
distintos: una sesión headless no modifica por sí sola la ventana abierta.
Un token no sustituye permisos por método; CLI conserva permisos normales del
usuario, mientras los roots MCP deben limitar accesos.

## Tareas sin duplicados

| ID / prioridad | Aceptación futura |
|---|---|
| E06 P1 | Contrato neutral de capas/máscaras/texto/ajustes, importación/exportación con manifiesto de pérdidas; no prometer roundtrip universal |
| E10 P1 | Puente explícito de instancia, catálogo versionado, roots y operaciones permitidas; lectura por defecto y errores estructurados |
| E05/E02 P1 | Guardado nuevo atómico, undo/redo/reapertura y mismo documento visible para agente/usuario, comprobados en una copia |
| B04/B06 | Windows, fidelidad, componentes/licencias y GUI reales pendientes; no adoptar otro editor antes de justificar carencia frente a Krita |

Evaluación concluida; integración no validada. No habilitar autodiscovery global.
