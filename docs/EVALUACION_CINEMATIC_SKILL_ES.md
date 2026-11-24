# Cinematic Skill: evaluación #76

24-11-2026 UTC. `Moh4696/cinematic-skill@bf435561c6203f90f971300efe952b68b5ec3417`.
Sin versión de paquete/runtime declarada en requisitos revisados: identidad por commit.
Lectura estática; no instalar skill, fuentes, paquetes ni ejecutar examples/new_project.

## Decisión y contraste

Métodos útiles: eventos ligados a palabras, cámara continua y expediente de créditos;
no otro director/TTS/renderer por defecto. E04 timing, E05 invalidación/jobs, E06
escena, E11 eventos semánticos y E14 gráficos ya cubren el ámbito. Añadir solo
anclaje por ocurrencia de palabra y estado de tiempo estimado vs medido, procedencia
de recursos y planificación de memoria. Remotion/HyperFrames/FFmpeg, mezcla,
captions y `resource_sampling.py` existen; no acreditar composición Skia preparada
por tener Python ni sustituir runtime aprobado. Revisión de still/contact strips no
prueba sonido, transiciones completas o percepción a velocidad normal.

## Fuentes y requisitos Windows

[README](https://github.com/Moh4696/cinematic-skill/blob/bf435561c6203f90f971300efe952b68b5ec3417/README.md),
[requirements](https://github.com/Moh4696/cinematic-skill/blob/bf435561c6203f90f971300efe952b68b5ec3417/requirements.txt):
skia-python>=87.6 (144.1 probado upstream), NumPy>=1.24, Pillow>=10,
SciPy>=1.10 en requirements aunque se describe opcional; FFmpeg/ffprobe externos.
No lock ni mínimo Python explícito en esos requisitos: revisar wheels Windows/ABI
antes de instalar en entorno aislado. No tocar .venv/ComfyUI. macOS say no disponible
en Windows; espeak-ng u otra voz local preparada son alternativas, no dependencias
ya comprobadas. Benchmark92s/1080p/~6min laptop16GB no predice este equipo.

[engine](https://github.com/Moh4696/cinematic-skill/blob/bf435561c6203f90f971300efe952b68b5ec3417/skills/cinematic-film/scripts/engine.py),
[split_takes](https://github.com/Moh4696/cinematic-skill/blob/bf435561c6203f90f971300efe952b68b5ec3417/skills/cinematic-film/scripts/split_takes.py),
[voz](https://github.com/Moh4696/cinematic-skill/blob/bf435561c6203f90f971300efe952b68b5ec3417/skills/cinematic-film/scripts/tts_say.py),
[render](https://github.com/Moh4696/cinematic-skill/blob/bf435561c6203f90f971300efe952b68b5ec3417/skills/cinematic-film/scripts/render.py):
doc.W(line,word) consume timing del proyecto, no prueba alineación forzada de cada
palabra por sí mismo. Estimación por texto/pausas y split de audio requieren marcar
incertidumbre y revisión; ASR/alineación preparada puede aportar reloj real. Nuevo
audio debe invalidar eventos/captions dependientes sin aprobarlos automáticamente.
Memoria consciente en renderer no acredita pico RAM de cualquier escena/parallelism
en Windows; CPU count o tabla declarada no sustituyen medición.

## Licencias/$0/offline

[MIT](https://github.com/Moh4696/cinematic-skill/blob/bf435561c6203f90f971300efe952b68b5ec3417/LICENSE)
del código, conservar aviso. Fotos/mapas/fuentes/voces mantienen derechos propios.
[fetch_commons](https://github.com/Moh4696/cinematic-skill/blob/bf435561c6203f90f971300efe952b68b5ec3417/skills/cinematic-film/scripts/fetch_commons.py)
requiere red y guarda créditos; filtro de licencia no prueba exactitud del registro,
dominio público en toda jurisdicción ni derechos de personas/marcas. No copiar
material/story del ejemplo. Sintetizar SFX por código tampoco elimina obligaciones
de bibliotecas o assets utilizados. Aquí no se creó ningún sonido.

Render puede ser local$0 con recursos/fuentes/voz preparados; investigación Commons
y get_fonts requieren red. Reutilizar ASR/TTS elegibles, sin cuotas cloud obligatorias.
No instalar scratch voice, descargar fuentes o ejecutar render para evaluar.

## Tareas con aceptación

| Prioridad | Carencia / grupo | Aceptación |
|---|---|---|
| P1 | Anclajes por palabra E04/E11 | ID/ocurrencia/span, texto/hash de narración y tiempos medidos/interpolados/estimados; palabra repetida/ausente, Unicode español, cifras/citas y cambios de voz en fixtures |
| P1 | Invalidación E05/E06 | Solo eventos/tomas/captions afectados por nueva narración; conservar revisiones y motivo; no reemplazar aprobación por retiming |
| P1 | Ledger de recursos E06/E14 | URL/revisión/autor/licencia/atribución/adquisición/hash y derivaciones; unknown bloquea reutilización de producción, no inventar créditos |
| P2 | Memoria/QA | Presupuesto por tamaño/capas/workers con errores explícitos y muestreo futuro; QA temporal/audio separado de stills y de schema |

Bloqueos: runtime/wheels/fuentes y calidad perceptual sin validar. No impiden
contratos neutros. Pausas editoriales upstream no se importan como confirmaciones
rutinarias en esta fase. Configuraciones/originales/GitHub Dark intactos.
