# Ducking codificado y efecto sin marcar — #174

Prueba nueva sobre copia de 4 s del proyecto QA portugués, 640×360 / 8 fps / H.264 y AAC estéreo 48 kHz. Se conservan cortes, mezclador y parámetros de ducking anteriores; se añade un impacto existente **sin marcar como música** durante la voz, y un subtítulo técnico QA 1–3 s. Sin inferencias, ASR ni nuevas voces.

No había un MP4 bypass de este montaje y ajustes exactos: los renders anteriores pertenecían a otros montajes y el ensayo anterior de ducking solo produjo audio del grafo. Fueron necesarias **dos exportaciones nuevas** (bypass y activo). Después se recuperaron sus resultados sin repetirlas.

Se decodificaron 192.000 muestras por canal de cada MP4. Se aislaron referencias de voz, música y SFX con el mismo grafo y se compararon los residuos de las mezclas. La referencia de música comprimida conserva la topología del grafo completo y silencia el SFX antes de restar la voz; no se usa una rama aislada que cambie el drenaje del sidechain. Los arrays se guardaron para reutilizarlos, sin nuevas decodificaciones tras aprobar las mediciones.

| Ventana | RMS de música activa / bypass |
|---|---:|
| Antes de la voz, 0,2–0,8 s | 1,000000 |
| Durante la voz, 1,3–2,7 s | 0,568882 |
| Subventana con voz más baja, 2,2–2,7 s | 0,903349 |
| Tras recuperación, 3,7–3,95 s | 0,999934 |

El ducking depende del nivel de la voz. Una primera aserción exigía una reducción mayor del 20 % también en la subventana más baja; allí la reducción observada fue del 9,7 %. Se conservan ambos resultados, usando para la comparación principal la misma ventana 1,3–2,7 s del ensayo de audio anterior. No se cambió el motor ni se volvió a renderizar para alcanzar un umbral artificial.

La proyección del efecto sin marcar en 1,5–2,04 s arrojó ganancia **0,998139 bypass**, **0,999613 activa**: relación **1,001477**. El nivel se conserva dentro de la variación de AAC; no es identidad bit a bit. Los fotogramas y sus PTS coinciden entre ambas versiones. El cue seleccionable se extrajo con texto y límites idénticos.

[Informe con rutas, hashes ya registrados y método](EDITOR_DUCKING_MP4_EVIDENCIA_20261126.json). Salida activa: `projects/qa174-duck-export-root/edit-3a89b7b9db09/assets/editor-renders/33c5165343f54c6e9272759c5e0c3a0b/montage.mp4`.

La escucha humana queda pendiente. No se sustituyó la página `projects/qa174-eq-ab-review/escucha-ab.html` ni se añadió otra escucha obligatoria. No se consultó/reinició4750, no se inspeccionaron descargas y no se repitieron las pruebas del mezclador ni CI. Wan VACE Low válido y PR#2 en borrador se conservan.
