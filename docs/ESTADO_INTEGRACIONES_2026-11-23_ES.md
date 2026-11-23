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
| #26 | Node portable, npm/npx y binding API; PATH del proceso de Studio | Comprobación visual del panel bloqueada por rechazo automático de Chrome headless |
| #27 | Ollama local sin nube; preparación del Qwen GGUF existente | Sin inferencia, prueba del director ni benchmark |

Detalles y huellas en `COORDENADAS_DEPORTIVAS_ES.md`, `BIBLIOTECAS_AISLADAS_ES.md`, `ENTORNO_CLI_STUDIO_ES.md`, `OLLAMA_LOCAL_ES.md` y los issues respectivos. Las tareas de preparación #6 y #8–#16 se reconciliaron con sus evidencias existentes y se cerraron sin repetir instalaciones. #7 conserva pendiente su fase de edición/pintura. Se mantienen Blender, FreeCAD, Krita, Kinovea, OpenSCAD, Avogadro, OpenModelica y QGIS y sus rutas guardadas.

## Inventario histórico recuperado

La PR #1 usa otra rama (`feat/zero-cost-local-policy`). Sus documentos se localizaron en el commit `3a4fb6658020ea9d5be556d6c859fae1bbc2abdc`; no estaban perdidos ni pertenecen automáticamente a la rama actual. El [manifiesto adicional histórico](https://github.com/D3ckardCain/OPENMONTAGE-IA/blob/3a4fb6658020ea9d5be556d6c859fae1bbc2abdc/docs/model_download_manifest_additional.json) contiene 189 archivos y 26 grupos de modelos. Su declaración es metadatos remotos, no certificación de descargas locales ni de licencias comerciales de cada componente. El [diseño histórico de agentes](https://github.com/D3ckardCain/OPENMONTAGE-IA/blob/3a4fb6658020ea9d5be556d6c859fae1bbc2abdc/docs/AUTOMATIZACION_AGENTES.md) se conserva como referencia, sin reemplazar el contrato actual.

No se fusionan PRs, no se publican vídeos ni se activan proveedores comerciales. Las fases de inferencia, calidad, rendimiento RAM/VRAM y producción con datos reales siguen sin acreditarse y quedan fuera de esta validación sin contenido. Configuraciones privadas, entornos, ejecutables y pesos permanecen fuera de los commits.

## Pruebas de la continuación

Suite Windows: **3314 passed, 13 skipped, 3 xfailed y 58 subtests passed**, 507.72 segundos. Se usó el entorno QA separado con las dependencias de Studio visibles, Node/FFmpeg en el PATH del proceso y npm offline. Los scripts QA manuales de medios quedaron excluidos mediante opt-in; no se ejecutó contenido real. La fixture documental de FFmpeg distingue PATH, ruta guardada y archivo ausente.

El commit `01a2a72619ad0e42faeb8c2fe7b0148e2ffad33f` pasó CI remoto `45289587500` y contratos `45289587498` / `45289569242`. Los 15 bindings de aplicaciones de la API respondieron configurados y con ejecutable localizado; eso no acredita apertura ni automatización de cada aplicación en esta ejecución. No se repitieron las aperturas previamente aprobadas.
