# QGIS en Studio

QGIS se registra mediante Aplicaciones, con entrega de proyectos `.qgs` y `.qgz`.
La edición Windows LTR de OSGeo4W utiliza `bin/qgis-ltr-bin.exe`; la variante
regular Qt5 utiliza `bin/qgis-bin.exe`. Studio conserva la validación de nombres
y rechaza instaladores y scripts batch arbitrarios.

## Entorno de arranque

`lib/qgis_runtime.py` prepara exclusivamente el entorno del proceso hijo Windows.
Comprueba recursos de QGIS, Qt5, Python, GDAL y PROJ antes de abrirlo. Establece
PATH y las variables de bibliotecas, plugins y datos según la estructura oficial
de OSGeo4W, sin modificar el entorno del servidor, PATH global o Python de otros
programas. Descarta variables heredadas de Python, Qt, QGIS, GDAL, PROJ, OSGeo4W,
Conda y entornos virtuales. Python de QGIS permanece dentro de su distribución.

La apertura usa un perfil `openmontage` en `.backlot/studio/qgis`, separado del
perfil habitual del usuario, y las opciones `--noplugins` y `--noversioncheck`.
PROJ_NETWORK=OFF evita descargas automáticas de rejillas. No constituye un bloqueo
general de red. La entrega de archivos conserva los límites del proyecto y pasa
argumentos directamente, con `shell=False`, sin invocar batch ni consolas.

La configuración del ejecutable se guarda con `POST /api/studio/applications/qgis`.
`GET /api/studio/applications` informa la ruta y si el archivo existe. La apertura
se realiza con `POST /api/studio/applications/qgis/launch`, indicando `project_id`
y, opcionalmente, `file`. El resultado `launched_not_verified` acredita la creación
del proceso; hay que comprobar su ventana y registros para confirmar el arranque.

## Preparación y validación de esta entrega

Se buscó primero una instalación o paquete existente en las carpetas disponibles
de aplicaciones, descargas, herramientas y bibliotecas geográficas y en el registro
de instalaciones de Windows. No se encontró QGIS. Se obtuvo el MSI oficial LTR
`QGIS-OSGeo4W-3.44.15-2.msi`, 580468736 bytes, y se contrastó con el manifiesto
oficial `.sha256sum`: `81f7933bda110fa683a5f8f8129bc9b2ad2b814e65e99916c0d657af9518399c`.
Se conservó el MSI y se extrajo una imagen administrativa en una carpeta nueva,
sin instalación global, asociaciones de archivos ni cambios de PATH global.

El diagnóstico real `--version` devolvió QGIS 3.44.15-Solothurn, build 44b4ef05178.
La carga de PyQGIS mediante su propio Python 3.12.15 comprobó Qt 5.15.13,
GDAL 3.13.3, PROJ 9.8 y registro de proveedores, sin crear capas ni mapas.
Las pruebas de código usan una estructura OSGeo4W sintética y procesos simulados.
Cubren aislamiento, conservación de configuraciones, recursos ausentes, nombres,
rutas de proyecto, perfiles y argumentos de apertura.

Validación local de Studio: API con `configured=true` y `file_found=true`, panel
«QGIS · Ejecutable localizado» y apertura mediante su endpoint de aplicaciones.
El proceso abrió la ventana «Proyecto sin título — QGIS», con handle de ventana
y estado Responding=true; el registro de arranque quedó vacío, sin errores.
El servidor se reinició después de comprobar que no había trabajos activos ni
pendientes. Las configuraciones previas se compararon antes y después.

## Alcance y límites

QGIS es software GPL; se conservan las licencias incluidas y las de sus componentes.
La distribución comprobada es Windows x64 Qt5 LTR. El adaptador de entorno Windows
rechaza estructuras incompletas y no declara soporte para Qt6 ni paquetes distintos
de OSGeo4W. GRASS, SAGA, plugins externos, render y algoritmos geográficos requieren
comprobaciones posteriores. No se genera contenido en esta fase.

El programa puede trabajar con datos locales offline. Servicios WMS/WFS/XYZ,
repositorios de plugins y otras fuentes remotas necesitan conexión y pueden tener
licencias, claves o condiciones propias. Su presencia como proveedor no acredita
acceso gratuito ni una consulta satisfactoria. No se usan servicios de pago.
El MSI estándar excluye algunas rejillas opcionales de transformación; las
operaciones que las necesiten requieren obtenerlas y verificarlas por separado.
Abrir QGIS no acredita automatización cartográfica ni precisión geográfica.

Fuentes oficiales: [instalación y requisitos de distribución](https://qgis.org/resources/installation-guide/),
[checksum del MSI](https://download.qgis.org/downloads/QGIS-OSGeo4W-3.44.15-2.sha256sum),
[perfiles y opciones de arranque 3.44](https://docs.qgis.org/3.44/en/docs/user_manual/introduction/qgis_configuration.html).
