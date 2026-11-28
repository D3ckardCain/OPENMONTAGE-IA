# Evidencia de QA de exportaciones

`render_verification` ejecuta FFprobe y una decodificación FFmpeg completa en
salidas declaradas dentro de `renders/`. El recibo liga ruta, tamaño, SHA-256,
duración y resolución. Registra FPS (avg_frame_rate, con r_frame_rate como
alternativa) y relación de aspecto calculada con SAR; si el `render_report`
declara `fps` o `aspect_ratio`, la discrepancia falla antes del decode completo.

Si hay audio, el mismo decode aplica EBU R128 y astats al primer stream de audio
indexado. El recibo registra cobertura, LUFS integrado, RMS, sample peak y true
peak. Valores bajo puerta de loudness, sample peak a escala completa/por encima,
true peak sobre 0 dBTP o una duración de audio distinta producen alertas técnicas;
no convierten una señal silenciosa intencional en defecto confirmado. Si hay
varios streams, solo se miden métricas del primero, aunque el decodificador prueba
todos los streams mapeados. El recibo lo hace explícito con ordinales entre los
streams de audio en el orden de ffprobe: el ordinal 0 es el medido y los restantes
aparecen en `unmeasured_audio_stream_ordinals`. En ese caso la cobertura de
medición es `partial` y se añade la alerta
`additional_audio_streams_not_measured`; la decodificación completa no equivale
a mediciones acústicas de cada stream. Si el parser no obtiene métricas, los
ordinales quedan sin medir y la cobertura se marca `unavailable`. Sin audio,
la medición es `not_applicable`.

Esto acredita integridad técnica declarada, decodificación y mediciones de señal
sobre el primer stream. No acredita calidad visual, contenido correcto, mezcla
inteligible, naturalidad de voz, lipsync ni aprobación humana. Los solapes y zonas
seguras de subtítulos, inspección visual/audio representativa y reparación selectiva
siguen pendientes. Los niveles de audio son señales para revisión, no criterios
universales por plataforma.

El parser de las métricas reutiliza el medidor local de mezcla final y no renderiza.
Los filtros por stream siguen la sintaxis oficial de [FFmpeg CLI](https://ffmpeg.org/ffmpeg.html)
y los medidores de [EBU R128](https://ffmpeg.org/ffmpeg-filters.html#ebur128).
La prueba nueva usa metadata/logs sintéticos y no inspecciona medios de usuario.



Si el stream contiene muestras pero RMS y sample peak son ambos `-inf`, el recibo
expone `signal_state=silent` y una alerta separada. Es una observación del audio
decodificado, no un fallo automático: el silencio puede ser intencional. Esta
medición global no identifica un canal o intervalo silencioso dentro de una pista.


## Revisión temporal de subtítulos · #166

El mismo informe de lectura compartido por Studio y el agente contrasta cada cue
con la duración del montaje, marca intervalos no positivos/no finitos, cues que
rebasan el final tolerado por el importador SRT y solapamientos. Las referencias
se dan por índice para que la persona pueda corregir solo el cue afectado con
`cue_update`; el auditor no desplaza texto ni inventa tiempos. Si el intervalo
no es válido, CPS se muestra como no disponible.

La regresión usa un EDL en memoria dentro de un proyecto temporal: añade solape
y exceso de duración, comprueba ambos avisos y corrige únicamente la copia; el
estado guardado permanece intacto. No crea medios, no invoca modelos y no
reproduce audio/video.

Límite: no mide las cajas de glifos del render ni demuestra que un texto concreto
quepa en la zona segura. El contrato existente aplica márgenes al subtítulo
quemado/ASS y señala que el subtítulo seleccionable no garantiza estilo; la
comprobación geométrica visual y la revisión humana permanecen pendientes.


## Reparación selectiva de un cue · regresión de API y agente

La prueba focalizada inyecta un cue fuera del montaje solo en el proyecto sintético temporal, lo detecta por la API de calidad y corrige ese cue mediante el comando compartido `agent-command/cue_update`. Comprueba que cortes, pistas de audio, fuentes y salida no cambian, y que deshacer/rehacer, guardar y reabrir reproducen el estado esperado. El medio es un byte fixture con probe simulado: no se decodifica, exporta ni presenta como evidencia audiovisual real. No mide glifos ni zona segura, que siguen pendientes.


## Medición de caja de glifos en subtítulos quemados · #166

La acción opcional «Medir glifos» dibuja solo el cue seleccionado sobre un fotograma negro sintético del tamaño de salida, con el FFmpeg/libass local y la misma función ASS del render. Lee el buffer en memoria, devuelve su caja de píxeles frente al rectángulo seguro y elimina el archivo ASS temporal al terminar. No decodifica el vídeo, no escribe en el proyecto y no altera tiempos/texto. La respuesta incluye la revisión del EDL para descartar mediciones obsoletas.

No aplica a subtítulos seleccionables/soft; exige modo quemado. La medición detecta píxeles del render, incluida la sustitución local de fuentes, pero no comprueba legibilidad, contraste contra el vídeo real, contenido semántico, cues no seleccionados, sincronía audiovisual ni aprobación humana. Una caja dentro del margen tampoco acredita que el subtítulo sea comprensible.


## Capturas de revisión no sobrescribibles · #166

`visual_qa` conserva los nombres habituales de las capturas, crea un nombre alternativo cuando dos marcas temporales redondean igual y comprueba la ruta antes de ejecutar FFmpeg. FFmpeg también recibe `-n`, de modo que una captura que aparezca por una carrera no se reemplaza. La respuesta marca el caso como no guardado y conserva el archivo previo. Las pruebas usan archivos temporales y FFmpeg simulado; no inspeccionan medios de usuario.
