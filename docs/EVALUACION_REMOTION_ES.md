# Remotion existente — evaluación #51

24-11-2026 UTC. No se instaló Node/npm/Remotion, descargó Chromium ni renderizó.
Se revisaron composer, lockfile, herramientas y licencias/documentación oficiales.

## Versiones y estado comprobable

`remotion-composer/package.json` pide ^4.0.484; `package-lock.json` resuelve remotion
y CLI4.0.484, React18.3.1. Licencia de esa versión fijada en
[tag4.0.484 /97b72073](https://github.com/remotion-dev/remotion/blob/97b7207325ffb7f338b2139301f46ad52de53eab/LICENSE.md).
También se consultó [main0e4c50cc](https://github.com/remotion-dev/remotion/tree/0e4c50cc93265b92eaaa40892c86b19c9fc07a0f)
para separar documentación vigente y anuncios futuros de la versión fijada.

No se encontraron package.json de Remotion instalado en `remotion-composer/node_modules`
ni `node_modules` raíz en las rutas comprobadas. Eso acredita ausencia en esas rutas,
no en todo el disco. El lockfile no demuestra instalación/disponibilidad. No ejecutar
npx para comprobarlo: podría intentar resolver/descargar paquetes. Node preparado
no equivale a tener composer, navegador y recursos completos.

## Ya tenemos y carencias justificadas

| Área | Implementación existente | Qué falta verificar/mejorar |
|---|---|---|
| Composición | `video_compose.py` enruta Remotion/HyperFrames/FFmpeg según render_runtime aprobado; Explainer, CinematicRenderer y autoría atelier | No crear otro adaptador genérico. Completar diagnóstico del conjunto exacto y preservación del runtime elegido |
| Estadísticas y captions | Componentes de tarjetas/gráficos, CaptionOverlay y remotion_caption_burn | Conectar datos y palabras locales con schema/procedencia; validar español y legibilidad, no añadir plantillas comerciales |
| Contratos | edit_decisions, asset_manifest, salidas por proyecto, verificación/entrega con ffprobe | Registrar versión de renderer, entrada/props, navegador y recursos en recibo reproducible; distinguir composición de generación neuronal |
| Progreso/cancelación | Transporte de agente cancelable y recibos; compositor llama proceso mediante run_command | subprocess.run captura salida al terminar: no demuestra progreso en vivo o cancelación del render. El stop de Qwen #42 no mata un render enviado |
| Recuperación | Estado de proyecto/checkpoints y verificación de salidas | Plan de job durable y reconciliación de proceso/salida parcial; no anunciar render reanudado por volver a lanzar el mismo comando |

Fuentes locales: `tools/video/video_compose.py`, `remotion_caption_burn.py`,
`tools/base_tool.py`, `lib/render_verification.py`, `lib/final_delivery.py` y composer.
Las pruebas de contratos existentes no son un benchmark de los pesos o GPU del usuario.

## Licencia y costo $0

Remotion tiene licencia propia, no MIT. La versión fijada permite Free License para
individuos, ciertas organizaciones pequeñas/no lucrativas y evaluación no comercial,
y restringe vender/relicenciar derivados del software. No dar por aprobada toda
redistribución de un editor o toolkit. Mantener licencia/avisos por paquete.

La [FAQ vigente](https://www.remotion.dev/docs/license/faq) remite a headcount total y
define participación de agencias/contratistas/clientes; no basta contar a quienes
pulsan render. No se determinó aquí la entidad/equipo aplicable ni su elegibilidad.
Registrar esa condición antes de uso productivo/distribución; no contratar Company
License por esta tarea. Si la ruta exige pago, no usarla: preparar alternativa
compatible con el brief, como FFmpeg existente para cortes simples o HyperFrames
tras su propia revisión, sin sustituir unilateralmente el runtime aprobado.

La licencia fijada y main no son byte-idénticas; la documentación anuncia cambios5.0.
No actualizar automáticamente ni aplicar condiciones futuras como si fueran4.0.484.
Recursos, fuentes, React, Chromium y binarios multimedia tienen licencias aparte;
la licencia de OPENMONTAGE no convierte Remotion en AGPL ni elimina sus términos.

## Offline: Node local no es render web

La [documentación de telemetría](https://www.remotion.dev/docs/telemetry) distingue
CLI/renderer Node de `@remotion/web-renderer`: el render web envía telemetría incluso
sin clave, mientras el envío automático del render servidor depende de configuración/
licencia. No inferir offline integral de que los fotogramas se calculen en el navegador.
No desactivar requisitos de licencia ni habilitar servicios cloud para evitar esta diferencia.

Para Node4.0.484, offline requiere paquetes/navegador/binarios y todos los medios,
fuentes y módulos ya presentes. Auditar importaciones, URLs y carga de fuentes de
cada composición; presencia de `@remotion/google-fonts` no prueba ni excluye por sí
sola una petición si existe un wrapper local. Reusar los recursos ya preparados;
nada fue descargado o ejecutado para esta revisión. Probar red denegada sobre fixture
será una tarea futura, no una certificación derivada de la FAQ actual.

## Tareas futuras con aceptación

| Prioridad | Tarea | Aceptación |
|---|---|---|
| P0 | Elegibilidad/versiones | Registro de entidad/equipo y versión/licencia aplicable, incluido alcance de distribución; si requiere pago, ruta no elegible y propuesta separada sin cambiar configuración |
| P0 | Doctor sin instalación | Resolver solo paquetes locales y navegador configurado; reportar ausente/incompatible sin npx remoto. Huellas/versiones de lock/props/recursos y ningún upgrade |
| P1 | Contrato de job | Estados e ID persistentes, progreso estructurado, timeout y cancelación de proceso propio; mocks demuestran que detener espera no implica detener renderer |
| P1 | Recuperación/recibos | Reconciliar job/salida/hash sin duplicar; conservar parcial separado, fuente intacta y errores claros; no declarar éxito por archivo presente |
| P1 | Offline y español | Fixtures de rutas/URLs/fuentes/¿¡/acentos, fps y captions; red externa denegada y ninguna descarga automática. Primero pruebas de datos/transporte sin render |
| P2 | Validación audiovisual | En fase autorizada: render sintético, ffprobe/decodificación, audio, sincronía, RAM/CPU/GPU y calidad; no extrapolar de otra máquina |

No se necesita otro editor multipista de #46 para reutilizar esta integración.
Evaluación completada; elegibilidad, preparación local y pruebas físicas quedan
pendientes. Configuraciones, GitHub Dark, ComfyUI y PR#2 borrador conservados.
