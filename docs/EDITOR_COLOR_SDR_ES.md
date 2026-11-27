# Color por clip y comparación del mismo fotograma

Entrega acotada de #174, no paridad con Resolve/Lightroom. Seleccionar clip de vídeo → **Color del clip · SDR**. Exposición−2…2EV, contraste0,25…2, saturación0…2 y gamma0,5…2; guardar, quitar o bypass conservando ajustes. No se admiten huecos ni clips bloqueados. Los originales no se modifican.

Usuario y agente usan `clip_color` sobre la misma revisión e historial. Ejemplo de comando:

```json
{"operation":"clip_color","revision":12,"id":"ID_CLIP","color":{"exposure_ev":0.6,"contrast":1,"saturation":0.6,"gamma":1,"bypass":false}}
```

`color:null` quita el ajuste. Deshacer/rehacer y guardar/reabrir conservan el documento. Split/duplicado reutilizan el ajuste del material. Bypass y valores neutros no invalidan un render idéntico; los valores conservados siguen siendo editables. No se aplican color a audio ni capas en esta entrega.

Vista previa preparada y exportación reutilizan `studio_color.suffix`: `exposure` float RGB y `eq` en SDR, antes de montaje/capas/títulos. La ayuda del FFmpeg **ya instalado** confirmó `exposure`; no se añaden binarios. Conversión SDR y clipping posibles; no es RAW, gestión HDR ni balance de blancos calibrado. Curvas PCHIP disponibles en la entrega posterior descrita abajo; HSL, LUT con procedencia/licencia y scopes avanzados siguen pendientes.

**Comparar en el cursor** exige situarlo dentro del clip seleccionado. API GET `/{pid}/color-compare?clip_id=…&clip_seconds=…`, agente acción `color_compare`. Decodifica un fotograma y lo divide para ambos lados: izquierda sin color, derecha con ajustes guardados, incluso si el montaje está en bypass (se indica). Botón **Ampliar comparación** abre diálogo de1100px máximo, cierre con botón/Esc y foco. Usa el encuadre actual, sin audio/capas/títulos/transiciones. El tiempo informado es solicitado, no PTS medido. No representa el montaje final completo ni cambia el proyecto.

Una comparación simultánea como máximo, tamaño acotado a480×270 por lado, timeout20s, sin reintento automático. Si el proyecto cambia, se descarta la respuesta. Ante error incierto de escritura, recuperar estado antes de reenviar.

## Evidencia nueva

7 casos focalizados: contrato compartido, bypass/digest, historial/reapertura, entradas inválidas atómicas, bloqueo/split, filtro común y API/agente. Panel real aislado4781 sobre copia portuguesa existente: guardar0,6EV/saturación0,6, undo/redo/reabrir, comparación, ampliar/cerrar. Sin errores JS; principal4750 intacto.

Un único MP4 nuevo4s640×360, intento `beb6e6548b24488d89910596f34ed6e8`. Bypass previo `acb36238a1fb433581dc954ce8442c9c` reutilizado **tras comprobar igualdad de identidad del montaje/ajustes**. Duración4s, textos/tiempos de subtítulos exactos y payload AAC idéntico. A1s, diferencia RGB media del efecto17,934; diferencia media del fotograma exportado frente al lado procesado de comparación2,761/255 tras escala, no identidad de píxeles por compresión/escala. Fotograma e interfaz inspeccionados. No se repitieron render bypass, PCM, ASR, síntesis, CI ni escucha.

Recibos privados `.runtime/qa/color174/{ui.json,media.json,panel.png,comparison.png,export-frame.png,enlarged.png}`. Esta prueba acredita el nuevo ajuste en copia/servidor aislado, no activación4750 ni valoración humana de color/audio. Escucha A/B anterior se conserva sin cambios; activación agrupada espera confirmación de reinicio.

## Histograma RGB del mismo fotograma

La respuesta de comparación incluye `histogram`, disponible también para el agente.32 intervalos de8 niveles por canal RGB, recuentos exactos de píxeles y extremos0/255 para cada mitad. Imagen de visualización8bit, incluyendo letterbox; no se infieren clipping, luminosidad física, niveles broadcast, HDR, waveform ni vectorscope. Gráficos antes/después se autoescalan individualmente: comparar distribución, no altura absoluta entre gráficos; los recuentos de API conservan las cantidades exactas. No se mide toda la duración del clip.

2 pruebas nuevas del histograma pasan: bins/extremos y presupuesto de píxeles. Para verificar los gráficos se reutilizó `comparison.png`: backend calculó sus bins, y UI real4782 recibió esa respuesta mediante **intercepción GET explícita de QA**, no mediante una nueva decodificación/exportación.2 SVG/6 curvas RGB, una consulta, cero errores JS; captura inspeccionada. Esta comprobación de UI usa una respuesta controlada, no acredita una nueva ejecución audiovisual. No se repitieron los7 casos de color ni el MP4 aprobado.

## Curvas por puntos

Seleccionar clip → **Curvas de color · puntos PCHIP**. Canal maestro/R/G/B,2–8 puntos de entrada/salida0–1, extremos de entrada0/1 obligatorios y entradas crecientes. Clic añade punto; campos numéricos permiten modificarlo por teclado y quitar interiores. Guardar todas, restablecer canal o quitar curvas. La polilínea discontinua es **guía de puntos**, no un dibujo de la interpolación del motor; revisar la imagen procesada en Color → Comparar. PCHIP confirmado por ayuda del FFmpeg existente, sin nuevos paquetes. No se aceptan archivos de curva ni expresiones arbitrarias.

```json
{"operation":"clip_color_curves","revision":14,"id":"ID_CLIP","curves":{"interpolation":"pchip","channels":{"master":[[0,0],[0.524,0.7],[1,1]]}}}
```

Mismo comando para usuario/agente. `curves:null` quita; una curva identidad se omite del documento. Bypass de Color omite también curvas conservando puntos; no hay un segundo bypass independiente. Curvas se aplican después de ajustes básicos y antes de composición. Split copia puntos; historial/reapertura y bloqueo reutilizan el editor, sin mutar originales.

7 casos nuevos de curvas pasan, sin repetir los casos básicos/histograma: validación atómica, historial/reapertura/split, bypass, identidad, filtro común y agente. UI real4783 en la misma copia, nueva curva maestra0,524→0,7 guardada, undo/redo/reabierta. Un único MP4 nuevo necesario para esta curva,4s640×360, intento `15710a7792344339b3f4664ccce31b0d`; baseline de color previo `beb6e6548b24488d89910596f34ed6e8` reutilizado tras comparar identidad del montaje. AAC igual (`MD5=64e179d44f4ca79b5fc68e3345fdae45`, cacheado para futuras comparaciones), duración4s, cues y tiempos exactos. Diferencia RGB curva/sin curva9,501/255; exportación frente a comparación procesada3,130/255. Fotograma inspeccionado. No se atribuye escucha humana ni reproducción aprobada al navegador: el inspector/diálogo son reales y la comprobación AV es mediante FFmpeg. Evidencia `EDITOR_COLOR_CURVAS_EVIDENCIA_20261126.json`.
