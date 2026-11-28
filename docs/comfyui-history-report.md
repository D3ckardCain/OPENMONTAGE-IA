# Registro de trabajos existentes

`lib.comfy_history_report.summarize_history(history)` interpreta un historial
ComfyUI ya obtenido o exportado. No abre conexiones, carga modelos, descarga
medios, inicia trabajos, cancela trabajos ni modifica el historial recibido.
El panel Estudio, sección Modelos y discos, permite seleccionar un historial
JSON con «Historial ComfyUI». La ruta POST `/api/studio/comfy-history/report`
interpreta exclusivamente el JSON recibido (máximo 8 MB). No consulta el servidor
ComfyUI. El resultado puede consultarse temporalmente o guardarse con «Guardar informe
en el proyecto seleccionado». «Ver informes del proyecto seleccionado» recupera
los registros después de reiniciar. Las rutas GET/POST
`/api/studio/comfy-history/projects/{pid}` leen o guardan el resumen normalizado
en `comfy_history_reports.json` dentro del proyecto. Una importación idéntica
no se duplica; un cambio de estado conserva un informe adicional. Se admiten
hasta 100 informes por proyecto sin eliminar los anteriores. No se copian pesos,
videos ni prompts completos. No existe importación automática del ordenador del usuario.

Devuelve identificador, estado, archivos declarados por nodo y tiempo entre
`execution_start` y `execution_success`, cuando ambos están presentes y son
válidos. Un historial ausente no demuestra que un trabajo esté ejecutándose.
Las interrupciones y errores prevalecen sobre indicadores de éxito.

La duración del video y su calidad visual quedan sin verificar. Ni los tiempos
ni la configuración del flujo actualmente abierto se atribuyen a otro trabajo.
Para comparar equipos deben conservarse el workflow del trabajo, semilla,
imagen de entrada, dimensiones, cuadros, pasos, modelos y versiones; registrar
por separado hardware, ubicación de pesos y si la carga fue fría o en caché.
El tiempo del historial es tiempo de ejecución informado, no tiempo en cola.

## Estado de la prueba del usuario

WAN 2.2 I2V 14B produjo un primer MP4 de 640×640, 5,0625 segundos,
con tiempo mostrado de 4886,86 segundos en la laptop RTX 4060 de 8 GB,
16 GB RAM y archivos en USB. Estos datos fueron observados en la interfaz,
no importados por este módulo. La calidad se revisó mediante fotogramas;
no existe todavía una medición completa de consistencia temporal.

El prompt de levantar el brazo pertenece al segundo trabajo, aún en producción
al realizar la revisión. No corresponde al primer video. La PC grande indicada
por el usuario tiene 32 GB RAM, RTX 5060 y Ryzen 9; VRAM y modelo exacto de CPU
pendientes de confirmar. No se predice su velocidad a partir de estos datos.

## Validación

`python -m pytest tests/tools/test_comfy_history_report.py -q`

Doce casos entre el lector y `tests/tools/test_comfy_history_routes.py` cubren
éxito, errores, interrupciones, datos ausentes, marcas de tiempo inválidas,
rechazo de formatos incorrectos y la ruta del panel con conexiones bloqueadas.
Son pruebas de interpretación e integración sin inferencia ni acceso a GPU.

## Ficha del equipo y condiciones

En cada informe guardado, completa los datos disponibles y pulsa «Guardar ficha
 de esta prueba». La ficha incluye equipo, CPU, GPU, VRAM, RAM, disco y condiciones
 de ejecución. Los campos desconocidos pueden quedar vacíos. Son declaraciones
 del usuario, marcadas sin verificación automática, y no alteran los tiempos ni
 los archivos del historial. Cada cambio conserva una versión anterior; repetir
 la misma ficha no añade otra versión. El máximo es 100 versiones por informe.

La ruta POST `/api/studio/comfy-history/projects/{pid}/{report_id}/context`
valida los campos y mantiene el aislamiento por proyecto. Los trece casos de
prueba incluyen persistencia de fichas, versiones y conservación de evidencias.
No se calculan mejoras de rendimiento entre pruebas con configuraciones distintas.
