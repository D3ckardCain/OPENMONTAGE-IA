# Silencios: aplicación reversible compartida — #130

26-11-2026 UTC. Extiende el [contrato de propuestas](PROPUESTAS_SILENCIO_STUDIO_ES.md).
[Evidencia](SILENCIOS_130_APLICACION_RESULTADOS.json). No instala, analiza audio,
transcribe, infiere ni renderiza. Se conservan originales y configuraciones.

## Operación real

El comando `silence_apply` del editor recibe la propuesta original, su nueva
`proposal_sha256`, `selected_ids`, `reviewed=true` y la revisión actual.
Se envía por `/command` o `/agent-command`; el agente reutiliza
`studio_project_edit`3.3.1, `action=command`. No hay otro escritor del proyecto.

```json
{
  "operation": "silence_apply",
  "revision": 0,
  "proposal": {"set_id": "conjunto guardado", "analysis": "usar el objeto original completo"},
  "proposal_sha256": "copiar la huella exacta devuelta por silence-proposal",
  "selected_ids": ["copiar un ID del borrador revisado"],
  "reviewed": true
}
```

Ejemplo esquemático, no payload ejecutable: `proposal` debe contener los campos
completos del contrato original, incluidas las huellas de EDL/palabras y el
análisis explícito de fuente. No inventar huellas ni reenviar tras conflicto.

Se recalcula la propuesta sobre el EDL actual y se verifica su huella completa.
Selecciones ajenas/duplicadas/vacías, análisis alterado y revisiones obsoletas
fallan antes de guardar. Solo se aplican candidatos seleccionados y revisados.
La propuesta declara `apply_available=true`; el endpoint sigue siendo de lectura.
La capacidad anuncia `apply_command=silence_apply` en el backend nuevo.

Se reutilizan `split`, `ripple_delete`, su validación y el commit/undo existentes.
Divisiones descendentes mantienen el reloj por fotogramas; se verifica el total
antes/después. Audio, capas, títulos, subtítulos y marcadores usan el mismo mapa
de eliminación. Las divisiones artificiales no introducen fades nuevos en cada
fragmento. IDs de piezas nuevas son distintos; atributos/fuentes se conservan.

Un fallo de bloqueo, transición incompatible, capa menor de un fotograma o exceso
de límites cancela la transacción completa, incluidos los splits intermedios.
Se mantienen los límites existentes:200clips,4capas visuales y20títulos; dividir
una capa puede excederlos. No se amplían ni se borran piezas para forzar éxito.

## Palabras y audio independiente

Los candidatos conservan todas las palabras de la guía con su margen. Antes de
aplicar se comprueban también palabras guardadas de audio situado por separado:
fuente, recorte, velocidad y posición. Una palabra conocida afectada bloquea el
candidato, incluso si la guía queda a salvo. No hay override de ese bloqueo.

Audio sin palabras o con cobertura ASR parcial necesita revisión explícita de la
pista en `reviewed_audio_ids`. Esto registra una declaración manual, no prueba
acústica ni garantía sobre voz desconocida. La ausencia de palabras no implica
silencio. No se ejecuta ASR para superar el bloqueo. Las revisiones quedan en
`silence_origin`, junto a hashes, selección, intervalos y evidencia sintética o
declarada; es una instantánea histórica, no alineación viva tras futuras ediciones.

Marcadores dentro del intervalo eliminado desaparecen con él; los situados en
su fin exclusivo sobreviven y se desplazan. Deshacer restaura también esos
marcadores. Títulos/cues que atraviesan cortes conservan la política existente
de fragmentación; esta entrega no inventa alineación interna de su texto.

## Fallo encontrado y corregido

La acumulación float de duraciones de clips divididos produjo un extremo
`2.4000000000000004` y eliminó un marcador colocado exactamente en2.4s.
El ripple ahora acumula enteros de fotograma y divide por FPS al construir cada
intervalo. La regresión nueva comprueba que el marcador del fin exclusivo se
conserva. No se ejecutó una suite histórica para repetir resultados aprobados.

## Validación en copia

21casos nuevos por subconjuntos: todas las pistas, historial/reapertura, locks,
rollback por límite de capas, selección parcial, bases obsoletas, velocidades a
24/30/60fps, palabras de audio independiente, revisión de audio desconocido y
API/agente aislados. Solo se repitió el caso fallido durante la corrección.
Se adaptaron dos expectativas antiguas de `apply_available`, sin reejecutarlas.

Copia persistente del montaje portugués ya existente, aislada bajo
`.runtime/qa/silence130-isolated/projects/edit-qa130-pt-silence`. Su medio existente
usa un enlace físico NTFS a la fuente: no hay otra copia de datos, ni lectura
para hash/procesamiento audiovisual. No escribir nunca sobre ese medio enlazado.
La validación solo escribe el artefacto del montaje en la copia aislada.

Se conservaron las116palabras guardadas y106ocurrencias completas del montaje.
Sobre una ventana **sintética** explícita0–25s se seleccionó el intervalo
10.28–10.64s,9fotogramas a25fps:22.72→22.36s. No se declara que ese intervalo sea
silencio medido ni se presenta un hueco ASR como evidencia acústica.

Se añadieron únicamente en la copia una pista de audio, capa, título y marcadores
para QA. Tras aplicar:2fragmentos de audio/capa/título,19textos de subtítulos
conservados y marcador del fin exclusivo preservado. Una sola revisión de edición;
undo exacto, redo exacto, guardar y nueva apertura HTTP leyeron el mismo resultado
persistente. El artefacto original mantuvo su SHA256 y el medio sus metadatos.

API mediante FastAPI/TestClient aislado; **no proceso residente4750 ni interacción
del panel**. Sin render, reproducción o escucha: sincronía validada como tiempos,
fuentes y persistencia del EDL, no calidad audiovisual. Revisión visual/waveform,
recibos acústicos reales y multiguía permanecen pendientes en #130.

Activación agrupada con #132, sin reiniciar ahora. PR#2 borrador y costo$0.
