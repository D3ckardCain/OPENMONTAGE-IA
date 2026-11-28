# Concat: evaluación #67

24-11-2026 UTC. `jub0t/Concat@281dabf2484dbe6a9654f1a103f21c5cc923a063`,
Cargo/README0.2.12 beta. Solo lectura; no instalar editor, ejecutar MCP o exportar.

## Decisión y contraste

Concat ofrece superficie MCP/JSON-RPC implementada, a diferencia del roadmap de
OpenCut#64. Es candidato para probar el contrato compartido E06/E10 de editores,
no razón para instalar todos OpenReel/OpenFilm/Concat. Studio ya tiene timeline
edit_decisions, composición, palabras/subtítulos y audio locales. Seleccionar un
piloto solo tras doctor/licencias y round-trip sintético; mantener director/ASR/TTS.
No atribuir al beta paridad comercial o estabilidad4K por README.

## Fuentes y contrato observado

[README](https://github.com/jub0t/Concat/blob/281dabf2484dbe6a9654f1a103f21c5cc923a063/README.md),
[MCP](https://github.com/jub0t/Concat/blob/281dabf2484dbe6a9654f1a103f21c5cc923a063/docs/MCP.md),
[tools.rs](https://github.com/jub0t/Concat/blob/281dabf2484dbe6a9654f1a103f21c5cc923a063/src/crates/concat-mcp/src/tools.rs)
y [rpc.rs](https://github.com/jub0t/Concat/blob/281dabf2484dbe6a9654f1a103f21c5cc923a063/src/crates/concat-api/src/rpc.rs):
stdio JSON-RPC2, initialize/discover, progreso y notifications/cancelled. Métodos
project/timeline/edit_apply/undo/redo y export_start/status/wait/cancel existen en
fuente; no solo nombre de función en marketing. Esto no prueba ejecución Windows.

--mcp auto elige window autenticado por automation.json o headless propio; fijar
modo explícito, nunca fallback de alcance oculto. Proyectos se bloquean por proceso;
live editing del proyecto visible sigue planificado. Ediciones en memoria hasta
project_save; close sin save puede descartar. Paths por defecto bajo home, roots
adicionales por variable: reducir a proyecto temporal. No copiar token a GitHub.
Seconds para timeline y fracción0–1 para keyframes/transforms requieren conversiones
explícitas a nuestros frames/unidades. Export_wait cancelado no se presume export
cancelado sin status/evidencia del backend; verificarlo con fixtures y luego proceso.

## Licencias y requisitos

[LICENSE](https://github.com/jub0t/Concat/blob/281dabf2484dbe6a9654f1a103f21c5cc923a063/LICENSE)
y [LICENSING](https://github.com/jub0t/Concat/blob/281dabf2484dbe6a9654f1a103f21c5cc923a063/LICENSING.md):
AGPL3-or-later; uso comercial no exige por sí mismo licencia comercial. Distribución,
derivados y red de versión modificada tienen obligaciones de fuente/avisos.
Licencia comercial alternativa no resuelve terceros, patentes de codecs o modelos.
Slint/GPL y RobustVideoMatting/GPL, fuentes y FFmpeg separado deben inventariarse;
README propone build development GPL compartido mientras LICENSING describe builds
distribuidos LGPL: distinguir artefactos, no inferir build uniforme. No copiar marca.

[Cargo](https://github.com/jub0t/Concat/blob/281dabf2484dbe6a9654f1a103f21c5cc923a063/src/Cargo.toml)
requiere Rust>=1.93; compilar necesita FFmpeg7+ development libraries, cmake/C++,
no solo ffmpeg.exe actual. ORT usa feature download-binaries. Windowsx64 anunciado,
ARM pausado; binario/firmas, hardware codecs y GPU efectiva no comprobados. No
seguir instrucciones de omitir SmartScreen como parte de esta evaluación.

## $0 y offline

App gratuita sin cuenta/nube obligatoria según README. Modelos de captions/voz/
cutout se descargan desde Settings antes de offline; no disparar descargas para
reemplazar ASR/TTS actuales. Cada modelo/referencia necesita derechos y loader
compatible, no basta catálogo local. Export/GPU/codecs/RAM/VRAM no medidos.
Local no asegura que instalación/updates y todo recurso estén sin egreso;
prueba futura con perfil cerrado y red bloqueada. No APIs pagadas ni contenido aquí.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Puente mínimo E01/E10 | Servidor falso de version/mode/timeline con auth y roots; modo incorrecto/ruta denegada/timeouts claros, allowlist de lectura, sin crear proyecto real |
| P1 | Round-trip E06 | IDs/tracks/media/tiempos/fps racional y fracciones se conservan; propiedades no soportadas reportadas, no silent drop |
| P1 | Reversible E05/E06 | edit batch/undo/save/close, lock y revisión obsoleta probados con mocks; originales y cambios de usuario no sobrescritos |
| P1 | Export lifecycle E05 | job_id/status/progreso/cancel/partial/receipt reconciliados; parar espera separado de cancel backend, no repetir export verificado |
| P2 | Piloto físico condicionado | Un solo editor elegido por cobertura medible, recursos/licencias cerrados y fase autorizada; medios sintéticos/ffprobe/revisión física separados |

Bloqueos: beta y build/licencias/recursos/hardware no validados. API fuente justifica
contrato piloto, no declaración de integración completa. Configuraciones intactas.
