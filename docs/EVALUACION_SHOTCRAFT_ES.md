# Video Shotcraft — evaluación #100

25-11-2026 UTC. [59f3e9b9e936ff2bce0e18446226d770a3f2f61f](https://github.com/Vincentwei1021/video-shotcraft/tree/59f3e9b9e936ff2bce0e18446226d770a3f2f61f).
Reutiliza #100/7146291307 y 7151162426. Árbol completo:124 recetas Markdown al
excluir `references/shots/ATTRIBUTION.md`;150 shots/previews son el catálogo
anunciado, no renders validados aquí. No confundir mirrors o menciones antiguas.

## Decisión y contraste

Referencia útil para un selector visual de plano y parámetros contextuales:
título, detalle de producto y cierre como piloto futuro pequeño. Ya existen
HyperFrames/Remotion, scene_plan, presets/contratos y revisión visual; no añadir
otro compositor o motor. La galería no puede sustituir el montaje profesional de
#92 ni introducir componentes stock silenciosamente en el modo atelier.

Demos documentados como funciones del frame y helpers de cámara/easing no
acreditan determinismo ni calidad de toda la secuencia en Windows. ClipCard
silencia audio por defecto y exige duración/loop explícitos. Preview del primer
frame, especialmente excluyendo casos con MP4, no valida movimiento o sonido.
Cambios de ritmo deben conservar intención y reloj, no depender de un score.

## Licencias y recursos

[Código/documentación Apache-2.0](https://github.com/Vincentwei1021/video-shotcraft/blob/59f3e9b9e936ff2bce0e18446226d770a3f2f61f/LICENSE).
No se identificó NOTICE raíz; revisar notices por componente si se reutiliza.
[Atribución de audio](https://github.com/Vincentwei1021/video-shotcraft/blob/59f3e9b9e936ff2bce0e18446226d770a3f2f61f/assets/audio/ATTRIBUTION.md)
y [sourcing](https://github.com/Vincentwei1021/video-shotcraft/blob/59f3e9b9e936ff2bce0e18446226d770a3f2f61f/references/sfx-sourcing.md):
SFX por proyecto con manifiesto, CC0/CC-BY por archivo y créditos cuando procedan;
previews MP3 con pérdida, no WAV originales. Convertir a WAV no recupera calidad.
RMS/sample peak no son LUFS/true peak ni escucha aprobada.

El BGM Mixkit sin identificación individual queda excluido de adopción automática;
MIT/Apache del código no resuelve música, texturas, capturas, marcas o fuentes.
Licencia Remotion4.0.484 y elegibilidad de entidad/equipo siguen [#51](EVALUACION_REMOTION_ES.md),
independientes del código Apache. No asumir render $0 si requiere licencia pagada.

## Windows y offline

Plantilla Remotion/CLI4.0.484, React19.2.7, TypeScript6.0.3; no actualizar el lock
actual por copiarla. Node/FFmpeg/navegador y fuentes preparados antes de offline;
Remotion puede descargar Chrome en primer render. Guías principales macOS;
Windows no validado. SF Pro y métricas macOS no se transfieren: usar fuentes
elegibles locales y revisar texto español/acentos a resolución final.
1920×1080/30fps no garantiza vertical/cuadrado con simples escalados.

JianYing Pro11.2 macOS no demuestra CapCut global o Windows. El intercambio es
opcional y con pérdidas explícitas, siempre subordinado al proyecto neutral.
Búsqueda Freesound/publicación online no forman parte del offline; no ejecutar
scrapers, publicadores, descargas, templates o vídeos del catálogo.

| Prioridad / ID | Aceptación futura |
|---|---|
| P1 E06/E11 | Plano con ID/versión, duración, fuentes, zonas seguras y parámetros; mismo estado para seek/preview/export; sin incorporar otro esquema de proyecto |
| P1 E04/E09 | Referencias sonoras conservan origen preview/original, licencia, autor, hash y cambios; tiempos/medición explícitos, sincronía audible revisada aparte |
| P2 E02/#92 | Galería pequeña con controles que operan de verdad; tres planos con medios propios, fuente elegible y ES/ratios; validar secuencia completa en fase autorizada |
| B02/B04/B06 | Elegibilidad Remotion/recursos, métricas tipográficas y piloto Windows/visual pendientes; no prometer acabado profesional por smoke tests |

Evaluación concluida. No se descargan audio/modelos/fuentes ni se instala o renderiza.
