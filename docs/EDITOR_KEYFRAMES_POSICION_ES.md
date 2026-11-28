# #174 — keyframes de posición de capas: primera entrega P0

Se reutilizan las capas, el historial y el render FFmpeg del proyecto compartido. No se crea otra timeline. Esta primera entrega cubrió X/Y; la continuación [EDITOR_KEYFRAMES_TRANSFORMACION_ES.md](EDITOR_KEYFRAMES_TRANSFORMACION_ES.md) incorpora escala, giro, opacidad y Bézier para capas. Fundido cruzado y otras partes de #174 siguen pendientes. El movimiento lineal anterior permanece disponible; activar keyframes de posición lo sustituye en esa capa y no permite activar ambos a la vez.

Selecciona una capa existente en el inspector y abre **Keyframes de posición de la capa**. Añade de 2 a 32 puntos con tiempo en la fuente, X/Y normalizados e interpolación hasta el siguiente punto: lineal, mantener o suave (smoothstep). Guarda o quita los keyframes. Dos curvas muestran X en azul e Y en naranja. Los puntos deben estar ordenados, dentro de la fuente y mantener la capa dentro del lienzo. Cambiar su tamaño vuelve a validar esos límites.

Con una curva activa se deshabilitan los X/Y estáticos y el movimiento lineal anterior, para que no parezcan controles de la posición animada. Al quitar la curva vuelven a habilitarse. El tamaño sigue editable y sujeto a validación. Esta exclusión se comprobó en un escenario de formulario nativo en navegador, sin escrituras API ni repetir el ciclo ya aprobado.

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

Después se validó también el panel completo contra API real en Studio QA4766, con raíz de proyectos y configuración aisladas: copia del vídeo propio de4s ya existente, aplicar curva, deshacer/rehacer, guardar/reabrir y cambio del agente visible en el panel con deshacer del usuario. Sin mocks de API o medios en esta fase. No se repitió render ni voz. El archivo original conservó tamaño y mtime. Se inspeccionó la captura1920×1080; timeline visible y desplazamiento interno del inspector. La prueba inicialmente trató una navegación a la misma URL como reapertura; se corrigió el arnés para recargar y se recuperó el estado persistido antes de continuar, sin repetir las escrituras terminadas. El servidor QA se detuvo al terminar, identificando exclusivamente su PID;4750 no se reinició. Activación principal y escucha/revisión audiovisual humana siguen pendientes.

La activación agrupada posterior en4750 se preparó sin trabajos activos y con224 JSON respaldados. La política rechazó el comando de reinicio (`blocked by policy`), que no se ejecutó. Salud sigueOK, PID153088 y224 JSON sin cambios; backend anterior conserva aviso de reinicio. Procedimiento manual y comprobación mínima: [ACTIVACION_EDITOR174_MANUAL_ES.md](ACTIVACION_EDITOR174_MANUAL_ES.md). No se intentó eludir el rechazo.
