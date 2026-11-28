# OpenCut: evaluación #64

24-11-2026 UTC. Principal `OpenCut-app/OpenCut`
`e668010778568641babef2cc40be4703ae6916d6`; Classic archivado
`OpenCut-app/opencut-classic@cf5e79e919144200294fb9fed22a222592a0aeea`.
Solo lectura: sin compilar, instalar herramientas ni abrir editor.

## Decisión y madurez

Esperar implementación comprobable del rewrite antes de conectar su API/MCP.
No abrir otra línea de editor: E06 intercambio y E10 puente acotado ya cubren
OpenReel/OpenFilm y se compararán con Concat#67. OPENMONTAGE tiene director,
edit_decisions, composición FFmpeg/Remotion/HyperFrames y persistencia propia;
no migrar Studio o GitHub Dark por promesas futuras de un editor.

[README principal](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/README.md)
declara reescritura y presenta Editor API, plugins, Rust multiplataforma, MCP,
headless y scripting como funciones venideras. No son diagnóstico aprobado.
[Desktop README](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/desktop/README.md)
advierte que actualmente solo abre una ventana. Tener ruta
[editor.tsx](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/web/src/routes/editor.tsx)
o api0.0.1 no establece export/automatización madura. No se hallaron rutas MCP o
headless por nombre en el árbol revisado; no afirmar ausencia universal de código.
[Classic README](https://github.com/OpenCut-app/opencut-classic/blob/cf5e79e919144200294fb9fed22a222592a0aeea/README.md)
y estado archived confirman mantenimiento detenido; no trasladar capacidades de
Classic a rewrite, ni del sitio alojado al código sin validar versión.

## Licencias y requisitos

[LICENSE MIT](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/LICENSE)
del principal: conservar avisos al adaptar; dependencias, fuentes/assets, codecs y
servicios requieren revisión propia. No se copió código Classic ni se deduce por
MIT raíz que GPUI u otras dependencias tienen los mismos términos.
[.prototools](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/.prototools)
fija moon2.3.3, Bun1.3.11 y Rust1.97.0; proto use instala herramientas, no se ejecutó.
[Web package](https://github.com/OpenCut-app/OpenCut/blob/e668010778568641babef2cc40be4703ae6916d6/apps/web/package.json)
usa React19.2/Vite8 y dependencias latest; snapshot/lock y requisitos efectivos se
deben cerrar antes de reproducir. Desktop GPUI documenta Windows Win32/DirectWrite,
pero no constituye export probado. Classic requiere stack distinto con Bun y
DB/Redis opcionales según alcance; no reinstalar infraestructura por esa alternativa.

## $0 y local/offline

No hay costo de licencia MIT del código por sí mismo. Patrocinio Fal y endpoints
Cloudflare no implican inferencia gratuita ni offline. Ejecutar un frontend local
no prueba persistencia, recursos, API o export sin red. El rewrite no aporta aquí
un perfil ejecutable acreditado de automatización; no conectarlo a servicios cloud
ni modificar ExecutionPolicy como preparación rutinaria. No instalar Classic para
suplir roadmap. Modelos/renderizadores actuales conservados.

## Tareas con aceptación

| Prioridad | Entrega | Aceptación |
|---|---|---|
| P2 | Matriz de madurez, E06/E10 | Por commit: anunciado/implementado/test upstream/validado local; endpoints/esquemas/cancel/export deben tener archivo y prueba, no solo README |
| P2 | Perfil de interoperabilidad | Proyecto sintético con IDs/fps/pistas/assets/hashes, unsupported explícito; sin pérdida silenciosa al comparar con edit_decisions |
| P3 | Gate para ensayo futuro | Solo si API/MCP/export reales y mantenidos, licencias/runtime cerrado, sandbox y offline; no instalar mientras falte evidencia |

Bloqueo de adopción: madurez insuficientemente acreditada del rewrite y Classic sin
mantenimiento. Evaluación terminada; no automatización periódica creada, medios
procesados ni configuraciones/ComfyUI modificados.
