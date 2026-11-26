# Borrador de subtítulos desde palabras guardadas — #129 / E04

Extiende #115 sin volver a transcribir. El montaje, los subtítulos y el historial
siguen siendo los mismos para Studio y el agente. No hay nuevo motor ni instalación.

## Uso después de la activación agrupada

En Candidatos, junto a un conjunto ASR guardado, «Preparar borrador de subtítulos
desde palabras guardadas» consulta el servidor sin escribir. Muestra tiempos,
texto, bloqueos y límites. Revisar texto/contexto/tiempos completos y marcar la
casilla de revisión antes de aplicar. Si ya existen subtítulos, confirmar su
reemplazo por separado. Deshacer recupera los anteriores; Rehacer y guardar/reabrir
usan el historial existente. El idioma del proyecto no cambia automáticamente.

El agente consulta `studio_project_edit` con `action: subtitle_draft`,
`project_id` y `set_id`. HTTP equivalente:
`GET /api/studio/editor/{pid}/subtitle-draft?set_id=...`.
La aplicación usa `action: command` y el comando compartido:

```json
{
  "operation": "subtitle_from_words",
  "revision": 12,
  "set_id": "id-del-conjunto",
  "input_edl_sha256": "huella-devuelta-por-el-borrador",
  "word_data_sha256": "huella-devuelta-por-el-borrador",
  "reviewed": true,
  "replace_existing": true
}
```

El servidor recalcula el candidato desde su propio EDL: no acepta una lista de
cues construida por el cliente como si fuera esta derivación. Exige revisión y
ambas huellas actuales. Una respuesta perdida no provoca reintentos automáticos;
consultar el proyecto y su historial antes de actuar de nuevo. Una revisión
repetida se rechaza con409. No hay escritor paralelo de archivos desde el agente.

## Contrato y límites

- Reutiliza `studio_word_clock`: cortes, repetición/reordenación, velocidad y
  duración cuantizada en fotogramas. No añade el offset de importación otra vez.
- Agrupación mecánica: hasta seis palabras,80 caracteres como objetivo,
  cuatro segundos y pausas de0.6s; separa clips, hablantes e idiomas declarados.
  Una palabra larga se conserva entera (límite del SRT400 caracteres).
  No omite negaciones ni decide si terminó una idea: requiere revisión semántica.
- Bloquea el borrador completo ante palabras parciales/cero, cobertura declarada
  incompleta, otros clips no cubiertos por el conjunto, solapes, texto no
  representable o intervalos que colapsan al redondear a milisegundos. Los huecos
  explícitos del EDL se permiten, sin inventar silencio ni subtítulos para ellos.
- Hasta2000 ocurrencias por borrador para acotar el recibo y el historial.
  La vista muestra hasta100cues; el JSON completo queda en API/agente.
- Conserva ocurrencias, índices, texto original, fuente/hash, transcripción/hash,
  racionales originales, idioma/hablante y calidad temporal **declarada**.
  No vuelve a leer/rehashear medios ni certifica alineación ASR.
- `subtitle_word_origin` guarda una fotografía de la derivación con
  `applied_cues_sha256` y `scope: snapshot_at_apply_not_live_alignment`.
  Ediciones posteriores pueden volverla histórica: comparar la huella de cues
  antes de atribuirles esa procedencia; no es alineación viva por palabra.

## Comprobado en esta entrega

15 casos pytest nuevos (14 iniciales y una guarda de límite posterior): Unicode,
negación, ocurrencias repetidas/velocidad, errores/bloqueos, bases obsoletas,
confirmación, GET sin escritura y aplicación por el agente a través de FastAPI
aislada con undo/redo/save/reopen. Sin medio real ni llamada ASR.

Seis escenarios de Chrome headless con DOM real y respuestas sintéticas:
revisión/aplicación, bloqueos, revisión obsoleta, error de envío, error de lectura
y cambio de proyecto. Cero errores de página, cero llamadas al Studio activo.
Prueba reproducible: `node tests/js/editor-word-subtitles.browser.cjs` con
Playwright/Chromium ya preparados (QA_CHROME opcional). No instala navegador.

No se repitieron suites aprobadas, el piloto Blender ni la muestra portuguesa.
[Evidencia y ejemplo estrictamente sintético](SUBTITULOS_DESDE_PALABRAS_129.json).
No se afirma CI completa, apariencia del panel4750, lectura audiovisual o
exportación de estos nuevos cues. Activación local pendiente en el mismo lote
que el selector Blender. #107 español, #112 sin recibo y acciones ocultas #113
conservan sus pendientes. Configuraciones/ComfyUI intactos,4.5 predeterminado,
costo$0, PR#2 borrador. Sin reinicios, descargas ni inferencias.
