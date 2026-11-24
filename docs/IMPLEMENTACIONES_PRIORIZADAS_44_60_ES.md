# Implementaciones priorizadas de las evaluaciones #44–#60

24-11-2026 UTC. Consolidación documental; **ninguna implementación de esta lista se
declara ejecutada por cerrar su evaluación**. Orden por impacto, reutilización y
dependencias, no por popularidad upstream. P0 precede P1, después P2/P3. Las fuentes,
versiones/licencias exactas y límites de lectura están en los informes enlazados.

“Ejecutable” significa que una fase de implementación puede comenzar con código,
entornos existentes y fixtures textuales/números/mocks, sin instalaciones, medios
reales, APIs de pago o información indispensable del usuario. **Esta fase solo
evalúa y documenta**: no ejecuta ese backlog ni genera fixtures audiovisuales.
Pruebas de navegador respetan la política de sesión; no lanzar otro browser para
sortear una restricción. Coste $0 aquí significa sin cargos, no ausencia de RAM,
disco, electricidad o mantenimiento.

## Cola única ejecutable, en orden

| ID / prioridad | Implementación y evaluaciones agrupadas | Reutilización / dependencia | Entrega y aceptación concreta |
|---|---|---|---|
| E01 P0 | Diagnóstico local sin instalaciones y contrato de efectos (#46/#47/#51/#52/#53/#54/#56/#58/#59/#60) | Registry, application/model diagnostics y settings actuales; primero especificación compartida, extensiones por adaptador | Reporta versión observada vs lock/fuente, ruta ausente vs denegada/incompatible, licencia pendiente, efectos lectura/medición/escritura y recursos offline. Fixtures de paths Windows/symlinks, dependencia ausente y timeout; nunca npx/pip/download/upgrade implícito. No reauditar instalaciones aprobadas sin necesidad |
| E02 P0 | Accesibilidad y robustez Studio (#45/#58; tokens #59/#60) | CSS/HTML/JS GitHub Dark y pytest/Playwright existentes; no instalar detectores | Contrato único de tokens y pruebas de contraste, teclado/foco, nombres/errores,320–1280px, zoom y textos españoles/rutas largas. Primero verificar riesgo del botón verde de #45; cambios solo por fallos observados. Fixtures API400/403/500/timeout y preservar input. Ningún gate estético, hooks o nueva UI/framework |
| E03 P0 | `clip_candidates` trazables y selección española (#44; medición #54 no decide semántica) | ASR preparado, Ollama, transcript y scene/edit_decisions; no instalar PeakCut | Esquema fuente/hash/transcript/lang/inicio-fin/motivo/modelo. Rechaza NaN/Inf, reloj incorrecto, rango fuera de fuente y duplicados; conserva rechazados y aprobación. LLM simulado etiquetado; no viralidad inferida de score |
| E04 P0 | Puente palabras/subtítulos y presets de encuadre (#44/#46/#51/#52/#54/#55) | ASR español/subtitle_gen/CaptionWord/auto_reframe existentes; E03 usa el contrato | Normaliza segundos/frames/offsets y fps racional sin perder palabras; ASS escapado, acentos/¿¡, sin voz/idioma incierto y zonas seguras por ratio. Casos de datos y strings sin audio/render. Preset vertical no significa seguimiento facial validado; no otro ASR/descargador |
| E05 P0 | Ciclo de jobs multimedia compartido (#46/#47/#51/#52/#54/#56) | Studio jobs/recibos/cancelación y puentes existentes; E01 | ID/estados persistentes, progreso, timeout, stop y reconciliación por backend; cerrar socket/espera separado de terminar inferencia/proceso. Mocks de caída, corrupción, parcial y stop durante etapa; nunca repetir herramienta/segmento con recibo válido. Propiedad de proceso/árbol y original intacto. Lo aprobado en Qwen#42 se reutiliza, no se repite como validación de renderer |
| E06 P1 | Intercambio neutral de proyectos/escenas (#46/#49/#52/#55; diseño #59/#60) | edit_decisions, rig_plan, pose_library y formatos Blender/Krita guardados; E04/E05 | Un sobre común de IDs/revisión/assets/hash/tiempos/unidades/jerarquía/cámara y extensiones por formato. Round-trip JSON sintético distingue pérdidas/unsupported; editar candidato con diff/undo/snapshot y rechazo de base obsoleta. No ejecutar HTML/código externo. No prometer convertidor universal ni export creativo aprobado |
| E07 P1 | Diagnóstico editorial español (#48) | script_diagnostic/reviewer, original/historial y Ollama actual | Reglas versionadas, lengua/offsets Unicode y severidad; `unscored`/error distintos de limpio. Corpus sintético técnico/deportivo/bíblico, falsos positivos; candidato separado y preservación de cifras/citas/negaciones/atribución. Diagnosticar nunca reescribe ni juzga autoría humana |
| E08 P1 | Research con muestras propias y baselines (#50) | youtube_client/channels, CSV propietario, dossiers y vidIQ manual | URLs/fecha/filtros/n/edad/formato/periodo y fórmulas; mediana0, ocultos/faltantes/duplicados dan desconocido explícito. Mocks de comentarios/hilos/páginas/cuota/desactivados; no inventar RPM/monetización. Cache/watchlist muestra vencimiento. Red fresca y TubeLab no necesarias para probar contrato |
| E09 P1 | Sincronía y drift con medición explícita (#54) | FFmpeg/ffprobe, audio_probe y audio_mixer; E01/E05 | Datos/mock de señales con offset/ppm conocidos, confianza/tolerancias y razones de omisión ante silencio/ruido/cola corta. LUFS/true peak medidos separados de normalizar mezcla. Prueba con audio sintético codificado queda para fase autorizada; no medios reales ni declarar lip-sync visual |
| E10 P1 | Contrato de lectura MCP/local por capacidades (#46/#53/#59) | Puente del agente y errores/procedencia; E01/E05/E06 | Loopback/identidad/scope/versión, allowlist efectiva, timeouts y errores estructurados. Servidor falso rechaza escritura/desconocido/ruta fuera de proyecto. tools/list y readOnlyHint no sustituyen enforcement. No conexión/install del editor/índice/prototipador físico para comenzar |
| E11 P1 | Eventos semánticos de animación (#55; poses/cámara #49) | scene_plan/character QA/Ink Theater/Ink Puppet y E06 | Cue/evento/actor/objeto/antes-después/propósito/tiempos y anclajes; fixtures de IDs rotos, conectores invertidos y decoración mal atribuida. Revisión visual futura sigue independiente; no generar geometría/animación ni importar catálogo de demos |
| E12 P2 | Buffer acotado de captura de directos (#44) | yt-dlp/FFmpeg existentes, E05 | Máquina de estados con listas/segmentos ficticios: reloj/discontinuidad, pines, cuota bytes/tiempo, falta audio/disco lleno, URL expirada y stop/resume. Limpieza solo de recursos propios. Mocks ejecutables offline; captura real requiere red y derechos aparte |
| E13 P2 | Contexto estructural auxiliar de código (#53) | rg y preguntas conocidas como baseline; E01/E10 | Primero corpus/contrato de callers/importers/tests y omisiones dinámicas; revisión y archivo/línea obligatorios. Benchmark futuro recall/precisión/tokens/RAM/tiempo/disco/frescura. No editar ni borrar código muerto automáticamente. Runtime/índice real condicionado a B03 |
| E14 P2 | Diagramas/editorial y tokens neutrales (#60/#59, mismo E02/E06) | diagram_gen/Mermaid para docs; no nuevo generador ni otro sistema visual | Esquema nodos/aristas/datos/fuentes y formato adecuado; export SVG sin red reutiliza system-fonts, protege outputs y rechaza referencias/código ajenos. Fixtures de flecha/valor equivocado, solapamiento y español. PNG/browser y diagrama factual real separados |
| E15 P3 | Medir necesidad de coordinador interno (#57) | GitHub issues/CI y flujo actual, no otro tablero | Especificar casos iguales de asignación/revisión/reintento y métricas de traspaso; adoptar solo con mejora medible. No iniciar agentes, autoactualización o infraestructura para realizar la comparación documental |

E01/E02 pueden comenzar independientemente. E03/E04 comparten transcript; no hace
falta terminar todas las extensiones de E01 para probar sus esquemas. E05 primero
con backends ya conectados, después extensiones elegibles. E06/E10 definen formatos
sin instalar editores. E07/E08 son independientes del render. E09/E12 comienzan
con datos/mocks. E13/E14/E15 no desplazan correcciones funcionales de Studio.

## Bloqueos y validaciones que no deben ocultarse

| ID | Ruta condicionada | Qué falta / evidencia de desbloqueo | Alternativa independiente |
|---|---|---|---|
| B01 | H3 en FreeVideo/OpenJutsu (#47/#56) | Licencia territorial/outputs/uso del artefacto exacto, inventario cerrado con huellas/tamaños y perfil de hardware. No asumir laptop8GB/16GB cumple demo16GB/64GB. Necesita runtime/ComfyUI separado, nunca parchear el actual | E01/E05/preflight/contratos de máscaras; WAN/LTX existentes conservados |
| B02 | Remotion ejecutable/distribución (#51) | Elegibilidad según versión/licencia y entidad/equipo; lock4.0.484 no prueba instalación. Si exige pago, excluida por costo$0. Navegador/paquetes locales y recursos/fuentes offline comprobados antes de render | E04/E05/E06 con mocks; no fallback silencioso de motor |
| B03 | Grafo CGR real (#53) | Python>=3.12 y wheel nativo Windows/licencias en entorno aislado; perfil sin embeddings/descargas/web, índice exclusivo/exclusiones y benchmark | E13 corpus/contrato + rg; no modificar .venv/ComfyUI |
| B04 | Nuevos editores/runtimes (#46/#49/#52/#55) | Licencias de componentes/NOTICE/recursos, requisitos efectivos de paquete y sandbox, fuentes/assets y lifecycle. OpenFilm intenta aprovisionar Chromium al primer uso; ArtCraft tiene rutas cloud/recursos excluidos | E06/E10/E11 especificaciones sin ejecutar apps, sin otra UI |
| B05 | Suite de diseño/prototipado/coordinación (#57/#58/#59) | Multica solo alcance interno elegible y stack completo; Penpot digests/DB/assets/offline y recursos, MCP con permisos acotados; Impeccable binario revisado sin hooks/Live. GitHub App/autorizaciones si se adopta sincronización Multica, no indispensable para seguimiento actual | E02/E10/E14/E15. Mantener GitHub Dark y conector actual |
| B06 | Export/QA audiovisual o visual física (varios) | Política/recursos de navegador, fase autorizada con medios sintéticos, luego revisión visual/auditiva. Preview/executable localizado/schema válido no acreditan calidad ni automatización completa | Tests de datos, contratos y procesos simulados; no evasión de restricciones |
| B07 | Fuentes externas/servicios/derechos (#44/#50/#60) | Directos/datos frescos requieren red y derecho de uso; TubeLab de pago excluido. Comentarios/ASR/captions tienen permisos/cuotas; no extrapolar muestras ni autores. Fuentes/íconos/marcas tienen licencias propias | Snapshots propios, CSV/mocks, fuentes sistema/locales y research cache con fecha |

No se necesita una respuesta del usuario para completar estas evaluaciones.
Los bloqueos se refieren a adopción/ejecución futura, no a impedimentos documentales.
No comprar licencias, crear cuentas/Apps, aceptar términos, descargar pesos ni
activar instancias para intentar cerrarlos en esta fase.

## Cobertura sin duplicados de los17 issues

| Evaluación | Informe y destino consolidado |
|---|---|
| #44 PeakCut | [Informe](EVALUACION_PEAKCUT_ES.md): E03/E04/E12, chat optativo tras B07 |
| #45 Taste | [Informe](EVALUACION_TASTE_SKILL_ES.md): E02, sin hook/gate global |
| #46 OpenReel | [Informe](EVALUACION_OPENREEL_ES.md): E01/E05/E06/E10; B04 |
| #47 FreeVideo | [Informe](EVALUACION_FREEVIDEO_ES.md): E01/E05; B01 |
| #48 Avoid AI Writing | [Informe](EVALUACION_AVOID_AI_WRITING_ES.md): E07 |
| #49 ArtCraft | [Informe](EVALUACION_ARTCRAFT_ES.md): E06/E11; B04 |
| #50 YouTube Research Skills | [Informe](EVALUACION_YOUTUBE_RESEARCH_SKILLS_ES.md): E08; B07 |
| #51 Remotion | [Informe](EVALUACION_REMOTION_ES.md): E01/E04/E05/E06; B02 |
| #52 OpenFilm | [Informe](EVALUACION_OPENFILM_ES.md): E01/E05/E06; B04 |
| #53 Code-Graph-RAG | [Informe](EVALUACION_CODE_GRAPH_RAG_ES.md): E01/E10/E13; B03 |
| #54 ffmpeg-skill | [Informe](EVALUACION_FFMPEG_SKILL_ES.md): E01/E04/E05/E09 |
| #55 Stickman Director | [Informe](EVALUACION_STICKMAN_DIRECTOR_ES.md): E04/E06/E11; B04 |
| #56 OpenJutsu | [Informe](EVALUACION_OPENJUTSU_ES.md): E01/E05/contrato máscaras; B01 |
| #57 Multica | [Informe](EVALUACION_MULTICA_ES.md): E15; B05 |
| #58 Impeccable | [Informe](EVALUACION_IMPECCABLE_ES.md): E02; B05 |
| #59 Penpot | [Informe](EVALUACION_PENPOT_ES.md): E02/E06/E10/E14; B05 |
| #60 Diagram Design | [Informe](EVALUACION_DIAGRAM_DESIGN_ES.md): E14; B06/B07 |

No volver a implementar cortes/unión, ASR, karaoke, normalización de mezcla,
adaptadores de aplicaciones, Blender/Krita, cancelación de Qwen#42 ni un director
multietapa por aparecer en otro README. Extender solo la carencia demostrada.
Las tareas seleccionadas se implementarán una a una con pruebas acotadas y manual;
una futura instalación queda separada de apertura, API/panel y automatización real.

## Verificación de esta fase

Ocho informes y esta consolidación se publican como documentación. Fuentes upstream
fijadas, licencias leídas y rutas/contratos locales contrastados. Validación estática
de UTF-8/enlaces/IDs/cobertura; CI remota se registra en #3 y PR#2. Sin ejecutar
candidatos, inferencia, indexación, render, audio o medios reales. Configuraciones,
originales, ComfyUI y GitHub Dark conservados; PR#2 permanece en borrador sin merge.
