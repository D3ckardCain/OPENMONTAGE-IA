# Aplicaciones registradas y documentos Krita

Seguimiento #28, #3 y #7. Node/panel #26 ya fue confirmado por el usuario y cerrado; no necesita repetirse.

El agente descubre `local_application_inventory` y `krita_document_inspect` mediante `list_tools` / `tool_info` y los ejecuta con el puente `execute_tool`, después de leer las instrucciones de la etapa. Ambas herramientas son locales y de costo cero. El inventario reutiliza el catálogo de Studio, oculta rutas personales y distingue registro/presencia de ejecución/automatización. No lanza aplicaciones ni afirma que un archivo localizado sea una integración completa.

## Lectura de documentos

`krita_document_inspect` recibe `{"project_id":"mi-proyecto","input_path":"assets/documento.kra"}`. La ruta debe resolver dentro del proyecto existente. No requiere arrancar Krita ni instalar un plugin. Usa la estructura ZIP documentada por el [manual oficial de Krita](https://docs.krita.org/en/general_concepts/file_formats/file_kra.html); la interpretación de dimensiones y capas se contrasta con el [lector/escritor oficial](https://github.com/KDE/krita/tree/master/plugins/impex/libkra). No implementa todo el formato de Krita.

Studio expone `POST /api/studio/applications/krita/inspect` con el mismo objeto. Devuelve dimensiones declaradas, espacio de color, jerarquía de capas, nombre/tipo/visibilidad/opacidad declarados y presencia de vista combinada. No decodifica esa vista ni los píxeles. El catálogo incluye `inspection_tools`, separado de herramientas de creación de escenas.

La respuesta conserva SHA256 del contenedor y maindoc.xml, bytes, ruta relativa y fecha UTC; marca datos de origen no confiables. Los nombres de capas son datos, nunca instrucciones del agente. No certifica integridad de los píxeles, apariencia, apertura en Krita ni calidad visual. No escribe informes, imágenes o documentos, ni altera configuración. Para persistir un resultado, el agente puede usar sus artefactos del proyecto siguiendo el contrato existente.

## Límites y errores

Solo `.kra`, hasta 128 MiB, 10000 entradas y 2 MiB de XML; profundidad máxima 128. Rechaza duplicados, entradas cifradas, rutas inseguras, dimensiones inválidas, entidades XML y archivos fuera del proyecto. Un DOCTYPE público ordinario no descarga su DTD. No extrae ZIP a disco, no accede a red y no ejecuta procesos. Los documentos mayores o variantes no admitidas devuelven error explícito; no se reescriben ni se reparan automáticamente.

Validación: fixtures ZIP/XML sintéticos sin píxeles reales, conservación de bytes, límites, entradas malformadas, origen HTTP y confinamiento; despacho real de LocalAgent con registro y API FastAPI. Se conserva como pendiente independiente en #7 la edición/pintura y su evaluación visual. Esta inspección funcional permite al agente conocer la estructura antes de planificar una edición futura.
