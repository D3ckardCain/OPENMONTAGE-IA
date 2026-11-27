# Evidencia de QA de exportaciones

`render_verification` ejecuta FFprobe y una decodificación FFmpeg completa en
salidas declaradas dentro de `renders/`. El recibo liga ruta, tamaño, SHA-256,
duración y resolución. La revisión reciente también registra FPS (avg_frame_rate,
con r_frame_rate como alternativa) y relación de aspecto calculada con SAR; si
el `render_report` declara `fps` o `aspect_ratio`, la discrepancia falla antes
del decode completo. No se modifica el archivo de salida.

Esto acredita integridad técnica declarada y decodificación, no calidad visual,
contenido correcto, mezcla inteligible, ausencia de clipping, naturalidad de voz
o sincronía labial. La inspección de frames/sonido por intervalos, zonas seguras,
overlaps de subtítulos y reparación selectiva aún requiere recibos específicos;
el estado de revisión humana sigue separado.

Las nuevas verificaciones de FPS/aspect ratio se prueban con metadatos sintéticos.
No se creó un render ni se inspeccionó ningún medio de usuario.
