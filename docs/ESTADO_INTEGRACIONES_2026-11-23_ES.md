# Estado de preparación local — 23 de noviembre de 2026

Seguimiento del inventario #3 en `feat/local-agent-research-foundation`. Preparación, apertura y automatización son resultados diferentes. Se conserva el inventario histórico; ninguna comprobación de imports acredita producción completa.

| Seguimiento | Resultado de esta fase | Límite |
|---|---|---|
| #19 | Coordenadas deportivas conectadas al registro de herramientas y agente; Kloppy/MPLSoccer reales en entorno aislado; procedencia y pruebas sintéticas | Sin partidos, gráficos ni análisis real |
| #21 | Socceraction: esquema SPADL, orientación e inversa sintéticos | Sin valoración de partidos ni entrenamiento |
| #22 | cq_warehouse/CadQuery: imports, tablas y cálculo numérico | Sin sólidos ni fabricación |
| #23 | SoccerTacticalVision: imports CPU y homografía sintética | Sin imágenes, detección ni tracking |
| #24 | MuseTalk: clases e imports MMLab y operadores nativos CPU | Sin cargar pesos, CUDA, audio ni avatar |
| #25 | TVCalib: Python 3.9 aislado, imports y tensores sintéticos | Sin calibración de vídeo ni mapas |
| #26 | Node portable, npm/npx y binding API; PATH del proceso de Studio; panel confirmado por el usuario y issue cerrado | No acredita render de los compositores |
| #27 | Ollama local sin nube; preparación del Qwen GGUF existente | Sin inferencia, prueba del director ni benchmark |

Detalles y huellas en `COORDENADAS_DEPORTIVAS_ES.md`, `BIBLIOTECAS_AISLADAS_ES.md`, `ENTORNO_CLI_STUDIO_ES.md`, `OLLAMA_LOCAL_ES.md` y los issues respectivos. Las tareas de preparación #6 y #8–#16 se reconciliaron con sus evidencias existentes y se cerraron sin repetir instalaciones. #7 conserva pendiente su fase de edición/pintura. Se mantienen Blender, FreeCAD, Krita, Kinovea, OpenSCAD, Avogadro, OpenModelica y QGIS y sus rutas guardadas.

## Inventario histórico recuperado

La PR #1 usa otra rama (`feat/zero-cost-local-policy`). Sus documentos se localizaron en el commit `3a4fb6658020ea9d5be556d6c859fae1bbc2abdc`; no estaban perdidos ni pertenecen automáticamente a la rama actual. El [manifiesto adicional histórico](https://github.com/D3ckardCain/OPENMONTAGE-IA/blob/3a4fb6658020ea9d5be556d6c859fae1bbc2abdc/docs/model_download_manifest_additional.json) contiene 189 archivos y 26 grupos de modelos. Su declaración es metadatos remotos, no certificación de descargas locales ni de licencias comerciales de cada componente. El [diseño histórico de agentes](https://github.com/D3ckardCain/OPENMONTAGE-IA/blob/3a4fb6658020ea9d5be556d6c859fae1bbc2abdc/docs/AUTOMATIZACION_AGENTES.md) se conserva como referencia, sin reemplazar el contrato actual.

No se fusionan PRs, no se publican vídeos ni se activan proveedores comerciales. Las fases de inferencia de producción, calidad creativa, rendimiento sostenido RAM/VRAM y producción con datos reales siguen sin acreditarse. La prueba sintética de herramientas descrita abajo tiene un alcance separado. Configuraciones privadas, entornos, ejecutables y pesos permanecen fuera de los commits.

## Continuación funcional

| Seguimiento | Conexión validada | Alcance pendiente |
|---|---|---|
| #28 | Inventario al agente e inspección KRA por API/execute_tool | Pintura, edición y apariencia en #7 |
| #29 | PyQGIS real: WGS84/Web Mercator, API/execute_tool, perfil aislado | Capas, mapas, exactitud topográfica y render |
| #30 | FreeCAD.Units real: parámetros y unidades por API/execute_tool | Modelado, fabricación y geometría |
| #31 | Lectura KVA2.1 y tiempos declarados, API/execute_tool | Vídeo real, tracking y mediciones espaciales |
| #32 | Qwen3 local solicita una llamada y el puente ejecuta una conversión nativa | Director multietapa, catálogo/contexto completo y calidad |
| #33 | Consulta HTTP de herramientas por nombre/capacidad antes de sondear estados | La carga inicial de módulos sigue existiendo |

Los paquetes y aperturas ya preparados en #8–#16 no se repiten. Las bibliotecas #21–#25 conservan sus diagnósticos y limitaciones documentados; imports de MuseTalk o TVCalib no acreditan inferencia de medios. La preparación de conectores y estas operaciones de lectura/cálculo no completan la automatización integral del inventario #3. Los resultados de producción, pintura, audio, vídeo, mapas y geometría requieren su fase de validación correspondiente; no se ejecutaron dentro de esta continuación.

## Pruebas de la continuación

Suite Windows: **3314 passed, 13 skipped, 3 xfailed y 58 subtests passed**, 507.72 segundos. Se usó el entorno QA separado con las dependencias de Studio visibles, Node/FFmpeg en el PATH del proceso y npm offline. Los scripts QA manuales de medios quedaron excluidos mediante opt-in; no se ejecutó contenido real. La fixture documental de FFmpeg distingue PATH, ruta guardada y archivo ausente.

El commit `01a2a72619ad0e42faeb8c2fe7b0148e2ffad33f` pasó CI remoto `45289587500` y contratos `45289587498` / `45289569242`. Los 15 bindings de aplicaciones de la API respondieron configurados y con ejecutable localizado; eso no acredita apertura ni automatización de cada aplicación en esta ejecución. No se repitieron las aperturas previamente aprobadas.
