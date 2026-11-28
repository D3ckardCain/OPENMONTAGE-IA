# Auto-Editor: evaluación #74

24-11-2026 UTC. `WyattBlue/auto-editor@3841cc93f6196be01eac268bacae16452ff5aeac`.
ae.nimble declara0.0.0 de build, no versión instalable estable. Revisión estática
Tag de release observado31.10.0, resuelto a `8ba98a1d358b3181ad320653804601ea3d455e45`; no confundir con0.0.0 del manifiesto ni afirmar prueba binaria.
del CLI Nim actual; no reutilizar requisitos de antiguas versiones Python.

## Decisión y existente

Conservar FFmpeg, `silence_cutter` (remove/speed_up/mark), video_trimmer/stitch y
edit_decisions con speed. Aporte específico: decisiones candidatas multiseñal/pista,
márgenes y export interoperable. Volumen/movimiento no equivalen a relevancia,
silencio prescindible ni interés semántico. Extender E03/E04/E05/E06; no instalar
otra UI ni motor para duplicar cortes. Pausas narrativas y palabras prevalecen sobre
un umbral mecánico sin aprobación editorial.

## Fuentes, versión y Windows

[README](https://github.com/WyattBlue/auto-editor/blob/3841cc93f6196be01eac268bacae16452ff5aeac/README.md),
[ae.nimble](https://github.com/WyattBlue/auto-editor/blob/3841cc93f6196be01eac268bacae16452ff5aeac/ae.nimble),
[instalación](https://github.com/WyattBlue/auto-editor/blob/3841cc93f6196be01eac268bacae16452ff5aeac/docs/src/installing.md):
Nim>=2.2.2/nimcrypto0.7.3; binarios Windows oficiales o build mediante WSL,
cmake/meson/ninja y makeffwin que descarga/compila dependencias. No son solo un
paquete Python o el ffmpeg.exe actual. Instalar/compilar no necesario para contratos.
Codecs habilitados/deshabilitados y CPU/GPU dependen del build, no del nombre CLI.

[edit.nim](https://github.com/WyattBlue/auto-editor/blob/3841cc93f6196be01eac268bacae16452ff5aeac/src/edit.nim)
parsea expresiones de señales; [JSON](https://github.com/WyattBlue/auto-editor/blob/3841cc93f6196be01eac268bacae16452ff5aeac/src/exports/json.nim)
tiene versiones1/2/3 y timebase. No tratar JSONv1 chunks con speed99999 como tiempo
real o contrato actual sin versión. [EDL](https://github.com/WyattBlue/auto-editor/blob/3841cc93f6196be01eac268bacae16452ff5aeac/src/exports/edl.nim)
limita vídeo/pistas y avisa más de4canales audio; promedia speed para M2: export
no es round-trip sin pérdidas de efectos/velocidades variables/subtítulos.

## Licencia, $0 y offline

[LICENSE Unlicense](https://github.com/WyattBlue/auto-editor/blob/3841cc93f6196be01eac268bacae16452ff5aeac/LICENSE)
del repositorio, no de todos los artefactos binarios. ae.nimble incluye componentes
FFmpeg/x264/x265/otros con términos propios; binario/codec exige inventario. App
gráfica y web tienen assets propietarios según README, no son CLI libre equivalente.
No cuenta ni nube obligatorias para CLI sobre archivos preparados, sin cargo de API.
Entrada URL puede disparar yt-dlp y fuentes remotas: excluirla del perfil offline.
No comando ejecutado, medios procesados, toolchain ni programas instalados.

## Tareas con aceptación

| Prioridad | Carencia / grupo | Aceptación |
|---|---|---|
| P1 | Cut candidates E03 | Método/config/pista/márgenes/fuente/hash y motivos; voz baja, ruido/música, silencio total y márgenes solapados en mocks; no aplicar corte automáticamente |
| P1 | Mapa fuente→salida E04 | Intervalos eliminados/acelerados y speed variable con fps racional; palabras/offsets/subtítulos correctos, huecos/solapes/conflicto explícitos |
| P1 | Export E06 | Versión JSON/EDL/Kdenlive/Shotcut específica; pérdida de pista/canal/efecto/speed reportada, rutas seguras y original intacto |
| P2 | Ejecución futura E05 | Job propio con progreso/cancel/recibo, no duplicar export; benchmark/QA perceptual posterior frente a silence_cutter, no aquí |

Bloqueos: build/licencias/compatibilidad y beneficio no medidos. Los datos/mocks
pueden extender herramientas actuales sin instalar CLI/GUI ni duplicar ASR.
