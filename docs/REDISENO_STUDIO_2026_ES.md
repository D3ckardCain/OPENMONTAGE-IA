# Studio: rediseÃ±o de interfaz

La carcasa visual se reemplaza por una aplicaciÃ³n de trabajo en ancho completo: navegaciÃ³n lateral, barra de contexto y espacios separados para VÃ­deo, Audio, SubtÃ­tulos, Biblioteca, Proyectos, InvestigaciÃ³n, Comparativas, Miniaturas, Avatares, Clips y Preferencias. El diseÃ±o usa GitHub Dark, iconos SVG locales, controles compactos y scroll dentro de paneles; no carga fuentes, imÃ¡genes ni cÃ³digo remoto.

## Flujos conectados

- **Proyectos:** lista y creaciÃ³n por `/api/studio/editor/projects`; muestra la ruta completa y las carpetas de trabajo que devuelve el workspace. La reserva de nombre y creaciÃ³n del Ã¡rbol siguen en el backend existente. La raÃ­z efectiva se lee de `/api/studio/storage`; cambiarla desde esta pantalla no estÃ¡ habilitado.
- **VÃ­deo / ediciÃ³n manual:** `/api/studio/editor/projects`, estado, carga de originales, registro, comandos compartidos, render y estado del render. Los controles visibles cubren aÃ±adir fuente, recortar, dividir, mover en orden, quitar, formato, deshacer/rehacer, guardar y exportar. El archivo importado se copia al proyecto segÃºn el endpoint; el archivo de origen no se mueve ni se elimina.
- **Audio:** presenta las pistas del montaje y conecta ganancia, mute y solo a `operation=clip`. No dibuja una forma de onda falsa. EQ, compresor, ducking y catÃ¡logo no aparecen como controles activos en esta entrega.
- **SubtÃ­tulos:** importa bytes SRT con la ruta existente, edita texto/tiempos con `cue_update`, aplica estilo/posiciÃ³n/modo/idioma con `subtitle_style` y descarga SRT. Nuevo bloque vacÃ­o no estÃ¡ soportado por el comando disponible y queda desactivado. Calidad, karaoke, lÃ­mites CPS y zonas seguras no se anuncian aquÃ­.
- **InvestigaciÃ³n (mÃ³dulo 10):** usa consulta real de YouTube y su configuraciÃ³n/credencial local. Las mÃ©tricas vacÃ­as se muestran como desconocidas. TikTok, Facebook e Instagram carecen de conector pÃºblico configurado; sus cifras solo pueden aportarse como notas locales sin verificar, que no se presentan como mediciones confirmadas.
- **Comparativas deportivas (mÃ³dulo 11):** reutiliza schema/query UEFA existente, con campos derivados del contrato de la API, y presenta alcance/contexto que devuelve la fuente. La cobertura depende del conector y no equivale a todo el deporte. EnvÃ­o a vÃ­deo, clips o miniaturas no estÃ¡ habilitado por este mÃ³dulo.
- **Otros modos:** las seis opciones de VÃ­deo estÃ¡n visibles. Solo Â«Editar material propioÂ» ejecuta el ciclo conectado. Texto a vÃ­deo, imagen a vÃ­deo, recreaciÃ³n desde referencia, guion a vÃ­deo y plantillas muestran estado no disponible/preparaciÃ³n pendiente. Miniaturas, avatares y clips describen lÃ­mites y no fingen una generaciÃ³n.

## Identidad y activaciÃ³n

La pÃ¡gina consulta `/api/studio/identity`. Si el proceso anuncia `restart_required`, muestra una advertencia discreta con hashes abreviados; no reinicia nada automÃ¡ticamente. La nueva pÃ¡gina tambiÃ©n se sirve desde el archivo local mientras el backend sigue siendo el ya residente. Toda escritura depende de que la ruta de API correspondiente responda y valide revisiÃ³n.

## RevisiÃ³n y lÃ­mites

VerificaciÃ³n local: HTTP 200 para `/studio`, `/ui/studio.css`, `/ui/studio.js` y `/api/studio/editor/capabilities`; 11 mÃ³dulos, IDs HTML Ãºnicos, sin entradas heredadas de CSS/JS visual y llaves CSS balanceadas. El endpoint de capacidades declarÃ³ comandos de ediciÃ³n compartidos, incluidos mezclador, keyframes, ducking, rampa, clips y subtÃ­tulos.

No se pudo hacer inspecciÃ³n visual de navegador en esta sesiÃ³n: el arranque aislado de Chromium/Edge fue rechazado por la polÃ­tica local y no hay una herramienta de captura/control de navegador disponible. No se declara revisiÃ³n visual completada. El proceso 4750 informÃ³ `restart_required=true`, por lo que tampoco se atribuye activaciÃ³n del backend nuevo ni se reiniciÃ³ Studio. Sin medios de prueba se dejan pendientes la reproducciÃ³n audiovisual real, el render, los paneles de generadores y la inspecciÃ³n visual en 1920Ã—1080/3440Ã—1440. No se instalaron dependencias ni se generÃ³ contenido.

