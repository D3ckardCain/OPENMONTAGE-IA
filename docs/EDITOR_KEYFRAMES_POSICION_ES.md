# #174 — keyframes de posición de capas: primera entrega P0

Se reutilizan las capas, el historial y el render FFmpeg del proyecto compartido. No se crea otra timeline. Esta entrega cubre únicamente X/Y de capas visuales: escala, giro, opacidad animada, curvas Bézier y fundido cruzado siguen pendientes. El movimiento lineal anterior permanece disponible; activar keyframes sustituye ese movimiento de la misma capa, y no permite activar ambos a la vez.

Selecciona una capa existente en el inspector y abre **Keyframes de posición de la capa**. Añade de 2 a 32 puntos con tiempo en la fuente, X/Y normalizados e interpolación hasta el siguiente punto: lineal, mantener o suave (smoothstep). Guarda o quita los keyframes. Dos curvas muestran X en azul e Y en naranja. Los puntos deben estar ordenados, dentro de la fuente y mantener la capa dentro del lienzo. Cambiar su tamaño vuelve a validar esos límites.

Prepara la vista previa para comprobar la composición. Se usa el mismo grafo de render al previsualizar y exportar; no se promete vista interactiva sin preparar. Los puntos usan segundos absolutos de la fuente: recortar o dividir una capa mediante ripple conserva su fase al mapear `fuente = entrada + (montaje − inicio) × velocidad`. Se mantiene el valor exterior a los extremos y no se extrapola fuera del lienzo.

## Agente y persistencia

Comando existente de edición, con revisión e idempotencia del puente habitual:

```json
{"operation":"layer_position_keyframes","revision":12,"id":"ID_CAPA","keyframes":{"clock":"source_seconds","points":[{"seconds":1,"x":0,"y":0,"interpolation":"smooth"},{"seconds":3,"x":0.5,"y":0.25,"interpolation":"linear"}]}}
```

`keyframes:null` elimina explícitamente la curva. Omitir el parámetro no elimina datos: devuelve error. Nunca se evalúan expresiones suministradas por el usuario. La operación es atómica y entra en deshacer/rehacer y guardar/reabrir. Ante HTTP10054, recupera revisión/estado antes de repetir una escritura.

## Evidencia y límites

Nueve pruebas nuevas focalizadas: historial y reapertura, grafo real, conservación del reloj en piezas ripple, datos inválidos sin mutación, incompatibilidad con movimiento previo, revalidación al redimensionar y comando del agente mediante API sobre el mismo documento con deshacer desde el usuario. Tras ampliar el caso de parámetro ausente se repitió únicamente esa prueba modificada. Los medios de esas pruebas de contrato están simulados; la evidencia de fotogramas se obtuvo por separado con FFmpeg real.

FFmpeg existente produjo ocho fotogramas sintéticos de 320×180: posiciones inicial, punto medio suave y tramo de mantener comprobados por píxeles. No se repitió el piloto ni se generó voz. La primera captura por pipe agotó el plazo; el ensayo acotado con `-nostdin` y archivo de salida terminó correctamente. No se atribuye aquella demora al editor sin más evidencia.

Navegador Chrome real con módulo/control nativos en escenario QA explícito: añadir/quitar puntos, editar X/Y, interpolación, guardar/quitar curvas y foco. El callback del backend se simuló en ese escenario; su contrato se comprobó por separado con las pruebas de edición. Se corrigió pérdida de foco al desactivar el botón tras quitar la curva. Esto **no acredita activación ni ciclo completo en el panel principal**. La capacidad permanece oculta si el backend activo no la anuncia; agrupar su activación con próximas entregas. Originales, configuraciones, `.venv` y ComfyUI intactos; PR #2 en borrador.
