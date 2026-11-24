# Contrato de timeline v2: operaciones atómicas

Esta entrega amplía el mismo EDL de usuario/agente. No hay otro proyecto interno
de agente. Cada comando exige revisión, guarda una vez y tiene un deshacer;
un batch fallido no publica resultados parciales. Orígenes e historial se conservan.

## Disponibilidad y activación

`GET /api/studio/editor/capabilities` anuncia los comandos realmente cargados.
La interfaz oculta acciones avanzadas si la instancia antigua no anuncia soporte;
no envía comandos nuevos a un backend que no los entiende. La herramienta nativa
`studio_project_edit` admite `action: capabilities` para la misma comprobación.

**El proceso activo 4750 no se ha reiniciado.** Código y pruebas v2 se preparan
por separado; publicar archivos Python no actualiza el proceso ya cargado. Su
activación local requiere una actualización controlada de ese servidor después
de comprobar trabajos activos. No se declara activa por CI ni por un render aislado.

## Operaciones compartidas

Ejemplos de objetos `command`; añade siempre la `revision` obtenida de `read`:

```json
{"operation":"duplicate","track":"video","ids":["clip-a","clip-b"]}
{"operation":"delete_keep_gap","track":"video","ids":["clip-a"]}
{"operation":"ripple_delete","track":"video","ids":["clip-a"]}
{"operation":"audio_trim_position","id":"audio-a","in_seconds":1,"out_seconds":4,"start_seconds":2}
{"operation":"flags","track":"audio","id":"audio-a","solo":true,"locked":false}
{"operation":"marker_add","seconds":2.5,"label":"Revisar corte"}
{"operation":"batch","operations":[{"operation":"trim","id":"clip-a","in_seconds":1,"out_seconds":3},{"operation":"clip","track":"audio","id":"audio-a","gain":0.25}]}
```

- **Duplicar** inserta las copias después de la selección, con IDs nuevos y la
  misma procedencia. En audio cada copia empieza al terminar su original.
- **Borrar con hueco** conserva tiempos mediante un clip real de negro/silencio,
  generado por el compositor, sin sustituirlo por un dibujo CSS.
- **Borrar con cierre global** elimina intervalos y ajusta audio/cues/marcadores.
  El audio que cruza un intervalo se divide en segmentos conservados y convierte
  sus tiempos a fuente incluyendo velocidad. Los cues recortan su intervalo;
  los marcadores dentro de lo eliminado desaparecen y los siguientes se desplazan.
  La transacción completa se rechaza si movería clips bloqueados.
- **Entrada de audio** guarda recorte y posición juntos, manteniendo el extremo
  derecho. El borde de la interfaz no deja dos operaciones a medio aplicar.
- **Mute/solo/bloqueo** son de clip, no grupos de pistas inexistentes. Solo aísla
  su audio y silencia los demás, incluido el audio base del vídeo; mute prevalece.
  Bloqueo impide recorte/movimiento/borrado y desplazamientos indirectos. Se puede
  desbloquear explícitamente; no equivale a un permiso de seguridad.
- **Marcadores** tienen ID, tiempo y etiqueta compartidos; pueden añadirse,
  editarse y quitarse de forma reversible. No se queman en el vídeo.
- **Batch** admite1–200 comandos de datos; no batch anidado ni operaciones de
  historial, importación o render dentro. Cada batch cuenta como una operación.

Interfaz disponible con backend compatible: Ctrl/clic amplía selección del mismo
tipo, Mayús/clic selecciona un rango; cambiar entre vídeo/audio inicia otra
selección. Ctrl+D duplica; Supr conserva hueco; Mayús+Supr hace cierre global;
M añade marcador. Parámetros y flags se aplican al clip principal del inspector.
La lista de marcadores permite guardar/quitar/ir. Borrar audio conserva las
posiciones de otras pistas. Un marcador o bloqueo no invalida una previsualización
si no cambia el contenido audiovisual.

## Identidad de render y ganancia

`edit_sha256` identifica todo el documento editable. `render_sha256` identifica
la parte audiovisual, excluyendo marcadores, bloqueos y fuentes no usadas. El
contrato de compositor forma parte de esa identidad. Los renders antiguos se
conservan y se marcan obsoletos cuando requieren el contrato actualizado.
El limitador mantiene el techo0.95 y compensación de latencia; se desactiva su
nivelado automático para no elevar silenciosamente la ganancia solicitada.

## Evidencia y límites

Pruebas de transacciones, rollback, deshacer, duplicación, bloqueo, ripple,
audio/cues/marcadores, grafo de solo y capacidades. Pruebas de navegador con
transporte interceptado reutilizan las funciones puras del backend; no son AV.

Además se ejecutó el compositor nuevo en otro proceso con raíz de proyectos
aislada, medios existentes y sin tocar Studio activo. Dos MP4 reales de6s:
hueco negro/silencioso (RGB y RMS0) y solo de audio independiente (ratio RMS≈0.2488
para ganancia0.25, silencio después del clip). Ambos decodifican por completo.
El primer ensayo reveló nivelado automático y permanece en el historial de QA;
la corrección se verificó en el mismo workspace, sin repetir importaciones.
Informe `EVIDENCIA_MODELO_TIMELINE_20261124.json`; validador opt-in
`python -B -m scripts.validate_studio_timeline_model --source-project ... --workspace ...`
con `--recheck` reutiliza su proyecto de laboratorio.

Esto no acredita activación del backend en4750, observación de Windows, escucha
o sincronía integral. Las entregas posteriores se detallan en
`EDITOR_EFECTOS_MANUALES_ES.md`, `EDITOR_CAPAS_TRANSICIONES_ES.md` y
`EDITOR_CANCELACION_RENDER_ES.md`, con evidencia separada y activación pendiente.
