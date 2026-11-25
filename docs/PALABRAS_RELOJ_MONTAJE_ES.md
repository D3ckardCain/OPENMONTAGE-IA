# E04: inspección de palabras en el reloj del montaje (#115)

Carencia independiente de #112–#114: las palabras ASR guardadas estaban en reloj
de fuente. SubtitleGen agrupa palabras, pero no conoce los cortes del EDL. Esta
entrega reutiliza esos registros y `studio_editor.frames`; no añade otro ASR,
alineador, motor de subtítulos ni ejecución de SubtitleGen que escriba archivos.

## Operación real de lectura

En Biblioteca → Candidatos por palabras, seleccionar un conjunto ASR guardado y
pulsar **Inspeccionar palabras en el reloj del montaje**. El control consulta la
API y muestra ocurrencias por clip, texto/índice, tiempo fuente→salida, idioma,
hablante declarado y origen temporal. Solo lectura: no escribe EDL/cues, no
crea SRT, no exporta y no llama modelos. Funciona sobre datos existentes.

API: GET `/api/studio/editor/{pid}/subtitle-words?set_id=ID_GUARDADO`.
Agente: StudioProjectEdit3.1.0, action=subtitle_words,project_id,set_id; utiliza
ese mismo GET y recibe revisión/base/hash junto al informe. No hay escritor o
proyecto privado del agente. Capability nueva `subtitle_words`; el control no
se ofrece con un backend antiguo. Una revisión cambiada mientras se consulta
impide presentar el informe como actual.

## Relojes, texto y procedencia

- Se recorre la pista de cortes de vídeo en su orden real. Clips ajenos y huecos
  avanzan el reloj; ocurrencias de una fuente repetida conservan IDs distintos.
- El inicio es la suma de fotogramas de salida anteriores/FPS, reutilizando la
  regla existente de redondeo del editor. Dentro del clip:
  `t_salida = inicio_clip + (t_fuente - entrada_fuente) / velocidad`.
- Se conservan intervalos medio abiertos y segundos más fracciones exactas
  `[numerador,denominador]`. El EDL actual admite FPS entero1–60 y su base se
  expresa racionalmente como[FPS,1]; **no** se añaden presets30000/1001 ni VFR.
  La representación racional no demuestra calibración de PTS de un medio real.
- No se vuelve a añadir el offset ya aplicado al importar las palabras. Se
  conservan índice, texto, spans fuente/salida, idioma y speaker declarado;
  speaker no identifica a una persona por esta operación.
- Texto/negaciones no se reescriben. Palabra parcial en un límite, intervalo
  cero o fin perdido por cuantización de fotogramas se **excluye y reporta**,
  sin recortar silenciosamente su texto ni inventar alineación. Si se corta «No»,
  queda visible en exclusiones y requiere revisar el corte/contexto.
- Una palabra no se convierte en «medida» por trasladar su reloj. Se preserva
  timing_status declarado(measured/estimated/imputed/unknown) con evidencia
  declarada/no verificada. Ausencia del campo queda unknown; no se realinea audio.
- Se incluyen SHA de fuente registrado, transcripción, datos de palabras y EDL,
  además de procedencia ASR guardada/modelo/offset/idioma cuando existen. Esta
  consulta **no relee ni certifica el archivo multimedia**: source_file_rehashed
  es false. El hash de metadata no sustituye verificar fuente real al exportar.
- Cobertura parcial permanece explícita; no se equipara ausencia de palabras
  con silencio. Palabras fuera de orden/cobertura o fuente declarada cambiada
  fallan, sin corrección oculta ni nueva descarga.

No se mapean voces de capas ni pistas de audio independientes en esta entrega;
solo el reloj secuencial de los cortes de vídeo. No se garantiza contexto editorial,
karaoke, sincronía perceptual, legibilidad final o safe areas por este informe.
Las ocurrencias solapadas conservan su solape; no se arreglan como cues ficticios.

Límites:5000palabras/200cortes/20000ocurrencias+exclusiones; excederlos produce
error, no un informe parcial disfrazado de completo. UI presenta las primeras100
ocurrencias/20exclusiones para evitar llenar el panel, con aviso; el JSON conserva
el informe completo. Tabla con scroll interno y resumen de estado accesible,
no anuncio de cada fila como log. Texto se inserta como textContent.

## Pruebas focalizadas nuevas y límites de activación

25 pytest nuevos aprobados: fuentes distintas, huecos, reordenación/duplicados,
velocidad/fracciones, offset no duplicado, negación cortada, duración cero,
cuantización/medio fotograma, cobertura parcial, solapes, fuentes obsoletas,
NaN/Inf/bool/orden/índices/FPS/límites y API/agente con bytes de proyecto intactos.
Solo metadatos/texto sintéticos, sin archivo multimedia que leer ni mock de ASR
presentado como inferencia. No se repiten pruebas aprobadas #107/#111–#114.

`scripts/validate_word_clock_ui.cjs`: Chrome/Playwright existentes, UI real con
informe sintético interceptado;3GET,0POST,0comandos. Tabla100filas con advertencia,
exclusiones/cobertura visibles, texto HTML no ejecutado, revisión obsoleta
rechazada, error claro y control ausente si falta capability. Sin errores JS.
Esto prueba el control en aislamiento, **no** el panel4750 ni sincronía audiovisual.

Código/manual preparados para el mismo reinicio manual futuro junto con
#112–#114. No se reinició ni consultó Studio activo, no se modificaron proyectos
originales, settings, .venv ni ComfyUI; no instalaciones, medios ni inferencias.
Coste$0; valoración natural/robótica sigue aplazada y PR#2 en borrador.

Plan de smoke del lote inicial: [#112–#114](COMPROBACION_CONJUNTA_112_114_ES.md).
Tras activar, el extra de #115 consiste solo en ver capability y consultar un
conjunto guardado en una copia QA; no volver a ejecutar ASR/exportación aceptados.
