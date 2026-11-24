# Operaciones funcionales de bibliotecas aisladas

Continuación de #21–#25. Se reutilizan los entornos `.runtime/<biblioteca>/venv`, fuentes y recibos ya preparados; no se instalan dependencias al ejecutar herramientas ni se modifican `.venv`, ComfyUI o configuraciones personales.

Cada operación está registrada como herramienta local de costo cero. El agente consulta `tool_info`, lee las instrucciones de la etapa y este manual, y llama a `execute_tool` con el proyecto correcto. La API de Studio usa exactamente la misma herramienta. Procesos `-I -B`, worker fijo compartido con el diagnóstico existente, sockets Python bloqueados, CPU/cachés temporales y modo HF/Torch offline. Máximo 500000 bytes de entrada, salida acotada y timeout 60s. No se aceptan scripts, módulos, rutas de checkpoints o comandos arbitrarios.

Los informes incluyen versiones importadas, SHA256 del payload canónico y worker, proyecto/UTC y recibo de preparación (commit y ZIP). El recibo no afirma revalidar todos los archivos instalados. La entrada es declarada por el usuario, no evidencia independiente. No se escriben informes o contenido automáticamente: el agente puede conservar resultados en sus artefactos conforme al contrato habitual.

## Socceraction: validar SPADL

Herramienta `socceraction_spadl_validate`; `POST /api/studio/libraries/socceraction/spadl/validate`. Entrada: `project_id`, `coordinate_system: "spadl_105x68_bottom_left_home_to_right"` y `actions` (1–1000 objetos SPADL). Los campos obligatorios son game_id, original_event_id (puede ser null), action_id, period_id, time_seconds, team_id, player_id, start_x, start_y, end_x, end_y, bodypart_id, type_id y result_id. Nombres bodypart_name/type_name/result_name son opcionales y deben corresponder a sus IDs. No se admiten columnas desconocidas.

Se comprueban tipos sin coerciones que trunquen IDs, valores finitos, identificadores, duplicados de action_id por partido y correspondencia nombre/ID. Después se usa `socceraction.spadl.schema.SPADLSchema` real para columnas, periodos, enums y límites. `native_schema_checked` distingue si los errores de entrada permitieron llegar al esquema. `valid=false` es un fallo de validación con issues acotados (hasta20) y procedencia; la API devuelve400 con el informe. Errores de instalación/proceso/timeout se diferencian mediante prefijos LIBRARY/SPADL.

El marco nativo es 105x68 metros, origen inferior izquierdo y local hacia la derecha, según [SPADL oficial](https://socceraction.readthedocs.io/en/latest/api/spadl_regular.html). La declaración es obligatoria; no se convierte ni orienta automáticamente, no se reparan acciones, no se transforman eventos de proveedores ni se entrena/ejecuta VAEP/xT. Un archivo válido no acredita exactitud de un partido ni licencia de sus datos.

Ejemplo de acción sintética: `{"game_id":0,"original_event_id":null,"action_id":0,"period_id":1,"time_seconds":0.0,"team_id":2,"player_id":0,"start_x":10.0,"start_y":20.0,"end_x":30.0,"end_y":40.0,"bodypart_id":0,"type_id":0,"result_id":1}`.

## cq_warehouse: dimensiones sin sólidos

Herramienta `warehouse_dimensions`; `POST /api/studio/libraries/cq_warehouse/dimensions`. Entrada: proyecto, `size` imperial numerado/fracción y TPI (p.ej. `#8-32` o `1/4-20`), `across_flats_mm` positivo hasta10000 y `sides` entero3–24. Usa las funciones oficiales decode_imperial_size y polygon_diagonal del [código preparado](https://github.com/gumyr/cq_warehouse/blob/a57bb7a24762d367d66369f280a24c38a64e73dd/src/cq_warehouse/fastener.py).

La sintaxis está limitada a números/fracciones positivas y tamaños numerados admitidos; no acepta expresiones o rutas. Devuelve diámetro y paso en mm y diagonal del polígono regular declarado. Para #8-32 se verificó4.1656mm/0.79375mm. No construye roscas, piezas, documentos o geometría y no acredita correspondencia con un estándar, ajuste físico o tolerancias de fabricación.

## Soccer Tactical Vision: homografía declarada

Herramienta `soccervision_homography`; `POST /api/studio/libraries/soccervision/homography`. Entrada: proyecto, matriz3x3 conocida, 1–1000puntosXY y source_units/target_units explícitos (pixels/metres/normalized/declared). Se llama al apply_homography oficial del entorno CPU, con rechazo de matrices singulares/condición>1e10, no finitos, puntos sobre el horizonte e inversa inestable. La salida conserva unidades declaradas y error de ida/vuelta, no exactitud de calibración. No estima la matriz desde imágenes, identifica puntos de campo, detecta jugadores, ejecuta tracking ni carga pesos. Las unidades declaradas no demuestran que la matriz corresponda a un campo o cámara reales.

## MuseTalk: plan de lotes con placeholders CPU

Herramienta `musetalk_batch_plan`; `POST /api/studio/libraries/musetalk/batch-plan`. Entrada: proyecto, audio_chunk_count/latent_frame_count (1–32), batch_size (1–16) y delay_frame (0–1000). Usa el datagen oficial de la fuente preparada para agrupar tensores CPU sintéticos pequeños. Devuelve índices de chunks/latentes, shapes y lote final parcial; prueba la correspondencia modular con desplazamiento. No recibe medios, rutas o checkpoints, ni ejecuta Whisper/VAE/UNet. Las formas placeholder no certifican embeddings/latentes reales ni sincronía de labios.

Se evita preprocessing, que construye modelos al importarse. El componente de batching es funcional y comprobable sin inferencia; la síntesis completa de avatares, compatibilidad de pesos y calidad siguen fuera de esta fase sin contenido real. La instalación CPU y las condiciones de componentes de #24 se conservan; no se añade CUDA ni se descargan modelos.

## TVCalib: parámetros normalizados

Herramienta `tvcalib_parameters`; `POST /api/studio/libraries/tvcalib/parameters`. Entrada: proyecto, loc/scale, values (1–1000), mode normalize/denormalize, feature_name y feature_unit explícitos. Usa FeatureScalerZScore de la fuente preparada, tensores CPU float64 y retorno numérico para medir consistencia. Valores/loc de magnitud<=1e9 y escala positiva1e-9–1e9; no se infieren distribuciones o unidades.

Normalize devuelve z-scores adimensionales; denormalize recupera la unidad declarada. Ejemplo loc10/scale2 convierte[8,10,12]↔[-1,0,1]. No construye una cámara, ajusta parámetros a imágenes, estima distorsión, ejecuta optimización o calibra vídeo. La calibración completa y calidad están pendientes fuera de esta operación numérica sin contenido real; no se declaran validadas por ejecutar el escalador.
