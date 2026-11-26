# Implementaciones priorizadas de las evaluaciones #44–#104 (excepto #70 CI y #92 editor)

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

Entrega P0 E01/#132 [HyperFrames local](HYPERFRAMES_DIAGNOSTICO_LOCAL_ES.md):
catálogo sin npm/npx/CLI/descargas, paquete revisado y requisitos explícitos,
doctor JSON requerido vs opcional e invalidación. E05/E06: staging común por
contenido sin colisiones; volumen0 conservado y fades no implementados rechazados.
23casos nuevos/5adaptados focalizados aprobados; no suites antiguas completas.
Pendientes P1: recursos offline reproducibles y render/seek/cancel/escucha reales.
Consulta real no encontró preparación en rutas revisadas, no ausencia global.
Sin instalaciones/reinicios/ComfyUI;4.5 predeterminado/PR#2 borrador conservados.

Actualización de activación #117/#129:
[validación real en4750](ACTIVACION_117_129_ES.md), PID130700/coherente;
subtítulos portugueses revisados/aplicados, undo/redo/save/reopen exactos en copia.
Selector habilitado,4.5 predeterminado intacto. No repetir ASR/síntesis/piloto;
exportación AV de los nuevos cues no comprobada, pendientes #107 español/#112/#113.

Evaluación independiente [#131 Soundsible](EVALUACION_SOUNDSIBLE_ES.md): biblioteca
y DJ beta0.40.0 fijados a3a619707…, MIT de software separado de música/pesos;
model_path/session y launcher tienen efectos de descarga/instalación. Reutilizar
music_library/audio_energy/audio_mixer/BMTS-Lite antes de nuevo analizador.
E04/E06/E09 P1: beats/entradas/transiciones corregibles y prueba A/B futura;
E01/E05: procedencia/caché/invalidación. Sin instalar ni generar música.

Comparación independiente [#130 FireCut](EVALUACION_FIRECUT_ES.md): ampliar
E03/E04 con propuesta revisable de silencios sobre waveform y E05 con recibos,
sin otro cutter/ASR/editor. Prioridad siguiente: contrato numérico y protección
de palabras/sincronía antes de medición/aplicación AV; E07 repeticiones y E09
multicámara posteriores. Gratis parcial no acredita suite offline/$0; no instalar
ni copiar recursos propietarios. Evaluación documental, integración no realizada.

Entrega P0 E04 [#129](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/129):
[borrador de subtítulos desde palabras guardadas](SUBTITULOS_DESDE_PALABRAS_ES.md).
Extiende #115 mediante su reloj existente, revisión/bases/hash y aplicación
reversible compartida; no ASR nuevo ni otra familia de backlog.15pytest nuevos
y6escenarios Chrome aislados aprobados. Activación agrupada con selector #117,
sin reiniciar4750 ni repetir piloto/muestra portuguesa. Cobertura parcial o
palabras cortadas bloquean el candidato completo. No afirmar validación AV.

Nueva entrega P0 E04 [#115](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/115):
[palabras en reloj del montaje](PALABRAS_RELOJ_MONTAJE_ES.md), inspección compartida
UI/API/agente sin ASR/cues/export. Reutiliza frames del EDL, conserva procedencia,
spans y racionales; reporta palabras parciales/cero y cobertura sin inventar
alineación.25pytest nuevos y control UI sintético(3GET/0POST) aprobados. Activación
pendiente en el mismo lote #112–#115; E04 global no se da por completo.
[Smoke breve preparado #112–#114](COMPROBACION_CONJUNTA_112_114_ES.md), no ejecutado;
sin repetir baterías ni síntesis aprobadas y sin fabricar recibos elegibles.

Siguiente entrega P0 E02 [#114](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/114):
[errores HTTP y formularios conservados](STUDIO_ERRORES_HTTP_ES.md), lector común
sin reintentos, deadline explícito solo en metadatos locales, protección de doble
submit/foco y reconocimiento de creación antes de fallo de refresco.26casos Node
y16escenarios browser sintéticos nuevos aprobados, sin API real ni inferencia.
Se agrupa con #112/#113 para una única activación manual futura; no los repite.

Entrega independiente E02 [#113](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/113):
[contraste y foco de controles](STUDIO_CONTRASTE_FOCO_ES.md). Falla observada del
botón verde3.919:1 corregida a4.631:1, preservando GitHub Dark. HTML/CSS reales
en fixture offline,4viewports/teclado/colores/negativos aprobados, sin servidor
activo ni acciones de producción. Se agrupa con #112 para una activación manual
futura. No se repite #111; E02 completo y validación del panel abierto pendientes.

Seguimiento E05 acotado [#112](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/112):
[recuperación de preescuchas Piper](PIPER_RECUPERACION_ES.md), ID compartido,
recibo/huellas y reconciliación sin repetir proveedor completado.26pruebas nuevas
sintéticas y regresión UI de pérdida HTTP/reload; sin nuevas síntesis españolas.
Preparado para activación posterior, no nueva cola ni cancelación del cálculo.
E05 global permanece abierto. #111 activado/verificado en4750; usuario confirmó
Davefx/Sharvard F/M, valoración natural/robótica aplazada.

| ID / prioridad | Implementación y evaluaciones agrupadas | Reutilización / dependencia | Entrega y aceptación concreta |
|---|---|---|---|
| E01 P0 | Diagnóstico local sin instalaciones y contrato de efectos (#46/#47/#51/#52/#53/#54/#56/#58/#59/#60); ampliado #62/#63/#66/#67/#68/#69; ampliado #71/#72/#73/#74/#75/#76/#77/#78; ampliado #79/#82/#83/#88/#89 | Registry, application/model diagnostics y settings actuales; primero especificación compartida, extensiones por adaptador | Reporta versión observada vs lock/fuente, ruta ausente vs denegada/incompatible, licencia pendiente, efectos lectura/medición/escritura y recursos offline. Fixtures de paths Windows/symlinks, dependencia ausente y timeout; nunca npx/pip/download/upgrade implícito. No reauditar instalaciones aprobadas sin necesidad. Servicio externo vs propio, PID/puerto/instancia y code revision vs image digest separados; requisitos de Node/runtime/loader no obligan a actualizar lo aprobado. Preflight distingue recursos preparados de descargas de codec/tokenizer/preset; tamaño cuantizado en disco no acredita memoria de ejecución. Sin reinstalar lo aprobado. Perfil completo de imagen/música incluye transformer/DiT/encoder/VAE/LM/variante/backend/offload y licencia por recurso. Reutilizar familias flux-klein/acestep catalogadas; ruta catalogada ausente no demuestra falta global ni autoriza descarga. Hypit/Codex global y ComfyUI no se alteran. |
| E02 P0 | Accesibilidad y robustez Studio (#45/#58; tokens #59/#60) | CSS/HTML/JS GitHub Dark y pytest/Playwright existentes; no instalar detectores | Contrato único de tokens y pruebas de contraste, teclado/foco, nombres/errores,320–1280px, zoom y textos españoles/rutas largas. Primero verificar riesgo del botón verde de #45; cambios solo por fallos observados. Fixtures API400/403/500/timeout y preservar input. Ningún gate estético, hooks o nueva UI/framework |
| E03 P0 | `clip_candidates` trazables y selección española (#44; medición #54 no decide semántica); ampliado #62; ampliado #73/#74/#75; ampliado #84/#85 | ASR preparado, Ollama, transcript y scene/edit_decisions; no instalar PeakCut | Esquema fuente/hash/transcript/lang/inicio-fin/motivo/modelo. Rechaza NaN/Inf, reloj incorrecto, rango fuera de fuente y duplicados; conserva rechazados y aprobación. LLM simulado etiquetado; no viralidad inferida de score. Asociación de cada recurso al fragmento de guion con fuente/licencia; no generar ni buscar stock para probar el contrato. Candidatos de límite por contenido/adaptación/fundido y señales booleanas de audio/pista/movimiento llevan método, umbral y falsos positivos. FPS/PTS y fin exclusivo explícitos; no equivalen a saliencia. Comparar con FFmpeg antes de otra dependencia. Selección de clips reutiliza ASR/Ollama; score no prueba viralidad. Tracking y suavizado ya existen: no duplicarlos ni otro downloader. |
| E04 P0 | Puente palabras/subtítulos y presets de encuadre (#44/#46/#51/#52/#54/#55); ampliado #61/#62/#63/#68; ampliado #71/#72/#73/#74/#75/#76/#78; ampliado #79/#85/#86/#89/#90 | ASR español/subtitle_gen/CaptionWord/auto_reframe existentes; E03 usa el contrato | Normaliza segundos/frames/offsets y fps racional sin perder palabras; ASS escapado, acentos/¿¡, sin voz/idioma incierto y zonas seguras por ratio. Casos de datos y strings sin audio/render. Preset vertical no significa seguimiento facial validado; no otro ASR/descargador. Añadir speaker local y spans sin atribuir identidad, parcial/final de ASR streaming y timestamps voz→plano. Fixtures de solape/code-switch/silencio; no truncar ni acelerar doblaje sin decisión explícita. Separar alineación medida, estimada e imputada; alineación no exige diarización ni puede degradarse silenciosamente. Palabras finales y segmentos alineados comparten reloj; mapear cortes/eliminaciones/velocidades al tiempo de salida preservando spans. Anclaje por reparto de letras no es alineación. QA de subtítulos/zonas seguras incluye región/intervalo/método/umbral/evidencia y desconocido explícito. Split/merge de cues conserva spans y rechaza base obsoleta. Crop probado con cajas sintéticas incluye cara ausente/múltiple/corte de plano y PTS; fallback explícito, sin garantía visual. PixelFX distingue120Hz simulación,12fps poses y fps final; freeze/evento no altera causalidad. Voz conversacional conserva speaker/idioma/tiempos. |
| E05 P0 | Ciclo de jobs multimedia compartido (#46/#47/#51/#52/#54/#56); ampliado #61/#62/#63/#66/#67/#68/#69; ampliado #71/#74/#76/#78; ampliado #79/#81/#83/#84/#85/#86/#87/#88/#89/#90 | Studio jobs/recibos/cancelación y puentes existentes; E01 | ID/estados persistentes, progreso, timeout, stop y reconciliación por backend; cerrar socket/espera separado de terminar inferencia/proceso. Mocks de caída, corrupción, parcial y stop durante etapa; nunca repetir herramienta/segmento con recibo válido. Propiedad de proceso/árbol y original intacto. Lo aprobado en Qwen#42 se reutiliza, no se repite como validación de renderer. Invalidación por hash/versión de guion/voz/asset/ratio y fallos de variante2 conservando variante1; chunks parciales nunca se promocionan a finales. Servicio externo no se detiene por ocupar puerto. Informe QA final estructurado: hallazgo, región/tiempo, evidencia y alcance; distingue freeze intencional, loudness medido y calidad visual no evaluada. Con datos/mocks validar errores/invalidation y evitar declarar aprobación por metadata/decode; prueba audiovisual queda en B06. Activación de componente preparado verifica hash/versión y falla con rollback explícito, conservando anterior ante lock Windows/interrupción; sin update global. Caché por hash/modelo/idioma/params, no basename/mtime. Ventanas/eventos cambian contexto e invalidan derivados. Publicación social es extensión de baja prioridad SOLO con mocks: aprobación ligada al hash, estados uncertain y reconciliación, no retry ciego ni cron real. |
| E06 P1 | Intercambio neutral de proyectos/escenas (#46/#49/#52/#55; diseño #59/#60); ampliado #61/#62/#64/#67/#69; ampliado #73/#74/#75/#76/#77; ampliado #79/#82/#83/#84/#86/#87/#88/#89/#90 | edit_decisions, rig_plan, pose_library y formatos Blender/Krita guardados; E04/E05 | Un sobre común de IDs/revisión/assets/hash/tiempos/unidades/jerarquía/cámara y extensiones por formato. Round-trip JSON sintético distingue pérdidas/unsupported; editar candidato con diff/undo/snapshot y rechazo de base obsoleta. No ejecutar HTML/código externo. No prometer convertidor universal ni export creativo aprobado. Extensiones de máscaras/roles y edificio/nivel/pared/abertura/IFC GUID; imported-mesh/derivado no se declara paramétrico. Cast/location/voz versionados, cambios invalidan solo dependientes; fuente y escena candidatas separadas. Shot record neutral distingue medición, estimación de cámara y descripción inferida por VLM; raw JSON no parseado es error, no evidencia validada. Export temporal conserva pérdidas/versión/timebase. Solo si útil, progreso de revisión local entre sesiones (baja prioridad) por identidad/hash, esquema validado sin secretos/rutas personales por defecto; no duplicar jobs ni biblioteca. Presets versionados y multirreferencias ordenadas por ID/hash/rol; música distingue instrumental/letras/idioma/tempo/repaint e intervalo protegido. Conversación fuente→afirmación→turno→speaker→perfil, sin otro TTS/UI. Asset pixel lleva paleta/semilla/pivote/alpha/buffers color-luz/capa y tiempos; unsupported explícito. Ningún paquete/plantilla externa se ejecuta por importar contrato. |
| E07 P1 | Diagnóstico editorial español (#48); ampliado #91, reutiliza #48 | script_diagnostic/reviewer, original/historial y Ollama actual | Reglas versionadas, lengua/offsets Unicode y severidad; `unscored`/error distintos de limpio. Corpus sintético técnico/deportivo/bíblico, falsos positivos; candidato separado y preservación de cifras/citas/negaciones/atribución. Diagnosticar nunca reescribe ni juzga autoría humana STE80 amplía el mismo módulo: condición→acción, glosario y modo por género. No traducir regex A–Z/listas/umbrales ingleses como validación española. Mock should→must/may→can se rechaza por modalidad; no inventar actor/causa para voz activa. Diagnóstico no reescribe, no certifica STE ni autoría. |
| E08 P1 | Research con muestras propias y baselines (#50); ampliado #62/#65; ampliado #80/#81/#86/#87 | youtube_client/channels, CSV propietario, dossiers y vidIQ manual | URLs/fecha/filtros/n/edad/formato/periodo y fórmulas; mediana0, ocultos/faltantes/duplicados dan desconocido explícito. Mocks de comentarios/hilos/páginas/cuota/desactivados; no inventar RPM/monetización. Cache/watchlist muestra vencimiento. Red fresca y TubeLab no necesarias para probar contrato. Esquema platform/namespace sin romper UC IDs; snapshots CSV/JSON propios, permisos/cobertura/métricas por plataforma. TikTok/IG nuevos no se anuncian implementados por importar tabla. Temas de comentarios enlazan IDs/citas/contexto/denominador y sesgos de muestra. Dossier conserva afirmación→pasaje/hash/fecha, unsupported/contradicción y presupuesto de consultas/tiempo/bytes; fuente fallida no habilita red ni se transforma en evidencia. Extiende #50/#65, sin ScrapeCreators ni segundo agente/índice. |
| E09 P1 | Sincronía y drift con medición explícita (#54) | FFmpeg/ffprobe, audio_probe y audio_mixer; E01/E05 | Datos/mock de señales con offset/ppm conocidos, confianza/tolerancias y razones de omisión ante silencio/ruido/cola corta. LUFS/true peak medidos separados de normalizar mezcla. Prueba con audio sintético codificado queda para fase autorizada; no medios reales ni declarar lip-sync visual |
| E10 P1 | Contrato de lectura MCP/local por capacidades (#46/#53/#59); ampliado #63/#64/#67/#69; ampliado #79/#81/#89 | Puente del agente y errores/procedencia; E01/E05/E06 | Loopback/identidad/scope/versión, allowlist efectiva, timeouts y errores estructurados. Servidor falso rechaza escritura/desconocido/ruta fuera de proyecto. tools/list y readOnlyHint no sustituyen enforcement. No conexión/install del editor/índice/prototipador físico para comenzar. Concat window/headless explícito, roots/locks/auth y status de export; Pascal escena activa por servicio y un cliente, home/procesos separados. OpenCut requiere código API real antes de conectar; lectura de perfiles no incluye creación/clonación. Fuente documental o paquete no puede ampliar scope/egreso ni instrucciones de agente. Mocks de redirección, endpoint relay y archivos fuera de proyecto; loopback no equivale a modelo offline. |
| E11 P1 | Eventos semánticos de animación (#55; poses/cámara #49); ampliado #61; ampliado #75/#76; ampliado #88/#89/#90 | scene_plan/character QA/Ink Theater/Ink Puppet y E06 | Cue/evento/actor/objeto/antes-después/propósito/tiempos y anclajes; fixtures de IDs rotos, conectores invertidos y decoración mal atribuida. Revisión visual futura sigue independiente; no generar geometría/animación ni importar catálogo de demos. Biblia/cast/location vinculados a toma y cámara; reutilizar from_take solo con dependencias/recibo compatibles y evidencia, nunca aprobación copiada de ejemplo. Cámara óptica estimada incorpora incertidumbre y escala/cadencia; sujeto/paralaje pueden confundirla. Eventos de palabra usan ocurrencia/span y origen del tiempo; no heredan certeza de heurísticas. Ventanas/contexto/eventos enlazados por revisión; cambio de actor o ancla incierta no conserva certeza anterior. Asset procedural distingue draw(t) de simulación avanzada por pasos; semilla sola no acredita seek determinista. |
| E16 P1 | Perfil trazable de voz y elegibilidad (#63/#68; timing #61/#62); ampliado #72/#78; ampliado #86, perfil Kokoro existente | Adaptadores Kokoro/Qwen/ASR preparados, E01/E04/E05; sin otra UI | Motor/variante/loader/revisión/hashes, voz/idioma y referencia autorizada con derechos separados. NC/unknown bloquea uso monetizado, AGPL de app no licencia pesos. Lotes/pausas preservan perfiles y segmentos; mocks de cambio de voz, parcial/error y ruta denegada. Calidad/identidad/doblaje real requiere fase posterior; no audio en evaluación Normalización española independiente: original inmutable, hablado, mapa de sustituciones, idioma/opciones/versión y procedencia. Fixtures de cifras/monedas/fechas ambiguas/unidades/siglas/emoji; offsets Python codepoints vs JS UTF-16 explícitos. Pesos Reverb NC bloqueados comercialmente; codec y preset con elegibilidad separada. Mocks sin voz ni modelos nuevos. Reutilizar binding es→e, prefijo de voz y carga local, sin otro catálogo. Speaker de conversación apunta a perfil elegible; no voz nueva ni derechos inferidos por filename. Texto original/hablado y pausas mantienen procedencia. |
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
| B01 | H3 en FreeVideo/OpenJutsu (#47/#56) #88 MovieRoll. | Licencia territorial/outputs/uso del artefacto exacto, inventario cerrado con huellas/tamaños y perfil de hardware. No asumir laptop8GB/16GB cumple demo16GB/64GB. Necesita runtime/ComfyUI separado, nunca parchear el actual MovieRoll nativo exige FA3 Hopper/sm90 y no tiene CPU offload;4090/5090 y playback siguen TODO.96GB es ejemplo de capacidad, no mínimo universal. Licencia Tencent excluye UE/ReinoUnido/CoreaDelSur y5(c) incluye outputs/resultados: ejecutar en México no habilita distribución global. Componentes Qwen/ByT5/Glyph/VAE separados; no instalar SGLang/vLLM para eludir bloqueo. | E01/E05/preflight/contratos de máscaras; WAN/LTX existentes conservados |
| B02 | Remotion ejecutable/distribución (#51) | Elegibilidad según versión/licencia y entidad/equipo; lock4.0.484 no prueba instalación. Si exige pago, excluida por costo$0. Navegador/paquetes locales y recursos/fuentes offline comprobados antes de render | E04/E05/E06 con mocks; no fallback silencioso de motor |
| B03 | Grafo CGR real (#53) #81. | Python>=3.12 y wheel nativo Windows/licencias en entorno aislado; perfil sin embeddings/descargas/web, índice exclusivo/exclusiones y benchmark Local Deep Research requiere Python>=3.12,<3.15; estable2.0.4 y avisos de seguridad revisados, no despliegue acreditado. No cambiar .venv3.11 para incorporar otro investigador/índice. | E13 corpus/contrato + rg; no modificar .venv/ComfyUI |
| B04 | Nuevos editores/runtimes (#46/#49/#52/#55); #61/#62/#64/#67/#69 #71/#73/#74/#75/#76. #79/#82/#83/#84/#89. | Licencias de componentes/NOTICE/recursos, requisitos efectivos de paquete y sandbox, fuentes/assets y lifecycle. OpenFilm intenta aprovisionar Chromium al primer uso; ArtCraft tiene rutas cloud/recursos excluidos. OpenCut rewrite no maduro/Classic archivado; Concat beta requiere build/modelos/codecs y modo. Pascal runtime aparte/WebGPU/IFC parcial; Anime depende de Fal/ElevenLabs y Swift macOS, MoneyPrinter local puede llamar proveedores externos. Raea FSL: uso interno permitido según finalidad; distribución/servicio exige evaluar Competing Use, avisos y componentes, sin prohibir toda distribución ni anticipar Apache antes del aniversario de cada versión. Runtimes/editor nuevos y plugins ComfyUI siguen condicionados; no tocar ComfyUI. Hypit licencia personalizada: interno/clientes/single-tenant permitido según condiciones; hosted/SaaS/multi-tenant incluso gratuito y suministro para beneficio comercial restringidos sin autorización; avisos en CLI/reports/manifests. No tratar como Apache ni prohibir toda publicación de forks. FLUX4B Apache separado de9B/devNC y discrepancia8/13GB; ACE-StepXL>=12GB no válido en8GB. AGPL ShortVideoFactory no es MIT. | E06/E10/E11 especificaciones sin ejecutar apps, sin otra UI |
| B05 | Suite de diseño/prototipado/coordinación (#57/#58/#59); #66 | Multica solo alcance interno elegible y stack completo; Penpot digests/DB/assets/offline y recursos, MCP con permisos acotados; Impeccable binario revisado sin hooks/Live. GitHub App/autorizaciones si se adopta sincronización Multica, no indispensable para seguimiento actual. ODS prerelease/WSL/Docker requiere cierre de requisitos/licencias; Pixel ODS-only no extraíble, tagv3.0.0 afectado por advisory no desplegable. | E02/E10/E14/E15. Mantener GitHub Dark y conector actual |
| B06 | Export/QA audiovisual o visual física (varios) #82/#83/#85/#88/#89/#90. | Política/recursos de navegador, fase autorizada con medios sintéticos, luego revisión visual/auditiva. Preview/executable localizado/schema válido no acreditan calidad ni automatización completa Memoria/calidad/precisión española/QA visual y export PixelFX no probados por mocks. Fuente Patch Pixel excluida de MIT: no copiar ni redistribuir; usar fuente elegible local. Hypit64Chromium no es perfil de laptop. | Tests de datos, contratos y procesos simulados; no evasión de restricciones |
| B07 | Fuentes externas/servicios/derechos (#44/#50/#60); #65 #76/#77. #79/#80/#81/#84/#85/#86/#87. | Directos/datos frescos requieren red y derecho de uso; TubeLab de pago excluido. Comentarios/ASR/captions tienen permisos/cuotas; no extrapolar muestras ni autores. Fuentes/íconos/marcas tienen licencias propias. Crédito Apify finito no garantiza operación$0; Display/Instagram tienen scopes concretos y Research TikTok requiere elegibilidad, no bypass de acceso. Streambert: no adoptar streaming/proveedores/descargador. TMDB comercial requiere licencia separada; términos AniList inaccesibles (403), sin permiso inferido. Recursos Commons/fonts exigen registro de derechos y procedencia; filtro automático no sustituye elegibilidad. ScrapeCreators créditos/caché no garantizan datos frescos$0; SearXNG local usa Internet. EdgeTTS y ranking OpenAI/Gemini de AIShorts son online; OpenAI-compatible no demuestra Ollama integrado. Anthropic/Firecrawl/Arcade/publicación social necesitan términos/permisos/costo por servicio; no cuentas/cron/mensajes. | Snapshots propios, CSV/mocks, fuentes sistema/locales y research cache con fecha |
| B08 | Motores de voz/ASR/doblaje nuevos (#63/#68) #72/#78. #83/#86. | OmniVoice default NC/tokenizer con términos propios; licencia de app no los habilita. VibeVoice metadata MIT no sustituye textos de recursos; TTS original retirado, ES Realtime experimental, loaders/CUDA/CPU/memoria sin validar. Inventario primero, sin pesos nuevos Reverb pesos CC-BY-NC-4.0: uso comercial bloqueado, no instalación automática pendiente. Codec Boson incorpora términos Meta/avisos y umbral100.000 usuarios anuales; preset sin derechos independientes no habilitado. WhisperX requiere inventario de alignment/NLTK/diarización; token/condiciones pyannote independientes, nunca descargas implícitas. Kokoro/Qwen perfiles existentes se conservan; documentos Podcastfy no acreditan TTS offline. Pesos/encoders/LoRA/voz y recursos de referencia exigen licencias propias, sin descarga implícita. | E16/E04/E05 con mocks y motores existentes, sin duplicar ASR/TTS |

No se necesita una respuesta del usuario para completar estas evaluaciones.
Los bloqueos se refieren a adopción/ejecución futura, no a impedimentos documentales.
No comprar licencias, crear cuentas/Apps, aceptar términos, descargar pesos ni
activar instancias para intentar cerrarlos en esta fase.

## Cobertura previa sin duplicados de las47 evaluaciones #44–#91

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
| #79 OpenCreator | [Informe](EVALUACION_OPENCREATOR_ES.md): E01/E04/E05/E06; B04 |
| #80 Social Research Methods | [Informe](EVALUACION_SOCIAL_RESEARCH_METHODS_ES.md): E08; B07 |
| #81 Local Deep Research | [Informe](EVALUACION_LOCAL_DEEP_RESEARCH_ES.md): E08/E05/E10; B03/B07 |
| #82 FLUX.2 klein4B | [Informe](EVALUACION_FLUX2_KLEIN_ES.md): E01/E05/E06 existentes; B04/B06 |
| #83 ACE-Step1.5 | [Informe](EVALUACION_ACESTEP15_ES.md): E01/E05/E06 existentes; B04/B06 |
| #84 Short Video Factory | [Informe](EVALUACION_SHORT_VIDEO_FACTORY_ES.md): E03/E04/E05/E06; B04 |
| #85 AI Shorts Generator | [Informe](EVALUACION_AI_SHORTS_GENERATOR_ES.md): E03/E04/E05, tracking ya existe; B07 |
| #86 Podcastfy | [Informe](EVALUACION_PODCASTFY_ES.md): E04/E05/E06/E08/E16, perfil Kokoro; B08 |
| #87 Social Media Agent | [Informe](EVALUACION_SOCIAL_MEDIA_AGENT_ES.md): E05/E06 baja prioridad; B07 |
| #88 MovieRoll | [Informe](EVALUACION_MOVIEROLL_ES.md): E05/E06/E11; B01 hardware/licencia |
| #89 Hypit | [Informe](EVALUACION_HYPIT_ES.md): E04/E05/E06/E11; B04 distribución |
| #90 PixelFX | [Informe](EVALUACION_PIXELFX_ES.md): E04/E05/E06/E11; fuente excluida B06 |
| #91 STE80 | [Informe](EVALUACION_STE80_ES.md): E07 único con #48, sin otro humanizador |

No volver a implementar cortes/unión, ASR, karaoke, normalización de mezcla,
adaptadores de aplicaciones, Blender/Krita, cancelación de Qwen#42 ni un director
multietapa por aparecer en otro README. Extender solo la carencia demostrada.
Las tareas seleccionadas se implementarán una a una con pruebas acotadas y manual;
una futura instalación queda separada de apertura, API/panel y automatización real.

## Verificación de esta fase

La tanda #79–#91 añade13 informes e índice. Se mantienen **16 entregas E01–E16 y8 grupos B01–B08**, con criterios ampliados en los mismos IDs:47 evaluaciones (#44–#69 y #71–#91); #70 es CI. Solo carencias contrastadas: rollback de componentes preparados, dossier/citas/presupuestos, perfiles completos imagen/música, presets/turnos y publicación incierta mediante mocks, eventos/asset pixel y extensión editorial E07. Tracking/crop, Kokoro, flux-klein y ACE-Step ya tienen código/perfil/catálogo: no se registran como conectores nuevos. Todo es documentación; bloqueos de adopción no son tareas de instalación automáticas. Fuentes upstream
fijadas, licencias leídas y rutas/contratos locales contrastados. Validación estática
de UTF-8/enlaces/IDs/cobertura; CI remota se registra en #3 y PR#2. Sin ejecutar
candidatos, inferencia, indexación, render, audio o medios reales. Configuraciones,
originales, ComfyUI y GitHub Dark conservados; PR#2 permanece en borrador sin merge.

## Ampliación #93–#104 — 25-11-2026 UTC

Se añaden12 evaluaciones: total59 (#44–#69, #71–#91 y #93–#104), conservando
16 entregas E01–E16 y8 bloqueos B01–B08. #92 es implementación del editor,
no otra evaluación. [Índice y fuentes de esta tanda](EVALUACIONES_93_104_ES.md).
Las aceptaciones siguientes amplían las filas anteriores; no abren otros motores.

| Familia / prioridad | Carencia demostrada y aceptación añadida | Informes |
|---|---|---|
| E01/E02 P0 | Identidad residente vs archivos servidos/capabilities: detectar revisión mezclada o reinicio necesario sin reiniciar automáticamente. Mantener contrato único UI/agente. Panel no promete operación por estar en catálogo. | [#93](EVALUACION_OPENSHOT_ES.md), [#99](EVALUACION_PHOSPHENE_ES.md) |
| E01 P0 | BgRemove ya fija u2net: no hereda hoy BRIA implícito. Resolver modelo/cache elegible explícito, licencia/huella/procedencia, error sin descarga o proveedor alternativo oculto. Perfil H3 separa encoder32B/VAE/LoRA y tiempo real. | [#94](EVALUACION_REMBG_ES.md), [#95](EVALUACION_H3_WORKFLOW_ES.md), [#98](EVALUACION_LONGLIVE_ES.md) |
| E03/E04 P0 | Candidatos por índice/ocurrencia de palabra y tiempos medidos, contexto y aceptación manual; crop editable/confianza/fallback ancho. No nuevo ASR, downloader ni puntuación viral. Snapping considera títulos/capas además de cortes/audio/cues, misma base temporal racional. | [#103](EVALUACION_AUTOCLIP_ES.md), [#93](EVALUACION_OPENSHOT_ES.md) |
| E05 P0 | Versionar toma/resultado y recursos compatibles; cancelar/reanudar sin repetir completados; solicitado/transporte cerrado/cómputo detenido/parcial son estados distintos. Formato QA y evidencia semántica/AV no intercambiables. | [#97](EVALUACION_CODE2VIDEO_ES.md), [#99](EVALUACION_PHOSPHENE_ES.md), [#104](EVALUACION_VOICEBOX_ES.md) |
| E06/E16 P1 | Proyecto neutral para capas/máscaras/texto/tomas/voz, pérdidas explícitas, undo/redo/reapertura. Regional Chatterbox V3 no se conecta por nombre al loader actual; tags y lenguas por variante, Kokoro es→e existente. | [#94](EVALUACION_REMBG_ES.md), [#96](EVALUACION_CHATTERBOX_ES.md), [#101](EVALUACION_PHOTOCRAFT_ES.md), [#104](EVALUACION_VOICEBOX_ES.md) |
| E10/E12 P1 OBS | Doctor autenticado de lectura/RPC/métodos disponibles; futuro start/stop explícito con propietario y reconciliación, nunca ToggleRecord ciego ni stop ajeno. Archivo nuevo con roots/procedencia importable. Puentes gráficos/audio no heredan toda REST por tener MCP. | [#102](EVALUACION_OBS_ES.md), [#101](EVALUACION_PHOTOCRAFT_ES.md), [#104](EVALUACION_VOICEBOX_ES.md) |
| E08/E09/E11 P1/P2 | Spec/fuentes/eventos medidos, QA por ventanas con presupuesto, audio original vs preview y licencia por recurso, mismo seek/preview/export. No llamar sincronía visual a detección de onsets, ni RMS a LUFS. Galería pequeña posterior, no importar catálogo creativo a atelier. | [#97](EVALUACION_CODE2VIDEO_ES.md), [#100](EVALUACION_SHOTCRAFT_ES.md), [#98](EVALUACION_LONGLIVE_ES.md) |

### Precisiones de bloqueos existentes

- **B01: distinguir MiniMax de Tencent.** H3 Community fija exclusión de UE,
  Reino Unido, Corea del Sur **y Estados Unidos**; cláusulaV.4 afecta outputs y
  revenue comercial anual superior aUSD20M requiere autorización previa. No
  confundirlo con MovieRoll/Tencent (territorios UE/UK/Corea, umbral100M MAU y
  cláusula5(c)). El workflow H3 de #95 no tiene LICENSE y no autoriza copiarlo.
  LongLive1.3B declara CC-BY-NC-SA4 (uso comercial bloqueado);2.0 usa NVIDIA Open
  Model License con obligaciones propias, no Apache del código. Plug no elimina
  condiciones de base. Ninguna de estas demos acredita8GB ni Windows local.
- **B03/B04:** Code2Video tiene pesos27B Apache2, pero repositorio/scripts sin
  LICENSE. Phosphene MIT es MLX/Apple, no ruta Windows probada. PhotoCraft alpha
  no promete PSD/KRA/ORA sin pérdidas y su marca/recursos no heredan MIT/Apache.
  Mantener B02 Remotion, derechos de recursos Shotcraft, Hypit y PixelFX previos.
- **B08:** TADA Llama3.2 y tokenizer no se vuelven MIT por codec/mirror; BRIA
  comercial requiere acuerdo, no se habilita por licenciaMIT de rembg. Chatterbox
  regional y companions requieren compatibilidad/identidad, no nueva descarga
  automática. Reverb NC continúa bloqueado comercialmente y Raea conserva la
  distinción uso interno/distribución; no se flexibilizan condiciones previas.
- **B06/B07:** No se ejecutaron OBS, GUI, voces, clips o redes sociales. Offline
  anunciado, cobertura de formatos o un endpoint no acreditan resultado real.

### Verificación de esta ampliación

Continuación independiente E01/#110: [BgRemove local explícito](BG_REMOVE_LOCAL_ES.md),
sin default/fallback/descarga de pesos, revisión declarada ligada a SHA y recibo
de procedencia.24pruebas focalizadas nuevas/adaptadas con proveedores/ONNX ficticios;
sin segmentación real, instalación ni nueva evaluación. E05/cancelación y calidad
visual siguen pendientes. [Activación agrupada](ACTIVACION_AGRUPADA_STUDIO_ES.md)
con #109/45b8609 y #108; sin reinicio en esta entrega. #107: portugués validado,
español pendiente, sin repetir comprobaciones aceptadas.

Confirmación humana registrada en #107: **muestra portuguesa validada**; la
española sigue pendiente y no se repiten las comprobaciones aceptadas. E04/#109
[idioma de subtítulos](IDIOMA_SUBTITULOS_STUDIO_ES.md): contrato compartido, und
en proyectos nuevos, declaración explícita para soft export, compatibilidad
antigua sin migrar.16casos pytest nuevos aprobados (incluye2Node y3muxes sintéticos
de0.4s), sin repetir muestra/ASR/CI. Activación local nueva pendiente, no reinicio.

Actualización #107: [entorno ASR aislado y muestra portuguesa](FASTER_WHISPER_AISLADO_PT_ES.md)
conFaster-Whisper1.2.1/CT2 4.9.1, pesos locales sin descarga. Inferencia CPU/int8
real0–25s:116palabras/12segmentos; copia22.72s,3candidatos,24subtítulos portugueses
incrustados y cambio de encuadre11.52s exportados. Original intacto; solo settings
del adaptador ASR autorizados. Validación española/escucha/ventana y comparación
transparente de audio pendientes; no se cierran E03/E04/E09 ni #107 por métricas.

Actualización #107 tras reconectar D:/E:: herramientas guardadas FFmpeg/FFprobe9.0.2
confirmadas con -version, sin cambios/descargas/copias de herramientas. Exportación
real3.416667s/1080×1920 H.264/AAC/mov_text aprobada técnicamente; encuadre comparado
con fuente, audio no silencioso y SRT0.5–2.5s extraído. [Evidencia actual](VALIDACION_CANDIDATOS_HTTP_ES.md).
El bloqueo físico del párrafo histórico siguiente queda levantado; #107 continúa
abierto por ventana/interacción/escucha no verificadas, no por falta de MP4.

Seguimiento #107: [activación y HTTP real en copia](VALIDACION_CANDIDATOS_HTTP_ES.md)
comprobados, candidatos/undo/reopen y encuadre persistente. Exportación AV bloqueada
por D: no conectado; #107 abierto, sin afirmar resultado audiovisual.
Continuación E01 [#108 diagnóstico de rutas](DIAGNOSTICO_RUTAS_MULTIMEDIA_ES.md):
7casos nuevos aprobados, distingue unidad/archivo/permiso/E/S sin cambiar rutas
ni fallback. Activación de ese texto en el proceso abierto no certificada.

Implementación [#107](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/107),
E03/E04 desde #103: candidatos por ocurrencia de palabra/tiempos, motivo,
contexto/negación y cobertura ASR declarada con huecos; aceptar/rechazar/corregir
e insertar en el EDL mediante add/trim existentes, undo/reopen compartidos.
Revisión visual local de fuente/foco/zoom/bandas aplica transform/FFmpeg actual,
sin nuevo tracker/ASR/AutoClip. [Manual y límites](CANDIDATOS_ENCUADRE_STUDIO_ES.md).
15pytest nuevas aprobadas, incluyendo wrapper de6Node; datos/DOM sintéticos,
no validación AV/ventana. Activación4750 y comprobación con medios pendientes;
trayectorias/keyframes/zona segura dinámica siguen pendientes de E04. No se
marca completa toda la familia ni se repiten suites aprobadas.

Seguimiento de implementación [#105](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/105):
E01/E02 identidad residente/UI/API/capacidades implementada y probada de forma
focalizada; [manual y límites](IDENTIDAD_COMPATIBILIDAD_STUDIO_ES.md). Activación
en4750 pendiente de reinicio manual, no autorizado automáticamente. No se marca
completa toda E01/E02 ni se considera resuelto el diagnóstico HTTP.

Continuación [#106](https://github.com/D3ckardCain/OPENMONTAGE-IA/issues/106),
E04/#93: snapping existente ampliado a límites de capas/títulos, sin escribir EDL
ni añadir otro motor. [Manual y alcance](SNAPPING_CAPAS_TITULOS_ES.md);3casos Node
numéricos nuevos aprobados. Interacción de ventana local pendiente, no inferida
de las pruebas; no se repiten regresiones antiguas ni se reinicia Studio.

Solo comprobación documental de UTF-8/enlaces/cobertura/pins; no repetir suites
ni CI aprobadas, no instalaciones/modelos ni captura HTTP/red. El diagnóstico
HTTP queda preservado como observación con causa raíz pendiente. Cierre de
evaluación significa informe/decisión completos, no integración ni AV validado.

## Preparación #117 — Blender paralelo, 25-11-2026

Extensión de E01/E06/E10/E11 existentes, sin nueva familia ni otro MCP:
[plan y aceptación](BLENDER_117_PREPARACION_PARALELA_ES.md),
[versiones/checksums/destinos](BLENDER_117_PLAN_20261125.json).
5.3.0 portable paralelo es el candidato reciente;4.5.15LTS conserva MN4.5.11
y Archimesh ya registrados. Enlace/tamaño/SHA256 oficiales publicados antes de
descargar; no binario descargado/instalado ni cambio de ruta activa en esta fase.
MN520.2.0 ya existe y se reutilizará como candidato; rango/ABI no prueban carga.

Aceptación incremental: provisión verificada en carpeta nueva/perfil aislado;
registro sin red/ABI real; selección explícita del mismo perfil Studio/agente;
adaptación del runtime EEVEE/acciones/samples a5.x con error ante incompatibilidad;
copia .blend y QA autorizados antes de migrar. El actual centro de actualizaciones
no tiene comparación automática Blender ni Applications selector multiperfil:
ampliarlos sin duplicar centro/instalaciones. No actualizar únicamente4.5 ni
instalar también5.2 por rutina; mantenimiento4.5.17 se evalúa por separado.

La activación previa #112–#115 ya tiene [evidencia local](ACTIVACION_112_115_RESULTADOS_ES.md).
#112 recuperación de completado sin recibo elegible y acciones ocultas de#113
siguen pendientes; no repetir síntesis/pruebas aprobadas ni reiniciar Studio.

### Provisión #117 — 26-11-2026 UTC

[Perfiles/uso/resultados](BLENDER_PERFILES_STUDIO_ES.md) y
[evidencia](BLENDER_117_VALIDACION_20261126.json): ZIP5.3.0 descargado/verificado
y extraído en ruta nueva, perfil/cp313 aislados. CLI/ventana y doctor5.3 reales;
API EEVEE/channelbags y seis capacidades del candidato comprobadas sin render.
Archimesh y MN520 cargan desde ZIP existentes;4.5/MN4.5.11 conservados.
Registro compartido4.5/5.3, API y selector implementados/probados en copia aislada,
sin fallback.4750 mismoPID: catálogo conoce ambas versiones por carga diferida,
pero selector deshabilitado hasta activación de rutas. No afirmar activación
por registro/catálogo; ninguna orden de reinicio ejecutada.14pruebas nuevas,
tres verificaciones de delta y sintaxis focalizada; no repetir suites aprobadas.
Pendientes: activación agrupada, uso real de complementos/28skills y QA creativo;
#112 y acciones ocultas#113 permanecen pendientes. Coste$0/PR#2 borrador.

### Piloto funcional #117 — 26-11-2026 UTC

Se amplía la evidencia de E01/E06/E10/E11 sin crear otra familia de backlog:
[piloto real y manual](BLENDER_117_PILOTO_ES.md),
[resultados numéricos](BLENDER_117_PILOTO_20261126.json).
Blender5.3/EEVEE generó una escena propia editable con materiales, tres luces
y animación de tres segundos; MP4 decodificado completo y revisado visualmente.
QA fijado de Blender-Skills pasó en las tres mallas. Doce casos nuevos
focalizados; no repetir suites anteriores. No certifica todas las skills ni
calidad artística final. 4.5 sigue por defecto. Activación del selector/API y
descubrimiento de herramienta agrupados para un futuro reinicio manual único;
no se reinició4750. #112 y acciones ocultas#113 conservan sus pendientes.
