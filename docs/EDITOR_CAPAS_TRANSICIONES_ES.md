# Capas visuales y transición manual por negro (#92)

Actualización #174: [fundido cruzado real con margen de fuente](EDITOR_FUNDIDO_CRUZADO_ES.md) y [keyframes de capas](EDITOR_KEYFRAMES_TRANSFORMACION_ES.md) ya están implementados y validados en QA aislado, pendientes de activación principal agrupada. Los límites indicados abajo sobre su ausencia corresponden a la entrega histórica del paso por negro.

Entrega sobre el mismo EDL, revisión y undo/redo de Studio/agente. Los controles
están condicionados por las capacidades del servidor actualizado. No se activan
por cambiar solo el catálogo ni se simulan con CSS.

Selecciona el segundo clip o uno posterior y abre **Transición por negro**.
La duración por lado se ajusta al fotograma de salida: oscurece y atenúa el
final anterior y recupera imagen/audio al inicio seleccionado. Quitar es otra
operación reversible. No solapa clips, no acorta el montaje ni mueve cues/audio.
Fundido cruzado y otras transiciones siguen no disponibles. Se rechazan duraciones
que se solapen dentro de un mismo clip y cambios sobre límites bloqueados.
Si reordenar/borrar dejaría una transición en el primer clip, se rechaza: quitarla
antes. No se elimina una decisión silenciosamente. Al dividir, el segundo segmento
no hereda la transición de entrada del original.

**Capas de vídeo** permite elegir una fuente registrada, entrada/salida, inicio,
velocidad, rectángulo normalizado X/Y/anchura/altura y opacidad. Hasta4 capas.
Guardar, actualizar, quitar y subir/bajar orden son transacciones reales.
La última capa es superior; títulos/subtítulos quemados quedan sobre las capas.
Pistas adicionales permiten seleccionarlas. Las capas deben caber en el lienzo
y en el tiempo del montaje. El borrado con cierre global de vídeo ajusta sus
intervalos y los de títulos/audio/cues/marcadores conjuntamente, con recorte o
división de fuente cuando corresponde. Otros recortes/reordenaciones que las
dejarían fuera se rechazan con error claro; ajustar sus tiempos primero, incluso
mediante un batch atómico. Véase `CORRECCION_RIPPLE_CAPAS_ES.md`.

Se componen con FFmpeg overlay, con PTS de inicio, intervalo habilitado y
`eof_action=pass:repeatlast=0`. La imagen no permanece después del intervalo.
El rectángulo encaja con bandas y conserva proporción. **Solo imagen**: el audio
de esa fuente se añade explícitamente en la pista de audio para evitar duplicarlo.
No incluye keyframes, máscaras, chroma, movimiento de capas por arrastre ni
transiciones cruzadas. No se anuncian esas funciones como completadas.

El agente usa `transition` (`id`, `type:dip_black|none`, `duration_seconds`) y
`layer_add/update/remove/move` con los mismos campos. `layer_move.index` es base0.
Los hashes AV incluyen capas/transiciones y la procedencia de todas sus fuentes;
el renderer verifica sus hashes antes/después. Los inputs de subtítulos blandos
se mapean después de las nuevas fuentes de capa.

## Validación

`EVIDENCIA_CAPAS_TRANSICIONES_20261124.json`: dos MP4 reales de4s, H264/AAC,
640×360/24FPS, con medios existentes en laboratorio aislado. Ambos decodifican
íntegramente. El fotograma exacto del corte por negro tiene media RGB0.
En el segundo MP4, la región superpuesta corresponde a otra ventana de fuente
(MAE≈1.99/255), difiere de la base≈82.74; fuera del rectángulo MAE≈0.77 y después
del intervalo≈0.58, compatibles con compresión. Se inspeccionó el fotograma.
No equivale a escucha, interacción del panel Windows ni activación del backend4750.

Validador opt-in del laboratorio existente: `python -B -m
scripts.validate_studio_timeline_model --source-project ID --workspace RUTA
--recheck --composition`. Pruebas unitarias: límites, locks, rollback, undo,
orden, identidad, grafo y mapa de subtítulos. Navegador CI: formularios reales
con transporte interceptado/modelo puro real, sin afirmar reproducción de medios.
#92 y PR#2 siguen abiertos; PR en borrador. Servidor activo no reiniciado.
