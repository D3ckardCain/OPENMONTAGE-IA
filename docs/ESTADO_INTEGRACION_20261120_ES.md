# Estado de integración — 20 de noviembre de 2026

Este documento describe código preparado y pruebas de software. No certifica que todos los modelos descargados estén completos o funcionen en los equipos físicos.

## Implementado

| Área | Estado del código | Límite actual |
| --- | --- | --- |
| Investigación de canales | API de YouTube, filtros de canales y muestras recientes, paso al estudio con encargo editable | La muestra no demuestra crecimiento, ingresos o monetización |
| Producción | Productor local guiado por pipelines, checkpoints y herramientas | Necesita un modelo local compatible y comprobaciones con los motores reales |
| Cola | Persistencia, ejecución secuencial, prioridades, retirada, lotes y comprobación previa | Se pausa ante bloqueos y aprobaciones; no reinicia generación al abrir la app |
| Modelos | 47 familias, 32 motores nativos y 15 rutas ComfyUI con recetas de preparación | Una receta no certifica dependencias, variante ni inferencia |
| Varios discos | Raíces de recursos, una raíz de proyectos activa por sesión, destino final opcional | Cambiar la raíz activa requiere reiniciar; no mueve archivos |
| Inventarios | Estados por ruta/tamaño, candidatos en otras ubicaciones, temporales y planes revisables por carpeta | Los inventarios son fotografías; no equivalen a inspección física actual |
| Versiones por idioma | Proyectos independientes, consulta de estado, selección para cola y exclusión del idioma original confirmado | Crear versiones no traduce ni produce videos por sí solo |
| Referencias | Análisis local, instantáneas compartidas y reutilización en el productor | Los informes parciales conservan sus lagunas; no verifican hechos externos |
| Traducción | MADLAD local, fragmentación sin pérdida del origen, checkpoints, recuperación y panel de proyecto | Calidad, contexto entre fragmentos y adaptación cultural requieren revisión |
| Voces | Correspondencias de idioma y consulta de voces locales Kokoro, detección de descargas fallidas | No certifica pronunciación, identidad del peso ni calidad |
| Exportaciones | Verificación técnica, copia al destino final, recuperación de entrega y catálogo | La verificación técnica no acredita contenido, derechos o calidad visual |
| Aplicaciones externas | Catálogo, configuración y apertura de archivos en aplicaciones registradas | Abrir un programa no automatiza todas sus funciones internas |

## Comprobaciones efectuadas

En esta revisión pasaron 194 pruebas conjuntas de cola, versiones, referencias, traducción, modelos, inventarios, preparación y entregas. Además pasó una prueba de integración que utiliza HTTP y proyectos reales temporales con respuestas de chat simuladas: crea versiones, comparte análisis, añade el lote a la cola y verifica que un bloqueo del primer productor conserve el segundo pendiente. No llama a servidores de modelos ni produce medios.

GitHub Actions conserva las comprobaciones de contratos en Windows y Linux y las pruebas de navegador con respuestas sintéticas. Cada cambio tiene su propio resultado; no debe extrapolarse una ejecución verde anterior a un commit aún pendiente.

## Pendiente antes de afirmar funcionamiento completo

1. Validar los pesos y entornos reales, por familia y variante, sin interrumpir generaciones existentes. Corregir o retirar los adaptadores que fallen después de esas pruebas.
2. Comprobar el circuito de producción con medios reales: referencia, investigación, guion, voces, música, subtítulos, escenas, montaje y entrega. Medir RAM, VRAM, tiempo y calidad en el PC final.
3. Completar y validar la automatización interna de las aplicaciones externas donde todavía solo existe apertura controlada.
4. Validar localización cultural y música con casos reales; las instrucciones del encargo no son un detector automático certificado.
5. Continuar los conectores oficiales de estadísticas de fútbol; no se considera completa la cobertura de todas las competiciones, jugadores y entrenadores.
6. Desarrollar y probar publicación/programación por red como módulo separado. Iniciar producción no autoriza publicar.
7. Preparar la guía final del usuario sobre el comportamiento ya comprobado en el equipo final.

El desarrollo mantiene el objetivo de operación local sin servicios de pago. Los informes de preparación no descargan ni instalan pesos por sí solos.
