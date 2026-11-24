# Implementaciones priorizadas de las evaluaciones #44–#78 (excepto #70, CI)

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
| E01 P0 | Diagnóstico local sin instalaciones y contrato de efectos (#46/#47/#51/#52/#53/#54/#56/#58/#59/#60); ampliado #62/#63/#66/#67/#68/#69; ampliado #71/#72/#73/#74/#75/#76/#77/#78 | Registry, application/model diagnostics y settings actuales; primero especificación compartida, extensiones por adaptador | Reporta versión observada vs lock/fuente, ruta ausente vs denegada/incompatible, licencia pendiente, efectos lectura/medición/escritura y recursos offline. Fixtures de paths Windows/symlinks, dependencia ausente y timeout; nunca npx/pip/download/upgrade implícito. No reauditar instalaciones aprobadas sin necesidad. Servicio externo vs propio, PID/puerto/instancia y code revision vs image digest separados; requisitos de Node/runtime/loader no obligan a actualizar lo aprobado. Preflight distingue recursos preparados de descargas de codec/tokenizer/preset; tamaño cuantizado en disco no acredita memoria de ejecución. Sin reinstalar lo aprobado. |
| E02 P0 | Accesibilidad y robustez Studio (#45/#58; tokens #59/#60) | CSS/HTML/JS GitHub Dark y pytest/Playwright existentes; no instalar detectores | Contrato único de tokens y pruebas de contraste, teclado/foco, nombres/errores,320–1280px, zoom y textos españoles/rutas largas. Primero verificar riesgo del botón verde de #45; cambios solo por fallos observados. Fixtures API400/403/500/timeout y preservar input. Ningún gate estético, hooks o nueva UI/framework |
| E03 P0 | `clip_candidates` trazables y selección española (#44; medición #54 no decide semántica); ampliado #62; ampliado #73/#74/#75 | ASR preparado, Ollama, transcript y scene/edit_decisions; no instalar PeakCut | Esquema fuente/hash/transcript/lang/inicio-fin/motivo/modelo. Rechaza NaN/Inf, reloj incorrecto, rango fuera de fuente y duplicados; conserva rechazados y aprobación. LLM simulado etiquetado; no viralidad inferida de score. Asociación de cada recurso al fragmento de guion con fuente/licencia; no generar ni buscar stock para probar el contrato. Candidatos de límite por contenido/adaptación/fundido y señales booleanas de audio/pista/movimiento llevan método, umbral y falsos positivos. FPS/PTS y fin exclusivo explícitos; no equivalen a saliencia. Comparar con FFmpeg antes de otra dependencia. |
| E04 P0 | Puente palabras/subtítulos y presets de encuadre (#44/#46/#51/#52/#54/#55); ampliado #61/#62/#63/#68; ampliado #71/#72/#73/#74/#75/#76/#78 | ASR español/subtitle_gen/CaptionWord/auto_reframe existentes; E03 usa el contrato | Normaliza segundos/frames/offsets y fps racional sin perder palabras; ASS escapado, acentos/¿¡, sin voz/idioma incierto y zonas seguras por ratio. Casos de datos y strings sin audio/render. Preset vertical no significa seguimiento facial validado; no otro ASR/descargador. Añadir speaker local y spans sin atribuir identidad, parcial/final de ASR streaming y timestamps voz→plano. Fixtures de solape/code-switch/silencio; no truncar ni acelerar doblaje sin decisión explícita. Separar alineación medida, estimada e imputada; alineación no exige diarización ni puede degradarse silenciosamente. Palabras finales y segmentos alineados comparten reloj; mapear cortes/eliminaciones/velocidades al tiempo de salida preservando spans. Anclaje por reparto de letras no es alineación. QA de subtítulos/zonas seguras incluye región/intervalo/método/umbral/evidencia y desconocido explícito. |
| E05 P0 | Ciclo de jobs multimedia compartido (#46/#47/#51/#52/#54/#56); ampliado #61/#62/#63/#66/#67/#68/#69; ampliado #71/#74/#76/#78 | Studio jobs/recibos/cancelación y puentes existentes; E01 | ID/estados persistentes, progreso, timeout, stop y reconciliación por backend; cerrar socket/espera separado de terminar inferencia/proceso. Mocks de caída, corrupción, parcial y stop durante etapa; nunca repetir herramienta/segmento con recibo válido. Propiedad de proceso/árbol y original intacto. Lo aprobado en Qwen#42 se reutiliza, no se repite como validación de renderer. Invalidación por hash/versión de guion/voz/asset/ratio y fallos de variante2 conservando variante1; chunks parciales nunca se promocionan a finales. Servicio externo no se detiene por ocupar puerto. Informe QA final estructurado: hallazgo, región/tiempo, evidencia y alcance; distingue freeze intencional, loudness medido y calidad visual no evaluada. Con datos/mocks validar errores/invalidation y evitar declarar aprobación por metadata/decode; prueba audiovisual queda en B06. |
| E06 P1 | Intercambio neutral de proyectos/escenas (#46/#49/#52/#55; diseño #59/#60); ampliado #61/#62/#64/#67/#69; ampliado #73/#74/#75/#76/#77 | edit_decisions, rig_plan, pose_library y formatos Blender/Krita guardados; E04/E05 | Un sobre común de IDs/revisión/assets/hash/tiempos/unidades/jerarquía/cámara y extensiones por formato. Round-trip JSON sintético distingue pérdidas/unsupported; editar candidato con diff/undo/snapshot y rechazo de base obsoleta. No ejecutar HTML/código externo. No prometer convertidor universal ni export creativo aprobado. Extensiones de máscaras/roles y edificio/nivel/pared/abertura/IFC GUID; imported-mesh/derivado no se declara paramétrico. Cast/location/voz versionados, cambios invalidan solo dependientes; fuente y escena candidatas separadas. Shot record neutral distingue medición, estimación de cámara y descripción inferida por VLM; raw JSON no parseado es error, no evidencia validada. Export temporal conserva pérdidas/versión/timebase. Solo si útil, progreso de revisión local entre sesiones (baja prioridad) por identidad/hash, esquema validado sin secretos/rutas personales por defecto; no duplicar jobs ni biblioteca. |
| E07 P1 | Diagnóstico editorial español (#48) | script_diagnostic/reviewer, original/historial y Ollama actual | Reglas versionadas, lengua/offsets Unicode y severidad; `unscored`/error distintos de limpio. Corpus sintético técnico/deportivo/bíblico, falsos positivos; candidato separado y preservación de cifras/citas/negaciones/atribución. Diagnosticar nunca reescribe ni juzga autoría humana |
| E08 P1 | Research con muestras propias y baselines (#50); ampliado #62/#65 | youtube_client/channels, CSV propietario, dossiers y vidIQ manual | URLs/fecha/filtros/n/edad/formato/periodo y fórmulas; mediana0, ocultos/faltantes/duplicados dan desconocido explícito. Mocks de comentarios/hilos/páginas/cuota/desactivados; no inventar RPM/monetización. Cache/watchlist muestra vencimiento. Red fresca y TubeLab no necesarias para probar contrato. Esquema platform/namespace sin romper UC IDs; snapshots CSV/JSON propios, permisos/cobertura/métricas por plataforma. TikTok/IG nuevos no se anuncian implementados por importar tabla. |
| E09 P1 | Sincronía y drift con medición explícita (#54) | FFmpeg/ffprobe, audio_probe y audio_mixer; E01/E05 | Datos/mock de señales con offset/ppm conocidos, confianza/tolerancias y razones de omisión ante silencio/ruido/cola corta. LUFS/true peak medidos separados de normalizar mezcla. Prueba con audio sintético codificado queda para fase autorizada; no medios reales ni declarar lip-sync visual |
| E10 P1 | Contrato de lectura MCP/local por capacidades (#46/#53/#59); ampliado #63/#64/#67/#69 | Puente del agente y errores/procedencia; E01/E05/E06 | Loopback/identidad/scope/versión, allowlist efectiva, timeouts y errores estructurados. Servidor falso rechaza escritura/desconocido/ruta fuera de proyecto. tools/list y readOnlyHint no sustituyen enforcement. No conexión/install del editor/índice/prototipador físico para comenzar. Concat window/headless explícito, roots/locks/auth y status de export; Pascal escena activa por servicio y un cliente, home/procesos separados. OpenCut requiere código API real antes de conectar; lectura de perfiles no incluye creación/clonación. |
| E11 P1 | Eventos semánticos de animación (#55; poses/cámara #49); ampliado #61; ampliado #75/#76 | scene_plan/character QA/Ink Theater/Ink Puppet y E06 | Cue/evento/actor/objeto/antes-después/propósito/tiempos y anclajes; fixtures de IDs rotos, conectores invertidos y decoración mal atribuida. Revisión visual futura sigue independiente; no generar geometría/animación ni importar catálogo de demos. Biblia/cast/location vinculados a toma y cámara; reutilizar from_take solo con dependencias/recibo compatibles y evidencia, nunca aprobación copiada de ejemplo. Cámara óptica estimada incorpora incertidumbre y escala/cadencia; sujeto/paralaje pueden confundirla. Eventos de palabra usan ocurrencia/span y origen del tiempo; no heredan certeza de heurísticas. |
| E16 P1 | Perfil trazable de voz y elegibilidad (#63/#68; timing #61/#62); ampliado #72/#78 | Adaptadores Kokoro/Qwen/ASR preparados, E01/E04/E05; sin otra UI | Motor/variante/loader/revisión/hashes, voz/idioma y referencia autorizada con derechos separados. NC/unknown bloquea uso monetizado, AGPL de app no licencia pesos. Lotes/pausas preservan perfiles y segmentos; mocks de cambio de voz, parcial/error y ruta denegada. Calidad/identidad/doblaje real requiere fase posterior; no audio en evaluación Normalización española independiente: original inmutable, hablado, mapa de sustituciones, idioma/opciones/versión y procedencia. Fixtures de cifras/monedas/fechas ambiguas/unidades/siglas/emoji; offsets Python codepoints vs JS UTF-16 explícitos. Pesos Reverb NC bloqueados comercialmente; codec y preset con elegibilidad separada. Mocks sin voz ni modelos nuevos. |
| E12 P2 | Buffer acotado de captura de directos (#44) | yt-dlp/FFmpeg existentes, E05 | Máquina de estados con listas/segmentos ficticios: reloj/discontinuidad, pines, cuota bytes/tiempo, falta audio/disco lleno, URL expirada y stop/resume. Limpieza solo de recursos propios. Mocks ejecutables offline; captura real requiere red y derechos aparte |
| E13 P2 | Contexto estructural auxiliar de código (#53) | rg y preguntas conocidas como baseline; E01/E10 | Primero corpus/contrato de callers/importers/tests y omisiones dinámicas; revisión y archivo/línea obligatorios. Benchmark futuro recall/precisión/tokens/RAM/tiempo/disco/frescura. No editar ni borrar código muerto automáticamente. Runtime/índice real condicionado a B03 |
| E14 P2 | Diagramas/editorial y tokens neutrales (#60/#59, mismo E02/E06) | diagram_gen/Mermaid para docs; no nuevo generador ni otro sistema visual | Esquema nodos/aristas/datos/fuentes y formato adecuado; export SVG sin red reutiliza system-fonts, protege outputs y rechaza referencias/código ajenos. Fixtures de flecha/valor equivocado, solapamiento y español. PNG/browser y diagrama factual real separados |
| E15 P3 | Medir necesidad de coordinador interno (#57) | GitHub issues/CI y flujo actual, no otro tablero | Especificar casos iguales de asignación/revisión/reintento y métricas de traspaso; adoptar solo con mejora medible. No iniciar agentes, autoactualización o infraestructura para realizar la comparación documental |

E01/E02 pueden comenzar independientemente. E03/E04 comparten transcript; no hace
falta terminar todas las extensiones de E01 para probar sus esquemas. E05 primero
con backends ya conectados, después extensiones elegibles. E06/E10 definen formatos
sin instalar editores. E07/E08 son independientes del render. E09/E12 comienzan
con datos/mocks. E16 comienza como perfil/licencia sin motores nuevos, extiende E04/E05 sin duplicarlos. E13/E14/E15 no desplazan correcciones funcionales de Studio.

## Bloqueos y validaciones que no deben ocultarse

| ID | Ruta condicionada | Qué falta / evidencia de desbloqueo | Alternativa independiente |
|---|---|---|---|
| B01 | H3 en FreeVideo/OpenJutsu (#47/#56) | Licencia territorial/outputs/uso del artefacto exacto, inventario cerrado con huellas/tamaños y perfil de hardware. No asumir laptop8GB/16GB cumple demo16GB/64GB. Necesita runtime/ComfyUI separado, nunca parchear el actual | E01/E05/preflight/contratos de máscaras; WAN/LTX existentes conservados |
| B02 | Remotion ejecutable/distribución (#51) | Elegibilidad según versión/licencia y entidad/equipo; lock4.0.484 no prueba instalación. Si exige pago, excluida por costo$0. Navegador/paquetes locales y recursos/fuentes offline comprobados antes de render | E04/E05/E06 con mocks; no fallback silencioso de motor |
| B03 | Grafo CGR real (#53) | Python>=3.12 y wheel nativo Windows/licencias en entorno aislado; perfil sin embeddings/descargas/web, índice exclusivo/exclusiones y benchmark | E13 corpus/contrato + rg; no modificar .venv/ComfyUI |
| B04 | Nuevos editores/runtimes (#46/#49/#52/#55); #61/#62/#64/#67/#69 #71/#73/#74/#75/#76. | Licencias de componentes/NOTICE/recursos, requisitos efectivos de paquete y sandbox, fuentes/assets y lifecycle. OpenFilm intenta aprovisionar Chromium al primer uso; ArtCraft tiene rutas cloud/recursos excluidos. OpenCut rewrite no maduro/Classic archivado; Concat beta requiere build/modelos/codecs y modo. Pascal runtime aparte/WebGPU/IFC parcial; Anime depende de Fal/ElevenLabs y Swift macOS, MoneyPrinter local puede llamar proveedores externos. Raea FSL: uso interno permitido según finalidad; distribución/servicio exige evaluar Competing Use, avisos y componentes, sin prohibir toda distribución ni anticipar Apache antes del aniversario de cada versión. Runtimes/editor nuevos y plugins ComfyUI siguen condicionados; no tocar ComfyUI. | E06/E10/E11 especificaciones sin ejecutar apps, sin otra UI |
| B05 | Suite de diseño/prototipado/coordinación (#57/#58/#59); #66 | Multica solo alcance interno elegible y stack completo; Penpot digests/DB/assets/offline y recursos, MCP con permisos acotados; Impeccable binario revisado sin hooks/Live. GitHub App/autorizaciones si se adopta sincronización Multica, no indispensable para seguimiento actual. ODS prerelease/WSL/Docker requiere cierre de requisitos/licencias; Pixel ODS-only no extraíble, tagv3.0.0 afectado por advisory no desplegable. | E02/E10/E14/E15. Mantener GitHub Dark y conector actual |
| B06 | Export/QA audiovisual o visual física (varios) | Política/recursos de navegador, fase autorizada con medios sintéticos, luego revisión visual/auditiva. Preview/executable localizado/schema válido no acreditan calidad ni automatización completa | Tests de datos, contratos y procesos simulados; no evasión de restricciones |
| B07 | Fuentes externas/servicios/derechos (#44/#50/#60); #65 #76/#77. | Directos/datos frescos requieren red y derecho de uso; TubeLab de pago excluido. Comentarios/ASR/captions tienen permisos/cuotas; no extrapolar muestras ni autores. Fuentes/íconos/marcas tienen licencias propias. Crédito Apify finito no garantiza operación$0; Display/Instagram tienen scopes concretos y Research TikTok requiere elegibilidad, no bypass de acceso. Streambert: no adoptar streaming/proveedores/descargador. TMDB comercial requiere licencia separada; términos AniList inaccesibles (403), sin permiso inferido. Recursos Commons/fonts exigen registro de derechos y procedencia; filtro automático no sustituye elegibilidad. | Snapshots propios, CSV/mocks, fuentes sistema/locales y research cache con fecha |
| B08 | Motores de voz/ASR/doblaje nuevos (#63/#68) #72/#78. | OmniVoice default NC/tokenizer con términos propios; licencia de app no los habilita. VibeVoice metadata MIT no sustituye textos de recursos; TTS original retirado, ES Realtime experimental, loaders/CUDA/CPU/memoria sin validar. Inventario primero, sin pesos nuevos Reverb pesos CC-BY-NC-4.0: uso comercial bloqueado, no instalación automática pendiente. Codec Boson incorpora términos Meta/avisos y umbral100.000 usuarios anuales; preset sin derechos independientes no habilitado. WhisperX requiere inventario de alignment/NLTK/diarización; token/condiciones pyannote independientes, nunca descargas implícitas. | E16/E04/E05 con mocks y motores existentes, sin duplicar ASR/TTS |

No se necesita una respuesta del usuario para completar estas evaluaciones.
Los bloqueos se refieren a adopción/ejecución futura, no a impedimentos documentales.
No comprar licencias, crear cuentas/Apps, aceptar términos, descargar pesos ni
activar instancias para intentar cerrarlos en esta fase.

## Cobertura sin duplicados de las34 evaluaciones

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
| #61 Make an Anime | [Informe](EVALUACION_MAKE_AN_ANIME_ES.md): E04/E05/E06/E11; no Ruby ni proveedores pagos, B04 |
| #62 MoneyPrinterTurbo | [Informe](EVALUACION_MONEYPRINTER_ES.md): E03/E04/E05/E06/E08; sin director/UI duplicados, B04 |
| #63 VoiceStudio | [Informe](EVALUACION_VOICESTUDIO_ES.md): E16/E04/E05/E10; B08 |
| #64 OpenCut | [Informe](EVALUACION_OPENCUT_ES.md): E06/E10, madurez antes de conexión; B04 |
| #65 TikTok/IG catálogo | [Informe](EVALUACION_SOCIAL_APIS_ES.md): E08; B07 |
| #66 ODS | [Informe](EVALUACION_ODS_ES.md): E01/E05, no reinstalar stack; B05 |
| #67 Concat | [Informe](EVALUACION_CONCAT_ES.md): E01/E05/E06/E10; B04 |
| #68 VibeVoice | [Informe](EVALUACION_VIBEVOICE_ES.md): E04/E05/E16; B08 |
| #69 Pascal | [Informe](EVALUACION_PASCAL_ES.md): E01/E05/E06/E10; B04 |
| #71 Raea | [Informe](EVALUACION_RAEA_ES.md): E01/E04/E05/E06/E11; interno vs distribución B04 |
| #72 WhisperX | [Informe](EVALUACION_WHISPERX_ES.md): E01/E04/E16; B08 |
| #73 PySceneDetect | [Informe](EVALUACION_PYSCENEDETECT_ES.md): E01/E03/E04/E06; comparar baseline FFmpeg |
| #74 Auto-Editor | [Informe](EVALUACION_AUTO_EDITOR_ES.md): E01/E03/E04/E05/E06; sin duplicar cortes |
| #75 ReaVideoBreakdown | [Informe](EVALUACION_REAVIDEO_BREAKDOWN_ES.md): E01/E03/E04/E06/E11; no modificar ComfyUI |
| #76 Cinematic Skill | [Informe](EVALUACION_CINEMATIC_SKILL_ES.md): E01/E04/E05/E06/E11/E14; B07 |
| #77 Streambert | [Informe](EVALUACION_STREAMBERT_ES.md): E06 progreso local de revisión, baja prioridad; B07 |
| #78 Reverb-TTS | [Informe](EVALUACION_REVERB_TTS_ES.md): E01/E04/E05/E16; NC comercial y codec B08 |

No volver a implementar cortes/unión, ASR, karaoke, normalización de mezcla,
adaptadores de aplicaciones, Blender/Krita, cancelación de Qwen#42 ni un director
multietapa por aparecer en otro README. Extender solo la carencia demostrada.
Las tareas seleccionadas se implementarán una a una con pruebas acotadas y manual;
una futura instalación queda separada de apertura, API/panel y automatización real.

## Verificación de esta fase

La tanda #71–#78 añade ocho informes e índice. Se mantienen **16 entregas E01–E16 y8 grupos B01–B08**, con criterios ampliados en los IDs existentes:34 evaluaciones en total (#44–#69 y #71–#78). #70 es corrección de CI, no evaluación de candidato. No se añade otro editor, TTS, descargador, biblioteca o director. Las mejoras de QA y temporización se integran en E04/E05; normalización en E16; progreso de revisión E06 es optativo y de baja prioridad. Todo es documentación. Fuentes upstream
fijadas, licencias leídas y rutas/contratos locales contrastados. Validación estática
de UTF-8/enlaces/IDs/cobertura; CI remota se registra en #3 y PR#2. Sin ejecutar
candidatos, inferencia, indexación, render, audio o medios reales. Configuraciones,
originales, ComfyUI y GitHub Dark conservados; PR#2 permanece en borrador sin merge.
