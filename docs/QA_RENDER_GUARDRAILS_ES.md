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
todos los streams mapeados.

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
