# #92: validación con medios existentes (2026-11-24)

**El motor y la API aislada se comprobaron con medios reales. El panel local todavía no está validado.** No se utilizaron mocks de FFmpeg/FFprobe ni se inició inferencia, descarga o instalación. Esta actualización continúa la [entrega anterior](VALIDACION_EDITOR_MANUAL_ES.md); no acredita todavía todos los criterios de #92.

## Estado de la instancia que está abierta

`GET http://127.0.0.1:4750/api/studio/editor/projects` sigue devolviendo **404**. El listener sigue siendo PID45692, iniciado2026-11-24T03:26:14.5444796Z, igual que en la sesión anterior. La cola informa `worker_active=false` y `local_task_active=false`.

El lanzador `OPENMONTAGE_ESTUDIO.cmd` llama a `backlot studio`; si ya hay un servidor saludable en4750, lo reutiliza y abre su URL. Por tanto, volver a abrir el panel no necesariamente actualiza el proceso que contiene las rutas Python. El código de esta copia sí incluye el router de edición.

Se intentó un reinicio condicionado **solo al404 y a que no hubiera trabajos activos**. La revisión automática rechazó el comando antes de ejecutarlo: `blocked by policy`, sin más motivo. El proceso original continúa; no se intentó otro mecanismo para eludirlo. Se necesita cerrar realmente ese servidor y arrancar la copia actualizada. No se reinicia un servidor cuya API de edición ya responda correctamente.

Para inspección de ventanas, la skill [computer-use](C:/Users/sando/.codex/plugins/cache/openai-bundled/computer-use/26.1117.31558/skills/computer-use/SKILL.md) exige `node_repl`; su guía dice «Use `node_repl` JavaScript for all Computer Use actions». Ese runtime no está disponible en la sesión. No se abrió un navegador alternativo. HTML/HTTP o fotogramas derivados no se presentan como revisión del panel local.

## Medio y aislamiento

Fuente existente en la biblioteca de vídeo del proyecto:

```text
D:\OPENMONTAJE-IA\BIBLIOTECAS_VIDEO\ANIMALES\NOAA\ex2502-dive04-0323-pinnoctopus_1920x1080.mp4
40 145 569 bytes; 1920×1080; 76.743333s; vídeo y audio
SHA256 27eea5e10838e5b05cd87ac5e9ab4ff80aba6aa7311f8c1ab19eb2d4f5e61e5b
```

Se conserva el archivo original; tamaño, mtime y SHA256 coinciden al terminar todas las fases. Se utilizó una copia de importación en un workspace nuevo bajo `projects/_qa-editor92-real-20261124-a/`, proyecto `edit-45a71ad12712`. No se reutilizan archivos personales fuera de la biblioteca ni se suben los vídeos/fotogramas a GitHub.

La prueba usa `FastAPI TestClient` **en proceso** sobre las rutas reales, con `OPENMONTAGE_PROJECTS_DIR` limitado a ese proceso y al workspace de diagnóstico. No es una petición al servidor4750 antiguo ni una simulación de su respuesta. No se modificaron configuraciones persistentes ni los proyectos anteriores. El renderer y todos los probes/decodificadores son los binarios FFmpeg/FFprobe configurados existentes.

## Vídeo real

1. Se crea un proyecto manual y se importa el archivo por el endpoint de upload. SHA256 de la copia coincide con el original.
2. Se añade un clip y recorta10–14s. La previsualización real dura4s.
3. Se divide en12s; el segundo corte se cambia a40–42s y se mueve delante. El primer corte original se recorta a10.5–12s.
4. Guardar y volver a leer el proyecto conserva las decisiones y la revisión: `40–42 → 10.5–12`, total3.5s. El segundo montaje se renderiza realmente a960×540.
5. Ambos MP4 pasan decodificación completa sin errores. La entrega de bytes mediante HTTP Range devuelve206.

La prueba descubrió un fallo de guardar/reabrir: guardar solo el historial incrementaba la revisión y hacía que un render con decisiones **idénticas** pareciera obsoleto. Reproducción real anterior: proyecto23/render22, decisiones iguales y `current=false`. Se corrigió la vigencia por SHA256 canónico de las decisiones, manteniendo la revisión de comandos para concurrencia. La UI usa esa misma identidad. Un cambio de edición invalida la preview; guardar o deshacer hasta el mismo contenido permite reutilizarla. Los resultados antiguos sin huella mantienen el criterio conservador anterior.

Prueba real posterior, sin repetir las fases ya aprobadas: se renderiza una vez, se guarda/reabre dos veces y se conserva el mismo archivo/hash. Proyecto25/render23, huella de edición coincidente y `current=true`. Se añadió regresión de backend y DOM; la prueba DOM sigue siendo sintética y no sustituye la comprobación audiovisual real ni la revisión del panel.

Se extrajeron y revisaron fotogramas reales: antes en0.5s se ve el plano de la fuente10.5s; después en0.5s aparece el plano cercano de40.5s y en2.5s vuelve el tramo de11s. El cambio de orden se ve en los archivos renderizados. Diferencia RGB media, escala0–255: resultado/fuente esperada2.27,2.29 y2.55; antes/después32.26. No se usa esa métrica como puntuación de calidad creativa.

## Audio real

Se extrae un fragmento del audio que ya contiene la copia importada; no se sintetiza una señal ni una voz. Se importa ese WAV por las rutas del editor, se silencia el audio de los cortes de vídeo y se mezcla la pista durante3.5s.

| Estado | RMS PCM normalizado | Pico PCM normalizado |
|---|---:|---:|
| Ganancia1 | 0.07560493 | 0.48947144 |
| Ganancia0.25, fundidos0.25s | 0.01691935 | 0.11773682 |
| Silenciado | 0 | 0 |

Relación RMS con ganancia/fundidos:0.223786. Los tres MP4 se renderizaron y decodificaron realmente. Guardar/releer conserva la pista y sus parámetros. Se restauró la pista después de la prueba de silencio; no se destruye la decisión anterior. La fase completada se reutiliza sin reimportar ni volver a renderizar cuando se ejecuta de nuevo el comando.

**No se acredita escucha humana ni waveform de Web Audio:** se verifican PCM/mezcla y persistencia del backend, no la experiencia auditiva o del navegador.

## Subtítulos reales sobre el vídeo

Se importa un SRT manual de prueba con BOM/CRLF, conservando sus bytes. El texto identifica expresamente la prueba: `QA #92: TEXTO MANUAL DE PRUEBA`; no es una transcripción ni afirma corresponder al audio.

Se desplazan los cues0.25s, se divide y se une el texto. El MP4 con pista `mov_text` se renderiza realmente y se vuelve a extraer su SRT: intervalo **0.750–1.750s**, texto correcto. Después se cambia a modo quemado, tamaño40, posición inferior, y se renderiza de nuevo. Se revisó el fotograma en1s: el texto manual aparece en dos líneas sobre la imagen, mientras el fotograma del MP4 con pista seleccionable no lo contiene quemado. Los bytes del SRT de origen siguen intactos tras los cambios y el proyecto se guarda/reabre.

No se declara sincronía semántica con la voz, traducción, karaoke ni selección de subtítulos en el navegador local.

## Evidencia y reproducción sin instalaciones

[JSON con hashes, tiempos, respuestas y métricas](EVIDENCIA_EDITOR_MEDIOS_REALES_20261124.json). Ocho renders reales completados: vídeo antes/después, tres estados de audio, subtítulos seleccionables/quemados y comprobación de reutilización al guardar. No se suben los medios; los archivos locales conservan procedencia y snapshots. Regresión local relacionada:90 passed/1 skipped,11.41s; sintaxis JS comprobada. La CI de la revisión se registra en #92 al finalizar.

Desde la raíz del repositorio, en un workspace **nuevo**, con una fuente autorizada de al menos43s y audio:

```powershell
.\.venv\Scripts\python.exe -B scripts/validate_studio_editor_media.py --source '<ruta-del-video>' --workspace 'C:\OPENMONTAGE-IA\projects\_qa-editor92-nuevo'
.\.venv\Scripts\python.exe -B scripts/validate_studio_editor_media.py --phase audio --source '<misma-ruta>' --workspace 'C:\OPENMONTAGE-IA\projects\_qa-editor92-nuevo'
.\.venv\Scripts\python.exe -B scripts/validate_studio_editor_media.py --phase subtitles --source '<misma-ruta>' --workspace 'C:\OPENMONTAGE-IA\projects\_qa-editor92-nuevo'
.\.venv\Scripts\python.exe -B scripts/validate_studio_editor_media.py --phase save-preview --source '<misma-ruta>' --workspace 'C:\OPENMONTAGE-IA\projects\_qa-editor92-nuevo'
```

El protocolo está acotado a esos fragmentos10–14/40–42s. No arranca/reinicia servidores, no abre ventanas ni llama a modelos. Usa dependencias ya presentes. El comando con medios reales es optativo, no se ejecuta en CI sin un archivo autorizado; los tests sintéticos anteriores mantienen su alcance separado.

Pendiente indispensable: activar la API del proceso local y disponer del controlador de ventanas permitido para verificar controles, reproducción, waveform y guardado/reapertura **en el panel**. #92 permanece abierto. PR#2 sigue en borrador; configuraciones/ComfyUI intactos, costo$0.
