# Inventario y hashes terminados — 26 noviembre 2026

No quedan lecturas SHA256 pendientes en el conjunto acordado. No se reinició el inventario por el cambio de letra. Se conservaron todos los archivos, Studio, configuraciones, entornos y descargas activas. No se eliminaron duplicados ni se descargaron sustitutos.

## Qué se contó

| Unidad | Resultado |
|---|---:|
| Filas de los4catálogos |595|
| Referencias distintas repositorio/revisión/archivo |591|
| Rutas candidatas iniciales |651|
| Auxiliares WanCamera añadidos/verificados aparte |2|
| Rutas finales del núcleo |653|
| Archivos ya aprobados del anexo, sin nuevas lecturas |15|
| Rutas totales incluidas, núcleo+anexo |668|
| Identidades físicas distintas |667|

Las595filas incluyen4referencias repetidas. Inicialmente528filas tenían1ruta y65tenían2;2auxiliares faltaban. Son658menciones fila/ruta que, al deduplicar7menciones repetidas, dan651rutas distintas. No son651modelos. Los2auxiliares completados después llevan el núcleo a653rutas. El anexo conserva13archivos regionales/Turbo y los documentos FLUX/Kokoro. Explicación y ejemplos: `INVENTARIO_REFERENCIAS_Y_RUTAS_ES.md`.

## Qué proceso duró y qué se repitió

El lector original terminó651rutas en3h57min. Reutilizó150resultados con identidad/metadatos coincidentes:149coincidencias previas y1diferencia previamente conocida. Otros15archivos aprobados del anexo también se reutilizaron. En conjunto hay503hashes nuevos completos y165resultados previos reutilizados; ningún hash aprobado se repitió por el cambio de letra.

El lector inicial registró34errores de acceso/estabilidad enF:, `OSError [Errno22] Invalid argument`, sin digest completo. La unidad seguía visible y las lecturas breves funcionaban. Un único `Get-FileHash -LiteralPath` sobre el primer fallido pudo calcular su hash oficial. Se recuperaron únicamente esos34fallidos mediante el mismo cmdlet integrado, con una pasada acotada y caché por archivo; el primer resultado exitoso se reutilizó. No se ejecutó el auxiliar.ps1 bloqueado ni se cambió ExecutionPolicy. La causa inicial no quedó aislada: no se atribuye a corrupción ni a salud del disco. No hubo reparaciones ni diagnósticos extensos.

**Corrección del avance:** confundí inicialmente «hash completado» con «coincidente». La recuperación terminó34/34, pero27coinciden y7difieren de la referencia de su ruta. Los34fallos originales y todos los resultados posteriores quedan conservados en el JSON final, sin ocultarlos. Actualmente no quedan errores de lectura pendientes ni lectores de hash propios activos.

## F: y reutilización de E:

F: es **Seagate Basic**, USB,1TB, NTFS, serial de volumen **F479B55E** (`4101616990`), disco1, serial físico `NABS41FF`. Se confirmaron2aliasE:→F: por volumen, identificador de archivo, tamaño, mtime y ctime: el FLUXkleinFP8 y su licencia. Se reutilizaron sus hashes; no se dedujo identidad solo por nombre o tamaño. Se revisaron169registros de las cachés antiguas/adicionales y no apareció ninguna verificación válida omitida para los pendientes. Al consolidar,668/668rutas conservaron sus metadatos y resultado reutilizable, sin leer pesos. La caché local consolidada conserva también resultados negativos para evitar rehacer sus hashes.

## Faltantes y discrepancias

No falta ninguna **ruta** del núcleo. Sin embargo,9referencias únicas no tienen la **variante correcta acreditada** en sus candidatas. Hay10rutas con diferencias:

| Conjunto/ruta | Hallazgo |
|---|---|
| MagiHuman `base/model.safetensors.index.json` | Es el índice oficial de **Distill**,13fragmentos; Base espera7. Archivo legítimo en otra ubicación, no prueba de corrupción de pesos. |
| Wan VACE `high_noise_model` enD: | Su SHA256 es el oficial de `low_noise_model`; hay dos copias de Low en lugar del par High/Low. |
| LongCat Avatar Single, fragmentos2–6 | Sus hashes corresponden a los fragmentos oficiales **Multi** respectivos. Las variantes Single correctas no quedan acreditadas allí. |
| LongCat Avatar, fragmento1 de Single y Multi | Ambos tienen el mismo SHA256 local, distinto de ambos esperados. No se identificó ese digest entre las referencias oficiales fijadas consultadas; se conservan sin declarar corrupción. |
| Copia antigua VoiceDesign1.7B enD: | Diferencia conocida, reutilizada por caché. La copiaC: validada sí coincide; no se repitió síntesis ni se sustituyó nada. |

El JSON incluye SHA256 esperado/obtenido, fuente/revisión, metadatos, variantes oficiales identificadas y URLs fijadas de las9referencias pendientes de variante. No inicia descargas. Para los dos fragmentos1 y VoiceDesignD: no se inventa una identidad oficial.

277de las591referencias únicas no publican SHA256 de contenido en esos metadatos: se contrastó el Gitblob oficial y se registró el SHA256 local sin llamarlo «oficial». Ninguna referencia del núcleo carece de ambos tipos de digest esperado.14referencias reutilizan la referencia fijada en inventarios previos; el resto proviene de metadatos oficiales fijados o de los2auxiliares pequeños. Las2entradas brutas «digest no disponible» eran tokenizadores grandes, ya contrastados por Gitblob; se integraron sin releerlos.

## Duplicados

En las668rutas hay81grupos de contenido idéntico y104copias independientes adicionales, aproximadamente135,54GB lógicos. No es una medición de asignación física ni una orden de borrado. El núcleo por sí solo contiene80grupos,25de ellos de payloads; los demás incluyen auxiliares que pueden necesitarse en cada subcarpeta. El par de nombres unidos por enlace duro comparte datos y no se cuenta como otra copia independiente. Se conservaron ambos conjuntos ACE-Step y todos los demás originales.

## Estado funcional y editor

Identidad, estructura y funcionamiento siguen separados: cada archivo registra el alcance de la inspección estructural; algunos formatos/tipos no se validan completamente. Un digest correcto no acredita compatibilidad, memoria ni calidad. No se repiten ASR, síntesis, renders o pruebas aprobadas.

Turbo: en proyectos y entornos QA existentes solo apareció un WAV>5s, la extracción portuguesa real paraASR; no acredita referencia sintética autorizada para clonación y no se usa. Las muestras sintéticas autorizadas conocidas son más cortas. Audio8 sigue pendiente de localizar/completar sus pesos, sin prueba funcional. CosyVoice permanece aplazado.

Las curvas de posición, escala, giro, opacidad y Bézier de **capas** están publicadas en `ccb602c`, con14pruebas nuevas focalizadas y dos renders nuevos necesarios para la equivalencia preview/export. Ver `EDITOR_KEYFRAMES_TRANSFORMACION_ES.md`. No se declara todo #174 terminado. La única activación agrupada de4750 sigue pendiente de la acción manual documentada por el rechazo de política anterior; no se elude ni se repiten las validaciones aprobadas. PR#2 permanece en borrador.

Artefactos: `DESCARGAS_COMPLETAS_RESULTADO_20261126.json`, `DESCARGAS_COMPLETAS_ARCHIVOS_20261126.csv`, `DESCARGAS_DUPLICADOS_20261126.csv` y `DESCARGAS_ANEXO_VOCES_DOCUMENTOS_20261126.json`.
# Actualización posterior

El índice MagiHuman Base ya está corregido y verificado contra su blob oficial. Quedan 9 rutas discrepantes / 8 referencias únicas pendientes; los contadores originales de este informe conservan el estado histórico previo. Véase [corrección y seguimiento de Wan VACE](CORRECCION_MAGIHUMAN_Y_WAN_VACE_ES.md).

