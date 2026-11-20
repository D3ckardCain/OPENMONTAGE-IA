# Centro de mando e integraciones

Estado: preparación; no se han ejecutado modelos ni aplicaciones reales en esta fase.

## Modelos

La matriz del panel incluye las 46 familias del catálogo: 31 motores nativos y 15 rutas ComfyUI. Todas las familias tienen receta de preparación; esto no acredita instalación ni inferencia. Los workflows API vinculados y las recetas todavía sin configurar se muestran por separado.

Se incluyen 20 plantillas de Comfy-Org y de los autores de sus integraciones, fijadas a una revisión, en tools/_comfyui/reference_templates. El manifiesto conserva origen y hash del blob. El botón «Preparar workflow sin generar» convierte el lienzo a API consultando únicamente /object_info. Expande subgrafos, conserva entradas expuestas, resuelve reroutes/bypasses inequívocos y elimina ramas ajenas a la salida elegida. Rechaza servicios externos, nodos ausentes, widgets ambiguos y parámetros sin binding. Guarda el grafo y sus bindings para el agente; nunca llama /prompt. Las plantillas siguen requiriendo revisar sus variantes frente a los pesos instalados. En particular, Hunyuan 720p no demuestra compatibilidad con pesos 480p; ACE Step 1 no sustituye a ACE Step 1.5.

Antes de las pruebas reales, cada familia necesita comprobar pesos completos, nodos/dependencias, contrato de entradas, salida esperada y recursos. La presencia en el inventario no acredita instalación o compatibilidad.

## Aplicaciones

La sección Aplicaciones centraliza rutas y apertura de archivos del proyecto. FFmpeg, FFprobe, yt-dlp y Deno alimentan los flujos existentes. Avogadro, OpenModelica, SolveSpace, Blender, FreeCAD y QGIS cuentan con registro para apertura de archivos compatibles; esto no acredita que estén instalados ni que exista automatización completa de sus funciones.

Los inventarios revisados contienen instaladores de Avogadro y OpenModelica, y un ejecutable de SolveSpace. Los otros registros son opciones de integración, no descargas confirmadas. No se ejecutan instaladores automáticamente. Una aplicación de escritorio conserva su propia ventana; el panel controla su configuración y la entrega de archivos.

La ejecución usa argumentos separados, sin shell, y restringe los archivos al proyecto. Guarda registros y evita duplicar procesos iniciados por el panel. No controla procesos abiertos fuera de la app.

## Almacenamiento

La app y su configuración pueden residir en M.2. Los modelos conservan sus rutas en varios discos. Los proyectos pueden registrarse en varios destinos; el cambio de raíz activa requiere reinicio. Las entregas finales tienen destino independiente, compartido con modelos o dedicado, y se verifican al copiarlas sin borrar originales.

## Cierre pendiente

Configurar las rutas reales de pesos, código, dependencias y ejecutables instalados; preparar los grafos contra la versión de ComfyUI instalada; después realizar pruebas reales de extremo a extremo. No quedan familias sin receta de preparación, pero todavía no se ha validado ninguna nueva inferencia. No eliminar pesos ni herramientas por errores de configuración. Las pruebas de código con simulaciones no sustituyen las pruebas de inferencia.

## Motores originales y pesos descargados

CogVideoX usa Diffusers local; DWPose usa sus dos ONNX y rutinas originales; LaMa requiere extraer el ZIP (config.yaml y models/best.ckpt). LongCat, LongCat Avatar y MagiHuman tienen adaptadores para sus motores originales; los tres necesitan un runtime Linux/WSL con CUDA preparado. No se transforman pesos originales en una variante ComfyUI distinta sin avisar.

Wan Camera y Wan Control adaptan exclusivamente los parámetros del ejemplo original VideoX-Fun. Wan S2V utiliza su CLI original. FramePack carga los checkpoints locales y ejecuta únicamente la función de trabajo original, sin abrir Gradio. Las revisiones de estos cuatro códigos se fijan y verifican mediante docs/runtime_sources.json; una revisión diferente debe adaptarse antes de usarla. No se descarga su código automáticamente.

FramePack necesita runtime_config con backbone_dir y vision_dir absolutos (repositorios auxiliares completos). MagiHuman necesita runtime_config con engine_config y evaluation_config, con todas sus rutas de pesos/config locales. El panel permite configurar ambos. Los motores conservan registros de proceso en el proyecto.

## Agentes y aplicaciones

application_catalog permite al agente consultar las diez herramientas registradas. application_open_project_file abre un archivo existente del proyecto con una de las seis aplicaciones de escritorio configuradas. Devuelve el proceso iniciado, nunca afirma que abrirlo equivalga a haber renderizado o terminado el trabajo. La automatización completa de las funciones internas de esas seis aplicaciones no está implementada por este mecanismo de apertura.

## Comprobaciones de esta fase

Se ejecutan pruebas de contratos con datos sintéticos y procesos simulados. No se lanzan los motores originales, no se cargan pesos, no se interrumpe ComfyUI y no se realizan descargas de modelos.

## Preparación del equipo desde el panel

La sección «Preparación del equipo» reúne un informe de las 46 familias, candidatos de carpetas de pesos, imports requeridos y sugerencias de entornos separados dentro de .runtimes en el disco de la app. Es un plan: no crea entornos ni acredita versiones instaladas. El informe se puede guardar y regenerar cuando cambien los discos.

La búsqueda de herramientas examina hasta 20 000 entradas y seis niveles en las carpetas elegidas. Omite pesos, bibliotecas voluminosas, enlaces y dependencias de programas. Puede ser parcial y lo indica; no es un inventario completo del disco. No inicia archivos. Los nombres coincidentes se presentan como candidatos y cada ruta se vincula mediante un botón explícito. No reemplaza configuraciones automáticamente ni usa instaladores como ejecutables.

FramePack y MagiHuman tienen formularios para sus pesos auxiliares. El formulario MagiHuman prepara distill, una GPU y Turbo VAE con los parámetros del ejemplo original; todavía necesita un motor Linux/WSL con CUDA. Los formularios crean JSON locales y vinculan runtime_config; no copian modelos ni prueban inferencia. Los cambios se bloquean mientras haya una producción o análisis local activo.

El agente puede consultar local_setup_report para conocer requisitos de configuración sin sondear dependencias, ejecutar aplicaciones o cargar modelos.

El diagnóstico principal reconoce FFmpeg mediante la ruta configurada aunque no esté en PATH. La presencia del archivo tampoco prueba su versión o funcionamiento.

## Verificación de exportaciones

Al finalizar, el productor usa las rutas configuradas de FFprobe y FFmpeg (con detección portable como alternativa cuando no hay ruta explícita). Comprueba que el render esté dentro del proyecto, tenga duración finita y positiva, dimensiones válidas, metadatos declarados compatibles y pistas de audio cuando se hayan declarado. Después intenta decodificar todo el video y su audio, sin reexportarlo, y calcula SHA-256. El informe render_verification.json conserva el resultado, incluso si falla.

Antes de copiar al destino final se compara la huella con la del archivo verificado. Si el render cambió, se bloquea la entrega; los originales se conservan. La revisión es técnica: no certifica calidad visual, derechos ni exactitud de la narración. La decodificación consume CPU y lectura de disco y puede tardar en videos grandes; no carga modelos IA ni publica contenido.
