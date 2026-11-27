# Alinear una capa estática al lienzo

Entrega P1 independiente de cuentas/estilos, reutiliza `layers`, coordenadas normalizadas y renderer. No crea otro lienzo ni timeline. Seleccionar capa → **Alinear capa estática al lienzo**: horizontal izquierda/centro/derecha/conservar, vertical arriba/centro/abajo/conservar y margen0–0,25. El comando guarda X/Y reales. Usuario y agente comparten `layer_align`, revisión e historial:

```json
{"operation":"layer_align","revision":12,"id":"ID_CAPA","horizontal":"center","vertical":"middle","margin":0.05}
```

Guía geométrica refleja la caja guardada y la proporción actual16:9/9:16/1:1/4:5/custom; **no representa el sujeto ni sustituye reproducción audiovisual**. Para ver otra composición preparar vista previa. No se permite alinear cajas que no caben en los márgenes, capas bloqueadas ni con movimiento/keyframes: se rechaza sin quitar su animación. La alineación no cambia intervalos, voz, fuentes, mapa continuo ni subtítulos. Un cambio de posición invalida la vista previa anterior; undo puede recuperar su identidad exacta.

11 casos nuevos focalizados pasan: posición/historial/reapertura/renderer, entradas inválidas atómicas, conservación del mapa continuo/bloqueo, rechazo de animación conservándola y proyección FFmpeg en4proporciones. No se repiten pruebas aprobadas de velocidad ni renders. Una aserción inicial del test suponía640×360 pese a que su fixture era1920×1080; corregida para usar dimensiones efectivas, sin alterar el renderer.

UI/API real aislada4790 en copia portuguesa ya usada: centrar capa0,25×0,25→X/Y0,375; guía320×180 sitúa caja120/67,5. Undo/redo, guardar/reabrir y mapa continuo conservado. La API marca el render anterior como no actual durante el cambio. Se deshizo finalmente y se comprobó EDL original exacto y render92frames de la rampa otra vez `current:true`, sin nuevo render ni reproducción repetida.

Alcance acreditado: comando, controles, guía/coordenadas, persistencia y grafo de overlay existente. **No se generó otro MP4 con la nueva posición** y no se presenta como revisión AV de esa composición. Evidencia `EDITOR_ALINEACION_CAPAS_EVIDENCIA_20261126.json`; activación4750 permanece pendiente de confirmación y agrupada. Kit de marca privado por cuenta sigue dependiendo de168.
