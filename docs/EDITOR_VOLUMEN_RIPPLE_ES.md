# Ripple con puntos de volumen opcional — #174

Continuación de `8b9f06d`. La automatización permanece en **tiempos absolutos por defecto**. En las herramientas de la timeline aparece una casilla desmarcada **Ripple: mover puntos de volumen**, disponible solo con la nueva capability `ripple_volume_points`. Se restablece desmarcada al reabrir/cambiar proyecto; no modifica configuraciones del usuario.

Con la casilla activada, **Borrar con cierre global** remapea las curvas de Vídeo y Audio en la misma transacción que corta y desplaza el material. También se remapean curvas en bypass para conservar su intención al reactivarlas. La casilla se transmite a la aplicación revisada de silencios, que reutiliza el mismo comando ripple interno; no se repite ASR ni se cambia su protección de palabras. Esta ampliación no cambia reordenación, división, borrado con hueco ni eliminación aislada de Audio: no son un cierre global de tiempo. Una petición explícita de mover puntos en esas eliminaciones no compatibles se rechaza.

## Política de límites y bordes

Para un tramo eliminado **[a,b)**:

1. Se quitan los puntos originales desde `a` inclusive hasta antes de `b`. Un punto en `b` pertenece al material superviviente derecho.
2. Los puntos posteriores se desplazan la duración total eliminada antes de ellos. Los anteriores conservan tiempo. Los puntos más allá del final visible también se desplazan.
3. En el empalme manda el valor de la curva original en `b`, interpolado si no había punto. Se crea/reemplaza el ancla del borde derecho en el nuevo tiempo.
4. Si hay material antes del empalme, se crea un ancla **una muestra antes**, con el valor original una muestra antes de `a`. Así se conserva la curva del material izquierdo y derecho, con una transición de como máximo **1/48000s** entre niveles distintos. En un corte desde0 no existe lado izquierdo y no se inventa tiempo negativo.
5. Un ancla sustituye puntos a menos de una muestra. En colisiones submuestra manda el borde más a la derecha. Tramos adyacentes se fusionan antes del remapeo. Aunque desaparezcan todos los puntos originales dentro del tramo, las anclas conservan el nivel de los segmentos supervivientes; no se restablece silenciosamente a factor1.
6. Si el resultado superase32 puntos por pista, se rechaza **toda la edición** con explicación. No se decima la curva ni se pierden clips/puntos. Los bloqueos existentes también conservan su rechazo atómico.

Esto es una política explícita de curva lineal, no un nuevo fade de varios fotogramas, una garantía de ausencia de clic perceptible ni un remapeo de curvas Bézier.

## Contrato compartido con el agente

Misma operación de Studio y `studio_project_edit`, revisión actual, selección de cortes de vídeo:

```json
{"operation":"ripple_delete","revision":12,"track":"video","ids":["ID_CLIP"],"move_volume_points":true}
```

Omitir la propiedad o enviar `false` conserva exactamente los tiempos absolutos. Solo se admiten booleanos. Comprobar primero capability `ripple_volume_points`; no confiar en un backend antiguo que ignore el parámetro. `silence_apply` admite el mismo booleano y lo transmite al ripple interno; su procedencia registra la elección. No se añade otro escritor ni otro proyecto para el agente. Bypass, puntos, medios y curvas remapeadas forman parte del mismo historial; respuesta incierta exige recuperar estado antes de repetir.

## Evidencia sin repetir render

**9 casos nuevos focalizados** aprobados: valor por defecto, movimiento explícito de ambas curvas incluida bypass, semántica [a,b) y valores de borde, transición de una muestra, múltiples tramos/adyacentes, parámetros/tipo de eliminación inválidos, límite32 con rollback, bloqueos, undo/redo/reapertura y puente del agente/API. El noveno caso verifica el nuevo parámetro de `silence_apply` con propuesta/ASR simulados y observación de la llamada interna; no acredita otra validación completa del flujo de silencios.

Panel/API reales en servidor aislado4777, **copia** de los medios y la curva ya aprobados. Con casilla desmarcada, borrar0–1s dejó puntos absolutos sin cambios; deshacer restauró el montaje. Con casilla activada, el material fuente1–4s pasó a montaje0–3s y la bajada2–4s pasó a1–3s. Ambas pistas recibieron los puntos `[0,0.6]`, `[1,1]`, `[3,0.2]` (s/factor). Se compararon siete instantes supervivientes: niveles idénticos dentro de1e−12 al evaluar el mismo tiempo fuente. Undo/redo, recarga y reapertura conservaron la curva; casilla volvió al valor seguro desmarcado. Cero erroresJS. Servidor propio cerrado.

[Informe estructurado](EDITOR_VOLUMEN_RIPPLE_EVIDENCIA_20261126.json). No hubo render, decodificación de audio, inferencia ni nueva escucha. La exportación anterior sigue siendo evidencia del motor de puntos; el presente seguimiento acredita remapeo, persistencia e interacción, no una reproducción audiovisual nueva del montaje recortado.

Pendientes: activación conjunta4750 tras confirmación del reinicio y valoración humana. La escucha A/B anterior sigue intacta. Las ocho descargas no se consultaron; Wan VACE Low válido se conserva. No se tocaron .venv, ComfyUI ni configuraciones. PR#2 en borrador, sin fusión.
