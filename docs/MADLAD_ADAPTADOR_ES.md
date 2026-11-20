# MADLAD-400 local

Se añade `model_madlad` como motor nativo de traducción, separado de M2M100. Usa el directorio local `google--madlad400-3b-mt` o una ruta explícita del adaptador. No descarga pesos ni usa API externa.

Entradas: `text`, `language` (código exacto del token de destino del tokenizer) y `output_dir`. El worker añade `<2idioma>`, comprueba que exista y procesa el texto con T5. Los guiones se dividen automáticamente en hasta 128 fragmentos de 512 tokens de entrada, incluyendo el prefijo. Conserva todos los caracteres del original, su orden y los intervalos de cada fragmento. Prioriza límites de frases y palabras. Carga el modelo una sola vez y devuelve traducciones emparejadas con sus fragmentos de origen. Si una salida no termina con el token de fin, informa de posible recorte en vez de declararla completa. La unión con saltos de línea no conserva necesariamente el formato final: requiere revisión editorial. El resultado exige revisión de calidad. No adapta automáticamente referencias culturales o música.

Se usa `local_files_only=True` y `use_safetensors=True`; GGUF no es compatible con este motor. Requiere torch, transformers y sentencepiece. La comprobación de archivos muestra ausencias sin proponer descargar de nuevo todo el modelo.

Fuente de implementación: https://huggingface.co/google/madlad400-3b-mt , revisión fa184c675da0b5c9e1c8694fccd4e12e2d422094. La ficha documenta T5 y el prefijo de idioma. Los tamaños exactos y hashes no se han recogido en este catálogo y se marcan desconocidos; no se puede declarar coincidencia por tamaño con los inventarios.

La preparación aumenta el catálogo a 47 familias (32 motores nativos). Las pruebas usan objetos simulados: falta probar los pesos reales y evaluar traducción por idioma.

## Recuperar una traducción

El motor guarda cada fragmento completado mediante reemplazo atómico. Al ejecutar de nuevo el mismo trabajo reutiliza esos fragmentos, incluida una ejecución ya terminada que no vuelve a cargar el modelo. La huella incluye texto, fragmentación, idioma, límite de salida, ruta del modelo y nombres/tamaños/fechas de sus archivos relevantes. Un cambio crea un registro distinto; los anteriores se conservan. Los metadatos no son una verificación criptográfica de los pesos.

Cerrar y abrir la app no inicia traducción automáticamente. La recuperación requiere volver a ejecutar la herramienta con el mismo directorio de salida. Los checkpoints no sustituyen la revisión lingüística del resultado.

## Panel del proyecto

En Producción, despliega «Traducir un guion con MADLAD local». Pega el texto e inicia la tarea explícitamente. Se usa CPU, el idioma objetivo del proyecto y su carpeta `translations/madlad`. El control de trabajo local impide simultanearla con productores, análisis y entregas. Usa «Consultar traducción guardada» para revisar estado y copiar el resultado. No sustituye el guion aprobado ni inicia producción.

Si la app se cerró, la consulta indica interrupción sin reanudar. Reenvía el mismo texto para recuperar fragmentos compatibles. El modelo se ejecuta como una acción local: no se promete cancelación a mitad de un fragmento. Las pruebas del panel y la tarea usan el motor simulado, sin pesos reales.
