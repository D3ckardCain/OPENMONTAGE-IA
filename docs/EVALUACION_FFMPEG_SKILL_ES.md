# ffmpeg-skill: evaluación #54

24-11-2026 UTC. `kajisho5/ffmpeg-skill@bad487c5c4c1d3db52893b27d5ff1278da5274a8`,
package 4.7.1. Lectura estática; SKILL.md se analizó como documentación externa,
sin instalar sus instrucciones, MCP, paquetes ni ejecutar sus operaciones.

## Decisión y solapamientos

Reutilizar contratos derivados de argparse y patrones de verificación; no registrar
42 wrappers ni reemplazar el director. Primero cubrir carencias justificadas de
medición de sincronía/drift y diagnóstico de capacidades por operación.

| Función upstream | Existente en OPENMONTAGE | Propuesta |
|---|---|---|
| cut/join/export | video_trimmer, video_stitch, video_compose y render_verification | Conservar; homologar reporte de comandos/probe, no duplicar motores |
| caption/karaoke | subtitle_gen, scene_subtitles, CaptionWord y ASR preparado | Reutilizar español/timestamps y fuentes locales; no otro downloader ASR |
| crop/silence | auto_reframe y silence_cutter, ambos experimentales | Comparar contratos y límites; centro de imagen no equivale a seguimiento de rostro |
| loudness/audio | audio_mixer ya admite loudnorm_target y normalización | Separar medición LUFS/true peak de mezcla; evitar anunciar como nuevo lo existente |
| sync/multicam/drift | Herramientas de audio/vídeo no acreditan por sí solas correlación de relojes | Candidato acotado: offset/confianza/ppm y motivo de omisión; no prueba lip-sync visual |
| color/HDR/check | FFmpeg/ffprobe y verificación técnica existentes | Inventario por filtro/build y metadatos; conversión no certifica calidad visual |

Evidencia local leída: `tools/video/auto_reframe.py`, `silence_cutter.py`,
`video_trimmer.py`, `video_stitch.py`, `tools/audio/audio_mixer.py`,
`tools/base_tool.py` y rutas `lib/render_verification.py`/subtítulos. La lectura
no certifica ejecución de todas esas funciones en este equipo.

## Fuente y requisitos fijados

[README](https://github.com/kajisho5/ffmpeg-skill/blob/bad487c5c4c1d3db52893b27d5ff1278da5274a8/README.md),
[package](https://github.com/kajisho5/ffmpeg-skill/blob/bad487c5c4c1d3db52893b27d5ff1278da5274a8/package.json),
[SKILL](https://github.com/kajisho5/ffmpeg-skill/blob/bad487c5c4c1d3db52893b27d5ff1278da5274a8/SKILL.md):
42 operaciones declaradas, 12 anunciadas por MCP normalmente; Python>=3.10,
FFmpeg/ffprobe>=6.1. Scripts base usan stdlib; instalador npm requiere Node>=16,
innecesario para adaptar contratos. Build, codecs, filtros, fuentes y ejecutables
deben inspeccionarse realmente antes de una futura operación; versión sola no basta.

[LICENSE](https://github.com/kajisho5/ffmpeg-skill/blob/bad487c5c4c1d3db52893b27d5ff1278da5274a8/LICENSE):
MIT del wrapper, conservar aviso si se copia. No licencia FFmpeg, codecs, modelos,
fuentes o material de demos. Revisar el build elegido y sus condiciones separadas;
no importar muestras generadas con Veo ni asumir que sus recursos son producción libre.

## Efectos, offline y cancelación

[runner](https://github.com/kajisho5/ffmpeg-skill/blob/bad487c5c4c1d3db52893b27d5ff1278da5274a8/scripts/_common/runner.py)
centraliza ejecución/probe y límites; listas argv evitan una shell para FFmpeg.
[MCP](https://github.com/kajisho5/ffmpeg-skill/blob/bad487c5c4c1d3db52893b27d5ff1278da5274a8/mcp/server.py)
atiende cancelación y termina árbol Windows de la llamada. Ocultar métodos de
tools/list NO los impide: todos siguen invocables por nombre. Una integración debe
aplicar allowlist efectiva, rutas confinadas y propiedad de procesos, sin matar
Studio ni ejecutables ajenos. El run_command local síncrono no demuestra ese ciclo.

[verify](https://github.com/kajisho5/ffmpeg-skill/blob/bad487c5c4c1d3db52893b27d5ff1278da5274a8/scripts/verify.py)
ignora dry-run y escribe salidas de pruebas; mediciones como sync aún pueden ejecutar
FFmpeg/ffprobe. No se ejecutó ninguna bandera dry-run como supuesto modo sin efectos.
Protección de inputs declarados y overwrite upstream debe contrastarse con alias,
symlinks y rutas Windows antes de confiarla a originales.

Base $0/offline con binarios/filtros/recursos presentes. ASR opcional puede descargar
pesos; no utilizarlo, reutilizar reconocimiento local preparado. La revisión HTML
no incluye español entre los cuatro idiomas anunciados: adaptar resultados al panel
actual, sin añadir otra página de revisión. No APIs, modelos ni instaladores usados.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P0 | Contrato común plan/medición/escritura | Cada método declara efectos; dry-run no promete ausencia de procesos; no overwrite ni salida igual a cualquier input/alias |
| P1 | Doctor por operación | Respuesta estructurada con executable/build/filtros/codecs/fuentes, ausente vs acceso denegado y comandos previstos; sin descargas |
| P1 | Offset y drift | Datos sintéticos con offset/ppm conocidos, silencio/ruido/cola corta y baja confianza; unidades y tolerancias explícitas; no medios reales |
| P1 | Jobs cancelables | Stop de Studio cierra proceso propio y descendientes, estado persistente cancelado, parciales identificados, reanudación sin repetir pasos completados |
| P2 | Metadatos y verificación | Esquema probe antes/después, hashes/procedencia y diferencias esperadas; fallo de decodificación no se informa como éxito; revisión perceptual separada |

Pendientes de adopción: validar build/filtros y alcance de operaciones, no instalar
otra suite. Las pruebas futuras requieren una fase ejecutable; aquí no hubo medios,
mediciones multimedia, imports upstream ni cambios de entornos/configuraciones.
