# Coordenadas QGIS sin mapas

Seguimiento #29/#3/#20. Se reutiliza el QGIS OSGeo4W registrado y su Python, sin cambiar `.venv`, ComfyUI ni el PATH global. No requiere reinstalar ni volver a abrir la aplicación.

El agente descubre `qgis_coordinates` y la ejecuta con `execute_tool` tras leer las instrucciones de la etapa. Entrada: `{"project_id":"mi-proyecto","source_crs":"EPSG:4326","target_crs":"EPSG:3857","points":[[0,0],[12.5,45]]}`. Studio expone `POST /api/studio/applications/qgis/transform` con el mismo objeto; la operación corre fuera del bucle HTTP. El catálogo informa `numeric_tools`, separado de apertura y generación de escenas.

PyQGIS usa `QgsCoordinateTransform`, `QgsCoordinateTransformContext` y puntos XY siguiendo la [API oficial](https://api.qgis.org/api/classQgsCoordinateTransform.html). Se desactivan las transformaciones aproximadas de sustitución y se rechazan resultados no finitos. Solo se admite EPSG:4326 ↔ EPSG:3857, con orden longitud/latitud para 4326 y metros este/norte para 3857. No se admite un CRS arbitrario, 3D, alturas, épocas ni rejillas remotas. La comprobación inversa mide consistencia numérica, no exactitud topográfica.

Límites: 1–1000 puntos finitos, petición serializada hasta 65536 bytes, latitud hasta ±85.0511287798066°, longitud hasta ±180° y Web Mercator hasta ±20037508.342789244 m por eje. No recorta puntos fuera de dominio. Web Mercator no proporciona distancias de terreno sin distorsión.

El worker usa perfil/auth/cache temporales, Qt offscreen, PROJ_NETWORK=OFF y red Qt desactivada. No carga proyectos, capas, plugins Python, imágenes ni modelos, ni ejecuta scripts de usuario. El entorno de arranque se construye con `lib/qgis_runtime.py`; solo el proceso hijo recibe sus variables. Tiempo máximo 60 segundos; salida JSON acotada. Errores de instalación, entrada, proceso y timeout se devuelven estructurados.

La respuesta incluye versión real QGIS, unidades, puntos, error de ida/vuelta y procedencia SHA256 de entrada canónica y worker, proyecto y fecha UTC. Los CRS y puntos son declaraciones de origen, no geolocalizaciones verificadas. No se escribe contenido ni informe automático; el agente puede persistir la respuesta en sus artefactos conforme al contrato habitual.

Pruebas sintéticas validan proceso aislado, límites, fallos, origen HTTP y despacho real del agente. `OPENMONTAGE_QGIS_NATIVE_QA=1` activa además pruebas numéricas con la instalación real, contrastadas con la fórmula independiente de Mercator. Esa prueba no crea capas ni mapas. En CI sin OSGeo4W queda omitida y se ejecutan los contratos sintéticos.
