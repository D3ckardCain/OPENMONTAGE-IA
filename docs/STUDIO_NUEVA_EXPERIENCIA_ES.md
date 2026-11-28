# Rediseño integral de Studio

Este documento es el contrato de producto para reemplazar la presentación de Studio. La nueva interfaz no hereda navegación, distribución, componentes ni estilos de la interfaz anterior. Se conserva la capa de servicios y sus contratos cuando están implementados y se usan; cada control nuevo debe enlazarse a una ruta/capacidad real o mostrarse como no disponible.

## Sistema visual aplicado

La búsqueda local de UI UX Pro Max recomendó una herramienta creativa de escritorio densa, con paneles compactos, foco visible y superficies oscuras. El patrón Hero-Centric que también apareció en la búsqueda no encaja con un editor de uso diario y se descarta. GitHub Dark se mantiene como preferencia del producto: fondo `#0d1117`, superficies `#161b22` y `#21262d`, bordes `#30363d`, texto `#e6edf3`, texto secundario `#8b949e` y acción principal azul `#2f81f7`. Se usan fuentes locales del sistema; ninguna fuente externa ni recurso remoto es requisito.

Reglas de interacción derivadas de UI UX Pro Max: controles semánticos con etiqueta, navegación de teclado, `:focus-visible`, foco no oculto por paneles persistentes, estados de carga/guardado/error próximos al control, movimiento reducido, sin iconos emoji, scroll dentro del panel y sin desbordamiento horizontal. El esqueleto prioriza lienzo de trabajo, biblioteca, visor y timeline; no una portada de marketing ni texto técnico.

## Módulos

1. **Texto a vídeo** — formulario breve y etapas; solo inicia herramientas de generación registradas y disponibles.
2. **Imagen a vídeo** — imagen de entrada en copia del proyecto y controles de movimiento únicamente si el adaptador activo los admite.
3. **Recrear desde referencia** — reutiliza análisis guardado o rutas locales existentes; cobertura y procedencia visibles.
4. **Guion y narración** — guion, voz y subtítulos mediante adaptadores disponibles, con revisión antes de avanzar.
5. **Edición de material propio** — editor compartido con el agente, historial de comandos y revisión manual.
6. **Plantillas recurrentes** — plantillas y campos existentes; “Adaptar para redes” forma parte de este modo y de los cinco anteriores, no es un modo separado.
7. **Avatares** — disponibilidad real del adaptador, modelo y licencia antes de ofrecer una acción.
8. **Miniaturas** — proyecto editable y procedencia de imágenes; nunca afirmar una variante generada si no se ejecutó.
9. **Clips y tráileres** — candidatos sustentados por transcripción/muestreo y cobertura mostrada.
10. **Investigación de nichos y canales** — permite consulta por tema/plataforma, comparación, revisión de publicaciones y un informe fechado con fuentes y criterios. Reutiliza el buscador/dossier de YouTube existente cuando la credencial y cuota están disponibles. La consulta global de TikTok, Facebook e Instagram no tiene conector público universal configurado: esos datos permanecen como `desconocidos` salvo que el usuario los aporte con fuente, fecha y alcance. No se presentan métricas privadas, scraper ni publicación social.
11. **Comparativas deportivas** — reutiliza los contratos de estadísticas, catálogos de fuentes, agente, expediente, revisión de métricas y tarjetas existentes. Cada cifra debe conservar fuente, fecha, competición/temporada/fase y contexto; los campos ausentes siguen `null`. La selección final se puede enviar a vídeo/clips/miniatura solo por las rutas ya soportadas; el diseño no crea una integración inexistente.

## Carpetas de proyecto

La raíz persistente sigue siendo la raíz configurada por Studio (`/api/studio/storage`); se muestra su ruta y la selección se guarda en la configuración local. El modelo actual usa una sola raíz activa por sesión: cambiarla se guarda y requiere el reinicio manual previsto por almacenamiento antes de crear proyectos ahí. No se migra nada al cambiarla.

Cada proyecto nuevo reserva de forma exclusiva una carpeta legible derivada de su nombre. Si ya existe, se usa una variante segura numerada (`nombre-2`, `nombre-3`); nunca se abre ni sobrescribe la carpeta preexistente. La respuesta de creación y la API de proyecto exponen la ruta completa. La estructura inicial común incluye `datos/`, `originales/`, `medios_generados/`, `audio/`, `subtitulos/`, `miniaturas/`, `edicion/`, `cache/` y `exportaciones/`, además de los directorios de contrato requeridos por servicios ya existentes.

El editor copia archivos importados a `originales/` y conserva su ubicación de origen. Los SRT importados se guardan en `subtitulos/`. Los pesos de modelos compartidos no se copian al proyecto. Los motores heredados todavía escriben bajo sus rutas de contrato (`artifacts/`, `assets/` y `renders/`); completar su migración a las carpetas semánticas requiere adaptar cada escritor y consumidor y es un criterio pendiente antes de afirmar que toda salida de todos los motores está ya centralizada en la estructura nueva.

## Evidencia

- Búsqueda UI UX Pro Max: `data-dense-dashboard` y guía de controles accesibles; variante Hero-Centric evaluada y descartada como inadecuada para el editor.
- La primera entrega de workspace verifica nombres legibles, colisión numerada y creación de los directorios comunes sin acceder a medios ni modelos.
- El rediseño completo, integración de los once módulos y revisión visual siguen abiertos hasta reemplazar la pantalla servida y comprobarla en navegador a los tamaños de viewport de #92.

