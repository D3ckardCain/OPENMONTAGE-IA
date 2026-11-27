# Velocidad por puntos y sincronía

Primera entrega acotada P1 de #174: **curva escalonada hold**, no rampa suave, reversa, congelado ni optical flow. Reutiliza los cortes, atempo/FFmpeg, reloj de palabras e historial existentes. No instala motores ni genera medios durante la revisión.

Seleccionar clip de vídeo → **Velocidad por puntos · escalonada**.2–8 puntos: segundo de fuente y velocidad solicitada0,25–4. El primero coincide con entrada; los demás son crecientes y anteriores a salida. Añadir punto desde el cursor o ajustar campos. El gráfico dibuja los escalones reales solicitados. **Revisar mapa y sincronía** calcula una propuesta sin escribir; muestra fotogramas/velocidades efectivas y duraciones. Confirmar y aplicar realiza **una** operación reversible, compartida con el agente.

API POST `/{pid}/speed-plan` y agente `studio_project_edit`3.11 acción `speed_plan` con `ramp:{id,points,follow_volume}`. El POST solo calcula; no inicia render ni cambia proyecto. Para escribir, mismo comando usuario/agente:

```json
{"operation":"clip_speed_ramp","revision":12,"id":"ID_CLIP","points":[{"source_seconds":0,"speed":0.75},{"source_seconds":1.94,"speed":1.5}],"follow_volume":false,"reviewed":true,"input_edl_sha256":"HASH_PROPUESTA"}
```

Revisión y huella de EDL obligatorias; cambios intermedios invalidan la propuesta. No hay reenvíos automáticos tras error incierto: recuperar estado/recibo antes de repetir. Se preservan fuentes/procedencia y el ID del primer tramo; nuevos tramos reciben IDs únicos con contrato/controles/velocidad solicitada. No se sustituyen originales ni se crea una segunda timeline.

Al reabrir, la timeline muestra esos tramos y sus velocidades; se conserva y muestra la receta original en el panel. **Una nueva propuesta actúa solo sobre el tramo seleccionado**. Reeditar toda la curva aplicada como un grupo único todavía está pendiente; deshacer/rehacer restaura el conjunto de esta operación. No se presenta esta entrega inicial como editor continuo de rampas completo.

## Reloj y alcance

Cada tramo se cuantiza a fotogramas de salida. La velocidad efectiva cubre íntegramente su intervalo fuente dentro de esos fotogramas; puede diferir ligeramente de la solicitada. Mapa creciente por nodos de montaje antes/después, invertible por segmentos. Vídeo y audio nativo usan la misma velocidad efectiva. Audio adicional y capas se dividen cuando cruzan nodos, conservando intervalos fuente; su inicio y velocidad siguen el mismo mapa. Títulos, cues y marcadores se remapean, también los posteriores al clip cuando cambia duración. Se conserva el texto, no se vuelve a transcribir.

Volumen: puntos permanecen absolutos por defecto. La opción explícita los mueve con material e inserta nodos necesarios con ganancia interpolada para conservar la curva. Bypass y valores se conservan; máximo32 puntos por pista. Esto **no cambia** el contrato de ripple ya aprobado.

Protección de palabras usa ASR guardado: rechaza un cambio dentro de palabra completa y verifica que el conjunto de ocurrencias completas no disminuye después de cuantizar. No acredita alineación acústica nueva. Se conservan parciales ya existentes como exclusiones, no se reconstruyen. Presupuesto:8 conjuntos/10000palabras; inspección individual conserva sus límites existentes.

La prueba real detectó «quando»(1,82–1,94s) excluida por un error de representación flotante al calcular1,94/2,6. Se corrige **el cálculo nuevo** desde `Fraction` decimal y redondeo de velocidad hacia arriba al float representable necesario; el límite racional ya no queda epsilon fuera del tramo. No se altera `studio_word_clock` ni la transcripción; hay regresión específica.

Rechazos explícitos: crossfade en proyecto, clip bloqueado, fundidos/compresor que se reiniciarían en divisiones, capa procedural que requiere otro remapeo, recursos bloqueados desplazados, velocidades vinculadas fuera0,25–4, karaoke que quedaría incompatible, exceso de clips/duración/puntos. No se silencian esos fallos ni se quitan efectos para forzar éxito. Para curvas suaves hace falta un motor/mapa continuo de vídeo **y audio** validado; aumentar cortes sin resolverlo no acredita una rampa suave. Audio vinculado cambia tempo durante el tramo; no se promete mantener música a tempo original.

## Evidencia

10 casos nuevos focalizados: sincronía/historial/reapertura, revisión/huella/entradas inválidas atómicas, palabras, volumen absoluto/seguimiento, capas/bloqueo, API/agente y regresión decimal.36 pruebas anteriores reutilizadas, sin suite/CI.

Panel/API real aislado4787 en copia de la portuguesa: revisar/aplicar, undo/redo, guardar/reabrir. Recursos existentes: vídeo/116palabras guardadas, un WAV Piper propio ya sintetizado (no nueva síntesis), capa y título de QA, marcador. Cambio de velocidad en1,94s: nodos0/1,94/4 →0/2,6/3,96; velocidades efectivas0,7461538461538462 y1,5147058823529413. Un MP4 nuevo necesario, intento `cbeb680b8d1f47d29aba58e84e9cd5fc`:99fotogramas/25fps, vídeo y audio3,96s;190080muestras48kHz decodificadas con audio no nulo. Cues extraídos conservan texto y tiempos remapeados≤1ms.16ocurrencias de palabra completas conservadas;1parcial previa sigue excluida. Audio adicional/capa producen2piezas cada uno; título0,670103…–3,629902… y marcador2,969708…s. Fotograma inspeccionado con título/capa visibles. No se afirma escucha, lip-sync medido ni otra alineación ASR.

Evidencia `EDITOR_VELOCIDAD_ESCALONADA_EVIDENCIA_20261126.json`, recibos privados `.runtime/qa/speed174/`. Original intacto; Studio4750 sin consultar/reiniciar. Activación se agrupa tras confirmación; escucha A/B anterior intacta.
