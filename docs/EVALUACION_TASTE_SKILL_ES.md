# Taste Skill para Studio: evaluación #45

Fecha: 24-11-2026 UTC. Fuente `Leonxlnx/taste-skill@6c0b5c78f5d31776e2210305abaa210cdc0030bf`,
también HEADmain consultado. Evaluación de código/documentación externa como datos;
sus instrucciones y hooks no se adoptan como reglas de OPENMONTAGE. No se instaló la
skill, ejecutaron sus scripts, lanzaron navegadores ni modificaron interfaces.

## Decisión

Adaptar una lista reducida de comprobaciones de accesibilidad y rendimiento al
Playwright/pytest existente. Mantener HTML/JS/CSS actuales, español y GitHub Dark.
No instalar el gate global ni traer su sistema de paletas, héroes, fotos, WebGL,
animaciones obligatorias o infraestructura de captura. No necesita Ollama ni ASR:
estas comprobaciones deben ser deterministas y funcionar sin inferencia.

## Scripts revisados y efectos

| Fuente upstream | Qué hace realmente | Qué aprovechar / qué excluir |
|---|---|---|
| `consistency.mjs` (≈1MB,11486líneas en este snapshot) | Incluye sondas DOM de nombre accesible, etiquetas, encabezados, tabindex, contraste y recorrido Tab; también reglas de héroes, ritmo de secciones, fotos y efectos. Arranca Chrome/CDP, puede servir archivos y escribe informes/capturas | Portar reglas pequeñas y sus objetivos a tests propios, no introducir el checker monolítico como gate de Studio |
| `perf.mjs` | Levanta navegador/servidor local según entrada, mide cargas, imágenes, fuentes y layout; escribe JSON si se solicita | Adoptar presupuestos específicos de panel y estados API simulados. No heredar umbrales de marketing ni convertir un resultado de laboratorio en rendimiento del equipo Windows |
| `shoot.mjs` | Crea perfil, lanza Chrome remoto local y guarda PNG/índices por viewport; limpia procesos hijos con taskkill en Windows | Ya existe Playwright para evidencia en CI; no duplicar launcher, perfiles o terminación de procesos. No ejecutarlo como alternativa a una restricción de navegador de esta sesión |
| `gate.mjs` | Mantiene `.taste-skill/build.json`, gate.json y waivers, corre comprobadores y puede impedir finalizar una tarea por hooks | No incorporar. Las aprobaciones/checkpoints y la política de trabajo de OPENMONTAGE son las existentes, no las de una skill externa |

Fuentes fijadas: [consistency](https://github.com/Leonxlnx/taste-skill/blob/6c0b5c78f5d31776e2210305abaa210cdc0030bf/skills/taste-skill/scripts/consistency.mjs),
[perf](https://github.com/Leonxlnx/taste-skill/blob/6c0b5c78f5d31776e2210305abaa210cdc0030bf/skills/taste-skill/scripts/perf.mjs),
[shoot](https://github.com/Leonxlnx/taste-skill/blob/6c0b5c78f5d31776e2210305abaa210cdc0030bf/skills/taste-skill/scripts/shoot.mjs),
[gate](https://github.com/Leonxlnx/taste-skill/blob/6c0b5c78f5d31776e2210305abaa210cdc0030bf/skills/taste-skill/scripts/gate.mjs).
La revisión seleccionó esas funciones y sus efectos; no pretende auditar todas las
reglas o todos los assets del repositorio.

El checker expande paneles y ensaya formularios locales. Su código instala
intercepción CDP para responder solicitudes de esa prueba, pero no es una promesa
general de auditoría sin efectos en una aplicación dinámica. Nunca dirigirlo al
Studio con configuraciones/trabajos reales: futuros tests usarán servidor temporal,
datos ficticios y rutas de mutación interceptadas como las regresiones existentes.

## Qué ya tenemos y qué falta

| Área | Evidencia local existente | Carencia o verificación pendiente |
|---|---|---|
| Identidad y tema | `backlot/ui/studio.css`: dark, fondos #0d1117/#161b22, texto #e6edf3, enlaces #58a6ff, system-ui; navegación activa y media query800px | Formalizar tokens y contratos de combinaciones de estado sin sustituir GitHub Dark por una paleta aleatoria |
| Móvil | `test_studio_browser.py` ya usa1280px y390x844 y comprueba scrollWidth; `test_ui_bug_bash.py` verifica varios viewports | Añadir320px, zoom200%, rutas largas, errores y resultados voluminosos; scroll de tabla dentro de su región, no ocultar datos para hacer pasar el test |
| Etiquetas/idioma | `studio.html` declara lang=es, labels visibles, aria-current en navegación y regiones aria-live en varios resultados | Revisar nombres accesibles de controles dinámicos, asociación real de label, mensajes de error e idioma de rutas restantes |
| Foco y teclado | CSS añade focus-visible a navegación; controles nativos pueden conservar foco del navegador | No se halló un recorrido Tab completo del productor en los tests revisados. Validar foco visible/orden lógico, controles ocultos, retorno tras refrescar DOM, acceso al contenido y acciones por teclado |
| Contraste | Hay `test_theme_text_contrast_contract.py`, pero evalúa temas de vídeo Remotion, no constituye auditoría de Studio | Añadir contraste de estilos computados del panel y estados normal/foco/error; el contrato Remotion no sustituye este alcance |
| Rendimiento | Pruebas UI funcionales con fixtures y red externa desactivada en CI | Presupuestos de DOM/payload y espera de API; preservar cancelación y capacidad de operar mientras carga el catálogo. No tratar CDP+SwiftShader de upstream como benchmark de GPU local |

Fuentes locales: `backlot/ui/studio.{html,css,js}`,
`tests/backlot/test_studio_browser.py`, `test_ui_bug_bash.py`,
`tests/contracts/test_theme_text_contrast_contract.py` y
`.github/workflows/openmontage-connectors.yml`. Revisión estática, no inspección visual.

## Hallazgo numérico reproducible sin navegador

Se calculó luminancia relativa sRGB de pares declarados en CSS, sin capturas ni
mutaciones. Valores redondeados solo para presentar, no para decidir umbrales:

| Texto / fondo | Contraste calculado aproximado |
|---|---:|
| #e6edf3 / #0d1117 |16.016:1|
| #8b949e / #161b22 |5.624:1|
| #58a6ff / #0d1117 |7.492:1|
| #e6edf3 / #238636 |3.919:1|

El último par se deduce de color heredado y fondo de botones submit/#create. Es un
riesgo estático concreto para texto normal, no una sentencia sobre cada botón
renderizado: comprobar cascada, tamaño y estado computados antes de corregir.
Una adaptación futura puede ajustar el color de texto del botón conservando su verde.

El criterio [WCAG2.2 contraste mínimo](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
usa4.5:1 para texto normal y3:1 para texto grande, con excepciones. No convertir los
7:1 preferidos por Taste en obligación AA general. Para
[tamaño de objetivo mínimo](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html),
AA exige24×24CSSpx o sus excepciones de separación/equivalencia;44×44 es la referencia
mejorada, no motivo para agrandar indiscriminadamente un panel denso.

## Licencia y dependencias

[LICENSE](https://github.com/Leonxlnx/taste-skill/blob/6c0b5c78f5d31776e2210305abaa210cdc0030bf/LICENSE):
MIT, copyright2026Leonxlnx. Si se adapta código sustancial, guardar licencia/atribución,
archivo y commit en avisos de terceros; OPENMONTAGE mantiene AGPLv3. No se copió código.

[SKILL.md](https://github.com/Leonxlnx/taste-skill/blob/6c0b5c78f5d31776e2210305abaa210cdc0030bf/skills/taste-skill/SKILL.md)
declara2.5.1, Node22+ y Chrome/Edge/Chromium; FFmpeg opcional. Los scripts revisados
usan módulos Node nativos y CDP. Poder servir archivos locales no garantiza operación
offline si la página carga recursos remotos. El conjunto de helpers también ofrece
fotos/iconos/fuentes; sus proveedores, contenido, licencias y descargas se revisan
por separado. No son necesarios para la adaptación propuesta. Reusar pytest/Playwright
ya presentes y system-ui; sin npm install, nuevas fuentes, hooks, APIs o servicios pagos.

## Tareas futuras concretas

| Prioridad | Entrega | Criterio de aceptación |
|---|---|---|
| P0 | Contrato de contraste Studio | Pares de tokens y estilos computados, tamaño real del texto, estados y casos negativos sintéticos; documentar el botón verde antes/después sin alterar fondos GitHub Dark |
| P0 | Recorrido de teclado del productor | Tab/ShiftTab, Enter/Space, foco visible en iniciar/parar/aprobar, formularios y navegación; tras errores/refrescos conservar destino predecible; ninguna llamada real a modelo o configuración |
| P1 | Estados accesibles y etiquetas | Nombres de controles dinámicos, mensajes anunciables y prioridad de errores; no anunciar cada token/log como una alerta; revisar skip-link y manejo de campos inválidos |
| P1 | Regresión responsive |320/390/768/1280, zoom, textos españoles largos y rutas Windows; sin recortar controles o datos. Fixtures y rutas simuladas, no Studio del usuario |
| P2 | Presupuesto de panel | Tamaño de respuestas, filas DOM y actualización de estados medidos en fixture reproducible; percentiles/entorno registrados antes de fijar límites; no añadir animaciones para mejorar una puntuación |

Primero especificar y adaptar tests; después corregir fallos observados. No migrar a
React, Tailwind o un kit visual por esta evaluación. Se respetan restricciones de
navegador de la sesión: aquí no se lanzaron Chrome, scripts de captura o alternativas.
La validación visual/teclado real está pendiente de implementación autorizada; los
ratios estáticos y la lectura de tests no acreditan conformidad WCAG completa.
