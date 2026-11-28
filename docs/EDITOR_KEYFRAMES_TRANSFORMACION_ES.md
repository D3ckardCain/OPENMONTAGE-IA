# #174 — escala, rotación, opacidad y curvas Bézier

Esta entrega completa esos canales para las **capas visuales existentes**, además de su posición. No acredita todavía keyframes de clips principales, títulos ni todo el backlog #174. Se conservan la EDL compartida, su revisión, agente, historial y reloj absoluto de fuente. La entrega anterior de posición sigue siendo compatible.

En el inspector, selecciona una capa. **Keyframes: escala, rotación y opacidad** permite elegir el canal, editar2–32 puntos y guardar/quitar una curva. Escala uniforme0,05–4× respecto a la anchura/altura base, rotación−3600° a3600° alrededor del centro y opacidad0–1. La opacidad animada sustituye su control estático, que queda deshabilitado. El tamaño base sigue editable. Lo que sale del lienzo se recorta: revisar antes de exportar.

Cada intervalo admite lineal, mantener, suave (smoothstep) o Bézier cúbica. Sus cuatro controles `[x1,y1,x2,y2]` están en0–1, sin sobreimpulso. Se editan numéricamente o arrastrando los dos tiradores del pequeño diagrama. La posición también admite Bézier. El gráfico de valor muestra la interpolación real; no es una etiqueta decorativa. Cambiar de canal conserva el borrador sin enviar una escritura; guardar lo incorpora al proyecto compartido.

## Agente

La capacidad nueva es `layer_transform_keyframes`. El comando revisionado habitual acepta:

```json
{"operation":"layer_transform_keyframes","revision":17,"id":"ID_CAPA","keyframes":{"clock":"source_seconds","curves":{"scale":[{"seconds":0,"value":0.5,"interpolation":"linear"},{"seconds":4,"value":1.5,"interpolation":"linear"}],"rotation":[{"seconds":0,"value":0,"interpolation":"smooth"},{"seconds":4,"value":90,"interpolation":"linear"}],"opacity":[{"seconds":0,"value":0,"interpolation":"bezier","control_points":[0.42,0.15,0.58,0.85]},{"seconds":4,"value":1,"interpolation":"linear"}]}}}
```

`curves` sustituye el conjunto de esos tres canales: leer y conservar los demás al actualizar uno. `keyframes:null` quita explícitamente todos esos canales. Las curvas X/Y siguen en `layer_position_keyframes`; Bézier añade `control_points` a cada punto de posición. Sin conversiones de reloj al dividir/recortar/ripple: `fuente = entrada + (tiempo de montaje − inicio) × velocidad`. No se admiten expresiones de usuario, valores no finitos ni canales desconocidos. Ante HTTP10054, recuperar estado/revisión antes de repetir.

## Motor y límites

El mismo muestreador por fotograma genera órdenes locales de escala, giro, opacidad y posición tanto para previsualización como para exportación. Usa [filtros y comandos oficiales de FFmpeg](https://ffmpeg.org/ffmpeg-filters.html), con archivos derivados dentro del directorio propio de cada render; sin paquetes ni servicios nuevos. Se comprueba cancelación durante su escritura. Los tiempos se anticipan0,1µs para evitar retrasar una orden al fotograma siguiente por redondeo decimal.

El escalado variable se centra primero en un lienzo intermedio transparente de tamaño fijo, antes del giro. La primera prueba detectó un recorte interno al girar tamaños variables; este lienzo lo corrigió. Se rechaza atómicamente un conjunto de lienzos animados superior a32MP, antes de renderizar: reducir escala/tamaño/salida. Es un límite de trabajo local, no una promesa de memoria para cualquier equipo. La escala se rasteriza a dimensiones pares: hay redondeos que pueden acumularse al ampliar y diferencias de remuestreo entre resoluciones, sin cambiar reloj o curvas. La comparación audiovisual acredita la muestra indicada, no identidad universal de píxeles.

## Evidencia nueva, sin repetir aprobaciones

-14 pruebas focalizadas nuevas aprobadas: los tres canales, Bézier y extremos, entradas inválidas sin mutación, persistencia, deshacer/rehacer/reapertura, fase tras ripple, tiempo fraccional, presupuesto y cancelación antes de generar comandos. No se repitieron las9 pruebas anteriores ni CI.
-24 fotogramas sintéticos nuevos verificaron escala/giro final, alpha0, colores de alpha intermedio y ausencia de píxeles de borde negro en los instantes muestreados. No se repitió el piloto.
-Panel y API reales en QA4766, configuración/proyectos aislados: editar los tres canales, arrastrar Bézier, guardar/reabrir, deshacer/rehacer y conservar borrador al cambiar de canal, sin alterar el servidor4750.
-Dos renders **nuevos necesarios para estas curvas**, de4s, reutilizaron la copia del vídeo propio existente: preview960×540 y export1280×720,32fotogramas cada uno. SSIM medio0,997245875 y mínimo0,984785, por encima de umbrales previos0,98/0,97 al comparar a la misma resolución. Las órdenes de giro/opacidad coinciden; audio PCM decodificado idéntico y textos/tiempos de subtítulos idénticos. No se afirma identidad de píxeles entre resoluciones diferentes.
-Chrome reprodujo ambos archivos con fotogramas decodificados, sin errores. Se inspeccionaron la captura del panel y un fotograma exportado con la capa girada. Escucha humana pendiente; no se hicieron ASR ni síntesis.

Evidencia estructurada: `EDITOR174_TRANSFORMACIONES_EVIDENCIA_20261126.json`. QA4766 quedó cerrado. La única activación del paquete completo en4750 sigue agrupada; el rechazo de política anterior no se elude. Ver `ACTIVACION_EDITOR174_MANUAL_ES.md` para el procedimiento manual actualizado.
