# Música bajo la voz en el editor — #174

Entrega local y reversible sobre el mismo proyecto editable por usuario y agente. Se revisó `tools/audio/audio_mixer.py`: ya existe ducking para operaciones de mezcla, pero no había comando, estado ni controles equivalentes en la timeline manual. Esta integración reutiliza su patrón FFmpeg `asplit` + `sidechaincompress`, sin invocar otro motor, instalar dependencias ni modificar el mezclador de producción existente.

## Uso y alcance

En Audio → **Música bajo la voz · ducking**, marcar los clips añadidos que sean música. El audio de los cortes de vídeo es la señal de referencia, después de ganancia/fades, EQ/compresor y mezclador. Los clips añadidos sin marcar, incluidos los SFX, pasan a la mezcla sin ducking. Guardar registra todas las marcas y parámetros en un único comando con revisión e historial.

- Umbral −50…−6 dBFS, ratio 1…20, ataque 2…200 ms y recuperación 20…2000 ms. El efecto depende del nivel de la referencia; no promete una reducción fija en dB.
- **Bypass** conserva parámetros y marcas y recupera exactamente el grafo original. **Quitar ducking** elimina parámetros y marcas, aun con un borrador numérico inválido. Ratio 1 o desactivado tampoco procesa.
- Preparar la vista previa del montaje para escuchar los cambios; el reproductor de fuente conserva el audio original. No hay mezcla DSP en directo.
- El detector recibe todo el audio del vídeo: no identifica idiomas, hablantes ni separa voz de música/ruido ya mezclados. La narración añadida en la pista Audio aún no puede elegirse como señal de referencia. No se anuncia ese control como disponible.
- Un solo de la pista Audio o silenciar el vídeo también silencia la referencia: en ese caso no hay voz que active el ducking. No se usa una voz oculta que siga atenuando música cuando está silenciada.
- Se comprime la suma de la música marcada, con makeup 1 y sin atenuación constante de compensación. Al caer la señal por debajo del umbral, la música recupera su nivel según release. La normalización/limitador finales siguen actuando sobre la mezcla completa.

Las marcas viven en cada clip, no en una lista de IDs susceptible de quedar obsoleta: dividir/duplicar/ripple conserva la función en los fragmentos; borrar la música no deja una referencia colgante. Cambiar la marca de un clip bloqueado se rechaza. Ajustar parámetros globales conservando sus marcas no modifica el clip bloqueado.

## Contrato compartido

Capability `audio_ducking`, a través de la acción `command` de `studio_project_edit`:

```json
{"operation":"audio_ducking","revision":12,"music_ids":["ID_CLIP_AUDIO"],"settings":{"enabled":true,"bypass":false,"threshold_db":-30,"ratio":6,"attack_ms":20,"release_ms":250}}
```

La selección sustituye todas las marcas de música. `settings:null` quita la cadena; no inventar IDs ni usar IDs de cortes de vídeo. Bypass guarda el mismo objeto con `bypass:true`. La identidad de render incluye únicamente ajustes/roles efectivos y el contrato `video-key-music-sidechain-v1`; el estado de edición conserva parámetros inactivos. Tras una respuesta HTTP incierta, recuperar estado y revisión antes de repetir la escritura.

## Evidencia

14 casos nuevos focalizados acreditan historial, persistencia, bypass/identidad, errores atómicos, bloqueo, borrado/división de música, grafo compartido y puente del agente/API. Se corrigieron dos supuestos de las fixtures: `add` elige pista por tipo de fuente y la preview reduce tamaño de vídeo; no eran fallos del motor. Después solo se repitieron los dos casos modificados, sin suites anteriores ni CI.

Prueba real FFmpeg del grafo completo, 4 s / 192.000 muestras por canal: voz del vídeo portugués existente, habilitada entre 1 y 3 s, sobre una cama extraída del vídeo QA propio ya disponible. Sin ASR, síntesis de voz, descarga ni nuevo render de vídeo. RMS de la cama respecto al bypass: **1,000 antes**, **0,569 durante**, **1,000 después** de la recuperación. Bypass restauró PCM idéntico muestra a muestra e identidad del render original. Deshacer/rehacer y guardar/reabrir conservan el estado. No se generaliza esta medición a todos los géneros ni se declara escucha humana.

Panel/API reales en copia aislada 4773: guardar, selección de música, bypass persistido, deshacer/rehacer, recarga, quitar con borrador inválido y rechazar selección vacía sin mutación. Cero errores de página. El servidor propio se cerró; Studio4750 intacto.

[Evidencia técnica](EDITOR_DUCKING_EVIDENCIA_20261126.json). Pendientes: activación y controles en4750 tras confirmación del reinicio; escucha humana y prueba audiovisual codificada específica de ducking. La única escucha humana solicitada sigue siendo la página A/B existente de EQ, sin añadir otra.

Referencia técnica: [documentación oficial de sidechaincompress de FFmpeg](https://ffmpeg.org/ffmpeg-filters.html#sidechaincompress). Sin servicios de pago ni dependencias nuevas. PR#2 permanece en borrador.

Actualizacion posterior: [validacion codificada de ducking y SFX sin marcar completada](EDITOR_DUCKING_MP4_ES.md). [Medicion de mezcla final](EDITOR_MEDICION_MEZCLA_FINAL_ES.md) implementada por separado. Siguen pendientes activacion4750 y escucha humana.
