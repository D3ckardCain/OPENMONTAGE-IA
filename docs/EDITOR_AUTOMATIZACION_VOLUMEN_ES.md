# Puntos de volumen por pista — #174

Ampliación local de las dos pistas lógicas del mezclador existente: audio de Vídeo y todos los clips añadidos de Audio. La revisión no encontró automatización por puntos; ganancia, fades, EQ/compresor, ducking y medición existentes se conservan.

## Controles reales en la timeline

Bajo cada pista aparece **Volumen · puntos lineales**. Se abre explícitamente para no desplazar las demás pistas por defecto; su apertura se conserva por proyecto en la sesión. Usa la misma escala temporal/zoom del montaje, sin otra timeline.

- Doble clic en la curva añade un punto. Arrastrar mueve tiempo y factor; se guarda un único comando al soltar. Esc o cancelar puntero restaura el borrador sin escritura.
- Seleccionar un punto permite editar segundos y factor mediante campos numéricos; también añadir en cursor o quitar. Flechas izquierda/derecha desplazan un fotograma; arriba/abajo cambian factor0,05, con Mayús×10. Supr quita el punto.
- **Alternar bypass** conserva puntos. **Quitar automatización** los elimina de esa pista. Todas las operaciones usan revisión/historial y se comparten con el agente.
- Curva de **ganancia lineal**, no interpolación logarítmica en dB ni Bézier. Hasta32 puntos por pista, tiempos0–7200s, factor0–4. Antes del primero y después del último se mantiene su valor. Sin puntos equivale a factor1.

El factor multiplica el nivel del mezclador; silencio/solo continúan prevaleciendo. Audio se automatiza después del retardo de cada clip en el reloj absoluto del montaje. Vídeo se automatiza después de unir sus cortes. Ambas curvas quedan antes del ducking: cambiar el nivel de la voz también cambia su efecto sobre la música. Los mismos puntos alimentan preview y exportación mediante evaluación por muestra a48kHz, preservando el estéreo explícitamente.

**Semántica de edición:** son puntos globales de pista, no keyframes unidos a cada clip. Dividir, reordenar y ripple no los trasladan automáticamente; mantienen sus segundos absolutos. Al acortar un montaje se conservan puntos posteriores por si se amplía de nuevo. Esta entrega no acredita remapeo automático de automatización con ripple ni curvas Bézier. El bloqueo de un clip no bloquea un control global de pista que no modifica ese clip.

El dibujo muestra el factor configurado, no una forma de onda ni prueba de reproducción procesada en directo. Preparar el montaje para escuchar el cambio. La fuente original permanece intacta.

## Contrato del agente

Capability y operación `track_volume_points`, usando `studio_project_edit` con acción `command` y revisión actual:

```json
{"operation":"track_volume_points","revision":12,"track":"audio","points":[{"seconds":0,"gain":0.2},{"seconds":2,"gain":1},{"seconds":4,"gain":0.2}],"bypass":false}
```

La operación sustituye todos los puntos de esa pista. `points:[]` quita la curva; `bypass:true` la conserva sin procesar. El backend rechaza puntos desordenados, repetidos, demasiado cercanos (menos de una muestra), no finitos y fuera de límites. No acepta expresiones FFmpeg del usuario. Curvas neutras, en bypass o de pista silenciada no invalidan el render; el documento conserva sus ajustes. Ante respuesta incierta, recuperar estado/revisión antes de repetir.

## Validación nueva

**14 casos focalizados aprobados**: historial, bypass/identidad, guardar/reabrir, entradas inválidas sin mutación, reloj después de retardo y concat, orden antes de ducking, mismo audio en preview/export, semántica de split/reordenación/ripple, borrador silenciado y puente del agente/API. No se repitieron suites de mezclador, ducking, medición ni CI.

Una copia de4s reutilizó **el MP4 bypass compatible ya aprobado**, sin renderizarlo. Ambas pistas recibieron la curva0,2→1→0,2 en0/2/4s. Se obtuvo una única salida nueva válida H.264/AAC,640×360/8fps. La primera tentativa falló porque la negociación del layout después de `aeval` resultaba en «2 channels» no reconocido por AAC; se corrigió añadiendo `aformat` estéreo explícito después de la evaluación y una aserción focalizada. Se conserva el intento fallido; no se declara como render válido.

| Ventana | Factor medido | Factor esperado ponderado por el audio |
|---|---:|---:|
| Antes de subida,0,3–0,7s | 0,388515 | 0,388691 |
| Pico,1,8–2,2s | 0,961722 | 0,961663 |
| Tras bajada,3,3–3,7s | 0,441406 | 0,441053 |

Comparación del audio AAC decodificado contra bypass×curva por muestra: correlación **0,999983**, error RMS relativo **0,5802%**,192.000 muestras/canal. Los valores de ventana son ponderados por la señal, no el factor solo en su punto medio. Los32 fotogramas y sus PTS coinciden; cues seleccionables conservan texto/tiempos. Bypass de ambas pistas recupera la identidad del render antiguo. Deshacer y guardar/reabrir recuperan los puntos activos.

Panel/API reales en QA4776 sobre copia: campos, arrastre con un commit, teclado, Esc sin escritura, bypass, undo/redo y reapertura. Se distinguió selección visual del punto (no persistente) de puntos guardados y se redondeó el incremento de teclado para evitar ruido decimal. Verificación de distribución de solo lectura en1920×1080 y3440×1440; controles compactos sin desbordamiento de página. QA propio cerrado. [Evidencia](EDITOR_AUTOMATIZACION_VOLUMEN_EVIDENCIA_20261126.json).

Pendientes: activación conjunta en4750 después de confirmación manual y escucha humana. Se mantiene intacta la única página A/B existente. Ocho descargas sin inspeccionar hasta confirmación; Wan VACE Low válido preservado. Costo0, sin dependencias ni cambios en ComfyUI/.venv. PR#2 permanece en borrador.
