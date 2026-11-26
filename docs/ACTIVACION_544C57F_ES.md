# Activación real de la entrega544c57f en Studio4750

26-11-2026 UTC. [Resultados](ACTIVACION_544C57F_RESULTADOS.json).
El usuario reinició manualmente. **No se reinició ni detuvo Studio** durante
esta comprobación. PR2 conservada en borrador. Sin CI, síntesis, ASR, render,
descarga, instalación ni recálculo manual de hashes de recursos/modelos.

## Identidad y compatibilidad

Puerto4750, PID138604, arranque12:13:08UTC. APIprotocol1/editor3.0;
identidad residente y disco coinciden, `restart_required=false`:
`bca8fb3156d1cb4a5c102adadacaee6109a1988265edf69acf6ecbad1505207a`.
Coincide con la identidad técnica guardada de la entrega validada.544c57f
solo consolidaba documentación del código4242eca; el checkout ZIP acredita
contenido, no una revisión Git cargada por magia. No se volvió a calcular
huella de los modelos ni a ejecutar la CI aprobada.

`/api/studio/editor/capabilities` coincide con `identity.editor` y su build.
Activos `silence_apply`, `qwen_tts_plan`, `reference_plan`, `component_add`,
`component_remove`, reloj/revisión compartidos y `qwen-preview-v1` con worker
real/cancelación propia/sin retry. Chrome real en4750 no muestra incompatibilidad.
Cola sin trabajo activo al preparar las copias. Blender4.5.15 sigue seleccionado;
5.3 está disponible como perfil separado, sin abrir Blender ni repetir piloto.

## Copias y operaciones comprobadas

Se crearon `edit-qa544-silence`, `edit-qa544-components` y `edit-qa544-qwen`.
JSON copiado; medios existentes enlazados para lectura. Solo estas copias reciben
escrituras. Sus recibos de render conservaban URL de la instancia aislada:
se ajustó únicamente la URL de las copias, sin regenerar archivos.
Los31JSON de las tres fuentes siguen idénticos por comparación directa,
sin hashes nuevos ni lectura completa de medios. Configuraciones sin cambios.

| Flujo | Evidencia en4750 | Límite |
|---|---|---|
| #130 silencios | Propuesta/revisión/aplicación real;116palabras fuente conservadas; undo/redo exactos y guardar/reabrir | Intervalo explícitamente sintético; no medición acústica ni escucha |
| Pistas/cues | Corte de1frame `[63,64)`;3audios/3títulos/3capas sincronizados por contrato;19cues pasan a20 por división de un cue atravesado | Dos tramos contiguos conservan el mismo texto; no exigir recuento idéntico como prueba de integridad |
| #146/#147 | Los tres formularios añaden tarjeta/comparativa/collage reales; deshacer restaura la base en cada caso; transformación manual/undo/redo/reapertura | Sin nuevo render de los cambios de esta sesión |
| #149 Qwen | Dos perfiles consultables; recibo Base recuperado/cargado/reproducido silenciado; importar duplicado deshabilitado; siguen3solicitudes previas | No nueva síntesis ni nueva cancelación. El estado cancelado de la prueba anterior sobrevivió al reinicio |
| #132 medios | MP4 HyperFrames existente4s reproducido desde4750; montaje de componentes4s y portugués22,36s también | Reproducción silenciada no acredita escucha ni nueva sincronía medida |
| #145 referencias | Herramienta registrada envía `reference_plan` al propietario4750; revisión18 guardada con origen agente; recuperación sin reenviar; undo19/redo20/save21 | Contrato inicial, sin dirección/generación automática ni revisión humana |

La copia portuguesa modificada queda con render anterior **current=false**:
el reproductor previo no se presenta como exportación del nuevo corte.
El render de componentes vuelve a **current=true** tras restaurar su base.
No se exportó para resolver esa obsolescencia, conforme al límite de esta tarea.
La comparación independiente de intervalos confirma el mapa2,52–2,56s para
4cortes/3audios/3capas/3títulos/20cues y todos los marcadores. Las116palabras
fuente permanecen idénticas. Es sincronía estructural, no revisión fonética.

## Continuación independiente: referencias #145/#122

Se reutilizaron recibo y PTS9,875/10,5/11,167 ya guardados. Se enlazó un marcador
existente como **nota técnica QA**, sin atribuir al usuario un comentario nuevo.
Comparación declarada del mismo instante9,875, con imagen antes/después idéntica
(control sin transformación). Solo escena `one` invalidada; `two` inalterada.
No extracción de fotogramas, ASR, descarga ni recálculo de hashes de medios.
FrameSampler figura disponible en el catálogo4750; su extracción/caché anteriores
no se repiten. Muestreo parcial no equivale a observar/escuchar el vídeo completo.

## Límites encontrados, sin ocultarlos

1. **HTTP #92:** una lectura Python recibió10054; PowerShell pudo leerla.
   El envío Python registrado `studio_project_edit` de referencias también
   recibió10054, pero el backend ya había confirmado en disco la revisión18
   con origen agente. No se reenviaron writes. Se recuperó estado por lectura;
   API del agente posterior guardó undo/redo/save19–21. Esto acredita el contrato
   backend, **no fiabilidad completa del transporte Python**. Causa desconocida;
   sin capturas extensas, cambios de red ni atribuirlo a selección de consola.
2. **HyperFrames #132:** código/catálogo activados y render guardado reproducible,
   pero `/api/studio/tools?name=hyperframes_compose` devuelve `unavailable`.
   El proceso manual no heredó selección privada de paquete/navegador/Node.
   El perfil preparado `.runtime/qa/hyperframes-offline-profile.json` y launcher
   `scripts/run_hyperframes_offline.py` siguen disponibles para hijos explícitos.
   No reinstalar ni redescargar; no se cambió el entorno del servidor ni se
   repitieron doctor/render. No declarar habilitado el runtime genérico4750.
3. **#112:** siguen sin existir registros `artifacts/piper_previews/*.json`
   elegibles. Qwen/sidecars WAV no los sustituyen. No se sintetizó para fabricar uno.
4. Escucha/naturalidad humanas, español audiovisual#107/#130, GLB propio#143
   y variantes audiovisuales ampliadas siguen pendientes. No se cierran por CI.

Siguiente alcance técnico concreto: selección explícita del perfil HyperFrames
en el puente existente, preservando el arranque normal, sin otra instalación;
requiere cambio acotado y comprobación separada, no otro render del piloto.
El problema HTTP mantiene su seguimiento y evidencia; no se cambia transporte
sin aislar la causa. Esta activación no reabre pruebas ya aprobadas.
