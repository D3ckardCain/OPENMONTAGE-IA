# Piloto Blender-Skills en Blender 5.3 — #117

Se ejecutó un piloto real, local y de costo $0 en el proyecto separado
`projects/qa117-blender-skills-53`. No se modificó ningún proyecto anterior.
Blender 4.5.15 sigue seleccionado por defecto. Studio no se reinició.

## Resultado comprobado

- Escena editable propia: cubo biselado animado, esfera metálica y suelo;
  tres materiales PBR procedurales, tres luces de área y cámara.
- Blender 5.3.0 / EEVEE, 16 muestras: 72 PNG, 640×360, 24 fps, tres segundos.
  FFmpeg empaquetó H.264/yuv420p, sin audio por diseño; no hubo inferencias.
- `renders/blender-skills-pilot.mp4`: 86319 bytes, SHA256
  `bd4d905105fc4c2c9cbb70e802a15b4ae359944a5350b3f76945f48c208d877f`.
- `assets/scene/pilot.blend`: SHA256
  `2bb1d95a01ac199dea027f66e214d9d794e90e05ea8f01c70b68b13e9229019a`;
  se reabrió sin guardarlo y conservó su huella tras render y QA.
- Decodificación completa sin errores; 72 fotogramas presentes, 57 distintos
  (hay pausas deliberadas). Rotación Z: 0 / 0.8 / 1.8 radianes.
- Revisión visual de cuatro fotogramas codificados y reproducción real hasta
  el final en Chrome. El reproductor descartó un fotograma; el archivo no lo perdió.
- Las tres mallas pasaron el QA de render de Blender-Skills fijado abajo:
  sin degenerados, normales invertidas, duplicados ni z-fighting detectados.
  Son 1150 triángulos. El borde abierto del suelo es deliberado.
- Doce casos nuevos focalizados pasaron (10 iniciales y dos guardas añadidas
  por separado); no se repitieron suites anteriores ni se afirma CI completa.

## Procedencia y límites

Guías y QA de [EL4CTEO/blender-skills](https://github.com/EL4CTEO/blender-skills/tree/1a1cc6c49312f9f370aae86f52b7b907f29c94f6),
revisión `1a1cc6c49312f9f370aae86f52b7b907f29c94f6`, licencia MIT.
Se leyeron core, scene-setup, pbr-materials, lighting-lookdev, animation,
rendering y asset-qa. Se ejecutaron únicamente `qa_check.py` y `_bpyx.py`
revisados, conservando licencia y comprobando sus Git blob SHA antes de importar.
No se instaló MCP ni una colección global de skills.

El render es una previsualización técnica: presenta ruido y se ve el borde
posterior del suelo. No es un bucle perfecto ni una entrega final artística.
La ausencia de UV es aceptable para estos materiales procedurales; no acredita
texturas UV, exportación de juegos o impresión. No se certifican las 28 skills,
Cycles, rendimiento GPU, geometría de Archimesh/Molecular Nodes ni otros flujos.
No hubo evaluación humana de imagen ni escucha (el piloto es silencioso).

Dos llamadas fallaron antes de ejecutar Blender/código externo: la resolución
inicial del marcador del proyecto se corrigió al contrato de checkpoints; una
copia de referencia tenía un LF adicional y se normalizó hasta igualar el blob
fijado. No se relajó la verificación ni se sustituyó la revisión.

## Uso reproducible por el agente

Leer `pipeline_defs/blender-skills-pilot.yaml` y
`skills/qa/blender-skills-pilot.md`; inicializar un **nuevo** proyecto y registrar
decisiones/autorización. Usar el transporte `scripts/run_pipeline_tool.py` con
`blender_skills_pilot` en la etapa permitida y un JSON de entrada dentro del
proyecto: `{"project_id":"<nuevo-id>","phase":"build"}`; después `render`,
`inspect` y, con referencias fijadas disponibles, `skills_qa`.
El transporte exige checkpoint en curso y el perfil aislado 5.3 explícito.
No acepta scripts arbitrarios ni reutiliza 4.5 como alternativa silenciosa.
Rechaza sobrescribir escenas, renderizados terminados o escenas modificadas.
Para repetir un piloto debe usarse otro proyecto; no ejecutar otra vez el actual.

Consultar los informes `artifacts/pilot-*.json`, `render_report.json` y
`final_review.json`; revisar el MP4 y los fotogramas antes de completar compose.
La aprobación completa de este piloto quedó registrada antes de generarlo;
no equivale a una aprobación visual humana posterior.

El selector/API y el descubrimiento de esta nueva herramienta en el proceso
residente quedan para una **única activación manual agrupada futura**.
No atribuir al panel activo la ejecución de estas llamadas: se hicieron desde
el agente mediante registro y pipeline. [Plan agrupado](ACTIVACION_AGRUPADA_STUDIO_ES.md).
Evidencia numérica: [JSON](BLENDER_117_PILOTO_20261126.json).
