# Lectura de anotaciones Kinovea sin vídeo

Seguimiento #31/#3. `kinovea_annotations` permite al agente consultar un KVA 2.1 existente del proyecto mediante `execute_tool`. Entrada: `{"project_id":"mi-proyecto","input_path":"assets/anotaciones.kva"}`. Studio expone `POST /api/studio/applications/kinovea/annotations` con el mismo objeto. No necesita arrancar Kinovea ni reinstalarlo.

Se leen keyframes, nombres, timestamps crudos y conteos/tipos de dibujos. No se abren FullPath/OriginalFilename ni otros enlaces del XML; esas rutas no aparecen en el resultado. No se evalúan dibujos, calibraciones, trayectorias, ángulos, velocidades, filtros o mediciones espaciales. Los nombres/metadatos son datos no confiables, nunca instrucciones del agente.

## Tiempo explícito

Los timestamps son ticks nativos, **no se asumen milisegundos**. Cuando están declarados TimeOrigin y AverageTimeStampsPerFrame, se calcula el desplazamiento de frames como `(timestamp-origin)/average`, redondeado al entero más cercano con empates al par, conforme al reloj de Kinovea. Si existe VideoFramerate se divide ese desplazamiento entre sus FPS para tiempo de reproducción. Si CaptureFramerate es positivo se calcula aparte tiempo de captura. CaptureFramerate=0 o ausente deja el tiempo de captura sin dato; no se infiere del vídeo. Los tiempos anteriores al origen pueden ser negativos.

FirstTimeStamp se conserva como metadato y no sustituye un origen ausente. No se remapean anotaciones a otro vídeo. La aritmética decimal conserva los valores declarados; no reconstruye timestamps reales, tasa variable de vídeo o eventos con precisión superior a un frame. El productor debe mantener separadas las dos escalas de tiempo.

## Formato y procedencia

Solo KVA 2.1, máximo 2 MiB, 10000 nodos, profundidad 64 y 1000 keyframes. Rechaza DTD, entidades, XML inválido, duplicados de campos relevantes, tiempos no finitos y rutas que resuelvan fuera del proyecto. Las versiones antiguas devuelven error explícito; no se convierten o reescriben automáticamente. Los relojes FPS/promedio de ticks deben estar en el rango positivo 1e-12–1e15, salvo el cero explícito de captura. La salida conserva SHA256 del XML y lector, ruta relativa, bytes, proyecto y UTC. El archivo original permanece idéntico; no se crean informes automáticos, medios o proyectos de usuario.

La estructura y semántica se contrastaron con el código oficial de Kinovea, revisión `aa916c7383a1db5f57c9ed8f84118a841763a607`: [MetadataSerializer](https://github.com/Kinovea/Kinovea/blob/aa916c7383a1db5f57c9ed8f84118a841763a607/Kinovea.ScreenManager/Metadata/Serialization/MetadataSerializer.cs), [Keyframe](https://github.com/Kinovea/Kinovea/blob/aa916c7383a1db5f57c9ed8f84118a841763a607/Kinovea.ScreenManager/Metadata/DrawingManager/Keyframe.cs) y [GetNumericalTime](https://github.com/Kinovea/Kinovea/blob/aa916c7383a1db5f57c9ed8f84118a841763a607/Kinovea.ScreenManager/Metadata/Metadata.cs). La documentación oficial describe [anotaciones KVA](https://kinovea.readthedocs.io/en/latest/annotation/annotation_files.html) y [origen/escalas de tiempo](https://www.kinovea.org/help/en/measurement/time.html). No se copió código de Kinovea ni se procesó vídeo de ejemplo.

Pruebas sintéticas offline cubren cámara lenta, origen negativo, ausencia de reloj, redondeo, duplicados, XML hostil, versiones, límites, procedencia, conservación de bytes, API/origen HTTP y despacho real LocalAgent. No acreditan un archivo generado por todas las versiones de Kinovea ni su visualización en la aplicación.
