# Centro de mando e integraciones

Estado: preparación; no se han ejecutado modelos ni aplicaciones reales en esta fase.

## Modelos

La matriz del panel incluye las 46 familias del catálogo: 21 trabajadores nativos y 25 puentes ComfyUI. Un puente no equivale a un workflow terminado. Los workflows API vinculados se muestran por separado.

Se incluyen 15 plantillas oficiales de Comfy-Org/workflow_templates, fijadas a una revisión, en tools/_comfyui/reference_templates. El manifiesto conserva origen y hash del blob. Son workflows de interfaz: requieren conversión a API y revisión de variantes antes de ejecutarse. No se vinculan automáticamente. En particular, Hunyuan 720p no demuestra compatibilidad con pesos 480p; ACE Step 1 no sustituye a ACE Step 1.5.

Antes de las pruebas reales, cada familia necesita comprobar pesos completos, nodos/dependencias, contrato de entradas, salida esperada y recursos. La presencia en el inventario no acredita instalación o compatibilidad.

## Aplicaciones

La sección Aplicaciones centraliza rutas y apertura de archivos del proyecto. FFmpeg, FFprobe, yt-dlp y Deno alimentan los flujos existentes. Avogadro, OpenModelica, SolveSpace, Blender, FreeCAD y QGIS cuentan con registro para apertura de archivos compatibles; esto no acredita que estén instalados ni que exista automatización completa de sus funciones.

Los inventarios revisados contienen instaladores de Avogadro y OpenModelica, y un ejecutable de SolveSpace. Los otros registros son opciones de integración, no descargas confirmadas. No se ejecutan instaladores automáticamente. Una aplicación de escritorio conserva su propia ventana; el panel controla su configuración y la entrega de archivos.

La ejecución usa argumentos separados, sin shell, y restringe los archivos al proyecto. Guarda registros y evita duplicar procesos iniciados por el panel. No controla procesos abiertos fuera de la app.

## Almacenamiento

La app y su configuración pueden residir en M.2. Los modelos conservan sus rutas en varios discos. Los proyectos pueden registrarse en varios destinos; el cambio de raíz activa requiere reinicio. Las entregas finales tienen destino independiente, compartido con modelos o dedicado, y se verifican al copiarlas sin borrar originales.

## Cierre pendiente

Completar workflows API específicos para las familias con puente genérico, configurar ejecutables instalados, y después realizar pruebas reales de extremo a extremo. No eliminar pesos ni herramientas por errores de configuración. Las pruebas de código con simulaciones no sustituyen las pruebas de inferencia.
