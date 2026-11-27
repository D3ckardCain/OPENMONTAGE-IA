# Cola autorizada: contraste de código y evidencia — 26 noviembre 2026

Base `1b1fdbd`, rama `feat/local-agent-research-foundation`, PR2 en borrador. Esta lista registra alcance, no acredita paridad completa ni activación principal.

| Orden | Área | Contraste y siguiente acción |
|---|---|---|
| P0 editor/audio #174 | Capas: posición, escala, giro, opacidad y curvas lineal/hold/smooth/Bézier ya implementadas con gráfica y tiradores; docs EDITOR_KEYFRAMES_TRANSFORMACION_ES.md conserva validación previa. Fundido cruzado real: EDITOR_FUNDIDO_CRUZADO_ES.md. Normalización con objetivo LUFS configurable −40…−5 ya existe en audio_mix y panel. | Reutilizar aprobaciones. Clips principales/títulos no tienen todos esos keyframes; no declarar completo ese alcance. Los puntos de volumen y ripple opcional están validados y no se repiten. |
| P0 audio/efectos #174/#177 | Mezclador, EQ/compresor/bypass, ducking, medición final, automatización y catálogo109 tienen evidencia aislada. | Esperar confirmación de reinicio y validar en una sola sesión4750 sobre copia. Escucha A/B humana pendiente. No consultar4750 antes. Bibliotecas adicionales #177 conservan sus restricciones de licencia. |
| P0 subtítulos #107/#115/#129/#174 | Cues con edición/arrastre/split/merge; palabras en reloj de montaje y borrador con procedencia ya implementados. Muestra portuguesa aprobada; española pendiente. | Primera ampliación: límites de lectura y zona segura con propuesta explícita de saltos y salidas distintas. Después karaoke con tiempos guardados, sin ASR nuevo. |
| Dependencia cuentas #168 | No existe account_id en backend/editor/puente ni filtro de propietario en listas de proyectos. project_path/listados son globales por ID. | Estilos/kit/favoritos **por cuenta** requieren antes esa base y migración sin asignar históricos por conjetura. No etiquetar una biblioteca global como cuenta. Se documenta dependencia; no bloquea mejoras por proyecto. |
| GSAP #186/#132 | Runtime/perfil offline y piloto ya preparados; no repetirlos. | Fijar revisión de guías oficiales y ejemplo nuevo de título determinista/seek/export offline con dependencias locales. |
| P1 producción | Color/before-after, remapeo de velocidad, lienzo/marca, voces por segmentos y avatar/lipsync requieren auditar sus implementaciones actuales. | Entregas pequeñas tras P0/GSAP, memoria/licencia antes de pesos; no repetir síntesis ni muestras aprobadas. |
| P2 | Máscaras/chroma, estabilización/tracking, proxies, multicámara/micrófono. | Después de P1: controles funcionales y prueba reproducible; no botones de disponibilidad ficticia. |
| Descargas | Seis LongCat Single, Multi1 y Wan High todavía sin confirmación de finalización. | No inventario ni hashes hasta confirmación. Luego solo ocho nuevos, integrar y limpiar vacíos; conservar Wan Low. |

Ninguna de estas dependencias autoriza a sobrescribir configuraciones, mover originales, modificar .venv/ComfyUI ni fusionar PR2. Las condiciones de reinicio y descargas son independientes. Se continúa con tareas locales independientes sin pedir confirmaciones rutinarias.

Avance posterior: lectura/zona publicada5dfb85d; karaoke con palabras guardadas implementado en entrega posterior (manual EDITOR_SUBTITULOS_KARAOKE_ES.md). Dependencia de cuentas168 permanece. Siguiente bloque: GSAP186/132.
