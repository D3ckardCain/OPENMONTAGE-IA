# Propuestas de silencio: contrato numérico compartido — #130

26-11-2026 UTC. Primera implementación P0 E03/E04 de la
[evaluación registrada](EVALUACION_FIRECUT_ES.md), vinculada a #3/#92.
No se instala FireCut, Auto-Editor ni otro motor. Código propio, costo$0.

## Qué funciona

`lib/studio_silence_proposal.py` convierte intervalos explícitos de silencio en
candidatos no seleccionados del montaje. Reutiliza `studio_word_clock.inspect`,
FPS/cortes/velocidades del EDL y las huellas de `studio_editor`. No lee medios,
invoca FFmpeg, transcribe, infiere, renderiza ni escribe el proyecto.

Acepta una fuente guía con palabras guardadas, cobertura procesada y tiempos
de fuente. Ordena/une intervalos solapados, aplica padding en ambos extremos,
resta todas las palabras con margen y redondea los límites hacia dentro a frames.
Conserva texto/negaciones y deja IDs por ocurrencia para clips repetidos o
reordenados. El mínimo de corte se comprueba en tiempo final, tras velocidad y
cuantización; un fragmento puede desaparecer a24fps y conservarse a60fps.

No deduce silencio de huecos del ASR. Intervalos acústicos y cobertura deben
declararse aparte. El método `synthetic_fixture` se etiqueta `synthetic_not_measured`.
`ffmpeg.silencedetect` se etiqueta `declared_not_independently_verified`: recibir
JSON no demuestra que se midió el medio ni equivale a VAD o ausencia de voz.

El análisis se vincula a source_id/SHA256 registrados. EDL, palabras y revisión
obsoletos devuelven conflicto; no se relee el archivo para recalcular huellas.
Cobertura acústica/ASR parcial, palabras cortadas/cero y otras fuentes sin guía
bloquean el conjunto. Multiguía se rechaza explícitamente, sin aplicar una
unión peligrosa ni asumir que una pista representa todas las voces.

## API y agente

POST `/api/studio/editor/{pid}/silence-proposal`, de solo lectura aunque usa
cuerpo JSON. Recibe `revision`, `set_id`, `input_edl_sha256`, `word_data_sha256`,
`analysis` y opcionales `padding_seconds`, `word_padding_seconds`, `min_cut_seconds`.
Las huellas/revisión se obtienen del proyecto y de `subtitle-words`, no se inventan.

Esquema del análisis:

```json
{
  "source_id": "ID registrado de la guía",
  "source_sha256": "SHA256 registrado de esa fuente",
  "clock": "source_seconds",
  "method": "synthetic_fixture",
  "threshold_db": -35,
  "min_silence_seconds": 0.3,
  "processed_ranges": [[0, 6]],
  "intervals": [[0.5, 2.5]]
}
```

Es una muestra numérica, no un análisis medido. Para reutilizar un recibo real
de `silence_cutter`/`mode=mark`, tomar los pares start/end de `silences` del
artefacto, no `speech_segments` ya acolchados. Aportar umbral/mínimo/cobertura y
vínculo a la fuente verificados de ese análisis. No ejecutar el cutter ahora ni
inventar esos datos si el recibo no los conserva. La validación de recibos
persistentes y su recuperación sin repetir análisis queda pendiente.

Agente: `studio_project_edit`3.3.0, `action="silence_proposal"`, con el mismo
cuerpo en `proposal`. Usa HTTP contra el único servidor propietario del proyecto,
sin otro escritor. La API anuncia `silence_proposal.read_only=true` y
`apply_available=false`; no se añade un comando de aplicación ficticio.

Respuesta: candidatos con intervalo fuente/montaje racional, frames, motivo,
`reviewed=false`/`selected=false`, parámetros, cobertura, hash del análisis y
procedencia. `ready_for_review` solo significa contrato apto para revisión.
**No significa listo para aplicar ni validación audiovisual.**

Límites:500intervalos/coberturas,2000candidatos, palabras/cortes según reloj
existente; hasta7200s, FPS entero1–60, velocidad existente0.25–4. NaN/Inf/bool,
rangos vacíos/invertidos/fuera de fuente y relojes ajenos se rechazan.

## Evidencia y siguientes fases

[Resultados numéricos](SILENCIOS_130_RESULTADOS.json):23casos nuevos aprobados
por subconjuntos, sin volver a ejecutar20casos ya aprobados tras el primer paso.
La expectativa inicial de cuatro cortes a24fps se corrigió a tres: el cuarto
duraba menos de100ms tras redondeo y su descarte era correcto.

API/agente se ejercitaron con FastAPI/TestClient aislado y proyecto temporal:
misma respuesta,400/409 claros, archivo/revisión/undo/cues intactos, sin medio
físico. Esto no valida el proceso residente4750, navegador, escucha ni ripple.
No se repiten suites anteriores, renders, ASR, síntesis ni CI. No instalaciones.

Pendientes del mismo #130: revisión/exclusión sobre waveform y escucha de
límites; análisis/recibos reales acotados; múltiples guías; aplicación global
con el ripple/batch existente, undo/redo/reopen y sincronía de todas las pistas,
capas/títulos/cues; muestra audiovisual española posterior. No copiar recursos
propietarios de FireCut. #130 permanece abierto.

Activación agrupada con #132; consultar
[plan conjunto](ACTIVACION_AGRUPADA_STUDIO_ES.md). No reiniciar ahora. ComfyUI,
configuraciones y originales intactos; PR#2 continúa en borrador.
