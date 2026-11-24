# Estado del encargo editorial7141865417 (#92)

## Implementado y probado, por entregas

1. Proporciones y preferencias: biblioteca320px, migración de tamaños comprimidos,
   restablecer solo distribución del editor, splitters por ratón/teclado,
   paneles con scroll interno y mínimo de pistas adaptado al número de filas.
   Ajustar al montaje incluye colas de audio/cues/marcadores, regla adaptable,
   cursor compartido, zoom y restauración de vista por proyecto.
2. Cortes por cursor, bordes por arrastre/teclado, imán opcional, audio posicionado,
   selección múltiple, duplicar, borrado con hueco negro/silencio y ripple,
   marcadores, solo/mute/bloqueo y undo/redo atómico. La pérdida de foco por
   ResizeObserver se corrigió conservando el handle y evitando redraw por altura.
3. Forma de onda real decodificada, medidor de RMS/pico de preescucha, ganancia,
   fades y normalización opcional reutilizando AudioMixer. Cues editables por
   formulario y arrastre, split/merge/offset/estilo y SRT original conservado.
4. Encuadre focal, zoom/reflejos/giro, títulos visibles ASS, preset local editable,
   composición de hasta4 capas y transición audiovisual por negro sin solapar.
5. Cancelación con intento exacto, cierre del encoder propio comprobado, parcial
   sin publicar y nuevo intento desde la misma revisión sin repetir herramientas.

Todo usa el mismo estado revisionado que `studio_project_edit`, con procedencia
y hashes de fuentes; no existe una maqueta o proyecto separado del agente.
Ninguna prueba instala modelos, hace inferencia ni altera ComfyUI.

## Qué acredita cada evidencia

| Ámbito | Resultado | Límite |
|---|---|---|
| HTTP activo4750 | Health y edición anterior responden tras Esc; ciclo previo con medios reales | Backend nuevo aún sin /capabilities; no reiniciado |
| Laboratorio FFmpeg local | Cortes, huecos, solo, mezcla, título, encuadre, capas, transición y cancelación con medios existentes; MP4 decodificados | Proceso y raíz aislados; no implica activación en4750 |
| CI navegador | DOM, proporciones1920×1080/3440×1440, preferencias y controles; transportes interceptados identificados | No carga audiovisual real ni observa ventana Windows |
| Ventana Windows y escucha | Pendiente | No hay node_repl/sky en sesión; no se sustituye con otro controlador |

Evidencias JSON: `EVIDENCIA_TIMELINE_LIVE_20261124`,
`EVIDENCIA_CUES_LIVE_20261124`, `EVIDENCIA_AUDIO_TIMELINE_20261124`,
`EVIDENCIA_MODELO_TIMELINE_20261124`, `EVIDENCIA_EFECTOS_MANUALES_20261124`,
`EVIDENCIA_CANCELACION_RENDER_20261124` y `EVIDENCIA_CAPAS_TRANSICIONES_20261124`.
Los primeros ensayos y sus fallos/correcciones quedan en historial, no se ocultan.

## Aceptación restante y bloqueos

La instrucción vigente de no reiniciar Studio impide activar módulos Python
nuevos dentro de su proceso. No se usará inyección/hot reload para eludirla.
Al habilitar la activación, comprobar antes trabajos activos; luego API real,
panel con proyecto y medios existentes, persistencia, reproducción/sincronía,
escucha, cancelación desde el botón y recuperación. Esa aceptación no se sustituye
con CI. No declarar finalizado #92 ni cerrar la PR.

Límites funcionales explícitos: transición cruzada, keyframes/máscaras, mezcla A/B,
edición de región de waveform, importación ASS/karaoke y conversión desde montajes
del pipeline aún no disponibles. Las capas son visuales y acotadas; el audio se
añade por su pista. Acortar/reordenar que deje títulos/capas/transiciones fuera
se rechaza con error y conserva la revisión; ajustar intervalos explícitamente.
Presets etiquetan destinos sin publicar ni certificar límites de plataformas.

Configuraciones de aplicaciones/settings y proyecto fuente continúan con sus
hashes originales. PR#2 en borrador y costo operativo$0.

## Publicación y CI del código

Entrega de efectos4ab1d5e; cancelación54aa0ca; capas/transiciones2807adca.
En2807adca: CI45483046903 aprobada,3466passed/44skipped/3xfail/40subtests,
131.24s; lint aprobado y suite sin red externa. Contratos45483047205 aprobados
en Windows/Linux; navegador43passed/70.52s. No hubo aumentos de timeout,
ocultación de fallos ni retirada de pruebas.

Capturas de proporciones1920×1080 y3440×1440 inspeccionadas desde artefacto
CI45482058890/14963015589. Acreditan layout con JSON del proyecto existente,
medios204 interceptados; el visor vacío/error en ellas NO acredita reproducción.
Evidencia HTTP actual: `EVIDENCIA_ACTIVACION_EDITOR_20261124.json`, con coincidencia
de archivos estáticos servidos y workspace, PID73536, health200/capabilities404.
