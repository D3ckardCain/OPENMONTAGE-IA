# Diagnóstico de bibliotecas aisladas

`prepared_library_doctor` está disponible en el registro de Studio y del agente,
capacidad `local_library_diagnostics`, costo cero. Usa `tool_info` y luego
`execute_tool` con `{"name":"prepared_library_doctor","inputs":{"library":"socceraction"}}`.
También admite `cq_warehouse`, `soccervision`, `musetalk` y `tvcalib`. Los nombres son una lista cerrada;
la entrada no admite módulos, comandos o scripts arbitrarios.

Cada biblioteca utiliza su propio `.runtime/<nombre>/venv`. El proceso hijo usa
Python con `-I -B`, un worker fijo, 60 segundos de tiempo máximo, caché temporal de
Matplotlib y auditoría que rechaza sockets. Las comprobaciones son sintéticas y
numéricas, sin leer entradas del usuario ni crear contenido. No modifica los
Python de Studio, ComfyUI, Blender o FreeCAD.

## Preparación comprobada

| Entorno | Código y licencia | Diagnóstico comprobado |
|---|---|---|
| Socceraction 1.5.3 | ML-KULeuven/socceraction, commit 93a1242d46c104889205753accaabadb00c45c6d, MIT | Esquema SPADL, orientación de un registro sintético y retorno, rechazo de coordenada inválida |
| cq_warehouse 0.8.0 / CadQuery 2.5.2 | gumyr/cq_warehouse, commit a57bb7a24762d367d66369f280a24c38a64e73dd, Apache-2.0 | Imports CadQuery/OCP y módulos warehouse, dimensiones numéricas y lectura de CSV incluido |
| Soccer Tactical Vision 0.1.0 | rafaelsouza-tech/soccer-tactical-vision, commit 4c557534c624948f3bfe3db956859c7ea3b442fa, MIT | Núcleo CPU e ida/vuelta de homografía numérica sintética |
| MuseTalk | TMElyralab/MuseTalk, commit 0a89dec45a0192b824e3cf4daf96c239440c5ed8, MIT y avisos de componentes | Clases VAE/UNet y APIs/operadores MMLab CPU sin construir modelos |
| TVCalib | MM4SPA/tvcalib, commit 1222c5230af2742395d74918ed6f34eb2b9bf7f9, MIT | Clases de cámara/calibración CPU y escalado numérico reversible |

Los ZIP originales se conservan. Se verificaron respectivamente 168, 142 y 95
archivos contra los blobs de esos commits oficiales. Se preservaron fuentes y
licencias. Las dependencias conservan sus propias condiciones de licencia.
Las huellas SHA256 locales de los ZIP y los recibos de instalación permanecen
en los recibos locales y en sus issues de seguimiento #21, #22 y #23.

Socceraction exige NumPy 1.x/pandas 2.x, por lo que no se añade al entorno de
Kloppy/MPLSoccer de #19. Pandera 0.17.2 falla con multimethod 2.1 al importar
`overload`. La preparación fijó `multimethod<2` (1.12), conservando las fuentes.
La restricción reproducible está en `requirements/socceraction-compatibility.txt`;
se aplica con `pip install -c <archivo> <carpeta de fuente verificada>` usando
exclusivamente el Python de ese entorno. Para cq_warehouse se incluye
`requirements/cq-warehouse-compatibility.txt`; hay que instalar CadQuery junto
con la fuente, porque setup.cfg de cq_warehouse no declara esa dependencia.
El diagnóstico SPADL conserva su campo fijo 105x68 y no debe aplicarse a otro campo
sin una conversión explícita. No acredita lectores de proveedores ni modelos VAEP/xT.

CadQuery 2.5.2 y OCP 7.7.2 importan junto a cq_warehouse sin construir sólidos.
El módulo oficial extensions modifica clases de CadQuery únicamente dentro de
ese proceso aislado. No se modifica FreeCAD. Crear roscas/piezas, exportar formatos
y evaluar tolerancias CAD requieren validación aparte.

Soccer Tactical Vision se preparó con las dependencias CPU declaradas. El grupo
GPU upstream tiene marcadores Linux/macOS ARM y no incluye Windows. Su instalación
base e importación no acreditan detectores, pesos, tracking, vídeo ni rendimiento.
La homografía de diagnóstico es conocida de antemano, no estimada desde imágenes.

## Motores de visión en CPU

MuseTalk se preparó con Python 3.11.9 y PyTorch 2.0.1+cpu, torchvision 0.15.2+cpu,
Diffusers 0.30.2, Transformers 4.39.2, MMCV 2.0.1, MMEngine 0.10.7,
MMDetection 3.1.0 y MMPose 1.1.0. El README recomienda Python 3.10/CUDA;
la comprobación efectuada aquí es exclusivamente CPU con la combinación indicada.
Los 100 archivos del ZIP se contrastaron con el commit oficial y se conservaron.
Las dependencias MMLab recientes proponían NumPy 2.x, incompatible con el
TensorFlow 2.12 declarado upstream. Se preservó NumPy 1.23.5 y se fijó una
combinación compatible en `requirements/musetalk-cpu-compatibility.txt`.
El wheel MMCV CPU procede del índice oficial OpenMMLab para torch2.0/Windows.

No se importa `musetalk.utils.preprocessing`: ese módulo upstream construye
modelos y carga checkpoints al importarse. El diagnóstico importa clases VAE/UNet,
APIs y operadores MMLab y clasifica nombres ficticios sin abrir archivos.
No instancia modelos ni deserializa pesos. Los pesos existentes en el inventario
se conservan sin duplicarlos; presencia y licencia del código no certifican
integridad, configuración o derechos de todos los modelos/componentes.

TVCalib usa un CPython 3.9.25 propio gestionado bajo `.runtime/managed-python`
mediante uv y un venv separado. No sustituye ni registra Python global.
El stack mínimo conserva PyTorch 1.11.0+cpu, torchvision 0.12.0+cpu, Kornia 0.6.3,
Lightning 1.5.10 y NumPy 1.19.5. Los 71 archivos del ZIP se verificaron contra
su commit oficial. Se importa el núcleo sin construir una cámara/calibración;
solo se comprueba escalado numérico e inversa con tensores sintéticos.
`requirements/tvcalib-cpu-diagnostics.txt` documenta los pins, incluido
torchmetrics 0.7.3; pip 24.0 admite los metadatos históricos de Lightning.
Se omiten Jupyter y dependencias de desarrollo. Este entorno antiguo se reserva
para diagnóstico aislado, con sockets bloqueados y sin entradas reales.

Ambos entornos pasan pip check. Los caches de Hugging Face/Torch/Matplotlib se
separan temporalmente y se activa modo offline. El resultado declara
`weights_loaded=false`, `model_inference_performed=false` y `cuda_validated=false`.
No se declara inferencia, sincronización de labios, calibración, precisión ni
rendimiento. Sus etapas de producción necesitan validación posterior autorizada.

## Procedencia y errores

El resultado devuelve versiones realmente importadas, comprobaciones sintéticas,
ausencia de red, lectura real de entradas, geometría, figuras e inferencia.
Incluye SHA256 del worker y, si existe, SHA256 del recibo local, commit y SHA256
del ZIP preparado y conteo de archivos contrastados. El recibo describe la fuente
preparada; no se afirma volver a verificar cada archivo instalado al diagnosticar.
Los errores `LIBRARY_*` distinguen entorno faltante, nombre inválido, tiempo
agotado, respuesta inválida, fallo de importación/diagnóstico y cambio del worker.

Ejecutar un diagnóstico no significa completar la automatización del programa.
Las operaciones de análisis y creación reales requieren contratos y pruebas
posteriores con entradas autorizadas. No se instala nada al llamar al diagnóstico.
