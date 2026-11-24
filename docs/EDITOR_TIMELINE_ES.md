# Timeline manual: primera entrega del encargo 7141865417

## Distribución y encuadre

La biblioteca parte de 320 px, con miniaturas contenidas y nombres en una línea
con tooltip. El editor migra únicamente sus dimensiones antiguas inválidas:
bibliotecas demasiado estrechas/anchas y alturas que comprimían las pistas.
No borra otras preferencias. **Distribución → Restablecer distribución** restaura
los tamaños y muestra los paneles laterales sin modificar ningún proyecto.
El alto mínimo útil de pistas aumenta según la ventana. Los parámetros extensos
de clip/subtítulos están en el inspector contextual; las acciones directas
permanecen bajo las pistas, que no se encogen al desplegar formularios.

**Ajustar al montaje** (`F`) calcula la escala usando el final del vídeo, audio
y subtítulos, sin el antiguo techo de160px/s. La primera apertura se ajusta al
contenido. `+`/`−` acercan/alejan y el deslizador sigue disponible. La regla cambia
sus intervalos con el zoom y crea solo las marcas visibles. Cursor, modo de zoom
y escala se recuerdan por proyecto en el navegador, separados del EDL.
Una cola de audio que exceda el vídeo se muestra y se advierte explícitamente:
el compositor actual termina la salida con el vídeo; Ajustar no cambia esa regla.

## Cursor y operaciones existentes

Arrastra la regla para mover el cursor. Con la regla enfocada, flechas avanzan
un fotograma; Mayús+flechas, un segundo; Inicio/Fin van a los extremos.
Si existe un montaje guardado vigente, el cursor busca en ese vídeo. Sin él,
el cursor sigue siendo editable, pero no se simula una vista compuesta.

Seleccionar un clip mantiene el monitor del montaje. **Ver fuente del clip**
es una acción explícita del inspector; **Ver montaje guardado** vuelve al render
existente sin generar otro. **Dividir en cursor** (`S`) convierte el tiempo del
montaje a tiempo de fuente, incluyendo posición y velocidad. Exige una división
interior con al menos un fotograma a cada lado; usa el comando compartido `split`,
con revisión, procedencia, guardado atómico y deshacer/rehacer existentes.
El recorte por números, división por tiempo de fuente, mover/reordenar, quitar,
ganancia, fades, velocidad, SRT y estilos conservan sus operaciones previas.

## Validación y siguientes entregas

Pruebas Node sin dependencias sobre el código de tiempo real: montaje3.5s,
colas independientes, dos horas, vacío, velocidades y bordes de división.
Pruebas de navegador con JSON interceptado: preferencias previas, restablecimiento,
escalas corta/larga, selección sin cambiar de monitor, cursor por teclado,
división revisionada y deshacer. Son evidencia de navegador en CI, no de la
pestaña Windows ni de reproducción real. Se conservan los medios existentes.

Pendientes del encargo: selección múltiple/operaciones atómicas, recorte por
bordes y snapping, duplicación, marcadores, borrado con/sin cierre de hueco,
transformaciones/títulos/transiciones, capas reales, waveforms por pista,
solo/bloqueo, medidores/mezcla, presets editables y cancelación de exportación.
No se añaden botones para esas capacidades antes de implementarlas. La escucha,
sincronía y observación de la ventana local se registran separadamente de API,
FFprobe y CI. No requiere inferencias, nuevas dependencias ni reiniciar Studio.
