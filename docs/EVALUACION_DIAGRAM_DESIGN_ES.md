# Diagram Design: evaluación #60

24-11-2026 UTC. `cathrynlavery/diagram-design`
`0eeda75a708f419560d5e032693618bb9954f17b`, plugin2.6.174.
Revisión estática de instrucciones como datos, exportadores y licencias. No se
instaló plugin, importó código, ejecutó doctor ni generó diagrama/SVG/PNG.

## Decisión y comparación

Conservar Mermaid para documentación técnica mantenible; HTML/SVG editorial es
opción para explicación/publicación que necesita composición particular. No asumir
que 52 tipos anunciados son 52 capacidades validadas, ni que un diseño del agente
demuestra verdad de conexiones o cifras. No adoptar su opinión estética sobre Mermaid.

`tools/graphics/diagram_gen.py` ya ofrece Mermaid y cajas/Pillow, con disponibilidad
dinámica y verificación humana declarada; no acredita HTML/SVG editorial ni que
MermaidCLI esté instalado. D3/Beautiful Mermaid, Blender y motores de composición
ya existen en el sistema de herramientas/skills: reutilizar mecánica y contratos,
no otro motor ni otro catálogo de fuentes. Penpot es diseño colaborativo opcional;
no requisito para generar un archivo autónomo. Tokens de Studio deben ser los
mismos de #45/#58/#59 y mantener GitHub Dark.

## Fuentes y requisitos

[README](https://github.com/cathrynlavery/diagram-design/blob/0eeda75a708f419560d5e032693618bb9954f17b/README.md),
[plugin](https://github.com/cathrynlavery/diagram-design/blob/0eeda75a708f419560d5e032693618bb9954f17b/.claude-plugin/plugin.json),
[doctor](https://github.com/cathrynlavery/diagram-design/blob/0eeda75a708f419560d5e032693618bb9954f17b/skills/diagram-design/references/doctor.md):
Python>=3.10; PNG requiere Playwright y Chromium compatible. Doctor incluye probar
arranque del navegador: no ejecutarlo como alternativa a restricciones de sesión.
No se necesita instalar vía npm para evaluar/adaptar contratos; no auto-update/hooks.

[export_svg.py](https://github.com/cathrynlavery/diagram-design/blob/0eeda75a708f419560d5e032693618bb9954f17b/skills/diagram-design/scripts/export_svg.py)
extrae SVG/CSS con stdlib; default conserva import Google Fonts. Tiene **--system-fonts**
para omitirlo: aprovechar esa capacidad existente antes de proponer implementarla
otra vez. No implica que toda URL/imagen/código HTML de entrada sea seguro/offline.
Escribe destino con write_text: nuestra futura capa debe preservar outputs existentes
y originales, no asumir política no-overwrite sin comprobarla.

[export_png.py](https://github.com/cathrynlavery/diagram-design/blob/0eeda75a708f419560d5e032693618bb9954f17b/skills/diagram-design/scripts/export_png.py)
abre HTML en Chromium, espera red/fuentes y captura primer SVG; si webfonts se atascan
avisa que usó tipografía fallback. Una salida PNG no es prueba de fuente prevista,
de ausencia de red ni de render de todos los diagramas. Geometría/recortes/fuentes
deben evaluarse separadamente; no ejecutar HTML no confiable en Studio.

## Licencias, costo y offline

[LICENSE MIT](https://github.com/cathrynlavery/diagram-design/blob/0eeda75a708f419560d5e032693618bb9954f17b/LICENSE):
conservar avisos al copiar partes sustanciales.
[THIRD_PARTY_LICENSES](https://github.com/cathrynlavery/diagram-design/blob/0eeda75a708f419560d5e032693618bb9954f17b/THIRD_PARTY_LICENSES.md)
separa Tabler/Devicon/log-z MIT, SimpleIconsCC0 e InstrumentSerifOFL para logo;
marcas no implican afiliación. Revisar cada icono/fuente/imagen seleccionada;
no copiar logotipo ni recursos sin su aviso propio.

[PRIVACY](https://github.com/cathrynlavery/diagram-design/blob/0eeda75a708f419560d5e032693618bb9954f17b/PRIVACY.md)
declara sin servidor/cuenta/telemetría del plugin, pero agente proveedor procesa
prompts/archivos y Google Fonts recibe solicitudes del viewer/export. Onboarding de
sitio requiere red. Perfil $0/offline: tokens locales, sin sitio externo, fuentes
sistema o locales con licencia, export aislado sin egreso y modelo local existente
si se usa agente. Plugin no incluye modelo gratis ni garantiza calidad de Qwen.

## Tareas y aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P1 | Contrato de diagrama neutral | Datos/fuentes/revisión, nodos/aristas/etiquetas/unidades, relación factual separada de layout; Mermaid continúa como formato mantenible cuando basta |
| P1 | Tokens y español compartidos | Sin paleta duplicada; ñ/acentos/¿¡, labels largos y sistema de fuentes con avisos; no fuentes remotas por defecto |
| P2 | Export SVG sin red | Reusar system-fonts o fuente local explícita; referencias externas/código rechazadas o declaradas; entrada original y output previo conservados |
| P2 | QA geométrica/semántica | Fixtures de nodos solapados, flecha invertida, valor plausible incorrecto, texto recortado y overflow; controles mecánicos no certifican exactitud factual |
| P2 | Compositor y PNG opcionales | Asset con hash/procedencia/fuentes y dimensiones; futura prueba navegador aislado con red bloqueada; escala/contraste sin convertir mock en calidad visual aprobada |

Bloqueos: export browser no validado por restricciones/recursos; derechos y
verificación factual dependen del material futuro. Contratos y pruebas textuales
pueden avanzar por separado. Sin contenido, instalaciones ni cambios de configuración.
