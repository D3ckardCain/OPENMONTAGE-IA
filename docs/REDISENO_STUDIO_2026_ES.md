# Studio: rediseño de interfaz

La carcasa visual se reemplaza por una aplicación de trabajo en ancho completo: navegación lateral, barra de contexto y espacios separados para Vídeo, Audio, Subtítulos, Biblioteca, Proyectos, Investigación, Comparativas, Miniaturas, Avatares, Clips y Preferencias. El diseño usa GitHub Dark, iconos SVG locales, controles compactos y scroll dentro de paneles; no carga fuentes, imágenes ni código remoto.

## Flujos conectados

- **Proyectos:** lista y creación por `/api/studio/editor/projects`; muestra la ruta completa y las carpetas de trabajo que devuelve el workspace. La reserva de nombre y creación del árbol siguen en el backend existente. La raíz efectiva se lee de `/api/studio/storage`; cambiarla desde esta pantalla no está habilitado.
- **Vídeo / edición manual:** `/api/studio/editor/projects`, estado, carga de originales, registro, comandos compartidos, render y estado del render. Los controles visibles cubren añadir fuente, recortar, dividir, mover en orden, quitar, formato, deshacer/rehacer, guardar y exportar. El archivo importado se copia al proyecto según el endpoint; el archivo de origen no se mueve ni se elimina.
- **Audio:** presenta las pistas del montaje y conecta ganancia, mute y solo a `operation=clip`. No dibuja una forma de onda falsa. EQ, compresor, ducking y catálogo no aparecen como controles activos en esta entrega.
- **Subtítulos:** importa bytes SRT con la ruta existente, edita texto/tiempos con `cue_update`, aplica estilo/posición/modo/idioma con `subtitle_style` y descarga SRT. Nuevo bloque vacío no está soportado por el comando disponible y queda desactivado. Calidad, karaoke, límites CPS y zonas seguras no se anuncian aquí.
- **Investigación (módulo 10):** usa búsqueda real de canales de YouTube y su configuración/credencial local. Las métricas vacías se muestran como desconocidas. TikTok, Facebook e Instagram carecen de conector público configurado; sus cifras solo pueden aportarse como notas locales sin verificar, que no se presentan como mediciones confirmadas. Auditorías históricas/compare snapshots, dossiers de ideas y comparación editorial existentes todavía no están conectados a esta pantalla.
- **Comparativas deportivas (módulo 11):** reutiliza schema/query UEFA existente, incluida la acción `compare_players`; los controles siguen el esquema (nombres/métricas en listas, temporada numérica, fase y campos específicos). Presenta alcance/contexto que devuelve la fuente. La cobertura depende del conector y no equivale a todo el deporte. Envío a vídeo, clips o miniaturas no está habilitado por este módulo.
- **Otros modos:** las seis opciones de Vídeo están visibles. Solo «Editar material propio» ejecuta el ciclo conectado. Texto a vídeo, imagen a vídeo, recreación desde referencia, guion a vídeo y plantillas muestran estado no disponible/preparación pendiente. Miniaturas, avatares y clips describen límites y no fingen una generación.

## Identidad y activación

La página consulta `/api/studio/identity`. Si el proceso anuncia `restart_required`, muestra una advertencia discreta con hashes abreviados; no reinicia nada automáticamente. La nueva página también se sirve desde el archivo local mientras el backend sigue siendo el ya residente. Toda escritura depende de que la ruta de API correspondiente responda y valide revisión.

## Revisión y límites

Verificación local: HTTP 200 para `/studio`, `/ui/studio.css`, `/ui/studio.js` y `/api/studio/editor/capabilities`; 11 módulos, IDs HTML únicos, sin entradas heredadas de CSS/JS visual y llaves CSS balanceadas. El endpoint de capacidades declaró comandos de edición compartidos, incluidos mezclador, keyframes, ducking, rampa, clips y subtítulos.

No se pudo hacer inspección visual de navegador en esta sesión: el arranque aislado de Chromium/Edge fue rechazado por la política local y no hay una herramienta de captura/control de navegador disponible. No se declara revisión visual completada. El proceso 4750 informó `restart_required=true`, por lo que tampoco se atribuye activación del backend nuevo ni se reinició Studio. Sin medios de prueba se dejan pendientes la reproducción audiovisual real, el render, los paneles de generadores y la inspección visual en 1920×1080/3440×1440. No se instalaron dependencias ni se generó contenido.
