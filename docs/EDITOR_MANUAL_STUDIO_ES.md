# Editor manual de Studio (#92)

Implementación inicial, local y sin inferencias. **#92 sigue abierto:** publicar código no acredita el ciclo audiovisual ni la aceptación visual de la instalación del usuario.

## Espacio de trabajo

Abre `/studio`. Vídeo, Audio, Subtítulos, Biblioteca y Proyectos conservan el mismo montaje seleccionado (`?edit=…`). La biblioteca queda a la izquierda, el monitor en el centro, el inspector a la derecha y las pistas abajo. Distribución permite ajustar tamaños y ocultar paneles; esos valores se guardan en el navegador. El color sigue siendo GitHub Dark. Producción y agente, Aplicaciones, Cola y Recursos conservan los flujos anteriores y sus configuraciones.

La fuente individual y el montaje tienen etiquetas distintas. **Ver fuente** reproduce el archivo importado, no simula la edición. **Preparar vista previa del montaje** ejecuta FFmpeg sobre la revisión guardada. La exportación usa el mismo grafo a resolución completa. Un cambio invalida la reproducción del montaje anterior. No se inicia inferencia al abrir una pestaña.

Guardar/reabrir sin cambiar decisiones conserva una vista previa vigente: su validez se determina por la huella del montaje, mientras la revisión de comandos sigue protegiendo las escrituras concurrentes. Los resultados anteriores sin huella conservan el criterio de revisión y pueden requerir una nueva preview una vez.

Si la instancia que ya estaba abierta no tiene las rutas nuevas, se informa que falta reiniciarla y los controles del editor quedan desactivados. Los accesos anteriores permanecen disponibles. No se debe matar un proceso ajeno ni reiniciar ComfyUI/Ollama para activar este editor.

## Ciclo de vídeo

1. **Nuevo montaje** crea un proyecto manual independiente; no reemplaza artefactos de una producción existente. Elige su título. Proyectos permite seleccionar/reabrirlo.
2. Importa o suelta vídeos/audio propios en Biblioteca. Studio conserva el original y guarda una copia de importación con nombre único. Alternativamente registra una ruta existente dentro de `assets/` de ese proyecto. No se aceptan rutas externas ni URL remotas.
3. **Añadir a pista** incorpora un medio al montaje. Selecciona el clip en las pistas para reproducir su fuente y abrir el inspector.
4. Ajusta entrada/salida y pulsa **Aplicar recorte**. **Dividir** usa el punto indicado en segundos de fuente. Arrastra para reordenar o usa **Anterior/Siguiente**. **Quitar clip** elimina la decisión, nunca el medio. Para quitar un intervalo interior, divide sus dos límites y quita el segmento central. Las pistas muestran miniaturas de las fuentes y un cursor ligado al tiempo del monitor; las filas de audio respetan su inicio temporal independiente.
5. Deshacer/Rehacer restauran decisiones anteriores; también Ctrl+Z/Ctrl+Mayús+Z fuera de formularios. Se retienen 50 estados. Cada operación guarda atómicamente; Guardar añade un punto explícito de historial. Reabrir lee disco y descarta cambios de formulario que no se hayan aplicado.
6. Selecciona proporción/FPS y pulsa **Aplicar salida**. Presets: horizontal 1920×1080, vertical 1080×1920, cuadrado 1080×1080 y 4:5 1080×1350. Siempre se encaja con bandas: no hay recorte ni estirado silencioso. Los nombres de plataforma son orientación de formato, no una certificación de sus límites de publicación.
7. Prepara la vista previa, espera el estado completado y revisa con los controles reales del reproductor. Exportar MP4 crea un resultado nuevo y un snapshot del montaje, con SHA256 y procedencia. Descargar resultado copia ese archivo al destino elegido por el navegador. Exportar no publica.

La base temporal del montaje es el FPS de salida: cada corte se ajusta al fotograma más próximo; se rechazan cortes inferiores a un fotograma. Entrada/salida siguen expresadas en segundos de fuente; velocidad modifica la duración resultante. Audio se rellena/recorta para mantener los límites de los clips y la duración final. Vista previa: 960×540, 540×960, 540×540 o 432×540 según proporción, siempre dimensiones pares y relación exacta.

## Audio

Añade audio desde la biblioteca y selecciona su clip. Entrada/salida, división, inicio en el montaje, velocidad, ganancia, silencio y fundidos modifican la mezcla FFmpeg. Las pistas adicionales se mezclan sobre el audio de los vídeos; la duración final es la del montaje de vídeo y se aplica un limitador. Los extremos que queden fuera del montaje no se exportan.

Audio muestra una forma de onda calculada por Web Audio a partir del primer canal del archivo seleccionado, sin generar audio. Un clic busca ese punto de la fuente. No representa la mezcla ni los efectos. Límite de decodificación: 100 MB; formatos no admitidos por el navegador producen un mensaje explícito. El zoom temporal de las pistas modifica su escala visual. Solo, bloqueo, medidores, pistas nombradas voz/música/FX y comparación A/B de mezclas siguen pendientes.

Kokoro, Qwen y ACE-Step no se ejecutan desde este editor. Sus flujos existentes permanecen en Producción/Recursos. Su integración previa no constituye una nueva prueba de voz o música.

## Subtítulos

Importar SRT valida y guarda sus cues y una copia de **los bytes originales**, con nombre y SHA256, incluso si incluye BOM o saltos CRLF. Los cambios posteriores en el campo SRT se guardan con Aplicar; nunca sustituyen esa copia de origen. También puedes escribir texto/tiempos directamente y aplicar. Se comprueban numeración, intervalos, duración, orden y solapamientos mediante el lector existente. Se muestran caracteres por segundo; no se declara un umbral universal de calidad.

Puedes desplazar todos los tiempos, dividir un cue por tiempo/carácter y unirlo al siguiente. Texto y tiempos también se corrigen en SRT. Exportar SRT/ASS descarga una representación de la revisión actual. ASS reutiliza el generador existente con Arial, tamaño relativo a 1080p, posición y márgenes seguros. Las llaves y barras del texto se escapan.

Para MP4 elige pista seleccionable (`mov_text`, sin promesa de conservar el estilo) o texto quemado (libass, ya no editable dentro del MP4). Prepara una nueva vista previa después de cambiarlo. La vista de pista seleccionable añade un texto de revisión en el navegador; el reproductor externo puede presentarlo de otra manera. ASS de entrada, karaoke por palabra, traducciones separadas y fuentes personalizadas siguen pendientes.

## Contrato compartido con el agente

Autoridad única: el servidor Studio en loopback. `tools.video.studio_project_edit.StudioProjectEdit` se conecta por HTTP al puerto `BACKLOT_PORT` o 4750. No crea otro escritor de archivos en el proceso del agente. Si Studio no está activo informa el fallo; no crea una copia alternativa del proyecto.

`read` devuelve revisión, decisiones y eventos sin los snapshots completos de deshacer. `command` exige revisión exacta y operaciones de la misma función que usa la UI. `register` registra un medio del proyecto. `render` prepara vista previa/exportación con revisión exacta; `render_status` consulta el resultado y su vigencia. Un render produce medios y solo debe solicitarse con material y alcance autorizados; las pruebas de esta entrega simulan su transporte, no lo ejecutan. Ejemplo, sin ejecutar medios ni inferencias:

```python
from tools.video.studio_project_edit import StudioProjectEdit
tool = StudioProjectEdit()
current = tool.execute({'project_id': 'edit-ID', 'action': 'read'})
# Leer current.success y revisar sus decisiones antes de escribir.
result = tool.execute({'project_id': 'edit-ID', 'action': 'command',
    'command': {'operation': 'save', 'revision': current.data['revision']}})
```

Operaciones: `add`, `trim`, `split`, `remove`, `move`, `clip`, `output`, `subtitles`, `cue_update`, `cue_split`, `cue_merge`, `cue_offset`, `subtitle_style`, `save`, `undo`, `redo`. Origen `user`/`agent`, revisión y fecha quedan en historial. HTTP 409 significa proyecto ocupado/revisión anterior: leer de nuevo, inspeccionar y decidir; no repetir ciegamente una mutación.

Persistencia autoritativa: `projects/<id>/artifacts/manual_edit.json`. Reutiliza los campos de corte `id/source/in_seconds/out_seconds/speed/render_runtime` del contrato editorial; añade fuentes identificadas, audio, cues y preferencias del editor. **No se afirma que esta extensión sea intercambiable sin conversión con todo `edit_decisions.schema.json` ni que todos los compositores interpreten sus campos.** El adaptador nuevo y el renderer leen el mismo documento; no se sobrescribe `artifacts/edit_decisions.json` de producciones anteriores. La reentrada de montajes de producción y el intercambio completo siguen pendientes.

Durante un agente activo la UI no puede editar ese proyecto. El agente usa su ruta dedicada y revisiones optimistas. Durante un render se bloquean ambas escrituras. Los exports conservan una revisión congelada; los resultados antiguos se identifican como tales. Un render que quedó `running` tras reiniciar se informa interrumpido, no completado ni reanudado automáticamente. La escritura genérica de artefactos/textos/herramientas no permite sobrescribir el estado manual, importaciones ni snapshots del editor: debe usarse el contrato con revisión. La disponibilidad de `studio_project_edit` exige que la API actual esté accesible, no solo que exista código instalado.

## Límites y validación pendiente

Límites operativos explícitos: 200 fuentes, 200 clips, dos horas de vídeo, 2 GB por archivo importado, 500 KB por SRT, 30 s de diagnóstico y 600 s por render. Fallos se conservan en `manual_render.json`; no hay reintentos indefinidos. Se restringen protocolos/contenedores de entrada de FFmpeg; no se ejecuta código remoto, motores de IA ni descargas.

No disponibles: títulos, transiciones, reencuadre focal, solo/bloqueo, mezcla A/B, selección detallada sobre waveform y conversión de proyectos de producción. Están indicadas en el panel; no hay botones que simulen haberlas hecho. #92 no se cierra hasta cubrir y validar su aceptación restante.

Referencias de interacción consultadas 2026-11-24, sin copiar código ni instalar aplicaciones: [Kdenlive 26.08, áreas/monitores](https://docs.kdenlive.org/en/user_interface.html), [Audacity, pistas y waveform](https://manual.audacityteam.org/man/audio_tracks.html), [Subtitle Edit, ventana principal](https://github.com/SubtitleEdit/subtitleedit/blob/main/docs/features/main-window.md). Inspiraron la separación fuente/montaje, controles por pista y edición temporal; no son dependencias nuevas.

Evidencia y bloqueos: [VALIDACION_EDITOR_MANUAL_ES.md](VALIDACION_EDITOR_MANUAL_ES.md).

Validación posterior del motor con un vídeo existente, audio real y subtítulos manuales: [VALIDACION_EDITOR_MEDIOS_REALES_ES.md](VALIDACION_EDITOR_MEDIOS_REALES_ES.md). Incluye el protocolo reproducible y separa API aislada/render real de revisión del panel local.
