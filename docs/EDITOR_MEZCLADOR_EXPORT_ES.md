# Mezclador: salida codificada y sincronía — #174

Continuación de `b4e4c3a`, en una copia nueva. Se reutilizaron el vídeo y los impactos SFX ya autorizados, incluyendo los ajustes EQ del clip existentes. Ambos grupos tienen audio audible verificado por sus referencias aisladas.

Se exportó **un único MP4 nuevo de 4 s**, H.264/AAC estéreo 48 kHz, 640×360 a 8 fps: nivel vídeo 0,3 y audio añadido 0,2. Para verificar silencio y solo sin renderizar otra vez vídeo, se produjeron dos salidas AAC solo de audio con el mismo grafo del editor: silencio de Audio y solo de Audio a nivel 0,2. No se repitió el render EQ/bypass aprobado.

El audio decodificado se comparó con las dos referencias de pista y su combinación esperada. Correlación/error RMS relativo:

| Estado | Correlación | Error RMS relativo |
|---|---:|---:|
| Nivel 0,3 vídeo + 0,2 audio | 0,999993 | 0,381 % |
| Silencio de Audio | 0,999993 | 0,384 % |
| Solo de Audio a 0,2 | 0,999964 | 0,848 % |

Son diferencias de la codificación AAC, no una prueba de escucha. Cada señal tiene 192.000 muestras por canal. Los 32 fotogramas decodificados **y sus PTS** son idénticos a la salida de vídeo previa reutilizada. Audio y vídeo mantienen duración de 4 s.

Dos subtítulos técnicos nuevos, explícitamente QA y no transcripción inventada, se exportaron como `mov_text`. Al extraerlos se conservaron exactamente textos y límites 0,750–1,750 y 2,000–3,500 s. Esto acredita sincronía temporal del subtítulo seleccionable, no un render de subtítulos quemados ni sincronía semántica de palabras.

Salida local: `projects/qa174-mixer-export-root/edit-43cd66fe472f/assets/editor-renders/eef989a8158645b097e6d9ba27d610e6/montage.mp4`. SHA256 ya registrado por el exportador: `e1e2af5aa01db0371809242d3c0a7320cd74dbca7487913b5d894a2bbdafed62`. No volver a renderizar o hashear para repetir esta aprobación.

[Informe estructurado](EDITOR_MEZCLADOR_EXPORT_EVIDENCIA_20261126.json). Original intacto, sin inferencias, instalaciones, CI ni comprobaciones de modelos. La instancia4750 y la escucha humana permanecen pendientes; `escucha-ab.html` se conserva sin modificar.

Activación agrupada futura, solo tras confirmación del reinicio manual: identidad residente/disco, `restart_required:false`, capabilities `track_mixer`, `audio_ducking`, `audio_processing`, `sfx_catalog`, `sfx_favorites`; en una copia comprobar mezclador, EQ, compresor, bypass y una preescucha/inserción. Sin otro reinicio ni repetir estas mediciones.
