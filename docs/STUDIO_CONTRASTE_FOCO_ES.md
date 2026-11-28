# E02: contraste y foco de controles de Studio (#113)

Actualización26-11-2026: las acciones antes ocultas pasaron en escenario
explícito permitido, HTML/CSS reales y acciones visibles, sin JS de producción:
contraste12,8804:1, foco sólido2px y Enter/Espacio con contadores locales.
Se combina con la activación4750 ya registrada y su recorrido real previo;
no se repiten formularios/viewports ni se inicia agente real. Criterios de
este issue acreditados en su alcance acotado; no conformidad WCAG global.
Evidencia: [cola conjunta](COLA_AUTONOMA_20261126_RESULTADOS.json).

Entrega independiente de #112, desde las evaluaciones fijadas #45/#58 y el
backlog E02. No se instalaron Taste, Impeccable, detectores, hooks ni frameworks.
Se reutilizan HTML/CSS, Chrome y Playwright ya disponibles. Coste operativo $0.

## Problema observado y cambio

Chrome calculaba para «Crear proyecto de producción»: texto16px system-ui
`rgb(230,237,243)` sobre `rgb(35,134,54)`. Contraste **3.9191574823649264:1**.
El texto pasa a blanco sobre el mismo verde: **4.630883088099265:1**.
Solo cambia el par de texto primario; fondo raíz `#0d1117`, paneles y verde
`#238636` conservan GitHub Dark. No se alteran densidad, distribución o acciones.

`studio.css` declara tokens semánticos de fondo/texto/control/acción/enlace/foco.
Los botones submit declarados y los de `#create` usan foreground primario blanco.
Foco común de teclado:2px azul existente `#58a6ff`, offset2px; las reglas específicas
del editor/nav conservan su prioridad. Forced colors usa Highlight del sistema.
El foco nativo anterior observado **ya era visible** (auto1px claro): se unifica
el contrato, no se presenta un supuesto fallo general de foco como descubierto.

Referencia de aceptación: [W3C contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
distingue texto normal4.5:1, grande3:1 y componentes inactivos excluidos; los
umbrales se comparan sin redondear. [Foco visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)
requiere un indicador perceptible de teclado. La prueba local de2px no se
presenta como certificación WCAG completa ni se impone AAA7:1.

## Pruebas focalizadas nuevas

`scripts/validate_studio_accessibility.cjs` lee el HTML/CSS real del repositorio,
retira sus scripts y construye una fixture de cabecera, formulario de creación
y controles nativos de iniciar/detener/aprobar. Sus eventos solo cuentan
activaciones y cancelan submit; ninguna llamada de producción ni API real.
No conecta a Studio4750. Todas las solicitudes de red se bloquean y el informe
confirmó **0 solicitudes**. No produce vídeo, voz, ASR ni imágenes generativas.

Entorno observado: Windows, Chrome158.0.8127.37, Node24.22.1; instalaciones
existentes. Se probaron320/390/768/1280×900CSSpx:

| Comprobación | Resultado |
|---|---|
| Texto primario normal/hover/pulsado | 4.630883088099265:1, aprobado |
|20 controles primarios declarados por viewport | Colores computados correctos; incluye ocultos, no interacción de esos20 paneles |
|8 controles del formulario | Tab y Mayús+Tab en orden, foco visible2px; contraste del foco frente a su panel>=3:1 |
|Iniciar/detener/aprobar | Tab real y activación nativa por Espacio/Enter, solo contadores fixture |
|Acentos,¿?,texto y ruta Windows largos | Cadenas conservadas, controles dentro del ancho y sin scroll horizontal de página |
|320/390/768/1280px | Ancho scroll igual al viewport, captura320 y1280 revisada |
|CSS zoom2 y forced-colors | Emulación pasa; no zoom físico/OS ni prueba humana de alto contraste |
|Negativo del par original | Falla4.5:1; mutar el token a gris reproduce el fallo, restaurarlo lo resuelve |
|Negativos/referencias de cálculo | Negro/blanco21:1 y mismo color1:1 |

El campo de título de una línea permite desplazamiento interno para texto largo;
no se afirma que toda su cadena quepa simultáneamente en320px. Se comprobó el
valor completo además de los límites del control. No se cambió el responsive
existente porque no falló en esta fixture.

Reproducción: proporcionar `PLAYWRIGHT_MODULE` y `CHROME_EXE` con instalaciones
existentes y ejecutar `node scripts/validate_studio_accessibility.cjs` desde la
raíz. `REPORT_PATH` opcional; por defecto `.runtime/qa/studio-accessibility.json`.
Sin instalación automática si faltan dependencias. Capturas locales
`.runtime/qa/studio-e02-320.png` y `studio-e02-1280.png`; no incluyen proyectos
del usuario ni se publican medios personales.

## Activación y alcance pendiente

#112 sigue pendiente de activación. Se agrupan **#112+#113** con futuras entregas
en un único reinicio **manual** y recarga posterior, según
[el plan compartido](ACTIVACION_AGRUPADA_STUDIO_ES.md). No se reinició ni se
recargó el Studio del usuario durante esta entrega; estilos computados en fixture
no prueban que el panel abierto haya aplicado la hoja nueva.

E02 global sigue abierto: quedan interacción de toda la aplicación, errores
API400/403/500/timeout, drag interrumpido, lector de pantalla, toque físico y
comprobación del panel real tras activación. Tampoco se acredita accesibilidad
de todos los pares de color, todos los paneles o del timeline completo.
Sin repetir #111, suites o CI aprobadas; sin nuevas instalaciones/inferencias.
Configuraciones, originales, .venv y ComfyUI intactos. PR#2 permanece en borrador.
