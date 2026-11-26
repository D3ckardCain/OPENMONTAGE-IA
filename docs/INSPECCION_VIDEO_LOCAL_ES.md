# Evidencia de vídeo con presupuesto — #122

`frame_sampler`0.2.0 añade `strategy=evidence` al motor existente. No instala
/watch, otro ASR ni un proveedor cloud. Reutiliza FFmpeg/FFprobe guardados y Pillow.

Entradas: archivo local, `output_dir`, `start_seconds`, `end_seconds`, `max_frames`
(1–12, por defecto4), `thumbnail_width`128–640, SHA256 de fuente opcional y
`stored_transcript` opcional del conjunto guardado del editor. Intervalo máximo120s.

La consulta elige objetivos uniformes sobre PTS decodificados por FFprobe,
no etiqueta una imagen con el tiempo solicitado sin comprobarlo. FFmpeg showinfo
verifica el PTS de las imágenes extraídas. El informe conserva racionales,
reloj de presentación de fuente, intervalo, presupuesto y método. Hoja de contacto
local con tiempos; no se envía vídeo/imágenes a Gemini ni se inicia visión/ASR.

Caché por contenido+intervalo+parámetros+identidad del ejecutable+versión del
contrato. La huella de fuente se reutiliza solo con ruta y dev/inodo/tamaño/mtime/
ctime iguales. Recibo e imágenes verificadas; cambios fallan sin sobrescribir
evidencia ajena. Una consulta repetida válida no vuelve a FFprobe/FFmpeg ni relee
el vídeo para hash. La transcripción se filtra al intervalo y exige la misma
huella de fuente; no se inventa alineación ni se altera el ASR guardado.

Validación real autorizada en el vídeo portugués existente: intervalo9.5–11.5s,
presupuesto3, ancho320px. PTS9.875/10.5/11.167s y6palabras guardadas reutilizadas.
Hoja inspeccionada; segunda consulta reutilizó caché con `_run` bloqueado, por lo
que no podía decodificar de nuevo. Nueve pruebas nuevas focalizadas aprobadas.
Sin render de vídeo, síntesis, nueva transcripción o descarga de modelos.

Cobertura **parcial**: imágenes muestreadas y transcripción declarada. No equivale
a observar cada fotograma, escuchar el audio, detectar todos los cortes, medir
sincronía, validar hechos o juzgar naturalidad. Los tiempos se expresan como PTS
originales; fuentes con offsets/ediciones exóticas requieren revisión específica.
No se adopta un extractor por escena ni dedup agresivo que oculte cambios sutiles.

Agente: pedir primero índice/JSON y solo la hoja o fotogramas necesarios; aumentar
el presupuesto únicamente ante una pregunta concreta. Los resultados devuelven
rutas, no cargas automáticas al modelo. Otra pregunta/rango tiene su propia clave.
Planificación desde referencias debe citar este recibo y declarar sus huecos.
