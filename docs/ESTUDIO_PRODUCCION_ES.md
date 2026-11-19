# Estudio de producción local

En Windows, abre `OPENMONTAGE_ESTUDIO.cmd` desde la carpeta del repositorio.
El lanzador usa `.venv\Scripts\python.exe` si existe, o Python instalado, y
abre el estudio. No instala dependencias ni descarga pesos silenciosamente.
También puedes ejecutar `python -m backlot studio`, que inicia Backlot si hace
falta y abre `/studio`. El servidor manual usa `python -m backlot serve --port 4750`.
El estudio controla las producciones; el buscador entrega su canal de referencia
mediante «Crear video a partir de este canal». El storyboard original sigue en
`/p/<proyecto>`, con acceso desde el estudio.

## Primera producción

1. En «Configurar ejecución local», comprueba Ollama y ComfyUI. Selecciona un
   modelo **ya instalado** con soporte de llamadas de herramientas y guarda.
2. Indica las carpetas de recursos accesibles en este equipo. Importa los dos
   inventarios en «Modelos y discos» para comparar el catálogo sin repetir pesos.
3. Crea un proyecto: solicitud, pipeline, idioma, referencia opcional y política
   de aprobación. El formulario no inicia ni descarga modelos silenciosamente.
4. Inicia los agentes. El productor lee el manifiesto y sus instrucciones, consulta
   especialistas, ejecuta herramientas locales y persiste artefactos/checkpoints.
5. Revisa actividad, artefactos y etapas. En modo guiado aprueba cada etapa que lo
   requiere. Si necesita aclaración, guárdala y reanuda. Detener es cooperativo:
   una inferencia/render ya enviado puede continuar hasta responder o agotar tiempo.
6. Los resultados aparecen con enlaces y reproductor cuando existen archivos.
   El estado `rendered` exige etapas completas y archivos reconocibles por ffprobe.
   La publicación externa no está autorizada por este flujo.

## Qué está integrado

- Los 12 pipelines públicos existentes, con sus esquemas, requisitos y skills.
- Transporte real de agentes a Ollama, delegación editorial en contextos separados,
  puente a herramientas concretas locales y registros persistentes por proyecto.
- Archivos de trabajo para subtítulos, SVG y proyectos de composición dentro de
  `assets/` o `workspaces/`, consultables por el productor sin editar checkpoints.
- Inspección de imágenes reales del proyecto mediante el modelo local cuando declara
  capacidad de visión; sin esa capacidad se informa la dependencia.
- Descubrimiento del registro local existente: análisis, investigación de YouTube,
  fuentes de fútbol, voz, imágenes, video, audio, composición y verificación según
  disponibilidad de cada herramienta. No se agregan proveedores de pago como fallback.
- Diagnóstico de servidores, GPU declarada por ComfyUI, FFmpeg y carpetas accesibles.
- Catálogos públicos de 564 entradas agrupadas; comparación por ruta/tamaño de
  múltiples inventarios. Son evidencia de archivos registrados, no de inferencia.

## Límites verificables

**No todos los pesos descargados tienen adaptador de ejecución.** Importar su
inventario o añadir una carpeta no instala software, no importa pesos en Ollama y
no registra modelos en ComfyUI. Este panel no promete ejecutar LongCat, CosyVoice,
Kokoro u otra familia sin su adaptador/runtime. Una integración faltante debe
aparecer como bloqueo y describir la dependencia; no se sustituye por datos falsos.

La selección de carpetas es contexto y diagnóstico: no altera `extra_model_paths`
de ComfyUI ni mueve archivos. Sus workflows conservan sus requisitos particulares.
El catálogo mantiene destinos históricos; usa el disco conectado al guardar y
copia la **carpeta**, sin añadir el nombre del archivo al campo de destino.

Un modelo de Ollama sin tool calling puede responder solo con texto: se muestra
`awaiting_input`, no una producción terminada. Los límites de turnos/contexto
conservan artefactos. Reanudar reconstruye el contexto desde solicitud, aclaraciones,
checkpoints y artefactos; el historial conversacional se guarda para auditoría.
Al reiniciar el servidor un trabajo sin worker activo figura como interrumpido.
Solo se ejecuta una producción a la vez para compartir recursos locales.

Una prueba recorre las etapas de `hybrid` hasta un MP4 de prueba generado por
FFmpeg, con un modelo simulado y checkpoints reales; deja publicación pendiente.
Esto valida el recorrido del orquestador, no la calidad generativa.

Las pruebas automatizadas verifican transporte, contratos, persistencia, política
$0 y control de interfaz con fixtures. **No prueban generación con la GPU Windows
ni calidad de inferencia de los modelos del usuario.** Una validación real necesita
Ollama, ComfyUI, pesos/workflows compatibles y un render de muestra en ese equipo.

## Archivos del proyecto

`production_request.json`: solicitud y autorización inicial. `job.json`: estado y
actividad. `checkpoint_<etapa>.json`: artefactos y decisiones por etapa.
`artifacts/*.json`: investigación, guion, escenas, manifiestos y reportes.
`assets/`: medios de producción. `renders/`: exportaciones.
`user_clarifications.json`: instrucciones adicionales. `agent_session.json`:
conversación auditable del productor. Las carpetas de modelos no se modifican.

## Adaptadores de pesos descargados

El registro incorpora 21 rutas nativas y 25 conexiones de workflow ComfyUI.
Su panel de configuración y diagnóstico está en «Modelos y discos». Consulta
[Adaptadores](ADAPTADORES_MODELOS_ES.md): implementaciones, dependencias,
parámetros, limitaciones y diferencia entre conector e inferencia validada.

## Organización del Estudio

El menú lateral separa Producción, Referencias e imágenes, Modelos y discos,
e Historial y pruebas. Cambiar de sección conserva los formularios y no inicia
ninguna herramienta. La configuración local permanece en el lateral. El acceso
a investigar canales conserva su página específica. Esta organización se
comprobó en el navegador real de desarrollo sin activar inferencias.
