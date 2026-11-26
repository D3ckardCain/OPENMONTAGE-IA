# Por qué hay595 referencias y651 rutas

Son unidades distintas: una referencia identifica un archivo de un repositorio/revisión oficial; una ruta identifica una ubicación local candidata. Ninguna cifra cuenta modelos operativos.

| Medida del inventario inicial | Cantidad | Significado |
|---|---:|---|
| Filas de los4 catálogos guardados |595| Incluyen4 referencias repetidas entre catálogos/grupos |
| Claves distintas repositorio + revisión + archivo |591| Referencias oficiales únicas |
| Filas con una ubicación encontrada |528| Una candidata local por fila |
| Filas con dos ubicaciones |65| Dos candidatas; aún no implica contenido idéntico |
| Filas inicialmente sin ubicación |2| Auxiliares WanCamera, completados después |
| Menciones fila/ruta |658| `528 + 65×2` |
| Rutas locales distintas |651| Al deduplicar7 menciones repetidas de las mismas rutas |
| Identidades físicas distintas |650| Hay un par de nombres unidos por enlace duro |

Las4 referencias repetidas son `tokenizer/spiece.model` de LongCat y `model.safetensors`, `config.json`, `README.md` de VoiceDesign1.7B. Los tres últimos tenían dos candidatas por fila: al repetir esas referencias se repiten6 menciones locales; LongCat repite otra. Por eso658 menciones se reducen a651 rutas. No hay56 modelos añadidos ni56 faltantes ocultos.

Los2 auxiliares nuevos de WanCamera se añadieron sin sobrescribir y con Git blobs oficiales comprobados. Tras ello se localizan las595 filas:653 rutas/652 identidades físicas. El barrido original sigue contando651 rutas; los dos archivos pequeños se verificaron aparte y se integran en el informe final.

Un enlace duro comparte los mismos bytes y no ocupa una segunda copia de datos. Dos rutas en discos distintos con el mismo nombre/tamaño necesitan comparación de hash: no se declaran duplicados por esos metadatos. El informe final agrupa SHA256 coincidentes y distingue enlaces duros, copias independientes y auxiliares compartidos que cada subcarpeta necesita. No elimina ninguno.

Audio8 se añadió después en #175 y su manifiesto separado no forma parte de esas595 filas. Su conjunto no está localizado ni probado. CosyVoice conserva sus conjuntos y sigue aplazado; el Qwen de #82 permanece resuelto y no se repite su diagnóstico.
