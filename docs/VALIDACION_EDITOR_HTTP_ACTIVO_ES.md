# #92: servidor activo y medios reales (2026-11-24)

**La API de edición ya responde200. Se validaron sus operaciones mediante HTTP real contra el servidor activo. No se reinició el servidor. La interacción con la ventana local sigue sin verificar.**

Esta fase sustituye el bloqueo404 registrado en [la prueba anterior](VALIDACION_EDITOR_MEDIOS_REALES_ES.md). La prueba anterior era en proceso aislado; esta usa conexiones HTTP reales a `http://127.0.0.1:4750`, sin TestClient ni sustituciones de FFmpeg/FFprobe.

## Navegación y proceso comprobados

- `/` responde con título **Backlot — Library** y un enlace a `/studio`; no contiene `edit-player`.
- `/studio` responde con el editor de Vídeo/Audio/Subtítulos y su monitor.
- `/api/studio/editor/projects` responde200. Inicialmente la lista estaba vacía; después contiene el proyecto de prueba creado por esta fase.
- El módulo `/ui/editor.js` servido coincide con el archivo local actualizado.
- PID73536 antes y después, Python3.11.9 de la instalación existente, raíz de proyectos `C:\OPENMONTAGE-IA\projects`. Cola pausada y sin trabajador al comenzar. No se ejecutaron comandos de reinicio, parada, instalación o apertura de navegador.

Proyecto preparado, seleccionable y editable por usuario/agente:

[Abrir el editor del proyecto real de QA](http://127.0.0.1:4750/studio?edit=edit-827337e03f38#video).

El enlace apunta al editor, no a la Library de la raíz. El vídeo de QA es una derivación breve de la biblioteca existente; no se incorpora a una producción anterior ni se reemplazan sus artefactos.

## Comprobaciones por HTTP real

Fuente conservada: `D:\OPENMONTAJE-IA\BIBLIOTECAS_VIDEO\ANIMALES\NOAA\ex2502-dive04-0323-pinnoctopus_1920x1080.mp4`,40145569bytes,76.743333s,1920×1080 con audio. SHA256 `27eea5e10838e5b05cd87ac5e9ab4ff80aba6aa7311f8c1ab19eb2d4f5e61e5b`; tamaño/mtime/hash coinciden al acabar. Los medios y fotogramas permanecen locales.

| Área | Resultado comprobado | Alcance pendiente |
|---|---|---|
| Vídeo | Upload40MB, añadir, recortar10–14s, dividir12s, mover40–42delante de10.5–12, guardar y GET/reabrir; previews4s/3.5s reales; fotogramas muestran el orden modificado | Clic/arrastre y playback dentro de la ventana local |
| Audio | Importar WAV extraído del audio existente, mezcla de3.5s, ganancia1/0.25 y fundidos, silencio PCM0, parámetros persistidos | Escucha humana y waveform Web Audio |
| Subtítulos | Importación de bytes SRT originales, desplazar/dividir/unir, mov_text extraído0.750–1.750s, texto quemado visto sobre un fotograma real | Edición/selección de pistas desde el navegador local |
| Guardar | Huella de edición conserva el mismo MP4 tras guardar/reabrir con revisión de comandos mayor | Estado visual del monitor en la ventana |
| Exportar | MP4 real1920×1080,3.5s, audio/subtítulos quemados, decodificación completa; SHA256 `72af68d538d06a7ccccc89a3ce554d64a3defa7a53779a80a70a324c0cdda734` | Descarga mediante el control del navegador |
| Agente | Herramienta `studio_project_edit` disponible; read/save del mismo proyecto25→26; origen `agent`, preview vigente; escritura con revisión anterior rechazada409 | No se ejecutó un modelo ni se acredita decisión de Ollama |

RMS PCM de audio real:0.07560493 a ganancia1;0.01691935 con ganancia0.25 y fundidos0.25s, relación0.223786. Silenciado: RMS0/pico0. El texto `QA #92: TEXTO MANUAL DE PRUEBA` es manual y no se presenta como transcripción. Se revisaron los fotogramas decodificados del montaje reordenado y del texto quemado; son archivos del resultado, no capturas de la ventana.

Nueve renders del servidor completados, decodificación completa sin errores y HTTP Range206 en9/9. El estado final conserva revisión27/render26, misma huella de edición y `current=true`. No se atribuye el éxito a mocks de transporte o de encoder.

## Fallos corregidos y diagnóstico reutilizable

El listado de proyectos solo se cargaba al iniciar la página o crear un proyecto desde ella. Entrar en «Proyectos» no volvía a consultarlo; un proyecto creado desde otro cliente/agente podía faltar hasta recargar la página. Se corrige el listener de ese menú para solicitar la lista actual, conservando proyecto y revisión seleccionados. Una regresión de navegador reproduce el alta externa con un fixture JSON; **esa prueba es de DOM/contrato, no prueba audiovisual de la ventana local**.

El modo HTTP del diagnóstico encontró inicialmente una dependencia `httpx` ausente. Se conserva el recibo fallido en `projects/_qa-editor92-live-20261124-a/report.json`; no se instaló nada. Se implementa transporte con `urllib` de la biblioteca estándar, limitado por CLI a un origen HTTP loopback y sin proxy. La ejecución completa aprobada está en `_qa-editor92-live-20261124-b/report.json`.

El script [validate_studio_editor_media.py](../scripts/validate_studio_editor_media.py) añade `--live-url`. Mantiene el modo aislado predeterminado y verifica que la raíz local de proyectos coincida con la anunciada por el servidor. Cada fase reutiliza el proyecto/recibos anteriores; no inicia servidores ni repite fases completadas.

```powershell
.\.venv\Scripts\python.exe -B scripts/validate_studio_editor_media.py --live-url http://127.0.0.1:4750 --source '<video-autorizado-existente>' --workspace 'C:\OPENMONTAGE-IA\projects\_qa-editor92-live-nuevo'
# Mismo source/workspace/URL para continuar; fragmentos acotados10–14/40–42s:
.\.venv\Scripts\python.exe -B scripts/validate_studio_editor_media.py --phase audio --live-url http://127.0.0.1:4750 --source '<misma-ruta>' --workspace 'C:\OPENMONTAGE-IA\projects\_qa-editor92-live-nuevo'
# Fases siguientes: subtitles, save-preview, export.
```

[JSON de evidencia: respuestas, hashes, tiempos y métricas](EVIDENCIA_EDITOR_HTTP_ACTIVO_20261124.json). No se suben medios, fotogramas, configuraciones ni entornos. Los resultados de CI del commit se registran en #92 después de finalizar; el harness de medios es optativo y no genera contenido en CI.

Validación local de esta revisión:90 passed/1 skipped en10.31s para editor/producción/UTF-8; sintaxis JS/Python y JSON de evidencia comprobados. La regresión de actualización del listado se ejecuta en el job de navegador existente de CI; no se lanzó uno local.

## Límite de revisión del panel

La skill [computer-use](C:/Users/sando/.codex/plugins/cache/openai-bundled/computer-use/26.1117.31558/skills/computer-use/SKILL.md) exige una sesión `node_repl` («Run this once per fresh `node_repl` JavaScript session»). Ese runtime no aparece en las herramientas disponibles. No se abrió otro navegador ni se usó un controlador alternativo para eludirlo. Sigue pendiente observar la ventana local y comprobar controles, playback, waveform y escucha allí. Las respuestas HTML, los fotogramas de FFmpeg y la CI con fixtures no sustituyen esa evidencia.

El bloqueo de API/reinicio está resuelto: **no se solicita otro reinicio**. #92 permanece abierto por la aceptación de ventana/playback y las funciones avanzadas ya documentadas. PR#2 continúa en borrador. Configuraciones mantienen SHA256 `497DDCD0…09AD952` y `33073A45…4CCF7B`; ComfyUI intacto, sin inferencias/descargas/instalaciones, costo$0.
