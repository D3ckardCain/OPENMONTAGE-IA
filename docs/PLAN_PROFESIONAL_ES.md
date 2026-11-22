# Plan de OPENMONTAGE‑IA

## Auditoría y punto de partida

En el commit 320bba9 pasaron 57 pruebas de comparativas, exportación y estudio. Una consulta real Messi–Mbappé en Qatar 2022 devolvió 7 y 8 goles y 29 y 21 disparos. La selección produjo un SVG y un segmento H.264 vertical de 720 × 1280 que FFmpeg decodificó completo. El segmento duró dos segundos y se probó sin audio. Chromium quedó bloqueado al arrancar en el entorno de auditoría. Quedan pendientes la validación visual y las pruebas de ComfyUI en la RTX 4060 de 8 GB.

El panel actual de fútbol expone consultas UEFA. El agente ya puede consultar varias fuentes, reunir lotes y validar una selección antes de exportar.

## Orden de implementación

1. **Métricas y fases.** Conservar las 54 métricas comunes en todas las competiciones y los campos adicionales que publique cada fuente. Mantener los datos sin evidencia como ausentes. Identificar edición, selección o club, fase, unidad y procedencia de cada cifra. Validar el calendario por edición. Los grupos, eliminatorias directas, semifinales, final y tercer puesto oficial cuentan en el total del torneo cuando se disputan. La clasificación previa corresponde a un bloque separado del historial individual. Un total de edición no habilita filtros por ronda.
2. **Mesa de comparativas.** Buscar dos jugadores, elegir competición y edición, revisar el informe con enlaces y seleccionar las métricas disponibles. Mostrar una vista previa antes de la aprobación. Guardar informe, selección y resultado de la revisión juntos. Exportar postal y clip desde el mismo expediente. Los filtros por ronda se habilitan cuando la fuente acredita ese alcance.
3. **Producción bilingüe.** Al crear una versión localizada, copiar la selección deportiva vigente al proyecto nuevo y registrar el ID y hash del expediente de origen. Una selección posterior crea una versión nueva sin alterar la anterior. Reusar la plantilla y las escenas cuando corresponda; generar y revisar audio y subtítulos por idioma. Marcar las piezas que requieren nueva revisión al cambiar datos o selección. Recuperar la entrega a otro disco desde el render verificado.
4. **Escala local.** Producir un piloto de diez piezas completas. Medir duración por etapa, uso máximo de RAM y VRAM, aprobación al primer intento y causas de reintento. Mantener la cola secuencial hasta tener medidas. Después separar tareas de CPU y GPU y asignar trabajadores según capacidad probada. Medir el rendimiento antes de comprometer el objetivo de 48 videos semanales. La publicación se opera por separado.

La sección **Cola de producciones → Ver tiempos de producción** muestra los intervalos inicio-fin del intento actual que la cola registró para cada trabajo. El total solo suma intervalos completos del intento actual; un bloqueo sin hora de fin aparece sin duración. Al solicitar un reintento se conserva la causa, estado y fechas del intento anterior en un historial de hasta veinte registros por trabajo; los registros antiguos no tenían este historial. Los checkpoints nuevos aportan además segundos de actividad del productor por etapa y sesión; la espera humana entre ejecuciones queda fuera de esos intervalos. Las etapas antiguas o interrumpidas sin cierre medido pueden quedar incompletas. El productor toma muestras de RAM del equipo y, si existe `nvidia-smi`, VRAM de la GPU NVIDIA más ocupada al iniciar y aproximadamente cada cinco segundos; guarda los máximos observados al terminar. Son valores de todo el equipo y GPU, no consumo atribuible exclusivamente al proyecto; picos entre muestras pueden escapar. Sin fuente disponible aparece «sin medir». La capacidad de 48 videos semanales aún no se estima. La consulta no inicia modelos ni producción.

El panel cuenta las etapas con checkpoint actual completado y `human_approved: true`; agrupa las causas de reintento por estado. Una aprobación automática autorizada también puede quedar marcada como aprobada. En una etapa guiada, «Solicitar cambios» registra el motivo y archiva el checkpoint pendiente antes de marcarlo para corrección; no inicia la producción. La primera decisión editorial explícita por etapa (aprobar o solicitar cambios) aporta la tasa de aprobación inicial. La tasa excluye etapas sin decisión y revisiones anteriores a este registro; conserva hasta 200 decisiones recientes por proyecto. No equivale a tasa de éxito de videos completos.

Al reanudar una etapa devuelta para corrección, el productor recibe explícitamente la etapa y el motivo editorial guardados en el checkpoint actual. Una vez escrito un checkpoint nuevo, la petición anterior queda en el historial y deja de aparecer como corrección pendiente.

Al pedir un reintento, la cola conserva también la última muestra de RAM y VRAM de ese intento, si existe y corresponde a su inicio. El panel muestra las muestras históricas por intento y el mayor pico guardado, sin presentar una muestra vieja como consumo del intento nuevo. Los proyectos anteriores a este registro no recuperan automáticamente mediciones ya sobrescritas.

Los eventos de tiempo por etapa se agrupan por las fechas del intento actual. Al reintentar se archiva el desglose del intento anterior y se muestra por separado. Los eventos antiguos sin fecha válida o eliminados por el límite del registro no se pueden asignar retroactivamente a un intento.

El resumen «Piloto provisional» toma los primeros diez registros de la cola actual y muestra terminados, bloqueados o en espera y cobertura de duración, RAM y VRAM para los terminados. Solo indica «mediciones completas» cuando los diez terminaron y todos tienen las tres medidas. La cola se puede reordenar o editar, así que este corte no fija una cohorte histórica; no prueba calidad editorial ni permite inferir rendimiento semanal.

«Fijar los primeros diez proyectos como piloto» guarda explícitamente una cohorte de diez IDs distintos, su orden y el disco de proyectos, sin iniciar generación. Desde entonces el resumen usa esa cohorte aunque se reordene la cola y muestra cuántos proyectos han sido retirados. Fijar otro grupo distinto crea un nuevo registro; se conservan hasta veinte grupos, pero el panel consulta el último. En otro disco, el panel advierte que la cohorte guardada pertenece a una raíz distinta y presenta un resumen provisional de la cola actual.

El informe separa los agregados de toda la cola de los del piloto: suma la duración de los intentos finales terminados en la cohorte y muestra los máximos medidos de RAM y VRAM, el número de reintentos y la proporción de primeras decisiones editoriales aprobadas solo para esos proyectos. Los picos incluyen intentos anteriores guardados. La duración no suma intentos fallidos ni demuestra calidad del video; las etapas sin decisión quedan fuera del porcentaje.

Para los trabajos marcados como terminados, el piloto cuenta los recibos `render_verification.json` con estado `passed` y las copias `final_delivery.json` con `copied: true`. La copia final solo es esperable si se configuró un disco de destino. La consulta lee recibos guardados; no vuelve a comprobar integridad o disponibilidad de los archivos ni la calidad visual o editorial.

«Comprobar cola sin ejecutar» consulta `GET /api/tags` en el Ollama local configurado, con límite de tres segundos, y comprueba que el nombre exacto del modelo seleccionado figure instalado. Cuando falta el modelo o no responde el servicio, muestra que la cola no está preparada. Esta consulta no descarga pesos ni ejecuta inferencia; tampoco valida la compatibilidad del modelo con llamadas de herramientas, la disponibilidad de ComfyUI o los workflows de cada etapa.

«Ejecutar cola local» repite la comprobación justo antes de lanzar un agente para el primer trabajo pendiente y rechaza el inicio si falta el modelo o no responde Ollama; la cola conserva su estado. Si ese trabajo ya tiene estado `rendered`, puede marcarlo como terminado sin exigir el modelo ni volver a generar.

### Desglose por ronda de Qatar 2022

El agente puede consultar partidos jugados, goles y tiros en grupos, octavos, cuartos, semifinal, tercer puesto y final. Verifica el calendario de 64 partidos y contrasta los eventos de los encuentros consultados con el marcador. Incluye prórroga y deja fuera las tandas de penaltis al contar goles y tiros. El informe conserva las URLs por partido y el nombre StatsBomb. Esta consulta está disponible para investigación. La selección de métricas permite revisar las cifras con sus fuentes. La licencia de StatsBomb Open Data, cláusulas 1.2.2 y 1.4, excluye la explotación comercial y exige el logotipo al publicar análisis. El informe queda fuera de los exportadores. Para las piezas del canal, OpenFootball aporta goles atribuidos por ronda y publica estos datos como dominio público. Se revisan los marcadores y se excluyen las tandas y los autogoles de los goles individuales. La lista de goleadores permite confirmar cifras positivas. La ausencia queda como dato sin verificar y no se convierte en cero, porque la fuente no acredita la participación de cada jugador. Los tiros y partidos por ronda siguen disponibles para investigación en StatsBomb.

### Mesa de comparativas

En **Fútbol**, elige entre las ediciones disponibles de AS, Classificação Geral y los conectores de DFL, Eredivisie, AFC, OFC, MLS y J.League, y selecciona **Torneo completo** para revisar las 54 métricas comunes con las cifras disponibles por jugador. La mesa muestra el alcance de cada fuente. Marca de una a seis métricas compartidas y genera la vista previa. La postal SVG y el clip MP4 de seis segundos usan esa misma selección. Classificação Geral busca primero por apellido y consulta por páginas si hace falta. Cuando la fuente publica totales de edición sin una fase verificable, la mesa indica ese alcance. Para J1, J2, J3 y Copa Levain 2025, la mesa solicita todos los rankings integrados en el conector oficial en lotes de seis métricas; une los resultados solo si coinciden edición, fuente e identidad de los jugadores. Conserva las consultas y los fallos por métrica, y bloquea la exportación verificada si falla un lote. Para una ronda concreta, OpenFootball aporta los goles acreditados. Si se reinicia el estudio, vuelve a consultar para validar una nueva exportación.

La edición de Premier League 2024/25 corresponde exclusivamente a las cifras acumuladas hasta la jornada 29 del informe oficial. Sus rankings muestran líderes, no el universo de jugadores ni el cierre de temporada; los campos no publicados permanecen sin dato. La mesa conserva ese corte en el título, el alcance y la referencia de la consulta.

UEFA EURO 2024 aparece como torneo final. La consulta pide las métricas publicadas por UEFA en lotes internos y conserva la edición, el identificador de competición, la fase y la página de cada cifra. La clasificación previa queda fuera de este total; se consulta por separado al solicitar el historial del jugador. Si una métrica no aparece pero otras están verificadas para los dos jugadores, se pueden elegir solo estas últimas. Un lote fallido bloquea la exportación verificada.

Champions League, Europa League y Conference League 2024/25 también están en la mesa con edición UEFA `2025` y fase `TOURNAMENT`. Los partidos previos de clasificación no se suman a las cifras de esa fase. Las tres ediciones usan la misma matriz de métricas y las mismas verificaciones de fuentes y selección que EURO 2024.

La Champions femenina 2024/25 usa la misma matriz y la edición UEFA `2025`, identificada como competición femenina en el selector. La fase de clasificación se mantiene separada de las estadísticas del torneo principal.

UEFA Nations League 2024/25 usa edición UEFA `2025` y fase `TOURNAMENT`. La mesa solicita los datos por jugador con el mismo esquema y marca como ausentes las cifras que el servicio no confirme. La ruta histórica exacta y la cobertura de sus métricas se deben contrastar con una consulta real desde la app antes de producir un piloto publicable.

FIFA Qatar 2022 también está en la mesa, identificado mediante los IDs de competición `17` y temporada `255711`. El conector comprueba ambos IDs en el servicio FIFA antes de atribuir cifras. El alcance del servicio es `season_aggregate_as_published`: no acredita por sí solo qué rondas incluye ni separa eliminatorias previas, así que la mesa muestra «fase sin acreditar» y evita llamarlo «torneo final». Las métricas disponibles se leen del informe estadístico FIFA, sin inventar las ausentes. FIFA entrega este informe en un único archivo de jugadores; el conector limita su tamaño y selecciona las métricas localmente, porque la fuente no acredita un parámetro para solicitar ese archivo por partes. El desglose por ronda de Qatar continúa en la fuente OpenFootball separada.

Para FIFA, UEFA y J.League, una cifra ausente en una métrica no impide escoger otras cifras verificadas de ambos jugadores. La selección exige valor, identidad y URL de origen de cada cifra. Los errores de consulta, los lotes fallidos, los jugadores ambiguos y las estadísticas de fases mezcladas siguen bloqueando la exportación. El nombre del archivo exportado conserva los IDs de FIFA o la edición y fase UEFA cuando el proveedor no usa los campos de las ligas.

La matriz común muestra las 54 métricas con nombres en español y grupos de participación, ataque, creación, defensa, portería, disciplina y físico para todas las ediciones. Las métricas propias de una fuente aparecen al final. «Sin dato» significa que esa fuente no aportó un valor verificable para ese jugador y alcance; no equivale a cero.

La consulta del agente conserva esa misma matriz de 54 campos incluso cuando una fuente no responde o no devuelve dos jugadores. En tal caso todas las cifras quedan ausentes, se conserva el error en la sección y no hay informe exportable. La presencia del campo común no acredita que la fuente publique esa métrica.
La mesa de la app también muestra la matriz ausente en un desplegable cuando una consulta falla o devuelve otra fase. Ninguna cifra del informe rechazado se conserva en ese desplegable.
Cada fila de una consulta de comparativa indica `availability`: `both_players`, `one_player` o `not_observed` según las cifras que esa consulta devolvió para los dos jugadores. El cero publicado cuenta como cifra observada. Este estado describe el resultado puntual, no la cobertura total de la fuente o del campeonato; los errores de consulta permanecen separados y bloquean la exportación.

El catálogo `sports_sources` ahora enumera para cada competición los campos comunes configurados en su adaptador y los campos adicionales. UEFA y FIFA marcan además el descubrimiento dinámico de métricas: sus cifras publicadas pueden superar el conjunto de equivalencias conocido. Estos recuentos describen código, no jugadores encontrados ni cobertura verificada:

| Conector compartido por competiciones de la lista | Campos comunes configurados | Pendiente principal |
|---|---:|---|
| UEFA | 34 | Verificar por competición y fase las cifras adicionales descubiertas. |
| FIFA | 3 equivalencias conocidas | Inventariar y definir el resto del feed de cada edición sin suponer unidades. |
| J.League | 32 | Comprobar disponibilidad por división, copa y jugador. |
| AS (Liga MX y torneos configurados) | 26 | Verificar rankings por edición; algunos pueden estar vacíos. |
| Premier League | 20 | Ampliar más allá del informe de líderes hasta la jornada 29. |
| DFL | 14 | Ampliar el universo de jugadores de los rankings y vistas previas. |
| AFC | 9 | Superar el informe de líderes de la Copa Asiática. |
| Classificação Geral | 7 | Acreditar fases y ampliar estadísticas de sus ligas y copas. |
| MLS y Eredivisie | 4 cada uno | Completar métricas y universo de jugadores. |
| OFC Nations Cup | 1 | Completar el resto de estadísticas con fuentes acreditadas. |

CONMEBOL y CONCACAF como instituciones; AFC, CAF y OFC como directorios; K League, Emiratos, Qatar, Sudáfrica, Marruecos y Egipto siguen sin conector de cifras en el catálogo. La matriz común permanece habilitada para todas, con valores ausentes hasta que una fuente verificable aporte cada cifra.

K League quedó en `source_inspection_only`: [la tabla pública de jugadores](https://www.kleague.com/record/player.do) ofrece varias columnas y [la API oficial de ranking](https://api.kleague.com/docs/api_pl_rank.jsp) documenta más campos, pero exige `authKey`. [El aviso del portal](https://portal.kleague.com/mainFrame.do?selectedMenuCd=0390) restringe copiar, almacenar, distribuir o vender registros sin autorización previa fuera de usos de prensa. No conectar esos datos a postales o videos del canal hasta aclarar acceso y permiso de uso; conservar la matriz común con valores ausentes. La tabla pública consultada por defecto muestra la temporada actual y no acredita por sí sola fases o ediciones anteriores.

UAE Pro League también quedó en `source_inspection_only`: [la página de estadísticas](https://www.uaeproleague.ae/en/stats) ofrece filtros de temporada y competición y una vista para comparar jugadores. [Sus condiciones](https://www.uaeproleague.ae/pages/en/terms-of-use) autorizan la reproducción del contenido del sitio para uso personal no comercial y [la explicación de datos](https://www.uaeproleague.ae/pages/en/data-capture) advierte que sus estadísticas no se deben tratar como oficiales. No incorporar esta fuente a las postales y videos del canal sin un permiso y una definición de datos adecuados; sus campos comunes siguen vacíos.

Qatar Stars League quedó en `source_inspection_only`: [el archivo 2025/26](https://qsl.qa/index.php/en/doha-bank-stars-league-archive) identifica la edición y muestra veinte goleadores, mientras [la ficha de temporada](https://www.qsl.qa/en/qatar-stars-league-20252026) indica 22 rondas. El archivo también muestra un play-off, por lo que no se atribuirán automáticamente sus cifras a otras fases. Una ausencia en la tabla de goleadores no equivale a cero; no hay allí las otras 53 métricas comunes. Quedan pendientes un extractor contrastado y las condiciones aplicables a la reutilización en el canal.

La PSL de Sudáfrica permanece en `source_inspection_only`: su web ofrece resultados y noticias, pero no se verificó allí un catálogo completo por jugador y temporada. Las condiciones de uso publicadas en `https://www.psl.co.za/content/101801` requieren consentimiento escrito previo para un uso comercial o no privado/educativo de la información del sitio. Mantener la matriz común sin valores de PSL hasta obtener una fuente apta para el canal.

Antes de ofrecer una postal o clip, la mesa compara la competición, la edición y la fase devueltas por la fuente con la opción elegida. Si difieren, descarta el informe y muestra el error de alcance sin emitir token de exportación. Para UEFA usa `seasonYear` y `phase`; para FIFA comprueba los IDs de competición y temporada y el alcance publicado.

Después de la vista previa, «Descargar expediente JSON» reúne el informe firmado durante la sesión, la matriz completa, la selección de hasta seis métricas y las cifras y URLs usadas para cada jugador. Incluye marca de tiempo UTC y checksum SHA-256 para detectar cambios accidentales en el archivo. «Guardar selección en proyecto» archiva cada revisión distinta sin sobrescribir las anteriores y crea un índice de la última para el agente productor. La verificación técnica del render guarda la identidad, hash y métricas de la selección vigente y rechaza un cambio durante la verificación. «Videos finales» muestra esa asociación conservada. No certifica que las cifras aparezcan correctamente en los fotogramas, derechos comerciales ni aprobación editorial. Sigue pendiente asociar el expediente a cada versión en español e inglés y revisar la concordancia visual del video.

## Modelos candidatos

| Candidato | Prueba de aceptación |
|---|---|
| [Qwen3‑TTS 12Hz 0.6B CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice) | Comparar contra Qwen3‑TTS 1.7B y Kokoro con el mismo guion en español e inglés. Revisar pronunciación de nombres y cifras y medir memoria y tiempo. |
| [Qwen3‑VL‑4B‑Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct), variante cuantizada compatible | Revisar pocos fotogramas por consulta. Medir memoria y legibilidad detectada en rótulos y subtítulos. |
| [RF‑DETR Nano](https://github.com/roboflow/rf-detr) | Medir detección de jugadores. Probar el balón pequeño, las oclusiones y los cambios de cámara de forma independiente. |

Cotejar los inventarios antes de descargar. Faster‑Whisper y PaddleOCR latino ya están catalogados. Usar los pesos disponibles de WAN, LTX, FLUX y Qwen3‑TTS 1.7B para la primera ronda. Los candidatos requieren validación local. El objetivo operativo sigue siendo cero dólares, sin tarjetas ni APIs de pago.

## Formatos iniciales

- **Duelo en 30 segundos.** Dos jugadores y tres métricas aprobadas. Una pieza vertical animada y una postal desde el mismo informe.
- **La jugada explicada.** Diagramas tácticos propios. Añadir velocidad, balón y fuera de juego después de validar la medición con referencias conocidas.
- **Ficha de leyenda.** Fútbol, béisbol y boxeo con corte y fuente visibles. Distinguir bateo y pitcheo, y ranking, récord y resultado de combate.
- **Biblia ilustrada.** Historias con continuidad de personajes, pronunciación revisada y versiones en español e inglés. Usar generadores de movimiento en planos donde aporten al relato.
