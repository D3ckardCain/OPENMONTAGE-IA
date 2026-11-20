# Selección de proveedores locales

## Comportamiento

Los selectores `tts_selector`, `image_selector` y `video_selector` consultan el
registro y descartan los adaptadores bloqueados antes de comprobar disponibilidad,
puntuar o construir listas de alternativas. El catálogo global los conserva como
inventario deshabilitado; una clave configurada no los habilita.

| Área | Regla |
|---|---|
| Voz | Solo proveedores permitidos; un fallo local se devuelve sin reintentar en una API comercial. |
| Imagen | Misma regla; los controles del selector no se envían al contrato nativo del generador. |
| Video | Además exige compatibilidad con imagen a video o referencias cuando se solicitan esas operaciones. No propone imágenes estáticas como sustitución automática. |

`preferred_tool` es una restricción exacta: si señala una herramienta bloqueada
o no disponible, la operación falla en lugar de ejecutarse con otra.
`preferred_provider` conserva la preferencia de puntuación upstream entre
candidatos permitidos; no habilita proveedores bloqueados.

Si el proveedor elegido falla, el selector devuelve el fallo. Las alternativas
son información para revisar, no autorización para cambiar automáticamente
de proveedor o de promesa de entrega. El registro también descarta alternativas
de imagen cuando el origen es una herramienta de generación de video.

## Conexión con Wan local

`comfyui_wan_local` declara explícitamente texto a video e imagen a video.
El selector adapta entradas compartidas antes de invocar su contrato estricto.

| Entrada compartida | Entrada nativa de Wan |
|---|---|
| `duration: "5"` o `"5s"` | `num_frames: 81`, a 16 FPS y con estructura `4n+1` |
| `aspect_ratio: "16:9"`, sin dimensiones | `width: 832`, `height: 480`; formato nativo aproximado, alineado a 16 |
| `aspect_ratio: "9:16"`, sin dimensiones | `width: 480`, `height: 832`; misma alineación |
| `aspect_ratio: "1:1"`, sin dimensiones | `width: 640`, `height: 640` |
| `seed: 0` | Se conserva el cero, sin sustituirlo por una semilla aleatoria |
| `reference_image_path` | Archivo local, subido únicamente al servidor ComfyUI loopback |

Una dimensión más una proporción permite calcular la otra, alineada a 16.
Si se suministran ambas, la proporción debe coincidir dentro de la tolerancia
de alineación (3 % relativo). Los conflictos entre duración y fotogramas o
entre proporción y dimensiones devuelven error.

Las duraciones compartidas admitidas van de 0.25 a 256 s. Los fotogramas se
ajustan a `4n+1`; el resultado informa fotogramas, FPS y duración nativos.
Por ejemplo, 81 fotogramas a 16 FPS ocupan 5.0625 s: la composición debe recortar
si la entrega exige exactamente 5 s. Son límites de contrato, no una garantía
de que cualquier tamaño/duración quepa en la GPU.

Los controles de selección/puntuación (`preferred_tool`, `preferred_provider`,
`preferred_provider_gap`, `hosting_provider`, `allowed_providers`, `task_context`)
no se envían al generador. Se conservan los datos creativos y de procedencia
admitidos, incluidos `project_dir`, `scene_id` y `output_path`.

Un adaptador que solo acepta URLs no provoca la subida automática de la imagen
local a fal.ai ni a otro servicio. Se exige una herramienta que admita la
referencia local; los grafos personalizados y Partner Nodes siguen bloqueados.
Las producciones reales siguen los manifiestos, etapas y aprobaciones normales.

## Pruebas y límites

`make test-zero-cost` incluye selección de voz/imagen/video con contratos
estrictos, proveedor local ausente o fallido, petición exacta de un proveedor
bloqueado, clasificación, alternativas y ausencia de subidas cloud. También
conecta el selector real al adaptador Wan real contra un servidor HTTP emulado,
tanto para texto a video como para imagen a video.

Los archivos de esas pruebas HTTP son marcadores binarios explícitos, no videos
de IA. No demuestran calidad, velocidad, consumo de VRAM ni funcionamiento de
los pesos descargados. La inferencia en la PC del propietario sigue pendiente.
