# Centro de mando e integraciones

Estado: preparación; no se han ejecutado modelos ni aplicaciones reales en esta fase.

## Modelos

La matriz del panel incluye las 47 familias del catálogo: 32 motores nativos y 15 rutas ComfyUI. Todas las familias tienen receta de preparación; esto no acredita instalación ni inferencia. Los workflows API vinculados y las recetas todavía sin configurar se muestran por separado.

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

La sección «Preparación del equipo» reúne un informe de las 47 familias, candidatos de carpetas de pesos, imports requeridos y sugerencias de entornos separados dentro de .runtimes en el disco de la app. Es un plan: no crea entornos ni acredita versiones instaladas. El informe se puede guardar y regenerar cuando cambien los discos.

La búsqueda de herramientas examina hasta 20 000 entradas y seis niveles en las carpetas elegidas. Omite pesos, bibliotecas voluminosas, enlaces y dependencias de programas. Puede ser parcial y lo indica; no es un inventario completo del disco. No inicia archivos. Los nombres coincidentes se presentan como candidatos y cada ruta se vincula mediante un botón explícito. No reemplaza configuraciones automáticamente ni usa instaladores como ejecutables.

FramePack y MagiHuman tienen formularios para sus pesos auxiliares. El formulario MagiHuman prepara distill, una GPU y Turbo VAE con los parámetros del ejemplo original; todavía necesita un motor Linux/WSL con CUDA. Los formularios crean JSON locales y vinculan runtime_config; no copian modelos ni prueban inferencia. Los cambios se bloquean mientras haya una producción o análisis local activo.

El agente puede consultar local_setup_report para conocer requisitos de configuración sin sondear dependencias, ejecutar aplicaciones o cargar modelos.

El diagnóstico principal reconoce FFmpeg mediante la ruta configurada aunque no esté en PATH. La presencia del archivo tampoco prueba su versión o funcionamiento.

## Verificación de exportaciones

Al finalizar, el productor usa las rutas configuradas de FFprobe y FFmpeg (con detección portable como alternativa cuando no hay ruta explícita). Comprueba que el render esté dentro del proyecto, tenga duración finita y positiva, dimensiones válidas, metadatos declarados compatibles y pistas de audio cuando se hayan declarado. Después intenta decodificar todo el video y su audio, sin reexportarlo, y calcula SHA-256. El informe render_verification.json conserva el resultado, incluso si falla.

Antes de copiar al destino final se compara la huella con la del archivo verificado. Si el render cambió, se bloquea la entrega; los originales se conservan. La revisión es técnica: no certifica calidad visual, derechos ni exactitud de la narración. La decodificación consume CPU y lectura de disco y puede tardar en videos grandes; no carga modelos IA ni publica contenido.

## Recuperar una entrega sin regenerar

El botón «Reintentar entrega verificada» recupera únicamente la copia al destino final. Requiere las etapas de producción completas, el informe técnico aprobado y una huella de las declaraciones de render sin cambios. Después vuelve a comprobar SHA-256 antes de copiar. Si cambió el informe o el video, exige verificar de nuevo; no vuelve a renderizar automáticamente.

La copia se ejecuta fuera del hilo de atención HTTP. Durante ella se excluyen otras tareas locales y cambios de configuración. Puede tardar con archivos grandes. delivery_retry.json conserva el resultado del intento; los originales y las copias finales anteriores se conservan. Completar la entrega no publica el video.

## Catálogo de videos finales

La sección «Videos finales» consulta recibos de entrega y verificaciones guardadas de hasta 500 proyectos del disco de trabajo activo. Muestra la ruta final, su disponibilidad actual y permite abrir el proyecto. Un error de lectura en un proyecto no oculta los demás. Indica listas parciales. No recorre los discos de recursos, copia archivos ni carga modelos. La disponibilidad no equivale a una nueva comprobación de SHA-256 o calidad. Para proyectos de otro disco hay que seleccionar su raíz y reiniciar.

Si falta la raíz de proyectos, el catálogo muestra «disco no disponible» en vez de presentar el resultado como una colección vacía. Las pruebas de interfaz incluyen entregas disponibles, ausentes, listas parciales y recibos ilegibles con datos simulados.

## Inventarios y tamaños desconocidos

El catálogo distingue ruta y tamaño coincidentes, ruta registrada con tamaño de catálogo desconocido, tamaño distinto y archivo no registrado. Muestra las coincidencias de ambos inventarios con disco, ruta, tamaño observado y fecha. Una ruta registrada con tamaño desconocido o diferente requiere revisar el archivo; no se presenta como ausente ni ofrece una descarga directa. Ninguna coincidencia confirma integridad o instalación.

Cuando no coincide la ruta esperada pero sí el nombre y un tamaño conocido y positivo, se muestran hasta veinte ubicaciones candidatas de los inventarios y el total encontrado. Se retiene la descarga directa hasta revisar la identidad. No se compara por nombre solo cuando el tamaño del catálogo es desconocido; nombres genéricos como `model.safetensors` no bastan. No se mueven archivos, se calculan hashes ni se considera que el modelo esté instalado.

## Lista revisable para FDM

«Preparar lista de descargas pendientes» requiere al menos dos inventarios con series distintas. Agrupa únicamente archivos no registrados, separa la carpeta de destino de los enlaces completos y avisa de nombres repetidos entre carpetas. Excluye registros coincidentes, tamaños desconocidos con ruta registrada y candidatos en otras ubicaciones. No inicia descargas ni importa datos en FDM. Revisa los discos y las fechas mostrados, así como las descargas posteriores del chat: ausencia en inventarios no prueba ausencia actual. Los enlaces se presentan en cuadros de texto para copiar por carpeta; no se genera un archivo `.fdd`.

## Inventarios para el productor

`model_catalog` devuelve en su resumen los recuentos de todos los estados de inventario, incluidos tamaño desconocido y candidatos en otras ubicaciones. `model_download_plan` exige un grupo concreto y devuelve solamente su lista revisable, usando al menos dos inventarios. Ninguna de estas herramientas inicia descargas ni considera que un archivo no registrado esté necesariamente ausente.

## Copias del mismo modelo en varios discos

La detección automática prefiere una copia con los archivos esperados presentes y no vacíos frente a otra incompleta de la misma carpeta de variante. Comprueba también los fragmentos declarados en índices de pesos. No compara contenido ni garantiza integridad o compatibilidad. No cambia entre variantes distintas y nunca sustituye una ruta `model_dir` configurada explícitamente. La preparación del equipo muestra archivos ausentes por candidato. No mueve ni elimina copias.
